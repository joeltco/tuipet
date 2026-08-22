"""Stage a save for a promo recording (tools/promo/*.tape).

Usage: seed.py <beat>

Recording has to be DETERMINISTIC and it has to be FLATTERING, and those pull
against each other.  The sim drifts on load -- persistence stamps _saved_at and
applies the elapsed decay -- so a pet staged minutes before the take is already
hungry, pooped and refusing by the time the camera rolls.  Every beat here is
therefore seeded in the same shell command as vhs, seconds before it records.

Flattering is the second half: `demo_seed.py egg` hatches its pet STARVING
(nothing sets hunger on the egg path), and "starving" in bold under a caption
reading "it's alive" is not the advert.  These seeds hatch a fed, clean, happy
creature and let the beats do the talking.
"""
import sys

sys.path.insert(0, "src")
from tuipet import data, persistence          # noqa: E402
from tuipet.pet import Pet                    # noqa: E402

beat = sys.argv[1] if len(sys.argv) > 1 else "egg"


def _rookie():
    _, by = data.load_sprites()
    num = next(n for n, r in sorted(by.items())
               if r["stage"] == "Rookie" and not r.get("_placeholder"))
    return Pet(num=num, name=by[num]["name"], stage="Rookie")


if beat == "egg":
    # hatches ~8s in: title card, a beat of egg wobble, then the crack
    p = Pet.new_egg(egg_type=0)
    p.stage_seconds = p.EGG_DURATION - 8.0
    p.hunger = 4                    # full: a newborn must not read "starving"
    p.energy = 24
    p.mood = 200
elif beat == "hungry":
    # the care beat: hungry ENOUGH that feeding visibly answers something
    p = _rookie()
    p.hunger, p.energy, p.mood = 2, 20, 180
    p.world_seconds = 9 * 3600.0    # mid-morning light in the arena
elif beat == "showcase":
    _, _by = data.load_sprites()
    num = next(n for n, r in sorted(_by.items())
               if r["stage"] == "Champion" and not r.get("_placeholder"))
    p = Pet(num=num, name=_by[num]["name"], stage="Champion")
    p.world_seconds = 9 * 3600.0
    p.hunger, p.energy, p.mood = 4, 24, 220
    p.wins, p.losses = 24, 3
    for n in [n for n, r in sorted(_by.items()) if not r.get("_placeholder")][:240]:
        persistence.album_add(n)      # an empty album photographs as an empty game
else:
    p = _rookie()
    p.world_seconds = 9 * 3600.0

p.bits = 99999 if beat == "showcase" else 800
for k in ("fish", "ball"):
    p.add_item(k)
persistence.set_auto_update(False)  # never let the launch updater run mid-take
persistence.save(p)
print("seeded", beat, p.name or "egg", p.stage)
