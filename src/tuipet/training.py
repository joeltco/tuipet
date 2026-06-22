"""Training — DVPet's four drills, each its own minigame, rendered in the
display box (no pop-up). Faithful to DVPet's training states (Vaccine_Training,
Data_Training, Virus_Training, HP_Training) and config numbers:

  HP Drill  — best-of-3 attack rounds (cfg _hpTrainingRounds 3, won 2); builds Effort.
  Vaccine   — rapid-tap hit count    (cfg VaccineGameHitsMin 20); builds Vaccine power.
  Data      — shoot on the lit frame  (cfg DataTrainShootFrame 7); builds Data power.
  Virus     — stop the power bar high  (cfg VirusGameBarMin 86, speed 4); builds Virus power.

A drill picker opens first; training a non-favored attribute costs a little
mood (cfg NoneTrainingAttributeMoodRankChange), handled in Pet.apply_training.
"""
from __future__ import annotations
import random
from rich.text import Text
from . import data
from .render import render_screen
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, MID, ACCENT, SIL_DAY, SIL_NIGHT
from . import menu

# DVPet config (normal difficulty)
VACCINE_HITS_MIN = 20
VACCINE_WINDOW = 40            # fast-ticks (~5s at 0.12s/tick) to mash
VIRUS_BAR_MIN = 86
VIRUS_SPEED = 4
DATA_SHOOT_FRAME = 7
DATA_REPS = 3
DATA_SLOTS = 8
HP_ROUNDS = 3
HP_ROUNDS_WON = 2
HP_METER_W = 28
HP_ZONE_W = 6
VBAR_W = 28

GAMES = [
    ("hp",      "HP Drill", "Effort", "best of 3 — build Effort"),
    ("vaccine", "Vaccine",  "Vaccine", f"mash to {VACCINE_HITS_MIN} hits"),
    ("data",    "Data",     "Data",    "shoot on the lit frame"),
    ("virus",   "Virus",    "Virus",   f"stop the bar over {VIRUS_BAR_MIN}"),
]


class TrainingPanel:
    def __init__(self, pet):
        self.pet = pet
        self.phase = "menu"          # menu | play | done
        self.gi = 0
        self.frame_i = 0
        self.flash = "Pick a drill."
        self.result = None
        self.success = False
        self._reset()

    def _reset(self):
        self.pos = 0.0
        self.dir = 1
        self.rep = 0
        self.hits = 0
        self.power = 0
        self.zone = 0
        self.taps = 0
        self.timer = VACCINE_WINDOW
        self.rounds_won = 0
        self.slot = 0
        self.target = 0

    @property
    def gkey(self):
        return GAMES[self.gi][0]

    # ---- lifecycle ----
    def _start_game(self):
        self.phase = "play"
        self._reset()
        gk = self.gkey
        if gk == "hp":
            self._new_hp_zone()
            self.flash = f"Round 1/{HP_ROUNDS} — strike the zone!"
        elif gk == "vaccine":
            self.flash = f"Mash SPACE! reach {VACCINE_HITS_MIN}"
        elif gk == "data":
            self.target = random.randrange(DATA_SLOTS)
            self.flash = "Shoot on the lit frame!"
        else:
            self.flash = f"Stop the bar over {VIRUS_BAR_MIN}!"

    def _new_hp_zone(self):
        self.zone = random.randint(0, HP_METER_W - HP_ZONE_W)
        self.pos = 0.0
        self.dir = 1

    def _finish(self, hits, power, attribute, game):
        self.success = hits >= 2
        self.result = self.pet.apply_training(hits, power, attribute, game=game)
        self.phase = "done"
        self.flash = self.result + "   (SPACE)"

    # ---- anim (called each fast tick) ----
    def anim(self):
        self.frame_i += 1
        if self.phase != "play":
            return
        gk = self.gkey
        if gk == "hp":
            self.pos += self.dir * 2
            if self.pos >= HP_METER_W - 1:
                self.pos = HP_METER_W - 1
                self.dir = -1
            elif self.pos <= 0:
                self.pos = 0
                self.dir = 1
        elif gk == "vaccine":
            self.timer -= 1
            if self.timer <= 0:
                ratio = self.taps / VACCINE_HITS_MIN
                hits = 3 if ratio >= 1.2 else (2 if ratio >= 0.8 else (1 if ratio >= 0.4 else 0))
                self._finish(hits, int(self.taps), "Vaccine", "vaccine")
        elif gk == "data":
            if self.frame_i % 2 == 0:
                self.slot = (self.slot + 1) % DATA_SLOTS
        elif gk == "virus":
            self.pos += self.dir * VIRUS_SPEED
            if self.pos >= 100:
                self.pos = 100
                self.dir = -1
            elif self.pos <= 0:
                self.pos = 0
                self.dir = 1

    # ---- key ----
    def key(self, k):
        if self.phase == "menu":
            if k in ("up", "k"):
                self.gi = (self.gi - 1) % len(GAMES)
            elif k in ("down", "j"):
                self.gi = (self.gi + 1) % len(GAMES)
            elif k in ("1", "2", "3", "4"):
                self.gi = int(k) - 1
                self._start_game()
            elif k in ("enter", "space"):
                self._start_game()
            elif k in ("escape", "t"):
                return ("done", None)
            return None
        if self.phase == "done":
            if k in ("space", "enter", "escape", "t"):
                return ("done", self.result)
            return None
        # phase == play
        if k in ("escape", "t"):
            return ("done", None)
        if k == "space":
            self._strike()
        return None

    def _strike(self):
        gk = self.gkey
        if gk == "hp":
            center = self.zone + HP_ZONE_W // 2
            if abs(self.pos - center) <= HP_ZONE_W // 2:
                self.rounds_won += 1
                self.flash = "HIT!"
            else:
                self.flash = "missed."
            self.rep += 1
            if self.rep >= HP_ROUNDS:
                won = self.rounds_won
                hits = 3 if won >= 3 else (2 if won >= HP_ROUNDS_WON else won)
                self._finish(hits, 0, None, "hp")
            else:
                self.flash = f"Round {self.rep + 1}/{HP_ROUNDS} — {self.flash}"
                self._new_hp_zone()
        elif gk == "vaccine":
            self.taps += 1
            self.flash = f"{self.taps} hits!"
        elif gk == "data":
            dist = min((self.slot - self.target) % DATA_SLOTS,
                       (self.target - self.slot) % DATA_SLOTS)
            if dist == 0:
                self.hits += 1
                self.power += 18
                self.flash = "BULLSEYE!"
            elif dist == 1:
                self.hits += 1
                self.power += 10
                self.flash = "clipped it"
            else:
                self.flash = "missed"
            self.rep += 1
            if self.rep >= DATA_REPS:
                self._finish(self.hits, self.power, "Data", "data")
            else:
                self.target = random.randrange(DATA_SLOTS)
        elif gk == "virus":
            v = int(self.pos)
            if v >= VIRUS_BAR_MIN:
                self._finish(3, v, "Virus", "virus")
            elif v >= 60:
                self._finish(2, v, "Virus", "virus")
            elif v >= 35:
                self._finish(1, v // 2, "Virus", "virus")
            else:
                self._finish(0, 0, "Virus", "virus")

    # ---- sprite frame for the current game/phase ----
    def _sprite_idx(self):
        gk = self.gkey
        if self.phase == "done":
            return 6 if self.success else 9   # AttackSuccess=6 / AttackFail=9
        if gk == "data":
            return DATA_SHOOT_FRAME if self.slot == self.target else 4
        return [4, 6][self.frame_i % 2]

    # ---- render ----
    def text(self):
        rec = data.load_sprites()[1][self.pet.num]
        if self.phase == "menu":
            return self._render_menu()
        idx = self._sprite_idx()
        if idx >= len(rec["frames"]) or not rec["frames"][idx]:
            idx = 0
        rows = rec["frames"][idx] or rec["frames"][0]
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        sprite = render_screen(rows, 40, 7, on, LCD_BG, bgimg=bgimg)
        out = menu.bar("TRAINING", GAMES[self.gi][1])
        out.append(sprite)
        out.append("\n")
        out.append_text(self._render_hud())
        out.append_text(menu.note(self.flash))
        if self.phase == "done":
            hint = "SPACE done"
        elif self.gkey == "vaccine":
            hint = "SPACE mash   ESC stop"
        elif self.gkey == "data":
            hint = "SPACE shoot   ESC stop"
        else:
            hint = "SPACE strike   ESC stop"
        out.append_text(menu.footer(hint))
        return out

    def _render_menu(self):
        out = menu.bar("TRAINING", "pick a drill")
        for i, (gk, label, attr, blurb) in enumerate(GAMES):
            tag = "effort" if gk == "hp" else f"{attr[:4]} pow"
            out.append_text(menu.row(f"{label:<9} {tag}", i == self.gi))
        out.append_text(menu.blanks(5))
        out.append_text(menu.note(GAMES[self.gi][3]))
        out.append_text(menu.footer("↑↓ pick   ENTER start   ESC out"))
        return out

    def _render_hud(self):
        gk = self.gkey
        t = Text()
        if gk == "hp":
            t.append_text(self._meter(self.pos, self.zone, HP_METER_W, HP_ZONE_W))
            dots = "●" * self.rounds_won + "○" * (HP_ROUNDS - self.rep) + "·" * (self.rep - self.rounds_won)
            t.append(f"\nround {min(self.rep + 1, HP_ROUNDS)}/{HP_ROUNDS}   won {dots}\n", style=INK)
        elif gk == "vaccine":
            filled = int((self.timer / VACCINE_WINDOW) * 24)
            t.append("time ", style=INK)
            t.append("█" * filled + "░" * (24 - filled), style=f"{ACCENT} on {LCD_BG}")
            done = self.taps >= VACCINE_HITS_MIN
            t.append(f"\nhits {self.taps}/{VACCINE_HITS_MIN} {'●' if done else '○'}\n",
                     style=INK_B if done else INK)
        elif gk == "data":
            ring = Text()
            for s in range(DATA_SLOTS):
                if s == self.slot and s == self.target:
                    ring.append("◉ ", style=f"{ACCENT} on {LCD_BG}")
                elif s == self.target:
                    ring.append("+ ", style=INK_B)
                elif s == self.slot:
                    ring.append("● ", style=f"{ACCENT} on {LCD_BG}")
                else:
                    ring.append("· ", style=f"{MID} on {LCD_BG}")
            t.append_text(ring)
            dots = "●" * self.hits + "○" * (DATA_REPS - self.rep) + "·" * (self.rep - self.hits)
            t.append(f"\nshot {min(self.rep + 1, DATA_REPS)}/{DATA_REPS}   hits {dots}\n", style=INK)
        else:  # virus
            t.append_text(self._powerbar(self.pos))
            t.append(f"\npower {int(self.pos)}   need {VIRUS_BAR_MIN}\n", style=INK)
        return t

    def _meter(self, pos, zone, w, zw):
        m = Text()
        m.append("[", style=INK)
        for i in range(w):
            if i == int(pos):
                m.append("█", style=f"{ACCENT} on {LCD_BG}")
            elif zone <= i < zone + zw:
                m.append("▓", style=f"{LCD_ON} on {LCD_BG}")
            else:
                m.append("─", style=f"{MID} on {LCD_BG}")
        m.append("]", style=INK)
        return m

    def _powerbar(self, pos):
        m = Text()
        m.append("[", style=INK)
        fill = int(pos / 100 * VBAR_W)
        needx = int(VIRUS_BAR_MIN / 100 * VBAR_W)
        for i in range(VBAR_W):
            if i == needx:
                m.append("|", style=INK_B)
            elif i < fill:
                m.append("█", style=f"{ACCENT} on {LCD_BG}")
            else:
                m.append("─", style=f"{MID} on {LCD_BG}")
        m.append("]", style=INK)
        return m
