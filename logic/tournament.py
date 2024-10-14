import threading
import time
import random
import logging
from chord.node_reference import ChordNodeReference

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')


class TournamentSimulator:
    def __init__(self, tournament_id, tournament_data, node: 'ChordNodeReference'):
        self.tournament_id = tournament_id
        self.data_t = {tournament_id: tournament_data}
        self.lock = threading.Lock()
        self.node = node

    def simulate_elimination_tournament(self):
        while not self.data_t[self.tournament_id]["completed"]:
            with self.lock:
                players = self.data_t[self.tournament_id]["players"]
                if not players: return

                if self.data_t[self.tournament_id]["winner"] is not None:
                    break

                next_round = []

                for player in players:
                    if "active" not in player:
                        player["active"] = True

                active_players = [p for p in players if p.get("active", True)]

                if len(active_players) < 2:
                    self.data_t[self.tournament_id]["winner"] = active_players[0]["name"]
                    self.data_t[self.tournament_id]["completed"] = True
                    self.node.update_tournament_result(self.tournament_id, self.data_t)
                    break

                random.shuffle(active_players)

                while len(active_players) > 1:
                    p1 = active_players.pop()
                    p2 = active_players.pop()

                    game_info = f"{p1['name']} vs {p2['name']} - Pending"
                    self.data_t[self.tournament_id]["games"].append(game_info)

                    winner = random.choice([p1, p2])
                    winner["score"] += 1

                    next_round.append(winner)

                    game_info = f"{p1['name']} vs {p2['name']} - Winner: {winner['name']}"
                    self.data_t[self.tournament_id]["games"][-1] = game_info

                if active_players:
                    next_round.append(active_players[0])

                for player in players:
                    player["active"] = player in next_round
            logging.info('updating tournament result')
            self.node.update_tournament_result(self.tournament_id, self.data_t)

            if len([p for p in players if p['active']]) < 2:
                continue
            time.sleep(10)

    def run_simulation(self):
        threading.Thread(target=self.simulate_elimination_tournament, daemon=True).start()

