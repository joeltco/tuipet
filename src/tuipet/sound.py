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
import subprocess

_DIR = os.path.join(os.path.dirname(__file__), "data", "sounds")


def _find_player():
    if shutil.which("termux-media-player"):
        return ["termux-media-player", "play"]      # Termux -> plays on the phone
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY") or os.environ.get("SSH_CLIENT"):
        return None                                  # SSH session: don't play on the server
    for cmd in (["paplay"], ["aplay", "-q"], ["afplay"],
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"], ["play", "-q"]):
        if shutil.which(cmd[0]):
            return cmd
    return None


_PLAYER = _find_player()


def available():
    return _PLAYER is not None


def play(name):
    """Play data/sounds/<name>.wav non-blocking; True if a player was dispatched."""
    if not _PLAYER:
        return False
    f = os.path.join(_DIR, name + ".wav")
    if not os.path.exists(f):
        return False
    try:
        subprocess.Popen(_PLAYER + [f], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        return True
    except Exception:
        return False
