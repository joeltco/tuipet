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


def test_invite_defers_while_typing():
    """Lobby audit 2026-07-07: an invite that pops mid-sentence EATS the next
    keystroke — typing "yeah" accepted a jogress on the y.  While the input
    line holds text (or a PM compose is open) the invite waits in the inbox;
    it prompts the moment the line clears."""
    pan = _lobby()
    responses = []
    pan.client.respond = lambda to, kind, acc, busy=False: responses.append((to, acc, busy))
    pan.buf = "ye"                                # mid-sentence
    pan.state.inbox.append({"t": "invite", "from_id": 2, "from_name": "Ryo",
                            "kind": "battle"})
    pan.anim()
    assert pan.invite_prompt is None              # NOT popped
    assert pan.state.inbox, "the invite must wait, not vanish"
    assert not responses, "waiting is not declining"
    assert "finish typing" in pan.status
    pan.key("y")                                  # the y lands in the SENTENCE
    assert pan.buf == "yey" and pan.invite_prompt is None
    pan.buf = ""                                  # line cleared (sent/erased)
    pan.anim()
    assert pan.invite_prompt is not None          # now it prompts
    assert not pan.state.inbox
    # same hold while a PM compose is open
    pan.invite_prompt = None
    pan.pm_to = (2, "Ryo")
    pan.state.inbox.append({"t": "invite", "from_id": 2, "from_name": "Ryo",
                            "kind": "battle"})
    pan.anim()
    assert pan.invite_prompt is None and pan.state.inbox
    pan.pm_to = None
    pan.anim()
    assert pan.invite_prompt is not None


def test_prompt_lines_keep_their_hints_with_long_names():
    """The key hints are FIXED CHROME (v0.2.349 doctrine): a 24-char name used
    to push [Y]/[N] / [Esc] clean off the 38-col prompt line.  The name field
    marquees instead — the hints render on EVERY frame, and the full name
    appears across the rolled loop."""
    long = "W" * 24
    pan = _lobby()
    pan.state.roster.append({"id": 3, "name": long,
                             "pet": {"name": "AncientGreymon", "stage": "Mega"}})
    pan.invite_prompt = {"from_id": 3, "from_name": long, "kind": "jogress"}
    rolled = ""
    for i in range(120):
        pan._mq = i
        last = pan.text().plain.split("\n")[-1]
        assert "[Y]/[N]" in last, f"frame {i} lost the hint: {last!r}"
        assert len(last) <= LCD_COLS
        rolled += last.split(" invites")[0]
    assert long in rolled                         # the whole name scrolls past
    pan.invite_prompt = None
    pan.action_for = (3, long, True)
    for i in range(120):
        pan._mq = i
        last = pan.text().plain.split("\n")[-1]
        assert "[Esc]" in last and "[B]attle" in last and "[M]sg" in last
        assert len(last) <= LCD_COLS
    pan.action_for = (3, long, False)             # the ghost variant
    last = pan.text().plain.split("\n")[-1]
    assert "[M]essage" in last and "[Esc]" in last
    pan.action_for = None                         # the selection status line
    pan.sel = 1                                   # sorted: the long-name live row
    pan.status = "Up/Down pick · Enter chat/act · Esc leave"
    others = pan._others()
    target = next(i for i, p in enumerate(others) if p["name"] == long)
    pan.sel = target
    for i in range(120):
        pan._mq = i
        last = pan.text().plain.split("\n")[-1]
        assert last.endswith("Enter to act"), last
        assert len(last) <= LCD_COLS


def test_join_leave_log_caps_at_the_shared_chat_cap():
    """The join/leave diff trims with net.CHAT_CAP — a hardcoded 200 drifted
    beside it (lobby audit 2026-07-07)."""
    from tuipet.net import CHAT_CAP
    pan = _lobby()
    pan._seen_ids = {1: "JoeltCo"}                # Ryo reads as a fresh join
    pan.state.chat = [("x", str(i)) for i in range(CHAT_CAP + 100)]
    pan.anim()
    assert len(pan.state.chat) == CHAT_CAP
