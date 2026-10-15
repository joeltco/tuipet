"""Menus audit 2026-10-14: presentation follows live rules and cell budgets."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from rich.cells import cell_len
from rich.text import Text

from tuipet import menu, persistence, shop, statusbox
from tuipet.app import TuiPetApp
from tuipet.pet import Pet, AUTO_CARE_HOUR_PRICE, AUTO_CARE_VISIT_PRICE


def _pet(**kw):
    p = Pet(num=100, name="Rex", stage="Champion", attribute="Vaccine", obedience=150)
    p.world_seconds = 600.0
    p.bits = 99999
    for key, value in kw.items():
        setattr(p, key, value)
    return p


class _Stats:
    border_subtitle = ""
    def update(self, text):
        self.text = str(text)


def _plain(text):
    return text.plain if isinstance(text, Text) else Text.from_markup(text).plain


def _fits(text, width, rows):
    lines = _plain(text).rstrip("\n").split("\n")
    assert len(lines) <= rows
    assert all(cell_len(line) <= width for line in lines), lines


def _card(p, panel, painter=None):
    app = SimpleNamespace(pet=p, mode=panel, stats_w=_Stats(), sound=False)
    fn = painter or statusbox.painter_for(panel)
    assert fn is not None
    fn(app)
    _fits(app.stats_w.text, 26, 16)
    return _plain(app.stats_w.text)


def _dossier(p, entry, mode="shop"):
    panel = SimpleNamespace(mode=mode, cursor=0, _rows=lambda: [entry])
    return _card(p, panel, statusbox.shop)


def test_a1_tantrum_text_matches_the_timeout():
    from tuipet.helpscreen import HELP
    from tuipet.disciplinescreen import DisciplinePanel
    p = _pet(obedience=50, discipline_call=True, scold_window=599)
    before = p.care_mistakes
    p.tick(1)
    assert p.obedience == 45 and p.care_mistakes == before
    text = " ".join(line for line, _ in HELP)
    assert "manners -5" in text and "cost a care mistake" not in text
    text = _card(p, DisciplinePanel(p))
    assert "manners -5" in text and "ignored tantrums cost ✗" not in text


@pytest.mark.parametrize("paint", [menu.header, menu.bar])
@pytest.mark.parametrize("right", ["界" * 24, "W" * 80, "W" * 37])
def test_a2_header_right_field_has_a_cell_budget(paint, right):
    _fits(paint("OPTIONS", right), menu.W, 2)
    assert menu._clip("title", 0) == ""


def test_a2_options_keeps_a_wide_account_readable():
    from tuipet.optionsscreen import OptionsPanel
    persistence.set_account("界" * 24, "password")
    panel = OptionsPanel(_pet(), lambda: False, lambda: None)
    _fits(panel.text(), 40, 12)
    assert "OPTIONS" in panel.text().plain and "界" in panel.text().plain


@pytest.mark.parametrize("glyph", ["界", "🐾"])
def test_a3_unicode_bug_input_fits_without_losing_typed_content(glyph):
    from tuipet.bugscreen import BugReportPanel, wrap
    panel = BugReportPanel(_pet())
    panel.buf = glyph * 160
    before = panel.buf
    _fits(panel.text(), 40, 12)
    assert "".join(wrap(before, 38)) == before
    assert panel.buf == before and panel.key("enter")[1] == ("bug", before)


def test_a3_caret_does_not_hide_the_last_full_width_character():
    from tuipet.bugscreen import BugReportPanel
    panel = BugReportPanel(_pet())
    panel.buf = "界" * 19
    text = panel.text().plain
    _fits(text, 40, 12)
    assert panel.buf in text and "_" in text


def test_a4_every_open_map_card_fits():
    from tuipet.adventurescreen import ZonePickPanel
    from tuipet.adventure import ZONES
    p = _pet()
    panel = ZonePickPanel(p)
    for count in range(1, len(ZONES) + 1):
        panel.indices = list(range(count))
        for i in range(count):
            panel.cursor = i
            text = _card(p, panel)
            assert ZONES[i]["tier"] in text
            assert f"{i + 1} of {count}" in text


@pytest.mark.parametrize("key", ["gold_pill", "egg:34"])
def test_a5_price_and_shortfall_are_complete_and_fit(key):
    p = _pet(bits=0)
    e = shop.entry(key) if key == "gold_pill" else dict(key=key, egg_idx=34, name="DORU Egg", price=10000)
    text = _dossier(p, e)
    assert "Price   10000b" in text and "Short   10000b" in text


@pytest.mark.parametrize("owned", [False, True])
def test_a6_egg_dossier_uses_egg_ownership(owned):
    p = _pet()
    e = dict(key="egg:34", egg_idx=34, name="DORU Egg", price=10000, owned=owned)
    text = _dossier(p, e)
    assert "digitama" in text and "carousel" in text
    assert "a curiosity" not in text and "Owned   x0" not in text
    if owned:
        assert "owned" in text and "ENTER buy" not in text
    else:
        assert "1 egg per profile/day" in text


def test_a6_spent_egg_purchase_ration_is_visible_before_buy():
    p = _pet(town_bought={"day": shop._today_ordinal(), "all:egg": 1})
    e = dict(key="egg:34", egg_idx=34, name="DORU Egg", price=10000, owned=False)
    text = _dossier(p, e)
    assert "egg bought today" in text and "ENTER buy" not in text
    assert "State   available" not in text


def test_a7_spent_home_stock_has_no_buy_hint_or_price_only_list_row():
    from tuipet.shopscreen import ShopPanel
    p = _pet()
    e = next(e for e in shop.home_stock(pet=p) if e["key"] == "capsule_a")
    assert shop.town_buy(p, e)[1] == "confirm"
    panel = ShopPanel(p)
    for tab in range(len(panel._tabs())):
        panel.tab = tab
        for i, entry in enumerate(panel._rows()):
            if entry.get("key") == "capsule_a":
                panel.cursor, panel.msg_t = i, 0
                text = _card(p, panel)
                assert "sold out today" in text and "ENTER buy" not in text
                assert any("Capsule" in line and "out" in line
                           for line in panel.text().plain.splitlines()[7:])
                assert "ENTER buy" not in _plain(panel.strip())
                return
    pytest.fail("Capsule shelf not found")


def test_a7_remaining_ration_and_scope_are_visible():
    p = _pet()
    e = dict(shop.entry("capsule_a"), left=1, town_id="home")
    text = _dossier(p, e)
    assert "1 left" in text and "profile/day" in text
    e = dict(shop.entry("fish"), left=2, town_id=0)
    text = _dossier(p, e)
    assert "2 left" in text and "town/day" in text


def test_a7_bought_power_cap_is_purchase_only_and_live():
    p = _pet(bought_power={"vaccine": 15})
    e = dict(shop.entry("vaccine_chip_g"), left=1, town_id=29)
    text = _dossier(p, e)
    assert "Bought V15/30 this gen" in text and "purchase cap reached" in text
    assert "ENTER buy" not in text
    text = _dossier(p, e, mode="bag")
    assert "purchase cap reached" not in text and "ENTER use" in text
    assert p.bought_power == {"vaccine": 15}


@pytest.mark.parametrize("key,limit", [("cold_compress", "once per life"),
                                      ("miracle_drink", "once per life"),
                                      ("grow_capsule", "once per stage")])
def test_a7_bag_use_limits_and_spent_state_are_visible(key, limit):
    p = _pet(inventory={key: 1})
    e = shop.entry(key)
    assert limit in _dossier(p, e, "bag")
    if key == "grow_capsule":
        p.grow_used = f"{p.num}:{p.stage}"
    else:
        p.once_used = [key]
    text = _dossier(p, e, "bag")
    assert "already used" in text and "ENTER use" not in text and "R sell" in text


def test_a7_relic_dossier_discloses_existing_body_gates():
    text = _dossier(_pet(), shop.entry("grey_claws"), "bag")
    assert "half stage" in text and "care gates" in text


@pytest.mark.parametrize("row,verb", [("theme", "open"), ("sound", "open"),
                                    ("account", "open"), ("cloud", "toggle"),
                                    ("update", "check"), ("keys", "open"),
                                    ("new", "retire"), ("erase", "confirm")])
def test_a8_options_card_names_the_selected_action(row, verb):
    from tuipet.optionsscreen import OptionsPanel, _ROWS
    p = _pet()
    panel = OptionsPanel(p, lambda: False, lambda: None)
    panel.cursor = _ROWS.index(row)
    assert f"ENTER {verb}" in _card(p, panel)


@pytest.mark.parametrize("state,verb", [("confirm", "erase"), ("confirm_new", "retire"),
                                      ("confirm_restart", "restart")])
def test_a8_options_confirmation_card_names_the_current_action(state, verb):
    from tuipet.optionsscreen import OptionsPanel
    p = _pet()
    panel = OptionsPanel(p, lambda: False, lambda: None)
    setattr(panel, state, True)
    assert f"ENTER {verb}" in _card(p, panel)


@pytest.mark.parametrize("child,title", [("ThemePanel", "Themes"), ("SoundPanel", "Sound"),
                                       ("KeysPanel", "Keys"), ("AccountPanel", "Account"),
                                       ("CloudWaitPanel", "Account"), ("TownPanel", "Town")])
def test_a8_each_child_has_its_own_card(child, title):
    from tuipet.optionsscreen import OptionsPanel, SoundPanel, KeysPanel
    from tuipet.themescreen import ThemePanel
    from tuipet.accountscreen import AccountPanel, CloudWaitPanel
    from tuipet.townscreen import TownPanel
    p = _pet()
    children = dict(ThemePanel=lambda: ThemePanel(),
                    SoundPanel=lambda: SoundPanel(lambda: False, lambda: None),
                    KeysPanel=lambda: KeysPanel(TuiPetApp.BINDINGS),
                    AccountPanel=lambda: AccountPanel("界" * 24),
                    CloudWaitPanel=lambda: CloudWaitPanel("界" * 24),
                    TownPanel=lambda: TownPanel(p, 0))
    mode = children[child]()
    if child == "AccountPanel":
        mode.pw_buf = "private-test-password"
    text = _card(p, mode)
    assert text.splitlines()[0] == title
    parent = OptionsPanel(p, lambda: False, lambda: None)
    parent.sub = mode
    assert _card(p, parent) == text
    if child in ("AccountPanel", "CloudWaitPanel"):
        assert "private-test-password" not in text and "*" not in text


@pytest.mark.parametrize("state,remedy", [({"sick": True}, "feed it the pill"),
    ({"asleep": True, "lights": True}, "lights off"),
    ({"injured": True}, "patch it up"), ({"hunger": 0}, "F"),
    ({"strength": 0}, "train"), ({"poop": 3}, "C"),
    ({"energy": 0}, "rest"), ({"discipline_call": True}, "scold it")])
def test_a9_alarm_keeps_the_complete_remedy_on_the_first_strip(state, remedy):
    p = _pet(**dict(dict(name="AncientMegatherimon", hunger=4, strength=4, energy=20), **state))
    text = TuiPetApp._need_message(SimpleNamespace(_fx_frame=100), p)
    _fits(text, 40, 1)
    assert remedy in _plain(text)


@pytest.mark.parametrize("over,tree,space,escape", [(False, True, "fight on", "forfeit"),
    (True, True, "result", "leave"), (True, False, None, "leave")])
def test_a10_cup_hints_match_the_bracket_and_result(over, tree, space, escape):
    from tuipet.tournamentscreen import TournamentPanel
    panel = TournamentPanel(_pet())
    panel.phase, panel.tree_view = "bracket", tree
    panel.tourney = SimpleNamespace(over=over)
    text = _plain(panel.strip())
    _fits(text, 40, 1)
    assert f"ESC {escape}" in text
    assert (f"SPACE {space}" in text) if space else "SPACE" not in text


def test_a11_raid_leader_name_and_markup_fit():
    from tuipet.raidscreen import RaidPanel
    p = _pet()
    panel = RaidPanel.__new__(RaidPanel)
    panel.pet, panel.sub = p, None
    panel.client = SimpleNamespace(raid=dict(now=1000, attempts=3, you=[1, 5000000],
        boss=dict(name="Boss", hp=5000000, max_hp=5500000, start=900, end=2000),
        top=[["[red]" + "界" * 16, 5000000]]))
    text = _card(p, panel)
    assert "5.0M" in text and "[red]" in text


def test_a11_ladder_unicode_name_column_and_footer_fit():
    from tuipet.lobbyscreen import LobbyPanel
    panel = LobbyPanel.__new__(LobbyPanel)
    panel.client = SimpleNamespace(name="Joel", ladder=dict(season="2026-10", days_left=17,
        top=[["界" * 24, 123]] * 8, you=[123, 1234]))
    text = panel._text_ladder()
    _fits(text, 40, 12)
    assert "season resets in 17 days" in text.plain


def test_a11_ladder_card_reserves_the_leaders_wins():
    from tuipet.lobbyscreen import LobbyPanel
    from tuipet.net import LobbyState
    p = _pet()
    panel = LobbyPanel.__new__(LobbyPanel)
    panel.state = LobbyState()
    panel.state.me_id = 1
    panel.bshow, panel.phase = None, "ladder"
    panel.client = SimpleNamespace(ladder=dict(season="2026-10", days_left=17,
        top=[["[red]" + "界" * 24, 1234]], you=[123, 1234]))
    text = _card(p, panel)
    assert "1234W" in text and "[red]" in text


def test_a12_help_distinguishes_the_accelerated_clock():
    from tuipet.helpscreen import HELP
    text = " ".join(line for line, _ in HELP)
    assert "2 game days" in text and "game-hour wage" in text
    assert all(cell_len(line) <= 38 for line, _ in HELP)


@pytest.mark.parametrize("stage", list(AUTO_CARE_VISIT_PRICE))
def test_a12_assistant_names_both_exact_fees_and_units(stage):
    from tuipet.assistscreen import AssistPanel
    p = _pet(stage=stage, bits=10 ** 20)
    panel = AssistPanel(p)
    _fits(panel.text(), 40, 12)
    visit, hour = AUTO_CARE_VISIT_PRICE[stage], AUTO_CARE_HOUR_PRICE[stage]
    assert f"{visit}b/care" in panel.text().plain
    if hour:
        assert f"{hour}b/game hour" in panel.text().plain
    text = _card(p, panel)
    assert f"Visit   {visit}b" in text and f"Hour    {hour}b/game hour" in text
    assert f"~{visit}b" not in text


@pytest.mark.parametrize("book", ["album", "hall"])
def test_a13_book_detail_card_has_detail_keys(book):
    from tuipet.albumscreen import AlbumPanel
    from tuipet.hallscreen import HallPanel
    p = _pet()
    panel = AlbumPanel(p) if book == "album" else HallPanel(p)
    if book == "hall":
        panel.elders = [dict(name="Rex", num=100, gen=1, stage="Champion", age=600, wins=1, cups=0)]
        panel.n = 1
    panel.detail = True
    text = _card(p, panel)
    assert "←→ page  ESC back" in text and "ENTER view" not in text and "ENTER page" not in text


@pytest.mark.parametrize("owned,worn,verb", [(False, False, "buy"), (True, False, "wear"), (True, True, "remove")])
def test_a13_honor_dossier_names_buy_wear_and_remove(owned, worn, verb):
    e = dict(title_id=1, name="Honor", price=1000, owned=owned, worn=worn)
    assert f"ENTER {verb}" in _dossier(_pet(), e)


@pytest.mark.parametrize("phase,hint", [("intro", "any key skip"), ("anim", "SPACE hurry")])
def test_a13_battle_card_names_the_phase_action(phase, hint):
    p = _pet()
    panel = SimpleNamespace(battle=None, enemy={"name": "Foe"}, raid=False,
        hud_php=5, hud_fhp=5, hud_note="Battle start!", locked=None, done_anim=False, phase=phase)
    assert hint in _card(p, panel, statusbox.battle)


def test_a14_egg_guide_labels_the_digitama_as_an_egg():
    from tuipet.eggguidescreen import EggGuidePanel
    text = _card(_pet(), EggGuidePanel())
    assert "Egg      " in text and "Hatches" not in text


@pytest.mark.parametrize("value", [1234, 99999, 10 ** 20])
def test_a15_big_home_numbers_fit_and_keep_exact_data(value, monkeypatch):
    from tuipet import digicore
    p = _pet(wins=value, battles=value, trophies=value, vaccine=value, data_power=value, virus=value)
    p.dna_owned = {"NatureSpirit": 123456}
    before = deepcopy(p.__dict__)
    monkeypatch.setattr(statusbox, "festival_line", lambda: "Christmas Festival")
    _fits("\n".join(statusbox.home_lines(p)), 26, 16)
    assert p.__dict__ == before
    pages = digicore.build_pages(p)
    assert str(value) in str(pages)
    assert p.dna_owned == {"NatureSpirit": 123456}


def test_menu_readouts_preserve_a_legitimate_legacy_bank_and_growth_clocks():
    p = Pet.new_egg(egg_type=0)
    p.dna_owned = {"NatureSpirit": 99, "DragonsRoar": 32, "None": 13}
    p.dna_applied = {"NatureSpirit": 123456}
    p.stage_seconds, p.age_seconds = 20.0, 20.0
    before = deepcopy(p.__dict__)
    statusbox.egg_lines(p)
    assert p.__dict__ == before
    restored, _ = persistence.pet_from_save(persistence.to_save_dict(p))
    assert restored is not None
    assert restored.dna_owned["NatureSpirit"] == 99
    assert restored.dna_owned["DragonsRoar"] == 32
    assert restored.dna_owned["None"] == 0           # legacy dud DNA cashed in (2026-10-15)
    assert restored.dna_applied["NatureSpirit"] == 123456
    assert restored.stage_seconds == p.stage_seconds and restored.age_seconds == p.age_seconds


@pytest.mark.parametrize("blob", [[], {"NatureSpirit": []}, {"NatureSpirit": "broken"}])
def test_malformed_bank_is_rejected_without_a_renderer_crash(blob):
    saved = persistence.to_save_dict(Pet.new_egg(egg_type=0))
    saved["dna_owned"] = blob
    restored, _ = persistence.pet_from_save(saved)
    assert restored is None


def test_ladder_card_keeps_the_players_own_wins():
    """Cross-check 2026-10-14: the leader-width fix reused `wins` and the
    player's row read the leader's count ('You #2 · 99WW')."""
    from types import SimpleNamespace
    seen = {}
    m = SimpleNamespace(client=SimpleNamespace(ladder={
        "season": 3, "you": [2, 7], "days_left": 4, "top": [["leader", 99], ["me", 7]]}))
    app = SimpleNamespace()
    orig = statusbox.card
    statusbox.card = lambda a, title, lines: seen.setdefault("lines", lines)
    try:
        statusbox._lobby_ladder(app, m)
    finally:
        statusbox.card = orig
    you = next(line for line in seen["lines"] if line.startswith("You"))
    assert "#2" in you and "7W" in you and "99" not in you and "WW" not in you
