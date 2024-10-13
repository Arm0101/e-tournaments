import socket
from chord.node import ChordNode, ChordNodeReference
import logging
from chord.utils import hash_function
import time
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    node = ChordNode(ip)
    node.send(f't01', {'data': f'ajsdnkjasndkjasndkjas'})
    logging.info(f'ALL TOURNAMENTS {node.get_tournaments()}')
    while True:
        pass
