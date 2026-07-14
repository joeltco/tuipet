"""Seeded symmetric PvP (proto 2) — canon BattleProtocol's peer-symmetric
exchange with the desync solved by a shared PRNG seed (commit-reveal nonces).

Pins: engine determinism (two engines, same cards + seed -> bit-identical
bouts, initiative coin flips included), the full two-panel bout with only
card/pick messages on the wire, both sides recording + ladder-reporting from
their OWN verdict, the commit-reveal checksum voiding a ground seed, and the
legacy fallback for a peer whose card has no proto.
"""
import random

from tuipet import lobbyscreen
from tuipet.battle import Battle, CardPet, battle_card, own_pick
from tuipet.net import LobbyState
from tuipet.pet import Pet


def _card(**kw):
    base = {"num": 100, "name": "A", "stage": "Champion",
            "vaccine": 5, "data_power": 5, "virus": 5, "hp": 10,
            "sick": False, "attribute": "Vaccine", "free": False,
            "field": "", "proto": 2, "bits": (1, 5)}
    base.update(kw)
    return base


# ---- the card ----------------------------------------------------------------

def test_battle_card_speaks_proto_2():
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.free_style = True
    c = battle_card(p)
    assert c["proto"] == 2
    assert c["free"] is True                 # the style bonus is BAKED in
    assert "field" in c                      # chip Field conditions see the truth


def test_enemy_free_bonus_finally_counts():
    """The host-authoritative era silently dropped the guest's Free +1."""
    p = Pet(num=100, stage="Champion")
    b = Battle(p, enemy=_card(free=True), source="pvp")
    assert b._enemy_counts == {"Vaccine": 6, "Data": 6, "Virus": 6}
    b2 = Battle(p, enemy=_card())            # legacy card: no key, no bonus
    assert b2._enemy_counts == {"Vaccine": 5, "Data": 5, "Virus": 5}


# ---- the engine ---------------------------------------------------------------

def test_final_attrs_takes_the_pick_verbatim():
    """Seeded PvP resolves Free/refusal at pick time: play_round must not
    re-roll or override either side's FINAL attribute."""
    p = Pet(num=100, stage="Champion", vaccine=9, data_power=1, virus=1)
    p.free_style = True                      # would normally override the pick
    b = Battle(p, enemy=_card(), source="pvp", final_attrs=True)
    b._forced_enemy_attr = "Data"
    b.play_round("Virus")
    assert b.last_player_attr == "Virus"     # not the own-way Vaccine
    q = Pet(num=100, stage="Champion", vaccine=9, data_power=1, virus=1)
    q.free_style = True
    b2 = Battle(q, enemy=_card(), source="pvp")
    b2._forced_enemy_attr = "Data"
    b2.play_round("Virus")
    assert b2.last_player_attr == "Vaccine"  # legacy path still fights its own way


def test_own_pick_brute_logic():
    mine = {"Vaccine": 9, "Data": 1, "Virus": 0}
    opp = {"Vaccine": 5, "Data": 5, "Virus": 5}
    assert own_pick(mine, opp) == "Vaccine"          # only +1 delta
    assert own_pick({"Vaccine": 0, "Data": 0, "Virus": 0}, opp, fallback="Data") == "Data"


def test_cardpet_engines_are_bit_identical():
    """The load-bearing invariant: two engines fed the same clamped cards and
    the same seed replay the same bout — initiative coin flips included (the
    all-equal cards below tie every checkFirst, forcing the rng draw)."""
    hc, gc = _card(name="H"), _card(name="G", num=101)
    for seed in (1, 7, 42, 1234):
        e1 = Battle(CardPet(dict(hc)), enemy=dict(gc), source="pvp",
                    rng=random.Random(seed), final_attrs=True)
        e2 = Battle(CardPet(dict(hc)), enemy=dict(gc), source="pvp",
                    rng=random.Random(seed), final_attrs=True)
        while not e1.over:
            for e in (e1, e2):
                e._forced_enemy_attr = "Data"
                e.play_round("Vaccine")
            assert (e1.pet_hp, e1.enemy_hp, e1.last_player_damage,
                    e1.last_enemy_damage, e1.last_player_first) == \
                   (e2.pet_hp, e2.enemy_hp, e2.last_player_damage,
                    e2.last_enemy_damage, e2.last_player_first)
        assert e1.won == e2.won and e2.over
    # across seeds the tied coin flip must actually swing both ways
    flips = set()
    for seed in range(20):
        e = Battle(CardPet(dict(hc)), enemy=dict(gc), source="pvp",
                   rng=random.Random(seed), final_attrs=True)
        e._forced_enemy_attr = "Data"
        e.play_round("Vaccine")
        flips.add(e.last_player_first)
    assert flips == {True, False}


def test_cardpet_records_nothing():
    shim = CardPet(_card())
    assert shim.record_battle(True, {}) == ""
    assert shim.refuse_attack(1, 1) is False


# ---- the two-panel bout --------------------------------------------------------

class _Wire:
    """Client stub with a QUEUE: relays buffer until pump() delivers them to the
    peer panel (the real lobby drains an inbox the same way)."""
    def __init__(self, my_id):
        self.id = my_id
        self.peer = None
        self.state = LobbyState()
        self.queue = []
        self.log = []                         # every payload that crossed
        self.reports = []
    def relay(self, to, payload):
        self.log.append(payload)
        self.queue.append(payload)
    def pump(self):
        q, self.queue = self.queue, []
        for p in q:
            self.peer._on_relay({"from_id": self.id, "payload": p})
    def ladder_report(self, won, opp):
        self.reports.append((won, opp))
    def respond(self, *a, **k):
        pass
    def update_pet(self, *a, **k):
        pass


def _panel(pet, wire):
    return lobbyscreen.LobbyPanel(pet, lambda name, pw, card: wire,
                                  name=pet.name or "x", pw="x")


def _bout():
    """Two live panels, cards crossed, ready in 'choose'."""
    a = Pet(num=100, stage="Champion", vaccine=9, data_power=5, virus=5,
            attribute="Vaccine", obedience=500)
    a.full_health = 12
    a.name, a.world_seconds = "alpha", 600.0
    b = Pet(num=101, stage="Champion", vaccine=5, data_power=5, virus=5,
            attribute="Data", obedience=500)
    b.full_health = 10
    b.name, b.world_seconds = "beta", 600.0
    wa, wb = _Wire(1), _Wire(2)
    pa, pb = _panel(a, wa), _panel(b, wb)
    wa.peer, wb.peer = pb, pa
    pa._enter_session(2, "beta", "battle", host=True)
    pb._enter_session(1, "alpha", "battle", host=False)
    wa.pump()
    wb.pump()
    assert pa.bt_p2p and pb.bt_p2p
    assert pa.bphase == pb.bphase == "choose"
    return pa, pb, wa, wb


def _press(pan, k):
    if pan.bshow is not None:                 # skip the volley replay
        pan._key_battle("space")
    pan._key_battle(k)


def test_p2p_bout_agrees_end_to_end():
    pa, pb, wa, wb = _bout()
    for _ in range(30):
        if pa.bphase == "over" or pb.bphase == "over":
            break
        _press(pa, "1")                       # alpha rides its 9-Vaccine edge
        _press(pb, "2")
        wa.pump()
        wb.pump()
        # each round both panels computed the SAME bout from opposite seats
        assert pa.my_hp == pb.opp_hp and pa.opp_hp == pb.my_hp
    assert pa.bphase == pb.bphase == "over"
    assert pa.bt_outcome == "★ YOU WIN! ★" and pb.bt_outcome == "YOU LOSE…"
    # both sides recorded their REAL pet from their own verdict
    assert pa.pet.wins == 1 and pb.pet.wins == 0
    assert pa.bt_reward and "Victory" in pa.bt_reward
    assert pb.bt_reward is not None           # the loser gets its line too
    # both filed INDEPENDENT ladder reports that agree
    assert wa.reports == [(True, "beta")] and wb.reports == [(False, "alpha")]
    # and the wire never carried a result — only cards and picks
    kinds = {m.get("t") for m in wa.log + wb.log}
    assert kinds == {"card", "pick"}


def test_p2p_free_style_fights_its_own_way_at_pick_time():
    pa, pb, wa, wb = _bout()
    pa.pet.free_style = True
    pa.bt_my_card["free"] = True              # as the card would have baked it
    _press(pa, "3")                           # the tamer says Virus...
    assert pa.bt_my_choice == "Vaccine"       # ...the pet fights its own way


def test_p2p_refused_order_resolves_at_pick_time(monkeypatch):
    pa, pb, wa, wb = _bout()
    monkeypatch.setattr(Pet, "refuse_attack", lambda self, a, b: True)
    _press(pa, "3")
    assert pa.bt_my_choice == "Vaccine"       # own way, not the ordered Virus
    assert "Refused" in pa.bt_log


def test_commit_reveal_mismatch_voids_the_bout():
    """A peer that reveals a nonce it never committed to (seed grinding) gets
    a VOID, not a bout."""
    pa, pb, wa, wb = _bout()
    _press(pa, "1")
    # tamper beta's pick in flight: swap the revealed nonce
    _press(pb, "2")
    for m in wb.queue:
        if m.get("t") == "pick":
            m["nonce"] = 12345
    wa.pump()
    wb.pump()
    assert pa.bphase == "over" and "checksum" in pa.bt_outcome
    assert pa.pet.wins == 0 and wa.reports == []    # nothing recorded, nothing filed


def test_legacy_peer_gets_the_host_authoritative_bout():
    """A card without proto (an old client) must fall back verbatim: the host
    builds its engine at begin and honours 'choice' relays."""
    w = _Wire(1)
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    pan = _panel(p, w)
    pan.phase, pan.partner, pan.is_host = "battle", (9, "kai"), True
    pan.bt_my_card = lobbyscreen._clamp_card(battle_card(p))
    pan.bphase = "card"
    old = {"num": 4, "name": "X", "stage": "Champion", "hp": 15,
           "vaccine": 5, "data_power": 5, "virus": 5}
    pan._on_relay({"from_id": 9, "payload": {"kind": "battle", "t": "card", "card": old}})
    assert not pan.bt_p2p
    assert pan.battle is not None             # legacy host: engine built up front
    pan.bt_my_choice = "Vaccine"
    pan.bphase = "wait"
    pan._on_relay({"from_id": 9, "payload": {"kind": "battle", "t": "choice", "attr": "Data"}})
    assert pan.battle.round == 1              # the old wire still resolves rounds


def test_p2p_peer_cannot_smuggle_legacy_results():
    """A proto-2 peer that ALSO sends a forged 'result' must be ignored — the
    legacy branches are p2p-fenced."""
    pa, pb, wa, wb = _bout()
    pb._on_relay({"from_id": 1, "payload": {"kind": "battle", "t": "result",
                                            "host_dealt": 99, "guest_dealt": 0,
                                            "hhp": 99, "ghp": 0, "over": True,
                                            "host_alive": True, "guest_alive": False}})
    assert pb.bphase == "choose" and pb.bt_outcome == ""


def test_clamp_card_is_shared_and_bounded():
    c = lobbyscreen._clamp_card({"vaccine": 10**9, "hp": 999999, "free": True, "proto": 2})
    assert c["vaccine"] == lobbyscreen.MAX_PVP_POWER
    assert c["hp"] == lobbyscreen.MAX_PVP_HP
    assert c["free"] is True and c["proto"] == 2      # non-numeric keys survive
