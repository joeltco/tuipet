#!/usr/bin/env python3
"""Build corpus/db/pen20.json from humulos' authoritative inline `result` database.

Source: corpus/canon/humulos/pen20/result.json (via extract_humulos_result.py from the
device page HTML). Complete + clean: every mon's stage, attribute, evo1-6 + exact req text,
parents, version (egg1/egg2 family names), jogress, sleep, strength. Supersedes the earlier
per-version/bonus WebFetch .md files (kept as backup in canon/humulos/pen20/evo_*.md).
Sprites: wayland-vpets assets/pen20. Stage timers: wayland docs (pen20 column).
"""
import os, re, json, difflib

HERE = os.path.dirname(os.path.abspath(__file__)); CORPUS = os.path.dirname(HERE)
RESULT = os.path.join(CORPUS, "canon/humulos/pen20/result.json")
SPR = os.path.join(CORPUS, "fan/wayland-vpets/assets/pen20")
STAGE_TIMER = {"Baby I": "10 min", "Baby II": "12 h", "Child": "24 h",
               "Adult": "40 h", "Perfect": "48 h", "Ultimate": None, "Super Ultimate": None}

def norm(s): return re.sub(r'[^a-z0-9]', '', (s or "").lower())
def clean_name(n):  # strip trailing version tag like "Angewomon (NSp)"
    return re.sub(r'\s*\([A-Za-z]{2,4}\)\s*$', '', n or "").strip()

def parse_req(raw):
    if not raw or raw.strip() in ("", "-"): return {}
    p = {}
    cm = re.search(r'(\d+\+?|\d+-\d+)\s*Care Mistakes?', raw); p.update(care_mistakes=cm.group(1)) if cm else None
    ef = re.search(r'(\d+\+?|\d+-\d+)\s*Effort', raw); p.update(effort=ef.group(1)) if ef else None
    if re.search(r'\bbattles?\b', raw, re.I): p["battles"] = True
    wr = re.search(r'(\d+/\d+)', raw); p.update(win_ratio=wr.group(1)) if wr else None
    jp = re.search(r'Jogress(?: with)?\s+([A-Za-z:][\w :]+)', raw, re.I)
    if jp: p["jogress_partner"] = jp.group(1).strip()
    elif re.search(r'jogress', raw, re.I): p["jogress"] = True
    return p

# sprite index
SPI = {}
if os.path.isdir(SPR):
    for fn in os.listdir(SPR):
        if fn.endswith(".png"): SPI[norm(fn[:-4])] = os.path.relpath(os.path.join(SPR, fn), CORPUS)
_SPI_KEYS = list(SPI)
def find_sprite(name, slug):
    hit = SPI.get(norm(name)) or SPI.get(norm(slug))
    if hit: return hit
    # fuzzy fallback for romanization variants (Guilmon->Guimon, Mugendramon->Mugendra, etc.)
    m = difflib.get_close_matches(norm(name), _SPI_KEYS, n=1, cutoff=0.86)
    return SPI[m[0]] if m else None

data = [d for d in json.load(open(RESULT)) if d.get("name") and d.get("evoStage")]
by_slug = {d["url"]: d for d in data if d.get("url")}

records = {}
for d in data:
    name = d["name"]; rid = norm(name); stage = d.get("evoStage")
    versions = []
    for vk in ("egg1", "egg2"):
        if d.get(vk) and d[vk] not in versions: versions.append(d[vk])
    evos = []
    for i in range(1, 7):
        ev = d.get(f"evo{i}")
        if not ev or ev in ("blank", "rest"): continue
        tname = clean_name(d.get(f"evo{i}_name") or by_slug.get(ev, {}).get("name") or ev)
        raw = (d.get(f"evo{i}_req") or "").strip()
        e = {"to": tname, "to_id": norm(tname), "via_slug": ev, "raw": raw, "parsed": parse_req(raw)}
        vtag = re.search(r'\(([A-Za-z]{2,4})\)\s*$', d.get(f"evo{i}_name") or "")
        if vtag: e["version_tag"] = vtag.group(1)
        evos.append(e)
    records[rid] = {
        "id": rid, "name": name, "stage": stage, "level": d.get("level"),
        "attribute": d.get("attribute") if d.get("attribute") not in ("invalid", "") else None,
        "alt_attribute": d.get("alt_attribute") or None,
        "devices": {"pen20": {"versions": versions, "stage_time": STAGE_TIMER.get(stage),
                              "evolves_to": evos}},
        "sprite": find_sprite(name, d.get("url")),
        "jogress_capable": d.get("jogress") == "Yes",
        "sleep": d.get("sleep") or None, "strength": d.get("strength_value") or None,
        "sources": ["humulos:pen20:result"]}

no_sprite = sorted(r["name"] for r in records.values() if not r["sprite"])
withevo = sum(1 for r in records.values() if r["devices"]["pen20"]["evolves_to"])
out = {"_meta": {"device": "pen20", "count": len(records), "with_evolutions": withevo,
        "source": "humulos inline `result` DB (canon/humulos/pen20/result.json) — authoritative + complete",
        "complete": "ALL pen20 mons (5 classic versions + 20th bonus lines) from the page's own structured data: exact evo conditions (evo*_req), stages, attributes, versions (egg1/egg2), jogress, sleep times, strength. Supersedes the earlier WebFetch .md extraction.",
        "version_tags_note": "evolves_to[].version_tag = the version that branch belongs to (NSp/DSa/NSo/WGu/MEm/VBu/etc); evo conditions can differ per version.",
        "sprite_gaps": no_sprite},
       "digimon": [records[k] for k in sorted(records)]}
with open(os.path.join(HERE, "pen20.json"), "w") as fh: json.dump(out, fh, indent=1, ensure_ascii=False)
print(f"wrote pen20.json: {len(records)} mons | with evolutions {withevo} | sprite_gaps {len(no_sprite)}")
if no_sprite: print("  no sprite:", ", ".join(no_sprite[:20]), "..." if len(no_sprite) > 20 else "")
