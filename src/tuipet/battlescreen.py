"""Battle — the authentic Digimon V-pet sequence (one monster on screen at a time).

Per DVPet's battle View (SpriteAnim.battlePlayerShootAnim / battlePlayerReceiveAttackAnim /
dodge / battleHit): the monsters are NEVER shown together during a volley. Whoever has
initiative is shown alone, rears back and FIRES its attack orb; the orb flies OFF the near
screen edge; the screen then switches to the DEFENDER alone, and the orb arrives from the
OPPOSITE off-screen edge -- the defender either DODGES (weaves aside, a 0-damage miss) or is
HIT (a fullscreen explosion flash). Then the roles reverse. Orbs are the real per-attribute /
per-Digimon projectiles (attackSprites.png + attackSpritesSpecial.png), not the menu icons.

Turn-interactive: each round you pick an attack type; Model.Battle resolves it; this drives
the presentation. Player stands on the RIGHT (faces left), enemy on the LEFT (faces right).
"""
from __future__ import annotations
import json, os
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
OVW = len(BANNER[0][0])
OVX = (COLS - OVW) // 2

# poses (tuipet DVPet 11-frame layout)
IDLE, TURN, ATTACK, CHEER_A, CHEER_B, COLLAPSE = 0, 1, 6, 5, 7, 10
CHARGE = 4                                      # DVPet shoot frame 4: pre-attack/charge pose
FIRE_Y = PXH - 14                                # orb travels across the monster's mid-body

# timeline tuning (ticks per beat)
BANNER_FLASHES, BANNER_HOLD = 3, 3
FACEOFF_T = 5                                    # 0.6s stare-down
WINDUP_T = 6                                     # 0.7s charge / rear-back before firing
FIRE_T = 7                                       # 0.84s per orb leg (~6px/beat, DVPet pace)
FIRE_CROSS = 12                                  # 1.4s: orb crosses from attacker to defender
EXPLODE_HOLD, EXPLODE_FRAMES = 2, 6              # 0.72s strobing hit flash
FLINCH_T = 8                                     # ~1.0s held hurt pose (DVPet aftermath)
DODGE_T = 9                                      # ~1.1s weave

OPTS = [("Vaccine", "Vaccine"), ("Data", "Data"), ("Virus", "Virus"), ("Surrender", None)]
# attack/defence chip effects -> a short on-screen label (DVPet AttackEffectProcess)
EFFECT_LABEL = {"DefenseUp": "Blocked!", "AttackUp": "Power up!", "Counter": "Counter!",
                "Weaken": "Weakened!", "DisableAttack": "Disabled!", "Leech": "Leech!",
                "Absorb": "Absorb!", "Heal": "Heal!", "First": "First strike!", "Second": "Second!"}


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _full(frame):
    oy = max(0, (PXH - len(frame)) // 2)
    return [(OVX + x, oy + y) for y, row in enumerate(frame)
            for x, c in enumerate(row) if c == "1"]


def _cbounds(rows):
    w = max(len(r) for r in rows)
    cols = [x for x in range(w) if any(x < len(r) and r[x] == "1" for r in rows)]
    return (min(cols), max(cols)) if cols else (0, w - 1)


class BattlePanel:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.sel = 0
        self.pet_attr = None
        self.foe_attr = None
        self.done_anim = False
        self.won = None
        self.hud_php = self.battle.pet_hp
        self.hud_fhp = self.battle.enemy_hp
        self.hud_note = "Battle start!"
        self.phase = "intro"
        tl = []
        for _ in range(BANNER_FLASHES):
            tl += [{"m": "banner", "f": 0}] * BANNER_HOLD
            tl += [{"m": "banner", "f": 1}] * BANNER_HOLD
        self.timeline = tl
        self.i = 0

    # ---- one round: pick attack, resolve, build the alternating-view timeline ----
    def _resolve_and_build(self, attr):
        b = self.battle
        ph0, fh0 = b.pet_hp, b.enemy_hp
        b.play_round(attr)
        self.pet_attr = b.last_player_attr
        self.foe_attr = b.last_enemy_attr
        pdmg, edmg = b.last_player_damage, b.last_enemy_damage
        # strike order: initiative first; a KO'd side does not retaliate
        if b.last_player_first:
            seq = [("pet", "foe", pdmg)]
            if fh0 - max(0, pdmg) > 0:
                seq.append(("foe", "pet", edmg))
        else:
            seq = [("foe", "pet", edmg)]
            if ph0 - max(0, edmg) > 0:
                seq.append(("pet", "foe", pdmg))

        tl = []
        ph, fh = ph0, fh0
        tl += [{"m": "faceoff", "view": seq[0][0], "ph": ph, "fh": fh}] * FACEOFF_T
        for atk, dfn, dmg in seq:
            other = edmg if atk == "pet" else pdmg
            dbl = dmg >= 2 and dmg >= other                  # DVPet doubleAttack: strong & out/matching power
            fxn = b.last_effect if atk == "pet" else None    # only the player carries chip effects (PvE)
            for s in range(WINDUP_T):
                tl.append({"m": "windup", "view": atk, "atk": atk, "wu": s, "ph": ph, "fh": fh})
            for s in range(FIRE_CROSS):                      # both shown: orb crosses to the defender
                tl.append({"m": "fire", "atk": atk, "def": dfn, "double": dbl, "fx": fxn,
                           "prog": (s + 1) / FIRE_CROSS, "ph": ph, "fh": fh})
            if dmg > 0:                                      # HIT: fullscreen flash, then flinch
                if dfn == "foe":
                    fh = max(0, fh - dmg)
                else:
                    ph = max(0, ph - dmg)
                for s in range(EXPLODE_FRAMES):
                    tl.append({"m": "hit", "f": (s // EXPLODE_HOLD) % 2, "def": dfn, "ph": ph, "fh": fh})
                tl += [{"m": "flinch", "view": dfn, "def": dfn, "ph": ph, "fh": fh}] * FLINCH_T
            else:                                            # DODGE: defender weaves, orb whiffs past
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
    def anim(self):
        self.frame_i += 1
        if self.phase in ("menu", "result"):
            return
        if self.i < len(self.timeline) - 1:
            self.i += 1
        elif self.phase == "intro":
            self.phase = "menu"
        else:
            if self.battle.over:
                self._enter_result()
            else:
                self.phase = "menu"

    def key(self, k):
        if self.phase == "intro":
            if k in ("space", "enter", "escape"):
                self.i = len(self.timeline) - 1
                self.phase = "menu"
            return None
        if self.phase == "menu":
            if k in ("up", "k"):
                self.sel = (self.sel - 1) % len(OPTS)
            elif k in ("down", "j"):
                self.sel = (self.sel + 1) % len(OPTS)
            elif k in ("1", "2", "3"):
                self.sel = int(k) - 1
                self._resolve_and_build(OPTS[self.sel][1])
            elif k in ("enter", "space"):
                if OPTS[self.sel][1] is None:
                    self.battle.surrender()
                    return ("done", None)
                self._resolve_and_build(OPTS[self.sel][1])
            elif k == "s":
                self.battle.surrender()
                return ("done", None)
            elif k == "escape":
                return ("done", None)
            return None
        if self.phase == "anim":
            if k in ("space", "enter", "escape"):
                self.i = len(self.timeline) - 1
            return None
        if k in ("space", "enter", "escape"):
            return ("done", self.battle)
        return None

    # ---- rendering ----
    def _rows(self, num, pose):
        fr = data.load_sprites()[1][num]["frames"]
        return (fr[pose] if pose < len(fr) else None) or fr[0]

    def _scene(self, placements, overlay):
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        return render_scene(placements, COLS, ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)

    def _place_both(self, ppose, fpose, hide=None, pshift=0, fshift=0):
        """BOTH monsters facing off (real-vpet layout): player on the LEFT facing RIGHT,
        foe on the RIGHT facing LEFT. Returns (placements, pmouth, fmouth, body_y) -- the
        two inner firing edges and the shared mid-body height the orb travels at."""
        b = self.battle
        prows = [] if hide == "pet" else self._rows(self.pet.num, ppose)
        frows = [] if hide == "foe" else self._rows(b.enemy["num"], fpose)
        pf = [r[::-1] for r in prows] if prows else []      # player faces RIGHT (native faces left)
        placements = []
        pmouth, fmouth, body_y = 2, COLS - 3, PXH - 12
        if pf:
            plo, phi = _cbounds(pf)
            px = (1 - plo) + pshift
            placements.append((pf, px, False))
            pmouth = px + phi + 1                           # right edge -> toward the foe
            body_y = (PXH - len(pf) - 2) + len(pf) // 2      # mid-body height
        if frows:
            flo, fhi = _cbounds(frows)                       # foe faces LEFT (native)
            fx = ((COLS - 2) - fhi) + fshift
            placements.append((frows, fx, False))
            fmouth = fx + flo - 1                            # left edge -> toward the player
        return placements, pmouth, fmouth, body_y

    def _orb_cross(self, fr, pmouth, fmouth, body_y, whiff=False):
        """The attacker's orb flying ACROSS the gap to the defender (player L->R, foe R->L).
        Reaches the defender's near edge at prog 1 (then the defender flashes); on a dodge
        it whiffs off the far edge. Same DVPet orb sprite, just routed between the two mons."""
        b = self.battle
        atk, prog = fr["atk"], fr["prog"]
        if atk == "pet":
            orb = data.attack_orb(self.pet.num, self.pet_attr, self._pow("pet", self.pet_attr))
        else:
            orb = data.attack_orb(b.enemy["num"], self.foe_attr, self._pow("foe", self.foe_attr))
        if not orb:
            return []
        w, h = len(orb[0]), len(orb)
        oy = body_y - h // 2
        if atk == "pet":                                    # left -> right
            x0, x1 = pmouth, (COLS if whiff else fmouth - w)
            src = [r[::-1] for r in orb]                     # orb art faces left -> flip to point right
        else:                                               # right -> left
            x0, x1 = fmouth - w, (-w if whiff else pmouth)
            src = orb
        x = int(x0 + (x1 - x0) * prog)
        pts = _blit(src, x, oy)
        if fr.get("double"):                                # doubleAttack: a second orb stacked above
            pts += _blit(src, x, oy - h - 1)
        return pts

    def _pow(self, side, attr):
        if side == "pet":
            return {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power,
                    "Virus": self.pet.virus}.get(attr, 0)
        e = self.battle.enemy
        return {"Vaccine": e.get("vaccine", 0), "Data": e.get("data_power", 0),
                "Virus": e.get("virus", 0)}.get(attr, 0)

    def _render_scene_frame(self, fr):
        b = self.battle
        m = fr["m"]
        ph = fr.get("ph", b.pet_hp)
        fh = fr.get("fh", b.enemy_hp)
        if m == "banner":                                    # full-screen BATTLE flash, no mons yet
            self.hud_php, self.hud_fhp, self.hud_note = ph, fh, "BATTLE!"
            return self._scene([], _full(BANNER[fr["f"]]))

        atk, dfn = fr.get("atk"), fr.get("def")
        ppose = fpose = IDLE                                  # both mons always on screen, facing off
        pshift = fshift = 0
        hide = None
        overlay = []
        note = ""
        if m == "faceoff":
            note = f"{self.pet.name[:8]} vs {b.enemy['name'][:8]}"
        elif m == "result":                                  # winner cheers, loser stays collapsed
            cheer = (CHEER_A, CHEER_B)[self.frame_i % 2]
            ppose, fpose = (cheer, COLLAPSE) if self.won else (COLLAPSE, cheer)
        elif m == "windup":
            wu = fr.get("wu", 0)
            charge = (TURN, TURN, IDLE, IDLE, CHARGE, CHARGE)[min(wu, 5)]
            back = -min(3, wu + 1)                            # rear back AWAY from the foe (player<-, foe->)
            if atk == "pet":
                ppose, pshift = charge, back
            else:
                fpose, fshift = charge, -back
            note = "..."
        elif m == "fire":
            lunge = -2 if fr.get("prog", 1) < 0.3 else 0      # snap forward on release
            if atk == "pet":
                ppose, pshift = ATTACK, -lunge
            else:
                fpose, fshift = ATTACK, lunge
            note = EFFECT_LABEL.get(fr.get("fx"), "Fire!")
        elif m == "hit":                                     # the LOSER (defender) flashes on/off
            if fr.get("f"):
                hide = dfn
            else:
                if dfn == "pet": ppose = COLLAPSE
                else: fpose = COLLAPSE
            note = "Hit!"
        elif m == "flinch":
            if dfn == "pet": ppose = COLLAPSE
            else: fpose = COLLAPSE
            note = "Hit!"
        elif m == "dodge":
            weave = TURN if self.frame_i % 2 else IDLE
            if atk == "pet":
                ppose, fpose = ATTACK, weave
            else:
                fpose, ppose = ATTACK, weave
            note = "Dodge!"

        place, pmouth, fmouth, body_y = self._place_both(ppose, fpose, hide=hide,
                                                         pshift=pshift, fshift=fshift)
        if m == "fire":
            overlay = self._orb_cross(fr, pmouth, fmouth, body_y)
        elif m == "dodge":
            overlay = self._orb_cross(fr, pmouth, fmouth, body_y, whiff=True)
        self.hud_php, self.hud_fhp, self.hud_note = ph, fh, note
        return self._scene(place, overlay)

    def _render_menu(self):
        b = self.battle
        out = menu.header("BATTLE", f"vs {b.enemy['name'][:16]}")
        tag = " BOSS" if b.enemy.get("boss") else ""
        out.append_text(menu.note(
            f"You HP {b.pet_hp}/{b.pet_max}   Foe HP {b.enemy_hp}/{b.enemy_max}{tag}"))
        out.append_text(menu.blanks(1))
        powr = {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power, "Virus": self.pet.virus}
        for i, (label, attr) in enumerate(OPTS):
            tagr = f"pow {powr[attr]}" if attr else "bow out"
            out.append_text(menu.row(f"{label:<10} {tagr}", i == self.sel))
        out.append_text(menu.footer("↑↓ pick   ENTER attack   ESC flee"))
        self.hud_php, self.hud_fhp, self.hud_note = b.pet_hp, b.enemy_hp, "Choose your attack"
        return out

    def text(self):
        if self.phase == "menu":
            return self._render_menu()
        if self.phase == "result":
            return self._render_scene_frame({"m": "result", "view": "pet"})
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        return self._render_scene_frame(fr)
