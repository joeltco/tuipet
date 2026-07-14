"""Load extracted sprites + game data from the DVPet CSVs."""
from __future__ import annotations
import csv
import gzip
import json
import os
import re
from functools import lru_cache

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")
_RAW = _DATA  # bundled CSVs (digimon/evolutions/foods) live alongside sprites


class AssetsError(RuntimeError):
    """A REQUIRED bundled atlas is missing or damaged.  Carries a player-facing
    message: an interrupted install used to surface as a raw gzip traceback on
    the first render (professionalism sweep 2026-07-14).  Optional atlases
    (effects/icons/backgrounds) keep degrading gracefully instead."""


def _load_bundled(name):
    """gunzip+parse a required atlas, or raise AssetsError in plain words."""
    try:
        with gzip.open(os.path.join(_DATA, name), "rt") as fh:
            return json.load(fh)
    except (OSError, EOFError, ValueError) as e:
        raise AssetsError(
            f"tuipet's game data is missing or damaged ({name}).\n"
            f"Reinstall it:   pip install --force-reinstall tuipet\n"
            f"(running from a source checkout? build the assets first: "
            f"tools/setup_assets.sh)"
        ) from e

# Frame roles VERIFIED against DVPet View/SpriteAnim drawNum() args (each per-Digimon
# strip is 11 frames, index 0-10; sheet order preserved by extract_sprites col 0..10):
#   0 idle/neutral base      6 attack / cheer-up (HP_Training_AttackSuccess, attackDefault)
#   1 idle-B / walk-B / toy   7 eat-chew / cheer-down(big) / wake-end
#   2 sleep                   8 eat-swallow
#   3 stretch / yawn          9 dejected / fail / disliked (HP_Training_AttackFail, jeer-up)
#   4 cheer-down / clean-done 10 collapse / dying (Dying, jeer-down, exhausted)
#   5 excited / cheer-up(big)
# State->frames taken from the real animations: Cheering=5,7  Jeering=9,10  Eating=8,7(x3)
# attackDefault=6,0  Cleaning=0,4  Bounce/Jump(play)=1,5  Dying=10.
ROLES = {
    "idle":   [0, 1],      # Idling / Discovering walk
    "walk":   [0, 1],
    "sleep":  [2, 3],      # idleSleep
    "happy":  [5, 7],      # Cheering: cheer(true) up=5 down=7 -- the canonical praise/win/evolve bounce
    "angry":  [9, 10],     # Jeering: jeer(false) up=9 down=10 (severe/bad-health scold; mild jeer(true) is 6/4)
    "eat":    [8, 7],      # eat(): open-mouth 8 -> chew 7 (verified DVPet order)
    "refuse": [4],         # refuse(): frame 4 (9 if Depressed) shaken by mirror toggle
    "attack": [6, 0],      # attackDefault: strike 6 -> reset 0
    "tantrum": [9, 10],    # tuipet unhappy-idle -> jeer poses
    "poop":   [4, 5],      # poop(): squat 4 -> sit 5 (verified)
    "play":   [1, 5],      # Bounce/Jump toy interact: 1 -> 5
    "wash":   [0, 4],      # Cleaning/Bathe: scrub 0 -> refreshed 4
    "heal":   [7, 8],      # recover(): eat-medicine, same as eat
    "sad":    [9],         # dejected/fail pose (HP_Training_AttackFail)
    "tired":  [9],         # disliked/weary pose
    "exhausted": [10],     # collapse pose (Dying)
    "yawn":   [0, 8],      # yawning(): idle 0 -> open-mouth 8 (verified)
    "wake":   [2, 3, 1],   # wakeUp(): groggy 2/3 -> settle 1 (verified)
    "surprise": [1, 5],    # AngrySurprise startle beats 1,5
    # surprising() -- the THUNDER startle, disposition-keyed (audit 2026-07-06):
    # the sour pet barely flinches, neutral reacts, the SUNNY one jumps hardest
    "startle_sour": [0, 4],    # disposition -1: idle <-> mild (+4)
    "startle": [4, 6],         # disposition  0: +4 <-> +6
    "startle_sunny": [9, 10],  # disposition +1: the dramatic jump (+9 <-> +10)
    "shield": [4],         # weathering(): rain -> frame 4 (verified)
    "huddle": [9],         # weathering(): cold/snow -> frame 9 (verified)
}
MIRROR_ROLES = {"refuse"}

STAGE_ORDER = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]
# full growth order including the Egg stage, for age/stage-rank gating (shop, tournament)
STAGE_RANK = ["Egg"] + STAGE_ORDER


def stage_rank(stage):
    """Index of `stage` in the full growth order (Egg..Mega); an unknown stage
    counts as fully grown (gates shop unlocks and tournament age limits)."""
    try:
        return STAGE_RANK.index(stage)
    except ValueError:
        return len(STAGE_RANK)      # unknown stage -> treat as fully grown


def pretty_field(name):
    """Display form of a CamelCase Field value (the data keeps it joined for
    matching): 'NightmareSoldier' -> 'Nightmare Soldier'. 'None'/single words
    are unchanged."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name or "")


PLACEHOLDER_NUMS: set[int] = set()


def _content_fill(frame):
    rows = [r for r in frame if "1" in r]
    if not rows:
        return 0.0
    left = min(r.find("1") for r in rows)
    right = max(r.rfind("1") for r in rows)
    w = right - left + 1
    return sum(r[left:right + 1].count("1") for r in rows) / (w * len(rows))


def frames_for(num, egg_type=0):
    """The full frames list for a roster num -- or the egg's shell frames for
    num -1, which has NO roster sheet.  Raw `load_sprites()[1][num]` lookups
    were the recurring egg-crash pattern (habitat, training, battle, adventure,
    transport -- five instances; egg sweep 2026-07-06): use THIS instead.
    Never empty: unknown nums get one blank frame (blit tolerates it)."""
    if num == -1:
        from . import egg as egg_mod
        return egg_mod.frames(egg_type) or [""]
    rec = load_sprites()[1].get(num)
    return rec["frames"] if rec else [""]


def record_for(num):
    """The roster record for a num -- NEVER a KeyError.  A save can carry a
    num this build's dex doesn't know (a data refresh, a downgrade after an
    evolution on a newer roster, a lobby peer on a newer build): persistence
    loads it on purpose (test_robustness pins that), so every sprite fetch
    must survive it.  Unknown nums wear the placeholder record -- the raw
    `load_sprites()[1][num]` index was a CRASH LOOP: the .bak holds the same
    num, so every relaunch died on the first paint (audit 2026-07-13)."""
    rec = load_sprites()[1].get(num)
    if rec is None:
        from . import placeholder
        rec = {"frames": placeholder.FRAMES, "w": placeholder.W,
               "h": placeholder.H, "_placeholder": True}
    return rec


def bob_frame(num, frame_i, role="idle", beat=5, egg_type=0):
    """The idle-bob frame fetch: the role's pose keyed at frame_i // beat
    (beat 5 = the ~2Hz WALK_BEAT bob every scene screen uses; dna's urgency
    bob passes 2, the title's gentle bob 4).  This fetch lived in EIGHT
    hand-rolled copies across the screens, drifting across four cadences
    (refactor 2026-07-05).  num -1 = the EGG, whose sheet lives in egg data,
    not the roster -- the habitat browser CRASHED on an egg (egg-stage audit
    2026-07-05); pass the pet's egg_type for the right shell art.  Falls back
    to the first non-empty frame.  A positive num NEVER returns None: an
    unknown num (cross-version save or lobby peer) wears the placeholder --
    returning None here fed place_combatant/grid.prep a None mid-battle and
    mid-jogress (audit 2026-07-13)."""
    if num == -1:
        from . import egg as egg_mod
        fr = egg_mod.frames(egg_type)
        if not fr:
            return None
        return fr[(frame_i // beat) % 2] or fr[0]
    rec = record_for(num)
    roles = ROLES.get(role, ROLES["idle"])
    fr = rec["frames"]
    idx = roles[(frame_i // beat) % len(roles)]
    f = fr[idx] if idx < len(fr) else None
    return f or next((x for x in fr if x), None)


@lru_cache(maxsize=1)
def load_sprites():
    from . import placeholder
    data = _load_bundled("sprites.json.gz")
    for rec in data:
        frames = rec["frames"]
        first = next((f for f in frames if f), None)
        best = max((sum(r.count("1") for r in f) for f in frames if f), default=0)
        # unfinished cells (solid square, near-blank, or fully empty) -> blob
        if (first is None or best < 10 or _content_fill(first) > 0.97
                or rec["name"].strip().upper() in ("EMPTY", "", "NA", "NULL", "NONE")):
            PLACEHOLDER_NUMS.add(rec["num"])
            rec["frames"] = placeholder.FRAMES
            rec["w"], rec["h"] = placeholder.W, placeholder.H
            rec["_placeholder"] = True
        else:
            # fill empty animation frames with the first real frame so no role
            # (idle/eat/sleep/...) ever renders blank
            rec["frames"] = [f if f else first for f in frames]
    by_num = {d["num"]: d for d in data}
    return data, by_num


def is_placeholder(num):
    load_sprites()
    return num in PLACEHOLDER_NUMS


@lru_cache(maxsize=1)
def load_evolutions():
    """num -> list of target nums it can evolve into."""
    path = os.path.join(_RAW, "evolutions.csv")
    evo = {}
    with open(path) as fh:
        r = csv.reader(fh)
        next(r)
        for row in r:
            cells = [c for c in row if c.strip() != ""]
            if not cells:
                continue
            src = int(cells[0])
            evo[src] = [int(x) for x in cells[1:]]
    return evo


@lru_cache(maxsize=1)
def load_foods():
    path = os.path.join(_RAW, "foods.csv")
    foods = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                fid = int(row["FoodIdentificationNum"])
                foods.append({
                    "id": fid,
                    "key": f"f:{fid}",
                    # DVPet's Java UI embeds <br> line breaks in names
                    # ("Vaccine<br>Chip G") -- strip like the consumable parser
                    "name": (row["Name"] or "?").replace("<br>", " "),
                    "hunger": int(row["Hunger"] or 0),
                    "weight": int(row["Weight"] or 0),
                    "health": int(row.get("Health") or 0),   # permanent HP gain (HP Chip)
                    "mood": int(row["Mood"] or 0),
                    "energy": int(row["Energy"] or 0),
                    "strength": int(row["Strength"] or 0),
                    "obedience": int(row["Obedience"] or 0),
                    "enthusiasm": int(row["Enthusiasm"] or 0),
                    "category": (row.get("Type") or "").strip(),
                    "protein": int(row.get("Proteins") or 0),
                    "vitamin_n": int(row.get("Vitamins") or 0),
                    "mineral": int(row.get("Minerals") or 0),
                    # inventory model (DVPet Consumable): StartingQuantity seeds what
                    # you own; CanDec=false = never depletes (the staples: Meat/Fish/
                    # Fruit/Vegetable); ShowInInventory=false = not on the feed page
                    # (Med/Vitamin ride the heal flows instead)
                    "bm": int(row.get("BMGauge") or 0),
                    # canon re-audit 2026-07: applyConsumable reads these for FOODS
                    # too -- 39 calorie foods, 3 lifespan foods, 7 attribute foods,
                    # a sleep food and 2 temp foods were silently dropped
                    "calories": int(row.get("Calories") or 0),
                    "seconds": int(row.get("Seconds") or 0),
                    "vaccine": int(row.get("Vaccine") or 0),
                    "data": int(row.get("Data") or 0),
                    "virus": int(row.get("Virus") or 0),
                    "sleep_lapse": int(row.get("SleepLapse") or 0),
                    "temp": int(row.get("Temp") or 0),
                    # trait affinity (checkRefused personality mods): a food that
                    # suits the pet's temperament goes down easier
                    "t_glutton": int(row.get("Glutton") or 0),
                    "t_restless": int(row.get("Restless") or 0),
                    "t_disposition": int(row.get("Disposition") or 0),
                    "start": int(row.get("StartingQuantity") or 0),
                    "can_dec": (row.get("CanDec") or "").strip().lower() == "true",
                    "show": (row.get("ShowInInventory") or "").strip().upper() == "TRUE",
                })
            except (KeyError, ValueError):
                continue
    return foods



def _temp_range(s):
    try:
        a, b = (s or "40t60").split("t")
        return (int(a), int(b))
    except (ValueError, AttributeError):
        return (40, 60)


def _temp_req(s):
    """Evolution temperature requirement (TempReq "lo t hi"), or None if unset
    ("0t-1" means no requirement)."""
    try:
        lo, hi = (s or "0t-1").split("t")
        lo, hi = int(lo), int(hi)
        return (lo, hi) if (hi >= lo and hi >= 0) else None
    except (ValueError, AttributeError):
        return None


def _int_or(s, default):
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default


# DVPet DNA fields by name ("None" is Enum.Field ordinal 0 = a REAL bankable/chargeable
# slot; only NA is excluded). Order here is tuipet's menu display order -- inventory and
# evolution gates are keyed by NAME (digimon.csv {Field}Key/{Field}Value matched by name),
# so this tuple's order is independent of Enum.Field ordinals.
FOOD_CATEGORIES = ("Meat", "Fish", "Veg", "Fruit", "Med", "Junk", "Grain", "Dairy")
DNA_FIELDS = ("VirusBuster", "MetalEmpire", "DragonsRoar", "JungleTrooper",
              "DeepSaver", "NightmareSoldier", "WindGuardian", "NatureSpirit",
              "DarkArea", "None")


def _gate(row, key, val):
    cond = (row.get(key) or "None").strip() or "None"
    try:
        v = float(row.get(val) or 0)
    except ValueError:
        v = 0.0
    return (cond, v)


def _attack_index(s):
    """digimon.csv col 55 'vaccineNum:dataNum:virusNum' -> per-attribute special-orb index (-1 = none)."""
    parts = (s or "").split(":")
    out = {}
    for attr, i in (("Vaccine", 0), ("Data", 1), ("Virus", 2)):
        try:
            out[attr] = int(parts[i])
        except (ValueError, IndexError):
            out[attr] = -1
    return out


@lru_cache(maxsize=1)
def load_orbs():
    return _load_bundled("orbs.json.gz")


@lru_cache(maxsize=1)
def load_device_attacks():
    """deviceAttacks.csv: species -> its real-hardware attack in orbs.json.gz
    'device' (ripped from MultiVPet's data.win, the classic V-Pet lineup).
    Keyed by normalized name so every roster row of the species matches."""
    path = os.path.join(_RAW, "deviceAttacks.csv")
    out = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            nm = "".join(c for c in (r.get("Name") or "").lower() if c.isalnum())
            if nm and r.get("AttackKey"):
                out[nm] = r["AttackKey"]
    return out


def attack_orb(num, attribute, power, frame_i=0):
    """The attack projectile.  Device-accurate first (Joel 2026-07-14): a species
    in deviceAttacks.csv fires ITS OWN real-hardware attack for EVERY attribute,
    exactly like the original V-Pet -- frame_i animates the 2-frame attacks at
    the caller's 10Hz clock.  Everyone else keeps DVPet checkAttackSprite: the
    per-species special orb (attackSpritesSpecial.png, digimon.csv col 55) if set
    for this attribute, else the generic per-attribute orb at the power tier
    floor(power/25) from attackSprites.png."""
    orbs = load_orbs()
    req = load_requirements().get(num) or {}
    nm = "".join(c for c in (req.get("name") or "").lower() if c.isalnum())
    key = load_device_attacks().get(nm)
    if key:
        frames = orbs.get("device", {}).get(key)
        if frames:
            return frames[frame_i % len(frames)]
    idx = (req.get("attack_index") or {}).get(attribute, -1)
    if idx is not None and idx >= 0:
        sp = orbs["special"].get(str(idx))
        if sp:
            return sp
    tiers = orbs["generic"].get(attribute) or orbs["generic"]["Vaccine"]
    t = max(0, min(int(power) // 25, len(tiers) - 1))
    return tiers[t] or next((x for x in tiers if x), None)


@lru_cache(maxsize=1)
def load_requirements():
    path = os.path.join(_RAW, "digimon.csv")
    reqs = {}
    for r in csv.DictReader(open(path)):
        try:
            num = int(r["DigimonNum"])
        except (KeyError, ValueError):
            continue
        prob = (r.get("Probability") or "100;100").split(";")
        try:
            p0, p1 = int(prob[0]), int(prob[1]) if len(prob) > 1 else 100
        except ValueError:
            p0, p1 = 100, 100
        reqs[num] = {
            "priority": float(r.get("Priority Default") or 0),
            "tournament_able": (r.get("TournamentAble") or "TRUE").strip().upper() != "FALSE",
            "sleep_lapse_inc": int(float(r.get("SleepLapseInc") or 1)),   # sleep-pressure rate (babies 9)
            "prob": p0, "probBound": p1,
            "mistakes": _gate(r, "MistakesKey", "MistakesValue"),
            "overeat": _gate(r, "OvereatKey", "OvereatValue"),
            "sick": _gate(r, "SickKey", "SickValue"),
            "injured": _gate(r, "InjuredKey", "InjuredValue"),
            "disturb": _gate(r, "DisturbKey", "DisturbValue"),
            "obedience": _gate(r, "ObedienceKey", "ObedienceValue"),
            "battles": _gate(r, "BattlesKey", "BattlesValue"),
            "wins": _gate(r, "WinsKey", "WinsValue"),
            "vaccine": [_gate(r, "VaccinePowerFirstKey", "VaccinePowerFirstValue"),
                        _gate(r, "VaccinePowerSecondKey", "VaccinePowerSecondValue")],
            "data": [_gate(r, "DataPowerFirstKey", "DataPowerFirstValue"),
                     _gate(r, "DataPowerSecondKey", "DataPowerSecondValue")],
            "virus": [_gate(r, "VirusPowerFirstKey", "VirusPowerFirstValue"),
                      _gate(r, "VirusPowerSecondKey", "VirusPowerSecondValue")],
            "weight": (r.get("Weight") or "None").strip(),
            "base_weight": int(float(r.get("NewWeight") or 20)),
            "ideal_temp": _temp_range(r.get("IdealTemp")),
            "xantibody": (r.get("Xantibody") or "None").strip() or "None",
            "temp_req": _temp_req(r.get("TempReq")),
            "habitat_req": _int_or(r.get("Habitat"), -1),
            "field": (r.get("NewField") or "None").strip() or "None",
            "element": (r.get("Element") or "None").strip() or "None",
            "mood": (r.get("Mood") or "None").strip(),
            "time": (r.get("Time") or "None").strip(),
            "special": (r.get("SpecialEvolution") or "None").strip() or "None",
            "level_fought_min": _int_or(r.get("MinLevelFought (vaccine+data+virus+[health*100])/100"), 0),
            "level_fought": _gate(r, "LevelFoughtKey", "LevelFoughtValue"),
            "dna": {f: _gate(r, f + "Key", f + "Value") for f in DNA_FIELDS},
            "evol_item": _int_or(r.get("EvolItemID"), -1),   # item that triggers this form
            "attack_index": _attack_index(r.get("SpecialAttacksVaccineDataVirus")),
            "name": (r.get("Name") or "").strip(),
            "food_pref": (r.get("FoodPreference") or "None").strip() or "None",
            # the taste-ledger SEEDS (Taste.setPreference/setAversion): the
            # preference biases the drift +2, the AVERSION -2 -- and the
            # attribute aversion also keys the WEAK injury tables (it never
            # drifts; only favorite/disliked do)
            "attr_pref": (r.get("AttributePreference") or "None").strip() or "None",
            "attr_aversion": (r.get("AttributeAversion") or "None").strip() or "None",
            # the TIME seeds stand in until the emergent time_pref ledger forms
            # an opinion (Pet.favorite_time/disliked_time) -- ~97% of the dex
            # carries real values (Morning/Noon/Night; audit 2026-07-13)
            "time_pref": (r.get("TimePreference") or "None").strip() or "None",
            "time_aversion": (r.get("TimeAversion") or "None").strip() or "None",
            # HiddenEvolution (digicore audit 2026-07-06): 130 forms are
            # CONCEALED in canon's evolution tree until first reached
            "hidden_evo": (r.get("HiddenEvolution") or "FALSE").strip().upper() == "TRUE",
            "food_aversion": (r.get("FoodAversion") or "None").strip() or "None",
            "food_intol": [x.strip() for x in (r.get("FoodIntolerance(; separator)") or "").split(";")
                           if x.strip() and x.strip() != "None"],
            "major_food": (r.get("MajorFood") or "None").strip() or "None",
            "hunger_decay": _int_or(r.get("HungerDecayCoefficient"), 60),
            "strength_decay": _int_or(r.get("StrengthDecayCoefficient"), 50),
            "poop_lapse": _int_or(r.get("PoopLapseInc"), 1),
            "poop_limit": _int_or(r.get("PoopLimit"), 64),
            "poop_sick_mult": float(r.get("PoopSickChanceBoundMultiplier") or 1.0),
            "filth_mood": _int_or(r.get("FilthLapseMoodChange"), -1),
            "max_strength": _int_or(r.get("MaxStrength"), 4),
            "vaccine_change": _int_or(r.get("VaccineChange"), 0),    # attributeEvolChange
            "data_change": _int_or(r.get("DataChange"), 0),
            "virus_change": _int_or(r.get("VirusChange"), 0),
            "lifespan_mod": _int_or(r.get("LifespanMod"), 0),        # per-form lifespan delta
            "give_item": _int_or(r.get("GiveItem"), -1),             # consumable granted on evolve
            "incarnations": _gate(r, "IncarnationsKey", "IncarnationsValue"),  # generation-count gate
            "max_energy": _int_or(r.get("MaxEnergy"), 24),          # DVPet per-Digimon maxEnergy
            "sleep_energy_gain": _int_or(r.get("SleepEnergyGain"), 3),
            "awake_inc": _int_or(r.get("AwakeLapseInc"), 1),   # 1 adult / 16 babies: short naps
            "can_assist": (r.get("CanAssist") or "").strip().upper() == "TRUE",   # AI Assistant pool
        }
    return reqs


def assist_pool():
    """The digimon.csv CanAssist pool -- Evolution.getRandomAssistDigimon's
    candidates for WHICH Digimon answers an AI Assistant contract."""
    return sorted(n for n, r in load_requirements().items() if r.get("can_assist"))


@lru_cache(maxsize=1)
def _name_canonical_map():
    """num -> the CANONICAL (lowest) num among same-name roster rows.  DVPet
    stores duplicate species rows (the 1410+ egg-hatch block mirrors the
    chart's canonical rows) and its dex sync is BY NAME: checkNaturalUnlocked
    propagates `unlocked` across every same-name row, so a form raised under
    either num reveals both (album/dex audit 2026-07-06).  Empty names stay
    themselves -- never lump the unnamed rows into one group."""
    _, by_num = load_sprites()
    groups = {}
    for n, rec in by_num.items():
        nm = (rec.get("name") or "").upper()
        if nm:
            groups.setdefault(nm, []).append(n)
    out = {}
    for ns in groups.values():
        c = min(ns)
        for n in ns:
            out[n] = c
    return out


def canonical_num(num):
    """The name-canonical roster num (checkNaturalUnlocked's identity)."""
    return _name_canonical_map().get(num, num)


@lru_cache(maxsize=1)
def _canonical_habitat_by_name():
    """DVPet stores duplicate species rows: the egg-hatch duplicates carry
    Habitat -1 while the base row carries the real habitat. Map name -> habitat."""
    path = os.path.join(_RAW, "digimon.csv")
    out = {}
    for r in csv.DictReader(open(path)):
        h = _int_or(r.get("Habitat"), -1)
        if h >= 0:
            out.setdefault((r.get("Name") or "").strip(), h)
    return out


def natural_habitat(num):
    """The habitat a Digimon calls home (-1 = none). Resolves DVPet's duplicate
    rows so egg-hatched forms still find their species' habitat."""
    h = load_requirements().get(num, {}).get("habitat_req", -1)
    if h is not None and h >= 0:
        return h
    _, by_num = load_sprites()
    name = (by_num.get(num, {}).get("name") or "").strip()
    return _canonical_habitat_by_name().get(name, -1)

# ---------------------------------------------------------------------------
# Battle enemies (parsed from enemies.csv).  Each enemy references a Digimon by
# number (its sprite + attribute) and carries battle Health and attribute power.
# ---------------------------------------------------------------------------


_ATTACKS = None


def _load_attacks():
    global _ATTACKS
    if _ATTACKS is None:
        _ATTACKS = {}
        cols = {"Vaccine": "VaccineName:Effect", "Data": "DataName:Effect", "Virus": "VirusName:Effect"}
        for r in csv.DictReader(open(os.path.join(_DATA, "digimon.csv"))):
            try:
                n = int(r["DigimonNum"])
            except (KeyError, ValueError):
                continue
            info = {}
            for a, c in cols.items():
                parts = [p.strip() for p in (r.get(c, "") or "").split(":")]
                effect = parts[1] if len(parts) > 1 and parts[1] else "None"
                info[a] = {"name": parts[0] if parts else "", "effect": effect,
                           "conditions": [p for p in parts[2:] if p]}
            _ATTACKS[n] = info
    return _ATTACKS


def move_name(num, attribute):
    """The flavour name of a Digimon's attack for an attribute (DVPet
    VaccineName/DataName/VirusName columns), e.g. 'Exhaust Flame'."""
    return (_load_attacks().get(num) or {}).get(attribute, {}).get("name", "")


def attack_info(num, attribute):
    """Full DVPet attack for an attribute: {name, effect, conditions[]} parsed from
    the digimon.csv Name:Effect:Condition(s) cell (AttackEffectProcess input)."""
    return (_load_attacks().get(num) or {}).get(attribute) or {"name": "", "effect": "None", "conditions": []}


@lru_cache(maxsize=1)
def load_enemies():
    _, by_num = load_sprites()
    path = os.path.join(_DATA, "enemies.csv")
    enemies = []
    for r in csv.DictReader(open(path)):
        try:
            dnum = int(r["Name"])
        except (KeyError, ValueError):
            continue
        rec = by_num.get(dnum)
        if not rec:
            continue  # enemy has no usable sprite (placeholder) -> skip
        vac = int(r.get("VaccinePower") or 0)
        dat = int(r.get("DataPower") or 0)
        vir = int(r.get("VirusPower") or 0)
        attr = rec["attribute"]
        if attr not in ("Vaccine", "Data", "Virus"):
            attr = max((("Vaccine", vac), ("Data", dat), ("Virus", vir)), key=lambda t: t[1])[0]
        # the real header is the essay-length "BitsWon (range of random bits -
        # ...)" -- a bare .get("BitsWon") never matched, so every enemy paid the
        # 1..5 fallback instead of its real purse (bosses pay 100..2000!):
        # boss-battle audit 2026-07.  Same trap as "MedicineHours (number...)".
        raw = next((v for k, v in r.items() if k and k.startswith("BitsWon")), "")
        bits = (raw or "1t5").split("t")
        try:
            blo, bhi = int(bits[0]), int(bits[-1])
        except ValueError:
            blo, bhi = 1, 5
        enemies.append({
            "num": dnum, "name": rec["name"], "stage": rec["stage"],
            "hp": max(2, int(r.get("Health") or 5)),
            "vaccine": vac, "data_power": dat, "virus": vir, "attribute": attr,
            "boss": (r.get("IsZoneBoss") or "FALSE").strip().upper() == "TRUE",
            "map": int(r.get("Map") or 1), "zone": int(r.get("Zone") or 1),
            "bits": (blo, bhi),
            "location": int(r.get("Location") or 0),
            "penalty": int(r.get("Penalty") or 0),
            "chance": int(r.get("AppearanceChance/100") or 100),
            "loot_table": int(r.get("LootTableID") or -1),
            # only the last boss carries one ("You saved<br>the Digital<br>World!"):
            # it cues the canon victory parade after the final ZoneChange
            "parade_msg": ((r.get("BossParadeMessage") or "").replace("<br>", " ").strip()
                           if (r.get("BossParadeMessage") or "null") != "null" else ""),
        })
    return enemies


def enemies_for_stage(stage):
    """Enemies whose Digimon are at the given stage (fallback: all)."""
    pool = [e for e in load_enemies() if e["stage"] == stage]
    return pool or load_enemies()


# ---------------------------------------------------------------------------
# Adventure maps: ordered maps -> ordered zones, each with its random-encounter
# enemies and zone boss(es), parsed from zones.csv + enemies.csv.
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_tournies():
    """Tournament trophies (tournies.csv): per-season cups with field/attribute/age
    restrictions, a BitModifier prize, ItemWon/FoodWon prizes, and enemy overrides."""
    path = os.path.join(_DATA, "tournies.csv")
    rows = list(csv.DictReader(open(path)))
    if not rows:
        return []
    hdr = list(rows[0].keys())
    age_col = next((k for k in hdr if k.startswith("AgeLimit")), "AgeLimit")
    food_col = next((k for k in hdr if k.startswith("FoodWon")), "FoodWonqAmount")

    def na(v):
        v = (v or "NA").strip()
        return "" if v in ("NA", "None", "") else v

    out = []
    for r in rows:
        try:
            tid = int(r["Trophy"])
        except (KeyError, ValueError):
            continue
        fid, famt = -1, 0
        fw = r.get(food_col) or "-1q-1"
        if "q" in fw:
            a, b = fw.split("q", 1)
            try:
                fid, famt = int(a), int(b)
            except ValueError:
                pass
        try:
            item = int(r.get("ItemWon") or -1)
        except ValueError:
            item = -1
        try:
            bm = float(r.get("BitModifier") or 1)
        except ValueError:
            bm = 1.0
        try:
            prelim = int(r.get("Prelim") or 0)
        except ValueError:
            prelim = 0
        out.append({
            "prelim": prelim,
            "id": tid, "sprite": int(r.get("SpriteNum") or 0),
            "season": na(r.get("Season")) or "Spring",
            "field_req": na(r.get("FieldRestriction")),
            "attr_req": na(r.get("AttributeRestriction")),
            "age_limit": na(r.get(age_col)),
            "bit_mod": bm, "item": item, "food_id": fid, "food_amt": famt,
            "reset_season": (r.get("ResetWonOnSeasonChange") or "FALSE").strip().upper() == "TRUE",
            "same_day_retry": (r.get("SameDayRetry") or "FALSE").strip().upper() == "TRUE",
            "enemy_stage": na(r.get("OverrideEnemyStage")),
            "enemy_attr": na(r.get("OverrideEnemyAttribute")),
            "enemy_elem": na(r.get("OverrideEnemyElement")),
            "enemy_field": na(r.get("OverrideEnemyField")),
        })
    return out


def _town_ranges():
    """towns.csv TownRange ("4201t4300") per TownID -- the REAL step spans."""
    out = {}
    for t in csv.DictReader(open(os.path.join(_DATA, "towns.csv"))):
        try:
            lo, hi = (t.get("TownRange") or "0t0").split("t")
            out[int(t["TownID"])] = (int(lo), int(hi))
        except (KeyError, ValueError):
            continue
    return out


def _zone_bgs(spec):
    """'0t600:12;601t1300:6;...' -> [(lo, hi, habitat_id)] step spans."""
    out = []
    for part in spec.split(";"):
        part = part.strip()
        if not part or ":" not in part or "t" not in part:
            continue
        span, _, hid = part.partition(":")
        lo, _, hi = span.partition("t")
        try:
            out.append((int(lo), int(hi), int(hid)))
        except ValueError:
            continue
    return out


@lru_cache(maxsize=1)
def load_maps():
    from collections import defaultdict
    enemies = load_enemies()
    by_mz = defaultdict(lambda: {"randoms": [], "bosses": []})
    for e in enemies:
        slot = "bosses" if e["boss"] else "randoms"
        by_mz[(e["map"], e["zone"])][slot].append(e)
    towns = _town_ranges()
    zmap = defaultdict(list)
    for z in csv.DictReader(open(os.path.join(_DATA, "zones.csv"))):
        try:
            m, zn = int(z["MapNum"]), int(z["ZoneNum"])
        except (KeyError, ValueError):
            continue
        ent = by_mz.get((m, zn), {"randoms": [], "bosses": []})
        tids = [int(x) for x in (z.get("TownID;") or "").split(";") if x.strip().isdigit()]
        zmap[m].append({
            "map": m, "zone": zn,
            "total_steps": int(z.get("TotalSteps") or 10000),
            "randoms": ent["randoms"], "bosses": ent["bosses"],
            # the zone's REAL town step-spans (WorldMap towns; rest + no encounters)
            "towns": sorted((*towns[t], t) for t in tids if t in towns),
            # the zone's discoverable loot pools (Zone.checkItem draws uniformly)
            "rand_items": [int(x) for x in (z.get("RandomItems") or "").split(":") if x.strip().isdigit()],
            "rand_foods": [int(x) for x in (z.get("RandomFood") or "").split(":") if x.strip().isdigit()],
            # BackgroundsAndRange: the journey's SCENERY -- "lo t hi : habitat_id"
            # spans; the backdrop changes as the pet walks the zone (DVPet canon)
            "bgs": _zone_bgs(z.get("BackgroundsAndRange") or ""),
        })
    return [{"map": m, "zones": sorted(zmap[m], key=lambda z: z["zone"])}
            for m in sorted(zmap)]

# ---------------------------------------------------------------------------
# Shop & consumables (foods.csv / items.csv sold via shopConsumable.csv).
# Each consumable carries care effects applied to the pet when used.
# ---------------------------------------------------------------------------
def _consumable(row, id_field):
    def num(k):
        try:
            return float(row.get(k) or 0)
        except ValueError:
            return 0.0
    def flag(k):
        return (row.get(k) or "FALSE").strip().upper() == "TRUE"
    return {
        "id": int(row[id_field]),
        "name": (row.get("Name") or "?").replace("<br>", " "),
        "desc": (row.get("Description") or "").replace("<br>", " "),
        "price": int(num("DefaultPrice")),
        "hunger": int(num("Hunger")),
        "mood": int(num("Mood")),
        "enthusiasm": int(num("Enthusiasm")),   # DVPet keeps spirit separate from mood
        "weight": int(num("Weight")),
        # a FRACTIONAL energy is a share of maxEnergy (canon applyItem: the
        # X-Program's -0.8, the Digimentals' -0.66) -- the old int() zeroed
        # every one of them (energy audit 2026-07-06).  Whole values stay int.
        "energy": (lambda v: v if v != int(v) else int(v))(
            num("Energy (<1 * maxEnergy)") or num("Energy")),
        "strength": int(num("Strength")),
        "obedience": int(num("Obedience")),
        "vaccine": int(num("Vaccine")),
        "data": int(num("Data")),
        "virus": int(num("Virus")),
        "cured": flag("Cured"),
        # DVPet Healed clears an injury; Recovered only restores battle HP (no tuipet
        # analog -- HP is recomputed per battle), so do NOT fold Recovered into healed,
        # else Steak/Tuna/Honey/Bath/etc. would falsely cure injuries (DVPet applyConsumable).
        "healed": flag("Healed"),
        # foods.csv uses FatiguedRelieved/DepressedRelieved; items.csv uses Removes *
        "unfatigue": flag("Removes Fatigue") or flag("FatiguedRelieved"),
        "vitamin": int(num("Vitamins")) > 0,   # foods.csv Vitamins>0 (e.g. "Vitamin") guards vs injury worsening
        "undepressed": flag("Removes Depressed") or flag("DepressedRelieved"),
        "seconds": int(num("Seconds")),     # DVPet setTotalLifespan: lifespan delta (sec)
        "temp": int(num("Temp")),           # DVPet temp change (clamped 0..MaxTemp=100)
        # ChangeToPrefTemp (canon: snap temp to the ideal midpoint; only the
        # Futon carries it) is DELIBERATELY unported -- Joel 2026-07-14:
        # "futons aren't supposed to be the go-to if the mon is cold".  The
        # futon pauses temperature, full stop; warming is the thermostat's
        # job (habitatscreen) or a warm consumable's (Temp>0).
        "sleep": flag("Sleep"),             # DVPet item Sleep flag: induce sleep
        # foods.csv SleepLapse: the bedtime nudge (Caffeine Pill) -- parsed by
        # load_foods for feed() but DROPPED here, so the bag door lost the
        # pill's signature effect (items.csv has no column -> 0; audit 2026-07-13)
        "sleep_lapse": int(num("SleepLapse")),
        # items.csv Disturb: using this item WAKES a sleeping pet -- canon useItem's
        # `if (item.disturb()) this.disturb()`.  Every item disturbs but the Futon
        # (Disturb=FALSE); foods have no column, so flag() defaults them to False.
        "disturb": flag("Disturb"),
        # DVPet FoodID/ItemID cols: ";"-list of consumables this one yields when used
        # (a "crafter" -- Toy Oven bakes random foods, Chocolate Egg pops random capsules)
        "unlocks_food": _idlist(row.get("FoodID")),
        "unlocks_item": _idlist(row.get("ItemID")),
        "action": (row.get("AnimationType") or "").strip(),  # DVPet item behaviour driver
        "dexnum": int(num("DigimonID")),  # direct ItemEvol target form (-1 if none)
        "category": (row.get("Type") or "").strip(),  # foods.csv food category for taste
        "effect_id": int(num("EffectID")) if (row.get("EffectID") or "").strip() not in ("", "-1") else -1,
        # DVPet Consumable uses-model: a held consumable carries uses up to MaxUses;
        # using spends UsesPer*; can_inc/can_dec gate buying/using (foods/items.csv).
        "max_uses": int(num("MaxUses") or 1),
        "gift_chance": int(num("GiftChance/100")),   # per-item odds of being the gift-call present
        # applyConsumable recovery deltas (in LAPSES): Med -2 sick, Bandage -2 injury
        "cure_lapse": int(num("CureLapseChange")),
        "heal_lapse": int(num("HealLapseChange")),
        "fatigue_lapse_change": int(num("FatigueLapseChange")),
        # toy engagement (applyItemNoObedience) + personality mood shaping
        "diminishing": flag("DiminishingReturns"),
        "interest_change": int(num("ItemDisinterestChange")),
        "t_glutton": int(num("Glutton")),
        "t_restless": int(num("Restless")),
        "t_disposition": int(num("Disposition")),
        "health": int(num("Health")),   # permanent fullHealthPoints gain (HP Chip)
        # items.csv AdventureLifeInc (Life Recovery, item 27): +N Digital World
        # life, gated at MaxAdventureLife (PhysicalState.useItem)
        "adv_life": int(num("AdventureLifeInc")),

        "uses_per": int(num("UsesPerFood") or num("UsesPerItem") or 1),
        # items.csv names these CanIncUses/CanDecUses; foods.csv CanInc/CanDec --
        # reading only the items name defaulted every FOOD to can_inc=True, letting
        # staples into the gift/discover pools (audit 2026-07)
        "can_inc": (row.get("CanIncUses") or row.get("CanInc") or "TRUE").strip().upper() != "FALSE",
        "can_dec": (row.get("CanDecUses") or row.get("CanDec") or "TRUE").strip().upper() != "FALSE",
        # DVPet getNormalItems: only items flagged ShowInInventory appear in the bag
        # (transports / key / evolution items are hidden). Foods have no column -> shown.
        "show_in_inventory": (row.get("ShowInInventory") or "TRUE").strip().upper() != "FALSE",
    }


def _idlist(s):
    out = []
    for x in (s or "").split(";"):
        x = x.strip()
        if x and x.lstrip("-").isdigit() and int(x) >= 0:
            out.append(int(x))
    return out


@lru_cache(maxsize=1)
def _load_consumables():
    foods, items = {}, {}
    for r in csv.DictReader(open(os.path.join(_DATA, "foods.csv"))):
        try:
            foods[int(r["FoodIdentificationNum"])] = _consumable(r, "FoodIdentificationNum")
        except (KeyError, ValueError):
            continue
    for r in csv.DictReader(open(os.path.join(_DATA, "items.csv"))):
        try:
            items[int(r["ItemIdentificationNum"])] = _consumable(r, "ItemIdentificationNum")
        except (KeyError, ValueError):
            continue
    return foods, items


# An item is "functional" in tuipet only if use_item actually applies an effect.
# Pure action-items whose AnimationType drives an UNIMPLEMENTED system carry
# zero stats and currently do nothing -- they are filtered out of the shop
# and loot until their system is built. Extend this as each system is
# implemented (transports, ItemEvol, Inherit and Recover lives all are now).
_FUNC_STATS = ("hunger", "mood", "enthusiasm", "weight", "energy",
               "strength", "obedience", "vaccine", "data", "virus")
_FUNC_FLAGS = ("cured", "healed", "unfatigue", "undepressed", "vitamin")


# DVPet world-warp items (items.csv AnimationType); handled by transportscreen.
TRANSPORT_ACTIONS = {"PhoenixTransport", "BirdraTransport", "GarudaTransport", "WhaTransport"}


def item_is_functional(e):
    if not e:
        return False
    if any(e.get(k) for k in _FUNC_STATS) or any(e.get(k) for k in _FUNC_FLAGS):
        return True
    if e.get("seconds") or e.get("temp") or e.get("sleep"):   # lifespan / temp / sleep items
        return True
    if e.get("effect_id", -1) >= 0:     # grants a temporary care effect (Futon)
        return True
    if e.get("action") == "ItemEvol":   # item-triggered evolution (now implemented)
        return True
    if e.get("action") == "Inherit":    # the Digimemory (now implemented)
        return True
    if e.get("adv_life"):               # Life Recovery (now implemented)
        return True
    if e.get("action") in TRANSPORT_ACTIONS:   # world-warp items (now implemented)
        return True
    return bool(e.get("special") or e.get("unlocks_food") or e.get("unlocks_item"))


# ---------------------------------------------------------------------------
# Bag taxonomy: shop_category buckets owned consumables into the bag tabs
# (food / medicine / toy / chip / special).  The SHOP roster itself is the
# DVPet home-shop roll (shop.py) -- no invented category/stage gating.
# ---------------------------------------------------------------------------
_SPECIAL_ANIMS = {"ItemEvol", "X_Program", "Inherit", "PhoenixTransport",
                  "BirdraTransport", "GarudaTransport", "WhaTransport", "PortToilet"}


def shop_category(e):
    """Bucket a consumable into food / medicine / toy / chip / special."""
    act = (e.get("action") or "").strip()
    if act in _SPECIAL_ANIMS or e.get("special") == "xantibody":
        return "special"
    if "Chip" in (e.get("name") or ""):          # the named battle chips only
        return "chip"
    if ("Med" in (e.get("category") or "") or e.get("cured")
            or act in ("Recover", "Bandaging")):  # cures / first-aid (not every healing food)
        return "medicine"
    return "food" if str(e.get("key", "")).startswith("f:") else "toy"


def _shop_season4(val, default=0):
    """Parse a ';'-separated per-season list (Spring;Summer;Fall;Winter) of ints."""
    parts = [x.strip() for x in (val or "").split(";")]
    out = []
    for i in range(4):
        try:
            out.append(int(parts[i]))
        except (IndexError, ValueError):
            out.append(default)
    return out


def _shop_time4(val):
    """Parse DefaultTimeAvailable 'AtB;AtB;AtB;AtB' -> 4 per-season [start,end] hour windows."""
    out = []
    for seg in (val or "").split(";"):
        seg = seg.strip()
        if "t" in seg:
            a, b = seg.split("t", 1)
            try:
                out.append([int(a), int(b)]); continue
            except ValueError:
                pass
        out.append([0, 23])
    while len(out) < 4:
        out.append(out[-1] if out else [0, 23])
    return out[:4]


def _default_econ(r):
    """DVPet home-shop economy: each consumable's OWN Default* columns
    (FoodType/Item build their _homeShop ShopConsumable from these).
    shopConsumable.csv is only the per-TOWN override table -- tuipet has the
    single home shop, so the Default* columns are the whole economy."""
    def i(k, d):
        try:
            return int(r.get(k) or d)
        except ValueError:
            return d
    return {
        "min_stock": i("DefaultMinStock", 1), "max_stock": i("DefaultMaxStock", 1),
        "stock_chance": _shop_season4(r.get("DefaultStockChance(SpringSummerFallWinter)"), 100),
        "time_avail": _shop_time4(r.get("DefaultTimeAvailable(HtH;SpringSummerFallWinter)")),
        "must_stock": (r.get("DefaultMustStock") or "false").strip().lower() == "true",
        "sale_chance": _shop_season4(r.get("DefaultSaleChance(SpringSummerFallWinter)"), 0),
        "sale_factor": i("DefaultSaleFactor", 1), "resell_factor": i("DefaultResellFactor", 0),
        "shop_unlocked": (r.get("ShopUnlocked") or "FALSE").strip().upper() == "TRUE",
    }


@lru_cache(maxsize=1)
def load_shop_overrides():
    """shopConsumable.csv: the per-TOWN override table -- towns.csv references
    these rows by ShopConsumableID to reprice/restock consumables locally."""
    out = {}
    path = os.path.join(_DATA, "shopConsumable.csv")
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path)):
        try:
            sid = int(r["ShopConsumableID"])
        except (KeyError, ValueError):
            continue
        def i(k, d):
            try:
                return int(r.get(k) or d)
            except ValueError:
                return d
        out[sid] = {
            "consumable_id": i("ConsumableID", -1),
            "is_food": (r.get("IsFood") or "false").strip().lower() == "true",
            "price": i("Price", 0),
            "min_stock": i("minStock", 1), "max_stock": i("maxStock", 1),
            "stock_chance": _shop_season4(r.get("stockChance(SpringSummerFallWinter)"), 100),
            "time_avail": _shop_time4(r.get("DefaultTimeAvailable(HtH;SpringSummerFallWinter)")),
            "must_stock": (r.get("MustStock") or "false").strip().lower() == "true",
            "sale_chance": _shop_season4(r.get("SaleChance(SpringSummerFallWinter)"), 0),
            "sale_factor": i("SaleFactor", 1), "resell_factor": i("ResellFactor", 0),
        }
    return out


@lru_cache(maxsize=1)
def load_towns():
    """towns.csv: the full town records -- local shop overrides + inventory
    sizes, sell permissions, and the town tournament (slots 0-23 are hourly
    cups; slots past 23 -- where ForceTrophies pin -- are ALWAYS open)."""
    out = {}
    for r in csv.DictReader(open(os.path.join(_DATA, "towns.csv"))):
        try:
            tid = int(r["TownID"])
        except (KeyError, ValueError):
            continue
        def ids(k):
            return [int(x) for x in (r.get(k) or "").split(":") if x.strip().isdigit()]
        forced = [int(x) for x in (r.get("ForceTrophies") or "").split(";")
                  if x.strip().lstrip("-").isdigit() and int(x) >= 0]

        def hours(k):
            """'6t23;6t23;24t17;6t23' -> per-season (start, end) opening spans,
            keyed Spring/Summer/Fall/Winter.  Canon Utility.isOpen(h, span) is a
            plain h >= start and h <= end -- so a '24t17' span (start past any
            real hour) is CLOSED FOR THE SEASON, not a wraparound."""
            spans = [(s.split("t") + ["", ""])[:2] for s in (r.get(k) or "").split(";")]
            seasons = ("Spring", "Summer", "Fall", "Winter")
            return {seasons[i]: (int(a), int(b))
                    for i, (a, b) in enumerate(spans[:4])
                    if a.strip().lstrip("-").isdigit() and b.strip().lstrip("-").isdigit()}
        out[tid] = {
            "id": tid,
            "items_override": ids("OverrideDefaultItemsSettings(ShopConsumableID)"),
            "foods_override": ids("OverrideDefaultFoodSettings(ShopConsumableID)"),
            "food_max": int(r.get("FoodShopInventoryMax") or 8),
            "item_max": int(r.get("ItemShopInventoryMax") or 12),
            "can_sell_items": (r.get("CanSellItems") or "false").strip().lower() == "true",
            "can_sell_food": (r.get("CanSellFood") or "false").strip().lower() == "true",
            "tournament_limit": int(r.get("TournamentLimit (0 to 23 are hours 0 to 23 \u2013 anything higher is always open)") or
                                    r.get("TournamentLimit") or 0),
            "forced_trophies": forced,
            # per-season shop opening hours (FoodShopOpen/ItemShopOpen columns);
            # winter-market towns (6/13/18) open ONLY in winter by this data
            "food_hours": hours("FoodShopOpen(SpringSummerFallWinter)"),
            "item_hours": hours("ItemShopOpen(SpringSummerFallWinter)"),
            # TownBackgroundID: the town's canonical scenery (a habitat id) --
            # shown on arrival in adventure and behind the town lobby
            "bg_habitat": (int(r["TownBackgroundID"])
                           if (r.get("TownBackgroundID") or "").strip().lstrip("-").isdigit()
                           and int(r["TownBackgroundID"]) >= 0 else None),
        }
    return out


def _shop_econ_default():
    """Always-stocked, no-sale defaults for specialty items not in shopConsumable.csv."""
    # NOT must_stock: these specialty extras (X-Antibody etc.) are not in DVPet's
    # shopConsumable.csv -- keep them buyable but as an occasional rare find, not a
    # permanent shelf fixture, so they do not clutter the faithful storefront.
    return {"min_stock": 1, "max_stock": 1, "stock_chance": [20] * 4,
            "time_avail": [[6, 23]] * 4, "must_stock": False,
            "sale_chance": [0] * 4, "sale_factor": 1, "resell_factor": 10}


@lru_cache(maxsize=1)
def home_shop_pool():
    """Every consumable + its own Default* shop economy.  randomizeShop pools
    the ones with ShopUnlocked && price > 0 (shop.py applies that filter); the
    rest are here so bag/loot lookups get data-driven resell factors too."""
    foods, items = _load_consumables()
    out = {}
    for fn, id_field, src, prefix in (("foods.csv", "FoodIdentificationNum", foods, "f"),
                                      ("items.csv", "ItemIdentificationNum", items, "i")):
        for r in csv.DictReader(open(os.path.join(_DATA, fn))):
            try:
                cid = int(r[id_field])
            except (KeyError, ValueError):
                continue
            base = src.get(cid)
            if not base:
                continue
            e = dict(base)
            e["key"] = f"{prefix}:{cid}"
            e.update(_default_econ(r))
            out[e["key"]] = e
    # tuipet specialty adaptations (kept from the old shop): the X-gear, the plain
    # Vitamin and the crafters ship with price 0 / ShopUnlocked false in the data,
    # but their mechanics must stay reachable -- stocked as occasional 20% finds
    for key, price in (("i:79", 2000), ("i:14", 4000), ("f:5", 300), ("f:58", 800), ("i:66", 1200)):
        e = out.get(key)
        if e and not (e.get("shop_unlocked") and e.get("price", 0) > 0):
            e["price"] = price
            e.update(_shop_econ_default())
            e["shop_unlocked"] = True
            if key in ("i:79", "i:14"):
                e["special"] = "xantibody"
    return list(out.values())


def consumable_by_key(key):
    for e in home_shop_pool():
        if e["key"] == key:
            return e
    # fall back to the full tables -- crafted/loot consumables need not have a shop slot
    try:
        kind, cid = key.split(":"); cid = int(cid)
    except (ValueError, AttributeError):
        return None
    foods, items = _load_consumables()
    base = (foods if kind == "f" else items).get(cid)
    if base:
        e = dict(base); e["key"] = key
        return e
    return None


@lru_cache(maxsize=1)
def load_loot_tables():
    """DVPet loot tables: table_id -> ordered list of {key, name, rate}.

    Built from lootTable.csv (table -> drop-rate IDs) and dropRate.csv
    (drop-rate ID -> consumable + percentage). A single 0..100 draw walks the
    list; the slack below 100 is the chance nothing drops (see loot.roll)."""
    foods, items = _load_consumables()
    rates = {}
    with open(os.path.join(_DATA, "dropRate.csv")) as fh:
        rd = csv.reader(fh)
        next(rd, None)
        for row in rd:
            if len(row) < 4 or not row[0].strip():
                continue
            try:
                did, cid, rate = int(row[0]), int(row[1]), int(row[3])
            except ValueError:
                continue
            is_food = row[2].strip().upper() == "TRUE"
            base = (foods if is_food else items).get(cid)
            if not base or not item_is_functional(base):   # no inert loot drops
                continue
            rates[did] = {"key": ("f:%d" if is_food else "i:%d") % cid,
                          "name": base["name"], "rate": rate}
    tables = {}
    with open(os.path.join(_DATA, "lootTable.csv")) as fh:
        rd = csv.reader(fh)
        next(rd, None)
        for row in rd:
            if not row or not row[0].strip():
                continue
            try:
                tid = int(row[0])
            except ValueError:
                continue
            tables[tid] = [rates[int(c)] for c in row[1:]
                           if c.strip().isdigit() and int(c) in rates]
    return tables


@lru_cache(maxsize=1)
def load_backgrounds():
    """Habitat background scenes (per time-of-day/weather frame) keyed by file name."""
    path = os.path.join(_DATA, "backgrounds.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=1)
def load_effects():
    """Auxiliary effect overlays (poop/zzz/frozen/wash/emotes) keyed by name."""
    path = os.path.join(_DATA, "effects.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=1)
def load_icons():
    """Food/item icons (frame 0) keyed f:<id> / i:<id>, or empty if not extracted."""
    path = os.path.join(_DATA, "icons.json.gz")
    if not os.path.exists(path):
        return {}
    try:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# Habitats (habitats.csv).  Each habitat is a home with a seasonal climate that
# drives the weather/temperature system, plus Field/Element affinities that help
# or hurt a pet living there.  Faithful to DVPet's Habitat model; the one tuning
# is WEATHER_CHANCE_SCALE, dividing DVPet's 1/# precip chance for the compressed
# clock so weather is actually visible.
# ---------------------------------------------------------------------------
WEATHER_CHANCE_SCALE = 4


@lru_cache(maxsize=1)
def load_care_effects():
    """DVPet careEffect.csv -> {id: effect}. Temporary care buffs (the Futon's sleep
    boost): a duration plus per-tick rate changes ("amount;every_n_ticks") and pause
    flags. Applied by pet.use_item / pet.tick."""
    def pair(v):
        parts = (v or "0;0").split(";")
        try:
            return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except ValueError:
            return (0, 0)
    def flag(v):
        return (v or "FALSE").strip().upper() == "TRUE"
    out = {}
    path = os.path.join(_DATA, "careEffect.csv")
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path)):
        try:
            eid = int(r["EffectID"])
        except (ValueError, KeyError, TypeError):
            continue
        out[eid] = {
            "name": (r.get("Name") or "").replace("<br>", " ").strip(),
            "desc": (r.get("Description") or "").replace("<br>", " ").strip(),
            "duration": int(r.get("MaxDuration") or 0),
            "end_on_sleep": flag(r.get("EndOnSleepChange")),
            "pause_temp": flag(r.get("PauseTemp")),
            "pause_call": flag(r.get("PauseCall")),
            "mood": pair(r.get("MoodChange")),
            "energy": pair(r.get("EnergyChange")),
            "hunger": pair(r.get("HungerChange")),
            "strength": pair(r.get("StrengthChange")),
            "can_reapply": flag(r.get("CanReapply")),
        }
    return out


@lru_cache(maxsize=1)
def load_digicore_config():
    """DVPet digicoreMenuConfig.csv -> {num: {label, icon, icon_x}}.
    Icon/IconX name the SPECIAL core badge png (setupDigicore info[1]/info[2]);
    a literal "null" HIDES the badge for that Digimon; unlisted Digimon get the
    default X-antibody-state badges."""
    label = {"burstCore.png": "Burst", "twelveCore.png": "Twelve",
             "twoCore.png": "Two", "darkcore.png": "Dark"}
    key = {"burstCore.png": "core_burst", "twelveCore.png": "core_twelve",
           "twoCore.png": "core_two", "darkcore.png": "core_dark"}
    out = {}
    path = os.path.join(_DATA, "digicoreMenuConfig.csv")
    if not os.path.exists(path):
        return out
    for r in csv.reader(open(path)):
        if len(r) < 2 or not r[0].strip().isdigit():
            continue
        icon = (r[1] or "").strip()
        icon_x = (r[2] or "").strip() if len(r) > 2 else ""
        out[int(r[0])] = {
            "label": label.get(icon),
            "icon": "hidden" if icon == "null" else key.get(icon),
            "icon_x": "hidden" if icon_x == "null" else key.get(icon_x),
        }
    return out


@lru_cache(maxsize=1)
def load_digicore_icons():
    """Back-compat: {num: core_label} for the Data Book PERSON page."""
    return {n: c["label"] for n, c in load_digicore_config().items() if c["label"]}


@lru_cache(maxsize=1)
def load_egg_unlock():
    """DVPet eggUnlock.csv -> {egg_index: rule}. Joined to tuipet egg indices by the
    egg's hatch name. Each rule is the parsed set of conditions that gate the egg;
    egg.evaluate() tests them against persistence.get_progress()."""
    from . import egg as egg_mod
    name_to_idx = {}
    for i in range(egg_mod.count()):
        name_to_idx.setdefault(egg_mod.hatch_name(i), i)

    def _int(v):
        v = (v or "").strip()
        return int(v) if v.lstrip("-").isdigit() else None

    def _opt(v):
        v = (v or "").strip()
        return None if v in ("", "-1", "None", "FALSE") else v

    rules = {}
    path = os.path.join(_DATA, "eggUnlock.csv")
    rows = list(csv.reader(open(path)))
    for r in rows[1:]:
        if len(r) < 23:
            continue
        idx = name_to_idx.get(r[0].strip())
        if idx is None:
            continue                      # egg not in this tuipet build
        hist = None
        if _opt(r[12]):
            hist = [int(x) for x in r[12].split(":") if x.strip().isdigit()]
        price = _int(r[2]) or 0
        rules[idx] = {
            "idx": idx,
            "name": r[0].strip(),
            "start": r[1].strip() == "TRUE",
            "price": price if price > 0 else 0,
            "map": _int(r[3]) if (_int(r[3]) is not None and _int(r[3]) >= 0) else None,
            "stage": _opt(r[4]),
            "xanti": r[5].strip() == "TRUE",
            "tourney": _int(r[6]) if (_int(r[6]) is not None and _int(r[6]) >= 0) else None,
            "zone": _opt(r[7]),
            "gen": _int(r[8]) if (_int(r[8]) is not None and _int(r[8]) >= 0) else None,
            "prev_field": _opt(r[9]),
            "prev_attr": _opt(r[10]),
            "prev_elem": _opt(r[11]),
            "history": hist,
            "food": _int(r[13]) if (_int(r[13]) is not None and _int(r[13]) >= 0) else None,
            "item": _int(r[14]) if (_int(r[14]) is not None and _int(r[14]) >= 0) else None,
            "habitat": _int(r[15]) if (_int(r[15]) is not None and _int(r[15]) >= 0) else None,
            "password": _opt(r[16]),
            # canon re-audit 2026-07: the checker compares these against the
            # PREVIOUS generation's snapshot, so they must source the (Temp)
            # prev-gen columns 18/20 -- the old 17/19 read the CURRENT-pet
            # columns (a latent mis-map; every one of the four is data-empty
            # in the corpus, so nothing observable changed)
            "obedience": _int(r[18]) if (_int(r[18]) is not None and _int(r[18]) >= 0) else None,
            "mood": _int(r[20]) if (_int(r[20]) is not None and _int(r[20]) >= 0) else None,
            "desc": (r[21] or "").strip(),
            "can_perm": r[22].strip() == "TRUE",
            # tuipet achievement columns (LINES_SPEC §7): unlocks that tell the
            # story of the egg -- lifetime wins (Sakumon = the battle egg),
            # album breadth (Petitmon = the collector egg), Mega-class kills
            # (Dodomon = the X egg)
            "wins": _int(r[23]) if (len(r) > 23 and _int(r[23]) is not None and _int(r[23]) >= 0) else None,
            "album_n": _int(r[24]) if (len(r) > 24 and _int(r[24]) is not None and _int(r[24]) >= 0) else None,
            "mega": _int(r[25]) if (len(r) > 25 and _int(r[25]) is not None and _int(r[25]) >= 0) else None,
            # online connections (DM20 connection-battle unlocks: Corona/Luna/
            # Meicoo/DORU) -- distinct tamers linked via a completed lobby
            # bout or jogress; persistence.record_connection() feeds it
            "connections": _int(r[26]) if (len(r) > 26 and _int(r[26]) is not None and _int(r[26]) >= 0) else None,
            # tuipet storefront (egg-ladder redesign 2026-07-12): where a
            # buyable egg is sold -- "home" (common shop) / "town" (biome-
            # exclusive rare) / "" (earned-free, never in a shop)
            "store": (r[27].strip().lower() if len(r) > 27 else ""),
        }
    return rules


@lru_cache(maxsize=1)
def load_titles():
    """titles.csv: the HONORS ladder -- purely cosmetic tamer titles, priced
    as the late-game prestige sink (bit-sink design 2026-07-14).  A title is
    profile-level (it survives generations) and rides the STATUS panel plus
    the lobby presence card."""
    out = []
    for r in csv.DictReader(open(os.path.join(_DATA, "titles.csv"))):
        try:
            out.append({"id": int(r["TitleID"]), "name": (r["Name"] or "").strip(),
                        "price": int(r["Price"]),
                        "desc": (r.get("Description") or "").strip()})
        except (KeyError, ValueError):
            continue
    return out


def title_name(tid):
    """The honor's display name ('' for -1/unknown -- nothing worn)."""
    for t in load_titles():
        if t["id"] == tid:
            return t["name"]
    return ""


@lru_cache(maxsize=1)
def load_habitats():
    path = os.path.join(_DATA, "habitats.csv")
    out = {}
    for r in csv.DictReader(open(path)):
        try:
            hid = int(r["ID"])
        except (KeyError, ValueError):
            continue

        def rng(k):
            try:
                a, b = (r.get(k) or "0t0").split("t")
                return (int(a), int(b))
            except (ValueError, AttributeError):
                return (0, 0)

        def num(k, default=0):
            try:
                return int(r.get(k) or default)
            except ValueError:
                return default

        def lst(k):
            return [x for x in (r.get(k) or "").split(";") if x and x != "Empty"]

        chance = num("Weather Chance (1/#)")
        out[hid] = {
            "id": hid,
            "name": r.get("Name") or f"Habitat {hid}",
            "bg": (r.get("File Name (png)") or "").strip(),
            "desc": r.get("Description") or "",
            "price": num("Price"),
            "unlocked": (r.get("Unlocked") or "FALSE").strip().upper() == "TRUE",
            "temps": {"Spring": rng("Spring Temp (#t#)"), "Summer": rng("Summer Temp (#t#)"),
                      "Fall": rng("Fall Temp (#t#)"), "Winter": rng("Winter Temp (#t#)")},
            "precip_mod": {"Spring": num("Spring Mod (inc precipitation during season)"),
                           "Summer": num("Summer Mod (inc precipitation during season)"),
                           "Fall": num("Fall Mod (inc precipitation during season)"),
                           "Winter": num("Winter Mod (inc precipitation during season)")},
            "cloud_mod": num("Cloud Mod (inc precipitation when cloudy)"),
            "weather_chance": 0 if chance <= 0 else max(1, chance // WEATHER_CHANCE_SCALE),
            "weather_change": num("Weather Change (make worse or clear up)", 100),
            "night_tf": num("NightTempFactor", 10),
            "morning_tf": num("MorningTempFactor", 3),
            # per-season daylight triple [morningStart, noonStart, nightStart]
            # (PhysicalState.checkTime bands the day by the HOME's latitude)
            "times": {season: tuple(int(x) for x in ((r.get(col) or "6;14;19").split(";") + [19, 19])[:3])
                      for season, col in (("Spring", "SpringTime"), ("Summer", "SummerTime"),
                                          ("Fall", "FallTime"), ("Winter", "WinterTime"))},
            "compat_fields": lst("CompatibleField"), "compat_elements": lst("CompatibleElement"),
            "incompat_fields": lst("IncompatibleField"), "incompat_elements": lst("IncompatibleElement"),
        }
    return out
