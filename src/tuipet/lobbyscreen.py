"""Multiplayer lobby panel — name login, presence, chat, jogress + battle sessions.

Chat-focused layout: a scrolling chat log on the left, a roster sidebar on the
right. Phases:

  name     type a handle, Enter to join  (only when no cached tamer name)
  lobby    chat default; Up/Down pick a player; Enter on empty input opens that
           player's action menu ([B]attle / [J]ogress); invites pop a [Y]/[N]
  jogress  both relay their pet's attribute, each resolves its fusion locally
           (jogress.resolve), shows the result, Enter evolves the pet
  battle   seeded symmetric PvP (proto 2, canon BattleProtocol's peer-symmetric
           exchange with the desync solved): both relay battle cards carrying a
           nonce COMMITMENT, reveal the nonce with the first pick, and derive a
           shared PRNG seed -- then each round both exchange only their FINAL
           attribute pick and each side resolves the identical card-vs-card engine
           locally. Neither peer trusts the other's arithmetic, so the monthly
           ladder's both-reports-must-agree check is real. A peer whose card
           has no "proto" gets the pre-2 host-authoritative relay verbatim
           (the inviter resolves and mirrors absolute results). PvP wins
           record onto the pet (evolution credit) just like PvE.

Decoupled from the app: `on_connect(name, card) -> LobbyClient` lets the app own
the WebSocket worker's lifecycle. Colours come from the live theme.
"""
from __future__ import annotations

import hashlib
import random

from rich.cells import cell_len, chop_cells, set_cell_size
from rich.text import Text

from . import data
from . import jogress
from . import battle
from . import battlescreen
from . import jogressscreen
from . import menu
from . import persistence
from .net import ANNOUNCE, CHAT_CAP
from .render import marquee
from .theme import INK, INK_B, DIM, SEL

CHATW = 25
ROSTW = 12
BODY = 8
CHAT_MAX = 400          # server MAX_CHAT: the local input buffer stops here too
# (ATTACK_KEYS left with the pick-a-move battle -- 0.5 BATTLE 2026-07-17)


# ⛔ THE CELL-WIDTH LAW (chat polish 2026-07-14).  The lobby is the ONE place a
# player types arbitrary text, and an emoji or a CJK glyph occupies TWO terminal
# cells while counting as ONE character.  `s[:w].ljust(w)` and `len(s)` measure
# CHARACTERS, so a line like "🔥🔥 emoji 日本語" overflowed its 25-column budget and
# shoved the roster divider `│` right off its column -- the layout visibly tore.
# Every width decision in this file goes through cell_len/set_cell_size/chop_cells.
def _fit(s, w):
    """Pad or truncate to exactly `w` DISPLAY CELLS (never characters)."""
    return set_cell_size(str(s), w)


def _wrap(s, w):
    """Word-wrap `s` into lines of <= w CELLS, hard-splitting any over-long word.
    A wide glyph is never split down the middle -- chop_cells keeps it whole."""
    out, line = [], ""
    for word in str(s).split(" "):
        while cell_len(word) > w:
            if line:
                out.append(line); line = ""
            chunks = chop_cells(word, w)
            out.append(chunks[0])
            word = "".join(chunks[1:])
        if not line:
            line = word
        elif cell_len(line) + 1 + cell_len(word) <= w:
            line += " " + word
        else:
            out.append(line); line = word
    if line:
        out.append(line)
    return out or [""]


def _tail_cells(s, w):
    """The LAST `w` cells of `s` -- the input line scrolls as you type, and a
    character-based slice let a typed emoji run past the frame."""
    while cell_len(s) > w:
        s = s[1:]
    return s


def _hpbar(hp, mx, w=10):
    fill = max(0, min(w, round(hp / mx * w))) if mx else 0
    return "█" * fill + "─" * (w - fill)


class AccountPanel:
    """Name + password entry. Tab/Up/Down switch fields; Enter on the password
    confirms when both are filled. Returns ("done", (name, password)), or
    ("done", None) on Esc. Used at first launch and to recover a failed login."""

    def __init__(self, name="", note="Name + password — the name is yours."):
        self.name_buf = name
        self.pw_buf = ""
        self.field = "pw" if name else "name"
        self.note = note
        self.sfx = None
        self.captures_text = True       # typing a name/password — never treat q as quit

    def strip(self):
        return menu.hints(("TAB", "switch"), ("ENTER", "go"), ("ESC", "back"))

    def key(self, k):
        if k == "escape":
            return ("done", None)
        if k in ("tab", "up", "down"):
            self.field = "pw" if self.field == "name" else "name"
            return None
        if k == "enter":
            if self.field == "name":
                self.field = "pw"
                return None
            name = self.name_buf.strip()[:24]
            if name and self.pw_buf:
                return ("done", (name, self.pw_buf))
            return None
        attr = "name_buf" if self.field == "name" else "pw_buf"
        cur = getattr(self, attr)
        if k == "backspace":
            cur = cur[:-1]
        elif k == "space":
            cur = cur + " "
        elif len(k) == 1 and k.isprintable():
            cur = cur + k
        setattr(self, attr, cur[:64])
        return None

    def text(self):
        t = Text()
        t.append("  TUIPET ACCOUNT\n\n", style=INK_B)
        # tail-window long input so a line never overruns the 40-col LCD
        # (the box CLIPS overflow live -- lobby audit 2026-07-04)
        nm = (self.name_buf + ("_" if self.field == "name" else ""))[-26:]
        pw = ("*" * len(self.pw_buf) + ("_" if self.field == "pw" else ""))[-26:]
        t.append("  name:     ", style=DIM)
        t.append(nm + "\n", style=INK_B if self.field == "name" else INK)
        t.append("  password: ", style=DIM)
        t.append(pw + "\n\n", style=INK_B if self.field == "pw" else INK)
        t.append(f"  {self.note[:38]}\n", style=DIM)
        t.append("  TAB switch   ENTER go   ESC back", style=DIM)
        return t


# PvP wire bounds (multiplayer audit 2026-07-13): the relay is peer-to-peer,
# so an opponent card is UNTRUSTED input.  HP ceiling = the oldest trained cap
# (pet.HEALTH_CAP_LADDER tops out at 30); power ceiling sits above the
# strongest enemy in the shipped data (virus 650) with headroom for a fully
# trained Mega.  A peer claiming more is clamped, not kicked.
MAX_PVP_HP = 30
MAX_PVP_POWER = 999


def _clamp_card(card):
    """Bound an UNTRUSTED battle card to what the game can actually produce.
    Module-level because seeded PvP feeds BOTH engines identically-clamped
    cards -- including one's own, clamped exactly as the peer clamps it."""
    def _n(v, d=0, lo=0, hi=999):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            v = d
        return max(lo, min(int(v), hi))
    card = dict(card)
    card["strength_max"] = _n(card.get("strength_max"), 4, 1, 9)
    card["strength"] = _n(card.get("strength"), 4, 0, card["strength_max"])
    card["hunger_max"] = _n(card.get("hunger_max"), 4, 1, 9)
    card["hunger"] = _n(card.get("hunger"), 4, 0, card["hunger_max"])
    card["energy_max"] = _n(card.get("energy_max"), 5, 1, 2000)
    card["energy"] = _n(card.get("energy"), 0, 0, card["energy_max"])
    card["weight"] = _n(card.get("weight"), 10, 1, 999)
    card["base_weight"] = _n(card.get("base_weight"), 10, 1, 999)
    card["trainings_cur"] = _n(card.get("trainings_cur"), 0, 0, 999)
    card["trainings_total"] = _n(card.get("trainings_total"), 0, 0, 9999)
    card["battles"] = _n(card.get("battles"), 0, 0, 10 ** 6)
    card["wins"] = _n(card.get("wins"), 0, 0, card["battles"])
    if card.get("hit_type") not in ("mega", "normal", "miss"):
        card["hit_type"] = "miss"
    card["num"] = _n(card.get("num"), 0, 0, 10 ** 6)
    # stage/attribute come from the SPECIES RECORD of the claimed num, never
    # the wire: a forged {"stage": "Special"} ranked 14.5 and auto-won every
    # online bout while the sprite still showed a Child (audit 2026-07-15).
    # Unknown nums (a newer build's dex) keep a KNOWN claimed stage so the
    # two engines stay symmetric; garbage stages already ranked as "Child".
    rec = data.record_for(card["num"])
    if not rec.get("_placeholder"):
        card["stage"] = rec.get("stage", "Child")
        card["attribute"] = rec.get("attribute", "Free")
    else:
        if card.get("stage") not in battle._RANK:
            card["stage"] = "Child"
        elif card.get("stage") == "Special":
            # every REAL Special is in the local dex and record-derived
            # above; an unknown num claiming the 14.5 rank is the forge
            card["stage"] = "Ultimate-Super Ultimate"
        if card.get("attribute") not in ("Vaccine", "Virus", "Data", "Free"):
            card["attribute"] = "Free"
    card["hp"] = 5
    return card


class LobbyPanel:
    def __init__(self, pet, on_connect, name=None, pw=""):
        self.pet = pet
        self.on_connect = on_connect
        self.client = None
        self.state = None
        self.captures_text = True      # chat input — q is a typed character, never quit
        self.entry = None              # AccountPanel while logging in
        self._last_name = name or ""
        self.buf = ""
        self.sel = 0
        self.scroll = 0                # chat scrollback: lines back from live
        self.rost_hidden = False       # → folds the player box (chat takes the
        #                                full width, ↑↓ scroll the log); ← restores
        self.action_for = None
        self.pm_to = None              # (id, name): the input line is a PM compose
        self.invite_prompt = None
        self.dm_peer = None            # (id, name): the open DM thread
        self.sfx = None
        # jogress session
        self.partner = None
        self.partner_species = None
        self.jphase = None
        self.jresult = None
        self.jshow = None             # the offline fusion scene, replayed here
        self.fail_reason = None
        self.j_confirmed = False           # two-phase commit: my yes is in
        self.j_partner_confirmed = False   # ...and theirs
        self.j_peer_two_phase = False      # the peer speaks the confirm protocol
        self.bshow = None             # the round's volley replay (BattlePanel shim)
        # battle session
        self.is_host = False
        self.battle = None
        self.opp_card = None
        self.bphase = None            # "card" | "choose" | "wait" | "over"
        self.bt_my_choice = None
        self.bt_opp_choice = None
        self.my_hp = self.my_max = 0
        self.opp_hp = self.opp_max = 0
        self.bt_log = ""
        self.bt_outcome = ""
        self.bt_reward = None
        self.bt_payload = None        # ("done", X) payload when the bout ends
        # seeded symmetric PvP (proto 3: the precomputed 0.5 race)
        self.bt_nonce = None          # my seed nonce (committed in my card msg)
        self.bt_peer_commit = None    # sha256 hex the peer committed to
        self.bt_peer_nonce = None     # revealed with the peer's first pick
        self.bt_my_card = None        # the exact clamped card I shipped (engine input)
        if name and pw:
            self._connect(name, pw)
        else:
            self.phase = "login"
            self.entry = AccountPanel(name=name or "")
            self.status = "Log in to the lobby."

    def _connect(self, name, pw):
        self._last_name = name
        self.client = self.on_connect(name, pw, self._card())
        self.state = self.client.state
        from . import persistence
        self.state.blocked = persistence.get_blocked()
        # DM threads + unread badges reload from the last session -- leaving a
        # PM (or the lobby) never loses the conversation (Joel 2026-07-10).
        # Seed-only merge: anything already live in this state wins.
        saved_dms, saved_unread = persistence.get_dms()
        for peer, thread in saved_dms.items():
            self.state.dms.setdefault(peer, thread)
        self.state.unread |= saved_unread
        self.phase = "lobby"
        self.status = "Connecting…"

    # ---- presence card ---------------------------------------------------
    def _card(self):
        _, by = data.load_sprites()
        info = by.get(self.pet.num, {})
        card = {"name": getattr(self.pet, "name", None) or info.get("name") or "Egg",
                "stage": self.pet.stage, "num": self.pet.num,
                "attr": getattr(self.pet, "attribute", "") or info.get("attribute") or "None"}
        # the worn honor rides the presence card (prestige sink 2026-07-14) --
        # the server stores and rebroadcasts the card verbatim, and clients
        # that predate titles simply ignore the extra field
        worn = data.title_name(persistence.get_title_worn())
        if worn:
            card["title"] = worn
        return card

    def _session_gate(self, kind):
        """PURE session eligibility for a REMOTE invite.  can_battle is a
        player-poke: its guard DISTURBS a sleeper (wake + mood hit + disturb
        count) and rolls a refusal -- a stranger's invite must never touch
        the pet (asleep sweep 2026-07-06).  Mirrors the gates without the
        side effects; the SEND side keeps the poke (the player pressed it)."""
        p = self.pet
        if getattr(p, "dead", False):
            return "It rests now — press N for a new egg."
        if p.asleep:
            return "zzz… asleep"
        if kind == "jogress":
            return jogress.can_jogress(p)      # pure: stage / DP checks
        if p.stage in ("Egg", "Fresh"):
            return "Too young to battle."
        return None

    def _others(self):
        """Everyone else ONLINE, lobby regulars first, then the playing
        ghosts (presence 2026-07-05: the roster carries the whole server)."""
        others = self.state.others() if self.state else []
        return sorted(others, key=lambda p: (not p.get("live", True),
                                             str(p.get("name", "")).lower()))

    def _pet_of(self, pid):
        """'Agumon · Champion' for a roster id ('' when unknown); a worn honor
        title trails as '· ★Bit Baron' (the marquee absorbs the length)."""
        for pl in (self.state.roster if self.state else []):
            if pl["id"] == pid:
                pet = pl.get("pet") or {}
                nm, st = pet.get("name"), pet.get("stage")
                t = str(pet.get("title") or "")[:24]
                tail = f" · ★{t}" if t else ""
                return f"{nm} · {st}{tail}" if nm and st else (nm or "")
        return ""

    # ---- per-tick refresh (the 0.1s interval clock calls this) -----------
    def anim(self):
        self._mq = getattr(self, "_mq", 0) + 1   # drives long-field marquees
        # session replays advance first (they render whatever the wire does)
        if self.bshow is not None:
            b = self.bshow
            if b.i < len(b.timeline) - 1:
                b.anim()                        # advances + emits the volley sfx
                if getattr(b, "sfx", None):
                    self.sfx = b.sfx
                    b.sfx = None
            else:
                self.bshow = None               # volley done -> choose/over shows
        if self.jshow is not None and self.jphase == "result":
            self.jshow.anim()                   # converge -> flash -> fused bounce
        lad = getattr(self.client, "ladder", None) if self.client else None
        if lad and lad.get("award"):
            a = lad["award"]
            if not persistence.ladder_award_claimed(a.get("season", "")):
                persistence.note_ladder_award(a["season"])
                self.pet.bits = min(self.pet.bits + int(a.get("bits") or 0), 99999999)
                claim = getattr(self.client, "ladder_claim", None)
                if claim:
                    claim(a["season"])
                self.sfx = "champion"
                self.status = (f"season {a['season']}: rank {a['rank']} — "
                               f"+{a['bits']}b claimed!")
        s = self.state
        if not s:
            return
        for m in list(s.inbox):
            t = m.get("t")
            if t == "invite":
                if m.get("kind") not in ("jogress", "battle"):
                    # the relay forwards kind verbatim: an unknown kind used
                    # to reach _enter_session, set a dangling partner and
                    # enter NO branch -- desync, not a session (audit
                    # 2026-07-13); auto-decline like the blocked path
                    self.client.respond(m.get("from_id"), m.get("kind"), False)
                    s.inbox.remove(m)
                    continue
                if m.get("from_name") in s.blocked:
                    self.client.respond(m.get("from_id"), m.get("kind"), False)
                    s.inbox.remove(m)
                    continue
                gate = self._session_gate(m.get("kind"))
                if gate:
                    # the pet can't honour this session (an egg, asleep...):
                    # auto-decline instead of prompting -- accepting used to
                    # start a bout the replay couldn't even render
                    # (egg-battle audit 2026-07-06)
                    self.client.respond(m.get("from_id"), m.get("kind"), False)
                    self.status = gate
                elif self.phase != "lobby" or self.invite_prompt is not None or self.action_for is not None:
                    self.client.respond(m.get("from_id"), m.get("kind"), False, busy=True)  # in a session
                elif self.buf or self.pm_to is not None:
                    # mid-sentence: the popped prompt would EAT the next
                    # keystroke -- typing "yeah" ACCEPTED a jogress on the y
                    # (lobby audit 2026-07-07).  Hold the invite in the inbox
                    # until the input line clears; the status says it's waiting.
                    self.status = f"{m.get('from_name', '?')} invites — finish typing"
                    continue
                else:
                    self.invite_prompt = m
                    self.sfx = "menu"
                s.inbox.remove(m)
            elif t == "invite_resp":
                s.inbox.remove(m)
                if m.get("accept"):
                    if self.phase == "lobby":
                        self._enter_session(m.get("from_id"), m.get("from_name", "?"), m.get("kind"), host=True)
                    else:                                  # already busy -> free the accepter
                        self.client.relay(m.get("from_id"), {"kind": m.get("kind"), "abort": True})
                elif m.get("busy"):
                    self.status = f"{m.get('from_name', '?')} is busy."
                else:
                    self.status = f"{m.get('from_name', '?')} declined."
            elif t == "relay":
                s.inbox.remove(m)
                self._on_relay(m)
        if s.login_failed:
            self.entry = AccountPanel(name=self._last_name, note=s.login_failed)
            self.phase = "login"
            s.login_failed = None
        elif s.error:
            self.status = f"! {s.error}"
            s.error = None
        elif s.connected and self.status == "Connecting…":
            # 36 chars: the old "Up/Down pick · …" ran 41 and CLIPPED its own
            # "Esc leave" hint off the 38-col line (Joel's live screen 2026-07-07)
            self.status = "↑↓ pick · ENTER chat · TAB ranks · ESC"
        # drop -> the client retries on its own; say so instead of stranding a banner
        if getattr(s, "reconnecting", False):
            self._seen_ids = None                  # a refilled roster is not a wave of joins
            if self.phase == "lobby":
                self.status = "Connection lost — reconnecting…"
            self._was_down = True
        elif s.connected and getattr(self, "_was_down", False):
            self._was_down = False
            if self.phase == "lobby":
                self.status = "Reconnected."
        # join/leave notices in the chat log (client-side roster diff)
        if s.connected:
            room = getattr(s, "room", None)
            if room != getattr(self, "_seen_room", None):
                # a room switch swaps the whole scope: not a wave of joins/leaves
                self._seen_room = room
                self._seen_ids = None
                if self.phase == "lobby":
                    self.status = (f"room: {room} · /leave exits" if room
                                   else "Back in the main lobby.")
            # announce LIVE lobby presences only, and by NAME: a home-screen
            # sync ghost's reconnect churn (a fresh connection id on every
            # drop) spammed the chat with "roxi joined / roxi left" while
            # roxi was never in the lobby (Joel 2026-07-17).  Ghosts still
            # sit in the sidebar as "playing" -- silently; and a live
            # player's quick reconnect keeps its NAME, so no false wave.
            live = {pl["name"] for pl in s.roster
                    if pl.get("live", True) and pl["id"] != s.me_id}
            old = getattr(self, "_seen_ids", None)
            if old is not None:
                for nm in sorted(live - old):
                    s.chat.append(("", f"{nm} joined"))
                for nm in sorted(old - live):
                    s.chat.append(("", f"{nm} left"))
                del s.chat[:-CHAT_CAP]      # the one cap, shared with net.py
            self._seen_ids = live
        # partner vanished mid-session
        if self.partner and not any(p["id"] == self.partner[0] for p in s.roster):
            if self.phase == "jogress" and self.jphase == "waiting":
                self.fail_reason, self.jphase = "Partner left.", "failed"
            elif self.phase == "jogress" and self.jphase == "result":
                self._return_to_lobby("Partner left — no fusion.")
            elif self.phase == "battle" and self.bphase not in (None, "over"):
                self.bt_outcome = "Opponent left."
                self.bt_payload = ("battle_msg", "Opponent left — battle void.")
                self.bphase = "over"

    # ---- session orchestration ------------------------------------------
    def _enter_session(self, pid, pname, kind, host):
        if self.invite_prompt is not None:
            # a CROSSED invite (both players invited each other): entering the
            # session must consume the other prompt, or it survives the whole
            # bout and re-offers a dead invite back in the lobby (session
            # audit 2026-07-07)
            inv = self.invite_prompt
            self.invite_prompt = None
            self.client.respond(inv.get("from_id"), inv.get("kind"), False, busy=True)
        self.partner = (pid, pname)
        if kind == "jogress":
            card = self._card()
            opts = jogress.options(self.pet)
            self.client.relay(pid, {"kind": "jogress", "attr": card["attr"],
                                    "num": card["num"], "name": card["name"],
                                    # canon JogressProtocol.sendPlayerInfo ships the
                                    # jogressMatch string (reachable fusion NAMES +
                                    # pairable attributes) and the growth stage --
                                    # they drive the mutual both-or-neither match
                                    # (session audit 2026-07-07)
                                    "stage": self.pet.stage,
                                    "fusions": [o["name"] for o in opts],
                                    "attrs": jogress.pairable_attrs(self.pet),
                                    # canon JogressProtocol ships the REAL sick
                                    # state: fusing with a sick partner is a 90%
                                    # catch (jogress audit 2026-07-06)
                                    "sick": bool(getattr(self.pet, "sick", False)),
                                    # two-phase commit capability (consent audit
                                    # 2026-07-07): both players confirm at the
                                    # result screen before either pet fuses
                                    "confirm2": True})
            self.phase, self.jphase = "jogress", "waiting"
            self.status = f"Fusing with {pname}…"
        elif kind == "battle":
            self.is_host = host
            self.phase, self.bphase = "battle", "card"
            card = battle.battle_card(self.pet)
            # the engine input must be the card AS THE PEER WILL SEE IT, so
            # clamp my own card exactly like _battle_begin clamps theirs
            self.bt_my_card = _clamp_card(card)
            # commit-reveal seed handshake: the nonce is COMMITTED before either
            # side has seen the other's (cards cross in flight), and revealed
            # with the first pick -- so neither client can grind the shared
            # seed for a favourable initiative coin flip.  Spiritually canon:
            # BattleProtocol exchanged a SHA-256 checksum at setup too.
            self.bt_nonce = random.getrandbits(64)
            commit = hashlib.sha256(str(self.bt_nonce).encode()).hexdigest()
            self.client.relay(pid, {"kind": "battle", "t": "card",
                                    "card": card, "commit": commit})
            self.status = f"Battle vs {pname}…"

    def _return_to_lobby(self, status=""):
        """End the current session and drop back into the chat lobby (not out of it).
        Any pet change (a fusion) is pushed so the roster shows your new form."""
        had_partner = self.partner is not None
        self.partner = self.partner_species = self.jresult = None
        self.jphase = self.fail_reason = None
        self.j_confirmed = self.j_partner_confirmed = self.j_peer_two_phase = False
        self.jpartner_sick = False
        self.jshow = self.bshow = None
        self.battle = self.opp_card = self.bphase = None
        self.bt_my_choice = self.bt_opp_choice = None
        self.bt_log = self.bt_outcome = ""
        self.bt_reward = self.bt_payload = None
        self.bt_nonce = self.bt_peer_commit = self.bt_peer_nonce = None
        self.bt_my_card = None
        self.is_host = False
        self.phase = "lobby"
        self.status = status or "Back in the lobby."
        if had_partner and self.client:
            self.client.update_pet(self._card())

    def _on_relay(self, m):
        if not self.partner or m.get("from_id") != self.partner[0]:
            return
        payload = m.get("payload") or {}
        kind = payload.get("kind")
        if payload.get("abort"):                       # partner cancelled / got busy
            if self.phase == "jogress" and self.jphase == "waiting":
                self.fail_reason, self.jphase = "Partner left the fusion.", "failed"
            elif self.phase == "jogress" and self.jphase == "result":
                self._return_to_lobby("Partner left — no fusion.")   # pre-commit: nobody fuses
            elif self.phase == "battle" and self.bphase not in (None, "over"):
                self.bt_outcome = "Opponent left."
                self.bt_payload = ("battle_msg", "Opponent left — battle void.")
                self.bphase = "over"
            return
        if kind == "jogress" and self.phase == "jogress" and payload.get("t") == "confirm":
            # two-phase commit: the partner said yes; fuse only when BOTH have
            self.j_partner_confirmed = True
            if self.jphase == "result" and self.j_confirmed:
                self._commit_fusion()
            return
        if kind == "jogress" and self.phase == "jogress" and payload.get("t") == "decline":
            if self.jphase in ("waiting", "result"):
                self._return_to_lobby("Partner declined — no one fused.")
            return
        if (kind == "jogress" and self.phase == "jogress"
                and self.jphase == "waiting" and payload.get("t") is None):
            self.j_peer_two_phase = bool(payload.get("confirm2"))
            self.partner_species = payload.get("name")
            self.jpartner_sick = bool(payload.get("sick"))   # contagion at the fuse
            reason = jogress.can_jogress(self.pet)      # honour asleep / too-young, like offline
            self.jresult = None if reason else jogress.resolve_online(self.pet, payload)
            if self.jresult:
                self.jphase = "result"
                self.sfx = "jogress"
                # the REAL fusion scene (lobby audit 2026-07-04: the old
                # lobby printed text while the fusion deserved its converge +
                # flash) -- both parents' actual sprites play the panel's beats
                self.jshow = jogressscreen.JogressPanel(
                    self.pet, self.pet.num,
                    payload.get("num") or self.pet.num,
                    self.jresult["num"])
            else:
                self.fail_reason = reason or "No resonance with that partner."
                self.jphase = "failed"
                # tell the partner so it can't hang at its result screen waiting
                # for a confirm we'll never send (resolve_online is symmetric, so
                # this only bites on a mid-handshake state change -- a pet that
                # dozed off or lost DP after inviting; jogress audit 2026-07-08)
                if self.partner:
                    self.client.relay(self.partner[0], {"kind": "jogress", "abort": True})
        elif kind == "battle" and self.phase == "battle":
            bt = payload.get("t")
            # each relay type is only honoured in the phase that expects it
            # (session audit 2026-07-07): an unguarded 'card' mid-fight
            # re-ran _battle_begin and RESET both HP bars; a stray 'result'
            # outside the guest's wait re-applied a stale round
            if bt == "card" and self.bphase == "card":
                self._battle_begin(payload.get("card") or {}, payload.get("commit"))
            elif bt == "pick" and self.bphase in ("card", "wait", "fight"):
                # proto 3 (0.5 BATTLE 2026-07-17): no picks in this world --
                # the "pick" message carries only the revealed seed nonce
                if self.bt_peer_nonce is None:
                    self.bt_peer_nonce = payload.get("nonce")
                    self._maybe_build()

    # ---- battle ----------------------------------------------------------
    def _battle_begin(self, opp_card, commit=None):
        """Cards crossed: clamp the untrusted card, verify the proto, and
        reveal my nonce.  The fight itself is SEEDED SYMMETRIC: both clients
        run the identical precomputed engine on identically-clamped cards, so
        no result ever crosses the wire."""
        opp_card = _clamp_card(opp_card)
        self.opp_card = opp_card
        try:
            proto_ok = int(opp_card.get("proto") or 0) >= 3 and bool(commit)
        except (TypeError, ValueError):
            proto_ok = False
        if not proto_ok:
            self.bt_outcome = "Battle void — version mismatch."
            self.bt_payload = ("battle_msg", "Battle void — the other side "
                              "runs an older tuipet.")
            self.bphase = "over"
            if self.partner:
                self.client.relay(self.partner[0], {"kind": "battle", "abort": True})
            return
        self.bt_peer_commit = commit
        self.my_max = self.my_hp = 5
        self.opp_max = self.opp_hp = 5
        self.bphase = "wait"
        # the nonce reveal is its own message now (no picks in this world)
        self.client.relay(self.partner[0],
                          {"kind": "battle", "t": "pick", "nonce": self.bt_nonce})
        self._maybe_build()

    def _maybe_build(self):
        """Both nonces in -> verify the commit, seed the shared engine, and
        precompute the whole 5-round fight (both sides independently)."""
        if self.battle is not None or self.bt_peer_nonce is None \
                or self.opp_card is None:
            return
        pn = self.bt_peer_nonce
        if hashlib.sha256(str(pn).encode()).hexdigest() != (self.bt_peer_commit or ""):
            self.bt_outcome = "Battle void — bad checksum."
            self.bt_payload = ("battle_msg", "Battle void — bad checksum.")
            self.bphase = "over"
            if self.partner:
                self.client.relay(self.partner[0], {"kind": "battle", "abort": True})
            return
        hn, gn = (self.bt_nonce, pn) if self.is_host else (pn, self.bt_nonce)
        seed = int.from_bytes(hashlib.sha256(f"{hn}:{gn}".encode()).digest()[:8], "big")
        host_card, guest_card = ((self.bt_my_card, self.opp_card) if self.is_host
                                 else (self.opp_card, self.bt_my_card))
        rng = random.Random(seed).random
        host = battle.Side.of_card(dict(host_card))
        guest = battle.Side.of_card(dict(guest_card))
        seq, hhp, ghp = battle.generate(host, guest, rounds=battle.ROUNDS_ONLINE,
                                        rng=rng)
        self.battle = {"seq": seq, "host_hp": 5, "guest_hp": 5, "i": 0}
        self.bphase = "fight"
        self._play_next_round()

    def _play_next_round(self):
        """Advance the precomputed fight one round and stage its volley."""
        b = self.battle
        if b is None:
            return
        if b["i"] >= len(b["seq"]) or b["host_hp"] <= 0 or b["guest_hp"] <= 0:
            self._battle_over()
            return
        h_hit, h_dmg, g_hit, g_dmg = b["seq"][b["i"]]
        b["i"] += 1
        if h_hit:
            b["guest_hp"] = max(0, b["guest_hp"] - h_dmg)
        if g_hit:
            b["host_hp"] = max(0, b["host_hp"] - g_dmg)
        if self.is_host:
            dealt = h_dmg if h_hit else 0
            taken = g_dmg if g_hit else 0
        else:
            dealt = g_dmg if g_hit else 0
            taken = h_dmg if h_hit else 0
        my0, opp0 = self.my_hp, self.opp_hp
        self.my_hp = b["host_hp"] if self.is_host else b["guest_hp"]
        self.opp_hp = b["guest_hp"] if self.is_host else b["host_hp"]
        self._stage_volley(my0, opp0, dealt, taken)
        self.bt_log = f"you \u2192 {dealt} dmg\n  them \u2192 {taken} dmg"

    def _battle_over(self):
        b = self.battle
        my_hp = b["host_hp"] if self.is_host else b["guest_hp"]
        opp_hp = b["guest_hp"] if self.is_host else b["host_hp"]
        won = opp_hp <= 0 and my_hp > 0
        draw = (my_hp > 0 and opp_hp > 0 and my_hp == opp_hp) \
            or (my_hp <= 0 and opp_hp <= 0)
        if not won and not draw and my_hp > opp_hp:
            won = True                     # rounds ran dry: higher HP stands
        self.bphase = "over"
        self.sfx = "attack"
        if self.partner:                   # a finished bout is a connection
            persistence.record_connection(self.partner[1])
        # the ladder needs BOTH stories: the winner's claim only credits when
        # the LOSER's agreeing report lands too, keyed by ACCOUNT name -- the
        # old code filed only on won (nobody ever confirmed) and led with the
        # PET name (which the server doesn't know), so the monthly ladder
        # never credited a single win (audit 2026-07-15)
        opp_nm = (self.partner or (0, ""))[1] or (self.opp_card or {}).get("name")
        report = getattr(self.client, "ladder_report", None)
        if report and opp_nm and not draw:
            report(won, opp_nm)
        from .pet import online_reward
        purse = online_reward(won, draw=draw)
        self.pet.record_battle(won and not draw, online=True)
        self.pet.add_bits(purse)
        self.bt_outcome = ("DRAW" if draw
                           else "\u2605 YOU WIN! \u2605" if won else "YOU LOSE\u2026")
        self.bt_reward = f"+{purse}b" + ("  (weekend bonus!)" if purse not in (100, 150, 200) else "")
        self.bt_payload = ("battle_msg", self.bt_outcome)

    def _stage_volley(self, my0, opp0, dealt, taken):
        """A presentation-only BattlePanel replays the round: my pet RIGHT,
        the opponent's LEFT, orbs/hit/dodge from the engine's numbers."""
        try:
            card = dict(self.opp_card or {})
            if not card.get("num"):
                return
            show = battlescreen.BattlePanel(self.pet, enemy=card)
            show.foe_attr = card.get("attribute", "Free")
            show.timeline = battlescreen.round_timeline(my0, opp0, dealt, taken, True)
            show.i = 0
            show.phase = "anim"
            show._last_m = None
            self.bshow = show
        except Exception:
            self.bshow = None               # presentation must never break the bout

    def _key_battle(self, k):
        if self.bshow is not None:              # the round is replaying
            if k in ("space", "enter", "escape"):
                self.bshow = None               # skip to the between-rounds card
            return None
        if self.bphase == "over":
            if k in ("enter", "space", "escape"):
                self._return_to_lobby(self.bt_outcome)
            return None
        if self.bphase == "fight":
            if k in ("space", "enter"):
                self._play_next_round()
            elif k == "escape":
                self._forfeit()
            return None
        if self.bphase in ("card", "wait") and k == "escape":
            self._forfeit()
        return None

    def _forfeit(self):
        """Leave a battle in progress -> tell the opponent, then back to the lobby."""
        if self.partner:
            self.client.relay(self.partner[0], {"kind": "battle", "abort": True})
        self._return_to_lobby("You forfeited.")

    # ---- input -----------------------------------------------------------
    def key(self, k):
        if self.phase == "login":
            return self._key_login(k)
        if self.phase == "jogress":
            return self._key_jogress(k)
        if self.phase == "battle":
            return self._key_battle(k)
        if self.phase == "dm":
            return self._key_dm(k)
        if self.phase == "ladder":
            return self._key_ladder(k)
        return self._key_lobby(k)

    def _key_ladder(self, k):
        if k in ("escape", "tab", "q", "g"):
            self.phase = "lobby"
        return None

    def _text_ladder(self):
        """The monthly rankings: online PvP wins, top ten, your rank, and the
        days left in the season.  Data is the server's ladder message; a page
        opened before the reply shows a fetching line and fills in live."""
        t = Text()
        lad = getattr(self.client, "ladder", None) if self.client else None
        if not lad:
            t.append("  LADDER\n\n", style=INK_B)
            t.append("  fetching the rankings…\n", style=DIM)
            return t
        t.append(f"  LADDER  season {lad.get('season', '?')}\n", style=INK_B)
        t.append("  one win = one rung · online only\n\n", style=DIM)
        top = list(lad.get("top") or [])[:8]
        you_rank, you_wins = (lad.get("you") or [0, 0])[:2]
        if not top:
            t.append("  no wins recorded yet — the rungs\n", style=INK)
            t.append("  are empty.  Go start the race!\n", style=INK)
        for i, (who, wins) in enumerate(top, start=1):
            mine = who == getattr(self.client, "name", None)
            t.append(f"  {'▸' if mine else ' '}{i:>2}. {str(who)[:16]:<16} {int(wins):>3}W\n",
                     style=INK_B if mine else INK)
        t.append("\n")
        if you_rank:
            t.append(f"  you: rank {you_rank} · {you_wins} win{'s' if you_wins != 1 else ''}\n",
                     style=INK_B)
        else:
            t.append("  you: unranked — win online to climb\n", style=DIM)
        d = int(lad.get("days_left") or 0)
        t.append(f"  season resets in {d} day{'s' if d != 1 else ''}\n", style=DIM)
        return t

    def _key_login(self, k):
        r = self.entry.key(k)
        if r is not None and r[0] == "done":
            if r[1] is None:
                return ("done", None)            # Esc -> leave the lobby
            self._connect(*r[1])
        return None

    def _commit_fusion(self):
        """BOTH confirms are in (or the peer is legacy): perform the fusion --
        the same path as offline jogress."""
        if self.partner:                # swapping DNA is the strongest connection
            persistence.record_connection(self.partner[1])
        msg = jogress.fuse(self.pet, self.jresult["num"])
        # (the jogress contagion left with the sickness system (BASIC VPET 2026-07-17))
        self.sfx = "jogress"
        self._return_to_lobby(msg)

    def _key_jogress(self, k):
        if self.jphase == "result":
            if self.jshow is not None and self.jshow.phase == "fusing":
                self.jshow.key(k)                       # any key skips the converge to the reveal
                return None
            if not self.j_peer_two_phase:
                # LEGACY peer (pre-v0.2.350): its client commits on any key with
                # no decline -- mirror it, or a mixed-version pair goes one-sided
                if k in ("enter", "space", "escape"):
                    self._commit_fusion()
                return None
            # two-phase commit (consent audit 2026-07-07): the fusion is
            # PERMANENT -- both players must say yes at the result screen
            if k in ("enter", "space") and not self.j_confirmed:
                self.j_confirmed = True
                self.client.relay(self.partner[0], {"kind": "jogress", "t": "confirm"})
                if self.j_partner_confirmed:
                    self._commit_fusion()
                else:
                    self.status = "Waiting for the partner…"
            elif k == "escape":
                # a real DECLINE: nobody fuses, both sides told
                self.client.relay(self.partner[0], {"kind": "jogress", "t": "decline"})
                self._return_to_lobby("Fusion declined — no one fused.")
            return None
        if self.jphase == "failed":
            if k in ("enter", "space", "escape"):
                self._return_to_lobby(self.fail_reason or "No resonance.")
            return None
        if k == "escape":                                  # cancel mid-fusion -> free the partner
            if self.partner:
                self.client.relay(self.partner[0], {"kind": "jogress", "abort": True})
            self._return_to_lobby("Fusion cancelled.")
        return None

    def _save_dms(self):
        """Persist the DM threads + unread badges (leaving must not lose them)."""
        if self.state is not None:
            from . import persistence
            persistence.save_dms(self.state.dms, self.state.unread)

    def _key_dm(self, k):
        """Private thread with one peer: type + Enter sends, Esc back to the lobby."""
        if k == "escape":
            self.phase, self.buf = "lobby", ""
            self._save_dms()                   # the conversation stays
            return None
        if k == "enter":
            if self.buf.strip() and self.dm_peer and self.client:
                self.client.pm(self.dm_peer[0], self.buf.strip(), self.dm_peer[1])
            self.buf = ""
            return None
        return self._edit(k)

    def _text_dm(self):
        s = self.state
        peer = self.dm_peer[1] if self.dm_peer else "?"
        me = (s.me_name or "you") if s else "you"
        w = CHATW + ROSTW + 1
        t = Text()
        t.append(_fit(f"✉ {peer}", w) + "\n", style=INK_B)
        rows = []
        for frm, tx in (s.dms.get(peer, []) if s else []):
            mine = frm == me
            who = "you" if mine else frm
            parts = _wrap(f"{who}: {tx}", w - 1)
            rows.append((parts[0], DIM if mine else INK_B))
            rows.extend((" " + ln, DIM if mine else INK_B) for ln in parts[1:])
        body = BODY + 1
        view = rows[-body:]
        view = [("", INK)] * (body - len(view)) + view
        if not rows:
            view[body // 2] = ("— no messages yet — say hi —"[:w], DIM)
        for ln, sty in view:
            t.append(_fit(ln, w) + "\n", style=sty)
        label = f"→{peer[:8]}: "
        fw = w - len(label)
        shown = self.buf if len(self.buf) < fw else self.buf[-(fw - 1):]
        caret = "_" if (getattr(self, "_mq", 0) // 5) % 2 == 0 else " "
        t.append(label, style=INK_B)
        t.append(_fit(shown + caret, fw) + "\n", style=INK)
        t.append(_fit("ENTER send · ESC back to lobby", w), style=DIM)
        return t

    def _slash(self, txt):
        """Chat slash commands (password rooms 2026-07-14): `/room <phrase>`
        joins the private room for that phrase — everyone typing the same
        phrase meets there (the phrase IS the password, DSprite-style 🔒);
        `/leave` returns to the main lobby.  Anything else prints the help."""
        cmd, _, arg = txt.partition(" ")
        cmd, arg = cmd.lower(), arg.strip()
        if cmd == "/room" and arg:
            self.client.room(arg)
            self.status = "Joining the room…"
        elif cmd == "/room":
            room = getattr(self.state, "room", None) if self.state else None
            self.status = f"room: {room} · /leave exits" if room else "main lobby · /room <phrase>"
        elif cmd in ("/leave", "/lobby"):
            self.client.room("")
            self.status = "Back to the main lobby…"
        else:
            self.status = "Commands: /room <phrase> · /leave"

    def _key_lobby(self, k):
        if self.invite_prompt is not None:
            inv = self.invite_prompt
            if k in ("y", "Y"):
                self.client.respond(inv.get("from_id"), inv["kind"], True)
                self.invite_prompt = None
                self._enter_session(inv.get("from_id"), inv.get("from_name", "?"), inv["kind"], host=False)
            elif k in ("n", "N", "escape"):
                self.client.respond(inv.get("from_id"), inv["kind"], False)
                self.status, self.invite_prompt = "Declined.", None
            return None
        if self.action_for is not None:
            pid, pname, plive = self.action_for
            if k in ("b", "B") and plive:
                err = self.pet.can_battle()      # an egg was free to INVITE (egg-battle audit 2026-07-06)
                if err:
                    self.status, self.action_for = err, None
                    return None
                self.client.invite(pid, "battle"); self.status = f"Battle invite → {pname}"; self.action_for = None
            elif k in ("j", "J") and plive:
                err = jogress.can_jogress(self.pet)
                if err:
                    self.status, self.action_for = err, None
                    return None
                self.client.invite(pid, "jogress"); self.status = f"Jogress invite → {pname}"; self.action_for = None
            elif k in ("p", "P") and not plive:
                self.client.ping(pid)
                self.status = f"Pinged {pname} \u2014 asked them to hop in the lobby!"
                self.action_for = None
            elif k in ("v", "V"):
                self.phase, self.dm_peer, self.buf = "dm", (pid, pname), ""
                self.state.unread.discard(pname)
                self._save_dms()               # the read badge sticks
                self.action_for = None
            elif k in ("x", "X"):
                from . import persistence
                b = self.state.blocked
                if pname in b:
                    b.discard(pname); self.status = f"Unblocked {pname}."
                else:
                    b.add(pname)
                    # net.py filters them out from here on, but everything they
                    # ALREADY said stayed on screen -- so "Blocked X." was only
                    # half true and the spam you muted was still sitting there.
                    # A mute means MUTE: sweep their lines out of the log too.
                    st = self.state
                    st.chat[:] = [(nm, tx) for nm, tx in st.chat if nm != pname]
                    st.unread.discard(pname)
                    self.status = f"Blocked {pname}."
                persistence.set_blocked(b)
                self.action_for = None
            elif k in ("m", "M"):
                # compose a private message: the input line retargets
                self.pm_to = (pid, pname)
                self.buf = ""
                self.status = f"PM → {pname} — ENTER send, ESC cancel"
                self.action_for = None
            elif k == "escape":
                self.action_for = None
            return None
        if k == "tab":
            # the MONTHLY LADDER (2026-07-14): online wins, fresh race each
            # month.  TAB because every letter belongs to the chat input.
            if self.client:
                self.client.ladder_get()       # refresh; the page renders live
            self.phase = "ladder"
            return None
        if k == "escape":
            if self.scroll:                    # scrolled log: snap to live first
                self.scroll = 0
                return None
            if self.pm_to is not None:
                self.pm_to, self.buf = None, ""
                self.status = "PM cancelled."
                return None
            self._save_dms()                   # leaving the lobby keeps the threads
            return ("done", None)
        if k == "pageup":
            # chat scrollback (polish 2026-07-07): CHAT_CAP lines of history
            # existed but only the last 8 ever showed
            self.scroll += BODY - 1            # _text_lobby clamps to the log
            return None
        if k == "pagedown":
            self.scroll = max(0, self.scroll - (BODY - 1))
            return None
        if k == "right" and not self.rost_hidden:
            # fold the player box: the chat gets the full width (Joel 2026-07-10)
            self.rost_hidden = True
            self.status = "↑↓ scroll · ← player box · ESC leave"
            return None
        if k == "left" and self.rost_hidden:
            self.rost_hidden = False
            self.status = "↑↓ pick · ENTER chat · TAB ranks · ESC"
            return None
        if k == "up":
            if self.rost_hidden:
                self.scroll += 1               # older; _text_lobby clamps to the log
            else:
                self.sel = max(0, self.sel - 1)
            return None
        if k == "down":
            if self.rost_hidden:
                self.scroll = max(0, self.scroll - 1)
            else:
                self.sel = min(max(0, len(self._others()) - 1), self.sel + 1)
            return None
        if k == "enter":
            self.scroll = 0                    # speaking snaps the view live
            if self.pm_to is not None:
                if self.buf.strip():
                    self.client.pm(self.pm_to[0], self.buf.strip(), self.pm_to[1])
                    self.status = f"✉ sent to {self.pm_to[1]}"
                self.pm_to, self.buf = None, ""
            elif self.buf.strip():
                txt = self.buf.strip()
                self.buf = ""
                if txt.startswith("/"):
                    self._slash(txt)
                else:
                    self.client.chat(txt)
            else:
                others = self._others()
                if others and not self.rost_hidden:   # no acting on an unseen pick
                    p = others[min(self.sel, len(others) - 1)]
                    self.action_for = (p["id"], p["name"], p.get("live", True))
            return None
        return self._edit(k)

    def _edit(self, k):
        if k == "backspace":
            self.buf = self.buf[:-1]
        elif k == "space":
            self.buf += " "
        elif len(k) == 1 and k.isprintable():
            self.buf += k
        # cap at the server's MAX_CHAT (chat-input audit 2026-07-07): the buffer
        # was unbounded -- a long paste grew it without limit (the server clips
        # the SENT text at 400, but the local buffer never stopped growing)
        self.buf = self.buf[:CHAT_MAX]
        return None

    # ---- render ----------------------------------------------------------
    def _care_cue(self):
        """The care alarm's on-screen half while the lobby TICKS (2026-07-13:
        the lobby is no longer a pause room -- app.on_tick runs the life-sim
        through chat, so the strip must carry the nag or the pet starves
        silently behind the chat window).  Compact by design: name(10) +
        the loudest need, <= 38 plain cols with the ESC hint."""
        from . import theme
        p = self.pet
        if not p.needs_attention():
            return ""
        if p.asleep and p.lights:
            w = "lights!"
        elif p.sick:
            w = "sick!"
        elif p.hunger == 0:
            w = "hungry!"
        elif p.strength == 0:
            w = "effort empty!"
        elif p.poop >= 3:
            w = "messy!"
        elif p.energy <= 0:
            w = "exhausted!"
        else:
            w = "misbehaving!"
        return (f"[{theme.NEG}]⚠ {(p.name or '?')[:10]} {w}[/] [dim]·[/] "
                + menu.hints(("ESC", "home")))

    def strip(self):
        """The message box under the LCD = the lobby's CONTEXT layer (hint
        overhaul 2026-07-10): session scenes keep their prompts, every other
        phase pops the hints for exactly what the keys do right now."""
        if self.bshow is not None:
            return "[dim]SPACE skip[/]"
        if self.jshow is not None and self.jphase == "result":
            name = (self.jresult or {}).get("name", "?")
            if self.jshow.phase == "fused":
                # every variant <= 40 with the longest dex name (menu-bounds
                # budget): 2+19+11 / 2+19+19 / 2+19+13
                if self.j_confirmed and not self.j_partner_confirmed:
                    return f"→ [b]{name}[/]  [dim]· waiting…[/]"
                if self.j_peer_two_phase:
                    return f"→ [b]{name}[/] [dim]· ENTER fuse · ESC[/]"
                return f"→ [b]{name}[/]  [dim]· ENTER fuse[/]"
            return "DNA… connect!  [dim]· ENTER skip[/]"
        if self.phase in ("jogress", "battle"):
            return ""                      # session text phases prompt in-LCD
        if self.phase == "login":
            return menu.hints(("TAB", "field"), ("ENTER", "go"), ("ESC", "back"))
        if self.phase == "ladder":
            return menu.hints(("TAB", "lobby"), ("ESC", "back"))
        if self.phase == "dm":
            cue = self._care_cue()      # the DM thread live-ticks too
            if cue:
                return cue
            return menu.hints(("ENTER", "send"), ("ESC", "back")) + \
                "  [dim]— thread saved[/]"
        if self.invite_prompt is not None:
            return menu.hints(("Y", "accept"), ("N", "decline"))
        if self.action_for is not None:
            _, _, plive = self.action_for
            if plive:
                return menu.hints(("B", "battle"), ("J", "jogress"),
                                  ("V", "DMs"), ("X", "block"))
            return menu.hints(("P", "ping"), ("V", "DMs"), ("X", "block"))
        if self.pm_to is not None:
            return menu.hints(("ENTER", "send ✉"), ("ESC", "cancel"))
        # the pet's alarm outranks everything social -- it only fires in the
        # phases the app live-ticks (lobby/dm), which are exactly the phases
        # that reach here past the session/login/prompt returns above
        cue = self._care_cue()
        if cue:
            return cue
        # the open room: a fresh ✉ pops its own nudge ahead of the key chrome
        unread = sorted(self.state.unread) if self.state else []
        if unread and not self.rost_hidden:
            who = unread[0][:12] + ("…" if len(unread) > 1 else "")
            return f"[b]✉ {who}[/][dim] unread — V on their name[/]"
        if self.rost_hidden:
            return menu.hints(("←", "players"), ("↑↓", "scroll"),
                              ("ESC", "live/leave"))
        return menu.hints(("→", "fold"), ("↑↓", "pick"),
                          ("ENTER", "act"), ("PgUp", "log"))

    def text(self):
        if self.phase == "login":
            return self._text_login()
        if self.phase == "jogress":
            return self._text_jogress()
        if self.phase == "battle":
            return self._text_battle()
        if self.phase == "dm":
            return self._text_dm()
        if self.phase == "ladder":
            return self._text_ladder()
        return self._text_lobby()

    def _text_login(self):
        return self.entry.text()

    def _text_jogress(self):
        t = Text()
        pname = self.partner[1] if self.partner else "?"
        if self.jphase == "result":
            if self.jshow is not None:          # the real fusion scene plays
                return self.jshow.text()
            me = self._card()["name"]
            other = self.partner_species or pname
            t.append("\n  ✦ JOGRESS ✦\n\n", style=INK_B)
            t.append(f"  {me} + {other}\n", style=INK)
            t.append(f"   →  {self.jresult['name']}\n\n", style=INK_B)
            if self.j_confirmed and not self.j_partner_confirmed:
                t.append("  waiting for the partner…", style=DIM)
            elif self.j_peer_two_phase:
                t.append("  [Enter] fuse    [Esc] decline", style=DIM)
            else:
                t.append("  [Enter] complete the fusion", style=DIM)
        elif self.jphase == "failed":
            t.append("\n  NO RESONANCE\n\n", style=INK_B)
            t.append(f"  {self.fail_reason}\n\n", style=INK)
            t.append("  [Enter] back to lobby", style=DIM)
        else:
            t.append("\n  FUSING…\n\n", style=INK_B)
            # a 24-char account name ran this line to 43 > the 40-col LCD
            # (menu-bounds audit 2026-07-07): the name field marquees instead
            t.append(f"  syncing DNA with {marquee(pname, 21, getattr(self, '_mq', 0) // 2)}\n\n", style=INK)
            t.append("  [Esc] cancel", style=DIM)
        return t

    def _text_battle(self):
        if self.bshow is not None:              # the round's volley replay
            return self.bshow.text()
        t = Text()
        pname = self.partner[1] if self.partner else "?"
        if self.bphase == "card":
            t.append("\n  BATTLE\n\n", style=INK_B)
            t.append(f"  vs {pname}\n\n", style=INK)
            t.append("  preparing…", style=DIM)
            return t
        if self.bphase == "over":
            t.append("\n  " + self.bt_outcome + "\n\n", style=INK_B)
            if self.bt_reward:
                t.append(f"  {self.bt_reward}\n\n", style=INK)
            t.append("  [Enter] back to lobby", style=DIM)
            return t
        me = self._card()["name"]
        oc = self.opp_card or {}
        t.append(f"  vs {pname[:10]}'s {str(oc.get('name', '?'))[:12]}"
                 f" · {str(oc.get('stage', '?'))[:9]}\n\n", style=DIM)
        t.append(f"  {_fit(me, 10)}{self.my_hp:>3}/{self.my_max:<2} [{_hpbar(self.my_hp, self.my_max)}]\n", style=INK_B)
        t.append(f"  {_fit(pname, 10)}{self.opp_hp:>3}/{self.opp_max:<2} [{_hpbar(self.opp_hp, self.opp_max)}]\n\n", style=INK)
        t.append(f"  {self.bt_log}\n\n" if self.bt_log else "\n\n", style=INK)
        if self.bphase == "wait":
            t.append("  syncing the arena…", style=DIM)
        else:
            t.append("  [SPACE] next volley   [ESC] forfeit", style=INK_B)
        return t

    def _chat_w(self):
        """The chat column's width: the folded player box cedes its columns."""
        return CHATW + ROSTW + 1 if self.rost_hidden else CHATW

    def _chat_rows(self):
        """The wrapped history as (line, style) rows, oldest first -- one
        style per MESSAGE (chat polish 2026-07-07): your own lines dim (you
        know what you said), PMs and lines that mention your name bright,
        join/leave notices dim; wrap continuations hang a 1-col indent so a
        long message reads as ONE message, not three."""
        s = self.state
        me = (s.me_name or "") if s else ""
        cw = self._chat_w()
        rows = []
        for nm, tx in (s.chat if s else []):
            if not nm:                                     # join/leave notice
                sty, parts = DIM, _wrap(f"· {tx}", cw - 1)
            elif str(nm) == ANNOUNCE:
                # the dev's line -- a new release, a heads-up -- used to render in
                # plain INK as "📢: text", i.e. indistinguishable from chatter and
                # reading like a PLAYER NAMED 📢 was talking.  It is the loudest
                # thing in the room: bright, and no name-colon (chat polish 07-14)
                sty, parts = INK_B, _wrap(f"{ANNOUNCE} {tx}", cw - 1)
            else:
                pm = str(nm).startswith("✉")
                mine = bool(me) and (nm == me or str(nm).startswith("✉→"))
                mention = bool(me) and me.lower() in str(tx).lower()
                # mine first: my own echo (chat or ✉→ PM) always reads dim
                sty = DIM if mine else (INK_B if (pm or mention) else INK)
                parts = _wrap(f"{nm}: {tx}", cw - 1)
            rows.append((parts[0], sty))
            rows.extend((" " + ln, sty) for ln in parts[1:])
        return rows

    def _text_lobby(self):
        s = self.state
        others = self._others()
        online = len(s.roster) if s else 0
        me = (s.me_name if s and s.me_name else None) or "connecting…"
        t = Text()
        cw = self._chat_w()
        rows = self._chat_rows()
        self.scroll = max(0, min(self.scroll, max(0, len(rows) - BODY)))
        # ASCII only in this column (the CELL-WIDTH LAW: rjust counts chars)
        in_room = bool(s and getattr(s, "room", None))
        right = (f"▲{self.scroll} back" if self.scroll
                 else (f"{online} in room" if in_room else f"{online} on"))
        # header: identity + the live/scroll marker (folded: no divider column)
        # -- your OWN worn honor shows here (read locally, so it's right even
        # before the roster syncs); a long title marquees, the chrome holds
        worn = data.title_name(persistence.get_title_worn())
        me_line = f"you: {me}" + (f" · ★{worn}" if worn else "")
        mw = cw - ROSTW if self.rost_hidden else CHATW
        mq = getattr(self, "_mq", 0) // 2
        t.append(_fit(marquee(me_line, mw, mq), mw) if cell_len(me_line) > mw
                 else _fit(me_line, mw), style=INK_B)        # confirm your identity
        if not self.rost_hidden:
            t.append("│", style=DIM)
        t.append(right.rjust(ROSTW)[:ROSTW] + "\n", style=INK_B)
        end = len(rows) - self.scroll
        view = rows[max(0, end - BODY):end]
        view = [("", INK)] * (BODY - len(view)) + view
        if not rows:                                       # the empty room
            hint = "— say hi, the room hears you —"
            if cell_len(hint) > cw:                        # folded col fits it; narrow one doesn't
                hint = "— say hi —"
            view[BODY // 2] = (hint.center(cw), DIM)
        sel = min(self.sel, len(others) - 1) if others else 0
        rlo = max(0, min(sel - BODY // 2, len(others) - BODY)) if len(others) > BODY else 0
        for i in range(BODY):
            t.append(_fit(view[i][0], cw), style=view[i][1])
            if self.rost_hidden:                 # the box is folded: chat owns the row
                t.append("\n")
                continue
            t.append("│", style=DIM)
            ridx = rlo + i
            if ridx < len(others):
                pl = others[ridx]
                cur = ridx == sel
                ghost = not pl.get("live", True)     # playing, not in the room
                nm = pl["name"]
                unread = bool(s) and nm in s.unread
                blk = bool(s) and nm in s.blocked
                mark = "✉" if unread else ("✕" if blk else ("·" if ghost else ""))
                sty = SEL if cur else (INK_B if unread else (DIM if (ghost or blk) else INK))
                # a worn honor stars the roster entry -- the room sees who's
                # titled at a glance; an entry too long for the column
                # MARQUEES (field-scroll doctrine) so the star is never lost.
                # marquee is char-based; the _fit wrapper keeps wide glyphs
                # (emoji names) inside the column per the cell-width law
                star = " ★" if (pl.get("pet") or {}).get("title") else ""
                pre, label = (">" if cur else " "), mark + nm + star
                if cell_len(pre + label) > ROSTW:
                    label = marquee(label, ROSTW - 1, getattr(self, "_mq", 0) // 2)
                t.append(_fit(pre + label, ROSTW), style=sty)
            elif i == 0 and not others:
                t.append(_fit(" nobody yet", ROSTW), style=DIM)
            else:
                t.append(_fit("", ROSTW), style=INK)
            t.append("\n")
        if self.pm_to is not None:                           # the input line is a PM compose
            label = f"✉{self.pm_to[1][:8]}: "
        else:
            label = "say: "
        t.append(label, style=INK_B)
        fw = CHATW + ROSTW - cell_len(label)
        shown = self.buf if cell_len(self.buf) < fw else _tail_cells(self.buf, fw - 1)
        caret = "_" if (getattr(self, "_mq", 0) // 5) % 2 == 0 else " "
        t.append(_fit(shown + caret, fw) + "\n", style=INK)
        # the prompt lines: the KEY HINTS are fixed chrome and must never clip
        # off the end -- a 24-char name used to push [Y]/[N] and [Esc] out of
        # the 38-col line entirely (lobby audit 2026-07-07); the NAME field
        # marquees instead (the v0.2.349 field-scroll doctrine)
        w = CHATW + ROSTW + 1
        mq = self._mq // 2 if hasattr(self, "_mq") else 0
        if self.invite_prompt is not None:
            inv = self.invite_prompt
            blurb = self._pet_of(inv.get("from_id"))
            who = f"{inv.get('from_name', '?')} ({blurb})" if blurb else inv.get("from_name", "?")
            tail = f" invites {inv['kind']}  [Y]/[N]"
            t.append(_fit(marquee(who, w - len(tail), mq) + tail, w), style=INK_B)
        elif self.action_for is not None:
            pid, pname, plive = self.action_for
            blurb = self._pet_of(pid)
            who = f"{pname} ({blurb})" if blurb else pname
            if self.state and pname in self.state.blocked:
                acts = "[X]unblock  [ESC]"
            elif plive:
                acts = "[B]attle [J]og [V] DMs [X]block [ESC]"
            else:
                acts = "not in lobby — [P]ing [V] DMs [X]block [ESC]"
            full = f"{who}:  {acts}"
            # whole line scrolls when it overflows (Joel 2026-07-09), else static
            t.append(marquee(full, w, mq) if len(full) > w else _fit(full, w), style=INK_B)
        elif self.scroll:
            # scrolled into the log: the line teaches its own way back
            t.append("▲ older — PgUp/PgDn · ESC back to live"[:w], style=DIM)
        else:
            line = self.status
            if self.rost_hidden and line.startswith("↑↓ pick"):
                # the box is folded: ↑↓ drive the log now, not the roster pick
                line = "↑↓ scroll · ← player box · Esc leave"
            elif others and line.startswith("↑↓ pick"):
                p = others[sel]
                if p.get("live", True):
                    blurb = self._pet_of(p["id"])
                    if blurb:
                        tail = " — Enter to act"
                        line = marquee(f"{p['name']}: {blurb}", w - len(tail), mq) + tail
                else:
                    tail = " — Enter to msg"
                    line = marquee(f"{p['name']} is playing", w - len(tail), mq) + tail
            t.append(line[:w], style=DIM)
        return t
