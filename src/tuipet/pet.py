"""DVPet game model: a single virtual pet, its stats, and care logic."""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from . import data
from . import egg as egg_mod
from . import evolution


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# Lifespan (seconds), scaled from DVPet's real-time model. A pet lives this long
# in total; reaching higher stages extends it; neglect (sickness/starvation/
# fatigue) burns it down faster. The final stretch is the geriatric "old age".
LIFE_START = 360.0
STAGE_LIFE = {"Rookie": 420.0, "Champion": 600.0, "Ultimate": 840.0, "Mega": 1080.0}
GERIATRIC_REMAIN = 75.0   # last N seconds of life = elderly

# Day/night: the world runs on an accelerated clock. One full DAY_LENGTH-second
# cycle runs dawn -> day -> dusk -> night. Night makes the pet sleepy: kept awake
# it tires and sulks faster, while rest is deepest then.
DAY_LENGTH = 240.0


def _phase_of(p):
    if p < 0.10:
        return "dawn"
    if p < 0.50:
        return "day"
    if p < 0.58:
        return "dusk"
    return "night"


@dataclass
class Pet:
    num: int
    name: str = ""
    stage: str = ""
    attribute: str = ""
    age_seconds: float = 0.0
    stage_seconds: float = 0.0      # time spent in the current stage
    hunger: int = 4                 # hearts 0..4 (4 = full)
    strength: int = 2               # effort hearts 0..4
    energy: int = 100               # 0..100
    mood: int = 80                  # 0..100
    weight: int = 20
    poop: int = 0
    sick: bool = False
    asleep: bool = False
    care_mistakes: int = 0
    wins: int = 0
    hatching: bool = False
    vaccine: int = 0
    data_power: int = 0
    virus: int = 0
    # care-quality counters that drive evolution (mirror DVPet's tracked stats)
    overeat: int = 0
    sick_count: int = 0
    injuries: int = 0
    disturb: int = 0
    obedience: int = 0
    battles: int = 0
    bits: int = 0
    trophies: int = 0
    adv_map: int = 0
    adv_zone: int = 0
    egg_type: int = 0
    lifespan: float = LIFE_START
    generation: int = 1
    dead: bool = False
    world_seconds: float = 0.0
    inventory: dict = field(default_factory=dict)
    # transient animation request, consumed by the UI
    anim: str = "idle"
    anim_ttl: float = 0.0

    # seconds in each stage before it is eligible to evolve (accelerated time)
    EGG_DURATION = 18      # seconds an egg incubates before hatching

    STAGE_DURATION = {
        "Fresh": 20, "InTraining": 40, "Rookie": 90,
        "Champion": 150, "Ultimate": 240, "Mega": 9e9,
    }

    @classmethod
    def hatch(cls, num=None):
        _, by_num = data.load_sprites()
        if num is None:
            fresh = [n for n, r in by_num.items() if r["stage"] == "Fresh"]
            num = random.choice(fresh)
        return cls.from_num(num)

    @classmethod
    def new_egg(cls, generation=1):
        return cls(num=-1, name="Digitama", stage="Egg",
                   egg_type=random.randint(0, 10), generation=generation)

    def _hatch_into_fresh(self):
        _, by_num = data.load_sprites()
        fresh = [n for n, r in by_num.items() if r["stage"] == "Fresh"]
        import random as _r
        self.evolve_to(_r.choice(fresh))
        self.hatching = False

    @classmethod
    def from_num(cls, num):
        _, by_num = data.load_sprites()
        r = by_num[num]
        return cls(num=num, name=r["name"], stage=r["stage"], attribute=r["attribute"])

    # ---- per-tick simulation -------------------------------------------------
    def tick(self, dt):
        self.world_seconds += dt          # the day/night clock runs even past death
        if self.dead:
            return
        self.age_seconds += dt
        self.stage_seconds += dt
        if self.anim_ttl > 0:
            self.anim_ttl -= dt
            if self.anim_ttl <= 0:
                self.anim = "sleep" if self.asleep else "idle"

        if self.stage == "Egg":
            if not self.hatching and self.stage_seconds >= self.EGG_DURATION:
                self.hatching = True
                self._hatch_t = 3.0
                self._set_anim("hatch", 3.0)
            if self.hatching:
                self._hatch_t = getattr(self, "_hatch_t", 3.0) - dt
                if self._hatch_t <= 0:
                    self._hatch_into_fresh()
            return

        if self.asleep:
            rate = 10 if self.day_phase == "night" else 5   # rest is deepest at night
            self.energy = _clamp(self.energy + rate * dt, 0, 100)
            if self.energy >= 100:
                self.asleep = False
                self._set_anim("idle", 0)
            return

        night = self.day_phase == "night"
        # at night an awake pet tires and grows cranky about twice as fast
        self.energy = _clamp(self.energy - (2.4 if night else 1.2) * dt, 0, 100)
        self.mood = _clamp(self.mood - (1.4 if night else 0.8) * dt, 0, 100)
        # hunger ticks down on a slow clock
        self._hunger_t = getattr(self, "_hunger_t", 0) + dt
        if self._hunger_t >= 12:
            self._hunger_t = 0
            if self.hunger > 0:
                self.hunger -= 1
            else:
                self.care_mistakes += 1
        # pooping
        self._poop_t = getattr(self, "_poop_t", 0) + dt
        if self._poop_t >= 18:
            self._poop_t = 0
            self.poop += 1
        # sickness from filth / starvation
        if (self.poop >= 3 or self.hunger == 0) and not self.sick and random.random() < 0.02 * dt:
            self.sick = True
            self.sick_count += 1
        # the pet nods off on its own when exhausted, and dozes earlier at night
        if not self.asleep and self.energy <= (35 if night else 0):
            self.asleep = True
            self._set_anim("sleep", 0)

        # lifespan: neglect burns life down faster than the natural clock
        extra = 0.0
        if self.sick:
            extra += 1.5
        if self.hunger == 0:
            extra += 1.0
        if self.energy <= 0:
            extra += 0.5
        if self.is_geriatric:
            extra += 0.5
        self.lifespan -= extra * dt
        if self.age_seconds >= self.lifespan:
            self._die()
            return

        self._maybe_evolve()

    @property
    def is_geriatric(self):
        return (not self.dead
                and self.stage in ("Rookie", "Champion", "Ultimate", "Mega")
                and (self.lifespan - self.age_seconds) < GERIATRIC_REMAIN)

    @property
    def day_phase(self):
        return _phase_of((self.world_seconds % DAY_LENGTH) / DAY_LENGTH)

    @property
    def is_daytime(self):
        return self.day_phase in ("dawn", "day")

    def _die(self):
        self.dead = True
        self.asleep = False
        self.hatching = False
        self._set_anim("idle", 0)

    def _base_weight(self):
        return data.load_requirements().get(self.num, {}).get("base_weight", 20)

    def _maybe_evolve(self):
        if self.sick or self.asleep or self.is_geriatric:
            return
        if self.stage_seconds < self.STAGE_DURATION.get(self.stage, 9e9):
            return
        target = evolution.select(self)
        if target is not None:
            self.evolve_to(target)

    def evolve_to(self, num):
        _, by_num = data.load_sprites()
        r = by_num[num]
        self.num, self.name = num, r["name"]
        self.stage, self.attribute = r["stage"], r["attribute"]
        self.stage_seconds = 0.0
        # per-stage care record resets; the next stage's care decides the next form
        self.care_mistakes = self.overeat = self.disturb = 0
        self.injuries = self.sick_count = 0
        self.weight = self._base_weight()
        # reaching a higher stage extends the total lifespan toward that stage's floor
        self.lifespan = max(self.lifespan, STAGE_LIFE.get(self.stage, self.lifespan))
        self._set_anim("happy", 2.5)

    # ---- care actions --------------------------------------------------------
    def _set_anim(self, name, ttl):
        self.anim, self.anim_ttl = name, ttl

    def feed(self, food=None):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            self.disturb += 1
            return "zzz... asleep"
        foods = data.load_foods()
        food = food or (foods[0] if foods else {"name": "Meat", "hunger": 1, "weight": 4, "mood": 5})
        if self.hunger >= 4:
            self.weight += 1
            self.overeat += 1
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
        self.hunger = _clamp(self.hunger + max(1, food["hunger"]), 0, 4)
        self.weight += food.get("weight", 1)
        self.mood = _clamp(self.mood + food.get("mood", 0), 0, 100)
        self._set_anim("eat", 1.4)
        return f"Fed {food['name']}."

    def can_train(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            self.disturb += 1
            return "zzz... asleep"
        if self.energy < 12:
            self._set_anim("refuse", 1.0)
            return "Too tired to train."
        return None

    def apply_training(self, hits, power, attribute=None):
        """Apply the training minigame result (hits 0..3, power 0..100).

        The player picks which attribute to build (attribute arg); it accumulates
        across the whole life (it is NOT reset on evolution), exactly like DVPet.
        """
        attr = attribute or (self.attribute if self.attribute in ("Vaccine", "Data", "Virus") else "Vaccine")
        if hits >= 2:
            self.strength = _clamp(self.strength + 1, 0, 4)
        gain = max(0, power)
        if attr == "Vaccine":
            self.vaccine += gain
        elif attr == "Data":
            self.data_power += gain
        elif attr == "Virus":
            self.virus += gain
        self.weight = max(1, self.weight - 2)
        self.energy = _clamp(self.energy - 15, 0, 100)
        self.mood = _clamp(self.mood + hits * 3, 0, 100)
        if hits >= 2:
            self.obedience += 1
        # training while overweight risks an injury
        if evolution.weight_category(self.weight, self._base_weight()) == "Over" and random.random() < 0.5:
            self.injuries += 1
        self._set_anim("happy" if hits >= 2 else "attack", 1.8)
        rank = "Perfect!" if hits == 3 else ("Good!" if hits == 2 else ("Meh." if hits == 1 else "Whiff."))
        return f"{rank} +{gain} {attr}"

    def can_battle(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage in ("Egg", "Fresh"):
            return "Too young to battle."
        if self.asleep:
            self.disturb += 1
            return "zzz... asleep"
        if self.energy < 10:
            self._set_anim("refuse", 1.0)
            return "Too tired to battle."
        return None

    def record_battle(self, won, enemy=None):
        """Resolve a finished battle: update battles/wins and rewards."""
        self.battles += 1
        self.energy = _clamp(self.energy - 10, 0, 100)
        if won:
            self.wins += 1
            self.mood = _clamp(self.mood + 8, 0, 100)
            lo, hi = (enemy or {}).get("bits", (1, 5))
            gained = random.randint(lo, hi)
            self.bits += gained
            self._set_anim("happy", 2.0)
            return f"Victory! +{gained} bits"
        self.mood = _clamp(self.mood - 10, 0, 100)
        if random.random() < 0.3:
            self.injuries += 1
        self._set_anim("sad", 2.0)
        return "Defeat..."

    def clean(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if not self.poop:
            return "Nothing to clean."
        n, self.poop = self.poop, 0
        self.mood = _clamp(self.mood + 3, 0, 100)
        return f"Cleaned {n} poop."

    def heal(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if not self.sick:
            return "Not sick."
        self.sick = False
        self.mood = _clamp(self.mood + 5, 0, 100)
        self._set_anim("heal", 1.5)
        return f"{self.name} feels better!"

    def toggle_sleep(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        self.asleep = not self.asleep
        self._set_anim("sleep" if self.asleep else "idle", 0)
        return "Lights off. Zzz." if self.asleep else "Lights on."

    def play(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            self.disturb += 1
            return "zzz... asleep"
        self.mood = _clamp(self.mood + 8, 0, 100)
        self.energy = _clamp(self.energy - 4, 0, 100)
        self._set_anim("play", 1.5)
        return "Played together!"

    # ---- shop / items --------------------------------------------------------
    def buy(self, entry):
        if self.bits < entry["price"]:
            return "Not enough bits."
        self.bits -= entry["price"]
        self.inventory[entry["key"]] = self.inventory.get(entry["key"], 0) + 1
        return f"Bought {entry['name']}."

    def use_item(self, key):
        if self.inventory.get(key, 0) <= 0:
            return "None left."
        e = data.consumable_by_key(key)
        if not e:
            return "?"
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        self.inventory[key] -= 1
        if self.inventory[key] <= 0:
            del self.inventory[key]
        is_food = key.startswith("f:")
        if e["hunger"]:
            self.hunger = _clamp(self.hunger + e["hunger"], 0, 4)
        self.mood = _clamp(self.mood + e["mood"], 0, 100)
        self.weight = max(1, self.weight + e["weight"])
        if e["energy"]:
            self.energy = _clamp(self.energy + e["energy"], 0, 100)
        if e["strength"]:
            self.strength = _clamp(self.strength + e["strength"], 0, 4)
        self.obedience += e["obedience"]
        self.vaccine = max(0, self.vaccine + e["vaccine"])
        self.data_power = max(0, self.data_power + e["data"])
        self.virus = max(0, self.virus + e["virus"])
        if e["cured"]:
            self.sick = False
        if e["healed"]:
            self.injuries = max(0, self.injuries - 1)
        self._set_anim("eat" if is_food else "happy", 1.4)
        return f"Used {e['name']}."

    # ---- presentation helpers -----------------------------------------------
    def status_word(self):
        if self.dead:
            return "passed away"
        if self.is_geriatric:
            return "elderly"
        if self.asleep:
            return "asleep"
        if self.sick:
            return "sick"
        if self.hunger == 0:
            return "starving"
        if self.poop >= 3:
            return "needs cleaning"
        if self.day_phase == "night" and not self.asleep and self.energy < 45:
            return "sleepy"
        if self.mood < 25:
            return "unhappy"
        if self.mood > 75:
            return "happy"
        return "ok"
