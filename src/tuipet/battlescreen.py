"""Battle View — the authentic DM20 sequence (one monster on screen at a time).

Flow: a BATTLE! banner, then a pre-battle ATTACK-ORDER minigame (time your strike --
land it in the zone and you strike first), then the clash resolves automatically on
Power + the attribute triangle (see battle.py) and animates as an orb duel.

Per DVPet's battle View the monsters are never shown together during a volley: whoever
has initiative rears back and FIRES an orb off the near edge; the screen switches to the
DEFENDER, and the orb arrives from the far edge -- the defender DODGES (a 0-damage miss)
or is HIT (a fullscreen flash), then the roles reverse.  Player stands RIGHT (faces left),
enemy LEFT (faces right).  You do NOT pick an attribute -- your Digimon's is fixed.
"""
from __future__ import annotations
import json
import os
from . import data
from .battle import Battle
from .render import render_scene
from .theme import LCD_ON, LCD_BG, SIL_DAY, SIL_NIGHT
from . import menu

COLS, ROWS = 40, 12
PXH = ROWS * 2                                   # 24 px tall
with open(os.path.join(os.path.dirname(__file__), "data", "battle_overlays.json")) as _f:
    _OV = json.load(_f)
BANNER = _OV["battle_banner"]
EXPLODE = _OV["hit_explosion"]

# the authentic 32-wide play window, centred inside the 40-wide LCD canvas.
PLAY_COLS = 32
PLAY_X0 = (COLS - PLAY_COLS) // 2                # 4
PLAY_R = PLAY_X0 + PLAY_COLS                     # 36

# poses, WAYLAND-native frame order (0 idle_1, 1 idle_2, 4 happy, 5/7 cheer, 6 attack,
# 10 collapse; >=12 falls back to idle on short sheets).
IDLE, TURN, ATTACK, CHEER_A, CHEER_B, COLLAPSE = 0, 1, 6, 5, 7, 10
CHARGE = 4                                       # DVPet shoot frame 4: pre-attack / charge pose
BAND_TOP = PXH - 18                              # 6: creature/orb top limit
BAND_BOT = PXH - 2                               # 22: floor
FIRE_Y = PXH - 14                                # orb mid-body height (centred in the band)

# timeline tuning (ticks per beat, 1 tick == 0.1s)
BANNER_FLASHES, BANNER_HOLD = 3, 4
FACEOFF_T = 9
WINDUP_T = 9
FIRE_T = 12
EXPLODE_HOLD, EXPLODE_FRAMES = 3, 9
FLINCH_T = 12
DODGE_T = 14

# attack-order minigame: a marker sweeps the track; SPACE in the centre zone = strike first
MG_SPEED = 0.06                                  # marker travel per tick (0..1)
MG_ZONE = 0.14                                   # half-width of the "first strike" zone


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _full(frame):
    ox = max(0, (COLS - (len(frame[0]) if frame and frame[0] else 0)) // 2)
    oy = max(0, (PXH - len(frame)) // 2)
    return [(ox + x, oy + y) for y, row in enumerate(frame)
            for x, c in enumerate(row) if c == "1"]


def _cbounds(rows):
    w = max(len(r) for r in rows)
    cols = [x for x in range(w) if any(x < len(r) and r[x] == "1" for r in rows)]
    return (min(cols), max(cols)) if cols else (0, w - 1)


class BattlePanel:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.pet_attr = self.battle.pet_attr
        self.foe_attr = self.battle.enemy_attr
        self.frame_i = 0
        self.done_anim = False
        self.won = None
        self.hud_php = self.battle.pet_hp
        self.hud_fhp = self.battle.enemy_hp
        self.hud_note = "Battle start!"
        self.phase = "intro"
        self.sfx = "battle"
        self._last_m = None
        # attack-order minigame state
        self.mg_pos = 0.0
        self.mg_dir = 1
        self.mg_result = None            # True = player struck first
        tl = []
        for _ in range(BANNER_FLASHES):
            tl += [{"m": "banner", "f": 0}] * BANNER_HOLD
            tl += [{"m": "banner", "f": 1}] * BANNER_HOLD
        self.timeline = tl
        self.i = 0

    # ---- resolve the whole clash, then build the full orb-duel timeline ----
    def _resolve_and_build(self, player_first):
        b = self.battle
        b.resolve(player_first=player_first)
        tl = []
        ph, fh = b.pet_max, b.enemy_max
        tl += [{"m": "faceoff", "view": "pet", "ph": ph, "fh": fh}] * FACEOFF_T
        for a in b.attacks:
            atk = a["atk"]
            dfn = "foe" if atk == "pet" else "pet"
            dmg, dbl = a["dmg"], a["double"]
            for s in range(WINDUP_T):
                tl.append({"m": "windup", "view": atk, "atk": atk, "wu": s, "ph": ph, "fh": fh})
            for s in range(FIRE_T):                          # attacker: orb leaves off-screen
                tl.append({"m": "fire_out", "view": atk, "atk": atk, "double": dbl,
                           "prog": (s + 1) / FIRE_T, "ph": ph, "fh": fh})
            for s in range(FIRE_T):                          # defender: orb arrives off-screen
                tl.append({"m": "fire_in", "view": dfn, "atk": atk, "def": dfn, "double": dbl,
                           "prog": (s + 1) / FIRE_T, "ph": ph, "fh": fh})
            ph, fh = a["ph"], a["fh"]                         # HP after this attack lands
            if dmg > 0:                                      # HIT: fullscreen flash, then flinch
                for s in range(EXPLODE_FRAMES):
                    tl.append({"m": "hit", "f": (s // EXPLODE_HOLD) % 2, "def": dfn, "double": dbl, "ph": ph, "fh": fh})
                tl += [{"m": "flinch", "view": dfn, "def": dfn, "ph": ph, "fh": fh}] * FLINCH_T
            else:                                            # DODGE: defender weaves, orb whiffs
                for s in range(DODGE_T):
                    tl.append({"m": "dodge", "view": dfn, "atk": atk, "def": dfn,
                               "prog": (s + 1) / DODGE_T, "ph": ph, "fh": fh})
        self.timeline = tl
        self.i = 0
        self.phase = "anim"

    def _enter_result(self):
        self.done_anim = True
        self.won = bool(self.battle.won)
        self.phase = "result"

    # ---- driving ----
    def _emit_sfx(self):
        entry = self.timeline[self.i]
        m = entry.get("m")
        if m != self._last_m:
            if m == "fire_out":
                self.sfx = "strongAttack" if entry.get("double") else "attack"
            elif m == "hit":
                self.sfx = "strongHit" if entry.get("double") else "attack"
        self._last_m = m

    def anim(self):
        self.frame_i += 1
        if self.phase in ("result",):
            return
        if self.phase == "minigame":
            self.mg_pos += self.mg_dir * MG_SPEED            # marker sweeps + bounces
            if self.mg_pos >= 1.0:
                self.mg_pos, self.mg_dir = 1.0, -1
            elif self.mg_pos <= 0.0:
                self.mg_pos, self.mg_dir = 0.0, 1
            return
        if self.i < len(self.timeline) - 1:
            self.i += 1
            self._emit_sfx()
        elif self.phase == "intro":
            self.phase = "minigame"                          # banner done -> the attack-order minigame
        elif self.battle.over:
            self._enter_result()

    def key(self, k):
        if self.phase == "intro":
            if k in ("space", "enter", "escape"):
                self.i = len(self.timeline) - 1
                self.phase = "minigame"
            return None
        if self.phase == "minigame":
            if k in ("space", "enter"):                      # lock the strike
                self.mg_result = abs(self.mg_pos - 0.5) <= MG_ZONE
                self.sfx = "confirm"
                self._resolve_and_build(self.mg_result)
            elif k in ("escape", "s"):
                self.battle.surrender()
                return ("done", None)
            return None
        if self.phase == "anim":
            if k in ("space", "enter", "escape"):
                self.i = len(self.timeline) - 1              # skip to the end of the clash
            return None
        if k in ("space", "enter", "escape"):                # result -> close
            return ("done", self.battle)
        return None

    # ---- rendering ----
    def _rows(self, num, pose):
        fr = data.load_sprites()[1][num]["frames"]
        return (fr[pose] if pose < len(fr) else None) or fr[0]

    def _scene(self, placements, overlay):
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        return render_scene(placements, COLS, ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg,
                            clip=(PLAY_X0, PLAY_R))

    def _place_one(self, view, rows, xshift=0):
        if view == "foe":
            src = [r[::-1] for r in rows]
            lo, hi = _cbounds(src)
            x = (PLAY_X0 + 1 - lo) + xshift
            return [(rows, x, True)], x + hi + 1
        lo, hi = _cbounds(rows)
        x = ((PLAY_R - 2) - hi) + xshift
        return [(rows, x, False)], x + lo

    def _faceoff_scene(self):
        """Both combatants staring each other down (used for the minigame + intro)."""
        pl_foe = self._place_one("foe", self._rows(self.battle.enemy["num"], IDLE))[0]
        pl_pet = self._place_one("pet", self._rows(self.pet.num, IDLE))[0]
        return self._scene(pl_foe + pl_pet, [])

    def _pow(self, side):
        return self.pet.power if side == "pet" else self.battle.enemy_power

    def _orb_overlay(self, fr, mouth):
        atk, m, prog = fr["atk"], fr["m"], fr["prog"]
        if atk == "pet":
            orb = data.attack_orb(self.pet.num, self.pet_attr, self._pow("pet"))
        else:
            orb = data.attack_orb(self.battle.enemy["num"], self.foe_attr, self._pow("foe"))
        if not orb:
            return []
        w = len(orb[0])
        left = (atk == "pet")
        if m == "fire_out":
            x0, x1 = (mouth - w, PLAY_X0 - w) if left else (mouth, PLAY_R)
        else:
            x0, x1 = (PLAY_R, mouth) if left else (PLAY_X0 - w, mouth - w)
            if m == "dodge":
                x1 = PLAY_X0 - w if left else PLAY_R
        src = orb if left else [r[::-1] for r in orb]
        x = int(x0 + (x1 - x0) * prog)
        h = len(src)
        mid = BAND_TOP + (16 - h) // 2
        if fr.get("double"):
            pts = _blit(src, x, BAND_TOP) + _blit(src, x, BAND_BOT - h)
        else:
            pts = _blit(src, x, mid)
        return pts

    def _render_scene_frame(self, fr):
        b = self.battle
        m = fr["m"]
        ph = fr.get("ph", b.pet_hp)
        fh = fr.get("fh", b.enemy_hp)
        if m == "banner":
            scene = self._scene([], _full(BANNER[fr["f"]]))
            note = "BATTLE!"
        elif m == "hit":
            scene = self._scene([], _full(EXPLODE[fr["f"]]))
            note = "HIT!"
        else:
            view = fr.get("view", "pet")
            if m == "result":
                pose = (CHEER_A, CHEER_B)[self.frame_i % 2] if self.won else COLLAPSE
            elif m == "windup":
                pose = (TURN, TURN, IDLE, IDLE, CHARGE, CHARGE)[min(fr.get("wu", 0), 5)]
            elif m == "fire_out":
                pose = ATTACK
            elif m == "dodge":
                pose = TURN if self.frame_i % 2 else IDLE
            elif m == "flinch":
                pose = COLLAPSE
            elif m == "fire_in":
                pose = CHARGE if self.frame_i % 2 else IDLE
            else:                                            # faceoff
                pose = IDLE
            num = self.pet.num if view == "pet" else b.enemy["num"]
            rows = self._rows(num, pose)
            xshift = 0
            back = 1 if view == "pet" else -1
            if m == "windup":
                xshift = back * min(3, fr.get("wu", 0) + 1)
            elif m == "fire_out" and fr.get("prog", 1) < 0.35:
                xshift = -back * 2
            elif m == "dodge":
                xshift = back * (3 if self.frame_i % 2 else 2)
            place, mouth = self._place_one(view, rows, xshift)
            overlay = self._orb_overlay(fr, mouth) if m in ("fire_out", "fire_in", "dodge") else []
            scene = self._scene(place, overlay)
            note = {"faceoff": f"{self.pet.name[:8]} vs {b.enemy['name'][:8]}",
                    "windup": "...", "fire_out": "Fire!", "fire_in": "Incoming!",
                    "dodge": "Dodge!", "flinch": "Hit!", "result": ""}.get(m, "")
        self.hud_php, self.hud_fhp, self.hud_note = ph, fh, note
        return scene

    def minigame_cells(self, width=14):
        """(marker_index, zone_lo, zone_hi) for the status-HUD attack-order track."""
        pos = int(round(self.mg_pos * (width - 1)))
        zone_lo = int(round((0.5 - MG_ZONE) * (width - 1)))
        zone_hi = int(round((0.5 + MG_ZONE) * (width - 1)))
        return pos, zone_lo, zone_hi

    def text(self):
        if self.phase == "minigame":
            self.hud_php, self.hud_fhp = self.battle.pet_hp, self.battle.enemy_hp
            self.hud_note = "Time your strike!"
            return self._faceoff_scene()
        if self.phase == "result":
            return self._render_scene_frame({"m": "result", "view": "pet"})
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        return self._render_scene_frame(fr)
