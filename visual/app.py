from flask import Flask, render_template, request, redirect, url_for
import random
import json
import os
from chord.node import ChordNode
import socket
import base64
app = Flask(__name__)

tournaments = []
node = None


@app.route("/")
def index():
    _tournaments = node.get_tournaments()
    _tournaments = json.loads(_tournaments) if len(_tournaments) else {}
    _tournaments_to_render = {}
    for key, value in _tournaments.items():
        _tournaments_to_render[key] = {'data': {'completed': value}}
    for t in tournaments:
        if t not in _tournaments_to_render:
            _tournaments_to_render[t] = {'data': {'completed': False}}
    return render_template("index.html", tournaments=_tournaments_to_render)


@app.route("/tournament/<tournament_name>")
def tournament(tournament_name):
    _tournament = node.get(tournament_name)
    _tournament = json.loads(_tournament) if len(_tournament) > 0 else {}
    _tournament_to_render = {'data': _tournament}
    return render_template(
        "tournament.html", tournament=_tournament_to_render, name=tournament_name
    )


@app.route("/add_player/<tournament_name>", methods=["POST"])
def add_player(tournament_name):
    player_name = request.form["player_name"]
    player_code = request.form['player_code']
    player_code_base64 = base64.b64encode(player_code.encode("utf-8")).decode("utf-8")

    _tournament = node.get(tournament_name)
    _tournament = json.loads(_tournament)
    if _tournament and not _tournament["completed"]:
        _tournament['players'].append({"name": player_name, "score": 0, 'code': player_code_base64})
    node.send(tournament_name, _tournament)
    return redirect(url_for("tournament", tournament_name=tournament_name))


@app.route("/create_tournament", methods=["POST"])
def create_tournament():
    tournament_name = request.form["tournament_name"]
    tournament_type = request.form["tournament_type"]  # New field for type
    if tournament_name not in tournaments:
        tournaments.append(tournament_name)
        new_tournament = {
            "type": tournament_type,
            "players": [],
            "games": [],
            "winner": None,
            "completed": False,
        }
        node.send(tournament_name, new_tournament)
    return redirect(url_for("index"))


@app.route("/start_tournament/<tournament_name>", methods=["POST"])
def start_tournament(tournament_name):
    node.simulate_tournament(tournament_name)
    return redirect(url_for("tournament", tournament_name=tournament_name))


if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    node = ChordNode(ip)
    app.run(debug=False, host=ip, port=5001)

    while True:
        pass
