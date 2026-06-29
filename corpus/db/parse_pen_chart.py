#!/usr/bin/env python3
"""Parse a humulos Pendulum chart (pen / pen20) HTML into evolution edges.

Source: curl -s https://humulos.com/digimon/<dev>/ -A Mozilla/5.0 -o <dev>.html
The chart is a nested DOM TREE: each evolution node is <div class="digimon <attr><ver>">
(e.g. vaccine1 = Vaccine, Ver.1/Nature Spirits) containing a dot sprite + onClick id; the
<div class="reqs ..."> that precedes a node inside its "row" holds the conditions (gifs:
mistakeN/effortN/battles/battlewith/jogress*) to evolve INTO it from its parent node (the
nearest ancestor "digimon" div). Deterministic — no LLM.

Usage: python3 parse_pen_chart.py <dev> <html_path> <out_json>
"""
import sys, re, json
from html.parser import HTMLParser

ATTR = {"vaccine": "Vaccine", "data": "Data", "virus": "Virus", "free": "Free"}
VERSION = {"1": "Nature Spirits", "2": "Deep Savers", "3": "Nightmare Soldiers",
           "4": "Wind Guardians", "5": "Metal Empire"}

class El:
    __slots__ = ("tag", "cls", "id", "parent", "children", "imgs", "onclick")
    def __init__(self, tag, cls, _id, parent):
        self.tag, self.cls, self.id, self.parent = tag, cls, _id, parent
        self.children, self.imgs, self.onclick = [], [], None

class Tree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = El("root", "", None, None); self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div":
            el = El(tag, a.get("class", ""), a.get("id"), self.stack[-1])
            self.stack[-1].children.append(el); self.stack.append(el)
        elif tag == "img":
            self.stack[-1].imgs.append(a)
        # onClick can be on div or inner tag; capture nearest div
        if a.get("onclick"):
            self.stack[-1].onclick = a["onclick"]
    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            self.stack[-1].imgs.append(dict(attrs))
    def handle_endtag(self, tag):
        if tag == "div" and len(self.stack) > 1:
            self.stack.pop()

def reqs_gifs(el):
    """collect req gif names under a reqs element"""
    out = []
    def walk(e):
        for im in e.imgs:
            m = re.search(r'images/reqs/([a-z0-9_]+)\.gif', im.get("src", "") + im.get("data-src", ""))
            if m: out.append(m.group(1))
        for c in e.children: walk(c)
    walk(el)
    return out

def dec(d):
    if d == "10": return "10"
    if len(d) == 3: return f"{d[0]}-{d[1:]}"
    if len(d) == 2: return f"{d[0]}-{d[1]}"
    return d
def decode_cond(gifs):
    c = {}
    for g in gifs:
        if g.startswith("mistake"): c["care_mistakes"] = dec(g[7:])
        elif g.startswith("effort"): c["effort"] = dec(g[6:])
        elif g == "battles": c["battles"] = True
        elif g == "battlewith": c["battle_with"] = True
        elif g.startswith("jogress"): c["jogress"] = g[7:] or True
        else: c.setdefault("raw_gifs", []).append(g)
    return c

def node_info(dev, el):
    """if el is a digimon node, return (slug, name, attr, version)"""
    if "digimon" not in el.cls: return None
    slug = nm = None
    def find(e):
        nonlocal slug, nm
        for im in e.imgs:
            src = im.get("data-src", "") + im.get("src", "")
            m = re.search(rf'images/dot/{dev}/([a-z0-9_]+)\.gif', src)
            if m and not slug:
                slug = m.group(1); nm = im.get("title") or im.get("alt")
        for c in e.children: find(c)
    find(el)
    if not slug: return None
    attr = ver = None
    for tok in el.cls.split():
        m = re.match(r'(vaccine|data|virus|free)(\d?)', tok)
        if m:
            attr = ATTR[m.group(1)]
            if m.group(2): ver = m.group(2)
    return slug, (nm or slug).strip(), attr, ver

def nearest_digimon_ancestor(dev, el):
    p = el.parent
    while p is not None:
        if node_info(dev, p): return p
        p = p.parent
    return None

def main():
    dev, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    t = Tree(); t.feed(open(path, encoding="utf-8", errors="replace").read())
    # collect all digimon nodes
    nodes = []
    def collect(e):
        if node_info(dev, e): nodes.append(e)
        for c in e.children: collect(c)
    collect(t.root)

    edges = []
    nodeset = {}
    for el in nodes:
        slug, name, attr, ver = node_info(dev, el)
        nodeset.setdefault(slug, {"slug": slug, "name": name, "attr": attr, "versions": set()})
        if ver: nodeset[slug]["versions"].add(ver)
        # find reqs within this node's enclosing "row"
        row = el.parent
        while row is not None and "row" not in row.cls and "column" not in row.cls:
            row = row.parent
        gifs = []
        if row:
            for c in row.children:
                if "reqs" in c.cls: gifs += reqs_gifs(c)
        parent = nearest_digimon_ancestor(dev, el)
        if parent:
            ps = node_info(dev, parent)
            edges.append({"src": ps[0], "src_name": ps[1], "tgt": slug, "tgt_name": name,
                          "cond": decode_cond(gifs)})
    # dedupe
    seen = set(); uniq = []
    for e in edges:
        k = (e["src"], e["tgt"], json.dumps(e["cond"], sort_keys=True))
        if k in seen: continue
        seen.add(k); uniq.append(e)
    for n in nodeset.values(): n["versions"] = sorted(n["versions"])
    json.dump({"nodes": list(nodeset.values()), "edges": uniq}, open(out, "w"), ensure_ascii=False, indent=0)
    print(f"{dev}: nodes {len(nodeset)} | edges {len(uniq)}")
    roots = [n for n in nodeset if not any(e["tgt"] == n for e in uniq)]
    print(f"  roots (no incoming): {len(roots)} -> {[nodeset[r]['name'] for r in roots][:10]}")
    print("  sample edges:")
    for e in uniq[:6]: print("   ", e["src_name"], "->", e["tgt_name"], e["cond"])

if __name__ == "__main__":
    main()
