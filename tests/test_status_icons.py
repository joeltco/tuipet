"""Status-icon audit (2026-07): functions, placements, and the full manifest.

Verified vs SpriteAnim: the condition COLUMN order matches canon's setLocY
exactly (sick 55 / medicine 64 / injury 73 / bandage 83 / vitamin 93 /
fatigue 103, all active shown at once down the right edge); teach rides the
CREATURE (setDynamicComponentLocation), gated lights-on + awake, verbatim;
the 2-frame state blink (_stateNum) maps to tuipet's sf toggle; the emote
bubble (adjustEmotionLabel) and attention '!' zones.

Changed: the 2026-06-26 'for now' hide of st_medicine + st_teach is LIFTED
-- the med badge is the double-dose warning and teach flags a discipline
window that now expires with teeth (v0.2.182).

The MANIFEST (both directions, like the sound audit): every extracted icon
is either referenced by code or allowlisted with its reason below."""
import glob
import re

from tuipet import data
from tuipet.pet import Pet
import tuipet.app as app


# extracted-but-deliberately-unwired, with reasons:
ALLOWED_SILENT = {
    "sun": "time-of-day icon; tuipet's status line uses a text glyph instead",
    "moon": "as sun",
    "call": "DVPet's blinking call light; the attention '!' bubble covers it",
    "depressed": "the Data_Status mood icon; the digicore CONDITION page shows text",
    "flash": "attackHitFlash crop; battle_overlays.json hit_explosion is the source in use",
    "frozen": "DVPet's game-PAUSED indicator, not a cold state (documented in paint)",
    "battle_bag": "superseded by hp_dummies.json (the clean battleBags rows)",
    "train_button": "the mouse mash button; tuipet is keyboard-driven",
    "train_cannon": "duplicate alias of train_green in the generated json",
    "train_cannon_up": "duplicate alias of train_green_up",
}


def _referenced_keys():
    keys = set(data.load_effects())
    src = glob.glob("src/tuipet/*.py")
    text = "".join(open(f).read() for f in src)
    refs = set()
    for k in keys:
        if f'"{k}"' in text or f"'{k}'" in text:
            refs.add(k)
    # pattern-built families
    if '"field_" + ' in text or 'E.get("field_"' in text:
        refs |= {k for k in keys if k.startswith("field_")}
    if 'poop_s%d' in text or '"poop_s' in text:
        refs |= {k for k in keys if k.startswith("poop_s")}
    return keys, refs


def test_every_icon_is_referenced_or_allowlisted():
    keys, refs = _referenced_keys()
    dark = sorted(keys - refs - set(ALLOWED_SILENT))
    assert not dark, f"extracted icons no code draws (and no reason on file): {dark}"


def test_allowlist_carries_no_stale_entries():
    keys, refs = _referenced_keys()
    stale = sorted(k for k in ALLOWED_SILENT if k in refs or k not in keys)
    assert not stale, f"allowlisted icons that ARE now referenced (or gone): {stale}"


def _pts(pet, **kw):
    return app._effect_overlay(pet, 3, app.SCREEN_COLS, app.SCREEN_ROWS * 2, tick=3, **kw)


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_medicine_badge_is_back_and_warns():
    calm = _pet()
    dosed = _pet(med_lapse=30.0)
    assert len(_pts(dosed)) > len(_pts(calm))    # the double-dose warning shows


def test_teach_bubble_is_back_with_canon_gates():
    good = _pet(praise_flag=True)
    assert len(_pts(good)) > len(_pts(_pet()))   # discipline awaited: the bulb shows
    dark = _pet(praise_flag=True, lights=False)
    lit = _pet(praise_flag=True)
    assert len(_pts(dark)) < len(_pts(lit))      # canon: lights-off hides teach


def test_condition_column_shows_all_active_at_once():
    p = _pet(sick=True, sick_length=999.0, med_lapse=30.0)
    p.inj_length = 999.0
    n_all = len(_pts(p))
    q = _pet(sick=True, sick_length=999.0)
    assert n_all > len(_pts(q))                  # a fixed column, not a cycling slot
