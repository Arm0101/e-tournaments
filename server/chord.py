import socket
import threading
import hashlib


class Node:
    def __init__(self, id, port) -> None:
        self.id = id
        self.port = port
        self.successor = self
        self.predecessor = None
        self.finger_table = [self] * 10
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", self.port))
        self.server_socket.listen(5)
        self.active = True
        threading.Thread(target=self.listen_for_connections).start()

    def listen_for_connections(self):
        while self.active:
            conn, addr = self.server_socket.accept()
            print(f"Connection accepted from {addr}")
            threading.Thread(target=self.handle_connection, args=(conn,)).start()

    def handle_connection(self, conn):
        data = conn.recv(1024).decode()
        print(f"Received data: {data}")
        if data.startswith("FIND_SUCCESSOR"):
            id = int(data.split()[1])
            successor = self.find_successor(id)
            conn.send(str(successor.id).encode())
            print(f"Sent successor ID: {successor.id}")
        conn.close()

    def find_successor(self, id):
        if self.id == self.successor.id:
            return self
        if self.id < id <= self.successor.id:
            return self.successor
        else:
            node = self.closest_preceding_node(id)
            if node == self:
                return self.successor
            return node.find_successor(id)

    def closest_preceding_node(self, id):
        for finger in reversed(self.finger_table):
            if self.id < finger.id < id:
                return finger
        return self

    def send_find_successor(self, node, id):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", node.port))
        client_socket.send(f"FIND_SUCCESSOR {id}".encode())
        print(f"Sent FIND_SUCCESSOR request to node {node.id} for ID {id}")
        successor_id = int(client_socket.recv(1024).decode())
        client_socket.close()
        print(f"Received successor ID: {successor_id}")
        return Node(successor_id, node.port)

    def join(self, node):
        if node:
            self.predecessor = None
            self.successor = node.find_successor(self.id)
            print(f"Node {self.id} joined the network via node {node.id}")
        else:
            self.predecessor = self
            self.successor = self
            print(f"Node {self.id} initialized as the first node in the network")

    def stabilize(self):
        x = self.successor.predecessor
        if x and self.id < x.id < self.successor.id:
            self.successor = x
        self.successor.notify(self)
        print(f"Node {self.id} stabilized")

    def notify(self, node):
        if self.predecessor is None or self.id < node.id < self.predecessor.id:
            self.predecessor = node
        print(f"Node {self.id} notified by node {node.id}")

    def fix_fingers(self):
        for i in range(len(self.finger_table)):
            start = (self.id + 2**i) % (2**160)
            self.finger_table[i] = self.find_successor(start)
        print(f"Node {self.id} fixed fingers")

    def print_status(self):
        print(f"Node ID: {self.id}")
        print(f"Successor: {self.successor.id}")
        print(f"Predecessor: {self.predecessor.id if self.predecessor else None}")
        print("Finger Table:")
        for i, finger in enumerate(self.finger_table):
            print(f"  {i}: {finger.id}")
        print()

    def disconnect(self):
        self.active = False
        self.server_socket.close()
        print(f"Node {self.id} disconnected")


def hash_function(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16) % (2**160)


nodes = [Node(hash_function(f"node{i}"), 5000 + i) for i in range(10)]

# Unir los nodos a la red
nodes[0].join(None)
for i in range(1, len(nodes)):
    nodes[i].join(nodes[0])

# Estabilizar y actualizar las tablas de dedos
for node in nodes:
    node.stabilize()

for node in nodes:
    node.fix_fingers()

# Imprimir el estado de los nodos
for node in nodes:
    node.print_status()

# Desconectar 9 nodos
for i in range(1, 10):
    nodes[i].disconnect()

# Estabilizar y actualizar las tablas de dedos nuevamente
nodes[0].stabilize()
nodes[0].fix_fingers()

# Imprimir el estado del nodo restante
nodes[0].print_status()
