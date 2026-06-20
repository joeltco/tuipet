import gzip, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from tuipet.render import frame_text, PALETTES
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
here = os.path.dirname(__file__)
data = json.load(gzip.open(os.path.join(here, "..", "src/tuipet/data/sprites.json.gz"), "rt"))
by = {}
for x in sorted(data, key=lambda d: d["num"]): by.setdefault(x["name"], x)
c = Console(width=120)
x = by[sys.argv[1] if len(sys.argv) > 1 else "Agumon"]
on, off = PALETTES["ink"]
panels = [Panel(frame_text(f, on, off), title=str(i), padding=0) for i, f in enumerate(x["frames"])]
c.print(f"{x['name']} all 11 frames:")
c.print(Columns(panels[:6], padding=0))
c.print(Columns(panels[6:], padding=0))
