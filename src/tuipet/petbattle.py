"""The pet's BATTLE ledger (tier-5, 2026-07-17): eligibility, the drill
result, record_battle's canon bookkeeping (wins/exp/KO6/setPower), and
the attribute-rank machinery."""
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


class BattleMixin:
    """State contract: the Pet dataclass fields; composed into Pet."""

    def _power_bonus_attr(self):
        """set{Vaccine,Data,Virus}Power's bonus gate: the attribute whose gains
        a HAPPY pet doubles -- its own attribute (any stage), or for a None/
        Free-attribute pet past InTraining its EMERGENT favourite (the ledger
        drifts now; the AttributePreference seed stands in until one forms)."""
        if self.attribute in ("Vaccine", "Data", "Virus"):
            return self.attribute
        if self.stage in ("Fresh", "InTraining"):
            return "None"
        return self.favorite_attr or self._phys().get("attr_pref", "None")

    def _change_rank(self, cat):
        """Taste.changeRank: bump the eaten category's rank (+/- species pref bias); eating
        your current favourite/disliked pulls the OTHER ranks back toward 0; clamp to
        +/-RankLimit; a rank that reaches the cap becomes the new favourite/disliked."""
        pref, aver, _ = self._species_food()
        delta = RANK_CHANGE_FOOD
        if cat == pref:
            delta += RANK_PREF_INC
        elif cat == aver:
            delta -= RANK_PREF_INC
        if cat == self.disliked_food:
            delta += RANK_DISLIKED
            for c in data.FOOD_CATEGORIES:                 # incRankExcept toward 0
                if c != cat and self.food_ranks[c] < 0:
                    self.food_ranks[c] = min(0, self.food_ranks[c] + RANK_AFTER_FAV)
        if cat == self.favorite_food:
            for c in data.FOOD_CATEGORIES:                 # decRankExcept toward 0
                if c != cat and self.food_ranks[c] > 0:
                    self.food_ranks[c] = max(0, self.food_ranks[c] - RANK_AFTER_FAV)
        self.food_ranks[cat] = _clamp(self.food_ranks[cat] + delta, RANK_MIN, RANK_LIMIT)
        for c in data.FOOD_CATEGORIES:
            if self.food_ranks[c] >= RANK_LIMIT:
                self.favorite_food = c
            elif self.food_ranks[c] <= RANK_MIN:
                self.disliked_food = c

    def _rank_stage_inc(self):
        """RankChangeStage*Inc: young pets form tastes faster (+3/+2/+1)."""
        return RANK_STAGE_INC.get(self.stage, 0)

    def _promote_attr_ranks(self):
        """A rank at +-RankLimit becomes the emergent favourite/disliked
        (simplified from Taste.setNewFavDislike like the food port: no
        repeat-collision reroll -- all three attributes are valid both ways)."""
        for a in self._ATTR3:
            if self.attr_ranks[a] >= RANK_LIMIT and self.favorite_attr != a:
                self.favorite_attr = a
                if self.disliked_attr == a:
                    self.disliked_attr = ""
            elif self.attr_ranks[a] <= RANK_MIN and self.disliked_attr != a:
                self.disliked_attr = a
                if self.favorite_attr == a:
                    self.favorite_attr = ""

    def _change_attr_rank(self, attr):
        """Taste.changeRank for the attribute ledger: a drill warms the pet to
        its attribute (stage-scaled base, +-2 species preference/aversion
        bias); drilling the current favourite decays the others toward 0."""
        if attr not in self._ATTR3:
            return
        req = self._phys()
        delta = RANK_CHANGE_ATTR + self._rank_stage_inc()
        if attr == req.get("attr_pref", "None"):
            delta += RANK_PREF_INC
        elif attr == req.get("attr_aversion", "None"):
            delta -= RANK_PREF_INC
        if attr == self.disliked_attr:
            delta += RANK_DISLIKED
            for a in self._ATTR3:                          # incRankExcept toward 0
                if a != attr and self.attr_ranks[a] < 0:
                    self.attr_ranks[a] = min(0, self.attr_ranks[a] + RANK_AFTER_FAV)
        if attr == self.favorite_attr:
            for a in self._ATTR3:                          # decRankExcept toward 0
                if a != attr and self.attr_ranks[a] > 0:
                    self.attr_ranks[a] = max(0, self.attr_ranks[a] - RANK_AFTER_FAV)
        self.attr_ranks[attr] = _clamp(self.attr_ranks[attr] + delta, RANK_MIN, RANK_LIMIT)
        self._promote_attr_ranks()

    def _dec_attr_rank(self, attr, change):
        """decRankAndCheckFavDislikeChange: a bad experience keyed to an
        attribute sours it (None = all three, like canon's disturb(None))."""
        for a in ([attr] if attr in self._ATTR3 else self._ATTR3):
            self.attr_ranks[a] = _clamp(self.attr_ranks[a] - change, RANK_MIN, RANK_LIMIT)
        self._promote_attr_ranks()

    def can_train(self):
        """The source's drill gates (canon gates 2026-07-18, decompile
        L11697): a starving, sick, drained or filth-flanked pet refuses the
        drill with the head-shake.  (The energy line keeps the clone's own
        threshold -- too drained to SWING, a standing adaptation.)"""
        if (_g := self._guard()) is not None:
            return _g
        if self.hunger <= 0:
            self._set_anim("refuse", 1.0)
            return "Too hungry to train."
        if self.sick:
            self._set_anim("refuse", 1.0)
            return "Too sick to train."
        if self.poop:
            self._set_anim("refuse", 1.0)
            return "Clean up first!"
        if self.energy < TRAIN_ENERGY_COST:
            self._set_anim("refuse", 1.0)
            return "Too tired to train."
        return None

    def can_raid(self):
        """The raid gate (tidy audit 2026-07-18: appactions hand-rolled its
        own dead/egg/asleep with third wordings, and a raid press was the
        one poke that DIDN'T disturb a sleeper).  Youth still outranks
        sleep -- a too-young pet is never woken just to be refused."""
        if (g := self._guard(asleep_blocks=False)) is not None:
            return g
        if self.stage == "Fresh":
            return "Too young for a raid."
        if self.asleep:
            return self._disturbed()
        return None

    def max_health(self):
        """PhysicalState.getMaxHealth: the trained-HP CAP rises with lapsed life."""
        days = self.age_seconds / DAY_LENGTH
        for d, cap in HEALTH_CAP_LADDER:
            if days >= d:
                return cap
        return MAX_HEALTH_DEFAULT_CAP

    def _check_perfect_wins(self, force=True):
        """checkAndIncPerfectWins: every HP-drill success counts (force ==
        PracticeAlwaysIncPerfectWins TRUE) and every BATTLE WIN counts while the
        trained HP sits below its age cap (force=False rides canon's gate --
        Min{Strength,Hunger} are 0 at difficulty 0, so the HP-below-max clause
        is the whole test); each PerfectWinsLimit-th grows fullHealthPoints
        (HealthInc when it actually lands)."""
        if not force and self.full_health >= self.max_health():
            return ""
        self.perfect_wins += 1
        if self.perfect_wins % PERFECT_WINS_LIMIT == 0:
            before = self.full_health
            self.full_health = min(self.max_health(), self.full_health + PERFECT_WINS_HEALTH_INC)
            if self.full_health > before:
                return " HP +1!"                     # State.HealthInc
        return ""

    def train_result(self, success):
        """One clone drill (0.5 rules): energy -2 (floored at 0), the
        counters that feed the LINES TR gates, and a clean strike sheds a
        little weight.  The verdict pose mirrors the old drills' cheer/sad
        tell so the after-train fx keep working."""
        self._calm_discipline_call()                 # a drill placates the call
        self.exercise_today += 1
        self.stage_trainings += 1                    # LINES_SPEC TR gate: every attempt counts
        self.total_trainings += 1                    # lifetime (the 0.5 hit formula reads it)
        # the Effort meter fills per drill, win or lose (canon setExercise +1;
        # Joel 2026-07-17 "its not filling the effort meter?" -- the clone left
        # strength to the pill, but the gauge visibly ticking up per drill is
        # the shipped feel and the DM20 rule)
        self.strength = _clamp(self.strength + 1, 0, 4)
        self._set_energy(max(0, self.energy - TRAIN_ENERGY_COST))
        # the source sheds weight-2 on EVERY drill, win or lose (canon gates
        # 2026-07-18, decompile L11701) -- floored at the species BASE, not
        # at 1: the bare clone floor fattened a light classic pet (caught
        # live 2026-07-17; the adaptation stands)
        if self.weight > self._base_weight():
            self._set_weight(max(self._base_weight(), self.weight - 2))
        self._set_anim("happy" if success else "sad", 1.8)
        return True

    def can_battle(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage in ("Egg", "Fresh"):
            return "Too young to battle."
        if self.asleep:
            return self._disturbed()
        self._calm_discipline_call()                         # canBattle placates the tantrum
        # the source's battle gates (canon gates 2026-07-18, decompile
        # L11746/11813): a starving, drained, sick or filth-flanked pet
        # refuses the fight with the head-shake
        if (cond := self.battle_condition()) is not None:
            self._set_anim("refuse", 1.0)
            return cond
        if self.check_refused():                             # canBattle -> checkRefused
            return f"{self.name} refuses to fight!"
        return None

    def battle_condition(self):
        """The PURE condition half of can_battle -- no disturb, no anim, no
        refusal roll.  ONE source for every recorded bout: the cup and the
        invite-accept side used to skip these entirely, so a pet too
        starved/sick/drained to SEND a challenge could still grind three
        recorded cup battles per cup and auto-accept incoming invites
        (gameplay audit 2026-07-19)."""
        if self.hunger <= 0:
            return "Too hungry to fight."
        if self.energy < BATTLE_MIN_ENERGY:
            return "Too drained to fight."
        if self.sick:
            return "Too sick to fight."
        if self.poop:
            return "Clean up first!"
        return None

    def record_battle(self, won, enemy=None, online=False, source="battle",
                      free_style=None, low_health=False):
        """One battle, the 0.5 rules (clone record_battle, 2026-07-17):
        counters + flat costs, +2 trainings for a LOCAL bout.  KEPT from the
        classic version -- the progression channels the rest of the game
        feeds on: battle_log (Pen20 WIN gates), stage_battles (BTL gates),
        lifetime wins + the mystery-egg note, levels_fought, KO6 (a felled
        Mega, never in PvP -- untrusted cards), and the win's +1 power in
        the foe's attribute (the corpus checkStatTotal gates feed on it; a
        0.5 card's attribute string names the dominant power directly).
        The old free_style/low_health params are accepted-and-ignored for
        stragglers.  (Mood/compliance/contagion legs left with their
        systems; the perfect-wins HP ladder left with the classic battle.)"""
        if source == "pvp":
            online = True
        self.battles += 1
        self.stage_battles += 1                          # LINES_SPEC BTL gate (per-stage)
        self.battle_log = (self.battle_log + [1 if won else 0])[-15:]   # Pen20 rolling window
        self._set_energy(max(0, self.energy - BATTLE_ENERGY_COST))
        self._set_weight(max(1, self.weight - BATTLE_WEIGHT_COST))
        if not online:
            self.stage_trainings += 2                    # a local bout trains (clone rule)
        if not won:
            return ""
        self.wins += 1
        if not online:
            # DMX canon: defeating an enemy pays experience toward LEVEL (the
            # LV line gates).  PvP excluded like KO6 -- colluding tamers could
            # farm level-gated evolutions off untrusted cards.
            self.exp += EXP_PER_WIN
        from . import persistence as _persist
        total = _persist.wins_add(1)                     # lifetime wins (egg gates)
        if total in egg_mod.wins_thresholds():
            # a lifetime-wins egg gate just crossed (Zuba 75 / Hack 40 / V 25 /
            # Sakumon 50 / Chibickmon 10...): flash the nursery note
            self.egg_unlock_note = "A new egg appeared in the nursery!"
        if enemy:
            self.levels_fought.append(_enemy_level(enemy))
            # KO6: Stage VI is Mega, full stop; PvP excluded (untrusted
            # cards -- colluding tamers could farm it; egg/KO6 audit 2026-07-14)
            if enemy.get("stage") == "Mega" and not online:
                self.mega_kills += 1                     # LINES_SPEC KO6 gate
                _persist.mega_kills_add(1)               # ...and the X-egg progress
            # the win grows the pet's power in the foe's attribute (+1; a
            # HAPPY pet's favoured attribute doubles it, canon setPower)
            dom = enemy.get("attribute")
            if dom in self._ATTR3:
                inc = 1
                if self.current_mood() == "Happy" and dom == self._power_bonus_attr():
                    inc += BONUS_ATTRIBUTE_POWER
                if dom == "Vaccine":
                    self.vaccine += inc
                elif dom == "Data":
                    self.data_power += inc
                else:
                    self.virus += inc
        return "training +2" if not online else ""

    def can_escape(self, enemy):
        """PhysicalState.canEscape: a power-weighted roll -- prob = nextInt(mine +
        theirs); escaped iff prob <= mine, the foe's side padded by
        BossEscapeChance 50 / RandomEscapeChance 10 (bosses hold you harder)."""
        mine = self.vaccine + self.data_power + self.virus + (self.full_health or 1)
        theirs = (enemy.get("vaccine", 0) + enemy.get("data_power", 0)
                  + enemy.get("virus", 0) + enemy.get("hp", 0)
                  + (50 if enemy.get("boss") else 10))     # Boss/RandomEscapeChance
        return random.randrange(max(1, mine + theirs)) <= mine

    def check_surrender(self, health, enemy_health, enemy_max_health, full_hp):
        """Always 0 (fight on): the pet-initiated surrender/flee rode the
        obedience formula and left with the discipline system (BASIC VPET
        2026-07-16).  The PLAYER's surrender option stands."""
        return 0

    def surrender_effect(self, surrender_val, health, enemy_health):
        """ClockTic.surrenderEffect: the morale aftermath when the pet gives up (1) or
        its surrender request is accepted (2)."""
        self._set_mood(self.mood + SURR_EFFECT_MOOD_INC)
        if surrender_val == 1 and self._disposition() < 0 and health >= enemy_health:
            self._set_mood(self.mood - SURR_EFFECT_LOWDISP_MOOD_DEC)
        if health >= enemy_health:
            self._set_obedience(self.obedience
                                - (SURR_EFFECT_REQ_OBED_DEC if surrender_val == 2 else SURR_EFFECT_OBED_DEC))
        if surrender_val == 2 and health < enemy_health:
            self._set_obedience(SURR_EFFECT_REQ_LOWHP_OBED)      # setObedience(15), verbatim (a SET, not +=)

    def surrender_reject(self):
        """ClockTic: the trainer refuses the pet's surrender request (surrender==2) and
        sends it back in — it sulks but obeys a touch more.  If it then LOSES,
        battleEnd SETS obedience to 10 (the declined-request grudge).

        DORMANT since the 0.5 BATTLE rewrite (2026-07-17): nothing calls this
        cluster (surrender_reject / surrender_effect / check_surrender /
        can_escape), record_battle never reads _surr_declined, and
        SURR_DECLINED_LOST_OBED is unapplied -- the old comment claimed
        otherwise (gameplay audit 2026-07-19).  Kept as the canon reference
        for a battle flow that asks again; dormant stays dormant."""
        self._set_mood(self.mood - SURR_REJECT_MOOD_DEC)
        self._set_obedience(self.obedience + SURR_REJECT_OBED_INC)
        self._surr_declined = True                       # no live consumer (see above)

