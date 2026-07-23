"""Discipline — praise & scold, RESTORED (canon restoration B,
2026-07-23, Joel: "it was wrongfully stripped... whatever is canon
bring back").

The device pair as a two-row picker: PRAISE answers a proud moment (a
battle win, a mega drill — a ~10 game-min window), SCOLD answers the
tantrum call.  The gauge is obedience 0..100.  Wrong-moment verbs cost
nothing but land nothing (the no-praise-farming rule); refusals stay
soft — discipline is the tantrum economy, not a leash.
"""
from __future__ import annotations

from . import menu
from .theme import INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)

_ROWS = (
    ("Praise", "warmth for a proud moment"),
    ("Scold", "answer the tantrum call"),
)


class DisciplinePanel:
    def __init__(self, pet):
        self.pet = pet
        self.cursor = 1 if pet.discipline_call else 0   # an open call preselects Scold
        self.frame_i = 0
        self.sfx = None

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return menu.hints(("ENTER", "apply"), ("ESC", "back"))

    def key(self, k):
        if k in ("up", "down", "j", "k"):
            self.cursor = 1 - self.cursor
        elif k in ("enter", "space"):
            p = self.pet
            msg = p.praise() if self.cursor == 0 else p.scold()
            return ("done", str(msg))
        elif k == "escape":
            return ("done", None)
        return None

    def _state_line(self):
        p = self.pet
        if p.discipline_call:
            return "it is ACTING UP — a scold lands"
        if p.world_seconds <= getattr(p, "praise_window", 0.0):
            return "a PROUD moment — praise lands"
        return "all calm — neither will land"

    def text(self):
        out = menu.header("DISCIPLINE", f"manners {self.pet.obedience}/100")
        for i, (label, desc) in enumerate(_ROWS):
            sel = i == self.cursor
            out.append(f" {'▸' if sel else ' '} {label:<8}", style=SEL if sel else INK_B)
            out.append(f"{desc}\n", style=DIM)
        out.append("\n")
        out.append(f" {self._state_line()}\n", style=INK)
        out.append_text(menu.blanks(9 - 4))
        out.append_text(menu.footer("ENTER apply  ↑↓ pick  ESC out"))
        return out
