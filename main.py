import socket
from chord.node import ChordNode, ChordNodeReference
import logging
from chord.utils import hash_function
import time
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')

if __name__ == "__main__":
    print(hash_function('torneo1', 8))
    print(hash_function('torneo2', 8))
    print(hash_function('torneo3', 8))
    print(hash_function('torneo4', 8))
    print(hash_function('torneo5', 8))
    print(hash_function('torneo12', 8))
