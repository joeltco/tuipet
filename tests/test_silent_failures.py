"""The swallowed-failure sweep (2026-07-13).

Three shipped bugs shared one shape: a failure the code swallowed and reported
to the player as SUCCESS (iOS saves, iOS sound, the dead Termux bridge). These
pin the rest of that class -- every path where tuipet PROMISES the player
something and could quietly fail to deliver.
"""
import importlib
import os
import tempfile

from tuipet import persistence



# (the two cloud-drop tests left with the cloud-sync cut 2026-07-18)


def test_a_bug_report_never_promises_a_send_it_cannot_make(monkeypatch):
    """`add_pending_bug` swallowed OSError, so on a read-only save dir the
    player was told 'saved; it will send next time' while the report was
    simply gone."""
    home = tempfile.mkdtemp()
    os.chmod(home, 0o555)
    try:
        monkeypatch.setenv("HOME", home)
        for k in ("TUIPET_SAVE_DIR", "XDG_DATA_HOME"):
            monkeypatch.delenv(k, raising=False)
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)
        assert persistence.add_pending_bug({"text": "x"}) is False, \
            "an unstashable report must say so"
    finally:
        os.chmod(home, 0o755)
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)


def test_a_stashable_bug_reports_success():
    d = tempfile.mkdtemp()
    old = persistence.SAVE_DIR
    try:
        persistence.SAVE_DIR = d
        assert persistence.add_pending_bug({"text": "x"}) is True
        assert os.path.exists(os.path.join(d, "pending_bugs.jsonl"))
    finally:
        persistence.SAVE_DIR = old
