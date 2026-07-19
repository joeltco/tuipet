"""RAID — the community boss fight, on its own action key (BASIC VPET
2026-07-16; ported from the DSprite rebuild and given the sprite-rich screen
Joel asked for: the BOSS stands on the arena, not in a text menu).

One boss stands per rotation with a SHARED HP pool on the relay (energy_max
x 5.5M).  Every tamer gets 3 attempts a day: an attempt is the clone's
generate_raid (0.5 BATTLE 2026-07-17) — a 10-round volley from
RAID_PLAYER_HP against a boss that never falls locally, replayed through
the real battlescreen (the sprites Joel demanded).  The raw damage landed
is reported and the relay multiplies it against the pool (x5000 x
stage-mult, bound server-side to the card's num).  The volley writes
NOTHING on the pet's record.  When the community breaks the pool, the
board archives and pays on claim — and a felled boss is a Mega down: the
claim counts KO6 and the raids egg-unlock channel.
"""
from __future__ import annotations
from . import data, grid, persistence
from .battlescreen import BattlePanel
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, NEG, POS, COIN  # noqa: F401  (theme.apply propagation)
from . import menu

COLS, ROWS = 40, 12


def _fmt(n):
    """Board damage is raw x5000 x mult — millions.  Keep it readable."""
    n = int(n)
    if n >= 10_000_000:
        return f"{n // 1_000_000}M"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n // 1_000}k"
    return str(n)


class RaidPanel(menu.SubHost):
    def __init__(self, pet, connect, client=None):
        self.pet = pet
        self.sub = None
        self.frame_i = 0
        self.sfx = None
        self.msg = "Calling the raid gate…"
        self._dealt = 0
        self._credited = 0            # the gate's acked board damage this session
        name, pw = persistence.get_account()
        self.client = client or connect(name, pw, {"num": pet.num,
                                                   "name": pet.name or name})
        self._asked = False

    # ---- data ----
    @property
    def view(self):
        return getattr(self.client, "raid", None)

    def _boss(self):
        v = self.view or {}
        return v.get("boss") or {}

    def _standing(self):
        """The boss takes hits: announced (start passed) and pool > 0."""
        v = self.view or {}
        b = self._boss()
        return bool(b) and b.get("start", 0) <= v.get("now", 0) \
            and b.get("hp", 0) > 0

    def anim(self):
        if self.sub_anim():
            return
        self.frame_i += 1
        if not self._asked and getattr(self.client.state, "me_id", None) is not None:
            self.client.raid_get()
            self._asked = True
        elif self._asked and self.frame_i % 50 == 0:
            # keep the countdown/pool/board LIVE while the panel is open --
            # the one-shot fetch froze every timer until the player acted
            # (raid review 2026-07-18); one refetch per ~5s is polite
            self.client.raid_get()
        if self.view and self.msg == "Calling the raid gate…":
            self.msg = "The boss stands. SPACE to raid!" if self._standing() \
                else "The next boss is incoming…"
        hit = getattr(self.client, "last_hit", None)
        if hit is not None:
            # the gate's authoritative credit (raw x5000 x num-mult) -- the
            # panel used to show only the local raw and discard this ack
            # (audit 2026-07-18)
            self.client.last_hit = None
            dealt = int(hit.get("dealt", 0) or 0)
            if dealt > 0:
                self._credited += dealt
                self.msg = f"Gate credits {dealt:,} damage!"
                self.sfx = "attackHit"
            else:
                # the gate REFUSED the report (boss fell/expired mid-bout) --
                # the old flow left "reported!" standing (raid review 2026-07-18)
                self.msg = "The gate refused it — the boss is gone. Refetching…"
                self.client.raid_get()
        reward = getattr(self.client, "raid_reward", None)
        if reward is not None:
            self.client.raid_reward = None
            self._apply_reward(reward)

    def _apply_reward(self, reward):
        if not reward.get("ok"):
            self.msg = "Nothing to claim."
            self.sfx = "error"
            return
        bits = int(reward.get("bits", 0))
        self.pet.bits += bits
        got = list(reward.get("items") or [])
        for key in got:
            self.pet.add_item(key)
        if reward.get("defeated"):
            # the felled boss is a Mega down for everyone on the board: the
            # claim pays the KO6 counter and the raids egg-unlock channel
            self.pet.mega_kills += 1
            persistence.mega_kills_add(1)
            persistence.raid_add()
            cat = data.load_vitems()
            names = ", ".join(cat.get(k, {}).get("name", k) for k in got) \
                if got else ""
            self.msg = f"{reward.get('boss', 'The boss')} fell! " \
                       f"Rank {reward.get('rank', '?')}: {bits}b" \
                       + (f" + {names}" if names else "")
            self.sfx = "champion"
        else:
            self.msg = f"The boss escaped… {bits}b consolation."
            self.sfx = "confirm"

    def strip(self):
        if self.sub is not None:
            return ""
        return menu.hints(("SPACE", "raid!"), ("C", "claim"), ("ESC", "out"))

    # ---- the attempt ----
    def _boss_enemy(self):
        b = self._boss()
        num = int(b.get("num", -1))
        rec = data.record_for(num)
        return {"num": num, "name": b.get("name", rec.get("name", "?")),
                "stage": rec.get("stage", "Mega"),
                "attribute": rec.get("attribute", "Free"), "boss": True}

    def _report(self, b):
        dealt = int(getattr(b, "dealt", 0) or 0) if b is not None else 0
        if dealt > 0 and self.view:
            self.client.raid_hit(dealt, self.pet.stage)
            self._dealt += dealt
            # NEUTRAL until the ack lands: "reported!" used to stand even
            # when the gate rejected it or the socket was down (raid review
            # 2026-07-18); the ack path speaks the credit or the refusal
            self.msg = f"Landed {dealt} — reporting to the gate…"
        else:
            self.msg = "Not a scratch. Rest and try again."

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.sub = None
                self._report(r[1])
            return None
        if k in ("space", "enter"):
            v = self.view
            if not v:
                self.msg = "The gate hasn't answered yet…"
                self.client.raid_get()
                return None
            if not self._standing():
                self.msg = "The boss is not standing."
                self.sfx = "error"
                return None
            if int(v.get("attempts", 0)) <= 0:
                self.msg = "No attempts left today."
                self.sfx = "error"
                return None
            # the clone raid bout: RaidBout precomputes generate_raid and
            # the battlescreen replays it (records nothing on the pet)
            self.sub = BattlePanel(self.pet, self._boss_enemy(), raid=True)
            return None
        if k in ("c", "C"):        # both cases, like the lobby's letter keys
            award = (self.view or {}).get("award")
            if award:
                self.client.raid_claim(award["id"])
                self.msg = "Claim sent…"
            else:
                self.msg = "Nothing to claim yet."
            return None
        if k in ("escape", "r"):
            # the exit line speaks the GATE's number (board damage), not the
            # raw accumulator -- three magnitudes described one session
            # (raid review 2026-07-18)
            if self._credited:
                done = f"Raid: the gate credited {self._credited:,} damage."
            elif self._dealt:
                done = f"Raid: {self._dealt} raw landed — no gate credit yet."
            else:
                done = None
            return ("done", done)
        return None

    # ---- render ----
    def text(self):
        if self.sub is not None:
            return self.sub.text()
        v = self.view
        b = self._boss()
        if not v or not b:
            out = menu.header("RAID", "…")
            out.append_text(menu.blanks(4))
            out.append_text(menu.note(self.msg, tick=self.frame_i))
            out.append_text(menu.blanks(4))
            out.append_text(menu.footer("ESC out"))
            return out
        num = int(b.get("num", -1))
        # the BOSS looms on the arena, breathing on the walk beat -- the whole
        # point of taking raids out of the lobby's text page
        rows = data.bob_frame(num, self.frame_i,
                              "attack" if (self.frame_i // 9) % 4 == 3 else "idle")
        placements = [(grid.prep(rows, ph=ROWS * 2),
                       grid.X0 + (grid.W - grid.width(grid.prep(rows, ph=ROWS * 2))) // 2,
                       False)] if rows else []
        bgimg = self.pet.background(file="tourneyBack")
        scene = render_scene(placements, COLS, ROWS - 4, menu.scene_ink(bgimg),
                             LCD_BG, bgimg=bgimg, clip=grid.WINDOW)
        pool, pool_max = int(b.get("hp", 0)), max(1, int(b.get("max_hp", 1)))
        pct = max(0, min(100, pool * 100 // pool_max))
        bar = "█" * (pct * 24 // 100)
        stage = data.record_for(num).get("stage", "Mega")
        out = menu.bar(f"RAID · {b.get('name', '?')[:14]}", stage[:8])
        out.append_text(scene)
        out.append("\n")
        if not self._standing():
            left = max(0, int(b.get("start", 0) - v.get("now", 0)))
            out.append(f" INCOMING BOSS — {left // 3600}h {left % 3600 // 60}m\n",
                       style=INK_B)
        else:
            out.append(f" POOL {bar:<24}{pct:>3}%\n",
                       style=NEG if pct < 25 else INK_B)
        rank, mine = (list(v.get("you") or (0, 0)) + [0, 0])[:2]
        top = v.get("top") or []
        lead = f"{top[0][0][:10]} {_fmt(top[0][1])}" if top else "—"
        out.append(f" attempts {v.get('attempts', 0)}   "
                   f"you #{rank} {_fmt(mine)}   top {lead}\n", style=DIM)
        # the cadence line (2026-07-17): the WEEKLY window, the day's
        # attempts, and the real-calendar bonuses the relay already pays
        from . import tournament as _cad
        if self._standing():
            left = max(0, int(b.get("end", 0) - v.get("now", 0)))
            days, hrs = left // 86400, left % 86400 // 3600
            fest = _cad.holiday()
            # the relay pays x1.5 on WEEKENDS only -- "2x" and a festival
            # bonus were promises the server never paid (raid review
            # 2026-07-18); the festival stays as pure calendar flavor
            note = (f" weekly boss · {days}d {hrs}h left"
                    + (f" · {fest}" if fest
                       else " · weekend pays 1.5x" if _cad.is_weekend() else ""))
            out.append(note + "\n", style=DIM)
        award = v.get("award")
        if award:
            out.append(f" purse waiting: {award.get('boss', '?')[:12]} — press C\n",
                       style=POS)
        out.append_text(menu.note(self.msg, tick=self.frame_i))
        out.append_text(menu.footer("SPACE raid   C claim   ESC out"))
        return out
