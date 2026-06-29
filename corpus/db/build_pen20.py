#!/usr/bin/env python3
"""Build corpus/db/pen20.json — unified Pendulum Ver.20th database.

Conditions from humulos /pen20/ per-version (Nature Spirits / Deep Savers / Nightmare
Soldiers / Wind Guardians / Metal Empire). Pendulum's signature mechanic is JOGRESS (DNA):
combine two partners. Sprites + stage timers from wayland-vpets assets/pen20.
NOTE: pen20's full roster (~240) = these 5 classic versions + 20th-anniversary bonus lines
(Guilmon/V-mon/Terriermon/DORUmon/etc.) NOT yet pulled -> those appear sprite-only,
addition_pending=true.
"""
import os, re, json, glob

HERE = os.path.dirname(os.path.abspath(__file__)); CORPUS = os.path.dirname(HERE)
HUM = os.path.join(CORPUS, "canon/humulos/pen20")
SPR = os.path.join(CORPUS, "fan/wayland-vpets/assets/pen20")

STAGE_TIMER = {"Baby I": "10 min", "Baby II": "12 h", "Child": "24 h",
               "Adult": "40 h", "Perfect": "48 h", "Ultimate": None, "Egg": "1 min"}
STAGE_RE = r'(Baby I{1,2}|Child|Adult|Perfect|Ultimate|Egg)'
ATTRCODE = {"va": "Vaccine", "da": "Data", "vi": "Virus", "fr": "Free"}
VER = {"evo_v1_nature_spirits.md": (1, "Nature Spirits"), "evo_v2_deep_savers.md": (2, "Deep Savers"),
       "evo_v3_nightmare_soldiers.md": (3, "Nightmare Soldiers"), "evo_v4_wind_guardians.md": (4, "Wind Guardians"),
       "evo_v5_metal_empire.md": (5, "Metal Empire")}

def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower())

KNOWN = set()
for f in glob.glob(os.path.join(HUM, "evo_v*.md")):
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
    if not raw or raw.lower() in ("none", "terminal", "?", "next", "terminal?"): return {}
    if " OR " in raw:
        return {"alternatives": [parse_cond(a) for a in raw.split(" OR ")]}
    p = {}
    cm = re.search(r'(\d+\+?|\d+-\d+)\s*CM', raw); p.update(care_mistakes=cm.group(1)) if cm else None
    ef = re.search(r'(\d+\+?|\d+-\d+)\s*Effort', raw); p.update(effort=ef.group(1)) if ef else None
    wr = re.search(r'battles?\s*(\d+/\d+)', raw, re.I);
    if wr: p["win_ratio"] = wr.group(1); p["battles"] = True
    elif re.search(r'\bbattles?\b', raw, re.I): p["battles"] = True
    # jogress (DNA) — "with X" (named) | "Va+Da" (attr codes) | "WarGreymon + MetalGarurumon" (named)
    if "Jogress" in raw:
        mw = re.search(r'Jogress with ([A-Za-z: ]+)', raw)
        seg = (re.search(r'Jogress\s+([^();]+)', raw).group(1).strip() if re.search(r'Jogress\s+([^();]+)', raw) else "")
        if mw:
            p["jogress_partner"] = mw.group(1).strip()
        elif re.fullmatch(r'(Va|Da|Vi|Fr)(\s*\+\s*(Va|Da|Vi|Fr))*', seg):
            p["jogress_attrs"] = [ATTRCODE[x.lower()] for x in re.findall(r'Va|Da|Vi|Fr', seg)]
        elif "+" in seg:
            p["jogress_partners"] = [s.strip() for s in seg.split("+")]
        else:
            p["jogress_raw"] = seg
    return p

def sprite_index(d):
    idx = {}
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".png"): idx[norm(fn[:-4])] = os.path.relpath(os.path.join(d, fn), CORPUS)
    return idx
SPI = sprite_index(SPR)
def find_sprite(n): return SPI.get(norm(n))

records = {}
def rec(name, stage=None, attr=None):
    r = records.get(norm(name))
    if not r:
        r = records[norm(name)] = {"id": norm(name), "name": name, "stage": stage, "attribute": attr,
            "devices": {"pen20": {"versions": [], "stage_time": STAGE_TIMER.get(stage), "evolves_to": []}},
            "sprite": find_sprite(name), "sources": ["humulos:pen20"]}
    if stage and not r["stage"]:
        r["stage"] = stage; r["devices"]["pen20"]["stage_time"] = STAGE_TIMER.get(stage)
    if attr and not r["attribute"]: r["attribute"] = attr
    return r

for fn in sorted(glob.glob(os.path.join(HUM, "evo_v*.md"))):
    meta = VER.get(os.path.basename(fn))
    if not meta: continue
    vnum, vname = meta
    for line in open(fn):
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line: continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 4: continue
        name, stage, attr, rest = parts[0], parts[1], parts[2], "|".join(parts[3:])
        sm = re.search(STAGE_RE, stage); stage = sm.group(1) if sm else stage
        r = rec(name, stage, attr)
        dev = r["devices"]["pen20"]
        if vnum not in dev["versions"]: dev["versions"].append(vnum)
        rest = re.sub(r'^->\s*', '', rest).strip()
        if rest.lower() in ("(terminal)", "(next)", "(?)", "(terminal?)", "(terminal/special)", ""): continue
        seen = {(e["to"], e["raw"]) for e in dev["evolves_to"]}
        for chunk in rest.split(";"):
            chunk = chunk.strip()
            if not chunk or chunk.startswith("(") and chunk.endswith(")") and "Jogress" not in chunk and norm(chunk) not in KNOWN:
                # bare "(conditions)" with no target name (extractor dropped the target)
                dev.setdefault("_unresolved", []).append(chunk.strip("()"))
                continue
            to, cond = split_target(chunk)
            if not to or (to, cond) in seen: continue
            seen.add((to, cond))
            dev["evolves_to"].append({"to": to, "to_id": norm(to), "raw": cond, "parsed": parse_cond(cond)})
            rec(to)

# spine: wayland pen20 sprites -> records; 20th-addition lines (no version data) flagged
for k, path in SPI.items():
    if k not in records:
        records[k] = {"id": k, "name": os.path.basename(path)[:-4], "stage": None, "attribute": None,
            "devices": {"pen20": {"versions": [], "stage_time": None, "evolves_to": []}},
            "sprite": path, "sources": ["wayland-vpets:pen20"], "addition_pending": True}

no_sprite = sorted(r["name"] for r in records.values() if not r["sprite"])
pending = sorted(r["name"] for r in records.values() if r.get("addition_pending"))
withevo = sum(1 for r in records.values() if r["devices"]["pen20"]["evolves_to"])
out = {"_meta": {"device": "pen20", "count": len(records),
        "source": "humulos /pen20/ per-version (NS/DS/NSo/WG/ME) + wayland sprites/timers",
        "with_evolutions": withevo,
        "complete": "5 CLASSIC versions captured (Nature Spirits/Deep Savers/Nightmare Soldiers/Wind Guardians/Metal Empire). pen20's 20th-anniversary BONUS lines (Guilmon/V-mon/Terriermon/DORUmon/Ryudamon/etc.) NOT yet pulled -> addition_pending. Minor extraction noise: a few branch targets dropped (see device._unresolved), Mugendra=Mugendramon. JOGRESS is the key mechanic (jogress_attrs/jogress_partner/jogress_partners).",
        "addition_pending_count": len(pending), "sprite_gaps": no_sprite},
       "digimon": [records[k] for k in sorted(records)]}
with open(os.path.join(HERE, "pen20.json"), "w") as fh: json.dump(out, fh, indent=1, ensure_ascii=False)
print(f"wrote pen20.json: {len(records)} mons | with evolutions {withevo} | addition_pending {len(pending)} | sprite_gaps {len(no_sprite)}")
