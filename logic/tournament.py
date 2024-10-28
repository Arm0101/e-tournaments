import threading
import time
import random
import logging
from chord.node_reference import ChordNodeReference
import base64
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')


def get_winner(result1, result2):
    if result1 == 'rock' and result2 == 'paper':
        return 1
    if result1 == 'rock' and result2 == 'scissor':
        return 0
    if result1 == 'rock' and result2 == 'rock':
        return 1  # ???

    if result1 == 'paper' and result2 == 'scissor':
        return 1
    if result1 == 'paper' and result2 == 'rock':
        return 0
    if result1 == 'paper' and result2 == 'paper':
        return 1

    if result1 == 'scissor' and result2 == 'scissor':
        return 1
    if result1 == 'scissor' and result2 == 'rock':
        return 1
    if result1 == 'scissor' and result2 == 'paper':
        return 0
class TournamentSimulator:
    @staticmethod
    def generate_games(players, tournament_type="elimination"):
        games = []

        if tournament_type == "elimination":
            players_copy = players[:]

            for player in players_copy:
                if "active" not in player:
                    player["active"] = True
                if "next_round" not in player:
                    player["next_round"] = False

            active_players = [p for p in players_copy if p["active"]]

            if not active_players:
                next_round = [p for p in players_copy if p["next_round"]]
                if len(next_round) == 1:
                    return games
                else:
                    active_players = next_round

            if len(active_players) == 1:
                active_players = [p for p in players_copy if p["next_round"] or p['active']]
                for player in active_players:
                    player["active"] = True

            random.shuffle(active_players)
            while len(active_players) > 1:
                p1 = active_players.pop()
                p2 = active_players.pop()
                game_info = {
                    "player1": {p1["name"]: p1["score"]},
                    "player2": {p2["name"]: p2["score"]}
                }
                games.append(game_info)

        return games

    @staticmethod
    def simulate_game(tournament, players, node):
        logging.info(f'SIMULATING GAME {players} ({tournament['name']})')
        player1 = players['player1']
        player2 = players['player2']
        player1_code = ''
        player2_code = ''
        for p in tournament['players']:
            if p['name'] == list(player1.keys())[0]:
                player1_code = p['code']
            elif p['name'] == list(player2.keys())[0]:
                player2_code = p['code']

        decoded_code_1 = base64.b64decode(player1_code).decode("utf-8")
        decoded_code_2 = base64.b64decode(player2_code).decode("utf-8")
        player1_result = ''
        player2_result = ''

        namespace1 = {}
        exec(decoded_code_1, namespace1)

        if "play" in namespace1:
            result = namespace1["play"]()
            player1_result = result

        namespace2 = {}
        exec(decoded_code_2, namespace2)

        if "play" in namespace2:
            result = namespace2["play"]()
            player2_result = result
        winner = get_winner(player1_result, player2_result)
        if winner == 0:
            players = [player1, player2]
        else:
            players = [player2, player1]

        logging.info(f'WINNER {players[0]}')
        time.sleep(5)
        node.update_tournament_sim(name=tournament['name'], data={'winner': players[0], 'l': players[1]})
        return players

