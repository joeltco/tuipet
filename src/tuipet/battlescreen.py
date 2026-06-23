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

COLS, ROWS = 40, 12                              # fill the whole LCD (the HUD lives in the side panel)
PXH = ROWS * 2                                   # 24 px tall
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
    oy = max(0, (PXH - len(frame)) // 2)         # centre the 16px overlay in the 24px field
    return [(OVX + x, oy + y) for y, row in enumerate(frame)
            for x, c in enumerate(row) if c == "1"]


def _cbounds(rows):
    w = max(len(r) for r in rows)
    cols = [x for x in range(w) if any(x < len(r) and r[x] == "1" for r in rows)]
    return (min(cols), max(cols)) if cols else (0, w - 1)


# per-tick timeline kinds are built once at battle start
BANNER_FLASHES = 3        # how many times "BATTLE" blinks
BANNER_HOLD = 3           # ticks per banner frame
FACEOFF_T = 5
WINDUP_T = 3              # attacker rears back before firing
FIRE_T = 6                # the weapon flies one-way to the defender
EXPLODE_HOLD = 2          # ticks per explosion frame
EXPLODE_FRAMES = 6        # fullscreen hit-explosion flicker
FLINCH_T = 3              # defender reels after a hit
DODGE_T = 5               # defender leaps clear; the shot whiffs past


class BattlePanel:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.i = 0                                # index into the timeline
        self.done_anim = False
        self.hud_pl, self.hud_fl, self.hud_note = 3, 3, ""   # HUD state for the side panel
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
        self.result_winner = winner

        # --- build the turn-based exchange (DMU j(): one fires, the other dodges
        # or is hit; never simultaneous). The winner lands its shots; the loser's
        # shots mostly whiff, landing once for tension. First side to 0 lives loses.
        # orb count per side: out-powering the foe fires the stronger DOUBLE shot
        # (2 orbs, DMU Attack1), otherwise a single orb (Attack0) -- the manual:
        # "power higher than the enemy -> stronger attack."
        e = self.battle.enemy
        pet_pow = self.pet.vaccine + self.pet.data_power + self.pet.virus
        foe_pow = e.get("vaccine", 0) + e.get("data_power", 0) + e.get("virus", 0)
        orbs_of = {"pet": 2 if pet_pow > foe_pow else 1,
                   "foe": 2 if foe_pow > pet_pow else 1}

        pl = fl = 3
        loser_may_hit = 1                      # the loser lands this many before falling
        turn = winner                          # winner opens
        attacks = []
        while pl > 0 and fl > 0:
            atk = turn
            dfn = "foe" if atk == "pet" else "pet"
            if atk == winner:
                hit = True                     # the winner's shots connect
            else:
                # the loser only lands while it still has a budgeted hit AND it
                # won't KO the winner (so the winner survives to win)
                wlives = pl if winner == "pet" else fl
                hit = loser_may_hit > 0 and wlives > 1
                if hit:
                    loser_may_hit -= 1
            if hit:
                if dfn == "foe":
                    fl = max(0, fl - 1)
                else:
                    pl = max(0, pl - 1)
            attacks.append({"atk": atk, "def": dfn, "hit": hit,
                            "orbs": orbs_of[atk], "pl": pl, "fl": fl})
            turn = dfn                          # the defender shoots back next

        tl = []
        for _ in range(BANNER_FLASHES):         # 1) "BATTLE" banner flashes fullscreen
            tl += [{"m": "banner", "f": 0}] * BANNER_HOLD
            tl += [{"m": "banner", "f": 1}] * BANNER_HOLD
        tl += [{"m": "faceoff"}] * FACEOFF_T    # 2) the two face off
        cpl = cfl = 3                           # hearts shown DURING each beat
        for a in attacks:                       # 3) trade blows, one at a time
            for _ in range(WINDUP_T):
                tl.append({"m": "windup", "atk": a["atk"], "pl": cpl, "fl": cfl})
            for s in range(FIRE_T):
                tl.append({"m": "fire", "atk": a["atk"], "prog": (s + 1) / FIRE_T,
                           "orbs": a["orbs"], "pl": cpl, "fl": cfl})
            if a["hit"]:
                cpl, cfl = a["pl"], a["fl"]     # the shot lands -> life drops now
                for s in range(EXPLODE_FRAMES):
                    tl.append({"m": "hit", "f": (s // EXPLODE_HOLD) % 2, "def": a["def"],
                               "pl": cpl, "fl": cfl})
                tl += [{"m": "flinch", "def": a["def"], "pl": cpl, "fl": cfl}] * FLINCH_T
            else:
                for s in range(DODGE_T):        # the defender leaps clear -- a miss
                    tl.append({"m": "dodge", "def": a["def"], "prog": (s + 1) / DODGE_T,
                               "orbs": a["orbs"], "pl": cpl, "fl": cfl})
        self.timeline = tl

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
        fr = data.load_sprites()[1][num]["frames"]
        return (fr[pose] if pose < len(fr) else None) or fr[0]

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

    def _orb_ys(self, orbs):
        """1 orb on the firing line; 2 orbs straddle it 8px apart (DMU draws ap at
        y and y+8 for the double shot)."""
        return [PXH - 12] if orbs <= 1 else [PXH - 15, PXH - 7]

    def _shot_overlay(self, attacker, prog, orbs, p_edge, f_edge):
        """1 or 2 orbs fly from the attacker toward the defender (never both sides)."""
        if attacker == "pet":                            # player (left) fires right at the foe
            beam = ATK.get(self.pet_attr); src = beam
            x0, x1 = p_edge, f_edge - (len(beam[0]) if beam else 0)
        else:                                            # foe (right) fires left at the player
            beam = ATK.get(self.foe_attr); src = [r[::-1] for r in beam] if beam else beam
            x0, x1 = f_edge - (len(beam[0]) if beam else 0), p_edge
        if not beam:
            return []
        x = max(0, min(int(x0 + (x1 - x0) * prog), COLS - len(beam[0])))
        cells = []
        for y in self._orb_ys(orbs):
            cells += _blit(src, x, y)
        return cells

    def text(self):
        b = self.battle
        fr = self.timeline[min(self.i, len(self.timeline) - 1)] if not self.done_anim \
            else {"m": "result"}
        m = fr["m"]
        pl = fr.get("pl", 3)            # full hearts until an exchange decrements them
        fl = fr.get("fl", 3)

        if m == "banner":
            scene = self._scene([], _full(BANNER[fr["f"]]))
            note = "BATTLE!"
        elif m == "hit":
            scene = self._scene([], _full(EXPLODE[fr["f"]]))   # fullscreen hit explosion
            note = "HIT!"
        else:
            dfn = fr.get("def")
            atk = fr.get("atk") or ("foe" if dfn == "pet" else "pet")
            if m == "faceoff":
                pr = fpose = IDLE
            elif m in ("windup", "fire"):                      # only the attacker rears/fires
                pr = ATTACK if atk == "pet" else IDLE
                fpose = ATTACK if atk == "foe" else IDLE
            elif m == "dodge":                                 # the defender jukes (pose 1)
                pr = 1 if dfn == "pet" else IDLE
                fpose = 1 if dfn == "foe" else IDLE
            elif m == "flinch":                                # the struck side reels
                pr = COLLAPSE if dfn == "pet" else IDLE
                fpose = COLLAPSE if dfn == "foe" else IDLE
            else:                                              # result
                win = self.result_winner
                cheer = (5, 7)[self.frame_i % 2]               # winning(): cheer(true) 5,7
                pr = cheer if win == "pet" else COLLAPSE
                fpose = cheer if win == "foe" else COLLAPSE
            pet_rows = self._rows(self.pet.num, pr)
            foe_rows = self._rows(b.enemy["num"], fpose)
            placements, edges = self._place(pet_rows, foe_rows)
            pe, fe = edges.get("pet", 8), edges.get("foe", COLS - 8)
            overlay = []
            orbs = fr.get("orbs", 1)
            if m == "fire":                                    # the orb(s) fly AT the defender
                overlay = self._shot_overlay(atk, fr["prog"], orbs, pe, fe)
            elif m == "dodge":                                 # ...and sail on past the juke
                beam = ATK.get(self.pet_attr if atk == "pet" else self.foe_attr)
                if beam:
                    w = len(beam[0])
                    src = beam if atk == "pet" else [r[::-1] for r in beam]
                    x0, x1 = (fe, COLS - w) if atk == "pet" else (pe - w, 0)
                    x = max(0, min(int(x0 + (x1 - x0) * fr["prog"]), COLS - w))
                    for y in self._orb_ys(orbs):
                        overlay += _blit(src, x, y)
            scene = self._scene(placements, overlay)
            note = {"faceoff": f"{self.pet.name} vs {b.enemy['name']}",
                    "windup": "...", "fire": "Fire!", "dodge": "Dodge!",
                    "flinch": "Hit!", "result": ""}.get(m, "")

        # the LCD shows ONLY the battle scene (full height); the HUD (hearts, status,
        # controls) is published for the side stats panel via app._status_battle().
        self.hud_pl, self.hud_fl, self.hud_note = pl, fl, note
        return scene
