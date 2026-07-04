"""DNA screen -- the device's three DNA sub-screens plus a requirements viewer.

Home menu (DVPet DNA_Validation): Charge / Generate / Stats / Requirements.
  * Charge   (DNA_Inventory + DNA_Detail): spend banked DNA into the pet, bending
             evolution toward forms whose Field-DNA gates you meet. Charging off
             your own Field costs more spirit, sours mood, risks illness. On commit
             the pet absorbs it (the DNA_Feeding "dnaWash" fx plays on the display).
  * Generate (DNA_GenerateValidate + DNA_Generate): wager bits, mash SPACE ~10s; a
             faster mash earns a rarer Field (getDNARate bands), too slow/fast -> the
             dud None field. The won Field blinks in (the UnlockDNA reveal).
  * Stats    (DNA_Stats): each Field's charged share -- the evolution gate %.
  * Requirements: per evolution target, the Field-DNA % each form needs and whether
             your charged distribution satisfies it (DVPet's evolution-tree DNA page).
"""
from __future__ import annotations
import math
from . import data, grid, menu, evolution
from .render import render_scene
from .theme import LCD_ON, LCD_BG, SIL_DAY
from .pet import MAX_DNA_INVENTORY, dna_field_for_rate

MASH_TICKS = 100            # DVPet: 100 intervals x 0.1s = the 10s mini-game window
MASH_KEYS = ("space",)      # the single "button" you mash
_METER_W = 22

_HOME = (("charge", "Charge"), ("generate", "Generate"),
         ("stats", "Stats"), ("reqs", "Requirements"))


class DNAPanel:
    def __init__(self, pet):
        self.pet = pet
        self.fields = list(data.DNA_FIELDS)
        self.cursor = 0              # field cursor (charge / stats)
        self.amount = 1             # charge amount
        self.home_i = 0             # home-menu cursor
        self.req_i = 0              # requirements-viewer cursor
        self.frame_i = 0
        self.phase = "home"         # home | charge | stats | reqs | bet | mash | result
        self.bet = 1
        self.hits = 0
        self.mash_f = 0
        self.won = None             # (field, wager, rate) after a mini-game
        self.blink = 0              # UnlockDNA reveal blink counter
        self.last = "Generate DNA, then charge it."
        self.sfx = None
        self._targets = self._dna_targets()

    # ---- data ------------------------------------------------------------
    def _dna_targets(self):
        """The pet's evolution targets that declare a Field-DNA gate (getDNAReq)."""
        reqs = data.load_requirements()
        _, by = data.load_sprites()
        out = []
        for t in data.load_evolutions().get(self.pet.num, []):
            r = reqs.get(t)
            if not r:
                continue
            gates = {f: g for f, g in r["dna"].items() if g[0] != "None"}
            if gates:
                out.append((t, by.get(t, {}).get("name", "#%d" % t), gates, r))
        return out

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
                self.blink = 0
                self.sfx = "mischief"    # soundConfig unlockDNA -> mischief.wav (banks even None -- never a jeer)
        elif self.phase == "result":
            self.blink += 1              # drive the won-Field blink reveal

    # ---- input -----------------------------------------------------------
    def key(self, k):
        self.sfx = None
        return getattr(self, "_key_" + self.phase)(k)

    def _key_home(self, k):
        if k in ("up", "k"):
            self.home_i = (self.home_i - 1) % len(_HOME)
        elif k in ("down", "j"):
            self.home_i = (self.home_i + 1) % len(_HOME)
        elif k in ("enter", "space", "right", "l"):
            self.phase = _HOME[self.home_i][0]
            if self.phase == "generate":
                self.phase = "bet"
                self.bet = max(1, min(MAX_DNA_INVENTORY, self.amount))
            self.sfx = "select"
        elif k in ("escape", "x"):
            return ("done", None)
        return None

    def _key_charge(self, k):
        p, f = self.pet, self.field
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.fields)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.fields)
        elif k in ("left", "h"):
            self.amount = max(1, self.amount - 1)
        elif k in ("right", "l"):
            self.amount = min(MAX_DNA_INVENTORY, self.amount + 1)
        elif k in ("enter", "space"):
            amt = min(self.amount, p.dna_owned.get(f, 0))
            if amt <= 0:
                self.last = "No banked %s yet." % data.pretty_field(f)
                self.sfx = "error"
            elif p.apply_dna(f, amt):
                self.sfx = "compatible"
                return ("done", ("charged", f, amt))   # close -> DNA_Feeding absorb fx
        elif k == "escape":
            self.phase = "home"
        return None

    def _key_stats(self, k):
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.fields)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.fields)
        elif k in ("escape", "enter"):
            self.phase = "home"
        return None

    def _key_reqs(self, k):
        n = max(1, len(self._targets))
        if k in ("up", "k"):
            self.req_i = (self.req_i - 1) % n
        elif k in ("down", "j"):
            self.req_i = (self.req_i + 1) % n
        elif k in ("escape", "enter"):
            self.phase = "home"
        return None

    def _key_bet(self, k):
        p = self.pet
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
                self.phase = "home"
        elif k == "escape":
            self.phase = "home"
        return None

    def _key_mash(self, k):
        if k in MASH_KEYS:
            self.hits += 1                # locked in until the 10s timer ends
            self._mash_flash = 3          # the pet visibly throws itself into it
        return None

    def _key_result(self, k):
        self.phase = "home"              # the won DNA is banked -- back to the menu to charge it
        return None

    # ---- views -----------------------------------------------------------
    def text(self):
        return getattr(self, "_text_" + self.phase)()

    def _meter(self, rate):
        filled = max(0, min(_METER_W, int(round(rate / 80.0 * _METER_W))))
        return "█" * filled + "░" * (_METER_W - filled)

    def _home_tag(self, key):
        p = self.pet
        if key == "charge":
            return "%d banked" % sum(p.dna_owned.values())
        if key == "generate":
            return "mash for DNA"
        if key == "stats":
            return "%d charged" % p.dna_total()
        if key == "reqs":
            return "%d form(s)" % len(self._targets)
        return ""

    def _text_home(self):
        p = self.pet
        out = menu.bar("DNA", "%db" % p.bits)
        for i, (key, label) in enumerate(_HOME):
            out.append_text(menu.row("%-13s%s" % (label, self._home_tag(key)), i == self.home_i))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("[%s]" % (self.last or "")[:34], False))
        out.append_text(menu.footer("↑↓ pick  ENTER open  ESC out"))
        return out

    def _text_charge(self):
        p = self.pet
        out = menu.bar("DNA · CHARGE", "%db  x%d" % (p.bits, self.amount))
        for i, f in enumerate(self.fields):
            own = p.dna_owned.get(f, 0)
            chg = p.dna_applied.get(f, 0)
            pct = p.dna_percent(f)
            tag = "*" if f == p.field else " "           # * = your own Field (cheaper)
            label = "%s%-15s%3db %3dc %3d%%" % (tag, data.pretty_field(f)[:15], own, chg, pct)
            out.append_text(menu.row(label, i == self.cursor))
        out.append_text(menu.footer("↑↓fld ←→amt ENTER chg  ESC back"))
        return out

    def _text_stats(self):
        p = self.pet
        out = menu.bar("DNA · STATS", "%d charged" % p.dna_total())
        for i, f in enumerate(self.fields):
            pct = p.dna_percent(f)
            bar = "█" * (pct * 12 // 100)
            out.append_text(menu.row("%-14s%3d%% %s" % (data.pretty_field(f)[:14], pct, bar),
                                     i == self.cursor))
        out.append_text(menu.footer("↑↓ field   ESC back"))
        return out

    def _text_reqs(self):
        out = menu.bar("DNA · REQUIREMENTS", "%d form(s)" % len(self._targets))
        if not self._targets:
            out.append_text(menu.blanks(1))
            out.append_text(menu.note("No DNA evolutions from here."))
            out.append_text(menu.blanks(1))
            out.append_text(menu.row("Charged DNA only matters where a", False))
            out.append_text(menu.row("form lists a Field-DNA gate.", False))
            out.append_text(menu.footer("ESC back"))
            return out
        t, name, gates, r = self._targets[self.req_i]
        met = evolution._dna_ok(self.pet, r)
        out.append_text(menu.row("%-20s%s" % (name[:20], "✓ MET" if met else "… need"), True))
        out.append_text(menu.blanks(1))
        for f, (cond, val) in gates.items():
            cur = self.pet.dna_percent(f)
            ok = evolution._cmp(cond, val, cur)
            sym = "≥" if cond == "GreaterThan" else ("≤" if cond == "LessThan" else "=")
            mark = "✓" if ok else "·"
            out.append_text(menu.row("%s %-14s %s%3d%%  now %3d%%"
                                     % (mark, data.pretty_field(f)[:14], sym, int(val), cur), False))
        out.append_text(menu.footer("↑↓ form %d/%d   ESC back" % (self.req_i + 1, len(self._targets))))
        return out

    def _text_bet(self):
        p = self.pet
        out = menu.bar("DNA · GENERATE", "%db" % p.bits)
        out.append_text(menu.note("Wager bits, then mash for DNA."))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("wager:  %3d b" % self.bet, True))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("faster mash → rarer field", False))
        out.append_text(menu.row("too slow / too fast → None", False))
        out.append_text(menu.footer("←→ wager  ENTER mash!  ESC back"))
        return out

    def _text_mash(self):
        # a MINIGAME is a staged arena scene, like the training drills (audit
        # 2026-07-04 -- this was a bare text meter): the pet stands centre and
        # visibly throws itself into every press (strike pose, the vaccine
        # convention); rate/hits ride the gauge line below.
        p = self.pet
        flash = getattr(self, "_mash_flash", 0)
        self._mash_flash = max(0, flash - 1)
        rec = data.load_sprites()[1][p.num]
        pose = 6 if (flash > 0 and len(rec["frames"]) > 6 and rec["frames"][6]) else \
            data.ROLES["idle"][self.frame_i % 2]
        fr = rec["frames"][pose] or rec["frames"][0]
        bgimg = p.background()
        on = SIL_DAY if bgimg else LCD_ON
        # scene-only: the meter rides the strip (box-clip audit 2026-07-04 --
        # the bar+scene+meter stack ran 16 lines into the physical 12-row box)
        return render_scene([grid.center(grid.prep(fr, 24), ph=24)],
                            40, 12, on, LCD_BG, bgimg=bgimg)

    def strip(self):
        """The live mash meter under the LCD; other phases keep in-LCD menus."""
        if self.phase != "mash":
            return ""
        rate = self._rate()
        left = max(0.0, (MASH_TICKS - self.mash_f) / 10.0)
        return ("%s rate %d → [b]%s[/]  %0.1fs · mash SPACE!"
                % (self._meter(rate), rate, data.pretty_field(dna_field_for_rate(rate)), left))

    def _text_result(self):
        field, wager, rate = self.won
        show = (self.blink // 2) % 2 == 0            # DVPet unlockingDNA: the Field blinks in
        name = data.pretty_field(field)
        out = menu.bar("DNA · GENERATE", "rate %d" % rate)
        out.append_text(menu.blanks(1))
        out.append_text(menu.note(("✓ Got %d %s DNA" % (wager, name)) if show else "✓"))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("rate %d → %s" % (rate, name if show else ""), True))
        if field == "None":
            out.append_text(menu.row("None = the dud field (banked)", False))
        else:
            out.append_text(menu.row("banked — open Charge to use it", False))
        out.append_text(menu.footer("any key  →  DNA menu"))
        return out
