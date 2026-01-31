import random

class Game:
    def __init__(self):
        self.players = {}  # user_id -> stats

    def start_player(self, user_id):
        if user_id not in self.players:
            self.players[user_id] = {"score": 0, "shots": 0, "made": 0}
            return True
        return False

    def shoot(self, user_id):
        if user_id not in self.players:
            return {"error": "not_started"}
        self.players[user_id]["shots"] += 1
        r = random.random()
        # simple probabilities: 40% miss, 40% 2-pointer, 20% 3-pointer
        if r < 0.4:
            return {"result": "miss", "points": 0}
        elif r < 0.8:
            self.players[user_id]["made"] += 1
            self.players[user_id]["score"] += 2
            return {"result": "2pt", "points": 2}
        else:
            self.players[user_id]["made"] += 1
            self.players[user_id]["score"] += 3
            return {"result": "3pt", "points": 3}

    def stats(self, user_id):
        return self.players.get(user_id, None)
