"""Lobby screens audit (2026-07-04): every phase fits the physical LCD, and
the sessions play the REAL scenes -- PvP rounds replay the alternating-view
battle volley from the relayed result, the lobby fusion plays the offline
jogress converge/flash/reveal.  All wire-free: state + relays are stubbed."""
import random

from tuipet.pet import Pet
from tuipet import lobbyscreen
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
    pan.status = "↑↓ pick · ENTER chat · TAB ranks · ESC"
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


def test_chat_styles_tell_the_speakers_apart():
    """Chat polish 2026-07-07: my lines dim, PMs and mentions bright,
    notices dim, plain chat ink; a wrapped message hangs an indent."""
    from tuipet.theme import INK, INK_B, DIM
    pan = _lobby()
    pan.state.chat = [("JoeltCo", "hello all"),          # mine
                      ("Ryo", "yo JoeltCo nice pet"),    # mentions me
                      ("Ryo", "regular line"),           # plain
                      ("✉Ryo", "psst"),                  # PM in
                      ("✉→Ryo", "back at you"),          # PM out (mine)
                      ("", "mp joined")]                 # notice
    rows = pan._chat_rows()
    assert [r[1] for r in rows] == [DIM, INK_B, INK, INK_B, DIM, DIM]
    pan.state.chat = [("Ryo", "a very long message that has to wrap onto more lines here")]
    rows = pan._chat_rows()
    assert len(rows) > 1 and rows[1][0].startswith(" ")
    assert rows[0][1] == rows[1][1]                      # one message, one style


def test_chat_scrollback_pages_the_log():
    pan = _lobby()
    pan.state.chat = [("Ryo", f"msg{i}") for i in range(30)]
    assert "msg29" in pan.text().plain and "msg5" not in pan.text().plain
    pan.key("pageup")
    txt = pan.text().plain
    assert "▲" in txt and "msg29" not in txt             # older view + marker
    assert "back to live" in txt                         # the way home shows
    assert pan.key("escape") is None and pan.scroll == 0  # snap, NOT close
    assert "msg29" in pan.text().plain
    pan.key("pageup")
    pan.buf = "hi"
    pan.key("enter")                                     # speaking snaps live
    assert pan.scroll == 0
    _fits(pan, "lobby scrolled")


def test_chat_empty_state_and_caret_blink():
    pan = _lobby()
    pan.state.chat = []
    pan._mq = 0
    txt = pan.text().plain
    assert "say hi" in txt
    inp = [l for l in txt.split("\n") if l.startswith("say:")][0]
    assert "_" in inp
    pan._mq = 5                                          # the caret's off-beat
    inp = [l for l in pan.text().plain.split("\n") if l.startswith("say:")][0]
    assert "_" not in inp


def test_pvp_round_replays_the_real_volley():
    pan = _lobby()
    pan.partner = (2, "Ryo")
    pan.phase, pan.bphase, pan.is_host = "battle", "fight", True
    pan.opp_card = lobbyscreen._clamp_card({"name": "Wargle", "stage": "Adult",
                                            "num": 400})
    pan.my_hp = pan.my_max = 5
    pan.opp_hp = pan.opp_max = 5
    pan._stage_volley(5, 5, 2, 1)
    assert pan.bshow is not None                  # the volley stages
    markers = {e["m"] for e in pan.bshow.timeline}
    assert {"faceoff", "windup", "fire_out", "fire_in", "hit"} <= markers
    for _ in range(len(pan.bshow.timeline) + 5):  # plays through, all in budget
        if pan.bshow is None:
            break
        _fits(pan, "volley frame")
        pan.anim()
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
    pan.action_for = (3, long, True)              # long name -> the WHOLE line marquees
    rolled = ""
    for i in range(400):        # the line grew "[M] PM" (round 30): a longer
        pan._mq = i             # loop needs more frames to roll clear through
        last = pan.text().plain.split("\n")[-1]
        assert len(last) <= LCD_COLS              # never overruns the box
        rolled += last
    assert "[B]attle" in rolled and "[V] DM" in rolled \
        and "[M] PM" in rolled and "[ESC]" in rolled   # hints roll past
    pan.action_for = (3, long, False)             # the ghost variant
    rolled = ""
    for i in range(400):
        pan._mq = i
        last = pan.text().plain.split("\n")[-1]
        assert len(last) <= LCD_COLS
        rolled += last
    assert "[P]ing" in rolled and "[V] DM" in rolled \
        and "[M] PM" in rolled and "[ESC]" in rolled
    pan.action_for = None                         # the selection status line
    pan.sel = 1                                   # sorted: the long-name live row
    pan.status = "↑↓ pick · ENTER chat · TAB ranks · ESC"
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
    pan._seen_ids = {"JoeltCo"}                   # a NAME set since the ghost-churn
    #                                               fix (2026-07-17): Ryo = fresh join
    pan.state.chat = [("x", str(i)) for i in range(CHAT_CAP + 100)]
    pan.anim()
    assert len(pan.state.chat) == CHAT_CAP


def test_default_status_hint_renders_whole():
    """The connect-time hint itself must fit the 38-col line — the old
    41-char "Up/Down pick · …" clipped its own "Esc leave" to "Esc le"
    (Joel's live screen, 2026-07-07)."""
    pan = _lobby()
    pan.state.roster = [{"id": 1, "name": "JoeltCo", "pet": {}}]   # alone: raw status shows
    pan.status = "Connecting…"
    pan.anim()                                    # the connected transition sets it
    assert len(pan.status) <= 38
    last = pan.text().plain.split("\n")[-1]
    assert last.endswith("TAB ranks · ESC"), last


def test_malformed_relay_payloads_never_crash_the_battle():
    """The relay ships session payloads VERBATIM from the peer, so their shape
    is peer-controlled (audit 2026-07-13): a card missing the stat keys used
    to KeyError inside Battle, and a schema-drifted result crashed the guest
    mid-battle.  A malformed card is SANITIZED with defaults (an honest peer
    on a drifted schema still gets its bout, a hostile one a 0-stat foe); a
    sparse result applies with defaults."""
    pan = _lobby()
    pan.partner = (2, "Ryo")
    pan.phase, pan.bphase, pan.is_host = "battle", "card", True
    import hashlib as _h
    pan.bt_my_card = lobbyscreen._clamp_card({"num": 4})
    pan.bt_nonce = 7
    commit = _h.sha256(str(11).encode()).hexdigest()
    pan._battle_begin({"num": 5, "hp": "lol", "proto": 3}, commit=commit)
    assert pan.bphase == "wait", "a sanitized card still arms the bout"
    assert pan.opp_card["strength"] == 4 and pan.opp_card["hp"] == 5
    pan._on_relay = pan._on_relay                 # (unchanged surface)
    pan.partner = (2, "Ryo")
    pan.bt_peer_nonce = 11
    pan._maybe_build()                            # engine builds without KeyError
    assert pan.battle is not None


def test_unknown_invite_kinds_are_declined_not_entered():
    """An invite whose kind is neither jogress nor battle used to reach
    _enter_session, set a dangling partner and enter NO branch -- half-trusted
    relays from that peer for the rest of the session (audit 2026-07-13)."""
    pan = _lobby()
    declined = []
    pan.client.respond = lambda pid, kind, ok, **kw: declined.append((pid, kind, ok))
    pan.state.inbox.append(
        {"t": "invite", "kind": "trade", "from_id": 9, "from_name": "Mallory"})
    pan.anim()                                    # the tick drains the inbox
    assert pan.invite_prompt is None, "an unknown kind must never prompt"
    assert pan.partner is None
    assert declined and declined[-1][:2] == (9, "trade") and declined[-1][2] is False


def _tick_app(pan):
    """A TuiPetApp shell that can run on_tick with `pan` as the open mode."""
    from tuipet.app import TuiPetApp
    app = TuiPetApp.__new__(TuiPetApp)
    app.pet = pan.pet
    app.mode = pan
    app._mode_close = None
    app._needs = False
    app._nag_t = 0.0
    app._dying_fx = False           # __init__ sets it; the death check reads it
    app.beeps = []
    app.beep = lambda name=None, bell=True: app.beeps.append(name)
    app.flash = lambda *a, **k: None
    return app


def test_lobby_chat_ticks_the_life_sim_but_sessions_freeze():
    """Joel 2026-07-13: "make the lobby tick, alarm and all" -- chat is not a
    pause button.  on_tick runs the sim through the lobby/dm phases (with
    evolution HELD for the main view), keeps the canon freeze during
    battle/jogress sessions and login, and rings the care alarm on onset."""
    pan = _lobby()
    app = _tick_app(pan)
    t0 = pan.pet.age_seconds
    app.on_tick()
    assert pan.pet.age_seconds == t0 + 1.0, "the lobby must tick the sim"
    assert pan.pet.fx_hold, "evolution waits for the main view"

    pan.phase = "dm"
    app.on_tick()
    assert pan.pet.age_seconds == t0 + 2.0, "the DM thread ticks too"

    for frozen in ("battle", "jogress", "login"):
        pan.phase = frozen
        app.on_tick()
        assert pan.pet.age_seconds == t0 + 2.0, f"{frozen} keeps the canon freeze"

    pan.phase = "lobby"                          # the alarm rings on onset
    pan.pet.hunger = 0
    pan.pet.stage = "Rookie"
    app.on_tick()
    assert "alarm" in app.beeps


def test_death_in_the_lobby_returns_home_for_the_memorial(monkeypatch):
    """Death can't wait for ESC: the tick that kills the pet closes the lobby
    (tearing down the connection via the normal close path) and starts the
    dying fx on the home screen."""
    from tuipet.pet import Pet
    pan = _lobby()
    app = _tick_app(pan)
    closed = []
    app._mode_close = closed.append

    class _Scr:
        fx = None
        def start_fx(self, *a, **k): self.fx = a
    app.screen_w = _Scr()

    def die(self, dt):
        self.dead = True
    monkeypatch.setattr(Pet, "tick", die)
    app.on_tick()
    assert app.mode is None, "the lobby closes so the memorial owns the screen"
    assert closed == [None], "the normal close callback tears down the client"
    assert app.screen_w.fx and app.screen_w.fx[0] == "dying"
    assert "death" in app.beeps


def test_lobby_strip_carries_the_care_alarm():
    """The alarm's on-screen half rides the strip in the ticking phases --
    without it the pet starves silently behind the chat window.  It outranks
    the unread nudge, stays inside the 40-col budget, and clears with the need."""
    import re
    pan = _lobby()
    pan.pet.stage = "Rookie"
    pan.pet.hunger = 0
    pan.state.unread.add("Ryo")                  # the alarm outranks the mail
    cue = pan.strip()
    assert "⚠" in cue and "hungry" in cue
    assert len(re.sub(r"\[/?[^\[\]]*\]", "", cue)) <= 40
    pan.phase = "dm"
    assert "⚠" in pan.strip(), "the DM thread shows the cue too"
    pan.phase = "lobby"
    pan.pet.hunger = 4
    pan.pet.scold_flag = False
    pan.pet.discipline_call = False
    assert "⚠" not in pan.strip(), "the cue clears with the need"


def test_a_hostile_peer_card_is_clamped_to_legal_ranges():
    """Multiplayer audit 2026-07-13: the relay is peer-to-peer, so the
    opponent card is UNTRUSTED input.  Nothing bounded it -- a hacked client
    could ship hp=999999 and field an unkillable mon (the bout never ended).
    Every number is now clamped to what the game can actually produce."""
    c = lobbyscreen._clamp_card({"num": 964, "name": "Cheater", "stage": "Adult",
                                 "strength": 999, "strength_max": 999,
                                 "energy": 10 ** 9, "energy_max": 10 ** 9,
                                 "battles": -5, "wins": 10 ** 9,
                                 "hit_type": "nuclear", "hp": 999999})
    assert c["hp"] == 5, "everyone fights from 5 in the HP race"
    assert c["strength"] <= c["strength_max"] <= 9
    assert c["energy"] <= c["energy_max"] <= 2000
    assert c["battles"] == 0 and c["wins"] == 0
    assert c["hit_type"] == "miss", "an unknown hit-type reads as miss"


# ---- round 35 pins (account panel tidy, 2026-07-19) -------------------------

def test_the_name_field_obeys_the_cell_width_law():
    """An emoji is TWO cells: the old character slice let a wide name run
    the input line past the 40-col box.  Tail-window by cells now."""
    from rich.cells import cell_len
    pan = AccountPanel()
    for ch in "🔥" * 12:                            # 12 chars, 24 cells
        pan.key(ch)
    body = pan.text().plain
    for line in body.split("\n"):
        assert cell_len(line) <= 40, f"{cell_len(line)} cells: {line!r}"


def test_the_name_caps_live_at_the_servers_24():
    """What you SEE is what logs in -- the buffer used to hold 64 and the
    confirm silently trimmed to MAX_NAME."""
    pan = AccountPanel()
    for ch in "x" * 40:
        pan.key(ch)
    assert len(pan.name_buf) == 24
    pan.key("tab")
    for ch in "p" * 80:                             # the password keeps 64
        pan.key(ch)
    assert len(pan.pw_buf) == 64


def test_a_half_filled_confirm_speaks_up():
    """ENTER with a missing field used to do NOTHING at all."""
    pan = AccountPanel(name="joel")                 # field starts on pw, empty
    assert pan.key("enter") is None
    assert "both" in pan.note and pan.sfx == "error"
    for ch in "pw":
        pan.key(ch)
    assert pan.key("enter") == ("done", ("joel", "pw"))


def test_the_dead_pvp_bounds_are_gone():
    """MAX_PVP_HP/MAX_PVP_POWER described a clamp design that no longer
    exists -- _clamp_card in lobbybout owns the real per-field bounds."""
    from tuipet import accountscreen
    assert not hasattr(accountscreen, "MAX_PVP_HP")
    assert not hasattr(accountscreen, "MAX_PVP_POWER")


class _LadderClient(_FakeClient):
    """A fake that also has the ladder half-report surface."""
    def __init__(self):
        super().__init__()
        self.reports = []
    def ladder_report(self, won, opp):
        self.reports.append((won, opp))


def _running_fight(pan):
    pan.partner = (2, "Ryo")
    pan.phase, pan.bphase, pan.is_host = "battle", "fight", True
    pan.battle = {"seq": [(True, 1, False, 0)], "host_hp": 5, "guest_hp": 5, "i": 0}
    pan.opp_card = lobbyscreen._clamp_card({"name": "Wargle", "stage": "Adult",
                                            "num": 400})
    pan.my_hp = pan.my_max = pan.opp_hp = pan.opp_max = 5


def test_esc_mid_fight_files_the_forfeit_loss():
    """MED audit 2026-07-19: ESC in "fight" relayed only the abort — a losing
    player voided the result at will while the winner's half expired
    unconfirmed.  A committed fight left early is a LOSS, filed and counted."""
    pan = _lobby()
    pan.client = _LadderClient()
    _running_fight(pan)
    losses0 = pan.pet.battles - pan.pet.wins
    pan.key("escape")
    assert pan.client.reports == [(False, "Ryo")], "the losing half files"
    assert (pan.pet.battles - pan.pet.wins) == losses0 + 1, "the loss counts"
    assert any(p.get("abort") for _, p in pan.client.sent), "partner still told"
    assert pan.phase == "lobby" and "loss" in pan.status


def test_esc_before_the_commit_stays_a_free_backout():
    pan = _lobby()
    pan.client = _LadderClient()
    pan.partner = (2, "Ryo")
    pan.phase, pan.bphase = "battle", "card"
    b0 = pan.pet.battles
    pan.key("escape")
    assert pan.client.reports == [], "no seeded engine — nothing to report"
    assert pan.pet.battles == b0
    assert pan.status == "You forfeited."


def test_abort_mid_fight_is_a_forfeit_win_not_a_void():
    """The stayer's side of the same hole: the winner's half files so the
    pair credits, and the win pays like any decided bout."""
    pan = _lobby()
    pan.client = _LadderClient()
    _running_fight(pan)
    bits0, wins0 = pan.pet.bits, pan.pet.wins
    pan._on_relay({"from_id": 2, "payload": {"kind": "battle", "abort": True}})
    assert pan.client.reports == [(True, "Ryo")], "the winning half files"
    assert pan.pet.wins == wins0 + 1 and pan.pet.bits > bits0
    assert pan.bphase == "over" and "you win" in pan.bt_outcome.lower()
    _fits(pan, "forfeit-win over screen")


def test_abort_before_the_commit_still_voids():
    pan = _lobby()
    pan.client = _LadderClient()
    pan.partner = (2, "Ryo")
    pan.phase, pan.bphase = "battle", "wait"
    pan.battle = None
    pan._on_relay({"from_id": 2, "payload": {"kind": "battle", "abort": True}})
    assert pan.client.reports == []
    assert pan.bphase == "over" and "void" in pan.bt_payload[1]


def test_partner_vanishing_mid_fight_is_the_same_forfeit():
    """Killing the app instead of pressing ESC took the same void exit."""
    pan = _lobby()
    pan.client = _LadderClient()
    _running_fight(pan)
    pan.state.roster = [p for p in pan.state.roster if p["id"] != 2]
    pan.anim()
    assert pan.client.reports == [(True, "Ryo")]
    assert pan.bphase == "over" and "you win" in pan.bt_outcome.lower()
