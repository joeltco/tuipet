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
        return open(_sound_path()).read().strip() != "off"
    except OSError:
        return True


def _save_sound(on):
    try:
        os.makedirs(persistence.SAVE_DIR, exist_ok=True)
        with open(_sound_path(), "w") as fh:
            fh.write("on" if on else "off")
    except OSError:
        pass


def _lobby_uri():
    return os.environ.get("TUIPET_LOBBY_URL", "wss://ff3mmo.com/tuipet/")  # live lobby (TLS); override for local dev


def _preflight():
    """Fail loud and in plain words BEFORE the UI takes the terminal over
    (sweep 2026-07-14): damaged assets exit with the fix; a cramped window or
    a non-UTF-8 locale get a readable warning, then the game runs anyway --
    a clipped game beats a locked-out player."""
    try:
        data.load_sprites()
        data.load_orbs()
    except data.AssetsError as e:
        print(e)
        raise SystemExit(1)
    import shutil
    import sys
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


