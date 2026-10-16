"""Stage isolated saves for the VHS demo; run from the repository root."""
import os
from pathlib import Path
import sys

# Refuse to seed the real profile even if invoked without the tape's environment.
save_dir = os.environ.get("TUIPET_SAVE_DIR", "")
if not save_dir or not Path(save_dir).resolve().is_relative_to(Path("/tmp")):
    raise SystemExit("Set TUIPET_SAVE_DIR to an isolated directory under /tmp")
os.environ["TUIPET_NO_SYNC"] = "1"
sys.path.insert(0, "src")
from tuipet import data, persistence
from tuipet.pet import Pet

kind = sys.argv[1] if len(sys.argv) > 1 else "egg"
if kind in ("egg", "godzilla_egg"):
    # argv: egg [egg_type] -- any egg in the bank, seconds from hatching
    p = Pet.new_egg(egg_type=46 if kind == "godzilla_egg" else int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    p.stage_seconds = p.EGG_DURATION - (float(sys.argv[3]) if len(sys.argv) > 3 else 4.0)   # argv[3]: seconds left
elif kind in ("godzilla", "fragment"):
    p = Pet.new_egg(egg_type=46)
    for num in (1623, 1624, 1625, 1628, 1635, 1644):
        p.evolve_to(num)
    p.line_id = "godzilla"
    p.hunger = 3
    p.energy = p.max_energy
    p.gcell = 400
    p.obedience = 100
    p.strength = 4
    p.battles = 20
    p.wins = 18
    p.world_seconds = 9 * 60.0  # game clock: one second is one minute
    if kind == "fragment":
        p.dead = True
        p.gcell_frag_left = True
        p.death_banked = True
elif kind == "mon":
    # trailer: any Godzilla-line form at home, fed and rested, walking its scene
    # (argv: mon <dex> [stage_seconds_left] -- the second arg arms a live evolution)
    dex = int(sys.argv[2])
    p = Pet.new_egg(egg_type=46)
    p._hatch_into_fresh()
    p.evolve_to(dex)
    p.line_id = "godzilla"
    p.hunger, p.strength = 4, 4
    p.energy = p.max_energy
    p.obedience = 100
    p.gcell = 400
    p.world_seconds = 10 * 60.0
    if len(sys.argv) > 3:
        p.stage_seconds = p.STAGE_DURATION.get(p.stage, 0) - float(sys.argv[3])
        p.care_mistakes = 0
        p.stage_battles, p.battle_log = 15, [1] * 15
elif kind == "pet":
    # trailer: ANY species at home, fed and rested (argv: pet <dex>) -- the 0.6.31 montage
    from tuipet import lines
    dex = int(sys.argv[2])
    p = Pet.new_egg(egg_type=0)
    p._hatch_into_fresh()
    p.evolve_to(dex)
    p.line_id = next((lid for lid, ln in lines.load_lines().items() if dex in ln["members"]), p.line_id)
    p.hunger, p.strength = 4, 4
    p.energy = p.max_energy
    p.obedience = 100
    p.world_seconds = 10 * 60.0
    p.adv_progress = 12          # a road with some maps open
elif kind == "rookie":
    _, by = data.load_sprites()
    num = next(n for n, r in sorted(by.items())
               if r["stage"] == "Rookie" and not r.get("_placeholder"))
    p = Pet(num=num, name=by[num]["name"], stage="Rookie", hunger=2)
    p.world_seconds = 9 * 60.0
else:
    raise SystemExit(f"Unknown demo seed: {kind}")
p.bits = 800
for item in ("fish", "ball"):
    p.add_item(item)
persistence.set_auto_update(False)
persistence.set_account("demo", "demo")   # skip the first-launch account screen
from tuipet import update
_s = persistence.load_settings()
_s["seen_version"] = update.current_version()   # no stale WHAT'S NEW banner on camera
persistence.save_settings(_s)
persistence.save(p)
print("seeded", kind, p.name, p.stage)
