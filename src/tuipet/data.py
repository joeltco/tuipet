"""Load extracted sprites + game data from the DVPet CSVs."""
from __future__ import annotations
import csv, gzip, json, os
from functools import lru_cache

_HERE = os.path.dirname(__file__)
_DATA = os.path.join(_HERE, "data")
_RAW = _DATA  # bundled CSVs (digimon/evolutions/foods) live alongside sprites

# Authoritative frame roles, reverse-engineered from DVPet's View/SpriteAnim.class.
# Each creature strip has 11 frames (index 0-10):
#   0 idle/walk A      5 happy / cheer-up
#   1 idle/walk B      6 sad / unhappy
#   2 sleep/rest A     7 eat-closed (chew) / cheer-down
#   3 sleep/rest B     8 eat-open (mouth) / neutral
#   4 angry/refuse/attack   9 tired / sick / disliked / geriatric
#                          10 exhausted (very tired)
# Loops below mirror the game's own animations (cheer/jeer/eat/refuse/idleSleep).
ROLES = {
    "idle":   [0, 1],      # walk bob
    "walk":   [0, 1],
    "sleep":  [2, 3],      # idleSleep cycles 2,3
    "happy":  [5, 7],      # cheer(): good praise up=5 down=7
    "angry":  [6, 4],      # jeer(): bad praise up=6 down=4
    "eat":    [8, 7],      # eat(): mouth-open 8 / chew 7
    "refuse": [4],         # head-shake (mirrored); depressed -> 9
    "attack": [4, 6],      # battle/training charge poses
    "tantrum": [4, 6, 1],
    "poop":   [4, 5],
    "play":   [1, 5],
    "heal":   [8, 7],      # recover(): eats medicine
    "sad":    [6],
    "tired":  [9],
    "exhausted": [10],
    "yawn":   [8, 1],      # yawning(): mouth-open 8 -> settle 1
    "wake":   [3, 1],      # wakeUp(): groggy 3 -> up
    "surprise": [4, 6],    # surprising(): startle poses
    "shield": [4],         # weathering() rain: shielding pose
    "huddle": [9],         # weathering() snow/cold: huddle pose
}
# Roles drawn as a left/right mirror flip on alternating frames (head-shake etc.)
MIRROR_ROLES = {"refuse"}

STAGE_ORDER = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]


PLACEHOLDER_NUMS = set()


def _content_fill(frame):
    rows = [r for r in frame if "1" in r]
    if not rows:
        return 0.0
    left = min(r.find("1") for r in rows)
    right = max(r.rfind("1") for r in rows)
    w = right - left + 1
    return sum(r[left:right + 1].count("1") for r in rows) / (w * len(rows))


@lru_cache(maxsize=1)
def load_sprites():
    from . import placeholder
    with gzip.open(os.path.join(_DATA, "sprites.json.gz"), "rt") as fh:
        data = json.load(fh)
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
                foods.append({
                    "name": row["Name"],
                    "hunger": int(row["Hunger"] or 0),
                    "weight": int(row["Weight"] or 0),
                    "mood": int(row["Mood"] or 0),
                    "energy": int(row["Energy"] or 0),
                    "strength": int(row["Strength"] or 0),
                })
            except (KeyError, ValueError):
                continue
    return foods


def next_stage(stage):
    i = STAGE_ORDER.index(stage)
    return STAGE_ORDER[i + 1] if i + 1 < len(STAGE_ORDER) else None


def evolution_targets(num, stage):
    """Real evolution targets whose stage is the next stage up (with sprites)."""
    _, by_num = load_sprites()
    evo = load_evolutions()
    want = next_stage(stage)
    out = []
    for t in evo.get(num, []):
        rec = by_num.get(t)
        if rec and (want is None or rec["stage"] == want):
            out.append(t)
    # fall back to any next-stage creature if the graph has no usable target
    if not out and want:
        out = [n for n, rec in by_num.items() if rec["stage"] == want]
    return out

# ---------------------------------------------------------------------------
# Evolution requirements (parsed from digimon.csv).  Each Digimon's row holds
# the care/training conditions to evolve INTO that Digimon, as Key/Value gates
# where Key is a comparison operator and Value the threshold.  Mirrors the
# game's Model/EvolutionInfo + Model/Evolution.checkEvolReq exactly.
# ---------------------------------------------------------------------------
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


def _gate(row, key, val):
    cond = (row.get(key) or "None").strip() or "None"
    try:
        v = float(row.get(val) or 0)
    except ValueError:
        v = 0.0
    return (cond, v)


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
            "mood": (r.get("Mood") or "None").strip(),
            "time": (r.get("Time") or "None").strip(),
            "special": (r.get("SpecialEvolution") or "None").strip() or "None",
            "level_fought_min": _int_or(r.get("MinLevelFought (vaccine+data+virus+[health*100])/100"), 0),
            "level_fought": _gate(r, "LevelFoughtKey", "LevelFoughtValue"),
            "max_energy": _int_or(r.get("MaxEnergy"), 24),          # DVPet per-Digimon maxEnergy
            "sleep_energy_gain": _int_or(r.get("SleepEnergyGain"), 3),
        }
    return reqs


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
_MOVES = None


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
        bits = (r.get("BitsWon") or "1t5").split("t")
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
def load_maps():
    from collections import defaultdict
    enemies = load_enemies()
    by_mz = defaultdict(lambda: {"randoms": [], "bosses": []})
    for e in enemies:
        slot = "bosses" if e["boss"] else "randoms"
        by_mz[(e["map"], e["zone"])][slot].append(e)
    zmap = defaultdict(list)
    for z in csv.DictReader(open(os.path.join(_DATA, "zones.csv"))):
        try:
            m, zn = int(z["MapNum"]), int(z["ZoneNum"])
        except (KeyError, ValueError):
            continue
        ent = by_mz.get((m, zn), {"randoms": [], "bosses": []})
        zmap[m].append({
            "map": m, "zone": zn,
            "total_steps": int(z.get("TotalSteps") or 10000),
            "randoms": ent["randoms"], "bosses": ent["bosses"],
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
        "energy": int(num("Energy (<1 * maxEnergy)") or num("Energy")),
        "strength": int(num("Strength")),
        "obedience": int(num("Obedience")),
        "vaccine": int(num("Vaccine")),
        "data": int(num("Data")),
        "virus": int(num("Virus")),
        "cured": flag("Cured"),
        "healed": flag("Healed") or flag("Recovered"),
        "unfatigue": flag("Removes Fatigue"),
        "vitamin": int(num("Vitamins")) > 0,   # foods.csv Vitamins>0 (e.g. "Vitamin") guards vs injury worsening
        "undepressed": flag("Removes Depressed"),
    }


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


@lru_cache(maxsize=1)
def load_shop():
    """Shop inventory: resolved consumables with a stable key and shop price."""
    foods, items = _load_consumables()
    out = []
    seen = set()
    for r in csv.DictReader(open(os.path.join(_DATA, "shopConsumable.csv"))):
        try:
            cid = int(r["ConsumableID"])
        except (KeyError, ValueError):
            continue
        is_food = (r.get("IsFood") or "false").strip().lower() == "true"
        src = foods if is_food else items
        base = src.get(cid)
        if not base:
            continue
        key = f"{'f' if is_food else 'i'}:{cid}"
        if key in seen:
            continue
        seen.add(key)
        entry = dict(base)
        entry["key"] = key
        try:
            entry["price"] = int(r.get("Price") or entry["price"])
        except ValueError:
            pass
        out.append(entry)
    # special X-Antibody gear — not in shopConsumable.csv, but buyable here (and so
    # droppable as rare loot); using one induces the X-Antibody state, not care stats
    for sid, price in ((79, 2000), (14, 4000)):
        base = items.get(sid)
        key = f"i:{sid}"
        if base and key not in seen:
            entry = dict(base)
            entry["key"], entry["price"], entry["special"] = key, price, "xantibody"
            out.append(entry); seen.add(key)
    out.sort(key=lambda e: e["price"])
    return out


def consumable_by_key(key):
    for e in load_shop():
        if e["key"] == key:
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
            if not base:
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
            "compat_fields": lst("CompatibleField"), "compat_elements": lst("CompatibleElement"),
            "incompat_fields": lst("IncompatibleField"), "incompat_elements": lst("IncompatibleElement"),
        }
    return out
