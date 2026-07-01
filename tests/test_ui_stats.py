"""Stats-panel render bounds (Workstream C).

The #stats box is fixed at 30x18 with a round border + `padding: 0 1`, leaving an
inner area of exactly 26 cols x 16 rows. Any rendered line wider than 26 wraps and
eats into the 16-row budget (and looks broken). The worst offender was the
status_word + deco line, which could reach 38 cols (asleep+sick+poop+effect on an
elderly pet); _status_line now bounds it. These tests render the REAL paint methods
(bound onto a plain object, no Textual mount) and assert nothing overflows.
"""
import pytest
from rich.text import Text

from tuipet.app import Stats, _status_line
from tuipet.pet import Pet
from tuipet import data

INNER_W = 26
INNER_H = 16


class _FakeStats:
    """Carries Stats' real paint methods with none of the Textual machinery."""
    border_subtitle = None
    def update(self, x):
        self._cap = x
_FakeStats.paint = Stats.paint
_FakeStats._paint_egg = Stats._paint_egg
_FakeStats._paint_grave = Stats._paint_grave


def _render(pet):
    f = _FakeStats()
    f.paint(pet)
    return f._cap


def _line_widths(content):
    return [(len(Text.from_markup(ln).plain), Text.from_markup(ln).plain)
            for ln in content.split("\n")]


def _assert_fits(content):
    rows = content.split("\n")
    assert len(rows) <= INNER_H, f"{len(rows)} rows > {INNER_H}"
    for w, vis in _line_widths(content):
        assert w <= INNER_W, f"line {w}>{INNER_W} cols: {vis!r}"


def _top_num():
    """A real top-stage Digimon (Super Ultimate) — the widest name/stat strings."""
    _, by = data.load_sprites()
    n = next((k for k, r in by.items()
              if r["stage"] == "Super Ultimate" and not data.is_placeholder(k)), None)
    if n is None:
        pytest.skip("sprite assets not installed")
    return n


def test_normal_pet_fits():
    _assert_fits(_render(Pet.from_num(_top_num())))


def test_worst_case_pet_fits():
    p = Pet.from_num(_top_num())
    p.name = "Wargreymonmonmonmonmon"          # over the 22-cap
    p.age_seconds = 99 * 3600 + 59 * 60        # max-ish age string ('99h59m')
    p.vaccine = p.data_power = p.virus = 999
    p.weight = 999
    p.wins = 999; p.battles = 999
    p.asleep = True; p.sick = True; p.poop = 4
    p.fatigue_length = 100; p.inj_length = 100  # pile on the +tired / +hurt decos
    _assert_fits(_render(p))


def test_dm20_attribute_and_dp_shown():
    """DM20 status shows the pet's ONE attribute + aggregate DP, not three power counters."""
    p = Pet.from_num(_top_num())
    p.attribute = "Vaccine"
    p.vaccine, p.data_power, p.virus = 40, 30, 20
    content = _render(p)
    plain = Text.from_markup(content).plain
    assert "Attrib" in plain and "Vaccine" in plain
    assert "DP      90" in plain                  # dp == vaccine + data + virus
    # the old ●■▲ triple-power row is gone: ■/▲ appeared only there (a Vaccine badge is ●)
    assert "■" not in plain and "▲" not in plain
    _assert_fits(content)


def test_dp_property_is_attribute_sum():
    p = Pet(num=-1, stage="Rookie")
    p.vaccine, p.data_power, p.virus = 11, 22, 33
    assert p.dp == 66


def test_egg_view_fits():
    _assert_fits(_render(Pet(num=-1, stage="Egg")))


def test_grave_view_fits():
    p = Pet.from_num(_top_num())
    p.dead = True
    p.name = "Wargreymonmonmonmonmon"
    _assert_fits(_render(p))


def test_all_status_words_fit():
    """Each possible status word, paired with poop deco, still fits."""
    p = Pet.from_num(_top_num())
    for word in ["ok", "happy", "unhappy", "elderly", "needs cleaning",
                 "sick", "fatigued", "injured", "sleepy", "asleep",
                 "starving", "misbehaving", "did great!"]:
        p.status_word = lambda w=word: w
        p.poop = 4; p.sick = True
        _assert_fits(_render(p))


# ---- the helper directly ---------------------------------------------------

def test_status_line_keeps_all_when_fitting():
    line = _status_line("ok", ["[blue]Zzz[/]", "[red]+sick[/]"])
    assert "Zzz" in line and "+sick" in line
    assert len(Text.from_markup(line).plain) <= INNER_W


def test_status_line_drops_overflow():
    deco = ["[blue]Zzz[/]", "[red]+sick[/]", "[y]~poop x4[/]", "[g]✦Futon[/]"]
    line = _status_line("elderly", deco)
    assert len(Text.from_markup(line).plain) <= INNER_W
    assert "Zzz" in line                         # highest priority kept


def test_status_line_no_deco():
    assert _status_line("happy", []) == "[b]happy[/]   "


# ---- footer hints must fit the panel width (menu clips silently) -----------

def test_footer_literals_fit_width():
    import pathlib
    import re
    from tuipet import menu
    srcdir = pathlib.Path(__file__).resolve().parents[1] / "src" / "tuipet"
    over = []
    for f in sorted(srcdir.glob("*.py")):
        s = f.read_text()
        for m in re.finditer(r'footer\(\s*"([^"]*)"', s):
            txt = m.group(1)
            vis = re.sub(r"\[/?[^\]]*\]", "", txt)        # strip rich markup
            if len(vis) > menu.W:
                over.append((f.name, len(vis), txt))
    assert not over, f"footer hints exceed {menu.W} cols (menu.footer truncates them): {over}"
