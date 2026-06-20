"""Training minigame: strike the power meter when the marker hits the target zone.

Faithful to DVPet's bar-based training — three reps raise the pet's effort and its
attribute power (Vaccine/Data/Virus). Built as a modal Textual screen.
"""
from __future__ import annotations
import random
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

from . import data
from .render import render_screen

METER_W = 30
ZONE_W = 5
REPS = 3
LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"


class TrainingScreen(ModalScreen):
    CSS = """
    TrainingScreen { align: center middle; }
    #train { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 36; height: 16; }
    """
    BINDINGS = [("space", "strike", "Strike"), ("escape", "cancel", "Stop"),
                ("1", "attr('Vaccine')", "Vaccine"), ("2", "attr('Data')", "Data"),
                ("3", "attr('Virus')", "Virus")]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.pos = 0
        self.dir = 1
        self.rep = 0
        self.hits = 0
        self.power = 0
        self.flash = "Strike at the target!"
        self.frame_i = 0
        self._new_zone()
        self.done = False
        self.result = None
        self.train_attr = pet.attribute if pet.attribute in ("Vaccine", "Data", "Virus") else "Vaccine"

    def action_attr(self, which):
        if not self.done:
            self.train_attr = which
            self.flash = f"Training {which}"
            self.render_view()

    def _new_zone(self):
        self.zone = random.randint(0, METER_W - ZONE_W)

    def compose(self):
        yield Static(id="train")

    def on_mount(self):
        self.view = self.query_one("#train", Static)
        self.pet.anim = "attack"
        self.set_interval(0.05, self.tick)
        self.set_interval(0.4, self.anim_tick)
        self.render_view()

    def anim_tick(self):
        self.frame_i += 1

    def tick(self):
        if self.done:
            return
        self.pos += self.dir
        if self.pos >= METER_W - 1:
            self.pos = METER_W - 1; self.dir = -1
        elif self.pos <= 0:
            self.pos = 0; self.dir = 1
        self.render_view()

    def action_strike(self):
        if self.done:
            self.dismiss(self.result); return
        center = self.zone + ZONE_W // 2
        dist = abs(self.pos - center)
        if dist == 0:
            self.hits += 1; self.power += 20; self.flash = "GREAT!"
        elif dist <= ZONE_W // 2:
            self.hits += 1; self.power += 12; self.flash = "good"
        else:
            self.flash = "miss"
        self.rep += 1
        if self.rep >= REPS:
            self.finish()
        else:
            self._new_zone()
        self.render_view()

    def action_cancel(self):
        self.dismiss(self.result if self.done else None)

    def finish(self):
        self.done = True
        self.result = self.pet.apply_training(self.hits, self.power, self.train_attr)
        self.flash = self.result + "  (SPACE to close)"

    def render_view(self):
        # pet doing attack animation on a small LCD band
        _, by_num = data.load_sprites()
        rec = by_num[self.pet.num]
        frames = data.ROLES.get("attack", [4])
        idx = frames[self.frame_i % len(frames)]
        rows = rec["frames"][idx] or rec["frames"][0]
        sprite = render_screen(rows, 30, 6, LCD_ON, LCD_BG)

        # meter
        cells = []
        for i in range(METER_W):
            in_zone = self.zone <= i < self.zone + ZONE_W
            if i == self.pos:
                cells.append(("#cc0000", "█"))          # marker
            elif in_zone:
                cells.append(("#0b3d0b", "▓"))          # target zone
            else:
                cells.append(("#5a7a1a", "─"))
        meter = Text()
        meter.append("[", style="#0b3d0b on #9bbc0f")
        for color, ch in cells:
            meter.append(ch, style=f"{color} on #9bbc0f")
        meter.append("]", style="#0b3d0b on #9bbc0f")

        dots = "●" * self.hits + "○" * (REPS - self.rep) + "·" * (self.rep - self.hits)
        out = Text()
        out.append("TRAINING\n", style="b #0b3d0b on #9bbc0f")
        out.append(sprite)
        out.append("\n")
        out.append(meter)
        out.append(f"\nrep {min(self.rep + 1, REPS)}/{REPS}   hits {dots}   train: {self.train_attr}\n",
                   style="#0b3d0b on #9bbc0f")
        out.append(f"{self.flash}\n", style="b #0b3d0b on #9bbc0f")
        out.append("SPACE strike  1/2/3 type  ESC stop", style="#5a7a1a on #9bbc0f")
        self.view.update(out)
