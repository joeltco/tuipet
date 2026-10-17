"""q in the browser must never end the app: a tab has no "after" (2026-10-17)."""
from types import SimpleNamespace

from tuipet import web
from tuipet.appactions import ActionsMixin


def _fake(calls):
    return SimpleNamespace(pet=object(), autosave=lambda: calls.append("save"),
                           notify=lambda msg, **k: calls.append(msg),
                           exit=lambda: calls.append("exit"))


def test_q_in_browser_saves_and_stays(monkeypatch):
    monkeypatch.setattr(web, "is_browser", lambda: True)
    monkeypatch.setattr("tuipet.appactions.persistence.save", lambda pet: None)
    calls = []
    ActionsMixin.action_quit(_fake(calls))
    assert "exit" not in calls and "save" in calls
    assert any("Close the tab" in c for c in calls)


def test_q_in_terminal_still_exits(monkeypatch):
    monkeypatch.setattr(web, "is_browser", lambda: False)
    monkeypatch.setattr("tuipet.appactions.persistence.save", lambda pet: None)
    calls = []
    ActionsMixin.action_quit(_fake(calls))
    assert calls == ["exit"]
