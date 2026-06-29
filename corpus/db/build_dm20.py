#!/usr/bin/env python3
"""Build corpus/db/dm20.json — the unified DM20 Digimon database.

Merges three corpus layers:
  - evolution CONDITIONS: corpus/canon/humulos/dm20/evo_ver1-5.md + evo_special.md  (canon)
  - stage TIMERS:         wayland-vpets docs/fragments/evol-dm.md (dm20 column)        (canon-adjacent)
  - SPRITE refs:          corpus/fan/wayland-vpets/assets/dm20/<Name>.png             (canon-sourced)

Conditions keep the verbatim `raw` string (ground truth) plus a best-effort `parsed`.
Run: python3 corpus/db/build_dm20.py
"""
import os, re, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.dirname(HERE)
HUM = os.path.join(CORPUS, "canon/humulos/dm20")
SPRITES = os.path.join(CORPUS, "fan/wayland-vpets/assets/dm20")
SPRITES_ALL = os.path.join(CORPUS, "fan/wayland-vpets/assets/dmall")

# dm20 real-time stage timers (wayland docs/fragments/evol-dm.md, dm20 column)
STAGE_TIMER = {
    "Baby I": "1 min (egg hatch)", "Baby II": "10 min", "Child": "6 h",
    "Adult": "24 h", "Perfect": "36 h", "Ultimate": "48 h", "Super Ultimate": None,
}
STAGE_RE = r'(Super Ultimate|Baby I{1,2}|Child|Adult|Perfect|Ultimate)'
# (Digitama 1min -> Baby I; the table's per-stage time = how long spent AT that stage before it can evolve)

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

# ---- known names (for splitting "Name (cond)" where Name may contain parens) ----
KNOWN = set()
for f in glob.glob(os.path.join(HUM, "evo_*.md")):
    for line in open(f):
        m = re.match(r'^\**([^|]+?)\**\s*\|', line)
        if m and "|" in line:
            KNOWN.add(norm(m.group(1)))
# add Coredramon variants explicitly (they appear as targets w/ embedded parens)
for n in ("Coredramon (Blue)", "Coredramon (Green)"):
    KNOWN.add(norm(n))

def split_target(t):
    """'Wingdramon (15 Battles...)' -> ('Wingdramon','15 Battles...').
    'Coredramon (Blue) (Slayerdra Egg)' -> ('Coredramon (Blue)','Slayerdra Egg').
    'Zubaeagermon' -> ('Zubaeagermon', '')."""
    t = t.strip()
    if norm(t) in KNOWN:
        return t, ""
    # strip the last top-level (...) and test
    m = re.match(r'^(.*)\(([^()]*)\)\s*$', t)
    if m:
        name, cond = m.group(1).strip(), m.group(2).strip()
        return name, cond
    return t, ""

def parse_cond(raw):
    """Best-effort structured parse; `raw` is always preserved."""
    if not raw or raw.lower() in ("none", "no requirements", "no further evolution listed"):
        return {}
    p = {}
    alts = re.split(r'\s+OR\s+', raw)
    if len(alts) > 1:
        p["alternatives"] = [parse_cond(a) for a in alts]
        return p
    def grab(pat):
        m = re.search(pat, raw, re.I); return m.group(1).strip() if m else None
    cm = grab(r'(\d+\+|\d+-\d+)\s*(?:Care Mistakes|CM)')
    if cm: p["care_mistakes"] = cm
    tr = grab(r'(\d+\+|\d+-\d+)\s*Training')
    if tr: p["training"] = tr
    of = grab(r'(\d+\+|\d+-\d+)\s*Overfeed')
    if of: p["overfeed"] = of
    b = grab(r'(\d+)\s*Battles?')
    if b: p["battles"] = int(b)
    v = grab(r'(\d+(?:-\d+)?)\s*Victor')
    if v: p["victories"] = v
    t = grab(r'Wait\s*(\d+)\s*Minutes?')
    if t: p["time_min"] = int(t)
    ve = grab(r'Version\s*(\d+)\s*Egg')
    if ve: p["version_egg"] = int(ve)
    se = grab(r'(\w+)\s*Egg\b')
    if se and not ve: p["special_egg"] = se
    tag = grab(r'Tag Battle.*?with\s+(.+?)\)?$')
    if tag: p["tag_battle_with"] = tag
    return p

# ---- sprite index ----
def sprite_index(d):
    idx = {}
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".png"):
                idx[norm(fn[:-4])] = os.path.relpath(os.path.join(d, fn), CORPUS)
    return idx
SPI = sprite_index(SPRITES)
SPI_ALL = sprite_index(SPRITES_ALL)
def find_sprite(name):
    k = norm(name)
    return SPI.get(k) or SPI_ALL.get(k)

# ---- parse evolution files ----
records = {}  # id -> record
def add(name, stage, attr, version, evos):
    rid = norm(name)
    r = records.get(rid)
    if not r:
        r = records[rid] = {
            "id": rid, "name": name, "stage": stage, "attribute": attr,
            "devices": {"dm20": {"versions": [], "stage_time": STAGE_TIMER.get(stage),
                                  "evolves_to": []}},
            "sprite": find_sprite(name),
            "sources": ["humulos:dm20"],
        }
    dev = r["devices"]["dm20"]
    if version not in dev["versions"]:
        dev["versions"].append(version)
    seen = {(e["to"], e["raw"]) for e in dev["evolves_to"]}
    for to, raw in evos:
        if (to, raw) not in seen:
            dev["evolves_to"].append({"to": to, "to_id": norm(to), "raw": raw, "parsed": parse_cond(raw)})
            seen.add((to, raw))
    return r

VER = {"evo_ver1.md": 1, "evo_ver2.md": 2, "evo_ver3.md": 3, "evo_ver4.md": 4, "evo_ver5.md": 5}
for fn in sorted(glob.glob(os.path.join(HUM, "evo_*.md"))):
    version = VER.get(os.path.basename(fn), "special")
    for line in open(fn):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.replace("**", "")
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 4:
            continue
        name, stage, attr, rest = parts[0], parts[1], parts[2], "|".join(parts[3:])
        # normalize stage label ("Stage III (Child)" -> "Child")
        sm = re.search(STAGE_RE, stage)
        stage = sm.group(1) if sm else stage
        rest = re.sub(r'^->\s*', '', rest).strip()
        evos = []
        if rest and rest.lower() not in ("(none)", "none", "(no evolution listed)"):
            for chunk in rest.split(";"):
                chunk = chunk.strip()
                if not chunk or chunk.lower() in ("(none)", "none"):
                    continue
                to, cond = split_target(chunk)
                evos.append((to, cond))
        add(name, stage, attr, version, evos)

# ---- extras: fusion terminals + colosseum-only enemies (evo_extra.md) ----
extra = os.path.join(HUM, "evo_extra.md")
if os.path.exists(extra):
    for line in open(extra):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 4:
            continue
        name, stage, attr, rest = parts[0], parts[1], parts[2], "|".join(parts[3:])
        sm = re.search(STAGE_RE, stage); stage = sm.group(1) if sm else stage
        obtain = re.sub(r'^obtain:\s*', '', rest).strip()
        enemy_only = "colosseum enemy" in obtain.lower()
        r = records.get(norm(name))
        if not r:
            r = records[norm(name)] = {
                "id": norm(name), "name": name, "stage": stage, "attribute": attr,
                "devices": {"dm20": {"versions": [], "stage_time": STAGE_TIMER.get(stage),
                                     "evolves_to": []}},
                "sprite": find_sprite(name), "sources": ["humulos:dm20"],
            }
        r["obtain"] = obtain
        r["playable"] = not enemy_only          # colosseum enemies are opponents, not raisable

# ---- output ----
no_sprite = sorted(r["name"] for r in records.values() if not r["sprite"])
playable = sum(1 for r in records.values() if r.get("playable", True))
out = {
    "_meta": {
        "device": "dm20", "source": "humulos.com/digimon/dm20 (conditions) + wayland-vpets (sprites+timers)",
        "count": len(records), "playable": playable, "enemy_only": len(records) - playable,
        "schema": "see corpus/README.md",
        "note": "conditions: `raw` verbatim from humulos; `parsed` best-effort. versions 1-5 + 'special' lines + evo_extra (fusion terminals + colosseum-only enemies). playable=false => colosseum opponent, not raisable.",
        "sprite_gaps": no_sprite,
        "sprite_gaps_note": "all 5 are colosseum enemy-only; wayland-vpets carries only their X-Antibody forms (Murmukusmon absent). Fallback: DVPet roster has them — source enemy sprites there if needed.",
    },
    "digimon": [records[k] for k in sorted(records)],
}
outpath = os.path.join(HERE, "dm20.json")
with open(outpath, "w") as fh:
    json.dump(out, fh, indent=1, ensure_ascii=False)

# ---- validation report ----
no_sprite = [r["name"] for r in records.values() if not r["sprite"]]
print(f"wrote {outpath}: {len(records)} Digimon")
print(f"sprites matched: {len(records)-len(no_sprite)}/{len(records)}")
if no_sprite:
    print("  NO sprite for:", ", ".join(sorted(no_sprite)))
