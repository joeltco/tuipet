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
from .theme import INK, INK_B, DIM, SEL

CHATW = 25
ROSTW = 12
BODY = 8
ATTACK_KEYS = {"1": "Vaccine", "2": "Data", "3": "Virus"}


def _fit(s, w):
    s = str(s)
    return s[:w].ljust(w)


def _hpbar(hp, mx, w=10):
    fill = max(0, min(w, round(hp / mx * w))) if mx else 0
    return "█" * fill + "─" * (w - fill)


class NamePanel:
    """One-time tamer-name prompt shown at first launch; the app caches the result."""

    def __init__(self, default=""):
        self.buf = default
        self.sfx = None

    def key(self, k):
        if k in ("enter", "escape"):
            return ("done", self.buf.strip()[:24] or "Tamer")
        if k == "backspace":
            self.buf = self.buf[:-1]
        elif k == "space":
            self.buf += " "
        elif len(k) == 1 and k.isprintable():
            self.buf += k
        return None

    def text(self):
        t = Text()
        t.append("  WELCOME, TAMER\n", style=INK_B)
        t.append("\n  What should we call you?\n\n", style=DIM)
        t.append("  > ", style=INK_B)
        t.append(self.buf + "_", style=INK_B)
        t.append("\n\n  [Enter] confirm", style=DIM)
        return t


class LobbyPanel:
    def __init__(self, pet, on_connect, name=None):
        self.pet = pet
        self.on_connect = on_connect
        self.client = None
        self.state = None
        self.buf = ""
        self.sel = 0
        self.action_for = None
        self.invite_prompt = None
        self.sfx = None
        # jogress session
        self.partner = None
        self.partner_species = None
        self.jphase = None
        self.jresult = None
        self.fail_reason = None
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
        if name:
            self.client = self.on_connect(name, self._card())
            self.state = self.client.state
            self.phase = "lobby"
            self.status = "Connecting…"
        else:
            self.phase = "name"
            self.status = "Type a name, then Enter to join."

    # ---- presence card ---------------------------------------------------
    def _card(self):
        _, by = data.load_sprites()
        info = by.get(self.pet.num, {})
        return {"name": getattr(self.pet, "name", None) or info.get("name") or "Egg",
                "stage": self.pet.stage, "num": self.pet.num,
                "attr": getattr(self.pet, "attribute", "") or info.get("attribute") or "None"}

    def _others(self):
        return self.state.others() if self.state else []

    # ---- per-tick refresh (on_fast calls this) ---------------------------
    def anim(self):
        s = self.state
        if not s:
            return
        for m in list(s.inbox):
            t = m.get("t")
            if t == "invite":
                if self.phase == "lobby" and self.invite_prompt is None and self.action_for is None:
                    self.invite_prompt = m
                    self.sfx = "menu"
                else:
                    self.client.respond(m["from_id"], m.get("kind"), False)   # busy -> auto-decline
                s.inbox.remove(m)
            elif t == "invite_resp":
                s.inbox.remove(m)
                if m.get("accept"):
                    self._enter_session(m["from_id"], m["from_name"], m.get("kind"), host=True)
                else:
                    self.status = f"{m['from_name']} declined."
            elif t == "relay":
                s.inbox.remove(m)
                self._on_relay(m)
        if s.error:
            self.status = f"! {s.error}"
            s.error = None
        elif s.connected and self.status == "Connecting…":
            self.status = "Up/Down pick · Enter chat/act · Esc leave"
        # partner vanished mid-session
        if self.partner and not any(p["id"] == self.partner[0] for p in s.roster):
            if self.phase == "jogress" and self.jphase == "waiting":
                self.fail_reason, self.jphase = "Partner left.", "failed"
            elif self.phase == "battle" and self.bphase not in (None, "over"):
                self.bt_outcome = "Opponent left."
                self.bt_payload = ("battle_msg", "Opponent left — battle void.")
                self.bphase = "over"

    # ---- session orchestration ------------------------------------------
    def _enter_session(self, pid, pname, kind, host):
        self.partner = (pid, pname)
        if kind == "jogress":
            card = self._card()
            self.client.relay(pid, {"kind": "jogress", "attr": card["attr"],
                                    "num": card["num"], "name": card["name"]})
            self.phase, self.jphase = "jogress", "waiting"
            self.status = f"Fusing with {pname}…"
        elif kind == "battle":
            self.is_host = host
            self.phase, self.bphase = "battle", "card"
            self.client.relay(pid, {"kind": "battle", "t": "card",
                                    "card": battle.battle_card(self.pet)})
            self.status = f"Battle vs {pname}…"

    def _on_relay(self, m):
        if not self.partner or m.get("from_id") != self.partner[0]:
            return
        payload = m.get("payload") or {}
        kind = payload.get("kind")
        if kind == "jogress" and self.phase == "jogress" and self.jphase == "waiting":
            self.partner_species = payload.get("name")
            self.jresult = jogress.resolve(self.pet, payload.get("attr"))
            if self.jresult:
                self.jphase, self.sfx = "result", "jogress"
            else:
                self.fail_reason = jogress.can_jogress(self.pet) or "No resonance with that partner."
                self.jphase = "failed"
        elif kind == "battle" and self.phase == "battle":
            bt = payload.get("t")
            if bt == "card":
                self._battle_begin(payload.get("card") or {})
            elif bt == "choice" and self.is_host:
                self.bt_opp_choice = payload.get("attr")
                self._host_resolve()
            elif bt == "result" and not self.is_host:
                self._apply_result(payload, as_host=False)

    # ---- battle ----------------------------------------------------------
    def _battle_begin(self, opp_card):
        self.opp_card = opp_card
        if self.is_host:
            self.battle = battle.Battle(self.pet, enemy=dict(opp_card))
            self.my_max = self.my_hp = self.battle.pet_max
            self.opp_max = self.opp_hp = self.battle.enemy_max
        else:
            self.my_max = self.my_hp = battle.MAX_HEALTH.get(self.pet.stage, battle.MAX_HEALTH_DEFAULT)
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
               "hhp": max(0, b.pet_hp), "ghp": max(0, b.enemy_hp),
               "over": b.over, "host_alive": b.pet_hp > 0, "guest_alive": b.enemy_hp > 0}
        self.client.relay(self.partner[0], res)
        self._apply_result(res, as_host=True)

    def _apply_result(self, res, as_host):
        if as_host:
            self.my_hp, self.opp_hp = res["hhp"], res["ghp"]
            dealt, taken = res["host_dealt"], res["guest_dealt"]
            my_alive, opp_alive = res["host_alive"], res["guest_alive"]
        else:
            self.my_hp, self.opp_hp = res["ghp"], res["hhp"]
            dealt, taken = res["guest_dealt"], res["host_dealt"]
            my_alive, opp_alive = res["guest_alive"], res["host_alive"]
        self.bt_log = f"you hit {dealt} · took {taken}"
        self.bt_my_choice = self.bt_opp_choice = None
        if res.get("over"):
            self.bphase, self.sfx = "over", "attack"
            won = my_alive and not opp_alive
            if won:
                self.bt_outcome = "★ YOU WIN! ★"
            elif opp_alive and not my_alive:
                self.bt_outcome = "YOU LOSE…"
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

    def _key_battle(self, k):
        if self.bphase == "over":
            if k in ("enter", "space", "escape"):
                return ("done", self.bt_payload)
            return None
        if self.bphase == "choose":
            if k in ATTACK_KEYS:
                self.bt_my_choice = ATTACK_KEYS[k]
                self.client.relay(self.partner[0], {"kind": "battle", "t": "choice", "attr": ATTACK_KEYS[k]})
                self.bphase = "wait"
                if self.is_host:
                    self._host_resolve()
            elif k == "escape":
                return ("done", None)              # forfeit -> just leave; opponent sees you gone
            return None
        if self.bphase in ("card", "wait") and k == "escape":
            return ("done", None)
        return None

    # ---- input -----------------------------------------------------------
    def key(self, k):
        if self.phase == "name":
            return self._key_name(k)
        if self.phase == "jogress":
            return self._key_jogress(k)
        if self.phase == "battle":
            return self._key_battle(k)
        return self._key_lobby(k)

    def _key_name(self, k):
        if k == "escape":
            return ("done", None)
        if k == "enter":
            name = self.buf.strip() or "Tamer"
            self.client = self.on_connect(name, self._card())
            self.state = self.client.state
            self.phase, self.buf, self.status = "lobby", "", "Connecting…"
            return None
        return self._edit(k)

    def _key_jogress(self, k):
        if self.jphase == "result":
            if k in ("enter", "space", "escape"):
                return ("done", ("jogress", self.jresult["num"]))
            return None
        if self.jphase == "failed":
            if k in ("enter", "space", "escape"):
                return ("done", None)
            return None
        if k == "escape":
            return ("done", None)
        return None

    def _key_lobby(self, k):
        if self.invite_prompt is not None:
            inv = self.invite_prompt
            if k in ("y", "Y"):
                self.client.respond(inv["from_id"], inv["kind"], True)
                self.invite_prompt = None
                self._enter_session(inv["from_id"], inv["from_name"], inv["kind"], host=False)
            elif k in ("n", "N", "escape"):
                self.client.respond(inv["from_id"], inv["kind"], False)
                self.status, self.invite_prompt = "Declined.", None
            return None
        if self.action_for is not None:
            pid, pname = self.action_for
            if k in ("b", "B"):
                self.client.invite(pid, "battle"); self.status = f"Battle invite → {pname}"; self.action_for = None
            elif k in ("j", "J"):
                self.client.invite(pid, "jogress"); self.status = f"Jogress invite → {pname}"; self.action_for = None
            elif k == "escape":
                self.action_for = None
            return None
        if k == "escape":
            return ("done", None)
        if k == "up":
            self.sel = max(0, self.sel - 1); return None
        if k == "down":
            self.sel = min(max(0, len(self._others()) - 1), self.sel + 1); return None
        if k == "enter":
            if self.buf.strip():
                self.client.chat(self.buf.strip()); self.buf = ""
            else:
                others = self._others()
                if others:
                    p = others[min(self.sel, len(others) - 1)]
                    self.action_for = (p["id"], p["name"])
            return None
        return self._edit(k)

    def _edit(self, k):
        if k == "backspace":
            self.buf = self.buf[:-1]
        elif k == "space":
            self.buf += " "
        elif len(k) == 1 and k.isprintable():
            self.buf += k
        return None

    # ---- render ----------------------------------------------------------
    def text(self):
        if self.phase == "name":
            return self._text_name()
        if self.phase == "jogress":
            return self._text_jogress()
        if self.phase == "battle":
            return self._text_battle()
        return self._text_lobby()

    def _text_name(self):
        t = Text()
        t.append("  TUIPET LOBBY\n", style=INK_B)
        t.append("\n  Enter your tamer name:\n\n", style=DIM)
        t.append("  > ", style=INK_B)
        t.append(self.buf + "_", style=INK_B)
        t.append("\n\n  [Enter] join   [Esc] back", style=DIM)
        return t

    def _text_jogress(self):
        t = Text()
        pname = self.partner[1] if self.partner else "?"
        if self.jphase == "result":
            me = self._card()["name"]
            other = self.partner_species or pname
            t.append("\n  ✦ JOGRESS ✦\n\n", style=INK_B)
            t.append(f"  {me} + {other}\n", style=INK)
            t.append(f"   →  {self.jresult['name']}\n\n", style=INK_B)
            t.append("  [Enter] complete the fusion", style=DIM)
        elif self.jphase == "failed":
            t.append("\n  NO RESONANCE\n\n", style=INK_B)
            t.append(f"  {self.fail_reason}\n\n", style=INK)
            t.append("  [Enter] back to lobby", style=DIM)
        else:
            t.append("\n  FUSING…\n\n", style=INK_B)
            t.append(f"  syncing DNA with {pname}\n\n", style=INK)
            t.append("  [Esc] cancel", style=DIM)
        return t

    def _text_battle(self):
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
        t.append(f"  {_fit(me, 10)}{self.my_hp:>3}/{self.my_max:<2} [{_hpbar(self.my_hp, self.my_max)}]\n", style=INK_B)
        t.append(f"  {_fit(pname, 10)}{self.opp_hp:>3}/{self.opp_max:<2} [{_hpbar(self.opp_hp, self.opp_max)}]\n\n", style=INK)
        t.append(f"  {self.bt_log}\n\n" if self.bt_log else "\n\n", style=INK)
        if self.bphase == "wait":
            t.append("  waiting for opponent…", style=DIM)
        else:
            t.append("  attack:  [1] Vaccine  [2] Data  [3] Virus", style=INK_B)
        return t

    def _text_lobby(self):
        s = self.state
        others = self._others()
        online = len(s.roster) if s else 0
        me = (s.me_name if s and s.me_name else None) or "connecting…"
        t = Text()
        t.append(_fit(f"you: {me}", CHATW), style=INK_B)     # confirm your identity
        t.append("│", style=DIM)
        t.append(f"{online} on".rjust(ROSTW)[:ROSTW] + "\n", style=INK_B)
        chat = [f"{nm}: {tx}" for nm, tx in (s.chat[-BODY:] if s else [])]
        chat = [""] * (BODY - len(chat)) + chat
        for i in range(BODY):
            t.append(_fit(chat[i], CHATW), style=INK)
            t.append("│", style=DIM)
            if i < len(others):
                pl = others[i]
                marker = ">" if i == min(self.sel, len(others) - 1) else " "
                t.append(_fit(f"{marker}{pl['name']}", ROSTW),
                         style=SEL if marker == ">" else INK)
            elif i == 0 and not others:
                t.append(_fit(" nobody yet", ROSTW), style=DIM)
            else:
                t.append(_fit("", ROSTW), style=INK)
            t.append("\n")
        t.append("say: ", style=INK_B)                       # this is chat, not a login box
        t.append(_fit(self.buf + "_", CHATW + ROSTW - 5) + "\n", style=INK)
        if self.invite_prompt is not None:
            inv = self.invite_prompt
            t.append(f"{inv['from_name']} invites {inv['kind']}  [Y]/[N]", style=INK_B)
        elif self.action_for is not None:
            t.append(f"{self.action_for[1]}:  [B]attle  [J]ogress  [Esc]", style=INK_B)
        else:
            t.append(self.status[:CHATW + ROSTW], style=DIM)
        return t
