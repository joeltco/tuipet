import gzip, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from tuipet.render import frame_text, PALETTES
from rich.console import Console

here = os.path.dirname(__file__)
data = json.load(gzip.open(os.path.join(here, "..", "src/tuipet/data/sprites.json.gz"), "rt"))
# canonical entry per name = lowest DigimonNum
by = {}
for x in sorted(data, key=lambda d: d["num"]):
    by.setdefault(x["name"], x)
c = Console()
on, off = PALETTES["ink"]
names = sys.argv[1:] or ["Botamon", "Koromon", "Agumon", "Greymon", "WarGreymon"]
for nm in names:
    x = by.get(nm)
    if not x:
        c.print(f"[red]missing {nm}[/]"); continue
    c.rule(f"{nm}  ({x['stage']}, num {x['num']})  {x['w']}x{x['h']}")
    c.print(frame_text(x["frames"][0], on, off))
