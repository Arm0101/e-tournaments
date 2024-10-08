import socket
import threading
import time
import logging

from .codes import *
from .node_reference import ChordNodeReference
from .utils import hash_function, _inbetween

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')
BROADCAST_PORT = 9001


class ChordNode:
    def __init__(self, ip: str, port: int = 8001, m: int = 160):
        self.id = hash_function(ip)
        self.ip = ip
        self.port = port
        self.ref = ChordNodeReference(self.ip, self.port)
        self.successor = self.ref
        self.predecessor = None
        self.m = m
        self.finger = [self.ref] * self.m
        self.next = 0  # Finger table index to fix next
        self.data = {}  # Dictionary to store key-value pairs
        self.pred_data = {}
        self.pred2_data = {}

        # Start background threads for stabilization, fixing fingers, and checking predecessor
        threading.Thread(target=self.listen_for_broadcast, daemon=True).start()
        threading.Thread(target=self.stabilize, daemon=True).start()  # Start stabilize thread
        threading.Thread(target=self.fix_fingers, daemon=True).start()  # Start fix fingers thread
        threading.Thread(target=self.check_predecessor, daemon=True).start()  # Start check predecessor thread
        threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
        threading.Thread(target=self.get_data_from_predecessors, daemon=True).start()
        self.send_broadcast_join()

    def handle_join(self, node_id: int, node_ip: str, node_port: int):
        logging.info(f"Handle JOIN of {node_id}: {node_port}")
        new_node_ref = ChordNodeReference(node_ip, node_port)
        logging.info(new_node_ref)
        if node_id != self.id:

            if ((self.predecessor is None and self.id > new_node_ref.id) or
                    _inbetween(node_id, self.predecessor.id, self.id)):
                self.predecessor = new_node_ref

                self.predecessor.update_successor(self.ref)
                logging.info(f"Update predecessor to {self.predecessor}")

            if ((self.successor.id == self.ref.id and self.successor.id < new_node_ref.id) or
                    _inbetween(node_id, self.id, self.successor.id)):
                self.successor = new_node_ref
                self.successor.update_predecessor(self.ref)
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
        return node.successor  # Return successor of that node

    # Method to find the predecessor of a given id
    def find_predecessor(self, id: int) -> 'ChordNodeReference':
        node = self
        while not _inbetween(id, node.id, node.successor.id):
            node = node.closest_preceding_finger(id)
        return node

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
                if self.successor.id != self.id:
                    logging.info('stabilize')
                    logging.info(f'successor for {self.ref} is {self.successor}')
                    x = self.successor.predecessor
                    logging.info(f'predecessor of successor: {x}')
                    if x and x.id != self.id:
                        if _inbetween(x.id, self.id, self.successor.id):
                            self.successor = x
                        self.successor.notify(self.ref)
            except Exception as e:
                logging.error(f"Error in stabilize: {e}")
            logging.info(f"successor : {self.successor} predecessor {self.predecessor}")
            time.sleep(10)

    # Notify method to inform the node about another node
    def notify(self, node: 'ChordNodeReference'):
        logging.info('in notify')
        if node.id == self.id:
            pass
        if not self.predecessor or _inbetween(node.id, self.predecessor.id, self.id):
            self.predecessor = node

    # Fix fingers method to periodically update the finger table
    def fix_fingers(self):
        while True:
            try:
                self.next += 1
                if self.next >= self.m:
                    self.next = 0
                self.finger[self.next] = self.find_successor((self.id + 2 ** self.next) % 2 ** self.m)
            except Exception as e:
                logging.error(f"Error in fix_fingers: {e}")
            time.sleep(10)

    # Check predecessor method to periodically verify if the predecessor is alive
    def check_predecessor(self):
        while True:
            try:
                logging.info(f'pred: {self.predecessor}')
                if self.predecessor:
                    resp = self.predecessor.check_predecessor()
                    logging.info(f'resp from: {self.predecessor} is {resp}')
                    if resp == b'':
                        self.predecessor = self.find_predecessor(self.predecessor.id)
                        logging.info(f'new pred : {self.predecessor}')
                        self.predecessor.update_successor(self.ref)

            except Exception as e:
                logging.error(f"Error in check_predecessor: {e}")
                self.predecessor = None
            time.sleep(5)

    # Store key method to store a key-value pair and replicate to the successor
    def store_key(self, key: str, value: str):
        key_hash = hash_function(key)
        node = self.find_successor(key_hash)
        node.store_key(key, value)
        self.data[key] = value  # Store in the current node
        self.successor.store_key(key, value)  # Replicate to the successor

    # Retrieve key method to get a value for a given key
    def retrieve_key(self, key: str) -> str:
        key_hash = hash_function(key)
        node = self.find_successor(key_hash)
        return node.retrieve_key(key)

    def get_data_from_predecessors(self):
        while True:
            if self.predecessor and self.predecessor.id != self.id:

                self.pred_data = self.predecessor.send_predecessor_data().decode()
                pred2 = self.find_predecessor(self.predecessor.id)

                self.pred2_data = ''

                if pred2 and self.id != pred2.id and self.predecessor.id != pred2.id:
                    self.pred2_data = pred2.send_predecessor_data().decode()

            logging.info(f'pred: {self.pred_data}, pred2: {self.pred2_data}')
            time.sleep(5)

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

                data = conn.recv(1024).decode().split(',')

                data_resp = None
                option = int(data[0])

                if option == FIND_SUCCESSOR:
                    id = int(data[1])
                    data_resp = self.find_successor(id)
                elif option == FIND_PREDECESSOR:
                    id = int(data[1])
                    data_resp = self.find_predecessor(id)
                elif option == GET_SUCCESSOR:
                    data_resp = self.successor if self.successor else self.ref
                elif option == GET_PREDECESSOR:
                    logging.info(f'GET_PREDECESSOR {self.predecessor} {self.ref}')
                    data_resp = self.predecessor if self.predecessor else self.ref
                elif option == NOTIFY:
                    ip = data[2]
                    self.notify(ChordNodeReference(ip, self.port))
                elif option == CHECK_PREDECESSOR:
                    conn.sendall("OK".encode())
                    conn.close()

                elif option == CLOSEST_PRECEDING_FINGER:
                    id = int(data[1])
                    data_resp = self.closest_preceding_finger(id)
                elif option == STORE_KEY:
                    key, value = data[1], data[2]
                    self.data[key] = value
                elif option == RETRIEVE_KEY:
                    key = data[1]
                    data_resp = self.data.get(key, '')
                elif option == UPDATE_SUCCESSOR:
                    _ip = data[2]
                    self.update_successor(ChordNodeReference(_ip, self.port))
                elif option == UPDATE_PREDECESSOR:
                    _ip = data[2]
                    self.update_predecessor(ChordNodeReference(_ip, self.port))
                elif option == SEND_PREDECESSOR_DATA:
                    logging.info(f'Sending data from {self.ip}:{self.port}')
                    conn.sendall(f'DATA: {self.id} {self.ip},{self.port}'.encode())
                    conn.close()
                if data_resp:
                    response = f'{data_resp.id},{data_resp.ip}'.encode()
                    conn.sendall(response)
                conn.close()
