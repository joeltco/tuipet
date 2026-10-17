"""DNA screen -- the device's DNA sub-screens.

Home menu (DVPet DNA_Validation): Charge / Generate / Stats / Divergence.
(The Requirements viewer left with the DNA slim -- gate-forgiveness died
with it; this docstring lagged until the DNA review 2026-07-18.)
  * Charge   (DNA_Inventory + DNA_Detail): spend banked DNA into the pet, bending
             evolution toward a real Field's available road. The bill is
             ENERGY: 1/unit on your own Field, doubled off-Field (the old
             spirit/mood/illness costs left with their systems).  On commit
             the pet absorbs it (the DNA_Feeding "dnaWash" fx plays on the display).
  * Generate (DNA_GenerateValidate + DNA_Generate): wager bits, mash SPACE ~10s; a
             mash rate selects a Field, too slow/fast -> the
             None: a spoiled mash, half the wager back (2026-10-15). The won
             Field blinks in (the UnlockDNA reveal).
  * Stats    (DNA_Stats): each Field's charged share -- a corpus selection bonus.
  * Divergence (tuipet, "ultimate v-pet" arc 2026-07-07): the wild-road map --
             where each Field's charge can steer the NEXT evolution off the
             chart (evolution.divergence_roads), the stage threshold, and the
             armed state.  The door must be visible to be a choice.
"""
from __future__ import annotations
from .sfx import CueQueue
import math
from . import data, grid, menu, evolution, persistence
from rich.console import Console
from rich.text import Text
from .theme import LCD_ON, LCD_BG, SIL_SCENE  # noqa: F401  (palette names bound for theme.apply propagation)
from .pet import (MAX_DNA_INVENTORY, DNA_STABILIZER_BET,
                  DNA_RESONANT_BET, DNA_RATE_BANDS,
                  dna_award_field)

# every wager that buys something: 1..99 bank 1:1, then the two lab tiers
WAGER_TIERS = (MAX_DNA_INVENTORY, DNA_STABILIZER_BET, DNA_RESONANT_BET)
WAGER_LADDER = tuple(range(1, MAX_DNA_INVENTORY + 1)) + WAGER_TIERS[1:]

MASH_TICKS = 100            # DVPet: 100 intervals x 0.1s = the 10s mini-game window
MASH_KEYS = ("space",)      # the single "button" you mash
_METER_W = 12               # the strip meter: was 22 -> the whole line ran 62 cols and
#                             MARQUEED mid-minigame (a live meter must hold still --
#                             the training-audit rule; DNA audit 2026-07-05)

_HOME = (("charge", "Charge"), ("generate", "Generate"),
         ("stats", "Stats"), ("roads", "Divergence"))


def _field_word(f, w):
    """Fit a static Field name, marking any omitted tail explicitly."""
    s = data.pretty_field(f)
    if len(s) <= w:
        return s
    return menu.ellipsis(s, w)


class DNAPanel(CueQueue):
    def __init__(self, pet):
        self.pet = pet
        self.fields = list(data.DNA_FIELDS)
        # the CHARGE cursor never offers "None" (DNA ruling 2026-07-18): it
        # wasted energy, diluted every real Field's percent, and a None
        # strict-max BLOCKED divergence -- the UI stops selling self-harm.
        # (The None FIELD itself stays load-bearing: 387 corpus gates key
        # on it; stats still shows its share honestly.)
        self.charge_fields = [f for f in data.DNA_FIELDS if f != "None"]
        self.cursor = 0              # field cursor (charge / stats)
        self.amount = 1             # charge amount
        self.home_i = 0             # home-menu cursor
        self.frame_i = 0
        self.phase = "home"         # home | charge | stats | roads | bet | mash | result
        self.bet = 1
        self.hits = 0
        self.mash_f = 0
        self.won = None             # (field, wager, rate, banked, refund)
        self.splashed = {}          # actual adjacent-bank deltas, including zero
        self.blink = 0              # UnlockDNA reveal blink counter
        # the loop in one line, help-GROW's own grammar (gameplay polish
        # #12, 2026-07-22): "Generate, then charge" never said WHY -- for a
        # line pet the whole point of charging is the Divergence road
        self.last = "Generate · charge ONE Field · road"
        self.sfx = None
        self._roads = evolution.divergence_roads(pet)   # field -> wild-road targets
        self.road_i = 0
        self.target_i = 0

    def _armed(self):
        """The strict-max charged Field at/over the stage threshold WITH a
        road -- the next evolution will diverge (mirrors divergence_target's
        gate without picking the destination)."""
        return self.pet.highest_dna() if evolution.divergence_options(self.pet) else ""

    # (the Requirements viewer left with the DNA slim; BASIC VPET 2026-07-16)

    @property
    def field(self):
        # DNA audit 2026-10-14: card and commit share the phase's actual cursor.
        if self.phase == "charge":
            return self.charge_fields[self.cursor % len(self.charge_fields)]
        if self.phase in ("roads", "road_detail") and self._roads:
            fields = sorted(self._roads)
            return fields[self.road_i % len(fields)]
        return self.fields[self.cursor % len(self.fields)]

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
                self.splashed = {}
                if self.bet >= DNA_RESONANT_BET and field != "None":
                    fields = [f for _, f in DNA_RATE_BANDS if f != "None"]
                    i = fields.index(field)
                    for j in (i - 1, i + 1):
                        if 0 <= j < len(fields):
                            f = fields[j]
                            self.splashed[f] = self.pet.dna_owned.get(f, 0) - owned0.get(f, 0)
                self.phase = "result"
                self.blink = 0
                self.sfx = "mischief"    # soundConfig unlockDNA -> mischief.wav (a spoiled mash refunds half -- never a jeer)
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
            if self.phase == "charge":
                self.cursor %= len(self.charge_fields)
            if self.phase == "generate":
                self.phase = "bet"
                self.bet = max(1, min(MAX_DNA_INVENTORY, self.amount))
            self.sfx = "select"
        elif k in ("escape", "x"):
            return ("done", None)
        return None

    def _key_charge(self, k):
        p = self.pet
        f = self.charge_fields[self.cursor % len(self.charge_fields)]
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.charge_fields)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.charge_fields)
        elif k in ("left", "h"):
            self.amount = max(1, self.amount - 1)
        elif k in ("right", "l"):
            self.amount = min(MAX_DNA_INVENTORY, self.amount + 1)
        elif k in ("enter", "space"):
            amt = min(self.amount, p.dna_owned.get(f, 0), p.dna_affordable(f))
            if p.dna_owned.get(f, 0) <= 0:
                self.last = "No banked %s yet." % data.pretty_field(f)
                self.sfx = "error"
            elif amt <= 0:                          # DNA call #5 = A (2026-10-15)
                self.last = "Too tired — rest to charge."
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
        elif k in ("escape", "enter", "space"):
            self.phase = "home"
        return None

    def _key_road_detail(self, k):
        n = len(set(self._roads[self.field]))
        if k in ("up", "k"):
            self.target_i = (self.target_i - 1) % n
        elif k in ("down", "j"):
            self.target_i = (self.target_i + 1) % n
        elif k in ("escape", "enter", "space"):
            self.phase = "roads"
        return None


    def _key_roads(self, k):
        n = max(1, len(self._roads))
        if k in ("up", "k"):
            self.road_i = (self.road_i - 1) % n
        elif k in ("down", "j"):
            self.road_i = (self.road_i + 1) % n
        elif k == "enter" and self._roads:
            self.phase, self.target_i = "road_detail", 0
        elif k in ("escape", "enter", "space"):
            self.phase = "home"
        return None

    def _key_bet(self, k):
        p = self.pet
        # the wager walks ONLY the amounts that buy something (Joel 2026-10-15,
        # DNA call #3 = A): 1..99 bank 1:1, then the 500 STABILIZED and the
        # 2500 RESONANT tiers -- 100-499, 501-2499 and 2501+ bought nothing extra
        ladder = WAGER_LADDER
        i = ladder.index(self.bet) if self.bet in ladder else \
            max(j for j, v in enumerate(ladder) if v <= max(1, self.bet))
        if k in ("left", "h"):
            self.bet = ladder[max(0, i - 1)]
        elif k in ("right", "l"):
            self.bet = ladder[min(len(ladder) - 1, i + 1)]
        elif k in ("up", "k"):
            self.bet = next((v for v in WAGER_TIERS if v > self.bet), ladder[-1])
        elif k in ("down", "j"):
            self.bet = next((v for v in reversed((1,) + WAGER_TIERS) if v < self.bet), 1)
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
            return ("ARMED: %s" % _field_word(f, 10)) if f \
                else "%d road(s)" % sum(len(v) for v in self._roads.values())
        return ""

    def _text_home(self):
        p = self.pet
        out = menu.header("DNA", "%db" % p.bits)
        for i, (key, label) in enumerate(_HOME):
            out.append_text(menu.row("%-13s%s" % (label, self._home_tag(key)), i == self.home_i))
        return menu.page(out, self.last, self.frame_i)

    def _text_charge(self):
        p = self.pet
        # the charge never outruns the energy that pays for it (DNA call #5 = A)
        amt = min(self.amount, p.dna_owned.get(self.field, 0),
                  p.dna_affordable(self.field))
        cost = amt * (1 if self.field == p.field else 2)
        out = menu.header("DNA · CHARGE", "x%d / %d · energy -%d" % (amt, self.amount, cost))
        # DNA audit 2026-10-14: costs and wipe law fit without a scrolling tail.
        need = evolution.DIVERGE_NEED.get(p.stage)
        note = ("ARMED: next growth takes the road" if self._armed() else
                "Divergence road: unique leader >=%d" % need if self._roads and need else
                "No DNA road from this form.")
        out.append_text(menu.note(note))
        out.append_text(menu.note("Charges clear at every evolution"))

        def fmt(f, i):
            own = p.dna_owned.get(f, 0)
            chg = p.dna_applied.get(f, 0)
            pct = p.dna_percent(f)
            tag = "*" if f == p.field else " "           # * = your own Field (cheaper)
            road = "▸" if f in self._roads else " "      # ▸ = a wild road exists (Divergence page)
            # 17-col name: "Nightmare Soldier" fits whole (the 14-col slice
            # printed "Nightmare Sold" -- menu audit 2026-07-21); row = 35
            label = "%s%-17s%s%3db %3dc %3d%%" % (tag, _field_word(f, 17), road, own, chg, pct)
            return label

        self.cursor = menu.list_window(out, self.charge_fields, self.cursor, 6, fmt)
        return menu.page(out, "* own Field  ▸ road  ties disarm")

    def _text_stats(self):
        p = self.pet
        out = menu.header("DNA · STATS", "%d charged" % p.dna_total())
        for i, f in enumerate(self.fields):
            pct = p.dna_percent(f)
            bar = "█" * (pct * 12 // 100)
            out.append_text(menu.row("%-17s%3d%% %s" % (_field_word(f, 17), pct, bar),
                                     i == self.cursor))
        out.append_text(menu.footer(""))
        return out


    def _text_roads(self):
        p = self.pet
        need = evolution.DIVERGE_NEED.get(p.stage)
        out = menu.header("DNA · DIVERGENCE",
                       "need %dc" % need if need is not None else "top stage")
        if not self._roads or need is None:
            out.append_text(menu.blanks(1))
            out.append_text(menu.note("No wild roads from this form."))
            out.append_text(menu.blanks(1))
            out.append_text(menu.row("Bank DNA for a later form.", False))
            out.append_text(menu.row("Charging now cannot arm a road.", False))
            out.append_text(menu.footer(""))
            return out
        armed = self._armed()
        flds = sorted(self._roads)
        self.road_i %= len(flds)
        out.append_text(menu.note("ARMED: next growth takes the road" if armed else
                                  "Unique leader + road arms at %d" % need))
        out.append_text(menu.note("Charges clear at every evolution"))

        def fmt(f, i):
            chg = p.dna_applied.get(f, 0)
            mark = "▶" if f == armed else " "
            return "%s%-17s %2d / %-2d %d forms" % (mark, _field_word(f, 17),
                                                   chg, need, len(self._roads[f]))

        self.road_i = menu.list_window(out, flds, self.road_i, 6, fmt)
        return menu.page(out, "Ties disarm; need a road")

    def _target_name(self, num):
        # DNA audit 2026-10-14: roads obey the same reveal rule as DigiCore.
        if data.load_requirements().get(num, {}).get("hidden_evo") \
                and not persistence.album_seen(num):
            return "???"
        return data.load_sprites()[1].get(num, {}).get("name", "?")

    def _text_road_detail(self):
        targets = sorted(set(self._roads[self.field]))
        self.target_i %= len(targets)
        out = menu.header(data.pretty_field(self.field),
                       "%d / %d forms" % (self.target_i + 1, len(targets)))
        # The selected name wraps in full; no destination vanishes after two names.
        name = Text(self._target_name(targets[self.target_i]))
        wrapped = name.wrap(Console(width=menu.W), menu.W)
        for line in wrapped:
            out.append_text(line + Text("\n"))
        out.append_text(menu.note("Road options; final pick at growth"))
        self.target_i = menu.list_window(out, targets, self.target_i,
                                        max(1, 8 - len(wrapped)),
                                        lambda num, i: self._target_name(num))
        out.append_text(menu.footer(""))
        return out

    def _text_bet(self):
        p = self.pet
        out = menu.header("DNA · GENERATE", "%db" % p.bits)
        out.append_text(menu.note("Wager bits, then mash for DNA."))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("wager: %4d b" % self.bet, True))
        # the LIVE tier readout (DNA ruling 2026-07-18): every amount says
        # what it actually buys -- the 100-499 band used to pay extra for
        # nothing, silently
        if self.bet >= DNA_RESONANT_BET:
            tier = "RESONANT: up to 99/adjacent Field"
        elif self.bet >= DNA_STABILIZER_BET:
            tier = "STABILIZED: up to 99, never None"
        else:
            tier = "banks up to %d" % self.bet
        out.append_text(menu.row(tier[:38], False))
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("mash rate selects a Field", False))
        if self.bet >= DNA_STABILIZER_BET:
            out.append_text(menu.row("stabilized — it never rolls None", False))
        else:
            out.append_text(menu.row("too slow / fast → half back", False))
        out.append_text(menu.footer(""))
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
            fld = _field_word(dna_award_field(self.bet, rate), 9)
            # DNA audit 2026-10-14: even an extreme extrapolated rate fits 40 cells.
            shown_rate = str(rate) if rate <= 999 else "999+"
            return ("%s r%s→[b]%s[/] %.1fs SPACE"
                    % (self._meter(rate), shown_rate, fld, left))
        if self.phase == "charge":
            return menu.hints(("↑↓", "pick"), ("←→", "±"),
                              ("ENTER", "charge"), ("ESC", "back"))
        if self.phase == "bet":
            return menu.hints(("←→", "±1"), ("↑↓", "tier"),
                              ("ENTER", "mash!"), ("ESC", "back"))
        if self.phase == "result":
            return menu.hints(("any key", "continue"))
        if self.phase == "roads":
            return menu.hints(("↑↓", "pick"), ("ENTER", "open"), ("ESC", "back"))
        if self.phase in ("stats", "road_detail"):
            return menu.hints(("↑↓", "pick"), ("ESC", "back"))
        return menu.hints(("↑↓", "pick"), ("ENTER", "open"), ("ESC", "back"))

    def _text_result(self):
        field, wager, rate, banked, refund = self.won
        show = self.blink >= 8 or (self.blink // 2) % 2 == 0  # reveal, then hold readable
        name = data.pretty_field(field)
        out = menu.header("DNA · GENERATE", "rate %d" % rate)
        out.append_text(menu.blanks(1))
        got = ("✗ Spoiled mash" if field == "None"
               else "✓ Got %d %s DNA" % (banked, name))
        out.append_text(menu.note(got if show else "✓"))
        out.append_text(menu.note("Refund: %db" % refund))
        out.append_text(menu.row("rate %d → %s" % (rate, name if show else ""), True))
        if field == "None":
            out.append_text(menu.row("spoiled — half the wager back", False))
        elif wager >= DNA_RESONANT_BET:
            # DNA audit 2026-10-14: show actual landed deltas, not the uncapped splash.
            for f, gained in self.splashed.items():
                out.append_text(menu.row("+%d %s DNA" % (gained, data.pretty_field(f))))
        else:
            out.append_text(menu.row("banked — open Charge to use it", False))
        out.append_text(menu.footer(""))
        return out
