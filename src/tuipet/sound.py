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
import threading
import time
from collections import deque
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
        return max(10, min(100, int(open(_vol_conf(), encoding="utf-8").read().strip())))
    except (OSError, ValueError):
        return DEFAULT_VOLUME


def volume():
    return _volume


def set_volume(v):
    """Clamp, remember and persist the playback volume (percent)."""
    global _volume
    stop()
    _volume = max(10, min(100, int(v)))
    try:
        os.makedirs(_state_dir(), exist_ok=True)
        with open(_vol_conf(), "w", encoding="utf-8") as fh:
            fh.write(str(_volume))
    except OSError:
        pass                       # the level still holds for this session
    return _volume


def _scaled(f, name):
    """Cache the selected attenuation; cache failure must never play raw audio."""
    level = _volume  # A slider change during scaling must not poison another level's cache.
    dst = os.path.join(_cache_dir(), f"q{level}", name + ".wav")
    if os.path.exists(dst):
        return dst
    try:
        with wave.open(f) as w:
            params = w.getparams()
            frames = w.readframes(params.nframes)
        if params.sampwidth != 2:
            return None            # unsupported samples must not bypass volume
        a = array.array("h")
        a.frombytes(frames)
        if sys.byteorder == "big":
            a.byteswap()
        k = _amp(level)          # attenuation only (k <= 0.5): can never clip
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
        return None


def _find_player():
    # iOS (a-Shell, our official iPhone/iPad target) sandboxes audio and gives
    # Python no way to spawn a player -- subprocess/fork is not available.  Say
    # so up front rather than detecting a phantom player we could never run:
    # every beep would then raise, get swallowed, and (for the routine
    # bell=False sounds) leave the pet SILENT with Options still claiming a
    # backend.  No player on iOS -> the terminal bell carries the milestones,
    # and Options honestly reads "bell only".  (Sound audit 2026-07-13.)
    from .web import is_browser
    if is_browser() or hostinfo.is_ios():
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


class _Playback:
    """One audio channel, with bounded pending work and interruptible playback.

    Scaling, bridge probes, process waits and stop commands run off the UI thread.
    New cues interrupt long samples rather than mixing or building a stale backlog.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.pending = deque(maxlen=8)
        self.recent = {}
        self.generation = 0
        self.failure = False
        self.worker = None

    def submit(self, name, fallback):
        with self.lock:
            now = time.monotonic()
            gap = 0.08 if name in ("scroll", "menu", "select") else 0.25
            if now - self.recent.get(name, -1000) < gap:
                return True
            self.recent[name] = now
            self.pending.append((name, fallback, self.generation, now))
            if self.worker is None or not self.worker.is_alive():
                self.worker = threading.Thread(target=self.run, daemon=True)
                self.worker.start()
        return True

    def stop(self):
        with self.lock:
            self.generation += 1
            self.pending.clear()
            self.recent.clear()
            self.failure = False

    def interrupted(self, generation):
        with self.lock:
            return generation != self.generation or bool(self.pending)

    def run(self):
        global _PLAYER, _bridge_checked
        while True:
            with self.lock:
                if not self.pending:
                    self.worker = None
                    return
                name, fallback, generation, queued = self.pending.popleft()
            if time.monotonic() - queued > 0.75:
                continue
            proc = None
            player = _PLAYER
            try:
                if not player:
                    raise OSError("no audio backend")
                if not _bridge_checked and player[0] == "termux-media-player":
                    _bridge_checked = True
                    if not _termux_bridge_live():
                        raise OSError("Termux bridge unavailable")
                path = _scaled(os.path.join(_DIR, name + ".wav"), name)
                if not path:
                    # A broken cache is not evidence of a broken player.
                    with self.lock:
                        self.failure |= fallback and generation == self.generation
                    continue
                if generation != self.generation:
                    continue
                with wave.open(path) as wav:
                    duration = wav.getnframes() / wav.getframerate()
                proc = subprocess.Popen(player + [path], stdout=subprocess.DEVNULL,  # nosec B603 - fixed allowlist, no shell
                                        stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
                deadline = time.monotonic() + duration + 1
                remote = player[0] == "termux-media-player"
                while True:
                    rc = proc.poll()
                    if rc is not None and rc != 0:
                        raise OSError("audio player failed")
                    if self.interrupted(generation):
                        break
                    if rc is not None and not remote:
                        break
                    if time.monotonic() >= deadline:
                        if rc is None:
                            raise OSError("audio player stalled")
                        break
                    time.sleep(0.02)
                if remote:
                    # The bridge process does not own Android's playback lifetime.
                    try:
                        subprocess.run([player[0], "stop"], timeout=1,  # nosec B603 - fixed command
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       stdin=subprocess.DEVNULL)
                    except subprocess.TimeoutExpired:
                        pass  # A slow bridge is not proof that Android audio is absent.
            except Exception:
                _PLAYER = None
                with self.lock:
                    self.failure |= fallback and generation == self.generation
            finally:
                if proc is not None:
                    try:
                        if proc.poll() is None:
                            proc.terminate()
                        proc.wait(timeout=0.2)
                    except Exception:
                        try:
                            proc.kill()
                            proc.wait(timeout=0.2)
                        except Exception:
                            pass


_playback = _Playback()


def stop():
    """Cancel active/pending audio without waiting on an OS player."""
    _playback.stop()


def failed():
    """Consume an asynchronous milestone failure for the UI's bell fallback."""
    with _playback.lock:
        failure, _playback.failure = _playback.failure, False
        return failure


def play(name, fallback=False):
    """Queue optional audio without doing audio I/O on the UI thread."""
    if not _PLAYER or not isinstance(name, str) or not name.isalnum():
        return False
    if not os.path.exists(os.path.join(_DIR, name + ".wav")):
        return False
    try:
        return _playback.submit(name, fallback)
    except Exception:
        return False
