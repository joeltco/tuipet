"""tuipet lobby server — a standalone WebSocket relay.

Zero tuipet dependency: it knows nothing about pets, jogress, or battle rules.
It only does four things, so it can be dropped on any host and run as one file:

  * name login          a client joins with a handle + an opaque pet "card"
  * presence            everyone sees a live roster of who's online
  * chat                broadcast text to the room
  * point-to-point      invite / invite-response / session relay between two
                        clients (jogress and battle plug in here, client-side)

Wire format: one JSON object per message, discriminated by the field `t`.
Run:  python3 server.py            (PORT / HOST via env, defaults 0.0.0.0:8765)
"""
from __future__ import annotations

import asyncio
import json
import os
import itertools
import logging

import websockets

LOG = logging.getLogger("tuipet.lobby")
HOST = os.environ.get("TUIPET_HOST", "0.0.0.0")
PORT = int(os.environ.get("TUIPET_PORT", "8765"))

# defensive limits — a lobby relay, not a chat firehose
MAX_CLIENTS = 200
MAX_NAME = 24
MAX_CHAT = 400
MAX_MSG_BYTES = 64 * 1024          # a pet/battle card stays well under this

_ids = itertools.count(1)


class Client:
    __slots__ = ("id", "ws", "name", "pet", "live")

    def __init__(self, ws):
        self.id = next(_ids)
        self.ws = ws
        self.name = f"guest{self.id}"
        self.pet = {}              # opaque card the lobby never interprets
        self.live = False          # only logged-in clients appear in the roster

    def public(self):
        return {"id": self.id, "name": self.name, "pet": self.pet}


CLIENTS: dict[int, Client] = {}


def _clean(s, limit):
    return str(s).replace("\n", " ").replace("\r", " ").strip()[:limit]


def _unique_name(name):
    name = _clean(name, MAX_NAME) or "guest"
    taken = {c.name for c in CLIENTS.values()}
    if name not in taken:
        return name
    for n in itertools.count(2):           # "Joel" -> "Joel#2" -> "Joel#3"
        cand = f"{name}#{n}"
        if cand not in taken:
            return cand


async def _send(client, obj):
    try:
        await client.ws.send(json.dumps(obj))
    except Exception:
        pass                                # a dead socket gets reaped on its own task


async def _broadcast(obj, exclude=None):
    if CLIENTS:
        msg = json.dumps(obj)
        await asyncio.gather(*(
            c.ws.send(msg) for c in CLIENTS.values() if c.id != exclude
        ), return_exceptions=True)


def _roster():
    return {"t": "roster", "players": [c.public() for c in CLIENTS.values() if c.live]}


async def _push_roster():
    await _broadcast(_roster())


async def handler(ws):
    if len(CLIENTS) >= MAX_CLIENTS:
        await ws.send(json.dumps({"t": "error", "msg": "Lobby is full."}))
        return
    client = Client(ws)
    CLIENTS[client.id] = client
    logged_in = False
    try:
        async for raw in ws:
            if len(raw) > MAX_MSG_BYTES:
                continue
            try:
                m = json.loads(raw)
                t = m.get("t")
            except (ValueError, AttributeError):
                continue

            if t == "login":
                client.name = _unique_name(m.get("name"))
                client.pet = m.get("pet") or {}
                client.live = logged_in = True
                await _send(client, {"t": "welcome", "id": client.id, "name": client.name})
                await _push_roster()
                LOG.info("login id=%s name=%s (%d online)", client.id, client.name, len(CLIENTS))

            elif not logged_in:
                await _send(client, {"t": "error", "msg": "Log in first."})

            elif t == "pet":                # update my pet card -> refresh roster
                client.pet = m.get("pet") or {}
                await _push_roster()

            elif t == "chat":
                text = _clean(m.get("text"), MAX_CHAT)
                if text:
                    await _broadcast({"t": "chat", "from_id": client.id,
                                      "from_name": client.name, "text": text})

            elif t in ("invite", "invite_resp", "relay"):
                target = CLIENTS.get(m.get("to"))
                if target is None:
                    await _send(client, {"t": "error", "msg": "That player just left."})
                    continue
                out = {"t": t, "from_id": client.id, "from_name": client.name}
                if t == "relay":
                    out["payload"] = m.get("payload")
                else:
                    out["kind"] = m.get("kind")        # "jogress" | "battle"
                    if t == "invite_resp":
                        out["accept"] = bool(m.get("accept"))
                await _send(target, out)

            # unknown `t` is ignored — forward-compatible with newer clients
    except websockets.ConnectionClosed:
        pass
    finally:
        CLIENTS.pop(client.id, None)
        if logged_in:
            await _push_roster()
        LOG.info("gone  id=%s (%d online)", client.id, len(CLIENTS))


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    LOG.info("tuipet lobby on ws://%s:%d", HOST, PORT)
    async with websockets.serve(handler, HOST, PORT, max_size=MAX_MSG_BYTES):
        await asyncio.Future()             # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
