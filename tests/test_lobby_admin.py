"""Lobby admin channel (Joel 2026-07-10): a key-authed `admin` message lets the
dev read the room (`who`) and broadcast 📢 announcements; public room events
(chat/join/leave/announce) append to lobby_feed.jsonl for offline reading."""
import asyncio
import json
import os
import sys

from tuipet.net import LobbyClient, SyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import server  # noqa: E402


class _WS:
    def __init__(self, sent):
        self._sent = sent

    async def send(self, s):
        self._sent.append(json.loads(s))


def _client(sent, name="guest1", live=True, logged=True):
    c = server.Client(_WS(sent))
    c.name, c.live, c.logged = name, live, logged
    return c


def _wire(monkeypatch, tmp_path, key="s3cret"):
    monkeypatch.setattr(server, "FEED_PATH", str(tmp_path / "feed.jsonl"))
    monkeypatch.setenv("TUIPET_ADMIN_KEY", key)
    server.CLIENTS.clear()
    server.CHAT_BACKLOG.clear()
    return key


def test_admin_needs_the_key(tmp_path, monkeypatch):
    _wire(monkeypatch, tmp_path)
    sent = []
    admin = _client(sent, "snoop", logged=False)
    asyncio.run(server._handle_admin(admin, {"cmd": "who", "key": "wrong"}))
    asyncio.run(server._handle_admin(admin, {"cmd": "who"}))
    assert [m["t"] for m in sent] == ["error", "error"]
    monkeypatch.delenv("TUIPET_ADMIN_KEY")
    monkeypatch.setattr(server, "ADMIN_KEY_PATH", str(tmp_path / "nokey"))
    asyncio.run(server._handle_admin(admin, {"cmd": "who", "key": ""}))
    assert sent[-1]["t"] == "error"          # no key configured -> channel disabled


def test_admin_who_reads_the_room(tmp_path, monkeypatch):
    key = _wire(monkeypatch, tmp_path)
    room = []
    a = _client(room, "joel", live=True)
    b = _client(room, "mika", live=False)    # a home-screen ghost
    b.pet = {"name": "Aggy", "stage": "Champion"}
    server.CLIENTS[a.id], server.CLIENTS[b.id] = a, b
    sent = []
    asyncio.run(server._handle_admin(_client(sent, logged=False),
                                     {"cmd": "who", "key": key}))
    server.CLIENTS.clear()
    r = sent[-1]
    assert r["t"] == "admin_ok" and r["online"] == 2
    ghost = next(p for p in r["roster"] if p["name"] == "mika")
    assert ghost["live"] is False and ghost["pet"] == "Aggy"


def test_admin_announce_broadcasts_and_feeds(tmp_path, monkeypatch):
    key = _wire(monkeypatch, tmp_path)
    room = []
    a = _client(room, "joel", live=True)
    b = _client(room, "mika", live=False)
    server.CLIENTS[a.id], server.CLIENTS[b.id] = a, b
    sent = []
    asyncio.run(server._handle_admin(_client(sent, logged=False),
                                     {"cmd": "announce", "key": key,
                                      "text": "  v0.2.397 is live!  "}))
    server.CLIENTS.clear()
    assert sent[-1] == {"t": "admin_ok", "cmd": "announce", "sent": 2}
    out = [m for m in room if m.get("t") == "announce"]
    assert len(out) == 2 and all(m["text"] == "v0.2.397 is live!" for m in out)
    feed = [json.loads(l) for l in open(tmp_path / "feed.jsonl")]
    assert feed[-1]["kind"] == "announce" and feed[-1]["text"] == "v0.2.397 is live!"
    # late joiners replay it from the chat backlog
    assert {"t": "announce", "text": "v0.2.397 is live!"} in server.CHAT_BACKLOG
    server.CHAT_BACKLOG.clear()


def test_admin_empty_announce_sends_nothing(tmp_path, monkeypatch):
    key = _wire(monkeypatch, tmp_path)
    room = []
    server_client = _client(room, "joel", live=True)
    server.CLIENTS[server_client.id] = server_client
    sent = []
    asyncio.run(server._handle_admin(_client(sent, logged=False),
                                     {"cmd": "announce", "key": key, "text": "   "}))
    server.CLIENTS.clear()
    assert sent[-1] == {"t": "admin_ok", "cmd": "announce", "sent": 0}
    assert not room and not os.path.exists(tmp_path / "feed.jsonl")


def test_feed_logs_public_events(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "FEED_PATH", str(tmp_path / "feed.jsonl"))
    server._feed("chat", name="joel", text="hi room")
    server._feed("join", name="mika", ghost=True)
    server._feed("leave", name="mika", ghost=True)
    recs = [json.loads(l) for l in open(tmp_path / "feed.jsonl")]
    assert [r["kind"] for r in recs] == ["chat", "join", "leave"]
    assert all("ts" in r for r in recs)


def test_announce_lands_in_lobby_chat_unblockable():
    c = LobbyClient("ws://x/", "joel")
    c._handle('{"t": "welcome", "id": 1, "name": "joel"}')
    c.state.blocked.add("📢")                # even a weird block can't mute the dev
    c._handle('{"t": "announce", "text": "Blood Moon at 8"}')
    assert ("📢", "Blood Moon at 8") in c.state.chat


def test_announce_reaches_the_home_screen_ghost():
    s = SyncClient("ws://x/", "joel")
    s._handle('{"t": "announce", "text": "downtime 5 min"}')
    assert ("📢", "downtime 5 min") in s.inbox
