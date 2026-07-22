"""The HONORS board (prestige sink, bit-sink design 2026-07-14).

Cosmetic tamer titles priced 10k..250k: profile-level like egg licences
(they survive generations), bought on the shop's Honors tab, toggled worn
with ENTER, and shown on the STATUS border + the lobby presence card.
"""
from tuipet import data, persistence
from tuipet import lobbychat
from tuipet.pet import Pet
from tuipet.shopscreen import ShopPanel


def _panel(bits=500_000):
    p = Pet(num=-1, stage="Rookie", bits=bits)
    pan = ShopPanel(p)
    pan.tab = pan._tabs().index("Honors")
    return p, pan


def test_the_ladder_loads_ascending_and_unique():
    titles = data.load_titles()
    assert len(titles) >= 5
    ids = [t["id"] for t in titles]
    names = [t["name"] for t in titles]
    prices = [t["price"] for t in titles]
    assert len(set(ids)) == len(ids) and len(set(names)) == len(names)
    assert prices == sorted(prices) and prices[0] >= 10_000
    assert data.title_name(ids[0]) == names[0]
    assert data.title_name(-1) == ""
    # every honor carries its OWN inscription (item-info law v0.2.468: the
    # info panel never shows a generic line when the data can speak)
    descs = [t["desc"] for t in titles]
    assert all(descs) and len(set(descs)) == len(descs)


def test_buying_spends_bits_and_wears_the_honor():
    p, pan = _panel()
    first = data.load_titles()[0]
    pan.key("enter")
    assert p.bits == 500_000 - first["price"]
    assert first["id"] in persistence.get_titles_owned()
    assert persistence.get_title_worn() == first["id"]
    assert "Earned" in pan.msg


def test_enter_toggles_wearing_an_owned_honor():
    p, pan = _panel()
    pan.key("enter")                                  # buy (auto-wears)
    pan.key("enter")                                  # put it away
    assert persistence.get_title_worn() == -1
    pan.key("enter")                                  # wear it again
    assert persistence.get_title_worn() == data.load_titles()[0]["id"]
    assert p.bits == 500_000 - data.load_titles()[0]["price"]   # bought ONCE


def test_a_broke_tamer_is_refused_and_owns_nothing():
    p, pan = _panel(bits=5)
    pan.key("enter")
    assert "Not enough" in pan.msg
    assert p.bits == 5 and not persistence.get_titles_owned()
    assert persistence.get_title_worn() == -1


def test_titles_are_profile_level_like_egg_licences():
    _, pan = _panel()
    pan.key("enter")
    tid = data.load_titles()[0]["id"]
    # a NEW pet (a new generation) still owns and wears the honor
    q = Pet(num=-1, stage="Rookie")
    assert tid in persistence.get_titles_owned()
    assert persistence.get_title_worn() == tid
    del q


def test_the_status_subtitle_wears_the_honor():
    from tuipet.app import _gen_subtitle
    p = Pet(num=-1, stage="Rookie")
    p.generation = 3
    assert _gen_subtitle(p) == "gen 3"
    first = data.load_titles()[0]
    persistence.title_own(first["id"])
    persistence.set_title_worn(first["id"])
    assert _gen_subtitle(p) == "gen 3 · %s" % first["name"]


def test_the_lobby_card_carries_the_worn_title_only():
    from tuipet.lobbyscreen import LobbyPanel
    p = Pet(num=100, stage="Champion")
    pan = LobbyPanel.__new__(LobbyPanel)
    pan.pet = p
    assert "title" not in pan._card()                 # nothing worn: no field
    first = data.load_titles()[0]
    persistence.title_own(first["id"])
    persistence.set_title_worn(first["id"])
    assert pan._card()["title"] == first["name"]


def test_the_honors_tab_renders():
    _, pan = _panel()
    t = pan.text().plain
    assert "Honors" in t and "Bit Collector" in t and "10000b" in t
    assert data.load_titles()[0]["desc"].split()[0] in t   # the inscription shows
    pan.key("enter")
    t = pan.text().plain
    assert "worn" in t


# ---- the honor in the ROOM (roster star + own you-line, 2026-07-14) -----------

def _fake_lobby():
    from tuipet.lobbyscreen import LobbyPanel
    from tuipet.net import LobbyState

    class _C:
        def chat(self, t): pass
        def invite(self, *a): pass
        def respond(self, *a, **k): pass
        def relay(self, *a): pass
        def update_pet(self, c): pass

    p = Pet(num=100, stage="Champion")
    pan = LobbyPanel(p, on_connect=lambda n, pw, c: None)
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "JoeltCo"
    s.roster = [
        {"id": 1, "name": "JoeltCo", "live": True, "pet": {}},
        {"id": 2, "name": "Roxi", "live": True,
         "pet": {"name": "WarGreymon", "stage": "Mega", "title": "Bit Baron"}},
        {"id": 3, "name": "Averylongtamername", "live": True,
         "pet": {"name": "Agumon", "stage": "Rookie", "title": "Data Dynast"}},
    ]
    pan.client, pan.state, pan.phase = _C(), s, "lobby"
    pan.status = lobbychat.HINTS_OPEN
    return pan


def test_the_roster_stars_titled_players():
    t = _fake_lobby().text().plain
    assert "Roxi ★" in t                     # titled peer wears the star
    assert "JoeltCo ★" not in t              # untitled stays plain


def test_your_own_worn_honor_shows_on_the_you_line():
    pan = _fake_lobby()
    assert "you: JoeltCo" in pan.text().plain and "★" not in \
        pan.text().plain.split("\n")[0]      # nothing worn: plain you-line
    first = data.load_titles()[0]
    persistence.title_own(first["id"])
    persistence.set_title_worn(first["id"])
    head = pan.text().plain.split("\n")[0]
    assert "you: JoeltCo · ★" in head        # marquee head shows the honor


def test_long_roster_entries_scroll_the_star_into_view():
    pan = _fake_lobby()
    pan._mq = 0
    t0 = pan.text().plain
    assert "Averylongt" in t0                # the head of the long entry
    assert "mername ★" not in t0             # ...whose star is off-column
    pan._mq = 38                             # step 19 -> the window has slid
    t1 = pan.text().plain
    assert "mername ★" in t1, "the marquee must carry the star into view"


def test_the_prestige_ladder_reaches_a_million():
    """Gameplay polish #25 (2026-07-22): after 435k of honors the bankroll
    went inert.  Two rungs extend the existing ladder — same system, same
    plate, no new economy."""
    from tuipet import data
    ts = data.load_titles()
    assert len(ts) == 7
    prices = [t["price"] for t in ts]
    assert prices == sorted(prices) and prices[-1] == 1_000_000
    assert all(t["name"] and t["desc"] for t in ts)
