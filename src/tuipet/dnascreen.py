"""DNA charging screen (DVPet DNA_Inventory / DNA_Generate / DNA_Detail).

Bank Field-DNA by spending bits (generate), then charge it into the pet (apply).
Charged DNA shifts evolution toward forms whose Field-DNA requirements you meet —
DVPet's evolution-requirement bypass. Charging off your own Field costs more spirit,
sours mood, and risks illness (PhysicalState.applyDNA).
"""
from __future__ import annotations
from . import data, menu
from .pet import MAX_DNA_INVENTORY


class DNAPanel:
    def __init__(self, pet):
        self.pet = pet
        self.fields = list(data.DNA_FIELDS)
        self.cursor = 0
        self.amount = 1
        self.frame_i = 0
        self.last = "Generate DNA (G), then charge it in (ENTER)."
        self.sfx = None

    @property
    def field(self):
        return self.fields[self.cursor]

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        p = self.pet
        f = self.field
        self.sfx = None
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.fields)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.fields)
        elif k in ("left", "h"):
            self.amount = max(1, self.amount - 1)
        elif k in ("right", "l"):
            self.amount = min(MAX_DNA_INVENTORY, self.amount + 1)
        elif k == "g":                                   # generate: bits -> banked
            room = MAX_DNA_INVENTORY - p.dna_owned.get(f, 0)
            amt = min(self.amount, p.bits, room)
            if amt <= 0:
                self.last = "Need bits, or field is full (99)."
                self.sfx = "error"
            elif p.generate_dna(f, amt):
                self.last = f"Banked {amt} {f} DNA (−{amt}b)."
                self.sfx = "select"
        elif k in ("enter", "space"):                    # charge: banked -> applied
            amt = min(self.amount, p.dna_owned.get(f, 0))
            if amt <= 0:
                self.last = "No banked DNA — generate first (G)."
                self.sfx = "error"
            elif p.apply_dna(f, amt):
                same = f == p.field
                self.last = f"Charged {amt} {f}! ({'own' if same else 'off'}-field)"
                self.sfx = "compatible"
        elif k in ("escape", "x", "q"):
            return ("done", None)
        return None

    def text(self):
        p = self.pet
        out = menu.bar("DNA", f"{p.bits}b   charge x{self.amount}")
        for i, f in enumerate(self.fields):
            own = p.dna_owned.get(f, 0)
            chg = p.dna_applied.get(f, 0)
            pct = p.dna_percent(f)
            tag = "*" if f == p.field else " "           # * = your own Field (cheaper)
            label = f"{tag}{f[:17]:<17}{own:>3}b {chg:>3}c {pct:>3}%"
            out.append_text(menu.row(label, i == self.cursor))
        out.append_text(menu.footer("↑↓fld ←→amt  G gen  ENTER chg  ESC"))
        return out
