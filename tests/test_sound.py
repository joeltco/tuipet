"""Sound system audit (2026-07): player detection, failure modes, and the
name→wav contract.  sound.play must NEVER raise (a beep is not worth a crash),
and every sound name the code asks for by literal must ship a .wav — the
missing-asset failure mode is silence, which no one reports."""
import glob
import os
import re

from tuipet import sound


# ---- player detection --------------------------------------------------------

def test_termux_player_wins(monkeypatch):
    monkeypatch.setattr(sound.shutil, "which",
                        lambda c: "/usr/bin/x" if c == "termux-media-player" else None)
    assert sound._find_player() == ["termux-media-player", "play"]


def test_ssh_session_stays_silent(monkeypatch):
    monkeypatch.setattr(sound.shutil, "which",
                        lambda c: None if c == "termux-media-player" else "/usr/bin/x")
    monkeypatch.setenv("SSH_CONNECTION", "1.2.3.4 5 6.7.8.9 22")
    assert sound._find_player() is None          # never play on the SERVER


def test_desktop_player_order(monkeypatch):
    monkeypatch.delenv("SSH_CONNECTION", raising=False)
    monkeypatch.delenv("SSH_TTY", raising=False)
    monkeypatch.delenv("SSH_CLIENT", raising=False)
    monkeypatch.setattr(sound.shutil, "which",
                        lambda c: "/usr/bin/x" if c in ("aplay", "ffplay") else None)
    assert sound._find_player() == ["aplay", "-q"]   # allowlist order holds
    monkeypatch.setattr(sound.shutil, "which", lambda c: None)
    assert sound._find_player() is None


# ---- play() failure modes ------------------------------------------------------

def test_play_without_a_player_is_a_quiet_false(monkeypatch):
    monkeypatch.setattr(sound, "_PLAYER", None)
    assert sound.play("eat") is False
    assert sound.available() is False


def test_play_missing_wav_is_a_quiet_false(monkeypatch):
    monkeypatch.setattr(sound, "_PLAYER", ["true"])
    assert sound.play("no-such-sound") is False


def test_play_broken_player_never_raises(monkeypatch):
    monkeypatch.setattr(sound, "_PLAYER", ["/no/such/binary"])
    assert sound.play("eat") is False            # Popen's FileNotFoundError is swallowed


def test_play_dispatches_when_everything_exists(monkeypatch):
    monkeypatch.setattr(sound, "_PLAYER", ["true"])   # /usr/bin/true: exits instantly
    assert sound.play("eat") is True


# ---- the name -> wav contract ---------------------------------------------------

def _referenced_names():
    """Every sound name the code asks for by string literal."""
    names = set()
    src = os.path.join(os.path.dirname(sound.__file__))
    for f in glob.glob(os.path.join(src, "*.py")):
        s = open(f).read()
        names.update(re.findall(r'\bbeep\(\s*"([a-zA-Z][a-zA-Z0-9]*)"', s))
        names.update(re.findall(r'sound\.play\(\s*"([a-zA-Z][a-zA-Z0-9]*)"', s))
        names.update(re.findall(r'\bsfx\s*=\s*"([a-zA-Z][a-zA-Z0-9]*)"', s))
        for line in s.splitlines():                       # conditional sfx picks
            if re.search(r"\bsfx\s*=", line):
                for a, b in re.findall(r'"(\w+)"\s+if\s+.+?\s+else\s+"(\w+)"', line):
                    names.update((a, b))
        for m in re.finditer(r'(?:bite_)?snds"?\]?\s*=\s*\{([^}]*)\}', s):   # beat-keyed fx maps
            # keys may be computed (bite_snds uses pow-scaled beats): match VALUES
            names.update(re.findall(r'[^,{]+?:\s*"([a-zA-Z][a-zA-Z0-9]*)"', m.group(1)))
        names.update(re.findall(r'"(thunder\d?)"', s))    # the storm crack picks
        names.update(re.findall(r'"((?:small|large)Poop|poop)"', s))   # size-keyed picks
    return names


def test_every_referenced_sound_ships_a_wav():
    have = {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(sound._DIR, "*.wav"))}
    missing = sorted(_referenced_names() - have)
    assert not missing, f"code asks for sounds with no wav behind them: {missing}"


def test_every_shipped_wav_is_referenced():
    """The inverse: an unreferenced wav is a wired-nowhere asset (this audit found
    startBattle/mischief/thunder*/rain/wind exactly this way).  rain + wind are
    DVPet's precip LOOPS — a fire-and-forget player can't stop a loop, so they
    stay shipped-but-silent by design."""
    have = {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(sound._DIR, "*.wav"))}
    allowed_silent = {"rain", "wind"}
    dead = sorted(have - _referenced_names() - allowed_silent)
    assert not dead, f"shipped wavs no code path plays: {dead}"


# ---- volume (2026-07-15: full-scale chirps were piercing) -----------------------

def _peak(path):
    import array as _array
    import wave as _wave
    with _wave.open(path) as w:
        frames = w.readframes(w.getnframes())
    a = _array.array("h")
    a.frombytes(frames)
    return max(abs(s) for s in a)


def test_default_100_percent_is_the_baked_in_chop():
    """The TOP of the slider is already the halved wav — the piercing raw
    files are never what plays, and the default leaves the whole scale free
    to go DOWN ("should of started at 100%", Joel 2026-07-15)."""
    src = os.path.join(sound._DIR, "confirm.wav")
    assert sound.DEFAULT_VOLUME == 100
    sound.set_volume(100)
    out = sound._scaled(src, "confirm")
    assert out != src and os.path.exists(out)
    assert _peak(out) == _peak(src) // 2


def test_the_slider_is_perceptual_not_linear():
    """v1 mapped 50% to 0.5x amplitude — a mere -6dB, "still blairing".  The
    squared curve makes 50% a genuine 1/8 amplitude (~-18dB)."""
    src = os.path.join(sound._DIR, "confirm.wav")
    sound.set_volume(50)
    assert _peak(sound._scaled(src, "confirm")) == _peak(src) // 8
    sound.set_volume(10)                        # the floor is a whisper
    assert _peak(sound._scaled(src, "confirm")) <= _peak(src) // 190


def test_scaled_cache_is_reused_per_level(monkeypatch):
    src = os.path.join(sound._DIR, "confirm.wav")
    sound.set_volume(30)
    first = sound._scaled(src, "confirm")
    stamp = os.path.getmtime(first)
    assert sound._scaled(src, "confirm") == first
    assert os.path.getmtime(first) == stamp          # second call: pure lookup
    sound.set_volume(70)
    assert sound._scaled(src, "confirm") != first    # each level its own copy


def test_play_dispatches_the_scaled_copy(monkeypatch):
    """play() hands the PLAYER the attenuated file — the whole point."""
    sent = {}
    monkeypatch.setattr(sound, "_PLAYER", ["true"])
    monkeypatch.setattr(sound.subprocess, "Popen",
                        lambda argv, **kw: sent.setdefault("argv", argv))
    sound.set_volume(50)
    assert sound.play("confirm") is True
    assert sound._CACHE in sent["argv"][-1]


def test_scaling_failure_falls_back_to_the_original(monkeypatch):
    """A cache dir that cannot be written must not silence the game: the
    original full-strength wav still plays (loud beats mute)."""
    src = os.path.join(sound._DIR, "confirm.wav")
    sound.set_volume(50)
    monkeypatch.setattr(sound.os, "makedirs",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("ro")))
    assert sound._scaled(src, "confirm") is src


def test_volume_clamps_and_persists():
    assert sound.set_volume(7) == 10        # floor: the switch is the mute
    assert sound.set_volume(500) == 100
    sound.set_volume(40)
    assert sound._load_volume() == 40       # survives a relaunch
