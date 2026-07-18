"""Seed the demo save for tools/demo.tape (vhs).  Usage: demo_seed.py egg|rookie"""
import sys
sys.path.insert(0, "src")
from tuipet import data, persistence
from tuipet.pet import Pet

kind = sys.argv[1] if len(sys.argv) > 1 else "egg"
if kind == "egg":
    p = Pet.new_egg(egg_type=0)
    p.stage_seconds = p.EGG_DURATION - 8.0    # hatches ~8s after the title
else:
    _, by = data.load_sprites()
    num = next(n for n, r in sorted(by.items())
               if r["stage"] == "Rookie" and not r.get("_placeholder"))
    p = Pet(num=num, name=by[num]["name"], stage="Rookie", hunger=2)
    p.world_seconds = 9 * 3600.0              # mid-morning light
p.bits = 800
for k in ("fish", "ball"):        # the TUIPET catalog (2026-07-18)
    p.add_item(k)
persistence.set_auto_update(False)   # never let the launch updater run mid-recording
persistence.save(p)
print("seeded", kind, p.name, p.stage)
