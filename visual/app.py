from flask import Flask, render_template, request, redirect, url_for
import random
import json
import os

app = Flask(__name__)

# Estructura de datos para almacenar torneos y jugadores
tournaments = {}


# Cargar torneos desde un archivo JSON al iniciar la aplicación
def load_tournaments():
    if os.path.exists("tournaments.json"):
        with open("tournaments.json", "r") as f:
            return json.load(f)
    return {}


tournaments = load_tournaments()


def start_round_robin(players):
    games = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            games.append((players[i], players[j]))

    return games


def start_group_stage(players, group_size=4):
    random.shuffle(players)
    groups = [players[i : i + group_size] for i in range(0, len(players), group_size)]

    group_games = {}

    for index, group in enumerate(groups):
        group_games[f"Group {index + 1}"] = start_round_robin(group)

    return group_games


@app.route("/")
def index():
    return render_template("index.html", tournaments=tournaments)


@app.route("/create_tournament", methods=["POST"])
def create_tournament():
    tournament_name = request.form["tournament_name"]
    tournament_type = request.form["tournament_type"]  # New field for type
    if tournament_name not in tournaments:
        tournaments[tournament_name] = {
            "type": tournament_type,
            "players": [],
            "games": [],
            "winner": None,
            "completed": False,
        }
        save_tournaments()
    return redirect(url_for("index"))


@app.route("/add_player/<tournament_name>", methods=["POST"])
def add_player(tournament_name):
    player_name = request.form["player_name"]
    if tournament_name in tournaments and not tournaments[tournament_name]["completed"]:
        tournaments[tournament_name]["players"].append(
            {"name": player_name, "score": 0}
        )
        save_tournaments()  # Guardar cambios después de agregar un jugador
    return redirect(url_for("tournament", tournament_name=tournament_name))


@app.route("/start_tournament/<tournament_name>", methods=["POST"])
def start_tournament(tournament_name):
    if tournament_name in tournaments and not tournaments[tournament_name]["completed"]:
        players = tournaments[tournament_name]["players"]

        # Simulación de partidos: elige un ganador aleatorio
        if len(players) < 2:
            return redirect(
                url_for("tournament", tournament_name=tournament_name)
            )  # No se puede iniciar con menos de 2 jugadores

        if tournaments[tournament_name]["type"] == "elimination":
            while len(players) > 1:
                random.shuffle(
                    players
                )  # Mezclar los jugadores para emparejarlos aleatoriamente
            next_round = []
            for i in range(0, len(players), 2):
                if i + 1 < len(players):  # Asegurarse de que haya un par
                    winner = random.choice([players[i], players[i + 1]])
                    winner["score"] += 1  # Incrementar el puntaje del ganador
                    next_round.append(winner)
                    tournaments[tournament_name]["games"].append(
                        f"{players[i]['name']} vs {players[i + 1]['name']} - Ganador: {winner['name']}"
                    )
                else:
                    next_round.append(
                        players[i]
                    )  # Jugador sin pareja avanza automáticamente

            players = next_round

        final_winner = players[0]["name"]
        tournaments[tournament_name]["winner"] = final_winner
        tournaments[tournament_name]["completed"] = True

    elif tournaments[tournament_name]["type"] == "round_robin":
        games = start_round_robin(players)
        tournaments[tournament_name]["games"].extend(games)
    elif tournaments[tournament_name]["type"] == "group_stage":
        group_games = start_group_stage(players)
        tournaments[tournament_name]["games"].append(group_games)

    # Mark tournament as completed if needed and save results.
    tournaments[tournament_name]["completed"] = True
    save_results(tournament_name)
    save_tournaments()

    return redirect(url_for("tournament", tournament_name=tournament_name))


def save_results(tournament_name):
    results = {
        "tournament": tournament_name,
        "type": tournaments[tournament_name]["type"],  # Save tournament type
        "players": tournaments[tournament_name]["players"],
        "winner": tournaments[tournament_name]["winner"],
        "games": tournaments[tournament_name]["games"],
        "completed": tournaments[tournament_name]["completed"],
    }

    with open(f"{tournament_name}_results.json", "w") as f:
        json.dump(results, f, indent=4)


def save_tournaments():
    with open("tournaments.json", "w") as f:
        json.dump(tournaments, f, indent=4)


@app.route("/set_winner/<tournament_name>", methods=["POST"])
def set_winner(tournament_name):
    winner_name = request.form["winner_name"]
    if tournament_name in tournaments and not tournaments[tournament_name]["completed"]:
        tournaments[tournament_name]["winner"] = winner_name
        tournaments[tournament_name][
            "completed"
        ] = True  # Marcar torneo como completado
        save_results(tournament_name)  # Guardar resultados en archivo
        save_tournaments()  # Guardar estado de torneos
    return redirect(url_for("index"))


@app.route("/tournament/<tournament_name>")
def tournament(tournament_name):
    tournament_data = tournaments.get(tournament_name)
    return render_template(
        "tournament.html", tournament=tournament_data, name=tournament_name
    )


if __name__ == "__main__":
    app.run(debug=True)
