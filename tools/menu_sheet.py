"""The MENU CONTACT SHEET (menu audit 2026-07-21).

The adventure sheet's sibling for EVERY OTHER menu: drives each real
panel through its shipped views and prints every frame as visible text
with a 40-col ruler, so a human (or Claude) can EYEBALL word run-offs,
mid-word clips and overflow the way pytest never does (UI-render law).
Lines wider than 40 CELLS are flagged inline with their true cell width;
strips wider than 40 are flagged the same way (they marquee live, which
the hint law forbids).

Usage: HOME=<throwaway> python tools/menu_sheet.py [state ...]   (default: all)
"""
import datetime
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rich.cells import cell_len  # noqa: E402
from rich.text import Text  # noqa: E402

from tuipet import adventure, render, tournament  # noqa: E402
from tuipet.pet import Pet  # noqa: E402

D = datetime.date(2026, 3, 3)
tournament._today = lambda: D                 # a stable, festival-free day

RULER = "0---------1---------2---------3---------4---------5"

# -- the pixel tap (adventure_sheet's): scene frames decode to .#% -------------
_LAST = {"buf": None}
_real_paint = render._paint_cells


def _tap(buf, *a, **k):
    _LAST["buf"] = [row[:] for row in buf]
    return _real_paint(buf, *a, **k)


render._paint_cells = _tap


def show(title, panel, budget=40):
    txt = panel.text()
    print(f"\n===== {title} =====")
    print(RULER[:budget + 2])
    buf = _LAST["buf"]
    _LAST["buf"] = None
    if buf is not None:
        for row in buf:
            print("".join(".#%"[min(v, 2)] for v in row))
    else:
        lines = txt.plain.split("\n")
        for ln in lines:
            w = cell_len(ln)
            print(ln + (f"   ⚠ {w} cells" if w > budget else ""))
        if len(lines) > 17:
            print(f"⚠ {len(lines)} rows")
    strip = getattr(panel, "strip", lambda: "")()
    if strip:
        plain = Text.from_markup(strip).plain
        w = cell_len(plain)
        print(f"strip> {plain}" + (f"   ⚠ {w} cells (marquees!)" if w > 40 else ""))


def _pet(**kw):
    p = Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


SHEET = {}


def state(name):
    def deco(fn):
        SHEET[name] = fn
        return fn
    return deco


# ---- home chrome -------------------------------------------------------------
@state("chrome")
def _chrome():
    from tuipet import app, statusbox
    print("\n===== home chrome: action bar (71-cell lines) =====")
    for ln in Text.from_markup(app.keys_markup()).plain.split("\n"):
        w = cell_len(ln)
        print(ln + (f"   ⚠ {w} cells" if w > 71 else ""))
    print("\n===== home chrome: status card (26-col lane) =====")
    p = _pet()
    for raw in statusbox.home_lines(p):
        ln = Text.from_markup(raw).plain
        w = cell_len(ln)
        print(ln + (f"   ⚠ {w} cells" if w > 26 else ""))


# ---- the simple screens ------------------------------------------------------
@state("title")
def _title():
    from tuipet.titlescreen import TitlePanel
    show("title", TitlePanel())


@state("account")
def _account():
    from tuipet.accountscreen import AccountPanel
    a = AccountPanel()
    show("account (login form)", a)
    a.name = "averylongplayername"
    a.pw = "hunter2"
    show("account (typed long)", a)


@state("help")
def _help():
    from tuipet.helpscreen import HelpPanel
    h = HelpPanel(_pet())
    show("help (top)", h)
    while h.top < h._max_top():
        h.key("pagedown")
        show(f"help (top={h.top})", h)


@state("options")
def _options():
    from tuipet.optionsscreen import OptionsPanel
    o = OptionsPanel(_pet(), lambda: True, lambda: None)
    show("options root", o)
    o.key("down")
    show("options (second row)", o)


@state("sound")
def _sound():
    from tuipet.optionsscreen import SoundPanel
    show("options: sound", SoundPanel(lambda: True, lambda: None))


@state("keys")
def _keys():
    from tuipet.optionsscreen import KeysPanel
    from tuipet.app import TuiPetApp
    show("options: keys", KeysPanel(TuiPetApp.BINDINGS))


@state("themes")
def _themes():
    from tuipet.themescreen import ThemePanel
    show("themes", ThemePanel())


@state("scenes")
def _scenes():
    from tuipet.backgroundscreen import BackgroundPanel
    show("scenes", BackgroundPanel(_pet()))


@state("feed")
def _feed():
    from tuipet.feedscreen import FeedPanel
    show("feed", FeedPanel(_pet(bits=500)))


@state("shop")
def _shop():
    from tuipet.shopscreen import ShopPanel
    p = _pet(bits=9999)
    s = ShopPanel(p)
    for i, name in enumerate(("Food", "Items", "Eggs", "Honors")):
        s.tab = i
        show(f"home shop tab {i} ({name})", s)
    show("bag", ShopPanel(p, start_mode="bag", bag_only=True))


@state("digicore")
def _digicore():
    from tuipet.digicorescreen import DigiCorePanel
    d = DigiCorePanel(_pet())
    for i in range(len(d.pages)):
        d.i = i
        show(f"digicore page {i}: {d.pages[i][0]}", d, budget=40)


@state("dna")
def _dna():
    from tuipet.dnascreen import DNAPanel
    show("dna", DNAPanel(_pet()))


@state("jogress")
def _jogress():
    from tuipet.jogressscreen import JogressPanel
    j = JogressPanel(_pet(), 29, 45, 60)
    show("jogress (fusing)", j)
    j.phase = "fused"
    show("jogress (fused)", j)


@state("eggselect")
def _eggselect():
    from tuipet.eggselectscreen import EggSelectPanel
    e = EggSelectPanel(_pet())
    show("egg select", e)


@state("eggguide")
def _eggguide():
    from tuipet.eggguidescreen import EggGuidePanel
    g = EggGuidePanel(_pet())
    show("egg guide (first)", g)
    g.key("down")
    g.key("down")
    show("egg guide (scrolled)", g)


@state("townegg")
def _townegg():
    from tuipet.towneggscreen import TownEggPanel
    show("town egg", TownEggPanel(_pet(bits=9999), town_id=4))


@state("album")
def _album():
    from tuipet import persistence
    from tuipet.albumscreen import AlbumPanel
    persistence.album_add(29)                       # one discovered entry
    a = AlbumPanel(_pet())
    show("album (list, top)", a)
    a.i = a.roster.index(29)
    show("album (list, on Agumon)", a)
    a.key("enter")
    show("album (detail, seen)", a)
    a.key("escape")
    a.i = 0
    a.key("enter")
    show("album (detail, unseen)", a)


@state("assist")
def _assist():
    from tuipet.assistscreen import AssistPanel
    show("assist", AssistPanel(_pet()))


@state("bug")
def _bug():
    from tuipet.bugscreen import BugReportPanel
    b = BugReportPanel(_pet())
    show("bug report", b)


@state("death")
def _death():
    from tuipet.deathscreen import DeathPanel
    from tuipet import evolution
    p = _pet()
    mem = evolution.make_digimemory(p) if hasattr(evolution, "make_digimemory") else None
    d = DeathPanel(p, new_mem=mem)
    d._hold = 0
    show("death (memorial)", d)


@state("raid")
def _raid():
    from tuipet.raidscreen import RaidPanel
    stub = types.SimpleNamespace(state=types.SimpleNamespace(me_id=None),
                                 raid=None, raid_get=lambda: None,
                                 close=lambda: None)
    show("raid (calling the gate)", RaidPanel(_pet(), None, client=stub))


@state("cupboard")
def _cupboard():
    from tuipet.tournamentscreen import TournamentPanel
    p = _pet(bits=99999)
    p.strength = p.hunger = 4
    p._set_energy(p.max_energy)
    t = TournamentPanel(p)
    show("cup board", t, budget=40)
    t.key("down")
    show("cup board (row 2)", t, budget=40)


# ---- the lobby (Joel saw an ESC run-off here) --------------------------------
def _lobby(roster_extra=(), **kw):
    from tuipet.lobbyscreen import LobbyPanel
    from tuipet import net
    pan = LobbyPanel(_pet(), None)
    st = net.LobbyState()
    st.connected = True
    st.me_id = 1
    st.me_name = "joel"
    st.roster = [{"id": 1, "name": "joel", "pet": {"num": 29}},
                 {"id": 2, "name": "Ryo", "pet": {"num": 45}},
                 {"id": 3, "name": "Verylongplayername", "pet": {"num": 60},
                  "live": False}] + list(roster_extra)
    st.chat = [("Ryo", f"line {i}") for i in range(12)]
    from tuipet.lobbychat import HINTS_OPEN
    pan.state = st
    pan.phase = "lobby"
    pan.status = HINTS_OPEN
    for k, v in kw.items():
        setattr(pan, k, v)
    return pan


@state("lobby")
def _lobby_states():
    from tuipet.lobbyscreen import LobbyPanel
    pan = LobbyPanel(_pet(), None)
    show("lobby login", pan)
    show("lobby open room", _lobby())
    show("lobby folded", _lobby(rost_hidden=True,
                                status="↑↓ scroll · ← player box · ESC leave"))
    show("lobby scrolled", _lobby(scroll=3))
    show("lobby action (live peer)", _lobby(action_for=(2, "Ryo", True)))
    show("lobby action (ghost)", _lobby(action_for=(3, "Verylongplayername", False)))
    b = _lobby(action_for=(2, "Ryo", True))
    b.state.blocked = {"Ryo"}
    show("lobby action (blocked)", b)
    show("lobby invite", _lobby(invite_prompt={"from_id": 2, "from_name": "Ryo",
                                               "kind": "battle"}))
    show("lobby pm compose", _lobby(pm_to=(2, "Ryo")))
    u = _lobby()
    u.state.unread = {"Ryo"}
    show("lobby unread nudge", u)
    c = _lobby()
    c.pet.hunger = 0
    show("lobby care cue", c)
    d = _lobby(phase="dm", dm_peer=(2, "Ryo"))
    d.state.dms = {"Ryo": [("Ryo", "hello"), ("joel", "hi")] * 6}
    show("lobby dm", d)
    show("lobby ladder (fetching)", _lobby(phase="ladder"))
    lad = _lobby(phase="ladder")
    lad.client = types.SimpleNamespace(
        ladder={"season": 3, "top": [("Ryo", 41), ("joel", 30)],
                "you": [2, 30]}, name="joel")
    show("lobby ladder (filled)", lad)


def main():
    names = sys.argv[1:] or list(SHEET)
    for n in names:
        fn = SHEET.get(n)
        if fn is None:
            print(f"unknown state: {n}  (have: {', '.join(SHEET)})")
            continue
        fn()


if __name__ == "__main__":
    main()
