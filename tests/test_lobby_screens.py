"""Lobby screens audit (2026-07-04): every phase fits the physical LCD, and
the sessions play the REAL scenes -- PvP rounds replay the alternating-view
battle volley from the relayed result, the lobby fusion plays the offline
jogress converge/flash/reveal.  All wire-free: state + relays are stubbed."""
import random

from tuipet.pet import Pet
from tuipet.lobbyscreen import LobbyPanel, AccountPanel
from tuipet.net import LobbyState

LCD_ROWS, LCD_COLS = 12, 40


class _FakeClient:
    def __init__(self): self.sent = []
    def chat(self, t): pass
    def invite(self, *a): pass
    def respond(self, *a, **k): pass
    def relay(self, pid, payload): self.sent.append((pid, payload))
    def update_pet(self, c): pass


def _fits(panel, tag):
    lines = panel.text().plain.split("\n")
    assert len(lines) <= LCD_ROWS, f"{tag}: {len(lines)} lines"
    w = max(len(l) for l in lines)
    assert w <= LCD_COLS, f"{tag}: {w} cols"


def _lobby():
    random.seed(2)
    p = Pet(num=102, name="Devimon", stage="Champion", attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    pan = LobbyPanel(p, on_connect=lambda n, pw, c: None)
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "JoeltCo"
    s.roster = [{"id": 1, "name": "JoeltCo", "pet": {}},
                {"id": 2, "name": "Ryo", "pet": {"name": "WarGreymon", "stage": "Mega"}}]
    pan.client, pan.state, pan.phase = _FakeClient(), s, "lobby"
    pan.status = "Up/Down pick · Enter chat/act · Esc leave"
    return pan


def test_every_text_phase_fits_the_lcd():
    pan = _lobby()
    _fits(pan, "lobby")
    pan.buf = "x" * 80
    _fits(pan, "lobby long input")
    login = AccountPanel(name="a-very-long-tamer-name-indeed-oh-yes")
    login.pw_buf = "p" * 60
    _fits(type("W", (), {"text": staticmethod(login.text)})(), "login")
    pan.partner = (2, "Ryo")
    pan.phase, pan.jphase = "jogress", "waiting"
    _fits(pan, "jogress waiting")
    pan.phase, pan.bphase = "battle", "card"
    _fits(pan, "battle card")
    pan.opp_card = {"name": "WarGreymon", "stage": "Mega", "num": 964, "hp": 25,
                    "vaccine": 50, "data_power": 40, "virus": 30, "bits": (1, 5)}
    pan.my_hp = pan.my_max = 15
    pan.opp_hp = pan.opp_max = 25
    pan.bphase, pan.bt_log = "choose", "Pummel → 5 dmg\n  Terra Force ← 6 dmg"
    _fits(pan, "battle choose")
    pan.bphase = "over"
    pan.bt_outcome = "★ YOU WIN! ★"
    _fits(pan, "battle over")


def test_pvp_round_replays_the_real_volley():
    pan = _lobby()
    pan.partner = (2, "Ryo")
    pan.phase, pan.bphase, pan.is_host = "battle", "choose", False
    pan.opp_card = {"name": "WarGreymon", "stage": "Mega", "num": 964, "hp": 25,
                    "vaccine": 50, "data_power": 40, "virus": 30, "bits": (1, 5)}
    pan.my_hp = pan.my_max = 15
    pan.opp_hp = pan.opp_max = 25
    res = {"kind": "battle", "t": "result", "host_dealt": 6, "guest_dealt": 5,
           "hattr": "Vaccine", "gattr": "Virus", "hhp": 20, "ghp": 10,
           "host_first": True, "over": False, "host_alive": True, "guest_alive": True}
    pan._apply_result(res, as_host=False)
    assert pan.bshow is not None                  # the volley stages
    assert pan.strip() == "[dim]SPACE skip[/]"
    markers = {e["m"] for e in pan.bshow.timeline}
    assert {"faceoff", "windup", "fire_out", "fire_in", "hit"} <= markers
    seen = set()
    for _ in range(len(pan.bshow.timeline) + 5):  # plays through, all in budget
        if pan.bshow is None:
            break
        _fits(pan, "volley frame")
        pan.anim()
    assert pan.bshow is None                      # ...then the choose screen returns
    assert pan.my_hp == 10 and pan.opp_hp == 20   # guest mapping applied
    _fits(pan, "post-volley")


def test_lobby_fusion_plays_the_real_scene():
    from tuipet import jogress as jmod
    pan = _lobby()
    pan.partner = (2, "Ryo")
    pan.phase, pan.jphase = "jogress", "waiting"
    pan.pet.dp = 4
    pan.pet.compliance = True
    # a stubbed resonance so the scene stages regardless of the data roll
    real_can, real_resolve = jmod.can_jogress, jmod.resolve
    jmod.can_jogress = lambda p: None
    jmod.resolve = lambda p, a: {"num": 4, "name": "Agumon", "partners": ["Vaccine"]}
    try:
        pan._on_relay({"from_id": 2, "payload": {"kind": "jogress", "attr": "Vaccine",
                                                 "num": 7, "name": "Gabumon"}})
    finally:
        jmod.can_jogress, jmod.resolve = real_can, real_resolve
    assert pan.jphase == "result" and pan.jshow is not None
    for _ in range(30):                           # converge -> flash -> fused bounce
        _fits(pan, "fusion frame")
        pan.anim()
    assert pan.jshow.phase == "fused"
    assert "ENTER fuse" in pan.strip()        # menu-bounds rewording 2026-07-07
