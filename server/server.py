"""tuipet lobby server — a standalone WebSocket relay with named accounts.

Zero tuipet dependency. It does:
  * account login    name + password; first login to a name claims it (password
                     hashed with pbkdf2, stored in accounts.json), later logins to
                     that name must match. So your name is yours.
  * presence         a live roster of who's online
  * chat             broadcast text to the room
  * point-to-point   invite / invite-response / session relay between two clients
                     (jogress and battle plug in here, client-side)

Wire format: one JSON object per message, discriminated by the field `t`.
Run:  python3 server.py     (HOST/PORT/TUIPET_ACCOUNTS via env; defaults 0.0.0.0:8765)
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import itertools
import json
import logging
import os

import websockets

LOG = logging.getLogger("tuipet.lobby")
HOST = os.environ.get("TUIPET_HOST", "0.0.0.0")
PORT = int(os.environ.get("TUIPET_PORT", "8765"))
ACCOUNTS_PATH = os.environ.get(
    "TUIPET_ACCOUNTS",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts.json"))

MAX_CLIENTS = 200
MAX_NAME = 24
MAX_PW = 128
MAX_CHAT = 400
MAX_MSG_BYTES = 64 * 1024
PBKDF2_ITERS = 100_000

_ids = itertools.count(1)


# ---- accounts (name -> {name, salt, hash}, keyed by lowercased name) --------
def _load_accounts():
    try:
        return json.load(open(ACCOUNTS_PATH))
    except (OSError, ValueError):
        return {}


ACCOUNTS = _load_accounts()


def _save_accounts():
    tmp = ACCOUNTS_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(ACCOUNTS, f)
    os.replace(tmp, ACCOUNTS_PATH)


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, PBKDF2_ITERS).hex()


def _make_account(name, pw):
    salt = os.urandom(16)
    return {"name": name, "salt": salt.hex(), "hash": _hash(pw, salt)}


def _verify(pw, acc):
    return hmac.compare_digest(_hash(pw, bytes.fromhex(acc["salt"])), acc["hash"])


class Client:
    __slots__ = ("id", "ws", "name", "pet", "live")

    def __init__(self, ws):
        self.id = next(_ids)
        self.ws = ws
        self.name = f"guest{self.id}"
        self.pet = {}
        self.live = False


CLIENTS: dict[int, Client] = {}


def _clean(s, limit):
    return str(s).replace("\n", " ").replace("\r", " ").strip()[:limit]


async def _send(client, obj):
    try:
        await client.ws.send(json.dumps(obj))
    except Exception:
        pass


async def _broadcast(obj, exclude=None):
    if CLIENTS:
        msg = json.dumps(obj)
        await asyncio.gather(*(
            c.ws.send(msg) for c in CLIENTS.values() if c.id != exclude
        ), return_exceptions=True)


def _roster():
    return {"t": "roster", "players": [
        {"id": c.id, "name": c.name, "pet": c.pet} for c in CLIENTS.values() if c.live]}


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
                # A login_failed closes the socket (return): this client always
                # retries on a fresh connection, so keeping the old one open leaks it.
                name = _clean(m.get("name"), MAX_NAME)
                pw = str(m.get("pw") or "")[:MAX_PW]
                if not name:
                    await _send(client, {"t": "login_failed", "msg": "Name required."})
                    return
                key = name.lower()
                acc = ACCOUNTS.get(key)
                if acc:                                   # existing name -> must match
                    if not _verify(pw, acc):
                        await _send(client, {"t": "login_failed", "msg": "Wrong password for that name."})
                        return
                    name = acc["name"]                    # canonical capitalisation
                else:                                     # new name -> claim it
                    if not pw:
                        await _send(client, {"t": "login_failed", "msg": "Pick a password to claim this name."})
                        return
                    ACCOUNTS[key] = _make_account(name, pw)
                    _save_accounts()
                    LOG.info("registered account %s", name)
                if any(c.live and c.name.lower() == key for c in CLIENTS.values() if c is not client):
                    await _send(client, {"t": "login_failed", "msg": "That name is already online."})
                    return
                client.name = name
                client.pet = m.get("pet") or {}
                client.live = logged_in = True
                await _send(client, {"t": "welcome", "id": client.id, "name": client.name})
                await _push_roster()
                LOG.info("login id=%s name=%s (%d online)", client.id, client.name, len(CLIENTS))

            elif not logged_in:
                await _send(client, {"t": "error", "msg": "Log in first."})

            elif t == "pet":
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
                    out["kind"] = m.get("kind")
                    if t == "invite_resp":
                        out["accept"] = bool(m.get("accept"))
                        if m.get("busy"):           # auto-decline while in a session
                            out["busy"] = True
                await _send(target, out)
    except websockets.ConnectionClosed:
        pass
    finally:
        CLIENTS.pop(client.id, None)
        if logged_in:
            await _push_roster()
        LOG.info("gone  id=%s (%d online)", client.id, len(CLIENTS))


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    LOG.info("tuipet lobby on ws://%s:%d (%d accounts)", HOST, PORT, len(ACCOUNTS))
    async with websockets.serve(handler, HOST, PORT, max_size=MAX_MSG_BYTES):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
