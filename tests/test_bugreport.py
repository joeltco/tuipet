"""In-app bug reporter (Joel 2026-07-09): a `b` action collects text and sends a
one-shot report to the lobby server, with an offline stash that retries."""
import asyncio
import json
import os
import sys

from tuipet.pet import Pet
from tuipet.bugscreen import BugReportPanel, wrap
from tuipet import net, persistence


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", bits=99)


def _type(pan, s):
    for ch in s:
        pan.key("space" if ch == " " else ch)


def test_panel_collects_text_and_submits():
    pan = BugReportPanel(_pet())
    _type(pan, "shop crashed on buy")
    assert pan.key("backspace") is None
    assert pan.buf == "shop crashed on bu"
    _type(pan, "y")
    r = pan.key("enter")
    assert r == ("done", ("bug", "shop crashed on buy"))


def test_panel_empty_submit_is_rejected_and_esc_cancels():
    pan = BugReportPanel(_pet())
    assert pan.key("enter") is None            # empty: stays open with a nudge
    assert "Type the bug" in pan.msg
    _type(pan, "   ")                          # whitespace only still counts as empty
    assert pan.key("enter") is None
    assert pan.key("escape") == ("done", None)


def test_wrap_hard_splits_long_tokens():
    lines = wrap("x" * 90, 38)
    assert all(len(l) <= 38 for l in lines) and "".join(lines) == "x" * 90


def test_submit_bug_returns_false_when_server_unreachable():
    ok = asyncio.run(net.submit_bug("ws://127.0.0.1:1", "offline test", timeout=1.0))
    assert ok is False


def test_pending_bug_stash_roundtrip(tmp_path, monkeypatch):
    """peek reads WITHOUT deleting; write rewrites the survivors (bug audit
    2026-07-19: the old take-then-send lost every unsent report to a quit
    mid-flush -- the round-5 PM lesson)."""
    monkeypatch.setattr(persistence, "SAVE_DIR", str(tmp_path))
    assert persistence.peek_pending_bugs() == []          # nothing yet
    persistence.add_pending_bug({"text": "a", "name": "x"})
    persistence.add_pending_bug({"text": "b", "name": "y"})
    got = persistence.peek_pending_bugs()
    assert [r["text"] for r in got] == ["a", "b"]
    assert [r["text"] for r in persistence.peek_pending_bugs()] == ["a", "b"]   # STILL there
    assert persistence.write_pending_bugs(got[1:]) is True
    assert [r["text"] for r in persistence.peek_pending_bugs()] == ["b"]        # survivors only
    assert persistence.write_pending_bugs([]) is True
    assert persistence.peek_pending_bugs() == []                                # [] removes


def test_server_handle_bug_stores_and_acks(tmp_path, monkeypatch):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server
    bugs = tmp_path / "bugs.jsonl"
    monkeypatch.setattr(server, "BUGS_PATH", str(bugs))

    sent = []

    class _WS:
        async def send(self, s): sent.append(json.loads(s))

    class _Client:
        ws = _WS()
        name = "guest9"
        bugs_sent = 0

    c = _Client()
    asyncio.run(server._handle_bug(c, {"t": "bug", "text": "boom", "name": "Joel",
                                       "version": "0.2.393",
                                       "pet": {"num": 1, "hax": "x" * 9000}}))
    asyncio.run(server._handle_bug(c, {"t": "bug", "text": "   "}))   # empty -> rejected

    recs = [json.loads(l) for l in open(bugs)]
    assert len(recs) == 1                                  # only the real one stored
    assert recs[0]["from"] == "Joel" and recs[0]["text"] == "boom"
    assert recs[0]["pet"] == {"num": 1}                    # only the known pet fields ride
    assert sent[0] == {"t": "bug_ok", "ok": True}
    assert sent[1] == {"t": "bug_ok", "ok": False}


def test_server_bug_endpoint_is_abuse_capped(tmp_path, monkeypatch):
    """Unauthenticated by design, so capped (audit 2026-07-10): a connection
    gets MAX_BUGS_PER_CONN stores, and the file stops growing past MAX_BUG_FILE."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server
    bugs = tmp_path / "bugs.jsonl"
    monkeypatch.setattr(server, "BUGS_PATH", str(bugs))

    sent = []

    class _WS:
        async def send(self, s): sent.append(json.loads(s))

    class _Client:
        ws = _WS()
        name = "guest9"
        bugs_sent = 0

    c = _Client()
    for i in range(server.MAX_BUGS_PER_CONN + 3):
        asyncio.run(server._handle_bug(c, {"t": "bug", "text": "spam %d" % i}))
    stored = [json.loads(l) for l in open(bugs)]
    assert len(stored) == server.MAX_BUGS_PER_CONN         # the tail was refused
    assert [m["ok"] for m in sent].count(False) == 3

    monkeypatch.setattr(server, "MAX_BUG_FILE", 10)        # file already "full"
    c2 = _Client()
    c2.ws = _WS()
    asyncio.run(server._handle_bug(c2, {"t": "bug", "text": "one more"}))
    assert sent[-1] == {"t": "bug_ok", "ok": False}
    assert len(open(bugs).readlines()) == server.MAX_BUGS_PER_CONN   # nothing appended


def test_flush_survives_an_outage_and_drops_damaged_lines(tmp_path, monkeypatch):
    """The boot flush keeps unsent reports ON DISK through an outage (read-
    then-rewrite), sends in order, stops at the first failure, and drops
    empty-text damage instead of re-stashing it forever."""
    import asyncio
    from tuipet.app import TuiPetApp
    from tuipet import net
    monkeypatch.setattr(persistence, "SAVE_DIR", str(tmp_path))
    persistence.add_pending_bug({"text": "", "name": "damaged"})
    persistence.add_pending_bug({"text": "first", "name": "x"})
    persistence.add_pending_bug({"text": "second", "name": "y"})

    calls = []

    async def down(uri, text, meta=None, name=""):
        calls.append(text)
        return False

    monkeypatch.setattr(net, "submit_bug", down)
    app = TuiPetApp.__new__(TuiPetApp)             # the flush needs no UI
    asyncio.run(TuiPetApp._flush_bugs(app))
    assert calls == ["first"]                      # stopped at the outage
    left = [r["text"] for r in persistence.peek_pending_bugs()]
    assert left == ["first", "second"]             # kept, in order; damage gone

    async def up(uri, text, meta=None, name=""):
        return True

    monkeypatch.setattr(net, "submit_bug", up)
    asyncio.run(TuiPetApp._flush_bugs(app))
    assert persistence.peek_pending_bugs() == []   # all delivered, stash gone


def test_send_verdict_parks_under_a_mode_and_flashes_home():
    """The async send outcome must REACH the player (round-19 swallow class):
    home -> flash now; inside a screen -> parked, the drain flashes it on
    the next home frame."""
    from tuipet.app import TuiPetApp
    flashes = []
    app = TuiPetApp.__new__(TuiPetApp)
    app.flash = lambda m: flashes.append(m)
    app.mode = object()                            # a screen is open
    TuiPetApp._bug_verdict(app, "sent!")
    assert flashes == [] and app._bug_note == "sent!"
    TuiPetApp._drain_bug_note(app)                 # still in the mode: holds
    assert flashes == []
    app.mode = None
    TuiPetApp._drain_bug_note(app)                 # back home: it lands
    assert flashes == ["sent!"] and app._bug_note == ""
    TuiPetApp._bug_verdict(app, "again")           # home: immediate
    assert flashes == ["sent!", "again"]
