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


@app.route("/")
def index():
    return render_template("index.html", tournaments=tournaments)


@app.route("/create_tournament", methods=["POST"])
def create_tournament():
    tournament_name = request.form["tournament_name"]
    if tournament_name not in tournaments:
        tournaments[tournament_name] = {
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
        tournaments[tournament_name][
            "completed"
        ] = True  # Marcar torneo como completado

        # Almacenar resultados en un archivo JSON
        save_results(tournament_name)
        save_tournaments()
    return redirect(url_for("tournament", tournament_name=tournament_name))


def save_results(tournament_name):
    results = {
        "tournament": tournament_name,
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
