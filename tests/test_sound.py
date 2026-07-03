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
        for m in re.finditer(r'snds"?\]?\s*=\s*\{([^}]*)\}', s):   # beat-keyed fx maps
            names.update(re.findall(r'\d+:\s*"([a-zA-Z][a-zA-Z0-9]*)"', m.group(1)))
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
