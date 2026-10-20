"""Final bug hunt 2026-10-20 (Astra, proven by repro): each test fails on the
pre-fix code."""
from tuipet import data, persistence
from tuipet.pet import Pet


def _pet():
    num = next(n for n, r in data.load_sprites()[1].items()
               if r["stage"] == "Rookie" and not data.is_placeholder(n))
    p = Pet.from_num(num)
    p.obedience = 150
    return p


def test_album_records_for_the_account_switched_to(monkeypatch):
    monkeypatch.setattr(persistence, "_ALBUM_SEEN", set())
    p = _pet()
    persistence.set_account("first", "pw")
    persistence.save(p)
    persistence.set_account("second", "pw")
    persistence.save(p)
    assert data.canonical_num(p.num) in persistence.get_album()


def test_perfect_dig_bonus_digimemory_carries_its_own_payload():
    from tuipet.adventurescreen import AdventurePanel, INV_WALK_T
    p = _pet()
    pan = AdventurePanel(p)
    pan._find = "digimemory"
    pan._dig()
    pan._scene["t"] = INV_WALK_T
    pan._scene["meter"].update(bar=12, hist=[12])
    pan._lock_dig()
    assert pan._scene["grade"] == "mega"
    assert p.inventory["digimemory"] == 2 and len(p.wild_memories) == 2


# ---- hunt B: lobby / account / help ---------------------------------------
from rich.text import Text  # noqa: E402

from test_lobby_audit import _panel  # noqa: E402


def test_unread_name_with_markup_renders_literally():
    from tuipet.app import _hud_plain
    pan, state = _panel()
    state.unread.add("a[/]")
    state.dms["a[/]"] = [("a[/]", "hello")]
    assert "a[/]" in _hud_plain(pan.strip())


def test_invite_cannot_steal_the_clear_confirmation_y():
    pan, state = _panel()
    state.dms["mika"] = [("mika", "keep this message")]
    pan.sel = [p["name"] for p in pan._others()].index("mika")
    pan.key("enter")
    pan.key("d")
    state.inbox.append({"t": "invite", "from_id": 3, "from_name": "creep", "kind": "battle"})
    pan.anim()
    pan.key("y")
    assert pan.phase == "lobby" and pan.partner is None
    assert "mika" not in state.dms or not state.dms["mika"]


def test_rival_leaving_before_seed_drops_the_live_bar():
    from tuipet import battle
    pan, state = _panel()
    pan._enter_session(2, "mika", "battle", True)
    pan._battle_begin(battle.battle_card(pan.pet))
    pan.key("space")
    pan._on_relay({"from_id": 2, "payload": {"kind": "battle", "abort": True}})
    assert pan.bphase == "over" and pan.bshow is None
    assert "lock" not in Text.from_markup(pan.strip()).plain.lower()


def test_wide_last_password_char_and_cursor_stay_visible():
    from tuipet.accountscreen import AccountPanel
    pan = AccountPanel(name="tamer")
    for key in "a" * 25 + "界":
        pan.key(key)
    line = pan.text().plain.splitlines()[4]
    assert "界_" in line


def test_help_makes_no_tilde_escape_claim():
    from tuipet.helpscreen import HELP
    assert not any("also means Escape" in text for text, _ in HELP)
