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
        assert [sound.play("happy") for _ in range(3)] == [False, False, False]
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
    monkeypatch.setattr(appmod.sound, "play", lambda name: False)
    appmod.TuiPetApp.beep(app, "hatch")            # a milestone
    assert rung == [1], "a milestone must ring the bell when there is no player"
    appmod.TuiPetApp.beep(app, "eat", bell=False)  # a routine sound stays quiet
    assert rung == [1]
