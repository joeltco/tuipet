"""Battle View — clean single-screen pose animation (wayland style).

Presentation follows wayland-vpets' approach: the Digimon are shown together on one
screen and the fight reads through their POSES cycling (idle -> attack lunge -> the
outcome cheer/collapse), NOT DVPet's orb-clash spectacle (no projectiles, no fullscreen
explosions, no HP bars on the LCD, no attacker/defender view-switching).  The bout is
resolved by the DM20 engine (battle.py: Power + the attribute triangle); this just
animates it.  Player stands RIGHT (faces left), enemy LEFT (faces right).

Flow: face-off -> attack-order minigame (time your strike) -> a short pose flurry ->
the result pose.  You do NOT pick an attribute; your Digimon's is fixed.
"""
from __future__ import annotations
from . import data
from .battle import Battle
from .render import render_scene
from .theme import LCD_ON, LCD_BG, SIL_DAY, SIL_NIGHT

COLS, ROWS = 40, 12
PXH = ROWS * 2                                   # 24 px tall

# the authentic 32-wide play window, centred inside the 40-wide LCD canvas.
PLAY_COLS = 32
PLAY_X0 = (COLS - PLAY_COLS) // 2                # 4
PLAY_R = PLAY_X0 + PLAY_COLS                     # 36

# poses, DVPet native frame order (matches the bundled crisp DVPet atlas):
# 0 idle  1 idle-B  2 sleep  3 stretch  4 cheer-down  5 excited  6 attack
# 7 eat-chew  8 eat-swallow  9 dejected  10 collapse
IDLE, IDLE_B, ATTACK, CHEER_UP, CHEER_DN, COLLAPSE = 0, 1, 6, 5, 4, 10

# timing (ticks, 1 == 0.1s) -- brief and readable
FACEOFF_T = 8                                    # 0.8s square-off before the minigame
CLASH_BEAT = 4                                   # pose held per beat
CLASH_EXCHANGES = 4                              # attack lunges in the flurry
LUNGE = 3                                        # px the mon leans in on its attack beat
MG_SPEED = 0.06                                  # attack-order marker travel per tick
MG_ZONE = 0.14                                   # half-width of the "strike first" zone


def _cbounds(rows):
    w = max(len(r) for r in rows)
    cols = [x for x in range(w) if any(x < len(r) and r[x] == "1" for r in rows)]
    return (min(cols), max(cols)) if cols else (0, w - 1)


class BattlePanel:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.done_anim = False
        self.won = None
        self.hud_php = self.battle.pet_hp
        self.hud_fhp = self.battle.enemy_hp
        self.hud_note = "Battle start!"
        self.phase = "faceoff"
        self.sfx = "battle"
        # attack-order minigame
        self.mg_pos = 0.0
        self.mg_dir = 1
        self.mg_result = None
        self._t = 0                              # phase-local tick counter
        self._clash_len = 0

    # ---- driving ----
    def _start_clash(self, player_first):
        self.battle.resolve(player_first=player_first)
        self.hud_php, self.hud_fhp = self.battle.pet_hp, self.battle.enemy_hp
        self._clash_len = FACEOFF_T + CLASH_EXCHANGES * 2 * CLASH_BEAT
        self._t = 0
        self.phase = "clash"

    def anim(self):
        self.frame_i += 1
        self._t += 1
        if self.phase == "faceoff":
            if self._t >= FACEOFF_T:
                self.phase, self._t = "minigame", 0
        elif self.phase == "minigame":
            self.mg_pos += self.mg_dir * MG_SPEED
            if self.mg_pos >= 1.0:
                self.mg_pos, self.mg_dir = 1.0, -1
            elif self.mg_pos <= 0.0:
                self.mg_pos, self.mg_dir = 0.0, 1
        elif self.phase == "clash":
            # one attack "clink" sound near the middle of each exchange
            if self._t > FACEOFF_T and (self._t - FACEOFF_T) % (2 * CLASH_BEAT) == CLASH_BEAT:
                self.sfx = "attack"
            if self._t >= self._clash_len:
                self.done_anim = True
                self.won = bool(self.battle.won)
                self.sfx = "win" if self.won else "lose"
                self.phase, self._t = "result", 0

    def key(self, k):
        if self.phase == "faceoff":
            if k in ("space", "enter"):
                self._t, self.phase = 0, "minigame"
            elif k == "escape":
                self.battle.surrender()
                return ("done", None)
            return None
        if self.phase == "minigame":
            if k in ("space", "enter"):
                self.mg_result = abs(self.mg_pos - 0.5) <= MG_ZONE
                self.sfx = "confirm"
                self._start_clash(self.mg_result)
            elif k in ("escape", "s"):
                self.battle.surrender()
                return ("done", None)
            return None
        if self.phase == "clash":
            if k in ("space", "enter", "escape"):
                self._t = self._clash_len            # skip to the result
            return None
        if k in ("space", "enter", "escape"):
            return ("done", self.battle)
        return None

    # ---- rendering ----
    def _rows(self, num, pose):
        fr = data.load_sprites()[1][num]["frames"]
        return (fr[pose] if pose < len(fr) else None) or fr[0]

    def _one(self, view, pose, dx=0):
        """ONE Digimon on screen at a time, centred in the play window -- NEVER two sprites
        sharing the LCD (two 16px mons don't fit a 32px window without overlapping).  The
        pet faces left, the enemy faces right; `dx` nudges it (a small attack lunge)."""
        num = self.pet.num if view == "pet" else self.battle.enemy["num"]
        rows = self._rows(num, pose)
        mirror = (view == "foe")
        src = [r[::-1] for r in rows] if mirror else rows
        lo, hi = _cbounds(src)
        w = hi - lo + 1
        x = PLAY_X0 + (PLAY_COLS - w) // 2 - lo + dx         # centre the mon's ink
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        return render_scene([(rows, x, mirror)], COLS, ROWS, on, LCD_BG, bgimg=bgimg,
                            clip=(PLAY_X0, PLAY_R))

    def text(self):
        b = self.battle
        if self.phase == "faceoff":                          # the wild foe appears
            self.hud_note = f"vs {b.enemy['name'][:12]}"
            bob = IDLE_B if (self.frame_i // 3) % 2 else IDLE
            return self._one("foe", bob)
        if self.phase == "minigame":                         # your Digimon readies up
            self.hud_note = "Time your strike!"
            return self._one("pet", IDLE)
        if self.phase == "clash":
            # ONE mon at a time: the striker is shown alone in its attack pose, lunging
            # forward; then the other. No projectiles, no overlap.
            k = (self._t - FACEOFF_T) // CLASH_BEAT if self._t > FACEOFF_T else 0
            if k % 2 == 0:
                self.hud_note = f"{self.pet.name[:10]} strikes!"
                return self._one("pet", ATTACK, dx=-LUNGE)   # pet lunges left
            self.hud_note = f"{b.enemy['name'][:10]} strikes!"
            return self._one("foe", ATTACK, dx=LUNGE)        # foe lunges right
        # result: the winner cheers alone (up/down bounce), or you collapse
        self.hud_note = ""
        if self.won:
            cheer = CHEER_UP if (self.frame_i // 4) % 2 else CHEER_DN
            return self._one("pet", cheer)
        return self._one("pet", COLLAPSE)

    def minigame_cells(self, width=14):
        """(marker_index, zone_lo, zone_hi) for the status-HUD attack-order track."""
        pos = int(round(self.mg_pos * (width - 1)))
        zone_lo = int(round((0.5 - MG_ZONE) * (width - 1)))
        zone_hi = int(round((0.5 + MG_ZONE) * (width - 1)))
        return pos, zone_lo, zone_hi
