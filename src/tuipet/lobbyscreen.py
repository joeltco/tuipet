"""Multiplayer lobby panel — name login, presence, chat, jogress + battle sessions.

Chat-focused layout: a scrolling chat log on the left, a roster sidebar on the
right. Phases:

  name     type a handle, Enter to join  (only when no cached tamer name)
  lobby    chat default; Up/Down pick a player; Enter on empty input opens that
           player's action menu ([B]attle / [J]ogress); invites pop a [Y]/[N]
  jogress  both relay their pet's attribute, each resolves its fusion locally
           (jogress.resolve), shows the result, Enter evolves the pet
  battle   host-authoritative PvP: both relay battle cards, each round both pick
           an attribute, the inviter (host) resolves via the real engine and
           relays the absolute result; the guest displays it. PvP wins record
           onto the pet (evolution credit) just like PvE.

Decoupled from the app: `on_connect(name, card) -> LobbyClient` lets the app own
the WebSocket worker's lifecycle. Colours come from the live theme.
"""
from __future__ import annotations

from rich.text import Text

from . import data
from . import jogress
from . import battle
from . import battlescreen
from . import jogressscreen
from .net import CHAT_CAP
from .render import marquee
from .theme import INK, INK_B, DIM, SEL

CHATW = 25
ROSTW = 12
BODY = 8
CHAT_MAX = 400          # server MAX_CHAT: the local input buffer stops here too
ATTACK_KEYS = {"1": "Vaccine", "2": "Data", "3": "Virus"}


def _fit(s, w):
    s = str(s)
    return s[:w].ljust(w)


def _wrap(s, w):
    """Word-wrap `s` into lines of width <= w, hard-splitting any over-long word."""
    out, line = [], ""
    for word in str(s).split(" "):
        while len(word) > w:
            if line:
                out.append(line); line = ""
            out.append(word[:w]); word = word[w:]
        if not line:
            line = word
        elif len(line) + 1 + len(word) <= w:
            line += " " + word
        else:
            out.append(line); line = word
    if line:
        out.append(line)
    return out or [""]


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
        t.append("  [Tab] switch  [Enter] go  [Esc] back", style=DIM)
        return t


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
        self.action_for = None
        self.pm_to = None              # (id, name): the input line is a PM compose
        self.invite_prompt = None
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
        self.phase = "lobby"
        self.status = "Connecting…"

    # ---- presence card ---------------------------------------------------
    def _card(self):
        _, by = data.load_sprites()
        info = by.get(self.pet.num, {})
        return {"name": getattr(self.pet, "name", None) or info.get("name") or "Egg",
                "stage": self.pet.stage, "num": self.pet.num,
                "attr": getattr(self.pet, "attribute", "") or info.get("attribute") or "None"}

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
            return "zzz... asleep"
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
        """'Agumon · Champion' for a roster id ('' when unknown)."""
        for pl in (self.state.roster if self.state else []):
            if pl["id"] == pid:
                pet = pl.get("pet") or {}
                nm, st = pet.get("name"), pet.get("stage")
                return f"{nm} · {st}" if nm and st else (nm or "")
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
        s = self.state
        if not s:
            return
        for m in list(s.inbox):
            t = m.get("t")
            if t == "invite":
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
                        self._enter_session(m.get("from_id"), m["from_name"], m.get("kind"), host=True)
                    else:                                  # already busy -> free the accepter
                        self.client.relay(m.get("from_id"), {"kind": m.get("kind"), "abort": True})
                elif m.get("busy"):
                    self.status = f"{m['from_name']} is busy."
                else:
                    self.status = f"{m['from_name']} declined."
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
            self.status = "↑↓ pick · Enter chat/act · Esc leave"
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
            ids = {pl["id"]: pl["name"] for pl in s.roster}
            old_ids = getattr(self, "_seen_ids", None)
            if old_ids is not None:
                for pid, nm in ids.items():
                    if pid not in old_ids and pid != s.me_id:
                        s.chat.append(("", f"{nm} joined"))
                for pid, nm in old_ids.items():
                    if pid not in ids and pid != s.me_id:
                        s.chat.append(("", f"{nm} left"))
                del s.chat[:-CHAT_CAP]      # the one cap, shared with net.py
            self._seen_ids = ids
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
            self.client.relay(pid, {"kind": "battle", "t": "card",
                                    "card": battle.battle_card(self.pet)})
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
                self._battle_begin(payload.get("card") or {})
            elif bt == "choice" and self.is_host and self.bphase in ("choose", "wait"):
                self.bt_opp_choice = payload.get("attr")
                self._host_resolve()
            elif bt == "result" and not self.is_host and self.bphase == "wait":
                self._apply_result(payload, as_host=False)

    # ---- battle ----------------------------------------------------------
    def _battle_begin(self, opp_card):
        self.opp_card = opp_card
        if self.is_host:
            self.battle = battle.Battle(self.pet, enemy=dict(opp_card))
            self.my_max = self.my_hp = self.battle.pet_max
            self.opp_max = self.opp_hp = self.battle.enemy_max
        else:
            # the guest's own trained HP (its battle_card), not the stage table --
            # the table under-read a trained pet's bar until round one corrected it
            self.my_max = self.my_hp = battle.battle_card(self.pet)["hp"]
            self.opp_max = self.opp_hp = max(2, opp_card.get("hp", 10))
        self.bphase, self.bt_log = "choose", ""

    def _host_resolve(self):
        if self.battle is None or not (self.bt_my_choice and self.bt_opp_choice):
            return
        b = self.battle
        b._forced_enemy_attr = self.bt_opp_choice
        b.play_round(self.bt_my_choice)               # auto-records onto the host pet when it ends
        res = {"kind": "battle", "t": "result",
               "host_dealt": b.last_player_damage, "guest_dealt": b.last_enemy_damage,
               "hattr": self.bt_my_choice, "gattr": self.bt_opp_choice,
               "hhp": max(0, b.pet_hp), "ghp": max(0, b.enemy_hp),
               "host_first": b.last_player_first,   # additive: drives the volley replay
               "over": b.over, "host_alive": b.pet_hp > 0, "guest_alive": b.enemy_hp > 0}
        self.client.relay(self.partner[0], res)
        self._apply_result(res, as_host=True)

    def _apply_result(self, res, as_host):
        if as_host:
            dealt, taken = res["host_dealt"], res["guest_dealt"]
            my_attr, opp_attr = res.get("hattr"), res.get("gattr")
            my_alive, opp_alive = res["host_alive"], res["guest_alive"]
            mine_first = bool(res.get("host_first", True))
        else:
            dealt, taken = res["guest_dealt"], res["host_dealt"]
            my_attr, opp_attr = res.get("gattr"), res.get("hattr")
            my_alive, opp_alive = res["guest_alive"], res["host_alive"]
            mine_first = not res.get("host_first", True)
        # the round REPLAYS as the real alternating-view volley (lobby audit
        # 2026-07-04: PvP was a text log while PvE animates) -- built from the
        # hp BEFORE this round, then the choose/over screen takes over
        self._stage_volley(dealt, taken, my_attr, opp_attr, mine_first)
        if as_host:
            self.my_hp, self.opp_hp = res["hhp"], res["ghp"]
        else:
            self.my_hp, self.opp_hp = res["ghp"], res["hhp"]
        mine = data.move_name(self.pet.num, my_attr) or my_attr or "?"
        theirs = data.move_name((self.opp_card or {}).get("num", -1), opp_attr) or opp_attr or "?"
        self.bt_log = f"{mine} → {dealt} dmg\n  {theirs} ← {taken} dmg"
        if not res.get("over"):
            self.sfx = "strongHit" if dealt >= taken and dealt > 0 else "attackHit"
        self.bt_my_choice = self.bt_opp_choice = None
        if res.get("over"):
            self.bphase = "over"
            self.sfx = "attack"
            won = my_alive and not opp_alive
            if not my_alive:                       # own HP gone (incl. double-KO) = loss (battleEnd)
                self.bt_outcome = "YOU LOSE…"
            elif not opp_alive:
                self.bt_outcome = "★ YOU WIN! ★"
            else:
                self.bt_outcome = "DRAW"
            if as_host:
                self.bt_reward = getattr(self.battle, "reward", None)
                self.bt_payload = ("battle_msg", self.bt_outcome)   # engine already recorded
            else:
                self.bt_reward = None
                self.bt_payload = ("battle_record", won, self.opp_card)
        else:
            self.bphase = "choose"

    def _stage_volley(self, dealt, taken, my_attr, opp_attr, mine_first):
        """A presentation-only BattlePanel replays the round: my pet RIGHT, the
        opponent's LEFT, orbs/hit/dodge from the relayed numbers."""
        try:
            card = dict(self.opp_card or {})
            if not card.get("num"):
                return
            show = battlescreen.BattlePanel(self.pet, enemy=card)
            show.pet_attr = my_attr or "Vaccine"
            show.foe_attr = opp_attr or "Vaccine"
            show.timeline = battlescreen.round_timeline(
                self.my_hp, self.opp_hp, dealt, taken, mine_first)
            show.i = 0
            show.phase = "anim"
            show._last_m = None
            self.bshow = show
        except Exception:
            self.bshow = None                   # presentation must never break the bout

    def _key_battle(self, k):
        if self.bshow is not None:              # the round is replaying
            if k in ("space", "enter", "escape"):
                self.bshow = None               # skip straight to the choose/over screen
            return None
        if self.bphase == "over":
            if k in ("enter", "space", "escape"):
                if self.bt_payload and self.bt_payload[0] == "battle_record":
                    self.pet.record_battle(self.bt_payload[1], self.bt_payload[2])  # guest records its own result
                self._return_to_lobby(self.bt_outcome)   # host already recorded via the engine
            return None
        if self.bphase == "choose":
            if k in ATTACK_KEYS:
                self.bt_my_choice = ATTACK_KEYS[k]
                self.client.relay(self.partner[0], {"kind": "battle", "t": "choice", "attr": ATTACK_KEYS[k]})
                self.bphase = "wait"
                if self.is_host:
                    self._host_resolve()
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
        return self._key_lobby(k)

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
        msg = jogress.fuse(self.pet, self.jresult["num"])
        if getattr(self, "jpartner_sick", False):
            # canon startJogress: checkSick(90) -- swapping DNA with a
            # sick partner is a NEAR-CERTAIN catch
            if self.pet._check_sick(jogress.JOGRESS_SICK_CHANCE):
                msg += "  ...and it caught something."
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

    def _key_lobby(self, k):
        if self.invite_prompt is not None:
            inv = self.invite_prompt
            if k in ("y", "Y"):
                self.client.respond(inv.get("from_id"), inv["kind"], True)
                self.invite_prompt = None
                self._enter_session(inv.get("from_id"), inv["from_name"], inv["kind"], host=False)
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
            elif k in ("m", "M"):
                # compose a private message: the input line retargets
                self.pm_to = (pid, pname)
                self.buf = ""
                self.status = f"PM → {pname} — Enter send, Esc cancel"
                self.action_for = None
            elif k == "escape":
                self.action_for = None
            return None
        if k == "escape":
            if self.scroll:                    # scrolled log: snap to live first
                self.scroll = 0
                return None
            if self.pm_to is not None:
                self.pm_to, self.buf = None, ""
                self.status = "PM cancelled."
                return None
            return ("done", None)
        if k == "pageup":
            # chat scrollback (polish 2026-07-07): CHAT_CAP lines of history
            # existed but only the last 8 ever showed
            self.scroll += BODY - 1            # _text_lobby clamps to the log
            return None
        if k == "pagedown":
            self.scroll = max(0, self.scroll - (BODY - 1))
            return None
        if k == "up":
            self.sel = max(0, self.sel - 1); return None
        if k == "down":
            self.sel = min(max(0, len(self._others()) - 1), self.sel + 1); return None
        if k == "enter":
            self.scroll = 0                    # speaking snaps the view live
            if self.pm_to is not None:
                if self.buf.strip():
                    self.client.pm(self.pm_to[0], self.buf.strip())
                    self.status = f"✉ sent to {self.pm_to[1]}"
                self.pm_to, self.buf = None, ""
            elif self.buf.strip():
                self.client.chat(self.buf.strip()); self.buf = ""
            else:
                others = self._others()
                if others:
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
    def strip(self):
        """One line under the LCD while a session SCENE plays (the text phases
        carry their own prompts in-LCD)."""
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
            return "DNA... connect!  [dim]· ENTER skip[/]"
        return ""

    def text(self):
        if self.phase == "login":
            return self._text_login()
        if self.phase == "jogress":
            return self._text_jogress()
        if self.phase == "battle":
            return self._text_battle()
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
            t.append("  waiting for opponent…", style=DIM)
        else:
            t.append("  attack: [1]Vaccine [2]Data [3]Virus", style=INK_B)
        return t

    def _chat_rows(self):
        """The wrapped history as (line, style) rows, oldest first -- one
        style per MESSAGE (chat polish 2026-07-07): your own lines dim (you
        know what you said), PMs and lines that mention your name bright,
        join/leave notices dim; wrap continuations hang a 1-col indent so a
        long message reads as ONE message, not three."""
        s = self.state
        me = (s.me_name or "") if s else ""
        rows = []
        for nm, tx in (s.chat if s else []):
            if not nm:                                     # join/leave notice
                sty, parts = DIM, _wrap(f"· {tx}", CHATW - 1)
            else:
                pm = str(nm).startswith("✉")
                mine = bool(me) and (nm == me or str(nm).startswith("✉→"))
                mention = bool(me) and me.lower() in str(tx).lower()
                # mine first: my own echo (chat or ✉→ PM) always reads dim
                sty = DIM if mine else (INK_B if (pm or mention) else INK)
                parts = _wrap(f"{nm}: {tx}", CHATW - 1)
            rows.append((parts[0], sty))
            rows.extend((" " + ln, sty) for ln in parts[1:])
        return rows

    def _text_lobby(self):
        s = self.state
        others = self._others()
        online = len(s.roster) if s else 0
        me = (s.me_name if s and s.me_name else None) or "connecting…"
        t = Text()
        t.append(_fit(f"you: {me}", CHATW), style=INK_B)     # confirm your identity
        t.append("│", style=DIM)
        rows = self._chat_rows()
        self.scroll = max(0, min(self.scroll, max(0, len(rows) - BODY)))
        right = (f"▲{self.scroll} back" if self.scroll else f"{online} on")
        t.append(right.rjust(ROSTW)[:ROSTW] + "\n", style=INK_B)
        end = len(rows) - self.scroll
        view = rows[max(0, end - BODY):end]
        view = [("", INK)] * (BODY - len(view)) + view
        if not rows:                                       # the empty room
            view[BODY // 2] = ("— say hi, the room hears you —"[:CHATW], DIM)
        sel = min(self.sel, len(others) - 1) if others else 0
        rlo = max(0, min(sel - BODY // 2, len(others) - BODY)) if len(others) > BODY else 0
        for i in range(BODY):
            t.append(_fit(view[i][0], CHATW), style=view[i][1])
            t.append("│", style=DIM)
            ridx = rlo + i
            if ridx < len(others):
                pl = others[ridx]
                cur = ridx == sel
                ghost = not pl.get("live", True)     # playing, not in the room
                t.append(_fit((">" if cur else " ") + ("·" if ghost else "") + pl["name"], ROSTW),
                         style=SEL if cur else (DIM if ghost else INK))
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
        fw = CHATW + ROSTW - len(label)
        shown = self.buf if len(self.buf) < fw else self.buf[-(fw - 1):]
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
            who = f"{inv['from_name']} ({blurb})" if blurb else inv["from_name"]
            tail = f" invites {inv['kind']}  [Y]/[N]"
            t.append(_fit(marquee(who, w - len(tail), mq) + tail, w), style=INK_B)
        elif self.action_for is not None:
            pid, pname, plive = self.action_for
            blurb = self._pet_of(pid)
            who = f"{pname} ({blurb})" if blurb else pname
            acts = "[B]attle [J]og [M]sg [Esc]" if plive else "not in lobby — [P]ing  [M]sg  [Esc]"
            t.append(_fit(marquee(who, w - len(acts) - 3, mq) + ":  " + acts, w),
                     style=INK_B)
        elif self.scroll:
            # scrolled into the log: the line teaches its own way back
            t.append("▲ older — PgUp/PgDn · Esc back to live"[:w], style=DIM)
        else:
            line = self.status
            if others and line.startswith("↑↓ pick"):
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
