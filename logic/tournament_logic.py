class Player:
    def __init__(self, name) -> None:
        self.name = name


class Tournament:
    def __init__(self, name, rounds, num_players) -> None:
        self.name = name
        self.rounds = rounds
        self.num_players = num_players
        self.players = []

    def add_player(self, player: Player):
        if self.players.count() > self.num_players:
            self.players.append(player)
            return "Player has been added"
        else:
            return "Tournament is full"
