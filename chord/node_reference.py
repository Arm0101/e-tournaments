import json
import logging
import time

from .codes import *
import socket
from .utils import hash_function

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')


class ChordNodeReference:
    def __init__(self, ip: str, port: int = 8001, m: int = 8):
        self.id = hash_function(ip, m)
        self.ip = ip
        self.port = port

    # Internal method to send data to the referenced node
    def _send_data(self, op: int, data: str = None) -> bytes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(20)
                s.connect((self.ip, self.port))
                logging.info(f"OP DATAAAAA{op},{data}")
                s.sendall(f'{op},{data}'.encode('utf-8'))
                logging.info(f"SEND ALLLLL")

                response = b''
                while True:
                    part = s.recv(4096)
                    if not part:
                        break
                    response += part
                logging.info(f"RESPONSEEEEEEEEEEE{response}")
                return response
        except Exception as e:
            logging.error(f"Error sending data: {e}")
            return b''

    def send_tournaments(self):
        return self._send_data(SEND_TOURNAMENTS)

    def simulate(self, name: str):
        return self._send_data(SIMULATE_TOURNAMENT, name)

    def update_tournament_result(self, name, data):
        return self._send_data(TOURNAMENT_RESULT, f'{name}|{json.dumps(data)}')

    def send_data(self):
        return self._send_data(SEND_DATA)

    def update_successor(self, node: 'ChordNodeReference'):
        self._send_data(UPDATE_SUCCESSOR, f'{node.id},{node.ip}')

    def update_predecessor(self, node: 'ChordNodeReference'):
        self._send_data(UPDATE_PREDECESSOR, f'{node.id},{node.ip}')

    # Method to find the successor of a given id
    def find_successor(self, id: int) -> 'ChordNodeReference':
        response = self._send_data(FIND_SUCCESSOR, str(id)).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Method to find the predecessor of a given id
    def find_predecessor(self, id: int) -> 'ChordNodeReference':
        response = self._send_data(FIND_PREDECESSOR, str(id)).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Property to get the successor of the current node
    @property
    def successor(self) -> 'ChordNodeReference':
        response = self._send_data(GET_SUCCESSOR).decode().split(',')
        if response[0] != '':
            return ChordNodeReference(response[1], self.port)

    # Property to get the predecessor of the current node
    @property
    def predecessor(self) -> 'ChordNodeReference':
        response = self._send_data(GET_PREDECESSOR).decode().split(',')
        if response[0] != '':
            return ChordNodeReference(response[1], self.port)

    # Method to notify the current node about another node
    def notify(self, node: 'ChordNodeReference'):
        self._send_data(NOTIFY, f'{node.id},{node.ip}')

    # Method to check if the predecessor is alive
    def check(self):
        return self._send_data(CHECK)

    # Method to find the closest preceding finger of a given id
    def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
        response = self._send_data(CLOSEST_PRECEDING_FINGER, str(id)).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Method to store a key-value pair in the current node
    def store_key(self, key: str, value: str):
        self._send_data(STORE_KEY, f'{key}|{value}')

    # Method to retrieve a value for a given key from the current node
    def retrieve_key(self, key: str) -> str:
        response = self._send_data(RETRIEVE_KEY, key).decode()
        return response

    def run_game(self, tournament: str, game: str):
        return self._send_data(RUN_GAME, f'|{tournament}|{game}')

    def __str__(self) -> str:
        return f'({self.ip},{self.port})'

    def __repr__(self) -> str:
        return str(self)
