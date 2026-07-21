"""The lobby's SESSION engine — the proto-3 PvP bout and the jogress
commit, as a mixin over LobbyPanel's state (modularize 2026-07-17).
lobbyscreen owns the room (connection, roster, keys); THIS module owns
what happens once two tamers face each other: the commit-reveal card
exchange, the seeded volley replay, the ladder report, the fusion and
companion commits.  _clamp_card is the untrusted-peer boundary — every
wire card passes through it.
"""
from __future__ import annotations

import hashlib
import random

from rich.cells import cell_len, chop_cells, set_cell_size  # noqa: F401
from rich.text import Text  # noqa: F401

from . import data  # noqa: F401
from . import jogress  # noqa: F401
from . import battle  # noqa: F401
from . import battlescreen  # noqa: F401
from . import jogressscreen  # noqa: F401
from . import menu  # noqa: F401
from . import persistence  # noqa: F401
from .net import ANNOUNCE, CHAT_CAP  # noqa: F401
from .render import marquee  # noqa: F401
from .theme import INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)

CHATW = 25
ROSTW = 12
BODY = 8
CHAT_MAX = 400          # server MAX_CHAT: the local input buffer stops here too
from .lobbychat import _fit, _wrap, _tail_cells, _hpbar  # noqa: F401



def _evo_note(pet):
    """L17 keeps online duels progression-neutral -- when this pet is mid
    WIN-gate the purse line says where the wins must come from ("i dont
    think its filling either way"; Joel bug report 2026-07-21).  Quiet for
    every pet that has no open WIN gate: the note is an answer, not a nag."""
    from . import lines as _lines
    wg = _lines.win_gate_progress(pet)
    return "  (evo: local wins only)" if wg and wg[0] < wg[1] else ""

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
        card["stage"] = rec.get("stage", "Rookie")
        card["attribute"] = rec.get("attribute", "Free")
    else:
        # unknown num (a newer build's dex): keep a KNOWN claimed stage so the
        # two engines stay symmetric.  Anything unrankable -- "Special"
        # included, whose old re-map elif was dead behind this membership
        # check -- lands on "Rookie": the same rank 3 _RANK's default already
        # gave it, now wearing the tuipet word instead of "Child"
        if card.get("stage") not in battle._RANK:
            card["stage"] = "Rookie"
        if card.get("attribute") not in ("Vaccine", "Virus", "Data", "Free"):
            card["attribute"] = "Free"
    card["hp"] = 5
    return card


class BoutMixin:
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
        # pet.add_bits died with the classic revert (v0.5.0) -- every online
        # payout has crashed on BOTH sides since; caught by the live two-bot
        # smoke 2026-07-17.  The raid claim's idiom is the house style.
        self.pet.bits += int(purse)
        self.bt_outcome = ("DRAW" if draw
                           else "\u2605 YOU WIN! \u2605" if won else "YOU LOSE\u2026")
        # ask the calendar, not the amount: the weekend loss purse (150)
        # equals the plain draw purse, which hid the tag on weekend losses
        from .pet import weekend_bonus
        self.bt_reward = f"+{purse}b" + ("  (weekend bonus!)" if weekend_bonus() > 1 else "") + _evo_note(self.pet)
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
        """Leave a battle in progress -> tell the opponent, then back to the lobby.
        Once the seeded fight is RUNNING the bout is committed: walking out is
        a forfeit LOSS, filed with the ladder like any decided bout -- ESC in
        "fight" used to relay only the abort, so a losing player could void
        the result at will while the winner's half expired unconfirmed
        (MED audit 2026-07-19).  Pre-commit (card/wait) stays a free back-out."""
        counted = self.bphase == "fight" and self.battle is not None
        if counted:
            opp_nm = (self.partner or (0, ""))[1] or (self.opp_card or {}).get("name")
            report = getattr(self.client, "ladder_report", None)
            if report and opp_nm:
                report(False, opp_nm)
            self.pet.record_battle(False, online=True)
        if self.partner:
            self.client.relay(self.partner[0], {"kind": "battle", "abort": True})
        self._return_to_lobby("Forfeit — counted as a loss." if counted
                              else "You forfeited.")
    def _opp_fled(self):
        """The partner walked out of a RUNNING seeded fight (abort relay or
        roster vanish): that is THEIR forfeit.  File the winner's half so the
        pair credits when their agreeing loss lands, and pay the win -- both
        sites used to call it void, so the ladder never heard of it (MED
        audit 2026-07-19)."""
        opp_nm = (self.partner or (0, ""))[1] or (self.opp_card or {}).get("name")
        report = getattr(self.client, "ladder_report", None)
        if report and opp_nm:
            report(True, opp_nm)
        from .pet import online_reward
        purse = online_reward(True)
        self.pet.record_battle(True, online=True)
        self.pet.bits += int(purse)
        self.bt_outcome = "Opponent fled — you win!"
        from .pet import weekend_bonus
        self.bt_reward = f"+{purse}b" + ("  (weekend bonus!)"      # calendar, not amount
                                         if weekend_bonus() > 1 else "") + _evo_note(self.pet)
        self.bt_payload = ("battle_msg", self.bt_outcome)
        self.bphase = "over"

    # ---- input -----------------------------------------------------------
    def _commit_fusion(self):
        """BOTH confirms are in (or the peer is legacy): perform the fusion --
        the same path as offline jogress.  A COMPANION lends its data and
        stays itself (canon one-sided doors; jogress audit 2026-07-17)."""
        if self.partner:                # swapping DNA is the strongest connection
            persistence.record_connection(self.partner[1])
        if (self.jresult or {}).get("companion"):
            self.sfx = "jogress"
            self._return_to_lobby("It lent its power to the fusion.")
            return
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
            verb = ("lend" if (self.jresult or {}).get("companion")
                    else "fuse")       # a companion LENDS and stays itself --
            #                            "fuse" promised a change that never
            #                            comes (round 33)
            if self.j_confirmed and not self.j_partner_confirmed:
                t.append("  waiting for the partner…", style=DIM)
            elif self.j_peer_two_phase:
                t.append(f"  [Enter] {verb}    [Esc] decline", style=DIM)
            else:
                t.append(f"  [Enter] complete the {verb}", style=DIM)
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
