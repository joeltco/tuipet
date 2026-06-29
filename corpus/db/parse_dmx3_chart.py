#!/usr/bin/env python3
"""Parse humulos DMX V3 (XE/XF) evolution chart -> evo_v3_edges.json.
Source: curl -s https://humulos.com/digimon/dmx/3/ -A Mozilla/5.0 -o dmx3.html
The chart encodes edges via CSS classes xe_<src>_line -> reqs gifs -> xe_<tgt>_Req_line,
conditions as named gifs (mistakeN, effortN, levelcN, defeatultN, jogresswith, areaN),
and area-gating via enclosing row area=/areamax= attributes. Deterministic (no LLM)."""
import re, json
h=open('dmx3.html').read()

# slug -> display name (from dot-sprite nodes)
slugname={}
for m in re.finditer(r'images/dot/dmx/([a-z0-9_]+)\.gif"[^>]*?title="([^"]+)"', h):
    nm=m.group(2).strip()
    slugname.setdefault(m.group(1), nm)
# fix the egg title oddity
def name(slug): return slugname.get(slug, slug)

def dec_range(d):
    if d=="10": return "10"
    if len(d)==3: return f"{d[0]}-{d[1:]}"      # 810->8-10, 910->9-10
    if len(d)==2: return f"{d[0]}-{d[1]}"        # 03->0-3, 56->5-6
    return d                                      # single digit exact
def decode(gif):
    if gif.startswith("mistake"): return ("care_mistakes", dec_range(gif[7:]))
    if gif.startswith("effort"):  return ("effort", dec_range(gif[6:]))
    if gif.startswith("levelc"):  return ("level", dec_range(gif[6:]))
    if gif.startswith("defeatult"): return ("defeat_stage6", gif[9:])
    if gif=="jogresswith": return ("jogress", True)
    if gif.startswith("area"): return ("area_cleared_as_self", gif[4:])
    if gif=="other": return ("catch_all", True)
    return ("raw_"+gif, True)

# tokenize in document order: row area context, SRC, REQ(gifs), TGT
tok=[]
for m in re.finditer(r'areamax="(\d+|SP|RE)"|(?<!max)\barea="(\d+|SP|RE)"|(xe|xf)_([a-z0-9_]+?)_line"|(xe|xf)_([a-z0-9_]+?)_Req_line|class="reqs_dmx[^"]*">(.*?)</div>', h):
    if m.group(1): tok.append(('AMAX', m.group(1)))
    elif m.group(2): tok.append(('AMIN', m.group(2)))
    elif m.group(4): tok.append(('SRC', m.group(3), m.group(4)))
    elif m.group(6): tok.append(('TGT', m.group(5), m.group(6)))
    else:
        gs=re.findall(r'images/reqs/([a-z0-9_]+)\.gif', m.group(7))
        tok.append(('REQ', gs))

edges=[]
cur_src=None; cur_sub=None; cur_req=None; cur_area=None; area_kind=None
for t in tok:
    if t[0]=='AMIN': cur_area, area_kind = t[1], 'cleared'
    elif t[0]=='AMAX': cur_area, area_kind = t[1], 'not_cleared'
    elif t[0]=='SRC': cur_src, cur_sub = t[2], t[1]
    elif t[0]=='REQ': cur_req=t[1]
    elif t[0]=='TGT':
        sub, tgt = t[1], t[2]
        if cur_src is None: continue
        cond={}
        for g in (cur_req or []):
            k,v=decode(g); cond[k]=v
        if cur_area and area_kind:
            cond[f"area_{area_kind}"]=cur_area
        edges.append({"sub":sub, "src":cur_src, "src_name":name(cur_src),
                      "tgt":tgt, "tgt_name":name(tgt), "cond":cond})
        cur_req=None

# dedupe identical
seen=set(); uniq=[]
for e in edges:
    key=(e['sub'],e['src'],e['tgt'],json.dumps(e['cond'],sort_keys=True))
    if key in seen: continue
    seen.add(key); uniq.append(e)

xe=[e for e in uniq if e['sub']=='xe']; xf=[e for e in uniq if e['sub']=='xf']
print(f"parsed edges: total {len(uniq)} | xe {len(xe)} | xf {len(xf)}")
srcs_xe=sorted({e['src_name'] for e in xe}); srcs_xf=sorted({e['src_name'] for e in xf})
print(f"XE source mons: {len(srcs_xe)} | XF source mons: {len(srcs_xf)}")
print("\nsample XE edges (Gummymon):")
for e in xe[:6]: print("  ",e['src_name'],"->",e['tgt_name'],e['cond'])
json.dump(uniq, open('dmx3_edges.json','w'), ensure_ascii=False, indent=0)
print("\nwrote dmx3_edges.json")
