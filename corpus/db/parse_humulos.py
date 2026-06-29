#!/usr/bin/env python3
"""Parse a humulos device page into a NORMALIZED Digimon record list.

Two source forms, auto-detected:
  (A) inline `result = [...]` JSON array (pen20)  -> richest (version/jogress/strength)
  (B) pre-rendered detail cards <div id="X_card" class="details ATTR"> (dm/dm20/dmx/pen)
Both carry: name, slug(url), attribute, stage, evolves-to (target slug+name+req text),
evolves-from, power, sleep. Deterministic, no LLM.

Output record: {url,name,dub,attribute,level,stage,power,sleep,version,
                evos:[{to_slug,to_name,req}], prevos:[{slug,name,req}]}

Usage: python3 parse_humulos.py <out.json> <html1> [html2 ...]   (multiple = merge, e.g. dmx)
"""
import sys, re, json, html as _html

STAGE_RE = re.compile(r'Stage\s+([IVX]+)\+?\s*\(([^)]+)\)')

def is_selector(slug, name):
    """version/egg picker cards, not real Digimon (e.g. digitama_1, 'Digital Monster Ver.3')."""
    return (slug or "").startswith("digitama_") or (name or "").startswith("Digital Monster Ver")

def from_inline_result(h):
    i = h.find("result = [")
    if i < 0: return None
    start = h.index("[", i); depth = 0; instr = esc = False; end = None
    for j in range(start, len(h)):
        c = h[j]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        elif c == '"': instr = True
        elif c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = j + 1; break
    data = json.loads(h[start:end])
    out = []
    for d in data:
        if not d.get("name") or is_selector(d.get("url"), d.get("name")): continue
        evos = [{"to_slug": d.get(f"evo{i}"), "to_name": d.get(f"evo{i}_name"), "req": (d.get(f"evo{i}_req") or "").strip()}
                for i in range(1, 7) if d.get(f"evo{i}") and d.get(f"evo{i}") not in ("blank", "rest")]
        prevos = [{"slug": d.get(f"prevo{i}"), "name": d.get(f"prevo{i}_name"), "req": (d.get(f"prevo{i}_req") or "").strip()}
                  for i in range(1, 8) if d.get(f"prevo{i}")]
        ver = " ".join(x for x in (d.get("egg1"), d.get("egg2")) if x) or None
        out.append({"url": d.get("url"), "name": d["name"], "dub": d.get("dub"),
                    "attribute": d.get("attribute") if d.get("attribute") not in ("invalid", "") else None,
                    "alt_attribute": d.get("alt_attribute") or None,
                    "level": d.get("level"), "stage": d.get("evoStage"),
                    "power": d.get("strength_value") or None, "sleep": d.get("sleep") or None,
                    "jogress_capable": d.get("jogress") == "Yes", "version": ver,
                    "evos": evos, "prevos": prevos})
    return out

CARD_RE = re.compile(r'class="details(?:New)?\s+([A-Za-z ]*?)"\s+id="([a-z0-9_]+)_card"(.*?)(?=class="details(?:New)?\s|<div id="shade"|</body>)', re.S)
def _section(card, start_marker, end_marker):
    a = card.find(start_marker)
    if a < 0: return ""
    b = card.find(end_marker, a) if end_marker else len(card)
    return card[a:(b if b > 0 else len(card))]
def _links(seg):
    """Every clicker (slug+name), each with its OPTIONAL following deets (some evos have none)."""
    clickers = list(re.finditer(r'id="([a-z0-9_]+)_clicker"[^>]*>.*?<h3 class="names">\s*([^<]+?)\s*</h3>', seg, re.S))
    out = []
    for i, m in enumerate(clickers):
        span_end = clickers[i + 1].start() if i + 1 < len(clickers) else len(seg)
        dm = re.search(r'<p class="deets">([^<]*)</p>', seg[m.end():span_end])
        req = _html.unescape(dm.group(1)).strip() if dm else ""
        out.append((m.group(1), _html.unescape(m.group(2)).strip(), req))
    return out

def from_cards(h):
    out = []
    for m in CARD_RE.finditer(h):
        attr, slug, body = m.group(1).strip() or None, m.group(2), m.group(3)
        nm0 = re.search(r'<p class="sub">([^<]+)</p>', body)
        if is_selector(slug, nm0.group(1).strip() if nm0 else ""): continue
        nm = re.search(r'<p class="sub">([^<]+)</p>', body)
        dub = re.search(r'<p class="dub">([^<]*)</p>', body)
        st = STAGE_RE.search(body)
        bare_stage = None
        if not st:  # original dm/pen cards show a bare <div>Adult</div> (no "Stage IV" level)
            bs = re.search(r'<div>\s*(Baby I{1,2}|Child|Adult|Perfect|Ultimate|Super Ultimate|Hyper Ultimate)\s*</div>', body)
            bare_stage = bs.group(1) if bs else None
        power = re.search(r'Power:\s*([0-9]+)', body)
        sleep = re.search(r'Sleep Time:\s*([^<]+?)\s*</div>', body)
        prevo_seg = _section(body, "Evolves From", "Evolves To")
        evo_seg = _section(body, "Evolves To", '<div class="bj"')
        out.append({"url": slug, "name": (nm.group(1).strip() if nm else slug),
                    "dub": (dub.group(1).strip() if dub else None), "attribute": attr,
                    "level": (st.group(1) if st else None), "stage": (st.group(2).strip() if st else bare_stage),
                    "power": (power.group(1) if power else None),
                    "sleep": (sleep.group(1).strip() if sleep else None), "version": None,
                    "evos": [{"to_slug": s, "to_name": n, "req": r} for s, n, r in _links(evo_seg)],
                    "prevos": [{"slug": s, "name": n, "req": r} for s, n, r in _links(prevo_seg)]})
    return out

def parse_page(path):
    h = open(path, encoding="utf-8", errors="replace").read()
    return from_inline_result(h) or from_cards(h)

def main():
    out, htmls = sys.argv[1], sys.argv[2:]
    merged = {}
    for hp in htmls:
        for rec in parse_page(hp):
            key = rec["url"] or rec["name"]
            if key in merged:  # merge: union evos/prevos (multi-page devices like dmx)
                ex = merged[key]
                seen = {(e["to_slug"], e["req"]) for e in ex["evos"]}
                for e in rec["evos"]:
                    if (e["to_slug"], e["req"]) not in seen: ex["evos"].append(e)
            else:
                merged[key] = rec
    data = list(merged.values())
    json.dump(data, open(out, "w"), ensure_ascii=False)
    withevo = sum(1 for d in data if d["evos"])
    print(f"{[h.split('/')[-1] for h in htmls]} -> {out}: {len(data)} mons, {withevo} w/ evolutions")

if __name__ == "__main__":
    main()
