"""App plumbing (tier-3 split, 2026-07-17): platform detection, the
sound-preference file, the lobby URI, and the launch preflight.  Nothing
here touches the running game."""
from __future__ import annotations

import os
import platform as _pf  # noqa: F401
import sys  # noqa: F401

from . import data  # noqa: F401
from . import persistence

MIN_COLS, MIN_ROWS = 77, 24     # the fixed layout: #left 44 + #stats 30 + chrome


def host_platform():
    """The platform name for bug reports (hostinfo owns the detection so the
    sound backend and the bug feed can never disagree about the host)."""
    from . import hostinfo
    return hostinfo.host_platform()


def _sound_path():
    return os.path.join(persistence.SAVE_DIR, "sound.txt")


def _load_sound():
    try:
        return open(_sound_path(), encoding="utf-8").read().strip() != "off"
    except OSError:
        return True


def _save_sound(on):
    try:
        os.makedirs(persistence.SAVE_DIR, exist_ok=True)
        with open(_sound_path(), "w", encoding="utf-8") as fh:
            fh.write("on" if on else "off")
    except OSError:
        pass


def _lobby_uri():
    return os.environ.get("TUIPET_LOBBY_URL", "wss://ff3mmo.com/tuipet/")  # live lobby (TLS); override for local dev


def warm_data():
    """Load every bundled data table NOW, at launch (bug report 2026-10-14).
    The self-updater installs the next release over the package files while
    this one keeps running; anything this process reads lazily afterwards
    comes from the NEW release -- 0.5.350 parsed 0.6's evolution chart and
    crashed on a rule it had never heard of.  Each loader is lru-cached, so
    one call here pins this build's own data for the whole session."""
    import inspect
    from . import (adventure, data_core, data_meta, data_shop, data_world,
                   egg, lines)
    # sync audit 2026-10-14: this lazy table uses a module cache, not lru_cache.
    data_world._load_attacks()
    for mod in (data_core, data_world, data_meta, data_shop, lines, egg, adventure):
        for name, fn in list(vars(mod).items()):
            if not (name.startswith("load_") or name in ("_real_eggs", "_load_maps")):
                continue
            if not hasattr(fn, "cache_info"):
                continue
            try:
                if any(p.default is inspect.Parameter.empty
                       for p in inspect.signature(fn).parameters.values()):
                    continue
                fn()
            except Exception:
                pass              # a broken table surfaces where it's used


def _preflight():
    """Fail loud and in plain words BEFORE the UI takes the terminal over
    (sweep 2026-07-14): damaged assets exit with the fix; a cramped window or
    a non-UTF-8 locale get a readable warning, then the game runs anyway --
    a clipped game beats a locked-out player."""
    try:
        # EVERY required file, not just the two atlases this used to open:
        # eddy's 0.5.345 boot passed this gate with tournies.csv gone and
        # crashed hours later on the tournament key (2026-08-22).
        data.verify_assets()
        data.load_sprites()          # ...and these two must also PARSE
        data.load_orbs()
    except data.AssetsError as e:
        print(e)
        raise SystemExit(1)
    import shutil
    import time as _t
    warn = []
    cols, rows = shutil.get_terminal_size()
    if cols < MIN_COLS or rows < MIN_ROWS:
        warn.append(f"⚠ tuipet lays out for {MIN_COLS}×{MIN_ROWS}; this terminal is "
                    f"{cols}×{rows} — expect clipping.\n  (Enlarge the window, shrink "
                    f"the font, or rotate the phone.)")
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    if enc and "utf" not in enc:
        warn.append(f"⚠ tuipet draws with Unicode but this terminal reports '{enc}'.\n"
                    f"  If the art looks wrong:  export LANG=C.UTF-8")
    if warn:
        print("\n".join(warn))
        _t.sleep(2.5)


