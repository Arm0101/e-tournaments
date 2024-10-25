import random


def play():
    plays = ["Scissors", "Rock", "Paper"]
    x = random.randint(0, 2)
    return plays[x]
