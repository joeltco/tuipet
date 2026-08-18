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
