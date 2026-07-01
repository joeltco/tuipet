"""The egg selector is a free version-starter picker (DM20): every egg is available,
ENTER returns the centred egg index, ESC returns None. No unlock/password gating."""
from rich.markup import render as render_markup

from tuipet import egg as egg_mod
from tuipet import theme
from tuipet.eggselectscreen import EggSelectPanel


def test_every_egg_is_selectable():
    p = EggSelectPanel()
    assert p.n == egg_mod.count() >= 5
    assert p.i == 0


def test_enter_returns_centred_index_esc_cancels():
    p = EggSelectPanel()
    p.key("right")
    assert p.i == 1
    assert p.key("enter") == ("done", 1)          # hatches egg index 1
    assert p.key("escape") == ("done", None)      # back out, keep current pet


def test_no_unlock_or_password_surface():
    p = EggSelectPanel()
    # the stripped DVPet machinery must be gone
    for attr in ("entering", "buf", "states", "unlocked", "locked", "hint",
                 "captures_text", "_key_code", "_refresh"):
        assert not hasattr(p, attr), f"{attr} is a stripped DVPet unlock artifact"


def test_carousel_renders_valid_markup_every_theme():
    for th in theme._ORDER:
        theme.apply(th)
        p = EggSelectPanel()
        p.key("right"); p.anim()
        out = p.text()                            # rich Text; must not raise
        render_markup(out.markup)
