import socket
from chord.node import ChordNode
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')

if __name__ == "__main__":

    ip = socket.gethostbyname(socket.gethostname())
    node = ChordNode(ip)
    logging.info('ip')
    logging.info(ip)
    while True:
        pass
