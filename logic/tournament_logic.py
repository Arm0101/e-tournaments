import random


class Player:
    def __init__(self, name, points=0, subscribed=False) -> None:
        self.name = name
        self.points = points
        self.subscribed = subscribed


class Tournament:
    def __init__(self, name, rounds, num_players, started=False) -> None:
        self.name = name
        self.rounds = rounds
        self.num_players = num_players
        self.players = []
        self.started = started

    def start_tournament(self):
        self.started = True
        for player in self.players:
            player.subscribed = True
            player.points = 0

    def add_player(self, player: Player):
        if (
            len(self.players) <= self.num_players
            and player.subscribed == False
            and not self.started
        ):
            self.players.append(player)
            print(f"Player {player.name} has been added")
        else:
            print(
                "Tournament is full or started or player is already in another tournament"
            )

    def simulate(self):
        for r in range(self.rounds):
            for player in self.players:
                player.points = random.randint(3, 10)
        print("tournament simulated")

    def set_winner(self):
        winner = self.players[0]
        for player in self.players:
            if winner.points < player.points:
                winner = player
        for player in self.players:
            player.subscribed = False
        return winner


player1 = Player("Abdel")
player2 = Player("Dayelin")
player3 = Player("Arian")
tournament = Tournament("torneo 1", 10, 3)
tournament.add_player(player1)
# tournament.start_tournament()
tournament.add_player(player2)
tournament.add_player(player3)
tournament.simulate()
print(f"The winner in the {tournament.name} is {tournament.set_winner().name}")
