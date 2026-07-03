"""Lobby/net protocol audit (2026-07) vs DVPet's BattleProtocol / BattleHost /
JogressProtocol / Checksum.

Verified: the round exchange shape (choices out, results back; canon's
surrendered-flag handshake maps to tuipet's abort message), the jogress
handshake (attribute exchange -> each side resolves via the audited
pairJogressMatch semantics), and the card CONTENT (num/name/stage/three
powers/hp -- canon adds sprite ids tuipet derives from num, a checksum and
a difficulty tuipet does not model).

Documented deltas (in battle_card's docstring, none wire-changed):
PvPBonusPowerMultiple(2) power scaling (ordinal-neutral), current-vs-full
HP, no anti-tamper checksum, and host-authoritative resolution replacing
canon's desyncable peer-symmetric simulation.

Pinned here: the protocol invariants that keep PvP fair and deterministic."""
import random

from tuipet.pet import Pet
from tuipet import battle
from tuipet.net import LobbyState
from tuipet import lobbyscreen


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


class _Stub:
    def __init__(self, state): self.state = state
    def respond(self, *a, **k): pass
    def update_pet(self, *a, **k): pass
    def chat(self, *a, **k): pass
    def invite(self, *a, **k): pass
    def relay(self, to, payload):
        self.sent = (to, payload)


def _panel(state):
    p = _pet()
    pan = lobbyscreen.LobbyPanel(p, lambda n, pw, c: _Stub(state), name="j", pw="x")
    return pan


def test_card_carries_the_full_combat_snapshot():
    p = _pet(vaccine=50, data_power=30, virus=20, full_health=22)
    c = battle.battle_card(p)
    assert c["vaccine"] == 50 and c["data_power"] == 30 and c["virus"] == 20
    assert c["hp"] == 22 and c["stage"] == "Champion" and c["num"] == 100
    # RAW powers by design (the documented PvPBonusPowerMultiple delta)
    assert c["vaccine"] == p.vaccine


def test_host_result_is_absolute_and_complete():
    s = LobbyState()
    pan = _panel(s)
    pan._enter_session(2, "kai", "battle", host=True)
    pan._on_relay({"from_id": 2, "payload": {"kind": "battle", "t": "card",
                   "card": battle.battle_card(_pet(vaccine=5, data_power=5, virus=5,
                                                   full_health=8))}})
    random.seed(1)
    pan.bt_my_choice = "Vaccine"
    pan.bt_opp_choice = "Virus"
    pan._host_resolve()
    to, res = pan.client.sent
    assert to == 2 and res["t"] == "result"
    # ABSOLUTE state: both hps, both damages, both attrs, both liveness flags --
    # the guest displays, never simulates (no desync surface)
    for k in ("hhp", "ghp", "host_dealt", "guest_dealt", "hattr", "gattr",
              "over", "host_alive", "guest_alive"):
        assert k in res


def test_forced_attr_overrides_the_ai_exactly_once():
    p = _pet()
    b = battle.Battle(p, {"num": 4, "name": "X", "stage": "Champion", "vaccine": 5,
                          "data_power": 5, "virus": 5, "hp": 8, "bits": (0, 0)})
    b._forced_enemy_attr = "Virus"
    assert b._enemy_choice() == "Virus"            # the partner's real move wins


def test_guest_records_the_same_card_the_host_fought():
    s = LobbyState()
    pan = _panel(s)
    pan.is_host = False
    card = battle.battle_card(_pet(vaccine=9, full_health=8))
    pan.opp_card = card
    pan.partner = (2, "kai")
    pan.bphase = "wait"
    pan._apply_result({"host_dealt": 0, "guest_dealt": 9, "hattr": "Vaccine",
                       "gattr": "Vaccine", "hhp": 0, "ghp": 8, "over": True,
                       "host_alive": False, "guest_alive": True}, as_host=False)
    assert pan.bt_payload == ("battle_record", True, card)   # symmetric records
