"""The pet's CARE surface (tier-5, 2026-07-17): every player-initiated
act -- feeding, cleaning, items and the shop verbs, gifts, discipline and
the refusal rolls."""
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


class CareMixin:
    """State contract: the Pet dataclass fields; composed into Pet."""

    # (the DVPet furniture -- toilet training / the self-toilet / the manual
    # visit / the Futon tuck-in and its careEffect -- left with the staple
    # props: strict-DSprite items, 2026-07-17.  Poop lands on the floor and
    # the clean action washes it, full classic.)

    def check_refused(self, food=None, attr=None, energy_change=0.0, item=None):
        """The obedience refusal roll left with the discipline system (BASIC
        VPET 2026-07-16): the pet obeys care commands.  TWO meter rules
        survive because they are affordability, not temperament: the energy
        auto-refuse (a jogress/digimental/mode-change it cannot pay for) and
        feed()'s own full-belly head-shake."""
        self.refused = False
        if energy_change and self.energy + math.ceil(energy_change * self.max_energy) < 0:
            self._set_anim("refuse", 1.5)
            return True                  # can't afford the energy -> auto-refuse
        return False

    def manners_refusal(self, kind):
        """EARNED DISOBEDIENCE (D3, 2026-07-23): a NEGLECTED pet blows off
        a command.  True == it refused.

        Deliberately a SEPARATE door from check_refused: that one is
        AFFORDABILITY (the energy auto-refuse) and its only callers are
        the jogress and mode-change paths -- both EVOLUTION doors, and
        both outside the shape Joel approved.  Wiring manners into it
        would have silently started refusing evolutions (plan audit P2).

        Refusable: feed, train, battle.  NEVER clean, and never the pill
        or the bandage -- a pet you cannot clean or heal is a softlock,
        not a personality.  Feeding is also never refused while the belly
        is EMPTY: starvation kills, and no amount of attitude should be
        able to close the only door that saves it."""
        if kind not in ("feed", "train", "battle"):
            return False
        if kind == "feed" and self.hunger <= 0:
            return False                       # never starve a pet out of spite
        gap = DISOBEY_BELOW - self.obedience              # noqa: F405
        if gap <= 0:
            return False                       # well-raised: NEVER refuses
        p = min(1.0, gap / DISOBEY_BELOW) * DISOBEY_MAX_P  # noqa: F405
        if random.random() >= p:
            return False
        self.refused = True
        self._set_anim("refuse", 1.5)
        return True

    def refuse_attack(self, my_hp, enemy_hp):
        """Always False: the Orders-style mid-fight refusal left with the
        discipline system."""
        return False

    def stop_travel_prob(self):
        """PhysicalState.checkStopTravel as a per-fire PROBABILITY (the caller
        composes it over a full stride).  One draw per controller fire,
        r in [cap, cap + chance*3000); the energy fraction scales the draw
        DOWN, so a rested pet essentially never stops but a drained one plants
        its feet: refuse when r*(energy+1)/max - dispo*35 + obey - 5
        <= cap - obedience."""
        # the obedience walk-refusal left with the discipline system
        # (BASIC VPET 2026-07-16): only a truly DRAINED pet plants its feet
        energy_mod = 1.0 - (self.max_energy - (self.energy + 1)) / max(1, self.max_energy)
        return 1.0 if energy_mod <= 0 else 0.0

    def stop_travel_effects(self):
        """The refusal's side effects (split from the roll so it can compose)."""
        self.refused = True
        self._set_anim("refuse", 1.5)

    def check_stop_travel(self):
        """One canonical per-fire draw (kept for tests/direct callers)."""
        if random.random() < self.stop_travel_prob():
            self.stop_travel_effects()
            return True
        return False

    def check_compliant(self):
        """Always False ("never grudging"): compliance left with the
        discipline system.  Canon's True meant "it obeyed only because you
        spent its compliance token" -- the resentment branches (forced-feed
        rank souring, forced-fatigue obedience bills, grudging weak item
        application) key on it, so the willing constant is False."""
        return False

    def can_feed(self):
        """Guard for opening the feed menu (mirrors feed()'s own gates)."""
        if (_g := self._guard()) is not None:
            return _g
        return None

    def feed(self, food=None, assisted=False):
        """The DSprite feed (BASIC VPET 2026-07-16, cloned from v0.4.x): the
        F menu picks MEAT or PILL; the whole DVPet food catalog -- taste
        tiers, nutrition macros, calories, food evolutions -- left with it.
        Kept as the meat entry so the assistant and old callers still feed."""
        return self.feed_meat()

    def feed_meat(self, assisted=False):
        """Meat: hunger +1, weight +1.  The source's refusal gates (canon
        gates 2026-07-18, decompile L11676): a sick pet, a pet beside its
        own filth, or a full belly gets the head-shake and NOTHING else --
        the DVPet overeatPenalty (weight+1, mistake+1, bowel shove) left
        with it.  The overeat COUNTER still ticks: the evolution corpus's
        OF gates read it, and a full-belly attempt IS the overfeed signal.
        Feeding a sleeper DISTURBS it first (refusals don't wake it).

        assisted=True is the AI ASSISTANT's serving: canon assistantFeed
        dishes the AI Food Pill (AutoCareHungerFoodID 44), which a SICK
        pet still accepts -- routing the visit through YOUR meat's sick
        refusal made the assistant bill every visit for a head-shake while
        the pet starved (assistant audit 2026-07-19)."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        if self.sick and not assisted:
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too sick to eat — try the pill."
        if self.poop:
            self._set_anim("refuse", 1.0)
            return "Clean up first!"
        if self.hunger >= FULL_HUNGER:
            # THE OVERFEED PENALTY (D2, 2026-07-23): canon overeatPenalty
            # bills a stuffed pet -- weight piles on and it counts as a
            # care slip.  This branch was "penalty-free", which made
            # feeding the one care verb you could not get wrong; a vpet's
            # food has to be a decision.  The pet head-shakes FIRST, so
            # nothing is charged before you have been warned.  (The bag's
            # own foods refuse at a full belly and the assistant only
            # serves at hunger 0, so this is the single stuffing door.)
            self.overeat += 1                    # the OF-gate signal (evolution)
            self._set_weight(self.weight + 1)
            self.care_mistakes += 1
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full! (✗ overfed)"
        # (a HIRED assistant is never blown off -- you paid for that
        # visit; today the empty-belly exemption already covers it,
        # since auto-care only serves at hunger 0)
        if not assisted and self.manners_refusal("feed"):
            return f"{self.name} turns its nose up!"
        if self.asleep:
            self._disturbed()
        self._last_meal_starving = self.hunger == 0          # eat(): wolfed down
        self.hunger = _clamp(self.hunger + 1, 0, FULL_HUNGER)
        self._set_weight(self.weight + 1)
        # every meal advances the bowel gauge (applyFood: bmGauge += bmLapseInc)
        self._poop_t = getattr(self, "_poop_t", 0) \
            + self._poop_interval * self._phys().get("poop_lapse", 1) \
            / max(1, self._phys().get("poop_limit", 64))
        # (checkDirtyEating's filth-meal sickness risk left with the
        # sickness system (BASIC VPET 2026-07-17))
        self._set_anim("eat", 1.4)
        return "Fed Meat."

    def feed_pill(self):
        """The pill (clone rules): cures the sickness, strength +1, energy
        +7, weight +5.  Refused when there is nothing to cure or top up.
        Healing a sleeper DISTURBS it first.  (The classic spell machine
        left 2026-07-17; the DSprite flag is pill-cured ONLY.)  The pill is
        EATEN -- the source's EATING action, same as meat (pill-anim fix
        2026-07-18; the DVPet bandage anim left with it)."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        if self.poop:
            # the source refuses the pill beside filth too (canon gates
            # 2026-07-18, decompile L11677)
            self._set_anim("refuse", 1.0)
            return "Clean up first!"
        if not self.sick \
                and self.strength >= 4 and self.energy >= self.max_energy:
            self._set_anim("refuse", 1.0)
            return f"{self.name} doesn't need it."
        if self.asleep:
            self._disturbed()
        self.sick = False
        self.strength = _clamp(self.strength + 1, 0, 4)
        self._set_energy(self.energy + PILL_ENERGY_GAIN)
        self._set_weight(self.weight + PILL_WEIGHT_GAIN)
        self._last_meal_starving = False     # a tonic is never wolfed down
        self._set_anim("eat", 1.4)
        return "Took the pill."

    # ---- discipline: praise / scold, RESTORED (canon restoration B,
    # 2026-07-23, Joel: "it was wrongfully stripped... whatever is canon
    # bring back").  The device pair: SCOLD answers the tantrum call,
    # PRAISE answers a proud moment (a battle win, a mega drill).  The
    # gauge is `obedience` (0..100).  Refusals stay SOFT (standing rule);
    # discipline is the tantrum economy, not a leash. -----------------------
    def _open_praise(self):
        """A win or a mega drill opens a 600 game-min praise window
        (= ~10 REAL minutes; see THE UNIT LAW in petbody._tick_life --
        the label used to read "10 game-min", the P0b mislabel)."""
        self.praise_window = self.world_seconds + 600.0

    def _open_scold(self):
        """The tantrum's answer window: 600 game-min (~10 REAL minutes)
        before ignoring it counts."""
        self.scold_window = self.world_seconds + 600.0

    def _calm_discipline_call(self):
        """Bedtime (and canBattle, per canon) placates an open tantrum --
        no reward, no penalty, the moment just passes."""
        if self.discipline_call:
            self.discipline_call = False
            self.scold_window = 0.0

    def praise(self):
        """PRAISE: inside a proud-moment window it pays obedience +10 and
        the cheer; outside one, nothing -- the no-praise-farming rule
        (from the pre-strip discipline audit)."""
        if (_g := self._guard()) is not None:
            return _g
        if self.world_seconds <= getattr(self, "praise_window", 0.0):
            self.praise_window = 0.0
            self._set_obedience(self.obedience + 10)
            self._set_anim("happy", 1.8)
            return f"{self.name} beams with pride!"
        self._set_anim("happy", 1.0)
        return f"{self.name} looks pleased — but unsure why."

    def scold(self):
        """SCOLD: answering an open tantrum pays obedience +25 and the
        scolded sulk; scolding a calm pet just makes it sulk, no gain."""
        if (_g := self._guard()) is not None:
            return _g
        if self.discipline_call:
            self.discipline_call = False
            self.scold_window = 0.0
            self._set_obedience(self.obedience + 25)
            self._set_anim("sad", 1.8)
            return "Scolded — lesson learned."
        self._set_anim("sad", 1.4)
        return f"{self.name} sulks — it did nothing wrong."

    def clean(self):
        """PhysicalState.clean: wash the filth off the floor.  (The mood and
        obedience rewards this once paid are INERT -- both meters left with
        their systems 2026-07-16; the write-calls below are the standing
        no-op citations.)"""
        if (_g := self._guard()) is not None:
            return _g
        if not self.poop:
            return "Nothing to clean."
        n, self.poop = self.poop, 0
        self.poop_sizes = []                        # clearFilth()
        self._set_mood(self.mood + CLEAN_MOOD_INC)
        self._set_obedience(self.obedience + CLEAN_OBED_INC[self._disposition()])
        self._set_anim("wash", 1.2)
        return f"Cleaned {n} poop."

    def heal(self):
        """The pill (BASIC VPET 2026-07-16): the med/bandage staples left
        with the DVPet item system -- one staple treats everything, from the
        F menu (and the road's h key)."""
        return self.feed_pill()

    def set_auto_care(self, on):
        """SpriteAnim's Set_AutoCare switch -> PhysicalState.setAutoCare: hiring
        the assistant also rolls WHICH Digimon answers, from the digimon.csv
        CanAssist pool (Evolution.getRandomAssistDigimon)."""
        if self.dead:
            return "It rests now — press N for a new egg."
        self.auto_care = bool(on)
        if self.auto_care:
            pool = data.assist_pool()
            self.assistant_num = random.choice(pool) if pool else -1
            _, by_num = data.load_sprites()
            name = (by_num.get(self.assistant_num) or {}).get("name", "The assistant")
            return f"{name} is on duty."
        return "The assistant was dismissed."

    def toggle_lights(self):
        """The lights button (DVPet setLights): toggles the room light ONLY. The pet
        sleeps and wakes on its own schedule -- this does not force sleep or wake."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        self.lights = not self.lights
        if self.lights and self.asleep and self.nap:
            # lightSwitch: lights ON rouses a NAPPING pet (deep sleep ignores it;
            # sick or injured, the lost doze pushes bedtime a minute closer).
            # (canon !isFuton()'s nap shield left with the Futon: strict-DSprite
            # items, 2026-07-17)
            self._wake()                         # a nap wake rolls +-NapWakeMoodDec
            return "Lights on — up from its nap."
        if not self.lights and not self.asleep and self.energy <= 0:
            # the exhausted nag said "S — rest"; a flat "Lights off." read
            # as a no-op while the doze timer ran (QOL 2026-07-23)
            return f"Lights off — {self.name} settles down to rest…"
        return "Lights off." if not self.lights else "Lights on."

    # ---- shop / items --------------------------------------------------------
    # (buy_slot -- the town-counter purchase -- cut with the town chain
    # 2026-07-19; shop.buy is the ONE live purchase path)
    # (dead-code cut, LOW audit 2026-07-19: CareMixin.sell -- shop.sell is
    # the ONE live resell path -- plus _apply_item_stats (the DVPet
    # consumable core; the strict-DSprite item cut orphaned it), _fruit and
    # _erase_mistake (their items left the catalog; the textbook rides
    # _erase_mistakes_all).  Nothing live called any of them.)

    def _pick_gift(self):
        """The present pool (BASIC VPET 2026-07-16): a uniform pick from the
        DSprite catalog's treat tier (fruits and small care goods) -- the
        DVPet per-item GiftChance table left with the item system."""
        pool = ("fish", "cake", "energy_drink", "ball")
        return random.choice(pool)

    def claim_gift(self):
        """ClockTic.giftEnd: the present lands in the bag and the pet cheers."""
        key, self.gift = self.gift, ""
        if not key:
            return ""
        e = shop.entry(key) or {}
        self.add_item(key)
        self._set_anim("happy", 2.0)                # giftEnd -> State.Cheering
        return f"{self.name} gives you {e.get('name', 'a present')}!"

    def add_item(self, key, n=1):
        """Drop loot / grants straight into the bag."""
        self.inventory[key] = self.inventory.get(key, 0) + n

    def take_item(self, key, n=1):
        """Spend n from the bag, dropping the key at zero -- add_item's mirror
        (this decrement lived in four hand-rolled copies; refactor 2026-07-05)."""
        left = self.inventory.get(key, 0) - n
        if left <= 0:
            self.inventory.pop(key, None)
        else:
            self.inventory[key] = left

    def spend_bits(self, price):
        """The affordability gate + deduction in ONE place (the 'Not enough
        bits.' guard lived in four copies).  True when paid."""
        if self.bits < price:
            return False
        self.bits -= price
        return True

    def _compensate_attrs(self):
        """compensateAttributes x3 rotations: each negative power borrows from
        the next two in canon's order.  (Canon's zero-all escape only fires
        when all THREE are negative -- with both banks empty its loop would
        spin forever; unreachable with the shipped symmetric trades, and the
        port floors the deficit at 0 instead of freezing.)"""
        def comp(main, weak, normal):
            while main < 0:
                if weak > 0:
                    weak -= 1
                    main += 1
                if main < 0 and normal > 0:
                    normal -= 1
                    main += 1
                if weak <= 0 and normal <= 0 and main < 0:
                    return 0, weak, normal       # the safe floor (see docstring)
            return main, weak, normal
        v, d, vi = self.vaccine, self.data_power, self.virus
        v, d, vi = comp(v, d, vi)
        d, vi, v = comp(d, vi, v)
        vi, v, d = comp(vi, v, d)
        self.vaccine, self.data_power, self.virus = v, d, vi

    def use_item(self, key):
        """Consume one inventory item -> a short result message ('' = the
        item does nothing here, None-equivalent = don't have it).  The
        DSprite item table, cloned from v0.4.x (BASIC VPET 2026-07-16): the
        DVPet consumable machine -- meds, bandages, vitamins, toys, futons,
        transports, digimentals, crafters -- left with the item system.  A
        _Refused message keeps the item ('consume on refusal' burned
        Rev.Floppies on live pets; clone audit 2026-07-15)."""
        if self.inventory.get(key, 0) <= 0:
            return "None left."
        # the crest eggs (Armor-Spirit): the ONE clone item family that maps
        # onto a classic system -- each virtue joins its Digimental's
        # EvolItemID, so the armor evolutions stay reachable (the dub swap is
        # deliberate: reliability->Purity(18), destiny->Fate(25))
        if key.startswith("egg_of_"):
            return self._crest_egg(key)
        fx = {
            # ---- FOOD (the TUIPET catalog, 2026-07-18) ----------------------
            "fish": lambda: self._snack(hunger=1),
            "vegetable": lambda: self._snack(hunger=1, weight=-1),
            "tuna": lambda: self._snack(hunger=2, energy=1),
            "cake": lambda: self._snack(hunger=1, energy=2, weight=2),
            "cupcake": lambda: self._snack(hunger=1, energy=1),
            "cookie": lambda: self._snack(hunger=1, energy=1),
            "candy": lambda: self._snack(hunger=1, energy=1),
            "cheese_burger": self._junk,
            "giga_meal": self._giga_meal,
            "steak": self._premium_meat,
            "poison_mushroom": self._deadly,
            # ---- CARE -------------------------------------------------------
            "energy_drink": self._energy_drink,
            "slim_drink": self._super_carrot,
            "vitamin": self._vitamin,
            "bandage": self._bandage,
            "sleeping_pill": self._sleep_pill,
            "caffeine_pill": self._caffeine,
            "music_player": self._alarm,
            "textbook": self._erase_mistakes_all,
            "port_potty": self._smart_potty,
            # ---- GROWTH -----------------------------------------------------
            "dumbbell": self._training_pack,
            "grow_capsule": self._time_gear,
            "anti_evo_chip": self._anti_evo,
            "x_antibody": self._x_item,
            "dna_crystal": self._dna_crystal,
            "revive_floppy": self._revive_item,
            "digimemory": self._inherit_memory,
            # ---- TOYS (small LIVE dials; the SHOW is fired by the bag panel)
            "ball": lambda: self._toy(weight=-1, msg="A grand kickabout!"),
            "skateboard": lambda: self._toy(weight=-2, energy=-1,
                                            msg="It shreds!"),
            "xylophone": lambda: self._toy(energy=2, msg="A lovely recital."),
            "video_game": lambda: self._toy(energy=2, weight=1,
                                            msg="One more level…"),
            "television": lambda: self._toy(energy=3, weight=1,
                                            msg="Glued to the screen."),
            "bubble_bath": self._bubble_bath,
            "cold_shower": self._cold_shower,
            # ---- ADVENTURE (spent ON THE ROAD, not from the home bag) -------
            "town_transport": lambda: _Refused("Save it for the road (press T)."),
            "disaster_transport": lambda: _Refused("Save it for the road (press T)."),
            "life_recovery": lambda: _Refused("Restores adventure lives — use it on the road."),
        }.get(key)
        if fx is None:
            return ""
        # life-state guard: only the Rev.Floppy works on the dead, and
        # NOTHING works on an egg
        if self.dead and key != "revive_floppy":
            return _Refused("")
        if self.stage == "Egg" or self.num < 0:
            return _Refused("")
        # item on a sleeper: the alarm wakes mistake-FREE (its whole point),
        # the sleeping pill is pointless, the cold shower runs its OWN disturb
        # (same law, applied inside so "AWAKE and bracing" can be true),
        # anything else DISTURBS -- then applies
        if self.asleep and key not in ("music_player", "sleeping_pill",
                                       "cold_shower"):
            self._disturbed()
        out = fx()
        if not isinstance(out, _Refused) and out is not None:
            self.take_item(key)
        return out

    def _crest_egg(self, key):
        """A crest egg -> the classic Digimental item-evolution flow."""
        if self.dead or self.stage == "Egg" or self.num < 0:
            return _Refused("")
        item_id = self._CREST_IDS.get(key, -1)
        target = evolution.item_select(self, item_id)
        if target is None:
            self._set_anim("refuse", 1.0)
            return _Refused(f"{self.name} can't use that yet.")
        if self.asleep:
            self._disturbed()
        prev = self.num
        self.evolve_to(target)
        lines_mod.adopt_line(self, prev=prev)     # a special jump re-anchors
        self.take_item(key)
        self._set_anim("happy", 1.6)
        from . import persistence as _persist
        _persist.armor_add(1)                 # the crest-wave shop gate counts it
        return f"{self.name} armor-evolved!"

    def _energy_drink(self):
        """The label says "energy to FULL": SET the signed meter to max (the
        old += max_energy left a drained pet short of full), and refuse at
        full like every care sibling instead of vanishing for nothing."""
        if self.energy >= self.max_energy:
            return _Refused("Energy is already full.")
        self._set_energy(self.max_energy)
        return "Energy restored!"

    def _snack(self, hunger=0, energy=0, weight=0):
        """The TUIPET food family (2026-07-18): plain live-meter meals.
        Positive-hunger food is refused at a full belly, like every meal."""
        if hunger > 0 and self.hunger >= FULL_HUNGER:
            return _Refused("Refused - belly's full.")
        if hunger:
            self.hunger = _clamp(self.hunger + hunger, 0, FULL_HUNGER)
        if energy:
            self._set_energy(self.energy + energy)
        if weight:
            self._set_weight(max(1, self.weight + weight))
        return "Munch."

    def _giga_meal(self):
        if self.hunger >= FULL_HUNGER:
            return _Refused("Refused - belly's full.")
        self.hunger = FULL_HUNGER
        self._set_energy(self.energy + 4)
        self._set_weight(self.weight + 6)
        return "A FEAST."

    def _vitamin(self):
        # the canon second job (restoration 2026-07-23): a live vitamin
        # guards against battle injuries (the decompile's good_v/bad_v
        # column) for a game-day -- so a full-effort pet still has a
        # reason to take one before a hard fight
        if self.strength >= 4 and getattr(self, "vitamin_lapse", 0.0) > 0:
            return _Refused("Effort is full and the vitamin is working.")
        self.strength = 4
        # 1440 game-min == ONE GAME DAY (~24 real minutes of play).  Burns
        # down by dt in petbody._tick_life -- see THE UNIT LAW there.
        self.vitamin_lapse = 1440.0
        return "Effort brims — and it guards!"

    def _bandage(self):
        """The SECOND med, restored (canon restoration 2026-07-23, Joel:
        "it was wrongfully stripped").  Cures the injury, one dose --
        the pill's own grammar; the pill stays sick-only.  Two ailments,
        two meds, the device pair."""
        if not self.injured:
            return _Refused("Nothing to bandage.")  # noqa: F405
        self.injured = False
        self.inj_length = 0.0        # the wait is what the Bandage buys off
        self._set_anim("happy", 1.4)
        return "All patched up!"

    def _caffeine(self):
        """Tonight's bedtime pushed later: a quarter of the night off the
        clock the pet ACTUALLY sleeps by.  Line pets (every hatch) read the
        wall-clock window, not sleep_lapse -- the old pressure-only nudge
        made this a paid no-op for them (gameplay audit 2026-07-19); their
        push rides the same grace channel a disturb uses."""
        if self.asleep:
            return _Refused("Too late - it's already down.")
        if self._in_sleep_window() is not None:
            bt = lines_mod.bedtime_minutes(self)
            night = (self.WAKE_MINUTE - bt) % DAY_MINUTES
            self._bed_postpone_t = max(getattr(self, "_bed_postpone_t", 0.0),
                                       night * 0.25)
        else:
            self.sleep_lapse = max(0.0, self.sleep_lapse - self.sleep_limit * 0.25)
        return "Wide awake for a while yet."

    def _erase_mistakes_all(self):
        """The Textbook: study away EVERY care mistake (the source eraser's
        canon strength -- the one-at-a-time nerf left with the old shelf)."""
        if self.care_mistakes <= 0:
            return _Refused("No mistakes to erase.")
        self.care_mistakes = 0
        return "Every mistake, studied away."

    def _dna_crystal(self):
        """+10 banked DNA in the pet's own Field (the live DNA bank; skips
        one mash session)."""
        field = getattr(self, "field", "") or ""
        if field in ("", "None"):
            return _Refused("No Field to resonate with.")
        have = self.dna_owned.get(field, 0)
        if have >= MAX_DNA_INVENTORY:
            return _Refused("That Field's bank is full.")
        self.dna_owned[field] = min(MAX_DNA_INVENTORY, have + 10)
        return f"+{self.dna_owned[field] - have} {field} DNA banked!"

    def _toy(self, weight=0, energy=0, msg="Fun!"):
        """The toy dial: exercise sheds weight, couch time buys energy at a
        weight price.  The SHOW (itemfx script) is fired by the bag panel."""
        if weight:
            self._set_weight(max(1, self.weight + weight))
        if energy:
            self._set_energy(self.energy + energy)
        return msg

    def _bubble_bath(self):
        """Washes the filth, with style (a clean wearing toy clothes)."""
        if not self.poop:
            return _Refused("Squeaky clean already.")
        n, self.poop = self.poop, 0
        self.poop_sizes = []
        return f"Scrubbed {n} mess{'es' if n > 1 else ''} away."

    def _cold_shower(self):
        """The RUDE waker: not on the mistake-free list -- on a sleeper it
        runs the disturb ITSELF (the item-sleep law, kept; use_item leaves it
        to us so this wake branch can actually run) -- then the pep lands."""
        woke = ""
        if self.asleep:
            self._disturbed()                # bills + wakes like any rude item
            woke = "AWAKE and "
        self._set_energy(self.energy + 2)
        return f"Brrr! {woke}bracing."

    def _deadly(self):
        # through _die like every other death: it clears asleep/hatching and
        # sets the pose -- the hand-rolled dead=True skipped both, and the
        # tick-edge detector never saw a between-ticks death at all
        # (gameplay audit 2026-07-19; the app's state check pairs with this)
        self._die("a poison mushroom")
        return "...it was DELICIOUS. And fatal."

    def _junk(self):
        self.hunger = FULL_HUNGER
        self._set_weight(self.weight + 4)
        # the real mistake pipeline: the bare counter bumped care_mistakes
        # without the mood sting or mistake_day, so the burger slip was
        # invisible to the birthday judgment
        self._inc_mistake()
        return "Delicious. Regrettable."

    def _premium_meat(self):
        self.hunger = FULL_HUNGER
        # 12 REAL hours (Joel 2026-07-19, "tune them up to match the words"):
        # the old 12*60 ticks delivered 12 real MINUTES while the text and
        # this message promised hours -- the eat card's countdown exposed it
        self.full_until = self.world_seconds + 12 * 3600.0
        return "Satiated for 12 hours."

    def _smart_potty(self):
        self.clean()
        self.auto_clean_until = self.world_seconds + 24 * 3600.0  # 24 REAL hours (same ruling)
        return "Auto-clean for 24 hours."

    def _sleep_pill(self):
        """Sleep NOW, no argument.  A line pet's real sleep outside its
        window used to be woken by the very next tick's 7:00-sharp check --
        one second of sleep for 300b (gameplay audit 2026-07-19): out of
        hours the pill's sleep is the daytime DOZE shape instead (the
        shipped lights-out nap), which sleeps off the energy debt and can
        become the night when the window arrives."""
        if getattr(self, "away", False):
            # the ROAD is no bed (adventure energy audit 2026-07-23): the
            # march waits out pet.asleep, but the life sim is PAUSED in
            # every mode (the TIME LAW's one-law freeze), so a road sleep
            # never ends -- the pill froze the march FOREVER, ESC home the
            # only way out.  Refused, pill kept.
            return _Refused("Not on the road — no bed out here.")  # noqa: F405
        if self.asleep:
            return _Refused("It's already asleep.")
        self._fall_asleep()
        self.lights = False
        self._bed_postpone_t = 0.0      # "no argument" overrides a disturb grace
        if self._in_sleep_window() is False:
            self.nap = True
        return "Zzz..."

    def _alarm(self):
        """Wake Up Without Mistake: a clean wake, no disturb penalty.  In a
        line pet's sleep window the wake must HOLD like a rude one does --
        with no grace the pet re-slept on the very next tick, leaving the
        purpose-built alarm weaker than throwing any other item at the
        sleeper (gameplay audit 2026-07-19)."""
        if not self.asleep:
            return _Refused("It's already awake.")
        was_nap = self.nap
        self.asleep = False
        self.nap = False
        self.lights = True
        self.awake_lapse = 0.0
        if self._in_sleep_window() is not None and not was_nap:
            self._bed_postpone_t = float(random.randint(*DISTURB_POSTPONE))
        return "Rise and shine!"

    def _time_gear(self):
        # +120 REAL minutes (Joel 2026-07-19, "tune them up to match the
        # words"): the old +120 ticks was 2 real minutes -- a 500b bottle
        # of nearly nothing.  7200 ticks is the 2 hours the label sells.
        self.stage_seconds += 7200.0
        return "Time lurches forward."

    def _anti_evo(self):
        self.evo_blocked = not getattr(self, "evo_blocked", False)
        return "Evolution " + ("BLOCKED." if self.evo_blocked else "unblocked.")

    def _x_item(self):
        """The X-Antibody chip: raises the X state (the classic X system).
        Canon xEvolve() charges calcXAntibodyLifeDec() the instant X is gained
        from None (PhysicalState L3361) -- the X-Program's price in LIFE.  That
        burn was dead; the antibody was a free ride (Joel 2026-07-22)."""
        if self.x_antibody != "None":
            return _Refused("The antibody already runs in it.")
        # (calcXAntibodyLifeDec left with the lifespan clock -- DSprite
        # mortality 2026-07-22.  NOTE: the unmarked-pet death roulette was
        # never THIS item's -- it belonged to the separate X-PROGRAM item,
        # removed with the strict-DSprite shelf 2026-07-17; the chip has
        # always been the safe path.  Dossier audit 2026-07-22 corrected
        # this comment's false claim that a roulette ran "below".)
        self._set_xantibody("Permanent")
        from . import persistence as _persist
        _persist.note_xanti()
        return "The X-Antibody takes hold!"

    def _training_pack(self):
        """The Dumbbell: +10 stage trainings, capped 999 (the source's canon
        value -- the +5 was unexplained drift; TUIPET catalog 2026-07-18)."""
        self.stage_trainings = min(999, self.stage_trainings + 10)
        return "Training +10."

    def _revive_item(self):
        if not self.dead:
            return _Refused("No one needs reviving.")
        self.save_from_death()
        return "It LIVES."

    def _inherit_memory(self):
        """The Digimemory chip (DVPet item 32, anim Inherit): the ancestor's
        etched Va/D/Vi joins this pet's powers (petbase DIGIMEMORY_* law).
        (The chip's lifespan hours left with the lifespan clock -- DSprite
        mortality 2026-07-22; an OLD chip's "seconds" payload loads fine and
        is simply not applied.)  A chip with no payload aboard -- the estate
        husk -- stays a mute keepsake."""
        mem = self.digimemory
        if not mem:
            return _Refused("The chip is silent.")
        self.vaccine += int(mem.get("vaccine", 0) or 0)
        self.data_power += int(mem.get("data", 0) or 0)
        self.virus += int(mem.get("virus", 0) or 0)
        self.digimemory = {}
        return f"{mem.get('name', 'The ancestor')}'s power lives on!"

    def _super_carrot(self):
        if self.weight <= 1:
            return _Refused("Nothing left to trim.")
        self._set_weight(max(1, self.weight - 10))
        return "Feather-light!"

