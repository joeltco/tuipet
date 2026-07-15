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
ANNOUNCE = "📢"          # the dev's speaker: never a peer, never blockable


def parse_msg(raw):
    """One JSON-envelope guard for every lobby message: (msg, type) or
    (None, None) on anything malformed."""
    try:
        m = json.loads(raw)
        return m, m.get("t")
    except (ValueError, AttributeError):
        return None, None


class _WsClient:
    """The transport loop BOTH clients ride: connect -> login -> pump send +
    recv -> on a drop, retry with exponential backoff; a rejected login sets
    _stop and ends the loop for good.  This loop lived in two drifting copies
    (the send-loop `return`-kills-autosave bug lived in exactly this drift;
    refactor 2026-07-05).  Subclasses supply the login payload, their own
    _send_loop/_handle, and the connection-state bookkeeping hooks."""

    _backoff0 = 2.0
    _backoff_cap = 30.0

    async def run(self):
        backoff = self._backoff0
        while not self._stop:
            try:
                async with websockets.connect(self.uri, max_size=64 * 1024) as ws:
                    self._ws = ws
                    await ws.send(json.dumps(self._login_msg()))
                    self._on_connect()
                    backoff = self._backoff0
                    sender = asyncio.create_task(self._send_loop())
                    try:
                        async for raw in ws:
                            self._handle(raw)
                    finally:
                        sender.cancel()
            except Exception as e:
                self._on_error(e)
            finally:
                self._on_disconnect()
                self._ws = None
            if self._stop:
                break
            self._on_retry_wait()
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self._backoff_cap)
        self._on_stopped()

    # hooks -- default no-ops
    def _on_error(self, e):
        pass

    def _on_retry_wait(self):
        pass

    def _on_stopped(self):
        pass


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
        self.server_proto = 0                  # the relay's LOBBY_PROTO from welcome (0 = pre-handshake)
        self.reconnecting = False              # dropped -> the client is retrying with backoff
        self.dms: dict = {}                    # peer_name -> [(from_name, text)] private threads
        self.unread: set = set()               # peer names with unread DMs
        self.blocked: set = set()              # muted peers (loaded from settings on connect)
        self.room: str | None = None           # current password room (None = main lobby)

    def others(self):
        """Roster minus me — the people you can battle/jogress."""
        return [p for p in self.roster if p["id"] != self.me_id]


class SyncClient(_WsClient):
    """Background cloud-save sync over the same lobby server.

    Logs in with `sync_only` so it never joins the live roster (it can coexist with
    a lobby login on the same account). On connect it receives the account's stored
    save and hands it to `on_pull` once; thereafter `push_save` ships the latest
    local save up (only the newest pending push is kept). Reconnects with backoff;
    a bad password stops the loop. Fully fail-soft — offline just means no sync.
    """

    _backoff_cap = 60.0

    def __init__(self, uri, name, pw="", on_pull=None):
        # The server ACKs every save with {"t":"saved","ok":...} and answers
        # ok=False when it DROPPED it (a stale lease: a newer session of this
        # account owns the saves).  We never read that ack -- _handle had no
        # "saved" branch -- so a device whose lease was taken went on believing
        # its pet was syncing while the server binned every push.  Cross-device
        # progress vanished, silently.  (Swallowed-failure sweep 2026-07-13:
        # the same shape as the iOS silent save and the dead Termux bridge.)
        self.cloud_dropped = False
        self.uri = uri
        self.name = name
        self.pw = pw
        self.on_pull = on_pull
        self.connected = False
        self.inbox: list = []                 # (from_name, text) PMs -> the home-screen alert
        self._pending = None                  # latest save dict awaiting upload
        self._ws = None
        self._wake: asyncio.Event = asyncio.Event()
        self._stop = False                    # set on auth failure -> don't retry

    def push_save(self, save):
        self._pending = save                  # keep only the newest; server is last-write-wins
        self._wake.set()

    def _login_msg(self):
        from .cloudsync import BOOT           # one launch stamp per process
        return {"t": "login", "name": self.name, "pw": self.pw,
                "sync_only": True, "boot": BOOT}

    def _on_connect(self):
        self.connected = True
        if self._pending is not None:
            self._wake.set()                  # flush anything queued while we were down

    def _on_disconnect(self):
        self.connected = False

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
        m, t = parse_msg(raw)
        if t == "welcome":
            if self.on_pull is not None:
                self.on_pull(m.get("save"))    # server's stored save (or None)
        elif t == "saved":
            # the verdict on our last push: ok=False means the server BINNED it
            self.cloud_dropped = not m.get("ok")
        elif t == "pm":
            # the sync ghost is the HOME-SCREEN alert channel: the app drains
            # this into the message box (presence 2026-07-05)
            self.inbox.append((m.get("from_name", "?"), m.get("text", "")))
            del self.inbox[:-20]
        elif t == "announce":
            # a server announcement reaches the home screen the same way a PM
            # does -- the 📢 name marks it as the dev's line
            self.inbox.append(("📢", m.get("text", "")))
            del self.inbox[:-20]
        elif t == "login_failed":
            self._stop = True                  # wrong password -> stop retrying


class LobbyClient(_WsClient):
    def __init__(self, uri, name, pw="", pet=None, state=None):
        self.uri = uri
        self.name = name
        self.pw = pw
        self.pet = pet or {}
        self.state = state or LobbyState()
        self._ws = None
        self._q: asyncio.Queue = asyncio.Queue()
        self._stop = False                    # rejected login (or teardown) -> no retry
        self._had_welcome = False             # a past successful login makes drops RECONNECTS
        self._backoff0 = 2.0                  # first-retry delay (tests shrink it)
        self.ladder = None                    # last ladder message (rankings page)
        self.raid = None                      # last raid status message
        self.raid_reward = None               # a claimed reward, once

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

    def pm(self, to, text, to_name=None):
        msg = {"t": "pm", "to": to, "text": text}
        if to_name:
            msg["to_name"] = to_name       # lets the server queue when the id is stale/offline
        self._send(msg)

    def ping(self, to):
        """Nudge a ghost (app open, not in the lobby) to come battle -- rides the PM
        channel, which lands on their home-screen alert."""
        self.pm(to, "\u2694\ufe0f wants to battle -- come to the Lobby!")

    def respond(self, to, kind, accept, busy=False):
        msg = {"t": "invite_resp", "to": to, "kind": kind, "accept": bool(accept)}
        if busy:
            msg["busy"] = True
        self._send(msg)

    def relay(self, to, payload):
        self._send({"t": "relay", "to": to, "payload": payload})

    def room(self, code):
        """Join the password room for `code` (everyone typing the same phrase
        meets there); empty code returns to the main lobby."""
        self._send({"t": "room", "code": code})

    def ladder_report(self, won, opp):
        """File this side of a PvP outcome; the server pairs both stories."""
        self._send({"t": "ladder_report", "won": bool(won), "opp": opp})

    def ladder_get(self):
        self._send({"t": "ladder_get"})

    def ladder_claim(self, season):
        self._send({"t": "ladder_claim", "season": season})

    def raid_get(self):
        self._send({"t": "raid_get"})

    def raid_hit(self, damage, stage):
        self._send({"t": "raid_hit", "damage": int(damage), "stage": stage})

    def raid_claim(self, raid_id):
        self._send({"t": "raid_claim", "raid": raid_id})

    # ---- lifecycle (the loop itself lives on _WsClient) --------------------
    def _login_msg(self):
        from .cloudsync import BOOT           # one launch stamp per process: the
        #                                       server lets the newest launch evict
        #                                       its own stale room session (message
        #                                       audit 2026-07-06)
        return {"t": "login", "name": self.name, "pw": self.pw, "pet": self.pet,
                "boot": BOOT}

    def _on_connect(self):
        self.state.connected = True
        self.state.reconnecting = False

    def _on_error(self, e):                          # surfaced in the lobby as a banner
        if not self._had_welcome:
            self.state.error = str(e) or e.__class__.__name__

    def _on_disconnect(self):
        self.state.connected = False

    def _on_retry_wait(self):
        # nobody is reachable while down: an empty roster voids any live
        # session panel-side, exactly like a partner leaving
        self.state.roster = []
        self.state.reconnecting = True

    def _on_stopped(self):
        self.state.reconnecting = False

    async def _send_loop(self):
        while True:
            obj = await self._q.get()
            try:
                await self._ws.send(json.dumps(obj))
            except Exception:
                # don't lose the frame we already dequeued: requeue it so
                # run()'s reconnect spawns a fresh sender that delivers it.  A
                # bare `return` silently dropped that obj -- a move/invite frame
                # could vanish and hang a handshake (hardening 2026-07-12).
                try:
                    self._q.put_nowait(obj)
                except Exception:
                    pass
                return

    def _handle(self, raw):
        m, t = parse_msg(raw)
        s = self.state
        if t == "welcome":
            self._had_welcome = True
            s.me_id = m.get("id")
            s.me_name = m.get("name")
            try:
                s.server_proto = int(m.get("proto") or 0)
            except (TypeError, ValueError):
                s.server_proto = 0
        elif t == "ladder":
            self.ladder = m               # the rankings page renders from this
        elif t == "raid":
            self.raid = m                 # the raid page renders from this
        elif t == "raid_reward":
            self.raid_reward = m          # the claim flow consumes this once
        elif t == "roster":
            s.roster = m.get("players") or []
        elif t == "room_ok":
            s.room = m.get("room") or None
            s.chat.append(("", f"— room: {s.room} —" if s.room else "— main lobby —"))
            del s.chat[:-CHAT_CAP]
        elif t == "chat":
            nm = m.get("from_name", "?")
            if nm not in s.blocked:
                s.chat.append((nm, m.get("text", "")))
                del s.chat[:-CHAT_CAP]
        elif t == "announce":
            # a server announcement rides the public feed under the 📢 speaker
            # (unblockable -- it's the dev's line, not a peer's)
            s.chat.append((ANNOUNCE, m.get("text", "")))
            del s.chat[:-CHAT_CAP]
        elif t == "pm":
            nm = m.get("from_name", "?")
            if nm not in s.blocked:
                s.dms.setdefault(nm, []).append((nm, m.get("text", "")))
                del s.dms[nm][:-CHAT_CAP]
                s.unread.add(nm)
        elif t == "pm_ok":
            to = m.get("to_name", "?")
            s.dms.setdefault(to, []).append((s.me_name or "you", m.get("text", "")))
            del s.dms[to][:-CHAT_CAP]
        elif t in ("invite", "invite_resp", "relay"):
            s.inbox.append(m)
        elif t == "login_failed":
            msg = m.get("msg") or ""
            if self._had_welcome and "already online" in msg:
                # reconnect race: the server hasn't reaped our dead session yet --
                # NOT a credentials problem, so keep retrying instead of ejecting
                # the player to the login screen
                pass
            else:
                s.login_failed = msg
                self._stop = True
        elif t == "error":
            s.error = m.get("msg")


async def submit_bug(uri, text, meta=None, name="", timeout=8.0):
    """One-shot bug submit: connect, send a bug envelope (NO login needed),
    await the server ack, close.  True only on a server-confirmed store."""
    payload = {"t": "bug", "text": text, "name": name}
    if meta:
        payload.update(meta)
    try:
        async with websockets.connect(uri, max_size=64 * 1024, open_timeout=timeout) as ws:
            await ws.send(json.dumps(payload))
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            m, t = parse_msg(raw)
            return bool(t == "bug_ok" and m and m.get("ok"))
    except Exception:
        return False
