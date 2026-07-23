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
        self._no_account = name is None   # the gate refuses a nameless login;
        #  the old path sent name=None, which the server minted as "None"
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
        if self.msg == "Calling the raid gate…":
            # surface a refused call instead of ringing forever (the panel
            # swallowed login_failed/error and held this line for good)
            st = getattr(self.client, "state", None)
            if self._no_account:
                self.msg = "No account — log into the LOBBY first."
            elif st is not None and st.login_failed:
                self.msg = f"The gate turned us away: {st.login_failed}"
            elif st is not None and st.error:
                self.msg = f"Gate error: {st.error}"
            elif self.view:
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
                # the gate REFUSED the report -- speak ITS reason (the ack
                # carries `why`: a fallen boss OR spent attempts; the old
                # hardcoded "boss is gone" guessed wrong on stale-view
                # attempt races, raid round 2026-07-19).  No refetch here:
                # the gate re-sends the view with every hit ack now, like
                # the claim flow.
                self.msg = hit.get("why") or "The gate refused the report."
                self.sfx = "error"
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
                "attribute": rec.get("attribute", "Free"), "boss": True,
                # the COMMUNITY POOL rides the enemy dict so the battle
                # card can show the boss's REAL health (raid audit
                # 2026-07-23: the card showed RaidBout's 5/5 display stub)
                "pool": (int(b.get("hp", 0)), max(1, int(b.get("max_hp", 1))))}

    def _report(self, b):
        if b is None:
            # ESC before the bell: no volley rolled, no report, no attempt
            # spent -- the old "Not a scratch" called the walk-away a whiff
            # (raid round 2026-07-19)
            self.msg = "You back off. The attempt keeps."
            return
        dealt = int(getattr(b, "dealt", 0) or 0)
        if dealt > 0 and self.view:
            self.client.raid_hit(dealt)
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
    def _context_line(self, v, b):
        """The raid page's one context line: the status message alternates
        with the waiting purse / weekly cadence on the shop-tease beat (40
        ticks), so neither starves the other (menu.note marquees any of
        them when over-wide)."""
        award = v.get("award")
        if award:
            alt = f"purse waiting: {award.get('boss', '?')[:12]} — press C"
        elif not self._standing():
            alt = ""
        else:
            import time as _time
            from . import tournament as _cad
            left = max(0, int(b.get("end", 0) - v.get("now", 0)))
            days, hrs = left // 86400, left % 86400 // 3600
            fest = _cad.holiday()
            # the relay pays x1.5 on WEEKENDS only -- "2x" and a festival
            # bonus were promises the server never paid (raid review
            # 2026-07-18); the festival stays as pure calendar flavor.
            # The weekend note keys off the SERVER'S clock (its own `now`,
            # UTC weekday) -- borrowing the cups' LOCAL is_weekend() lied
            # both ways at week edges: a US Friday evening is already a
            # paying UTC Saturday, a US Sunday evening a 1x UTC Monday
            # (cup audit 2026-07-19).  Cups stay local: their purse pays
            # client-side, so the player's own weekend IS their truth.
            srv_wknd = _time.gmtime(v.get("now", _time.time())).tm_wday >= 5
            alt = (f"weekly boss · {days}d {hrs}h left"
                   + (f" · {fest}" if fest
                      else " · weekend claims pay 1.5x" if srv_wknd else ""))
        if self.msg and (not alt or (self.frame_i // 40) % 2 == 0):
            return self.msg
        return alt or self.msg

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        v = self.view
        b = self._boss()
        if not v or not b:
            out = menu.header("RAID", "…")
            out.append_text(menu.blanks(5))
            out.append_text(menu.note(self.msg, tick=self.frame_i))
            # keys ride the STRIP here like every other state of this
            # screen -- the in-LCD footer was the family's one stray
            # (raid round 2026-07-19)
            return out
        num = int(b.get("num", -1))
        # THE LCD IS PURE SCENE (raid uncramp 2026-07-23, Joel: "its still
        # a cramped up mess, it looks like hes in the sky").  The old page
        # stacked POOL bar + stats + cadence UNDER an 8-row scene -- every
        # one of those numbers already lives on the STATUS card, and the
        # boss paid for the duplication: a 16px sprite crammed edge-to-edge
        # in a 16px band, head touching the header, feet flush on text.
        # Now: header + a TALL 10-row stage + one context line.  The boss
        # gets 4px of sky and the standard 2px floor margin, and the
        # backdrop's BOTTOM 20px keeps the arena floor under its feet
        # (_paint_cells indexes bgimg by absolute row -- an unsliced 24px
        # backdrop painted this reduced scene with its sky band).
        rows = data.bob_frame(num, self.frame_i,
                              "attack" if (self.frame_i // 9) % 4 == 3 else "idle")
        sc_rows = ROWS - 2
        boss = grid.prep(rows, ph=sc_rows * 2) if rows else None
        placements = [(boss, (COLS - grid.width(boss)) // 2, False)] if boss else []
        bgimg = self.pet.background(file="tourneyBack")
        if bgimg and len(bgimg) > sc_rows * 2:
            bgimg = bgimg[-sc_rows * 2:]
        scene = render_scene(placements, COLS, sc_rows, menu.scene_ink(bgimg),
                             LCD_BG, bgimg=bgimg)
        stage = data.record_for(num).get("stage", "Mega")
        out = menu.bar(f"RAID · {b.get('name', '?')[:14]}", stage[:8])
        out.append_text(scene)
        out.append("\n")               # terminate the scene's last row
        if not self._standing():
            left = max(0, int(b.get("start", 0) - v.get("now", 0)))
            note = f"INCOMING BOSS — {left // 3600}h {left % 3600 // 60}m"
        else:
            # priority msg > waiting purse > the weekly cadence; every
            # number (pool, standing, tries, top) lives on the CARD
            note = self._context_line(v, b)
        out.append_text(menu.note(note, tick=self.frame_i))
        out.right_crop(1)          # 12 rows exactly, no trailing 13th
        return out
