#!/usr/bin/env python3
"""Lobby admin CLI — runs ON the box next to server.py (the key never leaves it).

  admin.py who                     the room right now (lobby + home-screen ghosts)
  admin.py announce "text"         broadcast a 📢 server line to everyone online
  admin.py kick|ban|unban|unmute NAME
  admin.py mute NAME MINUTES
  admin.py tail [N]                last N public feed events (default 20)
  admin.py watch                   follow the feed live (Ctrl-C to stop)

Key: TUIPET_ADMIN_KEY or ./admin.key.  Server: TUIPET_LOBBY_URL or ws://127.0.0.1:8765.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
URI = os.environ.get("TUIPET_LOBBY_URL", "ws://127.0.0.1:8765")
FEED = os.environ.get("TUIPET_FEED", os.path.join(_HERE, "lobby_feed.jsonl"))


def _key():
    k = os.environ.get("TUIPET_ADMIN_KEY", "").strip()
    if k:
        return k
    try:
        return open(os.path.join(_HERE, "admin.key"), encoding="utf-8").read().strip()
    except OSError:
        sys.exit("no admin key (create admin.key beside server.py)")


async def _rpc(payload, timeout=8.0):
    import websockets
    async with websockets.connect(URI, open_timeout=timeout) as ws:
        await ws.send(json.dumps(dict(payload, t="admin", key=_key())))
        deadline = asyncio.get_event_loop().time() + timeout
        while True:                       # the admin conn is a client too: skip the
            left = deadline - asyncio.get_event_loop().time()   # broadcast echo of
            raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, left))  # our own announce
            r = json.loads(raw)
            if r.get("t") in ("admin_ok", "error"):
                return r


def _safe(value):
    import unicodedata
    return "".join(c for c in str(value or "")
                   if unicodedata.category(c) not in ("Cc", "Cf"))


def _fmt(rec):
    rec = {k: _safe(v) if isinstance(v, str) else v for k, v in rec.items()}
    ts, kind = rec.get("ts", "?"), rec.get("kind", "?")
    if kind == "chat":
        return f"{ts}  <{rec.get('name')}> {rec.get('text')}"
    if kind == "announce":
        return f"{ts}  📢 {rec.get('text')}"
    if kind in ("join", "leave"):
        g = " (ghost)" if rec.get("ghost") else ""
        return f"{ts}  {'+' if kind == 'join' else '-'} {rec.get('name')}{g}"
    return f"{ts}  {json.dumps(rec)}"


def cmd_who():
    r = asyncio.run(_rpc({"cmd": "who"}))
    if r.get("t") != "admin_ok":
        sys.exit(f"refused: {r}")
    print(f"{r['online']} online")
    for p in r["roster"]:
        where = "lobby" if p["live"] else "ghost"
        pet = f" — {p['pet']} ({p['stage']})" if p.get("pet") else ""
        print(_safe(f"  [{where}] {p['name']}{pet}"))


def cmd_announce(text):
    r = asyncio.run(_rpc({"cmd": "announce", "text": text}))
    if r.get("t") != "admin_ok":
        sys.exit(f"refused: {r}")
    print(f"announced to {r['sent']} online player(s)")


def _feed_lines():
    try:
        return open(FEED, encoding="utf-8").readlines()
    except OSError:
        return []


def cmd_tail(n=20):
    for ln in _feed_lines()[-n:]:
        try:
            print(_fmt(json.loads(ln)))
        except ValueError:
            pass


def cmd_watch():
    f = None
    initial = True
    print(f"watching {FEED} (Ctrl-C to stop)")
    try:
        while True:
            try:
                stat = os.stat(FEED)
                if f is None:
                    f = open(FEED, encoding="utf-8")
                    if initial:
                        f.seek(0, os.SEEK_END)
                        initial = False
                rotated = (os.fstat(f.fileno()).st_dev, os.fstat(f.fileno()).st_ino) != (stat.st_dev, stat.st_ino)
                if not rotated and stat.st_size < f.tell():
                    f.seek(0)
                for ln in f:
                    try:
                        print(_fmt(json.loads(ln)), flush=True)
                    except ValueError:
                        pass
                if rotated:
                    # Drain the old descriptor before reading the replacement from zero.
                    f.close()
                    f = open(FEED, encoding="utf-8")
                    continue
            except OSError:
                pass
            time.sleep(1.0)
    except KeyboardInterrupt:
        return
    finally:
        if f is not None:
            f.close()


def cmd_moderate(cmd, name, minutes=None):
    payload = {"cmd": cmd, "name": name}
    if minutes is not None:
        payload["minutes"] = minutes
    result = asyncio.run(_rpc(payload))
    if result.get("t") != "admin_ok":
        sys.exit(_safe(f"refused: {result}"))
    print(_safe(f"{cmd}: {name}"))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in ("who", "announce", "tail", "watch", "kick", "mute", "unmute", "ban", "unban"):
        sys.exit(__doc__.strip())
    if args[0] in ("kick", "mute", "unmute", "ban", "unban"):
        if len(args) != (3 if args[0] == "mute" else 2):
            sys.exit("usage: admin.py kick|mute|unmute|ban|unban NAME [MINUTES]")
        cmd_moderate(args[0], args[1], int(args[2]) if len(args) == 3 else None)
    elif args[0] == "who":
        cmd_who()
    elif args[0] == "announce":
        if len(args) < 2 or not args[1].strip():
            sys.exit("usage: admin.py announce \"text\"")
        cmd_announce(" ".join(args[1:]))
    elif args[0] == "tail":
        cmd_tail(int(args[1]) if len(args) > 1 else 20)
    else:
        cmd_watch()
