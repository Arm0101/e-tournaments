import socket
from chord.node import ChordNode, ChordNodeReference
import logging
from chord.utils import hash_function

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    node = ChordNode(ip)
    node.send(f'aaaaaaa{ip}', {'data': f'aaaaaaa{ip}'})
    while True:
        pass
