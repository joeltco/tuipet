"""The roster + sim data (tier-1 split, 2026-07-17): sprites, the
evolution graph, the requirement corpus, canonical species mapping, stage
grammar.  Everything the SIM reads to know who a Digimon is."""
from __future__ import annotations
import csv  # noqa: F401
import gzip  # noqa: F401
import json  # noqa: F401
import os
import re  # noqa: F401
from functools import lru_cache  # noqa: F401

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")
_RAW = _DATA  # bundled CSVs (digimon/evolutions/foods) live alongside sprites


class AssetsError(RuntimeError):
    """A REQUIRED bundled atlas is missing or damaged.  Carries a player-facing
    message: an interrupted install used to surface as a raw gzip traceback on
    the first render (professionalism sweep 2026-07-14).  Optional atlases
    (effects/icons/backgrounds) keep degrading gracefully instead."""

def _damaged(name):
    """The one damaged-install message, shared by every loader."""
    return AssetsError(
        f"tuipet's game data is missing or damaged ({name}).\n"
        f"Reinstall it:   pip install --force-reinstall tuipet\n"
        f"(running from a source checkout? build the assets first: "
        f"tools/setup_assets.sh)")


def _load_bundled(name):
    """gunzip+parse a required atlas, or raise AssetsError in plain words."""
    try:
        with gzip.open(os.path.join(_DATA, name), "rt") as fh:
            return json.load(fh)
    except (OSError, EOFError, ValueError) as e:
        raise _damaged(name) from e


def _open_data(path):
    """open() a required csv/json data file, or raise AssetsError in the
    same plain words as _load_bundled -- the gz side always spoke kindly
    about a broken install while the csv side crashed with a raw
    FileNotFoundError traceback (data audit 2026-07-18)."""
    try:
        return open(path)
    except OSError as e:
        raise _damaged(os.path.basename(path)) from e

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
    with _open_data(path) as fh:
        r = csv.reader(fh)
        next(r)
        for row in r:
            cells = [c for c in row if c.strip() != ""]
            if not cells:
                continue
            src = int(cells[0])
            evo[src] = [int(x) for x in cells[1:]]
    # the one missing Frontier reversion edge (Fusion/Mode audit 2026-07-18,
    # unsealed by the spirit shelf): every Beast spirit's sheet links back to
    # its Human form (Vritramon 1125 -> Agunimon...) EXCEPT Bolgmon 1129 ->
    # Blitzmon 1119 (the Mode row that read "NO BASE") -- graft it.
    evo.setdefault(1129, [])
    if 1119 not in evo[1129]:
        evo[1129].append(1119)
    return evo

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
def load_requirements():
    path = os.path.join(_RAW, "digimon.csv")
    reqs = {}
    for r in csv.DictReader(_open_data(path)):
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
            # EvolFood: a FOOD-triggered form (food audit 2026-07-15) -- the
            # corpus has exactly one: Citramon evolves by eating an Orange
            # (food 42).  Locked out of natural timed care like item forms.
            "evol_food": _int_or(r.get("EvolFood"), -1),
            # per-species stomach (canon getStomachCapacity, geriatric-shrunk
            # at pet.stomach_capacity()): the applyFood diminishing divisor
            # and feed()'s mood gates read THIS, not a flat 4 (food audit
            # 2026-07-15; canon egg default 10)
            "stomach_capacity": _int_or(r.get("StomachCapacity"), 10),
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

def album_roster():
    """The album's page order: every name-canonical, non-placeholder roster
    num, sorted.  The SINGLE SOURCE for both the digicore trophy denominator
    and the album screen's pages — the book and its scoreboard can never
    disagree (the 1218/1547 uncompletable-album lesson, roster audit
    2026-07-14)."""
    _, by = load_sprites()
    return sorted({canonical_num(n) for n in by if not is_placeholder(n)})
