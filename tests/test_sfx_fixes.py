"""Approved SFX fixes: no test sends audio to an OS player."""
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tuipet import itemfx, menu, optionsscreen, sound
from tuipet.app import TuiPetApp
from tuipet.battlescreen import BattlePanel
from tuipet.lobbyscreen import LobbyPanel
from tuipet.net import LobbyClient, LobbyState
from tuipet.pet import Pet
from tuipet.sfx import CueQueue, bubble, crossed, drain


@pytest.fixture
def audio(monkeypatch):
    playback = sound._Playback()
    monkeypatch.setattr(sound, "_playback", playback)
    monkeypatch.setattr(sound, "_PLAYER", ["mock-player"])
    proc = Mock()
    proc.poll.return_value = 0
    spawn = Mock(return_value=proc)
    monkeypatch.setattr(sound.subprocess, "Popen", spawn)
    yield playback, proc, spawn
    playback.stop()
    worker = playback.worker
    if worker:
        worker.join(2)
        assert not worker.is_alive()


def finish(playback):
    worker = playback.worker
    if worker:
        worker.join(2)
        assert not worker.is_alive()


@pytest.mark.parametrize("player", ["paplay", "afplay", "ffplay"])
def test_nonzero_exit_retires_backend_and_reports_bell_once(audio, monkeypatch, player):
    playback, proc, spawn = audio
    monkeypatch.setattr(sound, "_PLAYER", [player])
    proc.poll.return_value = 1
    assert sound.play("win", fallback=True)
    finish(playback)
    assert not sound.available()
    assert sound.failed() and not sound.failed()
    assert not sound.play("win")
    assert spawn.call_count == 1
    proc.wait.assert_called()


def test_background_work_does_not_block_and_mute_discards_prepared_audio(audio, monkeypatch):
    playback, proc, spawn = audio
    entered, release = threading.Event(), threading.Event()
    scaled = sound._scaled

    def slow(*args):
        entered.set()
        assert release.wait(2)
        return scaled(*args)

    monkeypatch.setattr(sound, "_scaled", slow)
    try:
        assert sound.play("evolve")
        assert entered.wait(1)
        sound.stop()
        release.set()
        finish(playback)
        spawn.assert_not_called()
    finally:
        release.set()


def test_new_cue_interrupts_long_sample_and_reaps_child(audio):
    playback, proc, spawn = audio
    started, replaced = threading.Event(), threading.Event()
    proc.poll.side_effect = lambda: started.set() or None
    replacement = Mock()
    replacement.poll.return_value = 0

    def launch(*args, **kw):
        if spawn.call_count == 1:
            return proc
        replaced.set()
        return replacement

    spawn.side_effect = launch
    sound.play("evolve")
    assert started.wait(1)
    sound.play("attack")
    assert replaced.wait(1), "a new cue must interrupt the long sample"
    finish(playback)
    proc.terminate.assert_called()
    proc.wait.assert_called()
    assert spawn.call_count == 2


def test_rate_limit_and_queue_are_bounded(audio, monkeypatch):
    playback, _, spawn = audio
    # Hold the worker slot to inspect admission without scheduler races.
    playback.worker = SimpleNamespace(is_alive=lambda: True)
    monkeypatch.setattr(sound.time, "monotonic", lambda: 100)
    for _ in range(100):
        assert sound.play("menu")
    assert len(playback.pending) == 1
    for i in range(20):
        playback.submit(f"cue{i}", False)
    assert len(playback.pending) == 8
    spawn.assert_not_called()
    playback.worker = None


def test_volume_change_cancels_old_playback(audio):
    playback, _, _ = audio
    playback.worker = SimpleNamespace(is_alive=lambda: True)
    sound.play("win")
    generation = playback.generation
    assert sound.set_volume(20) == 20
    assert not playback.pending
    assert playback.generation == generation + 1
    playback.worker = None


def test_termux_probe_is_off_the_ui_thread(audio, monkeypatch):
    playback, _, _ = audio
    entered, release = threading.Event(), threading.Event()
    monkeypatch.setattr(sound, "_PLAYER", ["termux-media-player", "play"])
    monkeypatch.setattr(sound, "_bridge_checked", False)

    def probe():
        entered.set()
        assert release.wait(2)
        return False

    monkeypatch.setattr(sound, "_termux_bridge_live", probe)
    try:
        assert sound.play("win", fallback=True)
        assert entered.wait(1)
        release.set()
        finish(playback)
        assert sound.failed()
    finally:
        release.set()


@pytest.mark.parametrize("won", [True, False])
def test_local_verdict_sounds_once(won):
    panel = BattlePanel(Pet(num=100, stage="Champion"))
    panel.sfx = None
    panel.phase = "anim"
    panel.battle = SimpleNamespace(won=won)
    panel._enter_result()
    panel._enter_result()
    assert drain(panel) == ["win" if won else "lose"]


@pytest.mark.parametrize("won,draw,cue", [(True, False, "win"), (False, False, "lose"),
                                          (False, True, "lose")])
@pytest.mark.parametrize("arena", [True, False])
def test_online_verdict_including_forfeit_or_missing_arena_sounds_once(won, draw, cue, arena):
    panel = LobbyPanel(Pet(num=100), lambda *a: None)
    panel.bshow = BattlePanel(Pet(num=100), duel=True) if arena else None
    panel._show_verdict(won, draw, "verdict")
    panel._show_verdict(won, draw, "duplicate")
    assert drain(panel) == [cue]
    if arena:
        assert drain(panel.bshow) == []


def test_bandage_opening_is_in_first_crossed_beat():
    script = itemfx.SCRIPTS["Bandaging"]
    assert list(crossed({"prev": 0, "step": 1, "snds": script["snds"]})) == ["click"]
    assert script["steps"] == 24


def test_web_sound_control_is_labelled_and_inert(monkeypatch):
    monkeypatch.setattr(optionsscreen, "is_browser", lambda: True)
    toggle = Mock()
    panel = optionsscreen.SoundPanel(lambda: False, toggle)
    volume = sound.volume()
    for key in ("enter", "space", "right", "down", "left"):
        panel.key(key)
    toggle.assert_not_called()
    assert sound.volume() == volume
    assert "unavailable on web" in panel.text().plain
    assert "toggle" not in panel.strip()
    assert "unavailable on web" in optionsscreen._sound_value(False)
    assert panel.key("escape") == ("done", None)


def test_cue_transport_preserves_order_through_child_exit():
    class Child(CueQueue):
        def key(self, key):
            self.sfx = "confirm"
            self.sfx = "reward"
            return ("done", 3)

    host = menu.SubHost()
    host.sfx = "menu"
    host.sub = Child()
    done = Mock()
    assert host.sub_key("enter", done)
    done.assert_called_once_with(3)
    assert drain(host) == ["menu", "confirm", "reward"]
    assert host.sub is None
    assert drain(host) == []


def test_crossed_beats_and_simultaneous_maps_all_drain():
    assert list(crossed({"prev": 0, "step": 3, "snds": {1: "click", 3: "confirm"},
                         "bite_snds": {1: "eat", 2: "lastBite"}})) == [
                             "eat", "click", "lastBite", "confirm"]


def test_delegated_queues_do_not_overwrite_parent():
    parent, child = CueQueue(), CueQueue()
    parent.sfx = "menu"
    child.sfx = "click"
    child.sfx = "confirm"
    bubble(parent, child)
    assert drain(parent) == ["menu", "click", "confirm"]
    assert drain(child) == []


def lobby():
    panel = LobbyPanel(Pet(num=100), lambda *a: None)
    panel.phase = "lobby"
    panel.state = LobbyState()
    panel.client = Mock(ladder=None, ladder_reward=None)
    return panel


def test_incoming_pm_sounds_once_but_public_chat_is_silent(monkeypatch):
    panel = lobby()
    panel.state.chat.append(("peer", "public"))
    panel.anim()
    assert drain(panel) == []
    panel.state.pm_received += 1
    panel.anim()
    assert drain(panel) == ["menu"]
    panel.anim()
    assert drain(panel) == []
    panel.state.pm_received += 1
    panel.anim()
    assert drain(panel) == []  # a rapid second PM is rate limited


def test_incoming_pm_counter_ignores_blocked_peers():
    client = LobbyClient("ws://unused", "me")
    client.state.blocked.add("blocked")
    client._handle('{"t":"pm","from_name":"blocked","text":"quiet"}')
    assert client.state.pm_received == 0
    client._handle('{"t":"pm","from_name":"peer","text":"hi"}')
    assert client.state.pm_received == 1


def test_lobby_refusal_and_error_feedback_is_rate_limited(monkeypatch):
    panel = lobby()
    clock = [100.0]
    monkeypatch.setattr("tuipet.lobbyscreen.time.monotonic", lambda: clock[0])
    panel._sent_invites.add((2, "battle"))
    panel.state.inbox.append({"t": "invite_resp", "from_id": 2, "kind": "battle",
                              "accept": False, "busy": True})
    panel.anim()
    assert drain(panel) == ["refuse"]
    panel.state.error = "denied"
    panel.anim()
    assert drain(panel) == []
    clock[0] += 2
    panel.state.error = "denied"
    panel.anim()
    assert drain(panel) == ["error"]
    panel.anim()
    assert drain(panel) == []


def test_mute_clears_alarm_tails_without_enable_bell(audio, monkeypatch):
    app = TuiPetApp.__new__(TuiPetApp)
    app.sound = True
    app._beep_q = [2, 6]
    app.bell = Mock()
    app._toggle_sound()
    assert not app.sound and not app._beep_q
    app._toggle_sound()
    assert app.sound
    app.bell.assert_not_called()


def test_home_result_retains_poses_without_duplicate_verdict():
    from tuipet.appactions import ActionsMixin
    # A real arena Screen builds the same cheer script as the home view.
    from tuipet.arena import Screen
    screen = Screen.__new__(Screen)
    screen.fx = None
    app = SimpleNamespace(screen_w=screen, pet=SimpleNamespace(dead=False), repaint=Mock())
    ActionsMixin._after_battle(app, SimpleNamespace(over=True, won=True, enemy=None))
    assert screen.fx["kind"] == "cheer"
    assert screen.fx["snds"] == {}


def test_browser_app_cannot_enable_or_dispatch_audio(audio, monkeypatch):
    from tuipet import web
    monkeypatch.setattr(web, "is_browser", lambda: True)
    app = TuiPetApp.__new__(TuiPetApp)
    app.sound = False
    app.bell = Mock()
    app._toggle_sound()
    assert not app.sound
    app.sound = True
    app.beep("win")
    assert not audio[0].pending
    audio[2].assert_not_called()
    app.bell.assert_not_called()


def test_volume_change_during_scaling_keeps_cache_level_consistent(monkeypatch):
    import array
    import os
    import wave
    sound.set_volume(50)
    original_open = wave.open

    def changing_open(*args, **kwargs):
        monkeypatch.setattr(sound, "_volume", 100)
        return original_open(*args, **kwargs)

    monkeypatch.setattr(sound.wave, "open", changing_open)
    path = sound._scaled(os.path.join(sound._DIR, "confirm.wav"), "confirm")
    assert "q50" in path
    with original_open(path) as wav:
        scaled = array.array("h", wav.readframes(wav.getnframes()))
    with original_open(os.path.join(sound._DIR, "confirm.wav")) as wav:
        raw = array.array("h", wav.readframes(wav.getnframes()))
    assert max(map(abs, scaled)) == max(map(abs, raw)) // 8


def test_async_failure_bell_is_consumed_on_frame_once(audio):
    playback, proc, _ = audio
    proc.poll.return_value = 1
    sound.play("win", fallback=True)
    finish(playback)
    app = TuiPetApp.__new__(TuiPetApp)
    app.sound = True
    app.mode = SimpleNamespace(anim=Mock(), text=lambda: "result")
    app.screen_w = SimpleNamespace(update=Mock())
    app._center = lambda text: text
    for name in ("_drain_beep_q", "_hud_marquee", "_drain_pms", "_drain_verdict", "_mode_strip"):
        setattr(app, name, Mock())
    app._status_painter = lambda: Mock()
    app.bell = Mock()
    app.on_frame()
    app.on_frame()
    app.bell.assert_called_once()


def test_stalled_player_is_retired_and_reaped(audio, monkeypatch):
    import itertools
    playback, proc, _ = audio
    proc.poll.return_value = None
    clock = itertools.count(0, 0.2)
    monkeypatch.setattr(sound.time, "monotonic", lambda: next(clock))
    sound.play("menu", fallback=True)
    finish(playback)
    assert not sound.available()
    assert sound.failed()
    proc.terminate.assert_called()
    proc.wait.assert_called()
