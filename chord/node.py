import socket
import threading
import time
import logging
import json
from .codes import *
from .node_reference import ChordNodeReference
from .handler import Handler
from .utils import hash_function, _inbetween
from logic.tournament import TournamentSimulator
import copy
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')
BROADCAST_PORT = 9001
TOURNAMENT_PORT = 9002


class ChordNode:
    def __init__(self, ip: str, port: int = 8001, m: int = 8):
        self.id = hash_function(ip, m)
        self.ip = ip
        self.port = port
        self.ref = ChordNodeReference(self.ip, self.port)
        self.successor = self.ref
        self.predecessor = None
        self.predecessor2 = None
        self.predecessor3 = None
        self.handler = Handler(self.id)
        self.m = m
        self.finger = [self.ref] * self.m
        self.next = 0  # Finger table index to fix next
        self.data = self.handler.initial_data()
        self.pred_data = {}
        self.pred2_data = {}
        self.lock = threading.Lock()
        self.tournaments = []

        # Start background threads for stabilization, fixing fingers, and checking predecessor
        threading.Thread(target=self.listen_for_broadcast, daemon=True).start()
        threading.Thread(target=self.recv_tournament, daemon=True).start()
        threading.Thread(target=self.stabilize, daemon=True).start()  # Start stabilize thread
        threading.Thread(target=self.fix_fingers, daemon=True).start()  # Start fix fingers thread
        threading.Thread(target=self.check_predecessor, daemon=True).start()  # Start check predecessor thread
        threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
        threading.Thread(target=self.get_data_from_predecessors, daemon=True).start()
        threading.Thread(target=self.update_data, daemon=True).start()
        self.send_broadcast_join()

    def handle_join(self, node_id: int, node_ip: str, node_port: int):
        logging.info(f"Handle JOIN of {node_id}: {node_port}")
        new_node_ref = ChordNodeReference(node_ip, node_port)
        logging.info(new_node_ref)
        time.sleep(2)
        if node_id != self.id:
            if self.predecessor is None and self.id == self.successor.id:
                with self.lock:
                    self.predecessor = new_node_ref
                    self.predecessor2 = self.ref
                    self.predecessor3 = new_node_ref
                    self.predecessor.update_successor(self.ref)
                logging.info(f"Update predecessor to {self.predecessor}")

                if new_node_ref.id > self.predecessor.id:
                    with self.lock:
                        self.successor = new_node_ref
                        self.successor.notify(self.ref)
                    logging.info(f"Update successor to {self.successor}")

            if self.predecessor and _inbetween(node_id, self.predecessor.id, self.id):
                with self.lock:
                    self.predecessor.update_successor(new_node_ref)
                    self.predecessor = new_node_ref
                    self.predecessor.update_successor(self.ref)
                    self.predecessor2 = self.predecessor.predecessor if self.predecessor else None
                    self.predecessor3 = self.predecessor2.predecessor if self.predecessor2 else None
                logging.info(f"Update predecessor to {self.predecessor}")

            if _inbetween(node_id, self.id, self.successor.id):
                if new_node_ref.id != self.successor.id:
                    with self.lock:
                        self.successor = new_node_ref
                        self.successor.notify(self.ref)
                        logging.info(f"Update successor to {self.successor}")

    def listen_for_broadcast(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', BROADCAST_PORT))
        logging.info(f"Listen port: {BROADCAST_PORT}")

        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8').split(',')

            if message[0] == "JOIN":
                node_id = int(message[1])
                node_ip = message[2]
                node_port = int(message[3])

                logging.info(f"RECV JOIN from {node_id}  ({node_ip}:{node_port})")

                self.handle_join(node_id, node_ip, node_port)

    def notify_tournament(self, tournament):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        tournament_json = json.dumps(tournament)
        message = f"TOURNAMENT|{tournament_json}".encode('utf-8')

        sock.sendto(message, ('255.255.255.255', TOURNAMENT_PORT))
        logging.info(f"Notify tournament {tournament}")

        sock.close()

    def recv_tournament(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', TOURNAMENT_PORT))
        logging.info(f"Listening on tournament port: {TOURNAMENT_PORT}")

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8').split('|')

                if message[0] == "TOURNAMENT":
                    tournament = message[1]
                    if tournament:
                        tournament = json.loads(tournament)
                        logging.info(f"Received tournament: {tournament}")
                        exists = False
                        for t in self.tournaments:
                            if t['id'] == tournament['id']:
                                exists = True
                                t['completed'] = tournament['completed']
                        if not exists:
                            self.tournaments.append(tournament)

            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON: {e}")
            except Exception as e:
                logging.error(f"Error receiving tournament: {e}")

    def get_tournaments(self):
        return self.ref.send_tournaments()

    def send_broadcast_join(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"JOIN,{self.id},{self.ip},{self.port}".encode('utf-8')

        sock.sendto(message, ('255.255.255.255', BROADCAST_PORT))
        logging.info(f"SEND JOIN broadcast from {self.id}")

        sock.close()

    def update_successor(self, node: 'ChordNodeReference'):
        self.successor = node

    def update_predecessor(self, node: 'ChordNodeReference'):
        self.predecessor = node

    # Method to find the successor of a given id
    def find_successor(self, id: int) -> 'ChordNodeReference':
        node = self.find_predecessor(id)  # Find predecessor of id
        if node:
            return node.successor  # Return successor of that node

    # Method to find the predecessor of a given id
    def find_predecessor(self, id: int) -> 'ChordNodeReference':
        node = self
        while not _inbetween(id, node.id, node.successor.id):
            node = node.closest_preceding_finger(id)
        if isinstance(node, ChordNodeReference):
            return node
        return node.ref

    # Method to find the closest preceding finger of a given id
    def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
        for i in range(self.m - 1, -1, -1):
            if self.finger[i] and _inbetween(self.finger[i].id, self.id, id):
                return self.finger[i]
        return self.ref

    # Method to join a Chord network using 'node' as an entry point
    def join(self, node: 'ChordNodeReference'):
        if node:
            self.predecessor = None
            self.successor = node.find_successor(self.id)
            logging.info(f'in join: successor of {self.ref} is {self.successor} ')

            self.successor.notify(self.ref)
        else:
            self.successor = self.ref
            self.predecessor = None

    # Stabilize method to periodically verify and update the successor and predecessor
    def stabilize(self):
        while True:
            try:
                if self.successor and self.successor.id != self.id:
                    logging.info('stabilize')
                    x = self.successor.predecessor
                    logging.info(f'predecessor of successor: {x}')
                    if x and x.id != self.id:
                        if _inbetween(x.id, self.id, self.successor.id):
                            self.successor = x
                        self.successor.notify(self.ref)
            except Exception as e:
                logging.error(f"Error in stabilize: {e}")

            logging.info(f"(NODE_CON) successor : {self.successor} predecessor {self.predecessor}, {self.predecessor2},"
                         f"{self.predecessor3}")
            time.sleep(10)

    # Notify method to inform the node about another node
    def notify(self, node: 'ChordNodeReference'):
        if node.id == self.id:
            pass
        if not self.predecessor or _inbetween(node.id, self.predecessor.id, self.id):
            self.predecessor = node
            logging.info(f"predecessor {self.predecessor}, {self.predecessor.predecessor} ")
            self.predecessor2 = self.predecessor.predecessor
            self.predecessor3 = self.predecessor2.predecessor if self.predecessor2 else None

    # Fix fingers method to periodically update the finger table
    def fix_fingers(self):
        while True:
            try:
                self.next += 1
                if self.next >= self.m:
                    self.next = 0
                suc = self.find_successor((self.id + 2 ** self.next) % 2 ** self.m)
                if suc:
                    self.finger[self.next] = suc

            except Exception as e:
                logging.error(f"Error in fix_fingers: {e}")
            time.sleep(5)

    def dist_data(self, data: dict):
        if not data:
            return
        logging.info(f'dist_data {self.data}')
        for key, value in list(data.items()):
            self.data[key] = value

    # Check predecessor method to periodically verify if the predecessor is alive
    def check_predecessor(self):
        while True:
            try:
                # A --- B --- C --- D
                logging.info(f'pred: {self.predecessor}')

                if self.predecessor:

                    resp = self.predecessor.check()
                    logging.info(f'resp from: {self.predecessor} is {resp}')
                    if resp == b'':
                        logging.info('pred1 is dead')
                        self.dist_data(self.pred_data)
                        if self.predecessor2.id == self.id:
                            self.predecessor = None
                            self.predecessor2 = None
                            self.predecessor3 = None
                            self.successor = self.ref
                            continue

                        resp = self.predecessor2.check()
                        if resp == b'':
                            logging.info('pred2 is dead')
                            self.dist_data(self.pred2_data)
                            if self.predecessor3:
                                if self.predecessor3.id == self.id:
                                    self.predecessor = None
                                    self.predecessor2 = None
                                    self.predecessor3 = None
                                    self.successor = self.ref
                                    continue
                                else:
                                    self.predecessor = self.predecessor3
                                    self.predecessor.update_successor(self.ref)
                                    self.successor = self.predecessor
                                    self.predecessor2 = self.predecessor.predecessor
                                    self.predecessor3 = self.predecessor2.predecessor if self.predecessor2 else None

                        else:
                            logging.info(f'new pred : {self.predecessor}')
                            self.predecessor = self.predecessor2
                            self.predecessor.update_successor(self.ref)

                    self.predecessor2 = self.predecessor.predecessor
                    self.predecessor3 = self.predecessor2.predecessor if self.predecessor2 else None

            except Exception as e:
                logging.error(f"Error in check_predecessor: {e}")
                self.predecessor = None
            time.sleep(5)

    # Store key method to store a key-value pair and replicate to the successor
    def store_key(self, key: str, value: str):
        key_hash = hash_function(key, self.m)
        node = self.find_successor(key_hash)
        node.store_key(key, value)
        # self.data[key] = value  # Store in the current node
        # self.successor.store_key(key, value)  # Replicate to the successor

    # Retrieve key method to get a value for a given key
    def retrieve_key(self, key: str) -> str:
        key_hash = hash_function(key, self.m)
        node = self.find_successor(key_hash)
        return node.retrieve_key(key)

    def get_data_from_predecessors(self):
        while True:

            if self.predecessor:
                _pred_data = self.predecessor.send_predecessor_data().decode()
                if _pred_data:
                    self.pred_data = json.loads(_pred_data)

            if self.predecessor2:
                if self.id != self.predecessor2.id:
                    self.pred2_data = ''

                    _pred2_data = self.predecessor2.send_predecessor_data().decode()
                    if _pred2_data:
                        self.pred2_data = json.loads(_pred2_data)

            logging.info(f'pred: {self.pred_data}, pred2: {self.pred2_data}')
            time.sleep(8)

    def update_tournament_sim(self, name, data):
        with self.lock:
            logging.info(f'RESULT SIM {data}')
            self.data[name] = data[name]

    def _simulate_tournament(self, t_name):
        logging.info(f'RUN TOURNAMENT {t_name} IN NODE: {self.id}')
        if t_name in self.data:
            t_data = copy.deepcopy(self.data[t_name])
            sim = TournamentSimulator(t_name, t_data, self.ref)
            sim.run_simulation()

    def simulate_tournament(self, tournament_name):
        key_hash = hash_function(tournament_name, self.m)
        node = self.find_successor(key_hash)
        if node:
            node.simulate_tournament(tournament_name)

    def send(self, id, data):
        if data:
            completed = data['completed']
            data = json.dumps(data)
            self.store_key(id, data)
            self.notify_tournament({'id': id, 'completed': completed})
            logging.info(f'{hash_function(id, self.m)}: {data} saved')

    def get(self, id):
        return self.retrieve_key(id)

    def update_data(self):
        while True:
            logging.info(f'my data is {self.data}')

            with self.lock:
                try:
                    for key, value in list(self.data.items()):
                        key_hash = hash_function(key, self.m)
                        node = self.find_successor(key_hash)
                        logging.info(f'update data: {key_hash} -> {node.id if node else ''}')

                        if node and node.id != self.id:
                            node.store_key(key, value)
                            # remove from current node
                            self.data.pop(key)

                    self.handler.create(self.id, self.data)
                except Exception as e:
                    logging.error(f"Error in update_data")
            time.sleep(10)

    # Start server method to handle incoming requests
    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            logging.info(f"Server: {self.ip}:{self.port}")
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.port))
            s.listen(10)

            while True:
                conn, addr = s.accept()
                logging.info(f'new connection from {addr}')
                _data = conn.recv(1024).decode()
                logging.info(f'data: {_data}')
                data = _data.split(',')
                data_resp = None
                option = int(data[0])

                if option == FIND_SUCCESSOR:
                    id = int(data[1])
                    if id and id != 'None':
                        data_resp = self.find_successor(id)
                elif option == FIND_PREDECESSOR:
                    id = int(data[1])
                    if id and id != 'None':
                        data_resp = self.find_predecessor(id)
                elif option == GET_SUCCESSOR:
                    data_resp = self.successor if self.successor else self.ref
                elif option == GET_PREDECESSOR:
                    logging.info(f'GET_PREDECESSOR {self.predecessor} {self.ref}')
                    data_resp = self.predecessor if self.predecessor else self.ref
                elif option == NOTIFY:
                    ip = data[2]
                    if ip and ip != 'None':
                        self.notify(ChordNodeReference(ip, self.port))
                elif option == CHECK:
                    conn.sendall("OK".encode())
                    conn.close()

                elif option == CLOSEST_PRECEDING_FINGER:
                    id = int(data[1])
                    if id and id != 'None':
                        data_resp = self.closest_preceding_finger(id)
                elif option == STORE_KEY:
                    key, value = _data.split('|')
                    value = value.replace("'", '"').replace("None", "null").replace("False", "false").replace("True",
                                                                                                              "true")
                    value = json.loads(value)
                    key = key.split(',')[1]
                    if key and value and key != 'None' and value != 'None':
                        self.data[key] = value
                elif option == RETRIEVE_KEY:
                    key = data[1]
                    if key and key != 'None':
                        resp = self.data.get(key, '')
                        conn.sendall(json.dumps(resp).encode())
                        conn.close()
                elif option == UPDATE_SUCCESSOR:
                    _ip = data[2]
                    if _ip and _ip != 'None':
                        self.update_successor(ChordNodeReference(_ip, self.port))
                elif option == UPDATE_PREDECESSOR:
                    _ip = data[2]
                    if _ip and _ip != 'None':
                        self.update_predecessor(ChordNodeReference(_ip, self.port))
                elif option == SEND_PREDECESSOR_DATA:
                    # _data = {'id': self.id, 'ip': self.ip, 'port': self.port}
                    conn.sendall(json.dumps(self.data).encode())
                    conn.close()

                elif option == SEND_TOURNAMENTS:
                    conn.sendall(json.dumps(self.tournaments).encode())
                    conn.close()
                elif option == SIMULATE_TOURNAMENT:
                    t_name = data[1]
                    conn.sendall(f'RUN TOURNAMENT {t_name}'.encode())
                    self._simulate_tournament(t_name)
                    conn.close()

                elif option == TOURNAMENT_RESULT:
                    t_name, t_data = _data.split('|')
                    t_data = json.loads(t_data)
                    t_name = key.split(',')[0]
                    self.update_tournament_sim(t_name, t_data)
                    conn.close()
                if data_resp:
                    response = f'{data_resp.id},{data_resp.ip}'.encode()
                    conn.sendall(response)
                conn.close()
