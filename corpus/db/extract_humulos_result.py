#!/usr/bin/env python3
"""Extract humulos' inline `result = [...]` evolution database from a device page HTML.

EVERY humulos device page embeds a complete `result = [...]` JSON array (one object per
Digimon) with: name, level, evoStage, attribute, alt_attribute, egg1/egg2 (version names),
version (codes), url (slug), evo1-6 + evo*_name + evo*_req (exact condition text), prevo1-7,
jogress, battle, sleep, strength_value, shakes, note. This is THE clean authoritative source
(beats WebFetch markdown + chart parsing). Reusable for dm20/dmx/pen/dm too.

Usage: curl -s https://humulos.com/digimon/<dev>/ -A Mozilla/5.0 -o <dev>.html
       python3 extract_humulos_result.py <dev>.html <out.json>
"""
import sys, json
def extract(html_path, out):
    h = open(html_path, encoding="utf-8", errors="replace").read()
    start = h.index("[", h.index("result = ["))
    depth = 0; instr = esc = False; end = None
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
    json.dump(data, open(out, "w"), ensure_ascii=False)
    print(f"{html_path}: extracted {len(data)} entries -> {out}")
    return data
if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
