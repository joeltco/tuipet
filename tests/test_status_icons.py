"""Status-icon manifest + the Bandai-grammar placement rules (2026-07-11).

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

from tuipet import data
from tuipet.pet import Pet
import tuipet.app as app


# extracted-but-deliberately-unwired, with reasons:
ALLOWED_SILENT = {
    "sun": "time-of-day icon; tuipet's status line uses a text glyph instead",
    "moon": "as sun",
    "call": "DVPet's blinking call light; the msg-box alarm is tuipet's call chrome",
    # Bandai grammar 2026-07-11: the matrix is a stage, not a dashboard --
    # badges live on the status side (HUD deco / digicore / msg-box alarm)
    "attention": "the care-call is chrome: the msg-box alarm + beep carry it",
    "st_teach": "discipline window -> the +praise!/+scold! HUD badges",
    "st_medicine": "badge -> the +med HUD deco",
    "st_injury": "badge -> the +hurt HUD deco",
    "st_bandage": "badge -> the +bnd HUD deco",
    "st_vitamin": "badge -> the +vit HUD deco",
    "st_fatigue": "badge -> the +tired HUD deco",
    "train_hit": "the punch drill's Hit!! pop: 17px of art with no lawful berth"
                 " in the window beside a 16px bag and mon (LAW 2026-07-11);"
                 " the bag rock + lunge + flash carry the hit",
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
    # theme.py never draws effect icons; its palette KEYS ("flash", 2026-07-05)
    # collide with icon names and read as false references
    src = [f for f in glob.glob("src/tuipet/*.py") if not f.endswith("theme.py")]
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


def test_badges_are_hud_only():
    """Bandai grammar: medicine/teach/etc are BADGES -- zero LCD pixels; the
    HUD deco carries them (+med / +praise! / +scold!)."""
    assert _pts(_pet(med_lapse=30.0)) == []
    assert _pts(_pet(praise_flag=True)) == []
    import inspect
    src = inspect.getsource(app.Stats.paint)
    assert "+med" in src and "+praise!" in src and "+scold!" in src


def test_only_the_skull_joins_the_scene():
    """Of the six conditions only sickness is a scene actor (the real device
    stands a skull beside the pet); the others add nothing to the LCD."""
    p = _pet(sick=True, sick_length=999.0, med_lapse=30.0)
    p.inj_length = 999.0
    q = _pet(sick=True, sick_length=999.0)
    assert _pts(p) == _pts(q)                    # med/injury change nothing on-LCD
    assert _pts(q)                               # ...but the skull is up
    assert all(x >= 28 for x, _ in _pts(q))


def test_nap_wears_its_own_zzz_glyph():
    """Sleep-anim audit 2026-07-05: DVPet getLightsSprites picks napLights vs
    sleepLights -- a nap's indicator differs from the night's.  (Canon's
    nap-deepening flash keys napToSleepPercent; tuipet naps never convert, so
    only the static variant exists.)"""
    E = data.load_effects()
    assert len(E.get("zzz_nap", [])) == 2 and len(E["zzz"]) == 2
    assert E["zzz_nap"] != E["zzz"]                  # genuinely different art
    night = _pet(asleep=True, nap=False, anim="sleep")
    nap = _pet(asleep=True, nap=True, anim="sleep")
    pn = {(x, y) for x, y in _pts(night)}
    pp = {(x, y) for x, y in _pts(nap)}
    assert pn != pp                                  # the glyphs render differently
    # and the dark-room corner Zzz swaps too
    dark_night = _pet(asleep=True, nap=False, lights=False, anim="sleep")
    dark_nap = _pet(asleep=True, nap=True, lights=False, anim="sleep")
    assert {(x, y) for x, y in _pts(dark_night)} != {(x, y) for x, y in _pts(dark_nap)}
