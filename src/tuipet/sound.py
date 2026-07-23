"""Optional sound backend: play DVPet's WAV sound effects when an audio player
is available, otherwise stay silent so the app can fall back to the terminal
bell.

Detection avoids playing on the wrong machine: inside an SSH session we never
spawn a desktop player (it would play on the server, not at your terminal);
Termux's termux-media-player always plays on the phone, so it's preferred.
"""
from __future__ import annotations
import array
import os
import shutil
import subprocess  # nosec B404 - players run from a fixed allowlist, no shell, no user input
import sys
import wave

from . import hostinfo

_DIR = os.path.join(os.path.dirname(__file__), "data", "sounds")

# --- volume -------------------------------------------------------------------
# The DVPet WAVs ship at full scale and are PIERCING on a real speaker (Joel
# 2026-07-15: "chop that sound volume in half").  None of the allowlisted
# players share a volume flag (termux-media-player and aplay have none at
# all), so volume is applied to the SAMPLES: each level keeps a lazily-built
# cache of pre-attenuated copies that any player can just play.
#
# The slider is PERCEPTUAL, not raw amplitude (v1 mapped 50% to 0.5x, a mere
# -6dB -- "still blairing", Joel 2026-07-15): the baseline chop is baked into
# the TOP of the scale, so 100% is the default and already plays at half
# amplitude, and each step down squares away real decibels (50% = 1/8
# amplitude, ~-18dB; 10% = a whisper).  Range 10..100 in steps of 10 -- there
# is no 0, the sound switch is the mute.
# volume.txt + the scaled-wav cache ride the LIVE save dir, resolved at
# call time (the injectable-paths law; shape sweep 2026-07-19: this was
# theme.txt's twin -- a hardcoded ~/.local that silently dropped the
# volume choice on iOS and escaped the test sandbox.  erase_all sweeps
# volume.txt + sndcache/ now; it never had either).
def _state_dir():
    from . import persistence
    return persistence.SAVE_DIR


def _vol_conf():
    return os.path.join(_state_dir(), "volume.txt")


def _cache_dir():
    return os.path.join(_state_dir(), "sndcache")
DEFAULT_VOLUME = 50   # Joel 2026-07-23: "audio volume starts at 50% by
#                       default" -- a saved volume.txt still wins; only a
#                       fresh install (or a wiped save dir) lands here


def _amp(v):
    """Slider percent -> amplitude factor: 0.5 * (v/100)^2."""
    return 0.5 * (v / 100.0) ** 2


def _load_volume():
    try:
        return max(10, min(100, int(open(_vol_conf()).read().strip())))
    except (OSError, ValueError):
        return DEFAULT_VOLUME


def volume():
    return _volume


def set_volume(v):
    """Clamp, remember and persist the playback volume (percent)."""
    global _volume
    _volume = max(10, min(100, int(v)))
    try:
        os.makedirs(_state_dir(), exist_ok=True)
        with open(_vol_conf(), "w") as fh:
            fh.write(str(_volume))
    except OSError:
        pass                       # the level still holds for this session
    return _volume


def _scaled(f, name):
    """The pre-attenuated copy of `f` for the current volume (built lazily,
    one cache dir per level, atomic rename so a half-written wav is never
    served).  Any failure falls back to the ORIGINAL file: a full-strength
    chirp beats silence, and a state dir that can't hold a 40KB wav is
    already failing loudly everywhere else (saves, theme).  Even 100% is a
    scaled copy -- the piercing raw wavs are never played.  The q-prefix
    versions the CURVE: the retired v-dirs held v1's linear scaling and must
    not be served under the new mapping."""
    dst = os.path.join(_cache_dir(), f"q{_volume}", name + ".wav")
    if os.path.exists(dst):
        return dst
    try:
        with wave.open(f) as w:
            params = w.getparams()
            frames = w.readframes(params.nframes)
        if params.sampwidth != 2:
            return f               # every shipped wav is 16-bit PCM mono
        a = array.array("h")
        a.frombytes(frames)
        if sys.byteorder == "big":
            a.byteswap()
        k = _amp(_volume)          # attenuation only (k <= 0.5): can never clip
        for i in range(len(a)):
            a[i] = int(a[i] * k)
        if sys.byteorder == "big":
            a.byteswap()
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".part"
        with wave.open(tmp, "wb") as w:
            w.setparams(params)
            w.writeframes(a.tobytes())
        os.replace(tmp, dst)
        return dst
    except Exception:
        return f


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
_volume = _load_volume()


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
        subprocess.Popen(_PLAYER + [_scaled(f, name)], stdout=subprocess.DEVNULL,   # nosec B603 - fixed player cmd, no shell, path is our own data file
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
