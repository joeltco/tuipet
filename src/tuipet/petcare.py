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

    def feed_meat(self):
        """Meat: hunger +1, weight +1.  The source's refusal gates (canon
        gates 2026-07-18, decompile L11676): a sick pet, a pet beside its
        own filth, or a full belly gets the head-shake and NOTHING else --
        the DVPet overeatPenalty (weight+1, mistake+1, bowel shove) left
        with it.  The overeat COUNTER still ticks: the evolution corpus's
        OF gates read it, and a full-belly attempt IS the overfeed signal.
        Feeding a sleeper DISTURBS it first (refusals don't wake it)."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        if self.sick:
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too sick to eat — try the pill."
        if self.poop:
            self._set_anim("refuse", 1.0)
            return "Clean up first!"
        if self.hunger >= FULL_HUNGER:
            self.overeat += 1                    # the OF-gate signal, penalty-free
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
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

    # ---- discipline: praise / scold (PhysicalState) --------------------------
    def _open_praise(self):
        """A NO-OP: the praise window left with the discipline system."""

    def _open_scold(self):
        """A NO-OP: the scold window left with the discipline system."""

    def _calm_discipline_call(self):
        """A NO-OP: the tantrum left with the discipline system."""

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
        return "Lights off." if not self.lights else "Lights on."

    # ---- shop / items --------------------------------------------------------
    # (buy_slot -- the town-counter purchase -- cut with the town chain
    # 2026-07-19; shop.buy is the ONE live purchase path)
    def sell(self, entry):
        """Resell one from the bag at half price."""
        key = entry["key"]
        if self.inventory.get(key, 0) <= 0:
            return "None to sell."
        val = shop.resell_price(entry)
        self.take_item(key)
        self.bits += val
        return f"Sold {entry['name']} for {val}b."

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

    def _apply_item_stats(self, e, mod):
        """The canon applyItem stat core, shared by the generic path AND the
        special branches that used to skip it (energy audit 2026-07-06: the
        X-Program applied NONE of its hunger -10 / strength -13 / energy -0.8 /
        spirit -10 / mood -300, and the Digimentals skipped their -0.66 energy
        price).  A FRACTIONAL energy is a share of maxEnergy."""
        def _sc(v):
            return math.ceil(v * mod) if v > 0 else int(round(v * mod))
        if e["hunger"]:
            self.hunger = _clamp(self.hunger + _sc(e["hunger"]), 0, 4)
            self.calories = CALORIE_LIMIT               # food refills the calorie buffer
        # applyConsumable: the consumable's mood is shaped by personality tags
        self._set_mood(self.mood + _sc(e["mood"]) + _sc(self._personality_mood(e)))
        self._set_enthusiasm(self.enthusiasm + _sc(e.get("enthusiasm", 0)))
        # canon applyItem scales weight by the modifier like every other stat
        # (PhysicalState:3502 ceil(item.getWeight() x modifier))
        self._set_weight(self.weight + _sc(e["weight"]))
        if e["energy"]:
            ev = e["energy"]
            amt = math.ceil(ev * self.max_energy * mod) if ev != int(ev) else _sc(ev)
            self._set_energy(self.energy + amt)
        if e["strength"]:
            self.strength = _clamp(self.strength + _sc(e["strength"]), 0, 4)
        # canon scales obedience too (PhysicalState:3428) -- the old "obedience
        # is UNscaled" note misread the decompile (weight audit 2026-07-06)
        self._set_obedience(self.obedience + _sc(e["obedience"]))
        # applyAttributeChange + compensateAttributes (completeness sweep
        # 2026-07-06): the six +-15 TRADE toys (Board Game, Skateboard,
        # Dumbbell...) conserve the total -- a power driven below 0 borrows
        # the deficit 1:1 from the others, rotating through all three (the
        # old max(0,) clip quietly forgave the unpaid part of the trade)
        self.vaccine += _sc(e["vaccine"])
        self.data_power += _sc(e["data"])
        self.virus += _sc(e["virus"])
        self._compensate_attrs()
        # canon applyItem: a Disposition item nudges the MOOD RANK (the
        # tracker the Champion re-roll cashes in), scaled like every stat
        self.mood_rank += _sc(int(e.get("t_disposition", 0) or 0))

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
            "energy_drink": lambda: self._gain_energy(self.max_energy),
            "slim_drink": self._super_carrot,
            "vitamin": self._vitamin,
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
        # the sleeping pill is pointless, anything else DISTURBS -- then applies
        if self.asleep and key not in ("music_player", "sleeping_pill"):
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

    def _gain_energy(self, n):
        self._set_energy(self.energy + n)
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
        if self.strength >= 4:
            return _Refused("Effort is already full.")
        self.strength = 4
        return "Effort brims!"

    def _caffeine(self):
        """Tonight's bedtime pushed later: a quarter of the pressure window
        off the LIVE sleep clock (the real sleep_lapse nudge)."""
        if self.asleep:
            return _Refused("Too late - it's already down.")
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
            return "Squeaky clean already - but what a soak."
        n, self.poop = self.poop, 0
        self.poop_sizes = []
        return f"Scrubbed {n} mess{'es' if n > 1 else ''} away."

    def _cold_shower(self):
        """The RUDE waker: not on the mistake-free list, so using it on a
        sleeper disturbs first (the item-sleep law) -- then the pep lands."""
        woke = ""
        if self.asleep:
            self.asleep = False
            self.nap = False
            self.lights = True
            self.awake_lapse = 0.0
            woke = "AWAKE and "
        self._set_energy(self.energy + 2)
        return f"Brrr! {woke}bracing."

    def _fruit(self, quality):
        if self.hunger >= FULL_HUNGER and quality >= 0:
            return _Refused("Refused - belly's full.")
        self.hunger = _clamp(self.hunger + 1, 0, FULL_HUNGER)
        if quality > 0:
            self.strength = _clamp(self.strength + quality - 1, 0, 4)
        elif quality == 0:
            self._set_weight(self.weight + 3)
        return "Munch."

    def _deadly(self):
        self.dead = True
        self.death_cause = "a poison mushroom"
        return "...it was DELICIOUS. And fatal."

    def _junk(self):
        self.hunger = FULL_HUNGER
        self._set_weight(self.weight + 4)
        self.care_mistakes += 1
        return "Delicious. Regrettable."

    def _premium_meat(self):
        self.hunger = FULL_HUNGER
        self.full_until = self.world_seconds + 12 * 60.0   # 12 game-hours of satiety
        return "Satiated for 12 hours."

    def _smart_potty(self):
        self.clean()
        self.auto_clean_until = self.world_seconds + 24 * 60.0   # a game day
        return "Auto-clean for 24 hours."

    def _erase_mistake(self):
        if self.care_mistakes <= 0:
            return _Refused("No mistakes to erase.")
        self.care_mistakes -= 1
        return "One mistake, forgotten."

    def _sleep_pill(self):
        if self.asleep:
            return _Refused("It's already asleep.")
        self._fall_asleep()
        self.lights = False
        return "Zzz..."

    def _alarm(self):
        """Wake Up Without Mistake: a clean wake, no disturb penalty."""
        if not self.asleep:
            return _Refused("It's already awake.")
        self.asleep = False
        self.nap = False
        self.lights = True
        self.awake_lapse = 0.0
        return "Rise and shine!"

    def _time_gear(self):
        self.stage_seconds += 120.0        # +120 game-minutes of growth
        return "Time lurches forward."

    def _anti_evo(self):
        self.evo_blocked = not getattr(self, "evo_blocked", False)
        return "Evolution " + ("BLOCKED." if self.evo_blocked else "unblocked.")

    def _x_item(self):
        """The X-Antibody chip: raises the X state (the classic X system)."""
        if self.x_antibody != "None":
            return _Refused("The antibody already runs in it.")
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

    def _super_carrot(self):
        if self.weight <= 1:
            return _Refused("Nothing left to trim.")
        self._set_weight(max(1, self.weight - 10))
        return "Feather-light!"

