#!/usr/bin/env python3
"""Generic builder: corpus/canon/humulos/<dev>/records.json -> corpus/db/<dev>.json.

Consumes the normalized records (from parse_humulos.py — inline-result for pen20, detail
cards for dm/dm20/dmx/pen). Adds: structured condition parse (every device's vocabulary),
correct per-device real-time stage timers (wayland evol-dm.md), wayland sprite refs (fuzzy
fallback). For dmx, merges the V3 (XE/XF) chart edges (evo_v3_edges.json) that have no cards.

Usage: python3 build_device.py <dev>
"""
import os, re, json, difflib, sys

HERE = os.path.dirname(os.path.abspath(__file__)); CORPUS = os.path.dirname(HERE)

# correct real-time stage timers per device (wayland docs/fragments/evol-dm.md)
TIMERS = {
 "dm":    {"Baby I": "10 min", "Baby II": "6 h",  "Child": "24 h", "Adult": "36 h", "Perfect": "48 h"},
 "dm20":  {"Baby I": "10 min", "Baby II": "6 h",  "Child": "24 h", "Adult": "36 h", "Perfect": "48 h"},
 "dmx":   {"Baby I": "10 min", "Baby II": "12 h", "Child": "24 h", "Adult": "32 h", "Perfect": "40 h"},
 "pen":   {"Baby I": "1 h",    "Baby II": "16 h", "Child": "20 h", "Adult": "60 h", "Perfect": "68 h"},
 "pen20": {"Baby I": "10 min", "Baby II": "12 h", "Child": "24 h", "Adult": "40 h", "Perfect": "48 h"},
}
ATTRCODE = {"va": "Vaccine", "da": "Data", "vi": "Virus", "fr": "Free"}

def norm(s): return re.sub(r'[^a-z0-9]', '', (s or "").lower())
def clean_name(n): return re.sub(r'\s*\([A-Za-z]{2,4}\)\s*$', '', n or "").strip()

def parse_req(raw):
    """Unified condition parser across all five devices. `raw` always kept verbatim."""
    if not raw or raw.strip() in ("", "-"): return {}
    if re.search(r'\bOR\b', raw):
        return {"alternatives": [parse_req(a) for a in re.split(r'\s+OR\s+', raw)]}
    p = {}
    def g(pat):
        m = re.search(pat, raw, re.I); return m.group(1).strip() if m else None
    for key, pat in (("care_mistakes", r'(\d+\+?|\d+-\d+)\s*Care Mistakes'),
                     ("training", r'(\d+\+?|\d+-\d+)\s*Training'),
                     ("overfeed", r'(\d+\+?|\d+-\d+)\s*Overfeed'),
                     ("effort", r'(\d+\+?|\d+-\d+)\s*Effort'),
                     ("weight", r'(\d+\+?|\d+-\d+)\s*Weight'),
                     ("level", r'Level\s*(\d+\+?|\d+-\d+)'),
                     ("defeat_stage6", r'Defeat\s*(\d+\+?|\d+-\d+)\s*Stage VI'),
                     ("victories", r'(\d+(?:-\d+)?)\s*Victor'),
                     ("win_ratio", r'(\d+/\d+)'),
                     ("battles_n", r'(\d+)\s*Battles'),
                     ("time_min", r'Wait\s*(\d+)\s*Minutes')):
        v = g(pat)
        if v is not None: p[key] = int(v) if key in ("battles_n", "time_min") else v
    areas_c = re.findall(r'Area\s*(\d+|SP)\b(?!\s*[Nn]ot)', raw)
    if areas_c: p["area_cleared"] = areas_c
    areas_nc = re.findall(r'Area\s*(\d+|SP)\s*[Nn]ot cleared', raw)
    if areas_nc: p["area_not_cleared"] = areas_nc
    ve = g(r'Version\s*(\d+)\s*Egg')
    if ve: p["version_egg"] = int(ve)
    se = g(r'(\w+)\s*Egg\b')
    if se and not ve: p["special_egg"] = se
    tag = g(r'Tag Battle.*?with\s+(.+?)$')
    if tag: p["tag_battle_with"] = clean_name(tag)
    if "Jogress" in raw or "jogress" in raw:
        mw = re.search(r'Jogress with ([A-Za-z][\w :+]+)', raw)
        seg = re.search(r'Jogress\s+([^();]+)', raw)
        seg = seg.group(1).strip() if seg else ""
        if mw: p["jogress_partner"] = mw.group(1).strip()
        elif re.fullmatch(r'(Va|Da|Vi|Fr)(\s*\+\s*(Va|Da|Vi|Fr))*', seg):
            p["jogress_attrs"] = [ATTRCODE[x.lower()] for x in re.findall(r'Va|Da|Vi|Fr', seg)]
        else: p["jogress"] = True
    elif re.search(r'\d+\s*Battles|\bbattles\b', raw, re.I): p["battles"] = True
    return p

# ---- attribute backfill from DVPet (canonical per-mon property; needs JP->EN romanization) ----
import csv
_J2E = {"tailmon": "gatomon", "vamdemon": "myotismon", "omegamon": "omnimon", "dukemon": "gallantmon",
        "hououmon": "phoenixmon", "holydramon": "magnadramon", "ofanimon": "ophanimon",
        "anomalocarimon": "scorpiomon", "gaioumon": "gaiomon", "mugendramon": "machinedramon",
        "pinochimon": "puppetmon", "omegashoutmon": "omnishoutmon", "growmon": "growlmon",
        "megalogrowmon": "wargrowmon", "lordknightmon": "crusadermon", "vdramon": "veedramon",
        "doruguremon": "dorugreymon", "shakomon": "syakomon", "siesamon": "seasarmon",
        "alphamonouryuken": "alphamono",
        # full-name dub/mode mappings for the wayland-absent jogress-finals/Royal-Knights/Demon-Lords
        "beelzebumon": "beelzemon", "belialvamdemon": "malomyotismon", "craniummon": "craniumon",
        "murmukusmon": "murmuxmon", "rusttyranomon": "rusttyrannomon", "ulforcevdramon": "ulforceveedramon",
        "belphemonragemode": "belphemon", "lucemonfalldownmode": "lucemonfm",
        "ofanimonfalldownmode": "ophanimonfm", "imperialdramonpaladinmode": "imperialdramonpm",
        "omegamonalters": "omnimonalters", "karatukinumemon": "shellnumemon"}
_JUNK = {"blank", "rest", "evolution failure"}
# canon attributes where DVPet can't disambiguate by name (Virtue=Vaccine / Vice=Virus)
_ATTR_OVERRIDE = {"cherubimonvirtuex": "Vaccine", "cherubimonvicex": "Virus"}
def _dvpet_candidates(name):
    """yield DVPet norm-name keys to try for a humulos name (romanization + X-form)."""
    b = norm(name).replace("virtue", "v").replace("vice", "")
    yield b
    yield _J2E.get(b, b)
    m = re.match(r'(.*?)x$', b)            # X-form: romanize base, re-add x
    if m:
        mb = _J2E.get(m.group(1), m.group(1))
        yield mb + "x"; yield mb

def _dvpet_attr_index():
    dv = {}
    for r in csv.reader(open(os.path.join(CORPUS, "..", "raw_model", "digimon.csv"))):
        if len(r) > 7 and r[2]:
            dv[norm(r[2])] = r[7]
    return dv
def dvpet_attribute(name, dv):
    if norm(name) in _ATTR_OVERRIDE: return _ATTR_OVERRIDE[norm(name)]
    for key in _dvpet_candidates(name):
        if dv.get(key) not in (None, "None", ""): return dv[key]
    return None

# DVPet sprite (16x16 1-bit frames) -> rendered PNG, for mons wayland lacks
_DVPET_SPR = None
def _dvpet_sprite_index():
    global _DVPET_SPR
    if _DVPET_SPR is None:
        import gzip
        _DVPET_SPR = {}
        for rec in json.load(gzip.open(os.path.join(CORPUS, "..", "src/tuipet/data/sprites.json.gz"), "rt")):
            fr = next((f for f in rec.get("frames", []) if f), None)
            if rec.get("name") and fr:
                _DVPET_SPR.setdefault(norm(rec["name"]), fr)
    return _DVPET_SPR
def dvpet_render(name, dev):
    spi = _dvpet_sprite_index()
    fr = next((spi[k] for k in _dvpet_candidates(name) if k in spi), None)
    if not fr: return None
    try:
        from PIL import Image
    except ImportError:
        return None
    h, w = len(fr), len(fr[0]); S = 4
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if fr[y][x] == "1":
                for dy in range(S):
                    for dx in range(S): px[x * S + dx, y * S + dy] = (40, 40, 40, 255)
    outdir = os.path.join(CORPUS, "sprites_dvpet", dev); os.makedirs(outdir, exist_ok=True)
    fn = os.path.join(outdir, norm(name) + ".png"); img.save(fn)
    return os.path.relpath(fn, CORPUS)

def sprite_index(dev):
    d = os.path.join(CORPUS, f"fan/wayland-vpets/assets/{dev}")
    idx = {}
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".png"): idx[norm(fn[:-4])] = os.path.relpath(os.path.join(d, fn), CORPUS)
    return idx

def build(dev):
    recs = json.load(open(os.path.join(CORPUS, f"canon/humulos/{dev}/records.json")))
    SPI = sprite_index(dev); SK = list(SPI)
    timers = TIMERS[dev]
    def sprite(name, slug):
        h = SPI.get(norm(name)) or SPI.get(norm(slug))
        if h: return h, "wayland"
        m = difflib.get_close_matches(norm(name), SK, n=1, cutoff=0.86)
        if m: return SPI[m[0]], "wayland"
        dp = dvpet_render(name, dev)        # wayland-absent (jogress-finals/Royal Knights/etc) -> DVPet
        if dp: return dp, "dvpet"
        return None, None

    out = {}
    for r in recs:
        rid = norm(r["name"]); stage = r.get("stage")
        evos = []
        for e in r.get("evos", []):
            tn = clean_name(e.get("to_name") or e.get("to_slug"))
            raw = (e.get("req") or "").strip()
            ev = {"to": tn, "to_id": norm(tn), "raw": raw, "parsed": parse_req(raw)}
            vt = re.search(r'\(([A-Za-z]{2,4})\)\s*$', e.get("to_name") or "")
            if vt: ev["version_tag"] = vt.group(1)
            evos.append(ev)
        spath, ssrc = sprite(r["name"], r.get("url"))
        rec = {"id": rid, "name": r["name"], "stage": stage, "level": r.get("level"),
               "attribute": r.get("attribute"), "alt_attribute": r.get("alt_attribute"),
               "devices": {dev: {"versions": ([r["version"]] if r.get("version") else []),
                                 "stage_time": timers.get(stage), "evolves_to": evos}},
               "sprite": spath, "sprite_source": ssrc,
               "sleep": r.get("sleep"), "power": r.get("power"),
               "sources": [f"humulos:{dev}"]}
        if r.get("jogress_capable"): rec["jogress_capable"] = True
        out[rid] = rec

    # dmx: merge V3 (XE/XF) chart edges for mons with no card
    if dev == "dmx":
        v3 = os.path.join(CORPUS, "canon/humulos/dmx/evo_v3_edges.json")
        if os.path.exists(v3):
            for e in json.load(open(v3)):
                sid, tid = norm(e["src_name"]), norm(e["tgt_name"])
                for nm, nid in ((e["src_name"], sid), (e["tgt_name"], tid)):
                    if nid not in out:
                        _sp, _ss = sprite(nm, None)
                        out[nid] = {"id": nid, "name": nm, "stage": None, "level": None,
                                    "attribute": None, "alt_attribute": None,
                                    "devices": {"dmx": {"versions": ["XE/XF"], "stage_time": None, "evolves_to": []}},
                                    "sprite": _sp, "sprite_source": _ss, "sleep": None, "power": None,
                                    "sources": ["humulos:dmx:chart"], "attribute_pending": True}
                src = out[sid]
                raw = ", ".join(f"{k}={v}" for k, v in e["cond"].items())
                if not any(x["to_id"] == tid for x in src["devices"]["dmx"]["evolves_to"]):
                    src["devices"]["dmx"]["evolves_to"].append(
                        {"to": e["tgt_name"], "to_id": tid, "raw": raw, "parsed": e["cond"], "sub_version": e["sub"].upper()})

    # drop junk placeholder entries (chart artifacts: blank / rest / "Evolution Failure")
    for k in [k for k, r in out.items() if r["name"].lower() in _JUNK]:
        del out[k]

    # backfill null attributes from DVPet (romanization-aware); babies (DVPet None) -> Free
    if any(not r["attribute"] for r in out.values()):
        dv = _dvpet_attr_index()
        for r in out.values():
            if r["attribute"]: continue
            a = dvpet_attribute(r["name"], dv)
            if a:
                r["attribute"] = a; r["attribute_source"] = "dvpet"
            elif r["stage"] in ("Baby I", "Baby II") or norm(r["name"]) in dv:
                r["attribute"] = "Free"; r["attribute_source"] = "dvpet:baby/free"
            r.pop("attribute_pending", None)

    no_sprite = sorted(r["name"] for r in out.values() if not r["sprite"])
    no_attr = sorted(r["name"] for r in out.values() if not r["attribute"])
    withevo = sum(1 for r in out.values() if r["devices"][dev]["evolves_to"])
    meta = {"device": dev, "count": len(out), "with_evolutions": withevo,
            "source": f"humulos {dev} (parse_humulos.py: {'inline result' if dev=='pen20' else 'detail cards'}" + (" + V3 chart edges" if dev == "dmx" else "") + ")",
            "stage_timers": timers, "sprite_gaps": no_sprite, "attribute_gaps": no_attr,
            "note": "exact evo conditions from humulos (raw + parsed). real-time stage timers per device. sleep/power included."}
    res = {"_meta": meta, "digimon": [out[k] for k in sorted(out)]}
    json.dump(res, open(os.path.join(HERE, f"{dev}.json"), "w"), indent=1, ensure_ascii=False)
    print(f"{dev}.json: {len(out)} mons | {withevo} w/ evolutions | sprites {len(out)-len(no_sprite)}/{len(out)} | attr {len(out)-len(no_attr)}/{len(out)}")

if __name__ == "__main__":
    build(sys.argv[1])
