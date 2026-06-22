"""Battle — rebuilt to the official Digivice / Digital Monster battle sequence.

Researched from the Wikimon/Fandom wikis + the official manuals, and cross-checked
against Digimon Unlimited's own battle code (DigimonService.j()). The real vpet
battle is NOT the DVPet lunge-and-strike; it is:

  1. a fullscreen "BATTLE" banner flashes (DMU cl.az <-> cl.aA)
  2. the two Digimon face off (player left / foe right) and fire their attacks,
     which fly across and CLASH in the centre; the stronger pushes through
  3. on a hit, a fullscreen explosion covers the whole screen (DMU cm.f251a <-> cm.b)
  4. blows are exchanged a few times; the winner cheers, the loser collapses

Fullscreen overlay frames (16x32) live in data/battle_overlays.json. The Battle
engine still resolves the actual win/loss + rewards; this drives the animation.
"""
from __future__ import annotations
import json, os
from . import data
from .battle import Battle
from .render import render_scene
from .theme import LCD_ON, LCD_BG, INK, SIL_DAY, SIL_NIGHT
from . import menu

COLS, ROWS = 40, 8
PXH = ROWS * 2                                   # 16 px tall
_E = data.load_effects()
ATK = {"Vaccine": (_E.get("atk_vaccine") or _E.get("attack") or [None])[0],
       "Data":    (_E.get("atk_data") or _E.get("attack") or [None])[0],
       "Virus":   (_E.get("atk_virus") or _E.get("attack") or [None])[0]}
with open(os.path.join(os.path.dirname(__file__), "data", "battle_overlays.json")) as _f:
    _OV = json.load(_f)
BANNER = _OV["battle_banner"]                    # [az, aA]  fullscreen "BATTLE"
EXPLODE = _OV["hit_explosion"]                   # [f251a, b] fullscreen hit blast
OVW = len(BANNER[0][0])                          # 32
OVX = (COLS - OVW) // 2                           # centre the 32-wide overlay in 40

# poses (tuipet DVPet 11-frame layout)
IDLE, ATTACK, CHEER_A, CHEER_B, FLINCH, COLLAPSE = 0, 6, 6, 4, 9, 10


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _full(frame):
    """A fullscreen 16x32 overlay frame -> pixel coords, centred in the field."""
    return [(OVX + x, y) for y, row in enumerate(frame)
            for x, c in enumerate(row) if c == "1"]


def _cbounds(rows):
    w = max(len(r) for r in rows)
    cols = [x for x in range(w) if any(x < len(r) and r[x] == "1" for r in rows)]
    return (min(cols), max(cols)) if cols else (0, w - 1)


# per-tick timeline kinds are built once at battle start
BANNER_FLASHES = 3        # how many times "BATTLE" blinks
BANNER_HOLD = 3           # ticks per banner frame
FACEOFF_T = 5
BEAM_T = 6                # beams fly to centre
CLASH_T = 2               # beams meet
EXPLODE_HOLD = 2          # ticks per explosion frame
EXPLODE_FRAMES = 4        # total explosion ticks per hit
FLINCH_T = 3


class BattlePanel:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.i = 0                                # index into the timeline
        self.done_anim = False
        self._build()

    # ---- resolve outcome + build the animation timeline -----------------
    def _build(self):
        b = self.battle
        best = max(("Vaccine", "Data", "Virus"),
                   key=lambda a: {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power,
                                  "Virus": self.pet.virus}[a])
        guard = 0
        while not b.over and guard < 200:
            b.play_round(best); guard += 1
        self.won = bool(b.won)
        self.pet_attr = best
        self.foe_attr = b.enemy.get("attribute", "Virus")
        winner = "pet" if self.won else "foe"
        loser = "foe" if self.won else "pet"
        self.pet_lives = 3
        self.foe_lives = 3

        tl = []
        # 1) BATTLE banner flash (fullscreen)
        for _ in range(BANNER_FLASHES):
            tl += [{"m": "banner", "f": 0}] * BANNER_HOLD
            tl += [{"m": "banner", "f": 1}] * BANNER_HOLD
        # 2) face-off
        tl += [{"m": "faceoff"}] * FACEOFF_T
        # 3) three exchanges, the loser hit each time (stronger pushes through)
        pl, fl = 3, 3
        for ex in range(3):
            for s in range(BEAM_T):
                tl.append({"m": "beams", "prog": (s + 1) / BEAM_T})
            tl += [{"m": "clash"}] * CLASH_T
            if loser == "pet":
                pl -= 1
            else:
                fl -= 1
            for s in range(EXPLODE_FRAMES):
                tl.append({"m": "explode", "f": (s // EXPLODE_HOLD) % 2,
                           "loser": loser, "pl": pl, "fl": fl})
            tl += [{"m": "flinch", "loser": loser, "pl": pl, "fl": fl}] * FLINCH_T
        self.timeline = tl
        self.result_winner = winner

    # ---- driving --------------------------------------------------------
    def anim(self):
        self.frame_i += 1
        if self.i < len(self.timeline) - 1:
            self.i += 1
        else:
            self.done_anim = True

    def key(self, k):
        if k in ("escape", "space", "enter"):
            if self.done_anim:
                return ("done", self.battle)
            self.i = len(self.timeline) - 1       # skip to the end
            self.done_anim = True
        return None

    # ---- rendering ------------------------------------------------------
    def _rows(self, num, pose):
        rec = data.load_sprites()[1][num]
        return rec["frames"][pose] or rec["frames"][0]

    def _place(self, pet_rows, foe_rows):
        """player LEFT (faces right, mirror=True), foe RIGHT (faces left, mirror=False),
        anchored by real content edges so they hug the walls with a centre gap."""
        out = []
        edges = {}
        if pet_rows:
            src = [r[::-1] for r in pet_rows]            # mirror=True
            lo, hi = _cbounds(src)
            x = 1 - lo
            out.append((pet_rows, x, True))
            edges["pet"] = x + hi + 1                    # inner (right-facing) edge
        if foe_rows:
            lo, hi = _cbounds(foe_rows)                  # mirror=False
            x = (COLS - 2) - hi
            out.append((foe_rows, x, False))
            edges["foe"] = x + lo                        # inner (left-facing) edge
        return out, edges

    def _scene(self, placements, overlay):
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        return render_scene(placements, COLS, ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)

    def _beam_overlay(self, prog, p_edge, f_edge):
        """Both fighters' beams fly inward and clash at the centre."""
        cells = []
        mid = (p_edge + f_edge) // 2
        pbeam, fbeam = ATK.get(self.pet_attr), ATK.get(self.foe_attr)
        py = PXH - 12
        if pbeam:
            w = len(pbeam[0])
            x = int(p_edge + (mid - p_edge) * prog)
            cells += _blit(pbeam, min(x, mid - w), py)
        if fbeam:
            w = len(fbeam[0])
            x = int(f_edge - (f_edge - mid) * prog)
            cells += _blit([r[::-1] for r in fbeam], max(x - w, mid), py)
        return cells

    def text(self):
        b = self.battle
        fr = self.timeline[min(self.i, len(self.timeline) - 1)] if not self.done_anim \
            else {"m": "result"}
        m = fr["m"]
        pl = fr.get("pl", 0 if not self.won else 3)
        fl = fr.get("fl", 3 if not self.won else 0)

        if m == "banner":
            scene = self._scene([], _full(BANNER[fr["f"]]))
            note = "BATTLE!"
        elif m == "explode":
            scene = self._scene([], _full(EXPLODE[fr["f"]]))
            pl, fl = fr["pl"], fr["fl"]
            note = "HIT!"
        else:
            if m == "faceoff":
                pr, fpose = IDLE, IDLE
            elif m == "beams":
                pr, fpose = ATTACK, ATTACK
            elif m == "clash":
                pr, fpose = ATTACK, ATTACK
            elif m == "flinch":
                pr = COLLAPSE if fr["loser"] == "pet" else IDLE
                fpose = COLLAPSE if fr["loser"] == "foe" else IDLE
                pl, fl = fr["pl"], fr["fl"]
            else:  # result
                win = self.result_winner
                cheer = (5, 7)[self.frame_i % 2]        # winning(): cheer(true) poses 5,7
                pr = cheer if win == "pet" else COLLAPSE
                fpose = cheer if win == "foe" else COLLAPSE
                pl, fl = (3, 0) if self.won else (0, 3)
            pet_rows = self._rows(self.pet.num, pr)
            foe_rows = self._rows(b.enemy["num"], fpose)
            placements, edges = self._place(pet_rows, foe_rows)
            overlay = []
            if m == "beams":
                overlay = self._beam_overlay(fr["prog"], edges.get("pet", 8),
                                             edges.get("foe", COLS - 8))
            elif m == "clash":
                mid = (edges.get("pet", 8) + edges.get("foe", COLS - 8)) // 2
                overlay = [(mid + dx, PXH - 11 + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            scene = self._scene(placements, overlay)
            note = {"faceoff": f"{self.pet.name} vs {b.enemy['name']}",
                    "beams": "Clash!", "clash": "Clash!",
                    "flinch": "Hit!", "result": ""}.get(m, "")

        boss = "BOSS" if b.enemy["boss"] else ""
        out = menu.bar(f"BATTLE  vs {b.enemy['name']}"[:32], boss)
        out.append_text(scene)
        hearts = lambda n: "♥" * max(0, n) + "♡" * (3 - max(0, n))
        out.append(f"\nYou {hearts(pl)}", style=INK)
        out.append(f"      Foe {hearts(fl)}\n", style=INK)
        if self.done_anim:
            res = "VICTORY!" if self.won else "DEFEAT"
            out.append_text(menu.note(f"{res}  {b.reward}"))
            out.append_text(menu.footer("SPACE  continue"))
        else:
            out.append_text(menu.note(note))
            out.append_text(menu.footer("SPACE  skip"))
        return out
