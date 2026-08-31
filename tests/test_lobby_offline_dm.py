"""A PM you can't open is a message that never arrived (Joel 2026-08-18:
"cant read unread messages when player is offline").

A roster row is the ONLY door into a DM thread -- you pick a name, press
ENTER, then V.  The roster was strictly the server's live list, so the
moment the sender logged off their thread became unreachable: the ✉ badge
kept saying "V on their name" for a name that wasn't on screen, and the
unread message sat in the save file until they happened to come back.

These pin the door open: offline thread-partners get a roster row of their
own, at the bottom, and the actions on that row tell the truth about them.
"""
from tuipet.lobbychat import OFFLINE_ID
from tuipet.lobbyscreen import LobbyPanel
from tuipet.net import LobbyState
from tuipet.pet import Pet


class _FakeClient:
    def __init__(self):
        self.pings, self.pms = [], []

    def ping(self, to):
        self.pings.append(to)

    def pm(self, to, text, to_name=None):
        self.pms.append((to, text, to_name))


def _lobby(roster=(), dms=None, unread=()):
    """A connected lobby: me plus whoever the server reports, and whatever
    threads the save file brought back."""
    pan = LobbyPanel(Pet(num=102, name="Devimon", stage="Champion"),
                     on_connect=lambda n, pw, c: None)
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "JoeltCo"
    s.roster = [{"id": 1, "name": "JoeltCo", "pet": {}}] + list(roster)
    s.dms = dict(dms or {})
    s.unread = set(unread)
    pan.client, pan.state, pan.phase = _FakeClient(), s, "lobby"
    return pan


def _row(pan, name):
    return next((p for p in pan._others() if p["name"] == name), None)


def test_an_offline_thread_partner_still_has_a_roster_row():
    """THE BUG. Ryo PMs you and logs off; the thread must stay reachable."""
    pan = _lobby(dms={"Ryo": [("Ryo", "gg")]}, unread=["Ryo"])
    assert _row(pan, "Ryo") is not None, (
        "Ryo left a message and left the lobby -- with no roster row there is "
        "no key that opens the thread, so the unread PM can never be read")


def test_that_row_opens_the_thread_and_clears_the_badge():
    """The door has to actually turn: ENTER on the row, then V."""
    pan = _lobby(dms={"Ryo": [("Ryo", "gg")]}, unread=["Ryo"])
    pan.sel = pan._others().index(_row(pan, "Ryo"))
    pan.key("enter")                       # open the action line for that name
    assert pan.action_for is not None
    pan.key("v")
    assert pan.phase == "dm"
    assert pan.dm_peer[1] == "Ryo"
    assert "Ryo" not in pan.state.unread   # reading it clears the ✉


def test_a_reply_goes_out_addressed_by_name():
    """The offline id can't route; `to_name` is what the server queues on.
    Sending with a bare sentinel id would earn a 'No such player.'"""
    pan = _lobby(dms={"Ryo": [("Ryo", "gg")]})
    pan.phase, pan.dm_peer, pan.buf = "dm", (OFFLINE_ID, "Ryo"), "gg2"
    pan.key("enter")
    assert pan.client.pms == [(OFFLINE_ID, "gg2", "Ryo")]
    assert "offline" in pan.status         # and it SAYS the reply waits for them


def test_the_offline_row_offers_no_ping():
    """Ping means "come to the lobby" -- there is no app there to hear it,
    and ping() addresses by id alone, which for this row is the sentinel."""
    pan = _lobby(dms={"Ryo": [("Ryo", "gg")]})
    pan.action_for = (OFFLINE_ID, "Ryo", False)
    pan.key("p")
    assert pan.client.pings == []
    assert "[P]ing" not in pan.text().plain
    assert "ping" not in pan.strip()


def test_a_ghost_keeps_its_ping():
    """The tier above -- app open, not in the room -- is unchanged."""
    pan = _lobby(roster=[{"id": 7, "name": "Mika", "pet": {}, "live": False}])
    pan.action_for = (7, "Mika", False)
    pan.key("p")
    assert pan.client.pings == [7]


def test_someone_online_is_listed_once_and_keeps_their_real_id():
    """A thread with someone who IS here must not grow a second, dead row."""
    pan = _lobby(roster=[{"id": 2, "name": "Ryo", "pet": {}}],
                 dms={"Ryo": [("Ryo", "gg")]})
    rows = [p for p in pan._others() if p["name"] == "Ryo"]
    assert len(rows) == 1
    assert rows[0]["id"] == 2              # the live id, or invites break


def test_my_own_thread_never_lists_me():
    pan = _lobby(dms={"JoeltCo": [("JoeltCo", "note to self")]})
    assert _row(pan, "JoeltCo") is None


def test_the_offline_tail_sorts_below_everyone_present():
    """Who is actually here reads first; the address book follows."""
    pan = _lobby(roster=[{"id": 2, "name": "Zed", "pet": {}},
                         {"id": 3, "name": "Mika", "pet": {}, "live": False}],
                 dms={"Abe": [("Abe", "hi")]})
    assert [p["name"] for p in pan._others()] == ["Zed", "Mika", "Abe"]


def _card_of(pan):
    """The lobby's STATUS CARD -- the roster and the pick line moved here
    on 2026-08-31."""
    from tuipet import statusbox
    from tuipet.app import TuiPetApp, Stats

    class _FakeStats(Stats):
        def __init__(self): self.txt = ""
        def update(self, t): self.txt = str(t)
        @property
        def border_subtitle(self): return ""
        @border_subtitle.setter
        def border_subtitle(self, v): pass

    app = TuiPetApp.__new__(TuiPetApp)
    app.pet, app.stats_w, app.sound, app.mode = pan.pet, _FakeStats(), False, pan
    statusbox.lobby(app)
    return app.stats_w.txt


def test_the_pick_line_says_offline_not_playing():
    """"X is playing" is the GHOST's line.  Said over an offline row it turns
    a roster of people who are nowhere into a roster that looks busy.  The
    line lives on the CARD now, but it still has to name the RIGHT state."""
    pan = _lobby(roster=[{"id": 3, "name": "Mika", "pet": {}, "live": False}],
                 dms={"eddy": [("eddy", "yo")]})
    names = [p["name"] for p in pan._others()]

    pan.sel, pan._mq = names.index("eddy"), 0
    pick = _card_of(pan).split("\n")[-1]
    assert "offline" in pick, pick
    assert "elsewhere" not in pick and "in the room" not in pick

    pan.sel = names.index("Mika")            # the ghost keeps its own words
    pick = _card_of(pan).split("\n")[-1]
    assert "elsewhere" in pick and "offline" not in pick, pick


def test_offline_rows_sit_under_a_different_heading_than_ghosts():
    """One glance has to separate 'playing elsewhere' from 'not here at all'
    -- both are live=False, so a mark alone never could.

    THIS IS THE BUG THAT FORCED THE REFACTOR (Joel 2026-08-31).  The two
    states were a "·" and a "°" in a 12-cell column; he read that column for
    a week as a room with people in it.  They are LABELLED GROUPS now, and
    the label is the thing that cannot be misread."""
    pan = _lobby(roster=[{"id": 3, "name": "Mika", "pet": {}, "live": False},
                         {"id": 4, "name": "Zed", "pet": {}}],
                 dms={"eddy": [("eddy", "yo")]})
    pan._mq, pan.sel = 0, 0
    txt = _card_of(pan)
    # each name sits under its OWN heading, in order
    for head, who in (("IN THE ROOM", "Zed"), ("ELSEWHERE", "Mika"),
                      ("THREADS", "eddy")):
        assert head in txt, f"{head} missing"
        after = txt.split(head, 1)[1]
        nxt = min([after.index(h) for h in ("IN THE ROOM", "ELSEWHERE", "THREADS")
                   if h in after] or [len(after)])
        assert who in after[:nxt], f"{who} is not under {head}"
    # and the marks that caused this are gone from the surface
    assert "°" not in txt


# ---- CLEARING a thread (Joel 2026-08-31) --------------------------------
# "yes I should have the option to clear a thread, instead of it staying
# there forever."  Nothing in the game ever removed a key from state.dms:
# threads were immortal, and BLOCKING did not help -- the mute swept their
# public lines and left the transcript and its roster row standing.

def test_a_thread_can_be_cleared_and_does_not_come_back():
    """The whole point: the row exists to open the thread, so clearing the
    thread takes the row with it -- and the save agrees."""
    from tuipet import persistence
    pan = _lobby(dms={"Ryo": [("Ryo", "gg")]}, unread=["Ryo"])
    pan._save_dms()                                   # the thread is on disk
    assert "Ryo" in persistence.get_dms()[0]

    pan.sel = pan._others().index(_row(pan, "Ryo"))
    pan.key("enter")                                  # open Ryo's actions
    assert pan.action_for is not None
    pan.key("d")                                      # ask
    assert pan.confirm_clear is not None and pan.action_for is None
    assert "Ryo" in pan.state.dms, "D alone must not delete anything"
    pan.key("y")                                      # confirm

    assert pan.confirm_clear is None
    assert "Ryo" not in pan.state.dms                 # the transcript
    assert "Ryo" not in pan.state.unread              # the badge
    assert _row(pan, "Ryo") is None                   # the door
    assert "Ryo" not in persistence.get_dms()[0]      # and the save file
    # a reload cannot resurrect it (the quit flush saves this same dict)
    pan._save_dms()
    assert "Ryo" not in persistence.get_dms()[0]


def test_clearing_asks_before_it_forgets():
    """A wipe is permanent and unsendable, so it asks -- and N means keep."""
    pan = _lobby(dms={"Ryo": [("Ryo", "gg")]})
    pan.sel = pan._others().index(_row(pan, "Ryo"))
    pan.key("enter")
    pan.key("d")
    assert "clear" in pan.strip() and "keep" in pan.strip()
    assert "clear the thread with Ryo?" in pan.text().plain
    pan.key("n")
    assert pan.confirm_clear is None
    assert pan.state.dms["Ryo"] == [("Ryo", "gg")], "N must keep the thread"
    assert _row(pan, "Ryo") is not None


def test_clearing_a_live_peers_thread_leaves_the_PERSON_in_the_room():
    """Clearing a conversation is not blocking and not a departure: the
    server says who is here, and it still says Ryo."""
    pan = _lobby(roster=[{"id": 2, "name": "Ryo", "pet": {}, "live": True}],
                 dms={"Ryo": [("Ryo", "gg")]})
    pan.sel = pan._others().index(_row(pan, "Ryo"))
    pan.key("enter")
    pan.key("d")
    pan.key("y")
    assert "Ryo" not in pan.state.dms                 # the thread went
    row = _row(pan, "Ryo")
    assert row is not None and row["id"] == 2         # the person stayed
    assert row["id"] != OFFLINE_ID


def test_the_clear_verb_is_offered_only_when_there_is_a_thread():
    """No thread, nothing to forget -- and D must not fire on a blank row."""
    pan = _lobby(roster=[{"id": 2, "name": "Zed", "pet": {}, "live": True}],
                 dms={"Ryo": [("Ryo", "gg")]})
    pan.sel = pan._others().index(_row(pan, "Zed"))
    pan.key("enter")
    assert "clear thread" not in _card_of(pan)
    pan.key("d")
    assert pan.confirm_clear is None                  # inert, menu still up
    assert pan.action_for is not None

    pan.key("escape")
    pan.sel = pan._others().index(_row(pan, "Ryo"))
    pan.key("enter")
    assert "clear thread" in _card_of(pan)            # ...and offered here


def test_clearing_the_thread_you_are_reading_returns_you_to_the_room():
    """You cannot be left staring at a transcript that no longer exists."""
    pan = _lobby(dms={"Ryo": [("Ryo", "gg")]})
    pan.sel = pan._others().index(_row(pan, "Ryo"))
    pan.key("enter")
    pan.key("v")                                      # open the thread
    assert pan.phase == "dm" and pan.dm_peer[1] == "Ryo"
    pan._clear_thread("Ryo")
    assert pan.phase == "lobby" and pan.dm_peer is None
    assert pan.sel >= 0 and pan.sel <= max(0, len(pan._others()) - 1)
