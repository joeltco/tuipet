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


def _live_memory(mem):
    """A Digimemory payload with actual power behind it.  A payload can carry
    a name and three zeros -- the estate husk, or a pre-2026-07-29 etch whose
    faint life rounded away under DIGIMEMORY_ATTR_COEF -- and such a chip must
    read as silent everywhere (peek AND use), never as a legacy."""
    return bool(mem) and any(int(mem.get(f, 0) or 0)
                             for f in ("vaccine", "data", "virus"))


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

    # never a gift: a trap, a road tool, an heirloom, or a premium you'd feel
    # cheated to unwrap for free.  (Road items are already excluded by the
    # where=="home" test; listed here for intent.)
    _GIFT_BANNED = frozenset({"poison_mushroom", "digimemory", "revive_floppy",
                              "town_transport", "disaster_transport",
                              "life_recovery",
                              # the expansion (2026-07-26): traps and earned
                              # keys are never gift-wrapped -- the spirits
                              # are ENDGAME prizes (roads give Human, cups
                              # give Beast), the X-Program is an elite drop,
                              # and a gift is supposed to be NICE
                              "zone_transport", "continent_transport",
                              "x_program", "burnt_food", "hedonism_101",
                              "prank_capsule_a", "prank_capsule_b",
                              "human_fire_spirit", "human_light_spirit",
                              "human_ice_spirit", "human_wind_spirit",
                              "human_thunder_spirit", "human_earth_spirit",
                              "human_water_spirit", "human_wood_spirit",
                              "human_metal_spirit", "human_dark_spirit",
                              "beast_fire_spirit", "beast_light_spirit",
                              "beast_ice_spirit", "beast_wind_spirit",
                              "beast_thunder_spirit", "beast_earth_spirit",
                              "beast_water_spirit", "beast_wood_spirit",
                              "beast_metal_spirit", "beast_dark_spirit"})

    def _pick_gift(self, festival=False):
        """A SURPRISE present (2026-07-24, Joel: "presents should be just
        that, a surprise" / "make these items actually work").  Where the
        old pool was four fixed treats, a gift is now a TIER-WEIGHTED pick
        from the whole giftable catalog -- mostly a common treat, now and
        then something nicer, so you never quite know what you'll unwrap.

        A FESTIVAL present reaches one tier higher (up to rare); an ordinary
        day tops out at uncommon.  Legendary goods and the banned set are
        never gifts."""
        from . import shop
        cap = shop.TIER_ORDER.index("rare" if festival else "uncommon")
        pool = [k for k, v in shop.CATALOG.items()
                if k not in self._GIFT_BANNED and v.where == "home"
                and shop.TIER_ORDER.index(v.tier or "common") <= cap]
        weights = [shop.tier_weight(k) for k in pool]
        return random.choice(pool) if not weights \
            else random.choices(pool, weights=weights, k=1)[0]

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
            # ---- MEDICINE ---------------------------------------------------
            "vitamin": self._vitamin,
            "miracle_drink": self._miracle_drink,
            "cold_compress": self._cold_compress,
            # ---- CARE -------------------------------------------------------
            "sleeping_pill": self._sleep_pill,
            "caffeine_pill": self._caffeine,
            "music_player": self._alarm,
            "textbook": self._textbook,
            "port_potty": self._smart_potty,
            # ---- TRAINING ---------------------------------------------------
            "energy_drink": self._energy_drink,
            "slim_drink": self._super_carrot,
            "dumbbell": self._training_pack,
            # ---- EVOLUTION --------------------------------------------------
            "grow_capsule": self._time_gear,
            "anti_evo_chip": self._anti_evo,
            "x_antibody": self._x_item,
            "dna_crystal": self._dna_crystal,
            "vaccine_chip": lambda: self._attr_chip("vaccine", 15),
            "data_chip": lambda: self._attr_chip("data_power", 15),
            "virus_chip": lambda: self._attr_chip("virus", 15),
            "vaccine_chip_g": lambda: self._attr_chip("vaccine", 30),
            "data_chip_g": lambda: self._attr_chip("data_power", 30),
            "virus_chip_g": lambda: self._attr_chip("virus", 30),
            "omni_chip_g": lambda: self._attr_chip(None, 30),
            # ---- LEGACY -----------------------------------------------------
            "revive_floppy": self._revive_item,
            "digimemory": self._inherit_memory,
            # ---- PLAY (small LIVE dials; the SHOW is fired by the bag panel)
            "ball": lambda: self._toy(weight=-1, msg="A grand kickabout!"),
            "skateboard": lambda: self._toy(weight=-2, energy=-1,
                                            msg="It shreds!"),
            "xylophone": lambda: self._toy(energy=2, msg="A lovely recital."),
            "video_game": lambda: self._toy(energy=2, weight=1,
                                            msg="One more level…"),
            "television": lambda: self._toy(energy=3, weight=1,
                                            msg="Glued to the screen."),
            # ---- ADVENTURE (spent ON THE ROAD, not from the home bag) -------
            "town_transport": lambda: _Refused("Save it for the road (press T)."),
            "disaster_transport": lambda: _Refused("Save it for the road (press T)."),
            "life_recovery": lambda: _Refused("Restores adventure lives — use it on the road."),
            "zone_transport": lambda: _Refused("Save it for the road (press T)."),  # noqa: F405
            "continent_transport": lambda: _Refused("Save it for the road (press T)."),  # noqa: F405
            # ---- THE EXPANSION's singular doors (2026-07-26) ----------------
            "med": self._med_item,
            "elixir": self._elixir,
            "vitamin_g": self._vitamin_g,
            "gold_pill": self._gold_pill,
            "supplement": self._supplement,
            "hp_chip": lambda: self._attr_chip(None, 5),
            "hp_chip_g": lambda: self._attr_chip(None, 10),
            "board_game": self._board_game,
            "computer_game": self._computer_game,
            "toy_oven": self._toy_oven,
            "futon": self._futon,
            "x_program": self._x_program,
            "chocolate_egg": self._chocolate_egg,
            "book": self._textbook_lite,
            "hedonism_101": self._hedonism,
            "trampoline": lambda: self._toy(weight=-1, strength=1,
                                            msg="BOING. Light training!"),
        }.get(key)
        # the expansion FAMILIES: authored snacks, evolution keys, capsules
        if fx is None and key in self._SNACK_FX:
            fx = lambda: self._csv_snack(key)          # noqa: E731
        if fx is None and (key in self._ITEM_EVO_IDS
                           or key in self._DIRECT_EVO_TARGET):
            fx = lambda: self._evo_key(key)            # noqa: E731
        if fx is None and (key in self._CAPSULE_KEYS
                           or key in self._PRANK_CAPSULES):
            fx = lambda: self._capsule(key)            # noqa: E731
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
        # anything else DISTURBS -- then applies.  The FUTON joins the exempt
        # set (2026-07-26): it is the sleep family's fourth member -- sliding
        # a bed under a sleeper is the opposite of a disturbance.
        if self.asleep and key not in ("music_player", "sleeping_pill",
                                       "futon"):
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

    def _snack(self, hunger=0, energy=0, weight=0, obedience=0, powers=None,
               strength=0):
        """The TUIPET food family (2018-07-18 -> grown 2026-07-26): plain
        live-meter meals.  Positive-hunger food is refused at a full belly,
        like every meal.  The expansion legs (obedience / VDV powers /
        effort) land the authored columns of the new rows -- a pepper's +1
        power rides the chip grammar, effort clamps to its 0-4 gauge."""
        if hunger > 0 and self.hunger >= FULL_HUNGER:
            return _Refused("Refused - belly's full.")
        if hunger:
            self.hunger = _clamp(self.hunger + hunger, 0, FULL_HUNGER)
        if energy:
            self._set_energy(self.energy + energy)
        if weight:
            self._set_weight(max(1, self.weight + weight))
        if obedience:
            self._set_obedience(self.obedience + obedience)
        if strength:
            self.strength = _clamp(self.strength + strength, 0, 4)  # noqa: F405
        if powers:
            v, d, vi = powers
            self.vaccine += v
            self.data_power += d
            self.virus += vi
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
        push rides the same grace channel a disturb uses.

        THE NO-OP DOSE IS REFUSED (item sweep 2026-07-24).  Both branches
        could spend a 300b pill and move nothing -- a second pill while the
        grace already holds that push, or a pressure pet whose sleep_lapse
        is still 0 (nowhere near bedtime) -- while saying "Wide awake for a
        while yet."  Every care sibling refuses at full instead ("Energy is
        already full", "already a model pupil"); this was the outlier."""
        if self.asleep:
            return _Refused("Too late - it's already down.")
        if self._in_sleep_window() is not None:
            bt = lines_mod.bedtime_minutes(self)
            night = (self.WAKE_MINUTE - bt) % DAY_MINUTES
            push = night * 0.25
            if getattr(self, "_bed_postpone_t", 0.0) >= push:
                return _Refused("Bedtime's already pushed back.")  # noqa: F405
            self._bed_postpone_t = push
        else:
            if self.sleep_lapse <= 0:
                return _Refused("It's nowhere near bedtime.")      # noqa: F405
            self.sleep_lapse = max(0.0, self.sleep_lapse - self.sleep_limit * 0.25)
        return "Wide awake for a while yet."

    def _miracle_drink(self):
        """THE ERASER, rehoused and nerfed (Joel 2026-07-23: "one at a
        time, own item").  foods.csv row 18 is DVPet's own answer -- the
        ONLY consumable in either sheet carrying `Mistake = -1` -- so the
        eraser did not need inventing, only finding.

        Why it matters enough to keep at all: care mistakes are a DEATH
        clock, not a gate.  20 kills outright, an Ultimate/Mega dies at 5
        once two game-days into the stage, and the hazard ladder gets
        100x worse from 5 to 20.  The counter resets on every evolution
        -- but 241 of 417 Megas are TERMINAL, and for those it never
        resets again.  This drink is the only way back.

        Canon: Energy +12, Mistake -1.  Its -Mood and -Life legs are
        dropped: mood is a verified no-op meter and the lifespan clock
        left with DSprite mortality (2026-07-22)."""
        if self.care_mistakes <= 0:
            return _Refused("Nothing on the slate to erase.")   # noqa: F405
        self.care_mistakes -= 1
        self._set_energy(self.energy + MIRACLE_ENERGY_GAIN)   # noqa: F405
        left = self.care_mistakes
        return ("One slip, forgiven." if not left
                else f"One slip forgiven — {left} still on the slate.")

    def _cold_compress(self):
        """THE CHEAP ERASER (2026-07-27, Joel: "fill the cure hole").

        care_mistakes is the game's death clock -- 20 kills outright, an
        Ultimate dies at 5 -- and the ONLY answer was a 7777b drink that
        also paid +12 energy.  One luxury is not a ladder.  This one wipes
        the same single slip for a quarter of the price and takes the
        energy instead of giving it: relief you have to sleep off.
        """
        if self.care_mistakes <= 0:
            return _Refused("Nothing on the slate to erase.")   # noqa: F405
        if self.energy <= COMPRESS_ENERGY_COST:                 # noqa: F405
            return _Refused("Too drained to take the shock.")   # noqa: F405
        self.care_mistakes -= 1
        self._set_energy(self.energy - COMPRESS_ENERGY_COST)    # noqa: F405
        left = self.care_mistakes
        return ("One slip scrubbed off — and it stings." if not left
                else f"One slip scrubbed off — {left} still on the slate.")

    def _textbook(self):
        """THE TEXTBOOK, back to canon (Joel 2026-07-23: R4).  items.csv
        row 0 is `+Obedience -Mood +Stress`; mood and stress are stripped
        systems, so only the obedience leg lands -- and it is the FIRST
        item support the restored discipline system has ever had.

        Refused at a full gauge like every other care sibling, so it
        can't be burned for nothing."""
        if self.obedience >= MAX_OBEDIENCE:                   # noqa: F405
            return _Refused(f"{self.name} is already a model pupil.")  # noqa: F405
        before = self.obedience
        self._set_obedience(self.obedience + TEXTBOOK_OBEDIENCE)  # noqa: F405
        return f"Studied hard. (+{self.obedience - before} obedience)"

    def heal_bandage(self):
        """THE H KEY's verb: patch the battle injury, free (the bandage's
        FINAL door -- Joel 2026-07-26: "remove bandage as an item
        alltogether and just add an h heal hotkey".  It spent one day as a
        300b shop item (v0.5.277, tag-only, never on PyPI) and before that
        one era as the F menu's third row; a care action on this device is
        a BUTTON, and now it has its own).  The canon time-heal (injLapse)
        stays underneath as background truth.

        Mirrors feed_pill's shape: guarded, and healing a sleeper
        DISTURBS it first."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        if not self.injured:
            return _Refused("Nothing to bandage.")            # noqa: F405
        if self.asleep:
            self._disturbed()
        return self._bandage()

    _ATTR_FIELDS = ("vaccine", "data_power", "virus")
    _ATTR_WORD = {"vaccine": "Vaccine", "data_power": "Data", "virus": "Virus"}

    def _attr_chip(self, field, amount):
        """THE ATTRIBUTE CHIPS (P6, 2026-07-23) -- foods.csv rows 10/11/12
        (+15) and 20/21/22 (+30), plus 33 (Omni, all three).

        Va/D/Vi are LIVE and load-bearing: hundreds of evolution rows gate
        on them, and battle power reads them.  Until now the only ways to
        raise one were winning a battle in that attribute (+1) and the
        inheritance-only Digimemory -- so a whole live lever had nothing
        buyable behind it.  A chip is worth about fifteen wins.

        Uncapped ON PURPOSE: the win path it shortcuts is uncapped too
        (record_battle just does `self.vaccine += inc`), and inventing a
        ceiling here would be inventing a rule.  `field=None` is the Omni
        chip -- every power at once.

        Canon legs NOT applied: -Mood (a verified no-op meter) and
        +Stress (a stripped system)."""
        fields = self._ATTR_FIELDS if field is None else (field,)
        for f in fields:
            setattr(self, f, getattr(self, f) + amount)
        if field is None:
            return f"Every power surges! (+{amount} each)"
        return f"{self._ATTR_WORD[field]} power +{amount}!"

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

    def _toy(self, weight=0, energy=0, msg="Fun!", obedience=0, strength=0):
        """The toy dial: exercise sheds weight, couch time buys energy at a
        weight price.  The SHOW (itemfx script) is fired by the bag panel.
        The expansion legs: a spoiling toy dents obedience (authored), the
        trampoline's bounce is light training (effort, 0-4 gauge)."""
        if weight:
            self._set_weight(max(1, self.weight + weight))
        if energy:
            self._set_energy(self.energy + energy)
        if obedience:
            self._set_obedience(self.obedience + obedience)
        if strength:
            self.strength = _clamp(self.strength + strength, 0, 4)  # noqa: F405
        return msg

    def _deadly(self):
        # through _die like every other death: it clears asleep/hatching and
        # sets the pose -- the hand-rolled dead=True skipped both, and the
        # tick-edge detector never saw a between-ticks death at all
        # (gameplay audit 2026-07-19; the app's state check pairs with this)
        self._die("a poison mushroom")
        return "...it was DELICIOUS. And fatal."

    def _junk(self):
        # ⭐NOT A CARE MISTAKE (2026-08-01, Joel: "canonize all care mistakes").
        # THE BANDAI DEVICE RECORD IS THE AUTHORITY and it is explicit on this
        # one: a care mistake is a MISSED CALL, and OVERFEEDING is called out
        # by name as something that is NOT one.  The burger is junk food -- it
        # fills the belly and it makes the pet fat, which is the whole penalty.
        # It has no business touching the counter that gates evolution and
        # kills at 20.
        self.hunger = FULL_HUNGER
        self._set_weight(self.weight + 4)
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
        # the room drops AFTER the pill's own eat show, never before (bug
        # report 2026-07-26, v0.5.287: "sleep pill is shutting off lights
        # before eating animation, istead of after").  Lights-off is not a
        # dimmer: arenafx keeps DVPet's fully-opaque lightsOff cover up
        # through a care fx, so flipping it here blanked the whole arena --
        # pet, pill and bite strip -- for all 35 beats of the show the pill
        # was bought for.  Same shape as the Assistant_Lights visit, which
        # DVPet also toggles on its FINAL beat; the app flips it at fx end.
        self.pending_lights_out = True
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
        self.pending_lights_out = False   # the pill's debt dies with the sleep
        #                                   it served (sleep audit r2, 07-28)
        self.awake_lapse = 0.0
        if self._in_sleep_window() is not None and not was_nap:
            self._bed_postpone_t = float(random.randint(*DISTURB_POSTPONE))
        return "Rise and shine!"

    def _time_gear(self):
        """The Grow Capsule: a QUARTER of this stage off the growth clock
        (Joel 2026-07-24: "make the grow capsule worth 500b").

        Three rules keep it worth the bits without becoming the bug it
        replaced:

        * a FRACTION, not a flat number of minutes.  Stages run 180..2880
          game-minutes, so a figure that matters to an Ultimate would skip
          a baby stage whole.  A quarter is a quarter everywhere.
        * it HURRIES the wait, it never ENDS it: the push stops one tick
          short of the gate, so no stack of capsules can evolve a pet
          outright -- and at Ultimate, whose stage length IS
          LATE_STAGE_WINDOW, that same stop is what keeps capsules from
          arming the Pen20 frailty death by themselves.
        * a final form has no clock to hurry, and stage_seconds only
          feeds frailty there, so the capsule REFUSES rather than sell a
          pure downside (the no-duds rule).

        ⚠ THE UNIT LAW (item sweep 2026-07-24) is why the old number went:
        the 2026-07-19 pass read "+120min" as 120 REAL minutes and set
        7200, but dt is game-minutes 1:1 -- 2.5x the longest stage in the
        game, from one 500b bottle."""
        from . import digicore
        dur = self.STAGE_DURATION.get(self.stage, 0)
        if not dur or dur >= 9e8 or not digicore.has_next(self):
            return _Refused(f"{self.name} has nothing left to hurry.")  # noqa: F405
        ceiling = dur - 1.0                       # never reaches the gate
        target = min(self.stage_seconds + dur * GROW_CAPSULE_FRACTION,  # noqa: F405
                     ceiling)
        if target <= self.stage_seconds:
            return _Refused("The growth clock is already full.")  # noqa: F405
        moved = target - self.stage_seconds
        self.stage_seconds = target
        return f"Time lurches forward. (+{int(moved)}min)"

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

    def stash_wild_memory(self):
        """A FOUND digimemory carries a random payload (2026-07-24, Joel:
        "make wild chips carry a random payload").  Where an INHERITED chip
        holds a whole life scaled by its care bonus (measured 2026-07-29: a
        strong Mega life etches ~20-36 points spread across the three Fields,
        a modest one under 10), a wild one holds a stranger's faint trace --
        a small single-attribute
        imprint well under the +15 base chip.  Queued in `wild_memories`
        so it never collides with the single inherited-payload slot; the
        queue keeps one-chip-one-payload true no matter how many are held."""
        total = random.randint(WILD_MEMORY_MIN, WILD_MEMORY_MAX)  # noqa: F405
        field = random.choice(("vaccine", "data", "virus"))
        mem = {"name": "A stranger", "vaccine": 0, "data": 0, "virus": 0}
        mem[field] = total
        self.wild_memories.append(mem)
        return mem

    def peek_memory(self):
        """The payload the NEXT chip use will apply -- inherited first, then
        the oldest LIVE wild trace.  The inherit fx needs the numbers BEFORE
        use_item consumes them (shopscreen._use), so this must pick exactly
        what _inherit_memory will spend: an all-zero payload is silent, and
        the dossier must not promise it (2026-07-29)."""
        if _live_memory(self.digimemory):
            return self.digimemory
        return next((m for m in self.wild_memories if _live_memory(m)), {})

    def _inherit_memory(self):
        """The Digimemory chip (DVPet item 32, anim Inherit): a payload's
        Va/D/Vi joins this pet's powers (petbase DIGIMEMORY_* law).  An
        INHERITED chip's etched ancestor data takes priority; failing that,
        a FOUND chip spends the oldest wild trace (2026-07-24).  A chip with
        no payload of either kind -- a bare estate husk -- stays mute, and so
        does one whose numbers are ALL ZERO: a name with no power behind it
        (chips banked before 2026-07-29 can hold one, when the coefficient
        rounded a faint life away).  A dead inherited payload never buries a
        real wild trace -- the first payload with something in it wins.
        (The chip's lifespan hours left with the lifespan clock -- DSprite
        mortality 2026-07-22; an OLD chip's "seconds" payload is ignored.)"""
        inherited = _live_memory(self.digimemory)
        mem = self.digimemory if inherited else next(
            (m for m in self.wild_memories if _live_memory(m)), None)
        if not _live_memory(mem):
            return _Refused("The chip is silent.")  # noqa: F405
        self.vaccine += int(mem.get("vaccine", 0) or 0)
        self.data_power += int(mem.get("data", 0) or 0)
        self.virus += int(mem.get("virus", 0) or 0)
        if inherited:
            self.digimemory = {}
        else:
            self.wild_memories.remove(mem)   # the SPENT trace, not blindly [0]
        return f"{mem.get('name', 'The ancestor')}'s power lives on!"

    def _super_carrot(self):
        if self.weight <= 1:
            return _Refused("Nothing left to trim.")
        self._set_weight(max(1, self.weight - 10))
        return "Feather-light!"

    # ======================= THE EXPANSION (2026-07-26) =====================
    # Joel: "bring in all 99 unused items ... your call".  Every handler
    # below lands the AUTHORED columns of its source row on LIVE meters
    # (Mood/Enthusiasm/Stress stay dormant).  Board:
    # ITEM_EXPANSION_2026_07_26.md.

    # the plain snacks: stats straight off the authored foods.csv columns
    # (weight = Calories // 2, the new-row rule).  One table, one handler.
    _SNACK_FX = {
        "meat": dict(hunger=1, weight=2),
        "fruit": dict(hunger=1, obedience=-1),
        "bread": dict(hunger=1, weight=1),
        "cheese": dict(hunger=1, weight=2),
        "broccoli": dict(hunger=1, obedience=2),
        "orange": dict(hunger=1, obedience=-1),
        "honey": dict(hunger=1, energy=1, weight=1, obedience=-5),
        "yellow_pepper": dict(hunger=1, obedience=1, powers=(0, 0, 1)),
        "green_pepper": dict(hunger=1, obedience=1, powers=(0, 1, 0)),
        "red_pepper": dict(hunger=1, obedience=1, powers=(1, 0, 0)),
        "bitter_herbs": dict(hunger=0, obedience=5),
        "food_pill": dict(hunger=4, weight=3, obedience=5),
        "ai_food_pill": dict(hunger=1),
        "ai_supplement": dict(hunger=0, strength=1),
        "burnt_food": dict(hunger=1, strength=-1, obedience=5),
    }

    def _csv_snack(self, key):
        """A generic authored meal -- and the FOOD EVOLUTION door: one
        corpus form (Citramon) gates on `evol_food` and the source's
        processFoodEvol (evolution.food_select) sat with zero callers.
        Eating a new-table food now asks it; the meal is an extra gate,
        never a bypass."""
        out = self._snack(**self._SNACK_FX[key])
        if isinstance(out, _Refused):  # noqa: F405
            return out
        icon = shop.ICON_KEYS.get(key, "")
        target = evolution.food_select(self, int(icon[2:])) \
            if icon.startswith("f:") else None
        if target is not None:
            prev = self.num
            self.evolve_to(target)
            lines_mod.adopt_line(self, prev=prev)
            self._set_anim("happy", 1.6)
            return f"...the meal stirs something. {self.name} evolves!"
        return out

    def _med_item(self):
        """The field pill (foods.csv 4, grant-only): cures sickness, the
        free pill's one job in pocket form -- never sold, so the free-cure
        law holds."""
        if not self.sick:
            return _Refused("No sickness to treat.")  # noqa: F405
        self.sick = False
        self._set_anim("eat", 1.4)
        return "The sickness passes."

    def _elixir(self):
        """The premium combo (2000b): cures sickness AND fills the tank.
        The free pill stays the cure -- this sells convenience."""
        if not self.sick and self.energy >= self.max_energy:
            return _Refused(f"{self.name} doesn't need it.")  # noqa: F405
        self.sick = False
        self._set_energy(self.max_energy)
        self._set_anim("eat", 1.4)
        return "Illness swept away — brimming with life!"

    def _vitamin_g(self):
        """The golden mend (2000b): heals the injury AND the vitamin's
        whole job (effort full + a game-day's injury guard).  H stays the
        free cure -- this is the vitamin's big sibling."""
        if not self.injured and self.strength >= 4 \
                and getattr(self, "vitamin_lapse", 0.0) > 0:
            return _Refused("Nothing to mend and the guard is running.")  # noqa: F405
        self.injured = False
        self.inj_length = 0.0
        self.strength = 4
        self.vitamin_lapse = 1440.0
        self._set_anim("happy", 1.4)
        return "Golden! Mended, guarded, brimming."

    def _gold_pill(self):
        """Canon Energy +12 (the miracle drink's dose, no eraser)."""
        if self.energy >= self.max_energy:
            return _Refused("Energy is already full.")  # noqa: F405
        self._set_energy(self.energy + 12)
        return "Vitality, gilded!"

    def _supplement(self):
        """Effort to FULL + the obedience leg (authored +5) + its weight."""
        if self.strength >= 4 and self.obedience >= MAX_OBEDIENCE:  # noqa: F405
            return _Refused("Nothing left to firm up.")  # noqa: F405
        self.strength = 4
        self._set_obedience(self.obedience + 5)
        self._set_weight(self.weight + 1)
        return "Effort brims!"

    def _board_game(self):
        """The attribute RESHAPER (items.csv 5): Vaccine -15 -> Data +15,
        plus the authored obedience.  Refused when there is no Vaccine to
        convert -- a converter with an empty tank is a dud."""
        if self.vaccine < 15:
            return _Refused("Not enough Vaccine power to trade.")  # noqa: F405
        self.vaccine -= 15
        self.data_power += 15
        self._set_obedience(self.obedience + 5)
        return "A long game — order yields to logic. (Va-15 → D+15)"

    def _computer_game(self):
        """Virus -15 -> Data +15 (items.csv 8)."""
        if self.virus < 15:
            return _Refused("Not enough Virus power to trade.")  # noqa: F405
        self.virus -= 15
        self.data_power += 15
        return "High score — chaos compiles. (Vi-15 → D+15)"

    def _toy_oven(self):
        """'+Appetite': makes room for a meal (hunger -1)."""
        if self.hunger <= 0:
            return _Refused("The belly is already empty.")  # noqa: F405
        self.hunger = max(0, self.hunger - 1)
        return "Something smells wonderful — suddenly peckish."

    def _futon(self):
        """The deep daytime bed: lie down NOW (the sleeping pill's flow)
        and the doze HOLDS until the tank is FULL, not half (petbody's
        recovery-doze threshold reads futon_doze; cleared on wake)."""
        if getattr(self, "away", False):
            return _Refused("Not on the road — no bed out here.")  # noqa: F405
        if self.asleep:
            if getattr(self, "futon_doze", False):
                return _Refused("Already tucked in deep.")  # noqa: F405
            self.futon_doze = True
            return "The futon slides underneath — deeper sleep."
        self._fall_asleep()
        self.lights = False
        self._bed_postpone_t = 0.0
        if self._in_sleep_window() is False:
            self.nap = True
        self.futon_doze = True
        return "Tucked in deep. Zzz..."

    def _x_program(self):
        """The RISKY X (items.csv 14, a 100%-authored elite drop): the
        authored drains ARE the price -- belly emptied, effort zeroed,
        80% of the tank torn away -- then the X takes hold.  No invented
        death roll; the aftermath (hunger calls, red-energy stings) is
        the gamble."""
        if self.x_antibody != "None":
            return _Refused("The antibody already runs in it.")  # noqa: F405
        self.hunger = 0
        self.strength = 0
        self._set_energy(self.energy - int(self.max_energy * 0.8))
        self._set_xantibody("Permanent")
        from . import persistence as _persist
        _persist.note_xanti()
        return "It convulses... and TRANSCENDS. The X takes hold!"

    def _textbook_lite(self):
        """The Book (items.csv 2): the textbook's little brother -- the
        authored +5, same full-gauge refusal."""
        if self.obedience >= MAX_OBEDIENCE:                   # noqa: F405
            return _Refused(f"{self.name} is already a model pupil.")  # noqa: F405
        before = self.obedience
        self._set_obedience(self.obedience + 5)
        return f"A quiet chapter. (+{self.obedience - before} obedience)"

    def _hedonism(self):
        """Hedonism 101 (items.csv 1): obedience -80, exactly as authored.
        A trap with a warning label -- the poison mushroom's precedent:
        a trap always goes down, never refuses."""
        self._set_obedience(self.obedience - 80)
        return "It reads the WHOLE thing. Manners: obliterated."

    # the evolution KEYS (Joel: "wire fully").  item_select forms answer to
    # their care gates (the item is an extra gate, not a bypass);
    # item_direct is the authored paid shortcut (graph adjacency only).
    _ITEM_EVO_IDS = {
        "digitron": 33,
        "human_fire_spirit": 43, "human_light_spirit": 44,
        "human_ice_spirit": 45, "human_wind_spirit": 46,
        "human_thunder_spirit": 47, "human_earth_spirit": 48,
        "human_water_spirit": 49, "human_wood_spirit": 50,
        "human_metal_spirit": 51, "human_dark_spirit": 52,
        "beast_fire_spirit": 53, "beast_light_spirit": 54,
        "beast_ice_spirit": 55, "beast_wind_spirit": 56,
        "beast_thunder_spirit": 57, "beast_earth_spirit": 58,
        "beast_water_spirit": 59, "beast_wood_spirit": 60,
        "beast_metal_spirit": 61, "beast_dark_spirit": 62,
    }
    _DIRECT_EVO_TARGET = {
        "horn_helmet": 140, "grey_claws": 93, "water_bottle": 110,
        "torn_tatter": 121, "white_wings": 101, "black_wings": 102,
        "metal_armor": 213, "flaming_wings": 97,
    }

    def _evo_key(self, key):
        """A dormant door opens: the spirits and the Digitron ride the same
        item_select flow the crest eggs do; the direct items name their form
        outright.  Refused (item kept) when nothing answers."""
        item_id = self._ITEM_EVO_IDS.get(key)
        if item_id is not None:
            target = evolution.item_select(self, item_id)
        else:
            target = evolution.item_direct(self, self._DIRECT_EVO_TARGET[key])
        if target is None:
            self._set_anim("refuse", 1.0)
            return _Refused(f"{self.name} can't use that yet.")  # noqa: F405
        prev = self.num
        self.evolve_to(target)
        lines_mod.adopt_line(self, prev=prev)
        self._set_anim("happy", 1.6)
        if key.startswith("human_"):
            # the Frontier chain, kept authentic: mastering a HUMAN spirit
            # wakes its BEAST half -- the beast key lands in the bag, ready
            # for the next stage's door (roads give Human, the Human gives
            # Beast; no cup RNG invented)
            beast = key.replace("human_", "beast_", 1)
            if beast in self._ITEM_EVO_IDS:
                self.add_item(beast)
                return (f"{self.name} evolves — and the BEAST half of the "
                        "spirit answers!")
        return f"{self.name} evolves!"

    # the CAPSULES (Joel: "roll the existing find tool"): the gift roller
    # in item form.  The two AngrySurprise rips are PRANKS -- the box is
    # identical on the shelf and in the bag; that IS the gacha.
    _CAPSULE_KEYS = frozenset({"capsule_a", "capsule_b", "capsule_c",
                               "capsule_d", "capsule_e", "capsule_f",
                               "capsule_g", "capsule_h"})
    _PRANK_CAPSULES = frozenset({"prank_capsule_a", "prank_capsule_b"})
    _PRANK_POOL = ("burnt_food", "fruit", "cheese_burger", "ai_food_pill")

    def _capsule(self, key):
        """Open the box: a tier-weighted surprise from the gift pool -- and
        on a HOLIDAY the roll reaches one tier higher (the festival-present
        grammar; 'christmas presents are holiday versions of these').  A
        prank capsule pays from the junk drawer, every time."""
        if key in self._PRANK_CAPSULES:
            prize = random.choice(self._PRANK_POOL)
        else:
            from . import tournament
            prize = self._pick_gift(festival=bool(tournament.holiday()))
        while prize in self._CAPSULE_KEYS or prize in self._PRANK_CAPSULES:
            prize = self._pick_gift()        # never a box inside a box
        self.add_item(prize)
        self.pending_prize = prize           # the cheer SHOWS it (app hook)
        e = shop.entry(prize) or {}
        name = e.get("name", "something")
        if key in self._PRANK_CAPSULES:
            self._set_anim("refuse", 1.2)
            return f"...it's {name}. HA!"
        self._set_anim("happy", 1.6)
        return f"Inside: {name}!"

    def _chocolate_egg(self):
        """A snack with a TOY INSIDE (authored: 'Toy Inside +Mood'): the
        meal, then a common-tier surprise."""
        out = self._snack(hunger=1, weight=1)
        if isinstance(out, _Refused):  # noqa: F405
            return out
        # a TOY, as authored -- not another food (bug: "isnt there supposed
        # to be items in chocolate eggs?", 2026-07-28).  The old pool took
        # every common-tier good: 18 of 29 prizes were FOODS (one was
        # another chocolate egg), and grant-only treats leaked in because
        # a None tier reads as common.  Priced non-Feed commons only now.
        pool = [k for k, v in shop.CATALOG.items()
                if k not in self._GIFT_BANNED and v.where == "home"
                and k not in self._CAPSULE_KEYS
                and k not in self._PRANK_CAPSULES
                and v.price is not None and v.tier == "common"
                and v.category != "Feed"]
        prize = random.choice(pool)
        self.add_item(prize)
        self.pending_prize = prize           # the cheer SHOWS it (app hook)
        e = shop.entry(prize) or {}
        return f"Munch — a toy inside: {e.get('name', 'something')}!"

