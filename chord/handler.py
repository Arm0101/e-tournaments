import logging
import os

current_dir = os.getcwd()
db_path = os.path.join(os.path.dirname(__file__), '../db')
import json


class Handler:
    def __init__(self, id):
        self.id = id
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        self.db_folder = os.path.join(db_path, str(self.id))
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

    def initial_data(self):
        file = os.path.join(self.db_folder, f"{self.id}.json")
        if os.path.isfile(file):
            with open(file, 'r') as archivo:
                return json.load(archivo)
        return {}

    def create(self, id, data):
        json_file = os.path.join(self.db_folder, f"{id}.json")
        with open(json_file, 'w') as file:
            json.dump(data, file)

        logging.info(f'data created in file {json_file}')
