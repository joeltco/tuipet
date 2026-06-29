#!/usr/bin/env python3
"""Build corpus/db/dmx.json — unified Digital Monster X database.

Conditions from humulos /dmx/ (V1 XA/XB), /dmx/2/ (V2 XC/XD), /dmx/3/ Kera line — CLEAN.
V3 XE/XF main trees are NOT yet captured cleanly (see canon/humulos/dmx/evo_v3_STATUS.md);
those mons still appear here (sprite + stage timer) with evolution_status="v3_pending".
Sprites + stage timers: wayland-vpets assets/dmx + docs/fragments/evol-dm.md (dmx column).
"""
import os, re, json, glob

HERE = os.path.dirname(os.path.abspath(__file__)); CORPUS = os.path.dirname(HERE)
HUM = os.path.join(CORPUS, "canon/humulos/dmx")
SPR = os.path.join(CORPUS, "fan/wayland-vpets/assets/dmx")
SPR_ALL = os.path.join(CORPUS, "fan/wayland-vpets/assets/dmall")

STAGE_TIMER = {"Baby I": "10 min", "Baby II": "12 h", "Child": "24 h", "Adult": "32 h",
               "Perfect": "40 h", "Ultimate": None, "Super Ultimate": None, "Hyper Ultimate": None, "Egg": "1 min"}
STAGE_RE = r'(Hyper Ultimate|Super Ultimate|Baby I{1,2}|Child|Adult|Perfect|Ultimate|Egg)'

def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower())

KNOWN = set()
for f in glob.glob(os.path.join(HUM, "evo_*.md")):
    for line in open(f):
        if "|" in line and not line.startswith("#"):
            KNOWN.add(norm(line.split("|")[0]))

def split_target(t):
    t = t.strip()
    if norm(t) in KNOWN: return t, ""
    m = re.match(r'^(.*?)\(([^()]*)\)\s*$', t)
    if m: return m.group(1).strip(), m.group(2).strip()
    return t, ""

def parse_cond(raw):
    if not raw or raw.lower() in ("none", "no requirements"): return {}
    alts = re.split(r'\s+OR\s+', raw)
    if len(alts) > 1: return {"alternatives": [parse_cond(a) for a in alts]}
    p, rl = {}, raw
    def g(pat):
        m = re.search(pat, rl, re.I); return m.group(1).strip() if m else None
    cm = g(r'(\d+\+?|\d+-\d+)\s*(?:Care Mistakes?|CM)');     p.update(care_mistakes=cm) if cm else None
    ef = g(r'(\d+\+?|\d+-\d+)\s*Effort');                    p.update(effort=ef) if ef else None
    lv = g(r'Level\s*(\d+\+?|\d+-\d+)');                     p.update(level=lv) if lv else None
    d6 = g(r'Defeat\s*(\d+\+?|\d+-\d+)\s*Stage VI');         p.update(defeat_stage6=d6) if d6 else None
    cb = g(r'(\d+)\s*Cumulative Battles');                   p.update(cumulative_battles=int(cb)) if cb else None
    tm = g(r'Wait\s*(\d+)\s*Minutes?');                      p.update(time_min=int(tm)) if tm else None
    areas_c = re.findall(r'(?:Clear Area|Area)\s*(\d+|SP)\b(?!\s*[Nn]ot)', rl)
    if areas_c: p["area_cleared"] = areas_c
    areas_nc = re.findall(r'Area\s*(\d+|SP)\s*[Nn]ot cleared', rl)
    if areas_nc: p["area_not_cleared"] = areas_nc
    if re.search(r'Special Random Encounter cleared', rl, re.I): p["special_encounter"] = "cleared"
    elif re.search(r'Special Random Encounter [Nn]ot cleared', rl, re.I): p["special_encounter"] = "not_cleared"
    return p

def sprite_index(d):
    idx = {}
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".png"): idx[norm(fn[:-4])] = os.path.relpath(os.path.join(d, fn), CORPUS)
    return idx
SPI, SPI_ALL = sprite_index(SPR), sprite_index(SPR_ALL)
def find_sprite(n): return SPI.get(norm(n)) or SPI_ALL.get(norm(n))

records = {}
def rec(name, stage=None, attr=None):
    r = records.get(norm(name))
    if not r:
        r = records[norm(name)] = {"id": norm(name), "name": name, "stage": stage, "attribute": attr,
            "devices": {"dmx": {"versions": [], "stage_time": STAGE_TIMER.get(stage), "evolves_to": []}},
            "sprite": find_sprite(name), "sources": ["humulos:dmx" ]}
    if stage and not r["stage"]:
        r["stage"] = stage; r["devices"]["dmx"]["stage_time"] = STAGE_TIMER.get(stage)
    if attr and attr != "Free" and not r["attribute"]: r["attribute"] = attr
    return r

VER = {"evo_v1.md": 1, "evo_v2.md": 2, "evo_v3_kera.md": 3}
for fn in sorted(glob.glob(os.path.join(HUM, "evo_v*.md"))):
    ver = VER.get(os.path.basename(fn))
    if ver is None: continue
    for line in open(fn):
        line = line.strip().replace("**", "")
        if not line or line.startswith("#") or "|" not in line: continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 4: continue
        name, stage, attr, rest = parts[0], parts[1], parts[2], "|".join(parts[3:])
        sm = re.search(STAGE_RE, stage); stage = sm.group(1) if sm else stage
        r = rec(name, stage, attr)
        if ver not in r["devices"]["dmx"]["versions"]: r["devices"]["dmx"]["versions"].append(ver)
        rest = re.sub(r'^->\s*', '', rest).strip()
        if rest.lower() in ("(none)", "none", ""): continue
        seen = {(e["to"], e["raw"]) for e in r["devices"]["dmx"]["evolves_to"]}
        for chunk in rest.split(";"):
            chunk = chunk.strip()
            if not chunk or chunk.lower() in ("(none)", "none"): continue
            subv = None
            mt = re.search(r'\[(X[A-F])\]', chunk)
            if mt: subv = mt.group(1); chunk = chunk.replace(f"[{subv}]", "").strip()
            to, cond = split_target(chunk)
            if (to, cond) in seen: continue
            seen.add((to, cond))
            e = {"to": to, "to_id": norm(to), "raw": cond, "parsed": parse_cond(cond)}
            if subv: e["sub_version"] = subv
            r["devices"]["dmx"]["evolves_to"].append(e)
            rec(to)  # ensure target exists as a record

# ---- spine: every wayland dmx sprite name becomes a record (V3-only mons get stubs) ----
for k, path in SPI.items():
    if k not in records:
        # recover a display name from the filename
        fn = os.path.basename(path)[:-4]
        records[k] = {"id": k, "name": fn, "stage": None, "attribute": None,
            "devices": {"dmx": {"versions": [3], "stage_time": None, "evolves_to": []}},
            "sprite": path, "sources": ["wayland-vpets:dmx"], "evolution_status": "v3_pending"}

no_sprite = sorted(r["name"] for r in records.values() if not r["sprite"])
v3pending = sorted(r["name"] for r in records.values() if r.get("evolution_status") == "v3_pending")
out = {"_meta": {"device": "dmx", "count": len(records),
        "source": "humulos /dmx (V1 XA/XB) + /dmx/2 (V2 XC/XD) + /dmx/3 Kera line; wayland sprites+timers",
        "complete": "V1+V2+Kera evolution conditions CLEAN; V3 XE/XF main trees pending (see canon/humulos/dmx/evo_v3_STATUS.md)",
        "v3_pending_count": len(v3pending), "v3_pending": v3pending,
        "sprite_gaps": no_sprite,
        "condition_fields": "care_mistakes, effort, level, area_cleared[], area_not_cleared[], defeat_stage6, cumulative_battles, special_encounter, sub_version (XA-XF), time_min, alternatives[]"},
       "digimon": [records[k] for k in sorted(records)]}
with open(os.path.join(HERE, "dmx.json"), "w") as fh: json.dump(out, fh, indent=1, ensure_ascii=False)
print(f"wrote dmx.json: {len(records)} mons | sprites {len(records)-len(no_sprite)}/{len(records)} | v3_pending {len(v3pending)}")
if no_sprite: print("  no sprite:", ", ".join(no_sprite))
