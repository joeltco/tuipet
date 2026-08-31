"""THE LOBBY AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown lobby audit next."

F1 lives in `tools/pvp_smoke.py`, not here: the ONE check that covers the
live path end to end asserted the PRE-L17 rule (`battles == 2`) and so had
been failing by construction since 2026-07-20 — on a tool whose own
docstring says to run it after any lobby/net/server change.  A safety net
that always fails is not a net.  Its contract now matches L17, and this
file pins the two properties the tool checks so the code and the tool can
never drift apart again silently.

The rest of the lobby held under probing, and the probes are pinned here:
the doors a stranger can knock on, the bout's accounting under network
races, and every page against the box.
"""
import pytest

from tuipet import grid, lobbyscreen
from tuipet.net import LobbyState
from tuipet.pet import Pet

R, C = grid.ROWS, grid.COLS


class _Stub:
    def __init__(self, state):
        self.state = state
        self.me_id = 1
        self.sent = []
        self.reports = []
        self.ladder = self.raid = None
        self.ladder_reward = self.last_hit = self.raid_reward = None

    def respond(self, pid, kind, ok, busy=False):
        self.sent.append(("respond", pid, kind, ok, busy))

    def relay(self, pid, payload):
        self.sent.append(("relay", pid, payload))

    def ladder_report(self, won, opp):
        self.reports.append((won, opp))

    def __getattr__(self, n):
        return lambda *a, **k: None


def _state():
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "live": True},
                {"id": 2, "name": "mika", "live": True},
                {"id": 3, "name": "creep", "live": True}]
    return s


def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight() + 5
    p.bits = 1000
    return p


def _panel(**kw):
    st = _state()
    pan = lobbyscreen.LobbyPanel(_pet(), lambda n, pw, c: _Stub(st),
                                 name="joel", pw="x")
    pan.client = _Stub(st)
    pan.state = st
    pan.phase = "lobby"
    for k, v in kw.items():
        setattr(pan, k, v)
    return pan, st


# ---- the doors a stranger knocks on ------------------------------------

def test_an_accept_for_an_invite_I_never_sent_is_dropped():
    """C5: the relay stamps from_id, so the ledger is the forgery check --
    a crafted accept used to force this client into a session, INCLUDING a
    permanent jogress fusion."""
    pan, st = _panel()
    st.inbox.append({"t": "invite_resp", "from_id": 3, "from_name": "creep",
                     "kind": "jogress", "accept": True})
    pan.anim()
    assert pan.phase == "lobby" and pan.partner is None


def test_an_accept_for_an_invite_I_DID_send_opens_the_session():
    pan, st = _panel()
    pan._sent_invites.add((2, "battle"))
    st.inbox.append({"t": "invite_resp", "from_id": 2, "from_name": "mika",
                     "kind": "battle", "accept": True})
    pan.anim()
    assert pan.phase == "battle"


def test_a_drop_clears_the_ledger_so_stale_accepts_cannot_land():
    pan, st = _panel()
    pan._sent_invites.add((2, "battle"))
    st.reconnecting = True
    pan.anim()
    assert pan._sent_invites == set()
    st.reconnecting = False
    st.inbox.append({"t": "invite_resp", "from_id": 2, "from_name": "mika",
                     "kind": "battle", "accept": True})
    pan.anim()
    assert pan.phase == "lobby"


@pytest.mark.parametrize("kind", ["trade-your-save", "", "jogress "])
def test_an_unknown_invite_kind_is_auto_declined(kind):
    pan, st = _panel()
    st.inbox.append({"t": "invite", "from_id": 3, "from_name": "creep",
                     "kind": kind})
    pan.anim()
    assert pan.invite_prompt is None
    assert ("respond", 3, kind, False, False) in pan.client.sent


def test_a_blocked_peers_invite_never_reaches_the_prompt():
    pan, st = _panel()
    st.blocked = {"creep"}
    st.inbox.append({"t": "invite", "from_id": 3, "from_name": "creep",
                     "kind": "battle"})
    pan.anim()
    assert pan.invite_prompt is None
    assert any(s[0] == "respond" and s[3] is False for s in pan.client.sent)


def test_an_invite_mid_sentence_waits_instead_of_eating_the_keystroke():
    """Typing "yeah" used to ACCEPT a jogress on the y."""
    pan, st = _panel(buf="yeah lets go")
    st.inbox.append({"t": "invite", "from_id": 2, "from_name": "mika",
                     "kind": "battle"})
    pan.anim()
    assert pan.invite_prompt is None and len(st.inbox) == 1   # HELD
    assert "finish typing" in pan.status
    pan.buf = ""
    pan.anim()
    assert pan.invite_prompt is not None and not st.inbox     # then it prompts


def test_blocking_sweeps_the_log_it_promises_to_silence():
    pan, st = _panel()
    st.chat = [("creep", "spam spam spam"), ("mika", "hello")]
    pan.action_for = (3, "creep", {"num": 120, "name": "Kuwagamon",
                                   "stage": "Champion", "attribute": "Virus"})
    pan.key("x")
    txt = pan.text().plain
    assert "spam spam spam" not in txt and "hello" in txt
    assert "creep" in st.blocked          # ...and net.py drops what comes next


# ---- the bout's accounting, under network races ------------------------

def _bout(bphase="fight"):
    from tuipet import battle as B
    pan, _st = _panel(phase="battle", bphase=bphase, partner=(2, "mika"),
                      is_host=True,
                      opp_card={"num": 120, "name": "Kuwagamon",
                                "stage": "Champion", "attribute": "Virus",
                                "hit_type": "normal"})
    if bphase == "fight":
        pan.battle = B.Battle(pan.pet, dict(pan.opp_card))
    return pan


def _ledger(p):
    return dict(battles=p.battles, wins=p.wins, bits=p.bits, energy=p.energy)


def test_a_forfeit_files_exactly_one_loss_and_a_late_abort_adds_nothing():
    """The race that matters: I walk out, their abort crosses my forfeit on
    the wire and lands after it."""
    pan = _bout()
    before = _ledger(pan.pet)
    pan._forfeit()
    mid = _ledger(pan.pet)
    assert pan.client.reports == [(False, "mika")]
    assert mid["energy"] < before["energy"]          # the body was billed
    pan._on_relay({"t": "relay", "from_id": 2, "from_name": "mika",
                   "payload": {"kind": "battle", "abort": True}})
    assert _ledger(pan.pet) == mid                   # nothing doubled
    assert pan.client.reports == [(False, "mika")]


def test_an_opponents_flight_pays_once_even_if_the_abort_repeats():
    pan = _bout()
    pan._opp_fled()
    mid = _ledger(pan.pet)
    assert pan.client.reports == [(True, "mika")]
    assert mid["bits"] > 1000                        # the purse landed
    pan._on_relay({"t": "relay", "from_id": 2, "from_name": "mika",
                   "payload": {"kind": "battle", "abort": True}})
    assert _ledger(pan.pet) == mid
    assert pan.client.reports == [(True, "mika")]


def test_a_pre_bell_walk_out_costs_nothing():
    pan = _bout(bphase="card")
    before = _ledger(pan.pet)
    pan._forfeit()
    assert pan.client.reports == [] and _ledger(pan.pet) == before


def test_an_online_bout_is_progression_neutral_the_live_smoke_asserts_this():
    """THE L17 CONTRACT, pinned on both sides of the fence: here, and in
    tools/pvp_smoke.py, whose stale copy of this rule is F1 of the audit."""
    p = _pet()
    before = _ledger(p)
    p.record_battle(True, {"num": 120, "stage": "Mega", "attribute": "Virus"},
                    online=True)
    after = _ledger(p)
    assert after["battles"] == before["battles"]
    assert after["wins"] == before["wins"]
    assert after["energy"] < before["energy"]        # the BODY still pays
    assert p.mega_kills == 0                         # and no KO6 farming


# ---- every page inside the box -----------------------------------------

LOBBY_PAGES = {
    "lobby": {},
    "action menu": {"action_for": (2, "mika", {"num": 120, "name": "Kuwa",
                                               "stage": "Champion",
                                               "attribute": "Virus"})},
    "pm compose": {"pm_to": (2, "mika")},
    "invite prompt": {"invite_prompt": {"id": 2, "name": "mika",
                                        "kind": "battle"}},
    "dm": {"phase": "dm", "dm_peer": (2, "mika")},
}


@pytest.mark.parametrize("page", sorted(LOBBY_PAGES))
def test_every_lobby_page_fits_the_LCD(page):
    pan, st = _panel(**LOBBY_PAGES[page])
    st.chat = [(f"tamer{i % 4 + 2}",
                "a fairly long line of lobby chatter number %d" % i)
               for i in range(30)]
    st.dms = {"mika": [("mika", "hey there, good fight"),
                       ("joel", "gg! rematch later?")]}
    st.roster += [{"id": i, "name": f"tamer{i}", "live": True}
                  for i in range(4, 14)]
    plain = pan.text().plain.rstrip("\n")
    rows = plain.split("\n")
    assert len(rows) <= R, f"{page}: {len(rows)} rows into {R} — clipped"
    assert max(len(r) for r in rows) <= C, f"{page}: wider than {C}"
