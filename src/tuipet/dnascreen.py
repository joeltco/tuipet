"""DNA screen -- the device's DNA sub-screens.

Home menu (DVPet DNA_Validation): Charge / Generate / Stats / Divergence.
(The Requirements viewer left with the DNA slim -- gate-forgiveness died
with it; this docstring lagged until the DNA review 2026-07-18.)
  * Charge   (DNA_Inventory + DNA_Detail): spend banked DNA into the pet, bending
             evolution toward forms whose Field-DNA gates you meet.  The bill is
             ENERGY: 1/unit on your own Field, doubled off-Field (the old
             spirit/mood/illness costs left with their systems).  On commit
             the pet absorbs it (the DNA_Feeding "dnaWash" fx plays on the display).
  * Generate (DNA_GenerateValidate + DNA_Generate): wager bits, mash SPACE ~10s; a
             faster mash earns a rarer Field (getDNARate bands), too slow/fast -> the
             dud None field. The won Field blinks in (the UnlockDNA reveal).
  * Stats    (DNA_Stats): each Field's charged share -- the evolution gate %.
  * Divergence (tuipet, "ultimate v-pet" arc 2026-07-07): the wild-road map --
             where each Field's charge can steer the NEXT evolution off the
             chart (evolution.divergence_roads), the stage threshold, and the
             armed state.  The door must be visible to be a choice.
"""
from __future__ import annotations
import math
from . import data, grid, menu, evolution
from .theme import LCD_ON, LCD_BG, SIL_DAY  # noqa: F401  (palette names bound for theme.apply propagation)
from .pet import (MAX_DNA_INVENTORY, MAX_DNA_WAGER, DNA_STABILIZER_BET,
                  DNA_RESONANT_BET, dna_field_for_rate)

MASH_TICKS = 100            # DVPet: 100 intervals x 0.1s = the 10s mini-game window
MASH_KEYS = ("space",)      # the single "button" you mash
_METER_W = 12               # the strip meter: was 22 -> the whole line ran 62 cols and
#                             MARQUEED mid-minigame (a live meter must hold still --
#                             the training-audit rule; DNA audit 2026-07-05)

_HOME = (("charge", "Charge"), ("generate", "Generate"),
         ("stats", "Stats"), ("roads", "Divergence"))


class DNAPanel:
    def __init__(self, pet):
        self.pet = pet
        self.fields = list(data.DNA_FIELDS)
        self.cursor = 0              # field cursor (charge / stats)
        self.amount = 1             # charge amount
        self.home_i = 0             # home-menu cursor
        self.frame_i = 0
        self.phase = "home"         # home | charge | stats | roads | bet | mash | result
        self.bet = 1
        self.hits = 0
        self.mash_f = 0
        self.won = None             # (field, wager, rate) after a mini-game
        self.blink = 0              # UnlockDNA reveal blink counter
        self.last = "Generate DNA, then charge it."
        self.sfx = None
        self._roads = evolution.divergence_roads(pet)   # field -> wild-road targets
        self.road_i = 0

    def _armed(self):
        """The strict-max charged Field at/over the stage threshold WITH a
        road -- the next evolution will diverge (mirrors divergence_target's
        gate without picking the destination)."""
        f = self.pet.highest_dna()
        need = evolution.DIVERGE_NEED.get(self.pet.stage)
        if (f and f != "None" and need is not None
                and self.pet.dna_applied.get(f, 0) >= need and f in self._roads):
            return f
        return ""

    # (the Requirements viewer left with the DNA slim; BASIC VPET 2026-07-16)

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
                owned0 = dict(self.pet.dna_owned)
                bits0 = self.pet.bits
                field = self.pet.dna_minigame_award(self.bet, rate)
                # the result page reports what actually LANDED: near the 99
                # cap the overflow refunds as bits, and "Got 99" while 9
                # banked was a lie (DNA review 2026-07-18)
                banked = self.pet.dna_owned.get(field, 0) - owned0.get(field, 0)
                refund = self.pet.bits - bits0
                self.won = (field, self.bet, rate, banked, refund)
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


    def _key_roads(self, k):
        n = max(1, len(self._roads))
        if k in ("up", "k"):
            self.road_i = (self.road_i - 1) % n
        elif k in ("down", "j"):
            self.road_i = (self.road_i + 1) % n
        elif k in ("escape", "enter"):
            self.phase = "home"
        return None

    def _key_bet(self, k):
        p = self.pet
        if k in ("left", "h"):
            self.bet = max(1, self.bet - 1)
        elif k in ("right", "l"):
            self.bet = min(MAX_DNA_WAGER, self.bet + 1)
        elif k in ("up", "k"):
            self.bet = min(MAX_DNA_WAGER, self.bet + 100)
        elif k in ("down", "j"):
            self.bet = max(1, self.bet - 100)
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
        if key == "roads":
            f = self._armed()
            return ("ARMED: %s" % data.pretty_field(f)[:10]) if f \
                else "%d road(s)" % sum(len(v) for v in self._roads.values())
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
            road = "▸" if f in self._roads else " "      # ▸ = a wild road exists (Divergence page)
            label = "%s%-14s%s%3db %3dc %3d%%" % (tag, data.pretty_field(f)[:14], road, own, chg, pct)
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


    def _text_roads(self):
        p = self.pet
        need = evolution.DIVERGE_NEED.get(p.stage)
        out = menu.bar("DNA · DIVERGENCE",
                       "need %dc" % need if need is not None else "top stage")
        if not self._roads or need is None:
            out.append_text(menu.blanks(1))
            out.append_text(menu.note("No wild roads from this form."))
            out.append_text(menu.blanks(1))
            out.append_text(menu.row("Charge a Field to its threshold", False))
            out.append_text(menu.row("to steer the next evolution.", False))
            out.append_text(menu.footer("ESC back"))
            return out
        _, by = data.load_sprites()
        armed = self._armed()
        flds = sorted(self._roads)
        self.road_i %= len(flds)
        for i, f in enumerate(flds):
            names = "/".join(by.get(t, {}).get("name", "?") for t in self._roads[f][:2])
            if len(self._roads[f]) > 2:
                names += "…"
            chg = p.dna_applied.get(f, 0)
            mark = "▶" if f == armed else " "
            label = "%s%-13s %2d/%-2d %s" % (mark, data.pretty_field(f)[:13],
                                             chg, need, names[:15])
            out.append_text(menu.row(label, i == self.road_i))
        out.append_text(menu.note("Armed: next evolution takes the road."
                                  if armed else
                                  "Charge %d in ONE Field to arm." % need,
                                  tick=self.frame_i))
        out.append_text(menu.footer("↑↓ field   ESC back"))
        return out

    def _text_bet(self):
        p = self.pet
        out = menu.bar("DNA · GENERATE", "%db" % p.bits)
        out.append_text(menu.note("Wager bits, then mash for DNA."))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("wager: %4d b" % self.bet, True))
        # the lab tiers (high-stakes wagers, 2026-07-14): the premium past the
        # 99-DNA bank buys lab work, spent up front like the wager itself
        if self.bet >= DNA_RESONANT_BET:
            tier = "RESONANT: +%d to both neighbors" % (self.bet // 5)
        elif self.bet >= DNA_STABILIZER_BET:
            tier = "STABILIZED: a spoiled mash still banks"
        else:
            tier = ""
        out.append_text(menu.row(tier[:38], False))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("faster mash → rarer field", False))
        if self.bet >= DNA_STABILIZER_BET:
            out.append_text(menu.row("stabilized — it never rolls None", False))
        else:
            out.append_text(menu.row("too slow / too fast → None", False))
        out.append_text(menu.footer("←→ ±1  ↑↓ ±100  ENTER mash!  ESC back"))
        return out

    def _text_mash(self):
        # a MINIGAME is a staged arena scene, like the training drills (audit
        # 2026-07-04 -- this was a bare text meter): the pet stands centre and
        # visibly throws itself into every press (strike pose, the vaccine
        # convention); rate/hits ride the gauge line below.
        p = self.pet
        flash = getattr(self, "_mash_flash", 0)
        self._mash_flash = max(0, flash - 1)
        sheet = data.frames_for(p.num, getattr(p, "egg_type", 0))
        if flash > 0 and len(sheet) > 6 and sheet[6]:
            fr = sheet[6]                                     # strike pose on a press
        else:
            fr = data.bob_frame(p.num, self.frame_i, beat=2,
                                egg_type=getattr(p, "egg_type", 0))  # drill-urgency bob, not 10Hz
        # scene-only: the meter rides the strip (box-clip audit 2026-07-04 --
        # the bar+scene+meter stack ran 16 lines into the physical 12-row box)
        return menu.paint([grid.center(grid.prep(fr, 24), ph=24)], p.background())

    def strip(self):
        """The live mash meter under the LCD during the mini-game; every other
        phase pops its key hints (hint overhaul 2026-07-10).  Kept <= 40 visible
        cols so it NEVER marquees (a live meter holds still)."""
        if self.phase == "mash":
            rate = self._rate()
            left = max(0.0, (MASH_TICKS - self.mash_f) / 10.0)
            fld = data.pretty_field(dna_field_for_rate(rate))[:9]
            return ("%s r%-2d→[b]%-9s[/] %4.1fs SPACE!"
                    % (self._meter(rate), rate, fld, left))
        if self.phase == "charge":
            return menu.hints(("↑↓", "field"), ("←→", "amount"),
                              ("ENTER", "charge"))
        if self.phase == "bet":
            return menu.hints(("←→", "wager"), ("ENTER", "mash!"),
                              ("ESC", "back"))
        if self.phase == "result":
            return menu.hints(("any key", "bank it"))
        if self.phase in ("stats", "roads"):
            return menu.hints(("↑↓", "browse"), ("ESC", "back"))
        return menu.hints(("↑↓", "pick"), ("ENTER", "open"), ("ESC", "out"))

    def _text_result(self):
        field, wager, rate, banked, refund = self.won
        show = (self.blink // 2) % 2 == 0            # DVPet unlockingDNA: the Field blinks in
        name = data.pretty_field(field)
        out = menu.bar("DNA · GENERATE", "rate %d" % rate)
        out.append_text(menu.blanks(1))
        got = "✓ Got %d %s DNA" % (banked, name)
        if refund > 0:
            got += " · %db back" % refund            # the cap overflow, refunded
        out.append_text(menu.note(got if show else "✓"))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("rate %d → %s" % (rate, name if show else ""), True))
        if field == "None":
            out.append_text(menu.row("None = the dud field (banked)", False))
        elif wager >= DNA_RESONANT_BET:
            out.append_text(menu.row("resonance: +%d to both neighbors" % (wager // 5), False))
        else:
            out.append_text(menu.row("banked — open Charge to use it", False))
        out.append_text(menu.footer("any key  →  DNA menu"))
        return out
