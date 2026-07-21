"""Battle — the alternating-view volley show over the precomputed HP race
(the 0.5 battlescreen, ported 2026-07-17; DSprite is the ultimate truth
for animations and mechanics).

The fight itself is decided by battle.generate() (care, training, stage and
the attribute triangle feed each side's hit chance; the trained hit-type
sets damage).  This screen plays it back one round at a time: whoever fires
is shown alone, the orb flies off-screen, the defender dodges or eats the
blast.  Before the fight a TIMING BAR sets your hit-type for the bout —
good condition widens the mega window (care widens skill).
"""
from __future__ import annotations
import json
import os
from . import data
from .battle import Battle
from .theme import LCD_ON, LCD_BG, SIL_SCENE, SIL_LIGHTSOFF  # noqa: F401  (palette names bound for theme.apply propagation)
from . import grid
from . import menu
from . import strikefx

COLS, ROWS = 40, 12
PXH = ROWS * 2                                   # 24 px tall
with open(os.path.join(os.path.dirname(__file__), "data", "battle_overlays.json")) as _f:
    _OV = json.load(_f)
BANNER = _OV["battle_banner"]


def _hit_explode():
    """The hit flash: the source's Hit_1 blast blinked against blank (its
    renderer strobes it at 100ms).  The skull-and-crossbones that strobed
    here before was the OLD game's KO marker riding along in
    battle_overlays.json (v0.2-era) while the clone's real blast sat unused
    in battle_fx["hit"] (Joel 2026-07-15: training audit)."""
    e = data.load_battle_fx().get("hit", {}).get("Hit_1")
    if not isinstance(e, dict):
        return _OV["hit_explosion"]              # cross-version fallback
    w, h = int(e.get("width", 32)), int(e.get("height", 16))
    px = e.get("sprite") or []
    if len(px) < w * h:
        return _OV["hit_explosion"]
    rows = ["".join("1" if px[y * w + x] else "0" for x in range(w))
            for y in range(h)]
    return [rows, ["0" * w] * h]                 # frame 1 = the blink's OFF beat


EXPLODE = _hit_explode()

# poses (tuipet the classic V-pet 11-frame layout)
IDLE, TURN, ATTACK, CHEER_A, CHEER_B, COLLAPSE, WEARY = 0, 1, 6, 5, 7, 10, 9
CHARGE = 4                                      # the classic V-pet shoot frame 4: pre-attack/charge pose
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

BAR_MAX = 24                                     # the timing bar sweeps 0..24


def mega_window(pet):
    """Care widens the skill ceiling: condition score -> the mega zone
    [12-c, 12+c] on the 0..24 bar (width 1/3/5/7); ±5 around it = normal.
    (Classic gauges: flat 4-heart meters, age off the world clock.)"""
    from .pet import DAY_LENGTH
    wr = pet.wins / pet.battles if pet.battles > 0 else 0
    hu = pet.hunger / 4.0
    st = pet.strength / 4.0
    en = max(0, pet.energy) / pet.max_energy if pet.max_energy else 0
    ag = min((pet.age_seconds / DAY_LENGTH) / 5, 1)
    o = min(1.0, wr * 0.2 + hu * 0.2 + st * 0.2 + ag * 0.2 + en * 0.2)
    w = 1 + int(o * 3) * 2
    c = w // 2
    return 12 - c, 12 + c


def round_timeline(ph0, fh0, pdmg, edmg, player_first, effect=None,
                   hold_foe_bar=False):
    """One round's alternating-view volley timeline, from PURE round data --
    shared by the PvE panel (which reads it off its Battle) and the lobby's
    PvP replay (which reads it off the relayed result; lobby audit 2026-07-04:
    PvP rounds were a text log while PvE plays the full animation)."""
    # strike order: initiative first.  The ENGINE is simultaneous -- both
    # sides' landed blows are already on record -- so a KO'd side's strike
    # is only hidden when it MISSED (pure presentation, nothing applied).
    # Suppressing a landed one showed the pet losing HP with no animation:
    # the next page's true bar didn't match the replay (audit 2026-07-19).
    if player_first:
        seq = [("pet", "foe", pdmg)]
        if fh0 - max(0, pdmg) > 0 or edmg > 0:
            seq.append(("foe", "pet", edmg))
    else:
        seq = [("foe", "pet", edmg)]
        if ph0 - max(0, edmg) > 0 or pdmg > 0:
            seq.append(("pet", "foe", pdmg))
    tl = []
    ph, fh = ph0, fh0
    tl += [{"m": "faceoff", "view": seq[0][0], "ph": ph, "fh": fh}] * FACEOFF_T
    for atk, dfn, dmg in seq:
        other = edmg if atk == "pet" else pdmg
        dbl = dmg >= 2 and dmg >= other                  # the classic V-pet doubleAttack: strong & out/matching power
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
                if not hold_foe_bar:      # a raid boss's bar NEVER falls: the old
                    #  in-round dip snapped back to full at the next round's frames
                    fh = max(0, fh - dmg)
            else:
                ph = max(0, ph - dmg)
            # device-exact (GML 2026-07-14): the hit STING is skipped on the
            # final winning blow -- the KO presentation carries the audio
            final = dfn == "foe" and fh == 0
            for s in range(EXPLODE_FRAMES):
                tl.append({"m": "hit", "f": (s // EXPLODE_HOLD) % 2, "def": dfn,
                           "double": dbl, "final": final, "ph": ph, "fh": fh})
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
    blank = "0" * w if isinstance(rows[0], str) else [None] * w
    return [blank] * (h - keep) + [rows[i] for i in idx]


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
    def __init__(self, pet, enemy=None, wild=False, scene=None, rounds=None,
                 raid=False):
        from .battle import ROUNDS_LOCAL
        self.pet = pet
        self.raid = raid              # a RaidBout replay: boss bar holds, dealt counts
        self.wild = wild              # adventure wilds: ESC before the bell = flee
        # tournament + PvP battles play in the ARENA; home battles keep the
        # picked scene; adventure wilds pass the ROAD's biome scene via
        # `scene` (the road says where the fight is).
        self.arena = enemy is not None and not wild
        self.scene = scene
        self._rounds = rounds or ROUNDS_LOCAL
        self._enemy = enemy
        self.battle = None            # built AFTER the timing bar locks
        self.frame_i = 0
        self.pet_attr = pet.attribute
        self.foe_attr = None
        self.done_anim = False
        self.won = None
        self.ran_away = False
        self.hud_php = self.hud_fhp = 5
        self.hud_note = "Battle start!"
        self.phase = "intro"
        self.sfx = "battle"          # the banner sting
        self._last_m = None          # timeline marker edges -> per-event sfx
        self.bar = 0                 # the timing bar
        self.bar_dir = 1
        self.mega_lo, self.mega_hi = mega_window(pet)
        self.locked = None           # the locked hit-type
        tl = []
        for _ in range(BANNER_FLASHES):
            tl += [{"m": "banner", "f": 0}] * BANNER_HOLD
            tl += [{"m": "banner", "f": 1}] * BANNER_HOLD
        tl += [{"m": "reveal", "view": "foe"}] * REVEAL_T
        self.timeline = tl
        self.i = 0
        # the reveal needs the foe on screen before the fight exists
        from . import battle as battle_mod
        self._pick = enemy if enemy is not None else battle_mod.pick_enemy(pet)
        self.foe_attr = self._pick.get("attribute", "Free")

    @property
    def enemy(self):
        return self.battle.enemy if self.battle else self._pick

    def _start_fight(self, hit_type):
        """The bar locked: build the precomputed fight and roll the rounds."""
        self.pet.saved_hit_type = hit_type
        self.locked = hit_type
        if self.raid:
            from .battle import RaidBout
            self.battle = RaidBout(self.pet, self._pick)
        else:
            self.battle = Battle(self.pet, self._pick, rounds=self._rounds,
                                 source="pvp" if self.arena and not self.wild
                                 and self._pick.get("pvp") else "battle")
        self.hud_php, self.hud_fhp = self.battle.pet_hp, self.battle.enemy_hp
        self._next_round()

    def _next_round(self):
        b = self.battle
        ph0, fh0 = b.pet_hp, b.enemy_hp
        rec = b.play_round()
        if rec is None:
            self._enter_result()
            return
        self.timeline = round_timeline(ph0, fh0, rec["pdmg"], rec["edmg"],
                                       True, hold_foe_bar=self.raid)
        # the death beat is for a boss BEATEN TO ZERO -- won alone would fire
        # it on a survived raid, whose boss never falls
        if b.over and b.won and (b.enemy or {}).get("boss") and b.enemy_hp <= 0:
            self.timeline += boss_death_timeline(b.pet_hp)   # boss-death beat
        self.i = 0
        self.phase = "anim"

    def _enter_result(self):
        self.done_anim = True
        self.won = bool(self.battle.won) if self.battle else False
        self.phase = "result"

    # ---- driving ----
    def _emit_sfx(self):
        """A one-shot beep at timeline marker edges."""
        entry = self.timeline[self.i]
        m = entry.get("m")
        if m == "bossdie":
            prev = self.timeline[self.i - 1] if self.i else {}
            st = entry.get("stage")
            if st == "on" and prev.get("stage") != "on":
                self.sfx = "strongAttack"
            elif st == "squash" and prev.get("keep") != entry.get("keep"):
                self.sfx = "attackHit"
        elif m != self._last_m:
            s = (None if m == "hit" and entry.get("final")
                 else strikefx.beat_sfx(m, entry.get("double")))
            if s:
                self.sfx = s
            elif m == "reveal":
                self.sfx = "startBattle"
        self._last_m = m

    def anim(self):
        self.frame_i += 1
        if self.phase == "ready":
            self.bar += self.bar_dir
            if self.bar >= BAR_MAX or self.bar <= 0:
                self.bar_dir = -self.bar_dir
                self.bar = max(0, min(BAR_MAX, self.bar))
            return
        if self.phase == "result":
            return
        if self.i < len(self.timeline) - 1:
            self.i += 1
            self._emit_sfx()
        elif self.phase == "intro":
            self.phase = "ready"
        else:
            if self.battle is None or self.battle.over:
                self._enter_result()
            else:
                self._next_round()

    def strip(self):
        """The message-box hint line."""
        if self.phase == "ready":
            return menu.hints(("SPACE", "lock the bar"),
                              ("ESC", "flee" if self.wild else "back out"))
        if self.phase == "intro":
            return menu.hints(("SPACE", "skip"))
        if self.phase == "result":
            return menu.hints(("SPACE", "done"))
        return ""                              # the round animation plays clean

    def _lock_bar(self):
        if self.pet.battles >= 999 or self.mega_lo <= self.bar <= self.mega_hi:
            t = "mega"
        elif self.mega_lo - 5 <= self.bar <= self.mega_hi + 5:
            t = "normal"
        else:
            t = "miss"
        self.sfx = "confirm" if t != "miss" else "refuse"
        self._start_fight(t)

    def key(self, k):
        if self.phase == "intro":
            if k in ("space", "enter", "escape"):
                self.i = len(self.timeline) - 1
                self.phase = "ready"
            return None
        if self.phase == "ready":
            if k in ("space", "enter"):
                self._lock_bar()
            elif k == "escape":
                self.ran_away = True
                return ("done", None)          # walked away before the bell
            return None
        if self.phase == "anim":
            if k in ("space", "enter", "escape") and self.i >= SKIP_DEBOUNCE:
                last = next((j for j in range(len(self.timeline) - 1, -1, -1)
                             if self.timeline[j]["m"] in ("hit", "dodge")), None)
                if last is None or self.i >= last - (EXPLODE_FRAMES + 2):
                    self.i = len(self.timeline) - 1   # already at the impact
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
        rec = data.record_for(num) if num >= 0 else None
        if rec is None or rec.get("_placeholder"):
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
                          self.pet.background(
                              file=self.scene if self.scene is not None
                              else ("tourneyBack" if self.arena else None)),
                          rows=ROWS, cols=COLS, overlay=overlay, clip=grid.WINDOW)

    def _place_one(self, view, rows, xshift=0):
        """Place the ONE monster currently on screen. Player stands RIGHT (faces left), enemy
        LEFT (faces right). Returns (placements, mouth_edge) -- the inner edge the orb leaves
        from / arrives at."""
        # shared placement: pet (view!="foe") faces left on the right; foe faces right on the left
        return strikefx.place_combatant(view != "foe", rows, xshift)

    def _orb_overlay(self, fr, mouth):
        """The attacker's projectile flown by the shared strikefx, tinted
        with the firing mon's own hue (audit 2026-07-15)."""
        atk = fr["atk"]
        num = self.pet.num if atk == "pet" else self.enemy.get("num", 0)
        attr = self.pet_attr if atk == "pet" else self.foe_attr
        orb = data.attack_orb(num, attr, 0, frame_i=self.frame_i)
        # (the clone's per-mon colour tint stays behind: this tree is mono)
        return strikefx.orb_flight(orb, atk == "pet", fr["m"], fr["prog"],
                                   mouth, fr.get("double"))

    def _render_scene_frame(self, fr):
        b = self.battle
        m = fr["m"]
        ph = fr.get("ph", b.pet_hp if b else 5)
        fh = fr.get("fh", b.enemy_hp if b else 5)
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
                rows = self._rows(self.enemy["num"], COLLAPSE)
                if fr["stage"] == "squash":
                    rows = _squash_rows(rows, fr["keep"])
                xshift = (-1 if fr.get("jit") else 1) if fr["stage"] == "on" else 0
                place, _ = self._place_one("foe", rows, xshift)
                scene = self._scene(place, [])
            note = f"{self.enemy['name'][:12]} falls!"
        else:
            view = fr.get("view", "pet")
            dt = round(fr.get("prog", 0) * DODGE_T) if m == "dodge" else 0   # dodge beat 1..DODGE_T
            if m == "result":
                # defeat ALTERNATES collapse/weary like the win alternates its
                # cheer -- every reference flips the loser's injured pair; a
                # held pose read as a freeze (anim hardening 2026-07-14)
                pose = ((CHEER_A, CHEER_B) if self.won
                        else (COLLAPSE, WEARY))[(self.frame_i // 3) % 2]
            elif m == "windup":
                # the classic V-pet battlePlayerShootAnim sequences poses 1->0->4 (ready->idle->charge)
                # through the wind-up, then snaps to 6 (attack) only at the moment of firing.
                pose = (TURN, TURN, IDLE, IDLE, CHARGE, CHARGE)[min(fr.get("wu", 0), 5)]
            elif m == "fire_out":
                pose = ATTACK
            elif m == "reveal":
                # the classic V-pet startBattle: the opponent taunts 1 -> 6 -> 1 -> 6 before the menu
                pose = ATTACK if (self.frame_i // 3) % 2 else TURN
            elif m == "dodge":
                # airborne it holds its pose; canon flips 1/0/1 only on the return steps
                pose = IDLE if dt <= 10 else (TURN, TURN, IDLE, TURN)[dt - 11]
            elif m == "flinch":
                pose = COLLAPSE
            elif m == "fire_in":
                pose = CHARGE if (self.frame_i // 3) % 2 else IDLE  # the classic V-pet defender bobs 0<->4 awaiting the orb
            else:                                            # faceoff
                pose = IDLE
            num = self.pet.num if view == "pet" else self.enemy["num"]
            rows = self._rows(num, pose)
            xshift = 0
            back = 1 if view == "pet" else -1                # +x = pet's wall (right), foe's (left)
            if m == "windup":
                xshift = back * min(3, fr.get("wu", 0) + 1)  # rear back, charging up
            elif m == "fire_out" and fr.get("prog", 1) < 0.35:
                xshift = -back * 2                           # lunge toward the foe on release
            elif m == "dodge" and 1 <= dt <= 10:
                # the classic V-pet dodge(): LEAP toward its own wall AND UP, hang at the apex
                # while the shot whiffs past, then drop back to its mark (dt 11+)
                out, lift = ((2, 2), (3, 3), (3, 3), (3, 3), (3, 3), (3, 3),
                             (3, 3), (3, 3), (2, 1), (1, 0))[dt - 1]
                xshift = back * out
                # window-law: clamp the leap to the INK's headroom -- frames
                # carry transparent top padding, so the real art usually has
                # sky to hop into; pre-clamp the padded frame pushed ink to
                # y3-5, above the window top (audit 2026-07-13)
                top_pad = next((i for i, r in enumerate(rows)
                                if any(grid.lit(c) for c in r)), 0)
                lift = max(0, min(lift, top_pad + max(0, grid.BAND - len(rows))))
                if lift:                                     # blank rows below raise it off the floor
                    w = max(len(r) for r in rows)
                    blank = "0" * w if isinstance(rows[0], str) else [None] * w
                    rows = list(rows) + [blank] * lift
            place, mouth = self._place_one(view, rows, xshift)
            # no orb on "dodge": canon hides the attack sprite -- the unhurt hop IS the miss
            overlay = self._orb_overlay(fr, mouth) if m in ("fire_out", "fire_in") else []
            scene = self._scene(place, overlay)
            note = {"faceoff": f"{self.pet.name[:8]} vs {self.enemy['name'][:8]}",
                    "reveal": f"{self.enemy['name'][:12]} appears!",
                    "windup": "...", "fire_out": "Fire!", "fire_in": "Incoming!",
                    "dodge": "Dodge!", "flinch": "Hit!", "result": ""}.get(m, "")
            if m == "result":
                note = f"record {self.pet.wins}W/{self.pet.battles}"
        self.hud_php, self.hud_fhp, self.hud_note = ph, fh, note
        return scene

    def _render_ready(self):
        """The timing bar: a marker sweeps 0..24; SPACE locks it.  Inside the
        mega zone = double blasts most rounds; near it = normal; wide = miss.
        Rendered as the CANON pixel bar over the arena -- the same sprite as
        the training drill (strikefx.timing_bar; Joel 2026-07-19: 'the slide
        bar should be the same sprite as the training slide bar' -- the old
        text-glyph page was the one bar that looked nothing like it).  The
        strip carries SPACE/ESC; the status card carries the coaching."""
        self.hud_php, self.hud_fhp = 5, 5
        self.hud_note = "Set your timing!  (good care widens the mega zone)"
        return self._scene([], strikefx.timing_bar(self.bar, self.mega_lo,
                                                   self.mega_hi))

    def text(self):
        if self.phase == "ready":
            return self._render_ready()
        if self.phase == "result":
            return self._render_scene_frame({"m": "result", "view": "pet"})
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        return self._render_scene_frame(fr)
