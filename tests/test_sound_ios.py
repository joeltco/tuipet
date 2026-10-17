"""Sound on iOS (a-Shell, the official iPhone/iPad target) — audit 2026-07-13.

iOS sandboxes audio and gives Python no way to spawn a player (no fork). Two
traps this pins:
  * we must not DETECT a player we could never run — every beep would raise,
    get swallowed, leave routine (bell=False) sounds silent, and Options would
    still advertise a backend;
  * a player that turns out unspawnable anywhere must RETIRE, not raise on
    every single beep.
"""
import importlib
from unittest.mock import Mock

from tuipet import hostinfo, sound


def _as_ios(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("platform.machine", lambda: "iPhone15,2")
    importlib.reload(hostinfo)


def test_ios_is_detected_and_named(monkeypatch):
    _as_ios(monkeypatch)
    try:
        assert hostinfo.is_ios()
        assert hostinfo.host_platform() == "iOS"
    finally:
        importlib.reload(hostinfo)


def test_ios_never_claims_an_audio_player(monkeypatch):
    _as_ios(monkeypatch)
    try:
        importlib.reload(sound)
        assert sound._find_player() is None, "iOS cannot spawn a player"
        assert not sound.available()
        assert sound.backend() == ""          # Options -> "bell (iOS)", not a lie
        assert sound.play("happy") is False   # ...so the caller rings the bell
    finally:
        importlib.reload(hostinfo)
        importlib.reload(sound)


def test_an_unspawnable_player_retires_itself(monkeypatch):
    """No fork / dead binary / exhausted process table: fail ONCE, then fall
    back to the bell for good."""
    importlib.reload(sound)
    try:
        sound._PLAYER = ["afplay"]
        calls = []

        def boom(*a, **k):
            calls.append(1)
            raise OSError("posix_spawn not permitted")

        monkeypatch.setattr(sound.subprocess, "Popen", boom)
        assert sound.available()
        assert sound.play("happy", fallback=True)
        sound._playback.worker.join(2) if sound._playback.worker else None
        assert [sound.play("happy") for _ in range(3)] == [False, False, False]
        assert sound.failed()
        assert len(calls) == 1, "it must retire the player, not retry every beep"
        assert not sound.available()
    finally:
        importlib.reload(sound)


def test_the_bell_still_carries_milestones_without_a_player(monkeypatch):
    """app.beep falls through to the terminal bell when play() declines --
    that is what an iOS player actually hears."""
    import tuipet.app as appmod
    app = appmod.TuiPetApp.__new__(appmod.TuiPetApp)
    app.sound = True
    rung = []
    app.bell = lambda: rung.append(1)
    monkeypatch.setattr(appmod.sound, "play", lambda name, **kw: False)
    appmod.TuiPetApp.beep(app, "hatch")            # a milestone
    assert rung == [1], "a milestone must ring the bell when there is no player"
    appmod.TuiPetApp.beep(app, "eat", bell=False)  # a routine sound stays quiet
    assert rung == [1]


# ---- Termux: the bridge without the app (Joel 2026-07-13) --------------------

def _termux(monkeypatch, rc=0, exc=None):
    """A Termux host whose termux-media-player bridge answers with `rc`."""
    importlib.reload(sound)
    sound._PLAYER = ["termux-media-player", "play"]
    sound._bridge_checked = False
    spawned = []
    proc = Mock()
    proc.poll.return_value = 0
    def spawn(*a, **k):
        spawned.append(1)
        return proc
    monkeypatch.setattr(sound.subprocess, "Popen", spawn)

    class _R:
        returncode = rc

    def _run(*a, **k):
        if exc:
            raise exc
        return _R()

    monkeypatch.setattr(sound.subprocess, "run", _run)
    return spawned


def _finish_bridge():
    worker = sound._playback.worker
    if worker:
        worker.join(6)
        assert not worker.is_alive()


def test_termux_bridge_without_the_app_falls_back_to_the_bell(monkeypatch):
    spawned = _termux(monkeypatch, rc=1)
    assert sound.play("hatch", fallback=True)
    _finish_bridge()
    assert sound.failed()
    assert not spawned
    assert not sound.available()
    assert not sound.play("hatch")


def test_a_working_termux_setup_still_plays(monkeypatch):
    spawned = _termux(monkeypatch, rc=0)
    assert sound.play("hatch")
    _finish_bridge()
    assert spawned == [1]
    assert sound.backend() == "termux-media-player"


def test_a_slow_phone_keeps_its_sound(monkeypatch):
    import subprocess as sp
    spawned = _termux(monkeypatch, exc=sp.TimeoutExpired("termux-media-player", 4))
    assert sound.play("hatch")
    _finish_bridge()
    assert spawned
    assert sound.available()


def test_the_bridge_is_probed_once_not_every_beep(monkeypatch):
    _termux(monkeypatch, rc=0)
    probe = Mock(return_value=True)
    monkeypatch.setattr(sound, "_termux_bridge_live", probe)
    for cue in ("hatch", "confirm"):
        assert sound.play(cue)
        _finish_bridge()
    assert probe.call_count == 1


def test_volume_and_cache_ride_the_save_dir(tmp_path, monkeypatch):
    """volume.txt + the scaled-wav cache resolve through the LIVE save dir
    (shape sweep 2026-07-19: sound was theme.txt's twin — a hardcoded
    ~/.local that dropped the volume choice on iOS and escaped the test
    sandbox), and erase_all finally sweeps them (the volume pref was
    never in its list)."""
    import os
    from tuipet import persistence, sound
    monkeypatch.setattr(persistence, "SAVE_DIR", str(tmp_path))
    sound.set_volume(40) if hasattr(sound, "set_volume") else sound._save_volume(40)
    assert (tmp_path / "volume.txt").exists()
    os.makedirs(tmp_path / "sndcache" / "q40", exist_ok=True)
    removed = persistence.erase_all()
    assert "volume.txt" in removed and "sndcache/" in removed
    assert not (tmp_path / "volume.txt").exists()
    assert not (tmp_path / "sndcache").exists()
