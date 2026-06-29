# DMX Version 3 (XE/XF) — RESOLVED 2026-06-29
# WebFetch's markdown extractor truncated/self-looped on this dense chart, so V3 was
# instead parsed DETERMINISTICALLY from the raw chart HTML:
#   curl https://humulos.com/digimon/dmx/3/ -> corpus/db/parse_dmx3_chart.py -> evo_v3_edges.json (264 edges)
# The chart encodes edges via CSS classes (xe_<src>_line -> reqs gifs -> xe_<tgt>_Req_line),
# conditions as named gifs (mistakeN/effortN/levelcN/defeatultN/jogresswith/areaN), and area
# gating via row area=/areamax= attributes. evo_v1.md (XA/XB) + evo_v2.md (XC/XD) + evo_v3_kera.md
# came from clean WebFetch markdown. Pure-V3 mon STAGES inferred by propagating along the edge
# graph; ATTRIBUTES are null (the chart has no attribute data — backfill from wikimon/DVPet).
