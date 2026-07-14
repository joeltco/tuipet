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
import json
import os
from . import data
from .battle import Battle
from .theme import LCD_ON, LCD_BG, SIL_DAY, SIL_NIGHT  # noqa: F401  (palette names bound for theme.apply propagation)
from . import grid
from . import menu
from . import strikefx

COLS, ROWS = 40, 12
PXH = ROWS * 2                                   # 24 px tall
with open(os.path.join(os.path.dirname(__file__), "data", "battle_overlays.json")) as _f:
    _OV = json.load(_f)
BANNER = _OV["battle_banner"]
EXPLODE = _OV["hit_explosion"]

# poses (tuipet DVPet 11-frame layout)
IDLE, TURN, ATTACK, CHEER_A, CHEER_B, COLLAPSE = 0, 1, 6, 5, 7, 10
CHARGE = 4                                      # DVPet shoot frame 4: pre-attack/charge pose
# the 16px creature band on the 24px LCD (y6..y22); orbs must stay INSIDE it

# timeline tuning (ticks per beat, 1 tick == 0.1s); slowed for a readable vpet pace
BANNER_FLASHES, BANNER_HOLD = 3, 4
SKIP_DEBOUNCE = 6                                # anim ticks before a skip key registers
REVEAL_T = 12                                    # 1.2s opponent reveal/taunt (startBattle)
FACEOFF_T = 9                                    # 0.9s stare-down
WINDUP_T = 9                                     # 0.9s charge / rear-back before firing
FIRE_T = 12                                      # 1.2s per orb leg (~1.7px/tick, smooth glide)
EXPLODE_HOLD, EXPLODE_FRAMES = 3, 9              # 0.9s strobing hit flash
FLINCH_T = 12                                    # 1.2s held hurt pose
DODGE_T = 14                                     # 1.4s weave

OPTS = [("Vaccine", "Vaccine"), ("Data", "Data"), ("Virus", "Virus"), ("Surrender", None)]
# attack/defence chip effects -> a short on-screen label (DVPet AttackEffectProcess)
EFFECT_LABEL = {"DefenseUp": "Blocked!", "AttackUp": "Power up!", "Counter": "Counter!",
                "Weaken": "Weakened!", "DisableAttack": "Disabled!", "Leech": "Leech!",
                "Absorb": "Absorb!", "Heal": "Heal!", "First": "First strike!", "Second": "Second!"}


def round_timeline(ph0, fh0, pdmg, edmg, player_first, effect=None):
    """One round's alternating-view volley timeline, from PURE round data --
    shared by the PvE panel (which reads it off its Battle) and the lobby's
    PvP replay (which reads it off the relayed result; lobby audit 2026-07-04:
    PvP rounds were a text log while PvE plays the full animation)."""
    # strike order: initiative first; a KO'd side does not retaliate
    if player_first:
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
        fxn = effect if atk == "pet" else None           # only the player carries chip effects (PvE)
        for s in range(WINDUP_T):
            tl.append({"m": "windup", "view": atk, "atk": atk, "wu": s, "ph": ph, "fh": fh})
        for s in range(FIRE_T):                          # attacker shown: orb leaves off-screen
            tl.append({"m": "fire_out", "view": atk, "atk": atk, "double": dbl, "fx": fxn,
                       "prog": (s + 1) / FIRE_T, "ph": ph, "fh": fh})
        for s in range(FIRE_T):                          # defender shown: orb arrives off-screen
            tl.append({"m": "fire_in", "view": dfn, "atk": atk, "def": dfn, "double": dbl,
                       "prog": (s + 1) / FIRE_T, "ph": ph, "fh": fh})
        if dmg > 0:                                      # HIT: fullscreen flash, then flinch
            if dfn == "foe":
                fh = max(0, fh - dmg)
            else:
                ph = max(0, ph - dmg)
            for s in range(EXPLODE_FRAMES):
                tl.append({"m": "hit", "f": (s // EXPLODE_HOLD) % 2, "def": dfn, "double": dbl, "ph": ph, "fh": fh})
            tl += [{"m": "flinch", "view": dfn, "def": dfn, "ph": ph, "fh": fh}] * FLINCH_T
        else:                                            # DODGE: defender weaves, orb whiffs past
            for s in range(DODGE_T):
                tl.append({"m": "dodge", "view": dfn, "atk": atk, "def": dfn,
                           "prog": (s + 1) / DODGE_T, "ph": ph, "fh": fh})
    return tl


BOSSDIE_FLICKERS = 3                             # zoneBossDeath: 3 lit/dark cycles...
BOSSDIE_ON, BOSSDIE_OFF = 4, 2
BOSSDIE_STEP_T = 6                               # ...then a 3-step squash into the ground


def boss_death_timeline(ph):
    """SpriteAnim.zoneBossDeath: a beaten ZONE BOSS doesn't just explode -- it
    blinks out (three lights-flicker cycles over a shaken hurt pose, bossDying
    stings) and then SQUASHES into the ground in three steps (canon sizeY
    48->24->12->0 with the feet planted, bossDeath stings)."""
    tl = []
    for c in range(BOSSDIE_FLICKERS):
        for s in range(BOSSDIE_ON):
            tl.append({"m": "bossdie", "stage": "on", "jit": (c + s) % 2, "ph": ph, "fh": 0})
        tl += [{"m": "bossdie", "stage": "off", "ph": ph, "fh": 0}] * BOSSDIE_OFF
    for keep in (8, 4, 2):
        tl += [{"m": "bossdie", "stage": "squash", "keep": keep, "ph": ph, "fh": 0}] * BOSSDIE_STEP_T
    tl += [{"m": "bossdie", "stage": "off", "ph": ph, "fh": 0}] * 4
    return tl


def _squash_rows(rows, keep):
    """Vertical squash with the feet planted: sample `keep` rows across the
    sprite's height and pad the removed height with blank rows on top."""
    h = len(rows)
    if keep >= h:
        return rows
    idx = [round(i * (h - 1) / (keep - 1)) for i in range(keep)] if keep > 1 else [h - 1]
    w = max(len(r) for r in rows)
    return ["0" * w] * (h - keep) + [rows[i] for i in idx]


def _full(frame):
    # window-law: the 32x16 banner/flash fills the PLAY WINDOW exactly (like
    # training's explosion), not the whole LCD -- LCD-centring put its top two
    # rows in the bezel sky at y4-5 (audit 2026-07-13)
    w = len(frame[0]) if frame and frame[0] else 0
    ox = grid.X0 + max(0, (grid.W - w) // 2)
    oy = grid.TOP + max(0, (grid.BAND - len(frame)) // 2)
    return [(ox + x, oy + y) for y, row in enumerate(frame)
            for x, c in enumerate(row) if c == "1"]


# the creature-placement + grid helpers live in strikefx now (shared with training);
# keep the old module names as aliases so nothing downstream breaks.


class BattlePanel:
    def __init__(self, pet, enemy=None, wild=False):
        self.pet = pet
        self.wild = wild              # adventure PvE_Wild: Esc rolls canEscape, not surrender
        # BackgroundAnim checkBack: tournament + PvP battles play in the ARENA
        # (tourneyBack.png); wild + home battles keep the habitat scenery.  An
        # opponent supplied non-wild is exactly those two (townscreen/
        # tournamentscreen pass the bracket foe, the lobby passes the card).
        self.arena = enemy is not None and not wild
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.sel = 0
        self.pet_attr = None
        self.foe_attr = None
        self.done_anim = False
        self.won = None
        self.ran_away = False        # checkSurrender==1/accepted 2: it left the fight
        self.surrender_refused = False   # onSurrender: it wouldn't quit
        self.hud_php = self.battle.pet_hp
        self.hud_fhp = self.battle.enemy_hp
        self.hud_note = "Battle start!"
        self.phase = "intro"
        self.sfx = "battle"          # SoundConfig._battleFlash: the banner sting
        self._last_m = None          # tracks timeline marker edges for per-event sfx
        tl = []
        for _ in range(BANNER_FLASHES):
            tl += [{"m": "banner", "f": 0}] * BANNER_HOLD
            tl += [{"m": "banner", "f": 1}] * BANNER_HOLD
        # DVPet startBattle(): after the banner the OPPONENT is revealed alone,
        # taunting (drawNum 1 -> 6 -> 1 -> 6) with the _startBattle sting
        tl += [{"m": "reveal", "view": "foe"}] * REVEAL_T
        self.timeline = tl
        self.i = 0

    # ---- one round: pick attack, resolve, build the alternating-view timeline ----
    def _player_surrender(self):
        """ClockTic.onSurrender / Surrender_Validation: for a WILD (adventure)
        battle the Esc is an ESCAPE ATTEMPT -- canEscape's power-weighted roll;
        failing it FORCES a round ('tried to escape but failed', chooseAttack)
        and the fight goes on.  Elsewhere, giving up is the pet's to refuse --
        a proud one won't quit, opens the scold window, and fights the round
        its OWN way instead."""
        if self.wild:
            if self.pet.can_escape(self.battle.enemy):
                self.battle.surrender()          # the bout ends: neither win nor loss
                return ("done", None)
            self.sfx = "refuse"
            self.note = "Tried to escape… but failed!"
            self._resolve_and_build(self.battle._own_choice())
            return None
        if self.pet.check_refused():
            self.sfx = "refuse"
            self.surrender_refused = True        # the menu note shows the defiance
            self._resolve_and_build(self.battle._own_choice())
            return None
        self.battle.surrender()
        return ("done", None)

    def _resolve_and_build(self, attr):
        b = self.battle
        ph0, fh0 = b.pet_hp, b.enemy_hp
        b.play_round(attr)
        self.pet_attr = b.last_player_attr
        self.foe_attr = b.last_enemy_attr
        self.timeline = round_timeline(ph0, fh0, b.last_player_damage, b.last_enemy_damage,
                                       b.last_player_first, effect=b.last_effect)
        if b.over and b.won and (b.enemy or {}).get("boss"):
            self.timeline += boss_death_timeline(b.pet_hp)   # zoneBossDeath beat
        self.i = 0
        self.phase = "anim"

    def _enter_result(self):
        self.done_anim = True
        self.won = bool(self.battle.won)
        if self.ran_away and not self.won:
            self.battle.reward = f"{self.pet.name} fled the fight."
        self.phase = "result"

    # ---- driving ----
    def _emit_sfx(self):
        """Fire a one-shot beep at timeline marker edges: orb launch -> attack, impact -> hit."""
        entry = self.timeline[self.i]
        m = entry.get("m")
        if m == "bossdie":                       # canon soundConfig: bossDying ->
            prev = self.timeline[self.i - 1] if self.i else {}
            st = entry.get("stage")              # strongAttack, bossDeath -> attackHit
            if st == "on" and prev.get("stage") != "on":
                self.sfx = "strongAttack"
            elif st == "squash" and prev.get("keep") != entry.get("keep"):
                self.sfx = "attackHit"
        elif m != self._last_m:
            # DVPet: a doubleAttack launches AND lands with the strong stings
            s = strikefx.beat_sfx(m, entry.get("double"))
            if s:
                self.sfx = s
            elif m == "reveal":                  # setupBattle: _startBattle at the reveal
                self.sfx = "startBattle"
        self._last_m = m

    def anim(self):
        self.frame_i += 1
        if self.phase in ("menu", "result"):
            return
        if self.i < len(self.timeline) - 1:
            self.i += 1
            self._emit_sfx()
        elif self.phase == "intro":
            self.phase = "menu"
        else:
            if self.battle.over:
                self._enter_result()
            else:
                self._on_round_end()

    def _on_round_end(self):
        """ClockTic.onRoundEnd: after every resolved round the pet's morale
        rolls checkSurrender -- 0 fights on, 2 ASKS the trainer to quit, 1 it
        simply RUNS (scoldable)."""
        b = self.battle
        sv = self.pet.check_surrender(b.pet_hp, b.enemy_hp, b.enemy_max, b.pet_max)
        if sv == 2:
            self.phase = "surrender_ask"
            self.sfx = "refuse"
        elif sv == 1:
            self.pet.surrender_effect(1, b.pet_hp, b.enemy_hp)
            self.pet._open_scold()               # setScold(true): it fled without asking
            b.surrender()
            self.ran_away = True
            self._enter_result()
        else:
            self.phase = "menu"

    def strip(self):
        """The message-box hint line (hint overhaul 2026-07-10)."""
        if self.phase == "menu":
            return menu.hints(("1-3", "attack"), ("F", "style"),
                              ("4", "surrender"))
        if self.phase == "surrender_ask":
            return menu.hints(("ENTER", "allow"), ("ESC", "fight on"))
        if self.phase == "intro":
            return menu.hints(("SPACE", "skip"))
        if self.phase == "result":
            return menu.hints(("SPACE", "done"))
        return ""                              # the round animation plays clean

    def key(self, k):
        if self.phase == "intro":
            if k in ("space", "enter", "escape"):
                self.i = len(self.timeline) - 1
                self.phase = "menu"
            return None
        if self.phase == "surrender_ask":
            # Surrender_Validation: allow the quit, or send it back in
            if k in ("y", "enter"):
                b = self.battle
                self.pet.surrender_effect(2, b.pet_hp, b.enemy_hp)
                b.surrender()
                self.ran_away = True
                self._enter_result()
            elif k in ("n", "escape", "space"):
                self.pet.surrender_reject()      # sent back in: sulks, obeys a touch more
                self.sfx = "confirm"
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
            elif k == "4":                          # the 4th row: Surrender
                return self._player_surrender()
            elif k in ("enter", "space"):
                if OPTS[self.sel][1] is None:
                    return self._player_surrender()
                self._resolve_and_build(OPTS[self.sel][1])
            elif k == "s":
                return self._player_surrender()
            elif k == "f":
                # Battle_Style: Free (it fights its own way, +1 all powers)
                # vs Orders (your call; refusable, but discipline pays)
                self.pet.free_style = not self.pet.free_style
                self.sfx = "confirm"
            elif k == "escape":
                return ("done", None)
            return None
        if self.phase == "anim":
            # Joel 2026-07-05 ("it didn't play through to the death"): a fast
            # double-ENTER (pick + bounce) used to land here and vaporise the
            # whole round to the result.  Skips now (a) debounce the first
            # beats and (b) jump to the FINAL IMPACT, never past it -- even a
            # deliberate skip always shows the killing blow.
            if k in ("space", "enter", "escape") and self.i >= SKIP_DEBOUNCE:
                last = next((j for j in range(len(self.timeline) - 1, -1, -1)
                             if self.timeline[j]["m"] in ("hit", "dodge")), None)
                if last is None or self.i >= last - (EXPLODE_FRAMES + 2):
                    self.i = len(self.timeline) - 1   # already at the impact: finish
                else:
                    first = last
                    while first > 0 and self.timeline[first - 1]["m"] == self.timeline[last]["m"]:
                        first -= 1
                    self.i = first
            return None
        if k in ("space", "enter", "escape"):
            return ("done", self.battle)
        return None

    # ---- rendering ----
    def _rows(self, num, pose):
        rec = data.load_sprites()[1].get(num)
        if rec is None:
            # no roster sheet (an egg's num -1): render the shell art instead
            # of crashing -- the lobby PvP replay hit this live before the
            # session gates landed (egg-battle audit 2026-07-06)
            return data.bob_frame(num, pose,
                                  egg_type=getattr(self.pet, "egg_type", 0))
        fr = rec["frames"]
        return (fr[pose] if pose < len(fr) else None) or fr[0]

    def _scene(self, placements, overlay):
        # the habitat background is part of the scene -- the crisp sprites + orbs read fine
        # over it now (the clunk was the sprites/explosion, since fixed), so keep it visible.
        # clip: battle is a verified full-LCD 12-row canvas, so the window law
        # applies -- without it the orb visibly parked in the 4px margins on
        # every fire beat (audit 2026-07-13)
        return menu.paint(placements,
                          self.pet.background(file="tourneyBack" if self.arena else None),
                          rows=ROWS, cols=COLS, overlay=overlay, clip=grid.WINDOW)

    def _place_one(self, view, rows, xshift=0):
        """Place the ONE monster currently on screen. Player stands RIGHT (faces left), enemy
        LEFT (faces right). Returns (placements, mouth_edge) -- the inner edge the orb leaves
        from / arrives at."""
        # shared placement: pet (view!="foe") faces left on the right; foe faces right on the left
        return strikefx.place_combatant(view != "foe", rows, xshift)

    def _pow(self, side, attr):
        if side == "pet":
            return {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power,
                    "Virus": self.pet.virus}.get(attr, 0)
        e = self.battle.enemy
        return {"Vaccine": e.get("vaccine", 0), "Data": e.get("data_power", 0),
                "Virus": e.get("virus", 0)}.get(attr, 0)

    def _orb_overlay(self, fr, mouth):
        """The attacker's real orb, flown by the shared strikefx (player fires left, enemy
        fires right; the orb keeps a constant world direction across the screen switch)."""
        atk = fr["atk"]
        if atk == "pet":
            orb = data.attack_orb(self.pet.num, self.pet_attr, self._pow("pet", self.pet_attr),
                                  frame_i=self.frame_i)
        else:
            orb = data.attack_orb(self.battle.enemy["num"], self.foe_attr, self._pow("foe", self.foe_attr),
                                  frame_i=self.frame_i)
        return strikefx.orb_flight(orb, atk == "pet", fr["m"], fr["prog"], mouth, fr.get("double"))

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
        elif m == "bossdie":
            if fr["stage"] == "off":                     # lights-out beat: it blinks away
                scene = self._scene([], [])
            else:
                rows = self._rows(b.enemy["num"], COLLAPSE)
                if fr["stage"] == "squash":
                    rows = _squash_rows(rows, fr["keep"])
                xshift = (-1 if fr.get("jit") else 1) if fr["stage"] == "on" else 0
                place, _ = self._place_one("foe", rows, xshift)
                scene = self._scene(place, [])
            note = f"{b.enemy['name'][:12]} falls!"
        else:
            view = fr.get("view", "pet")
            dt = round(fr.get("prog", 0) * DODGE_T) if m == "dodge" else 0   # dodge beat 1..DODGE_T
            if m == "result":
                pose = (CHEER_A, CHEER_B)[(self.frame_i // 3) % 2] if self.won else COLLAPSE
            elif m == "windup":
                # DVPet battlePlayerShootAnim sequences poses 1->0->4 (ready->idle->charge)
                # through the wind-up, then snaps to 6 (attack) only at the moment of firing.
                pose = (TURN, TURN, IDLE, IDLE, CHARGE, CHARGE)[min(fr.get("wu", 0), 5)]
            elif m == "fire_out":
                pose = ATTACK
            elif m == "reveal":
                # DVPet startBattle: the opponent taunts 1 -> 6 -> 1 -> 6 before the menu
                pose = ATTACK if (self.frame_i // 3) % 2 else TURN
            elif m == "dodge":
                # airborne it holds its pose; canon flips 1/0/1 only on the return steps
                pose = IDLE if dt <= 10 else (TURN, TURN, IDLE, TURN)[dt - 11]
            elif m == "flinch":
                pose = COLLAPSE
            elif m == "fire_in":
                pose = CHARGE if (self.frame_i // 3) % 2 else IDLE  # DVPet defender bobs 0<->4 awaiting the orb
            else:                                            # faceoff
                pose = IDLE
            num = self.pet.num if view == "pet" else b.enemy["num"]
            rows = self._rows(num, pose)
            xshift = 0
            back = 1 if view == "pet" else -1                # +x = pet's wall (right), foe's (left)
            if m == "windup":
                xshift = back * min(3, fr.get("wu", 0) + 1)  # rear back, charging up
            elif m == "fire_out" and fr.get("prog", 1) < 0.35:
                xshift = -back * 2                           # lunge toward the foe on release
            elif m == "dodge" and 1 <= dt <= 10:
                # DVPet dodge(): LEAP toward its own wall AND UP, hang at the apex
                # while the shot whiffs past, then drop back to its mark (dt 11+)
                out, lift = ((2, 2), (3, 3), (3, 3), (3, 3), (3, 3), (3, 3),
                             (3, 3), (3, 3), (2, 1), (1, 0))[dt - 1]
                xshift = back * out
                # window-law: clamp the leap to the INK's headroom -- frames
                # carry transparent top padding, so the real art usually has
                # sky to hop into; pre-clamp the padded frame pushed ink to
                # y3-5, above the window top (audit 2026-07-13)
                top_pad = next((i for i, r in enumerate(rows) if "1" in r), 0)
                lift = max(0, min(lift, top_pad + max(0, grid.BAND - len(rows))))
                if lift:                                     # blank rows below raise it off the floor
                    rows = rows + ["0" * max(len(r) for r in rows)] * lift
            place, mouth = self._place_one(view, rows, xshift)
            # no orb on "dodge": canon hides the attack sprite -- the unhurt hop IS the miss
            overlay = self._orb_overlay(fr, mouth) if m in ("fire_out", "fire_in") else []
            scene = self._scene(place, overlay)
            note = {"faceoff": f"{self.pet.name[:8]} vs {b.enemy['name'][:8]}",
                    "reveal": f"{b.enemy['name'][:12]} appears!",
                    "windup": "...", "fire_out": "Fire!", "fire_in": "Incoming!",
                    "dodge": "Dodge!", "flinch": "Hit!", "result": ""}.get(m, "")
            if m == "result":
                from . import lines as _lines
                wg = _lines.win_gate_progress(self.pet)
                if wg:                               # every fight feeds the window
                    now, need, _win = wg
                    note = "evolution: %d/%d wins%s" % (
                        now, need, " \u2713" if now >= need else "")
            if fr.get("fx") and m == "fire_out":             # surface the player's chip effect
                note = EFFECT_LABEL.get(fr["fx"], fr["fx"])
        self.hud_php, self.hud_fhp, self.hud_note = ph, fh, note
        return scene

    def _render_menu(self):
        b = self.battle
        style = "FREE" if getattr(self.pet, "free_style", False) else "ORDERS"
        out = menu.header("BATTLE", f"vs {b.enemy['name'][:14]} · {style}")
        tag = " BOSS" if b.enemy.get("boss") else ""
        # the defiance notice gets its OWN line: appended to the HP line it fell
        # off menu.note's clip edge and never showed (audit 2026-07-04)
        ignored = "It IGNORED you!" if getattr(b, "refused_order", False) else ""
        if getattr(self, "surrender_refused", False):
            self.surrender_refused = False
            ignored = "It won't give up!"         # onSurrender: refuseSurrender
        out.append_text(menu.note(
            f"You HP {b.pet_hp}/{b.pet_max}   Foe HP {b.enemy_hp}/{b.enemy_max}{tag}"))
        out.append_text(menu.note(ignored) if ignored else menu.blanks(1))
        powr = {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power, "Virus": self.pet.virus}
        for i, (label, attr) in enumerate(OPTS):
            tagr = f"pow {powr[attr]}" if attr else ""
            out.append_text(menu.row(f"{label:<10} {tagr}", i == self.sel))
        out.append_text(menu.footer("↑↓ pick   ENTER attack   ESC surrender"))
        self.hud_php, self.hud_fhp, self.hud_note = b.pet_hp, b.enemy_hp, "Choose your attack"
        return out

    def text(self):
        if self.phase == "menu":
            return self._render_menu()
        if self.phase == "surrender_ask":
            out = menu.header("BATTLE", "it falters…")
            out.append_text(menu.blanks(1))
            out.append_text(menu.row(f"{self.pet.name} wants to give up!"))
            out.append_text(menu.blanks(3))
            out.append_text(menu.note("allow the retreat, or send it back in?"))
            out.append_text(menu.footer("ENTER allow   ESC fight on"))
            return out
        if self.phase == "result":
            return self._render_scene_frame({"m": "result", "view": "pet"})
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        return self._render_scene_frame(fr)
