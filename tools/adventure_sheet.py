"""The adventure/town/shop CONTACT SHEET (night hardening pass 2026-07-21).

Drives the REAL panels through every state today's arcs shipped and prints
each frame as visible ASCII -- the LCD pixel buffer decoded ('#' on, '.'
off, '%' free-ink weather layer) with the strip line under it -- so a
human (or Claude) can EYEBALL the screens the way pytest never does
(UI-render law: pytest never renders markup; the sheet is the eye).

Usage: python tools/adventure_sheet.py [state ...]   (default: all)
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tuipet import adventure, data, render, tournament  # noqa: E402
from tuipet.adventurescreen import (AdventurePanel, ZonePickPanel,  # noqa: E402
                                    HZ_TELE_T, HZ_LUNGE_T, INV_WALK_T,
                                    INV_REVEAL_T, INV_HOLD_T, PULSE_T)
from tuipet.pet import Pet  # noqa: E402

D = datetime.date(2026, 3, 3)
tournament._today = lambda: D                 # a stable, festival-free day

adventure.ENCOUNTER_CHANCE = 0.0              # the sheet drives states by hand
adventure.FIND_CHANCE = 0.0
adventure.HAZARD_CHANCE = 0.0

# -- the pixel tap: capture the buffer render_scene paints ---------------------
_LAST = {"buf": None}
_real_paint = render._paint_cells


def _tap(buf, *a, **k):
    _LAST["buf"] = [row[:] for row in buf]
    return _real_paint(buf, *a, **k)


render._paint_cells = _tap


def show(title, panel):
    txt = panel.text()
    print(f"\n===== {title} =====")
    buf = _LAST["buf"]
    _LAST["buf"] = None
    if buf is not None:
        for row in buf:
            print("".join(".#%"[min(v, 2)] for v in row))
    else:                                     # a text screen: plain rows
        for ln in txt.plain.split("\n"):
            print(ln)
    strip = getattr(panel, "strip", lambda: "")()
    if strip:
        from rich.text import Text
        print(f"strip> {Text.from_markup(strip).plain}")


def _pet():
    return Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)


def _on_road(pet=None, zone=None):
    pan = AdventurePanel(pet or _pet(), zone=zone or adventure.ZONES[0])
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    pan._wx = 14.0
    return pan


SHEET = {}


def state(name):
    def deco(fn):
        SHEET[name] = fn
        return fn
    return deco


@state("march")
def _march():
    show("march (healthy, mid-window)", _on_road())


@state("march-edge")
def _march_edge():
    p = _on_road()
    p._wx = 32.0
    show("march (exiting right)", p)


@state("march-sick")
def _sick():
    p = _on_road()
    p.pet.sick = True
    p.frame_i = 5
    show("march (sick trudge, collapse beat)", p)


@state("march-aged")
def _aged():
    p = _on_road()
    p.pet.age_seconds = p.pet.lifespan - 1
    show("march (aged shuffle)", p)


@state("nap")
def _nap():
    p = _on_road()
    p.pet.asleep = True
    show("roadside nap (Zzz)", p)


@state("refuse")
def _refuse():
    p = _on_road()
    p._refuse_t, p._refused = 12, True
    show("refusal (head-shake beat)", p)
    p._refuse_t = 0
    show("refusal (planted, weary)", p)


@state("glint")
def _glint():
    p = _on_road()
    p._find = adventure.ZONES[0]["find_keys"][0]
    p.frame_i = 6
    show("glint (attention bounce + !)", p)


@state("dig")
def _dig():
    p = _on_road()
    p._find = adventure.ZONES[0]["find_keys"][0]
    p.key("enter")
    for _ in range(INV_WALK_T + 4):
        p.anim()
    show("timed dig (the canon bar)", p)
    p.key("space")                            # lock wherever it stands
    while p._scene and p._scene["t"] < INV_WALK_T + 4:
        p.anim()
    show("dig suspense (dots + !)", p)
    while p._scene and p._scene["t"] < INV_REVEAL_T + 3:
        p.anim()
    show("dig reveal (find held up)", p)
    while p._scene and p._scene["t"] < INV_HOLD_T + 5:
        p.anim()
    show("dig carry-back (find in front)", p)


@state("hazard")
def _hazard():
    p = _on_road()
    p._hazard = {"t": 3, "enemy": adventure.ZONES[0]["randoms"][0],
                 "dodged": False, "hit": False}
    show("hazard telegraph (!)", p)
    p._hazard["t"] = HZ_TELE_T + HZ_LUNGE_T // 2
    show("hazard charge (pouncer in)", p)
    p._hazard.update(t=HZ_TELE_T + HZ_LUNGE_T + 4, dodged=True)
    show("hazard duck (pass-by)", p)
    p._hazard.update(dodged=False, hit=True,
                     t=HZ_TELE_T + HZ_LUNGE_T + 2)
    show("hazard eaten (burst + hurt)", p)


@state("gate")
def _gate():
    z = next(z for z in adventure.ZONES if z["bosses"])
    p = _on_road(zone=z)
    p.adv.loc = p.adv.total
    p._at_gate = True
    p.travelling = False
    show("gate faceoff", p)


@state("pulse")
def _pulse():
    p = _on_road()
    p.travelling = False
    p._pulse = {"t": 6, "parade": [], "msg": None}    # inside an ON span
    show("zone pulse (bright span)", p)
    p._pulse["t"] = 12                                # between spans
    show("zone pulse (rest beat)", p)


@state("parade")
def _parade():
    z = next(z for z in adventure.ZONES
             if z["bosses"] and z["bosses"][0].get("parade_msg"))
    p = _on_road(zone=z)
    p.travelling = False
    nums = [b["num"] for b in z["bosses"]][:3]
    p._parade = {"t": 10, "nums": nums, "msg": z["bosses"][0]["parade_msg"]}
    show("boss parade (marcher mid-cross)", p)


@state("summary")
def _summary():
    p = _on_road()
    p.adv.done = True
    p.adv.bits_earned, p.adv.wins, p.adv.fights = 264, 5, 5
    p.adv.finds, p.adv.lives, p.adv.best_streak = 3, 2, 4
    p.adv.holiday = "Odaiba Memorial Day"
    p._new_best = True
    p._summary = True
    p.travelling = False
    show("summary card (everything on)", p)


@state("teleport")
def _tele():
    p = AdventurePanel(_pet(), zone=adventure.ZONES[0])
    for _ in range(30):
        p.anim()
    show("teleport (leave, mid-shrink)", p)


@state("picker")
def _picker():
    from tuipet import persistence
    persistence.zone_best_set(0, 264)
    pet = _pet()
    pet.adv_progress = 3
    show("zone picker (with a best)", ZonePickPanel(pet))


@state("town")
def _town():
    from tuipet.townscreen import TownPanel
    show("town hub", TownPanel(_pet(), town_id=4))


@state("townshop")
def _townshop():
    from tuipet.shopscreen import ShopPanel
    pet = _pet()
    pet.bits = 9999
    pan = ShopPanel(pet, town_id=4)
    show("town shop (Food tab, deal day)", pan)
    pan.tab = 1
    show("town shop (Items tab)", pan)
    for _ in range(3):                        # drain the steak cap
        pan.tab = 0
        pan.key("enter")
    show("town shop (sold out today)", pan)
    bag = ShopPanel(pet, start_mode="bag", bag_only=True, town_id=0)
    show("town bag (demand sell rates)", bag)


def main():
    names = sys.argv[1:] or list(SHEET)
    for n in names:
        fn = SHEET.get(n)
        if fn is None:
            print(f"unknown state: {n}  (have: {', '.join(SHEET)})")
            continue
        fn()


if __name__ == "__main__":
    main()
