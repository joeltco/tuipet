"""Optional sound backend: play DVPet's WAV sound effects when an audio player
is available, otherwise stay silent so the app can fall back to the terminal
bell.

Detection avoids playing on the wrong machine: inside an SSH session we never
spawn a desktop player (it would play on the server, not at your terminal);
Termux's termux-media-player always plays on the phone, so it's preferred.
"""
from __future__ import annotations
import os
import shutil
import subprocess  # nosec B404 - players run from a fixed allowlist, no shell, no user input

from . import hostinfo

_DIR = os.path.join(os.path.dirname(__file__), "data", "sounds")


def _find_player():
    # iOS (a-Shell, our official iPhone/iPad target) sandboxes audio and gives
    # Python no way to spawn a player -- subprocess/fork is not available.  Say
    # so up front rather than detecting a phantom player we could never run:
    # every beep would then raise, get swallowed, and (for the routine
    # bell=False sounds) leave the pet SILENT with Options still claiming a
    # backend.  No player on iOS -> the terminal bell carries the milestones,
    # and Options honestly reads "bell only".  (Sound audit 2026-07-13.)
    if hostinfo.is_ios():
        return None
    if shutil.which("termux-media-player"):
        return ["termux-media-player", "play"]      # Termux -> plays on the phone
    if hostinfo.is_ssh():
        return None                                  # SSH session: don't play on the server
    for cmd in (["paplay"], ["aplay", "-q"], ["afplay"],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"], ["play", "-q"]):
        if shutil.which(cmd[0]):
            return cmd
    return None


_PLAYER = _find_player()


def available():
    return _PLAYER is not None


def backend():
    """The detected player's command name ('' when none — the app falls back
    to the terminal bell). Surfaced on the OPTIONS sound row so a silent
    install self-explains (the Termux no-player mystery)."""
    return _PLAYER[0] if _PLAYER else ""


_bridge_checked = False


def _termux_bridge_live():
    """Is the Termux:API *app* actually installed behind the bridge?

    `pkg install termux-api` gives you the termux-media-player BINARY, but it
    is only a bridge: without the Termux:API app (F-Droid/Play) it runs, spawns
    cleanly, and does NOTHING.  Popen therefore SUCCEEDS, play() reported True,
    app.beep() returned early -- and the bell never rang.  The game went
    totally silent while Options read "on . termux": no error, no exception,
    nothing to debug.  (The 'Termux no-player mystery'; Joel spotted the cause
    2026-07-13.)  So ask the bridge once, and believe only a DEFINITE refusal:
    a non-zero exit retires the player, a timeout does not (a slow phone must
    not lose its sound).
    """
    try:
        r = subprocess.run(["termux-media-player", "info"],   # nosec B603 B607 - fixed argv, no shell, no user input
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           stdin=subprocess.DEVNULL, timeout=4)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return True                     # slow, not absent: keep the player
    except Exception:
        return False


def play(name):
    """Play data/sounds/<name>.wav non-blocking; True if a player was dispatched."""
    global _PLAYER, _bridge_checked
    if not _PLAYER:
        return False
    if not _bridge_checked and _PLAYER[0] == "termux-media-player":
        # probed LAZILY (never at import): startup must not pay for it, and a
        # player that turns out to be a dead bridge retires like any other
        _bridge_checked = True
        if not _termux_bridge_live():
            _PLAYER = None
            return False
    f = os.path.join(_DIR, name + ".wav")
    if not os.path.exists(f):
        return False
    try:
        subprocess.Popen(_PLAYER + [f], stdout=subprocess.DEVNULL,   # nosec B603 - fixed player cmd, no shell, path is our own data file
                         stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        return True
    except Exception:
        # A player we cannot actually SPAWN is no player at all (a locked-down
        # host: no fork, a killed binary, an exhausted process table).  Retire
        # it for good instead of raising on every single beep -- the caller's
        # bell fallback then carries the sound, and Options stops advertising a
        # backend that does nothing (sound audit 2026-07-13).
        _PLAYER = None
        return False
