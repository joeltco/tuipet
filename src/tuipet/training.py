"""Training minigame: strike the meter when the marker hits the target zone.
Rendered in the display box (no pop-up)."""
from __future__ import annotations
import random
from rich.text import Text
from . import data
from .render import render_screen

METER_W = 30
ZONE_W = 5
REPS = 3
LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"


class TrainingPanel:
    def __init__(self, pet):
        self.pet = pet
        self.pos = 0
        self.dir = 1
        self.rep = 0
        self.hits = 0
        self.power = 0
        self.flash = "Strike at the target!"
        self.frame_i = 0
        self.done = False
        self.result = None
        self.train_attr = pet.attribute if pet.attribute in ("Vaccine", "Data", "Virus") else "Vaccine"
        self._new_zone()

    def _new_zone(self):
        self.zone = random.randint(0, METER_W - ZONE_W)

    def anim(self):
        self.frame_i += 1
        if self.done:
            return
        self.pos += self.dir * 2
        if self.pos >= METER_W - 1:
            self.pos = METER_W - 1; self.dir = -1
        elif self.pos <= 0:
            self.pos = 0; self.dir = 1

    def key(self, k):
        if k == "space":
            if self.done:
                return ("done", self.result)
            self._strike()
        elif k in ("escape", "t"):
            return ("done", self.result if self.done else None)
        elif k in ("1", "2", "3") and not self.done:
            self.train_attr = {"1": "Vaccine", "2": "Data", "3": "Virus"}[k]
            self.flash = f"Training {self.train_attr}"
        return None

    def _strike(self):
        center = self.zone + ZONE_W // 2
        dist = abs(self.pos - center)
        if dist <= 1:
            self.hits += 1; self.power += 20; self.flash = "GREAT!"
        elif dist <= ZONE_W // 2 + 1:
            self.hits += 1; self.power += 12; self.flash = "good"
        else:
            self.flash = "miss"
        self.rep += 1
        if self.rep >= REPS:
            self.done = True
            self.result = self.pet.apply_training(self.hits, self.power, self.train_attr)
            self.flash = self.result + "  (SPACE)"
        else:
            self._new_zone()

    def text(self):
        rec = data.load_sprites()[1][self.pet.num]
        frames = data.ROLES.get("attack", [4])
        idx = frames[self.frame_i % len(frames)]
        rows = rec["frames"][idx] or rec["frames"][0]
        sprite = render_screen(rows, 34, 7, LCD_ON, LCD_BG)
        meter = Text()
        meter.append("[", style=INK)
        for i in range(METER_W):
            in_zone = self.zone <= i < self.zone + ZONE_W
            if i == self.pos:
                meter.append("█", style=f"#cc0000 on {LCD_BG}")
            elif in_zone:
                meter.append("▓", style=f"#0b3d0b on {LCD_BG}")
            else:
                meter.append("─", style=f"#5a7a1a on {LCD_BG}")
        meter.append("]", style=INK)
        dots = "●" * self.hits + "○" * (REPS - self.rep) + "·" * (self.rep - self.hits)
        out = Text()
        out.append("TRAINING\n", style=INK_B)
        out.append(sprite)
        out.append("\n")
        out.append(meter)
        out.append(f"\nrep {min(self.rep + 1, REPS)}/{REPS}  hits {dots}  {self.train_attr}\n", style=INK)
        out.append(f"{self.flash}\n", style=INK_B)
        out.append("SPACE strike  1/2/3 type  ESC stop", style=DIM)
        return out
