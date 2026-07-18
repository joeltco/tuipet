"""The pet's DNA organ (tier-5, 2026-07-17): the banked/charged arrays,
the wager minigame award, and applyDNA's energy bill."""
from __future__ import annotations
import math  # noqa: F401
import random  # noqa: F401

from . import backgrounds  # noqa: F401
from . import data  # noqa: F401
from . import egg as egg_mod  # noqa: F401
from . import evolution  # noqa: F401
from . import lines as lines_mod  # noqa: F401
from . import shop  # noqa: F401
from . import theme  # noqa: F401
from .petbase import *  # noqa: F401,F403  (constants resolve HERE, per mixin)


class DnaMixin:
    """State contract: the Pet dataclass fields; composed into Pet."""

    # ---- DNA (DVPet DNA.class) -------------------------------------------
    def highest_dna(self):
        """DNA.getHighestDNA: the CHARGED field with the strict maximum -- a tie
        (or nothing charged) yields none (the caller falls back to the field)."""
        best, best_f = 0, ""
        for f in data.DNA_FIELDS:
            v = self.dna_applied.get(f, 0)
            if v > best:
                best, best_f = v, f
        if best and sum(1 for f in data.DNA_FIELDS
                        if self.dna_applied.get(f, 0) == best) == 1:
            return best_f
        return ""

    def dna_total(self):
        return sum(self.dna_applied.get(f, 0) for f in data.DNA_FIELDS)

    def dna_percent(self, field):
        """DNA.getPercent: this field's share of all charged DNA (the evolution gate)."""
        t = self.dna_total()
        return int(100 * self.dna_applied.get(field, 0) / t) if t else 0

    def can_charge_dna(self):
        # the shared _guard gate, keeping the DNA-flavoured egg line
        # (tidy audit 2026-07-18: dead/asleep were duplicated literals)
        if not self.dead and self.stage == "Egg":
            return "An egg has no DNA yet."
        return self._guard()

    def dna_bet(self, amount):
        """DVPet DNA_GenerateValidate (onEnter): pay the wager up front, before the mash
        mini-game runs. Returns False (and jeers) if the pet can't afford it."""
        if amount <= 0 or not self.spend_bits(amount):
            self._set_anim("refuse", 1.0)                   # Jeering: can't afford the wager
            return False
        return True

    def dna_minigame_award(self, amount, rate):
        """DVPet onDNAGenerate: the mash `rate` picks the Field; bank `amount` DNA of it
        (the wager was already spent in dna_bet). Overflow past the 99 cap refunds as
        bits, exactly like the device. Returns the Field won ("None" = wasted).

        High-stakes wagers (2026-07-14): only min(amount, 99) is bankable volume --
        the premium above the cap is LAB WORK and never refunds. A STABILIZED
        wager (>=500) clamps a spoiled rate into the nearest real band; a
        RESONANT one (>=2500) splashes amount//5 DNA into the two adjacent
        Fields (capped, no refund)."""
        field = dna_field_for_rate(rate)
        if field == "None" and amount >= DNA_STABILIZER_BET:
            rate = min(max(rate, DNA_RATE_BANDS[0][0] + 1), DNA_RATE_BANDS[-1][0])
            field = dna_field_for_rate(rate)
        gained = min(amount, MAX_DNA_INVENTORY)
        total = self.dna_owned.get(field, 0) + gained
        if total > MAX_DNA_INVENTORY:
            self.bits += total - MAX_DNA_INVENTORY          # refund the overflow as bits
            total = MAX_DNA_INVENTORY
        self.dna_owned[field] = total
        if amount >= DNA_RESONANT_BET and field != "None":
            splash = amount // 5
            fields = [f for _, f in DNA_RATE_BANDS if f != "None"]
            i = fields.index(field)
            for j in (i - 1, i + 1):
                if 0 <= j < len(fields):
                    nb = fields[j]
                    self.dna_owned[nb] = min(self.dna_owned.get(nb, 0) + splash,
                                             MAX_DNA_INVENTORY)
        return field

    def apply_dna(self, field, amount):
        """PhysicalState.applyDNA: owned -> charged.  The live bill is ENERGY
        (1/unit own Field, x2 off) + the strength ceiling below; canon's
        disturb/mood/spirit/sick costs left with their systems."""
        owned = self.dna_owned.get(field, 0)
        if amount <= 0 or owned < amount:
            self._set_anim("refuse", 1.0)                   # Jeering: not enough DNA
            return False
        self.dna_owned[field] = owned - amount
        self.dna_applied[field] = self.dna_applied.get(field, 0) + amount
        # canon calls disturb() -- a NO-OP on an awake pet (its whole body is
        # asleep-gated); the old `disturb += 1` falsely marked the evolution
        # counter on every charge (jogress/DNA audit 2026-07-06).  The asleep
        # case never reaches here: can_charge_dna disturbs and blocks first.
        # applyDNA strength: overflowing the Effort gauge lands at limit-1, NOT
        # the cap (setExercise(getExerciseLimit() - 1)) -- DNA can't top you
        # off.  Canon's limit is the species MaxStrength (4..14); tuipet's
        # gauge is the real toy's FOUR HEARTS everywhere (UI/training/decay),
        # so the limit folds to 4 -- the established design, kept.  The cap is
        # limit-1 (=3), but it is a CEILING, never a penalty: a pet already at
        # 4 (trained to full) keeps its heart -- on the real device limit-1 of
        # a wide byte gauge is no real drop; the 4-heart fold turned that into
        # a whole heart, so clamp up-only (DNA audit 2026-07-08).
        gain = DNA_STRENGTH_CHANGE * amount
        self.strength = max(self.strength, min(self.strength + gain, 3))
        same = field == self.field
        # the charge bill (see the constants): energy, doubled off-field --
        # the mood/spirit bills left with their systems
        self._set_energy(self.energy
                         - (DNA_SAME_FIELD_ENERGY if same else DNA_DIFF_FIELD_ENERGY) * amount)
        # (applyDNA's per-unit sickness risk left with the sickness system
        # (BASIC VPET 2026-07-17) -- the ENERGY bill above is the charge's cost now)
        return True

    def reset_dna(self):
        """DNA.resetDNA (via resetEvolVar): charged DNA clears on evolution; owned inventory persists."""
        self.dna_applied = {f: 0 for f in data.DNA_FIELDS}

