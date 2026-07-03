"""Lobby network client — the tuipet side of the multiplayer relay.

A `LobbyClient` runs as one asyncio task inside Textual's event loop. It owns a
`LobbyState` snapshot that the lobby Panel reads on each render tick (everything
runs on the one loop, so no locking). Outgoing messages are fire-and-forget via a
queue; incoming messages update the snapshot or land in `inbox` for the session
logic (jogress/battle) to drain.
"""
from __future__ import annotations

import asyncio
import json

import websockets

CHAT_CAP = 200


class LobbyState:
    """Render-friendly snapshot of the lobby; the Panel reads this every tick."""

    def __init__(self):
        self.connected = False
        self.error: str | None = None
        self.me_id: int | None = None
        self.me_name: str | None = None
        self.roster: list[dict] = []          # [{id,name,pet}] — replaced wholesale
        self.chat: list[tuple[str, str]] = []  # [(from_name, text)] — capped
        self.inbox: list[dict] = []            # invite / invite_resp / relay — drained by caller
        self.login_failed: str | None = None   # server rejected the login (bad password / name taken)

    def others(self):
        """Roster minus me — the people you can battle/jogress."""
        return [p for p in self.roster if p["id"] != self.me_id]


class SyncClient:
    """Background cloud-save sync over the same lobby server.

    Logs in with `sync_only` so it never joins the live roster (it can coexist with
    a lobby login on the same account). On connect it receives the account's stored
    save and hands it to `on_pull` once; thereafter `push_save` ships the latest
    local save up (only the newest pending push is kept). Reconnects with backoff;
    a bad password stops the loop. Fully fail-soft — offline just means no sync.
    """

    def __init__(self, uri, name, pw="", on_pull=None):
        self.uri = uri
        self.name = name
        self.pw = pw
        self.on_pull = on_pull
        self.connected = False
        self._pending = None                  # latest save dict awaiting upload
        self._ws = None
        self._wake: asyncio.Event = asyncio.Event()
        self._stop = False                    # set on auth failure -> don't retry

    def push_save(self, save):
        self._pending = save                  # keep only the newest; server is last-write-wins
        self._wake.set()

    async def run(self):
        backoff = 2
        while not self._stop:
            try:
                async with websockets.connect(self.uri, max_size=64 * 1024) as ws:
                    self._ws = ws
                    await ws.send(json.dumps({"t": "login", "name": self.name,
                                              "pw": self.pw, "sync_only": True}))
                    self.connected = True
                    backoff = 2
                    if self._pending is not None:
                        self._wake.set()       # flush anything queued while we were down
                    sender = asyncio.create_task(self._send_loop())
                    try:
                        async for raw in ws:
                            self._handle(raw)
                    finally:
                        sender.cancel()
            except Exception:
                pass                           # offline / dropped -> retry after backoff
            finally:
                self.connected = False
                self._ws = None
            if self._stop:
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

    async def _send_loop(self):
        while True:
            await self._wake.wait()
            self._wake.clear()
            save = self._pending
            if save is not None and self._ws is not None:
                try:
                    await self._ws.send(json.dumps({"t": "save", "save": save}))
                except Exception:
                    # a failed send must NOT kill the loop (it used to `return`,
                    # silently ending autosave uploads for the process lifetime);
                    # keep the save pending -- the reconnect loop re-wakes us
                    self._wake.set()
                    await asyncio.sleep(1.0)

    def _handle(self, raw):
        try:
            m = json.loads(raw)
        except (ValueError, AttributeError):
            return
        t = m.get("t")
        if t == "welcome":
            if self.on_pull is not None:
                self.on_pull(m.get("save"))    # server's stored save (or None)
        elif t == "login_failed":
            self._stop = True                  # wrong password -> stop retrying


class LobbyClient:
    def __init__(self, uri, name, pw="", pet=None, state=None):
        self.uri = uri
        self.name = name
        self.pw = pw
        self.pet = pet or {}
        self.state = state or LobbyState()
        self._ws = None
        self._q: asyncio.Queue = asyncio.Queue()

    # ---- outgoing (called from the UI thread/loop) -----------------------
    def _send(self, obj):
        self._q.put_nowait(obj)

    def chat(self, text):
        self._send({"t": "chat", "text": text})

    def update_pet(self, pet):
        self.pet = pet
        self._send({"t": "pet", "pet": pet})

    def invite(self, to, kind):
        self._send({"t": "invite", "to": to, "kind": kind})

    def respond(self, to, kind, accept, busy=False):
        msg = {"t": "invite_resp", "to": to, "kind": kind, "accept": bool(accept)}
        if busy:
            msg["busy"] = True
        self._send(msg)

    def relay(self, to, payload):
        self._send({"t": "relay", "to": to, "payload": payload})

    # ---- lifecycle -------------------------------------------------------
    async def run(self):
        """Connect, log in, then pump send + recv until the socket closes."""
        try:
            async with websockets.connect(self.uri, max_size=64 * 1024) as ws:
                self._ws = ws
                await ws.send(json.dumps({"t": "login", "name": self.name,
                                          "pw": self.pw, "pet": self.pet}))
                self.state.connected = True
                sender = asyncio.create_task(self._send_loop())
                try:
                    async for raw in ws:
                        self._handle(raw)
                finally:
                    sender.cancel()
        except Exception as e:                       # surfaced in the lobby as a banner
            self.state.error = str(e) or e.__class__.__name__
        finally:
            self.state.connected = False
            self._ws = None

    async def _send_loop(self):
        while True:
            obj = await self._q.get()
            try:
                await self._ws.send(json.dumps(obj))
            except Exception:
                return

    def _handle(self, raw):
        try:
            m = json.loads(raw)
            t = m.get("t")
        except (ValueError, AttributeError):
            return
        s = self.state
        if t == "welcome":
            s.me_id = m.get("id")
            s.me_name = m.get("name")
        elif t == "roster":
            s.roster = m.get("players") or []
        elif t == "chat":
            s.chat.append((m.get("from_name", "?"), m.get("text", "")))
            del s.chat[:-CHAT_CAP]
        elif t in ("invite", "invite_resp", "relay"):
            s.inbox.append(m)
        elif t == "login_failed":
            s.login_failed = m.get("msg")
        elif t == "error":
            s.error = m.get("msg")
