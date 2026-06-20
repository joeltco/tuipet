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
        # unfinished art shows as a solid square; swap in the generic blob sprite
        first = next((f for f in rec["frames"] if f), None)
        if first is not None and _content_fill(first) > 0.97:
            PLACEHOLDER_NUMS.add(rec["num"])
            rec["frames"] = placeholder.FRAMES
            rec["w"], rec["h"] = placeholder.W, placeholder.H
            rec["_placeholder"] = True
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
            "mood": (r.get("Mood") or "None").strip(),
            "time": (r.get("Time") or "None").strip(),
            "special": (r.get("SpecialEvolution") or "None").strip() or "None",
        }
    return reqs

# ---------------------------------------------------------------------------
# Battle enemies (parsed from enemies.csv).  Each enemy references a Digimon by
# number (its sprite + attribute) and carries battle Health and attribute power.
# ---------------------------------------------------------------------------
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
    out.sort(key=lambda e: e["price"])
    return out


def consumable_by_key(key):
    for e in load_shop():
        if e["key"] == key:
            return e
    return None


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
