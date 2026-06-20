"""Tournament — a single-elimination bracket (quarter/semi/final) against
stage-appropriate opponents, faithful to DVPet's 8-entrant tourney. Win all three
matches to take the cup: a trophy plus scaled bits. Each match reuses the battle
engine, so tournament fights also count toward battle/win evolution requirements.
"""
from __future__ import annotations
from . import battle

ROUNDS = ["Quarterfinal", "Semifinal", "Final"]
BITS = {"Rookie": 60, "Champion": 120, "Ultimate": 220, "Mega": 400}


class Tournament:
    def __init__(self, pet):
        self.pet = pet
        self.name = f"{pet.stage} Cup"
        self.round = 0
        self.over = False
        self.champion = False
        self.reward_bits = 0
        # the final is a boss-tier opponent
        self.opponents = [battle.pick_enemy(pet, boss=(i == 2)) for i in range(3)]
        self.last = f"Welcome to the {self.name}!"

    @property
    def round_name(self):
        return ROUNDS[min(self.round, 2)]

    def current_opponent(self):
        return self.opponents[min(self.round, 2)]

    def record(self, won):
        if not won:
            self.over = True
            self.champion = False
            self.last = f"Eliminated in the {self.round_name}."
            return self.last
        self.round += 1
        if self.round >= 3:
            self.over = True
            self.champion = True
            self.reward_bits = BITS.get(self.pet.stage, 60)
            self.pet.bits += self.reward_bits
            self.pet.trophies += 1
            self.last = f"CHAMPION! +{self.reward_bits} bits and a trophy!"
        else:
            self.last = f"Won the {ROUNDS[self.round - 1]}! On to the {self.round_name}."
        return self.last
