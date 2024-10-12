import os

current_dir = os.getcwd()
db_path = os.path.join(os.path.dirname(__file__), '../db')
import pickle


class Handler:
    def __init__(self, id):
        self.id = id
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        self.db_folder = os.path.join(db_path, str(self.id))
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

    def data(self):
        return f'Send data from : {self.id}'

    def create(self, id, data):
        folder = os.path.join(self.db_folder, str(id))
        if not os.path.exists(folder):
            os.makedirs(folder)
