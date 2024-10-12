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

        if len(players) < 2:
            return redirect(url_for("tournament", tournament_name=tournament_name))

        if tournaments[tournament_name]["type"] == "elimination":
            final_winner = simulate_elimination(players, tournament_name)
            tournaments[tournament_name]["winner"] = final_winner

        elif tournaments[tournament_name]["type"] == "round_robin":
            final_winner = simulate_round_robin(players, tournament_name)
            tournaments[tournament_name]["winner"] = final_winner

        elif tournaments[tournament_name]["type"] == "group_stage":
            groups = start_group_stage(players)  # Assume this function creates groups
            group_winners = simulate_group_stage(groups, tournament_name)
            tournaments[tournament_name]["winner"] = group_winners

        # Mark tournament as completed and save results.
        tournaments[tournament_name]["completed"] = True
        save_results(tournament_name)  # Save detailed results
        save_tournaments()  # Save overall tournament state

    return redirect(url_for("tournament", tournament_name=tournament_name))


def simulate_elimination(players, tournament_name):
    while len(players) > 1:
        random.shuffle(players)  # Shuffle players for random pairing
        next_round = []
        for i in range(0, len(players), 2):
            if i + 1 < len(players):  # Ensure there is a pair
                winner = random.choice([players[i], players[i + 1]])
                winner["score"] += 1  # Increment the winner's score
                next_round.append(winner)
                tournaments[tournament_name]["games"].append(
                    f"{players[i]['name']} vs {players[i + 1]['name']} - Winner: {winner['name']}"
                )
            else:
                next_round.append(
                    players[i]
                )  # Player without a pair advances automatically
        players = next_round
    return players[0]["name"]  # Return the final winner


# Return the final winner


def simulate_round_robin(players, tournament_name):
    scores = {
        player["name"]: player["score"] for player in players
    }  # Initialize scores

    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            winner = random.choice([players[i], players[j]])
            scores[winner["name"]] += 1

            # Update individual player's score in the original list
            for player in players:
                if player["name"] == winner["name"]:
                    player["score"] += 1

            tournaments[tournament_name]["games"].append(
                f"{players[i]['name']} vs {players[j]['name']} - Winner: {winner['name']}"
            )

    # Determine the overall winner based on scores
    max_score = max(scores.values())
    winners = [name for name, score in scores.items() if score == max_score]

    return (
        winners[0] if len(winners) == 1 else winners
    )  # Return a single winner or list of winners


def simulate_group_stage(groups):
    group_winners = {}

    for group_name, players in groups.items():
        winner = simulate_round_robin(players)
        group_winners[group_name] = winner

    return group_winners


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
