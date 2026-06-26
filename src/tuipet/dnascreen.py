"""DNA screen (DVPet DNA_Inventory / DNA_Generate mini-game / DNA_Detail).

Generate Field-DNA with the real DVPet mash mini-game (G): wager bits, then mash
SPACE for ~10s -- your hit-rate lands on a Field by DVPet's getDNARate bands (faster
mash -> rarer field; too slow/fast -> None, a wasted wager). Then CHARGE banked DNA
into the pet (ENTER) to bend evolution toward forms whose Field-DNA gates you meet.
Charging off your own Field costs more spirit, sours mood, and risks illness.
"""
from __future__ import annotations
import math
from . import data, menu
from .pet import MAX_DNA_INVENTORY, dna_field_for_rate

MASH_TICKS = 100            # DVPet: 100 intervals x 0.1s = the 10s mini-game window
MASH_KEYS = ("space",)      # the single "button" you mash
_METER_W = 22


class DNAPanel:
    def __init__(self, pet):
        self.pet = pet
        self.fields = list(data.DNA_FIELDS)
        self.cursor = 0
        self.amount = 1
        self.frame_i = 0
        self.phase = "menu"          # menu | bet | mash | result
        self.bet = 1
        self.hits = 0
        self.mash_f = 0
        self.won = None              # (field, wager, rate) after a mini-game
        self.last = "Charge, or G to generate."
        self.sfx = None

    @property
    def field(self):
        return self.fields[self.cursor]

    # ---- mini-game math (DVPet drawDNAGenerateAnim) ----------------------
    def _rate(self):
        """rate = ceil(hits / time * 10), time in seconds. At the 10s mark this is
        just your total hit count, so the Field = how many presses you land."""
        if self.mash_f <= 0:
            return 0
        return int(math.ceil(self.hits / (self.mash_f / 10.0) * 10.0))

    def anim(self):
        self.frame_i += 1
        if self.phase == "mash":
            self.mash_f += 1
            if self.mash_f >= MASH_TICKS:
                rate = self._rate()
                field = self.pet.dna_minigame_award(self.bet, rate)
                self.won = (field, self.bet, rate)
                self.phase = "result"
                self.sfx = "select"      # DVPet banks even None (UnlockDNA) -- never a jeer

    # ---- input -----------------------------------------------------------
    def key(self, k):
        p = self.pet
        self.sfx = None
        if self.phase == "mash":
            if k in MASH_KEYS:
                self.hits += 1
            return None                                  # locked in until the timer ends
        if self.phase == "result":
            self.phase = "menu"                          # any key dismisses the result
            return None
        if self.phase == "bet":
            if k in ("left", "h"):
                self.bet = max(1, self.bet - 1)
            elif k in ("right", "l"):
                self.bet = min(MAX_DNA_INVENTORY, self.bet + 1)
            elif k in ("enter", "space"):
                if p.dna_bet(self.bet):
                    self.phase, self.hits, self.mash_f = "mash", 0, 0
                    self.sfx = "select"
                else:
                    self.last = "Not enough bits to wager."
                    self.sfx = "error"
                    self.phase = "menu"
            elif k in ("escape", "x", "q", "g"):
                self.phase = "menu"
            return None
        # ---- menu phase ----
        f = self.field
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.fields)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.fields)
        elif k in ("left", "h"):
            self.amount = max(1, self.amount - 1)
        elif k in ("right", "l"):
            self.amount = min(MAX_DNA_INVENTORY, self.amount + 1)
        elif k == "g":                                   # open the generate mini-game
            self.bet = min(MAX_DNA_INVENTORY, max(1, self.amount))
            self.phase = "bet"
        elif k in ("enter", "space"):                    # charge: banked -> applied
            amt = min(self.amount, p.dna_owned.get(f, 0))
            if amt <= 0:
                self.last = "No banked DNA -- generate it with G first."
                self.sfx = "error"
            elif p.apply_dna(f, amt):
                same = f == p.field
                self.last = f"Charged {amt} {f}! ({'own' if same else 'off'}-field)"
                self.sfx = "compatible"
        elif k in ("escape", "x", "q"):
            return ("done", None)
        return None

    # ---- views -----------------------------------------------------------
    def _meter(self, rate):
        filled = max(0, min(_METER_W, int(round(rate / 80.0 * _METER_W))))
        return "█" * filled + "░" * (_METER_W - filled)

    def text(self):
        return {"bet": self._text_bet, "mash": self._text_mash,
                "result": self._text_result}.get(self.phase, self._text_menu)()

    def _text_menu(self):
        p = self.pet
        out = menu.bar("DNA", f"{p.bits}b   x{self.amount}")
        for i, f in enumerate(self.fields):
            own = p.dna_owned.get(f, 0)
            chg = p.dna_applied.get(f, 0)
            pct = p.dna_percent(f)
            tag = "*" if f == p.field else " "           # * = your own Field (cheaper)
            label = f"{tag}{data.pretty_field(f)[:16]:<16}{own:>3}b {chg:>3}c {pct:>3}%"
            out.append_text(menu.row(label, i == self.cursor))
        out.append_text(menu.footer("↑↓fld ←→amt  G gen  ENTER chg  ESC"))
        return out

    def _text_bet(self):
        p = self.pet
        out = menu.bar("DNA · GENERATE", f"{p.bits}b")
        out.append_text(menu.note("Wager bits, then mash for DNA."))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row(f"wager:  {self.bet:>3} b", True))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("faster mash → rarer field", False))
        out.append_text(menu.row("too slow / too fast → None", False))
        out.append_text(menu.footer("←→ wager  ENTER mash!  ESC back"))
        return out

    def _text_mash(self):
        rate = self._rate()
        field = dna_field_for_rate(rate)
        left = max(0.0, (MASH_TICKS - self.mash_f) / 10.0)
        out = menu.bar("DNA · GENERATE", f"wager {self.bet}b")
        out.append_text(menu.note("⚡ MASH  SPACE !"))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row(self._meter(rate), False))
        out.append_text(menu.row(f"rate {rate:>3}    hits {self.hits:>3}", False))
        out.append_text(menu.row(f"→ {data.pretty_field(field)}", False))
        out.append_text(menu.footer(f"{left:0.1f}s left   mash SPACE!"))
        return out

    def _text_result(self):
        field, wager, rate = self.won
        out = menu.bar("DNA · GENERATE", f"rate {rate}")
        out.append_text(menu.blanks(1))
        # DVPet banks the rolled Field even when it is None (the dud field): over/under
        # mashing still yields real -- if near-useless -- None-field DNA, not a whiff.
        out.append_text(menu.note(f"✓ Got {wager} {data.pretty_field(field)} DNA"))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row(f"rate {rate} → {field}", False))
        if field == "None":
            out.append_text(menu.row("None = the dud field (banked)", False))
        else:
            out.append_text(menu.row(f"banked into {field} DNA", False))
        out.append_text(menu.footer("any key to continue"))
        return out
