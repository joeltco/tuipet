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
import time
from collections import deque

import websockets

LOG = logging.getLogger("tuipet.lobby")
HOST = os.environ.get("TUIPET_HOST", "0.0.0.0")  # nosec B104 - lobby server is meant to listen on all interfaces (behind nginx)
PORT = int(os.environ.get("TUIPET_PORT", "8765"))
ACCOUNTS_PATH = os.environ.get(
    "TUIPET_ACCOUNTS",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts.json"))
SAVES_PATH = os.environ.get(
    "TUIPET_SAVES",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves.json"))
BUGS_PATH = os.environ.get(
    "TUIPET_BUGS",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "bugs.jsonl"))
MAX_BUG_TEXT = 2000
MAX_BUGS_PER_CONN = 5           # a real player files one or two, not a firehose
MAX_BUG_FILE = 5 * 1024 * 1024  # stop appending past 5MB -- the disk-fill backstop

# ---- admin channel (key-authed): live feed + announcements ------------------
# The key lives ONLY on the box (admin.key beside server.py, or TUIPET_ADMIN_KEY);
# no key file -> the whole admin channel is disabled.  PUBLIC room events (chat,
# joins/leaves, announcements) append to the feed for offline reading -- PMs are
# private and never logged.
FEED_PATH = os.environ.get(
    "TUIPET_FEED",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "lobby_feed.jsonl"))
ADMIN_KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin.key")
MAX_ANNOUNCE = 300
MAX_FEED = 2 * 1024 * 1024      # rotate past 2MB: feed -> feed.1 (one generation kept)


def _admin_key():
    k = os.environ.get("TUIPET_ADMIN_KEY", "")
    if k:
        return k.strip()
    try:
        return open(ADMIN_KEY_PATH).read().strip()
    except OSError:
        return ""

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


# ---- cloud saves (name.lower() -> full pet save dict incl. _saved_at) --------
def _load_saves():
    try:
        return json.load(open(SAVES_PATH))
    except (OSError, ValueError):
        return {}


SAVES = _load_saves()
_saves_lock = asyncio.Lock()


_STAGES = {"Egg", "Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"}


def _valid_save(save):
    """Vocabulary check (2026-07-04 'Child' incident): an OUTDATED client once
    pushed a rebuild-era save (stage 'Child', empty name) and last-write-wins
    served it to every device.  The server now refuses formats it doesn't
    speak; clients also reject on pull, but the cloud must not carry them."""
    if not isinstance(save, dict):
        return False
    stage = save.get("stage")
    if stage not in _STAGES:
        return False
    if stage != "Egg" and not (save.get("name") or "").strip():
        return False
    return True


async def _store_save(key, save):
    """Last-write-wins by the client-stamped _saved_at: only newer saves land.
    Returns True when the save was stored (the client is told via the ack)."""
    if not _valid_save(save):
        return False
    incoming = save.get("_saved_at") or 0
    have = (SAVES.get(key) or {}).get("_saved_at") or 0
    if incoming < have:
        return False                              # stale push -> ignore (a newer device won)
    SAVES[key] = save
    async with _saves_lock:
        tmp = SAVES_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(SAVES, f)
        os.replace(tmp, SAVES_PATH)               # atomic
    return True


# ---- session leases (the two-device fork, 2026-07-04; boot-stamped 2026-07-05) --
# A phone left RUNNING keeps autosave-pushing its own fork of the pet with ever
# NEWER wall-clock stamps, so a fresh desktop session loses every quit to the
# background device ("things arent getting saved between quits").  Only the
# holder of an account's lease may push saves.  The lease belongs to the most
# recent APP LAUNCH, not the most recent connection: clients stamp their login
# with `boot` (wall-clock at process start), and a login whose boot is OLDER
# than the holder's is denied the lease.  Without the stamp, a backgrounded
# phone re-took the lease on every wifi-blip reconnect and the fork reopened.
# Only sync_only logins take a lease — a live lobby login never pushes saves,
# and letting it bump the serial staled its own device's autosync mid-session.
LEASES: dict[str, tuple[float, int]] = {}     # key -> (boot stamp, serial)


def _take_lease(client, key, boot):
    cur = LEASES.get(key)
    # boot 0.0 = a legacy client with no stamp: it keeps last-login-wins (and
    # stores 0.0, so any stamped login can take over) — otherwise un-upgraded
    # devices would be silently locked out of saving until their next update
    if cur and boot and boot < cur[0]:
        client.lease = None            # an older app launch may not push saves
        return
    serial = (cur[1] if cur else 0) + 1
    LEASES[key] = (boot, serial)
    client.lease = serial


def _lease_ok(client, key):
    cur = LEASES.get(key)
    return cur is not None and cur[1] == getattr(client, "lease", None)


# The room's recent history (message audit 2026-07-06): the server kept no
# chat log, so backing out of the lobby and re-entering greeted a VOID -- a
# fresh client's pane filled only with what came after.  A live login now
# replays this rolling window so re-entry rejoins the conversation.
CHAT_BACKLOG: deque = deque(maxlen=30)


class Client:
    __slots__ = ("id", "ws", "name", "pet", "live", "lease", "logged", "boot",
                 "bugs_sent")

    def __init__(self, ws):
        self.id = next(_ids)
        self.ws = ws
        self.name = f"guest{self.id}"
        self.pet = {}
        self.live = False
        self.lease = None
        self.logged = False
        self.boot = 0.0
        self.bugs_sent = 0


CLIENTS: dict[int, Client] = {}


def _clean(s, limit):
    return str(s).replace("\n", " ").replace("\r", " ").strip()[:limit]



# ---- monthly ladder (2026-07-14): online PvP wins, fresh race every month ----
# Both sides of a bout auto-report; a win only lands when the two stories agree
# (a lone client can't forge a ladder), and a pair of friends can only credit
# LADDER_PAIR_CAP wins per hour (the KO6 lesson: any player-reported counter
# WILL be farmed).  Past-season podium finishers claim a bits award in-client.
LADDER_PATH = os.environ.get(
    "TUIPET_LADDER",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "ladder.json"))
LADDER_PAYOUT = {1: 25000, 2: 10000, 3: 5000}
LADDER_PAIR_CAP = 3
LADDER_CONFIRM_S = 90.0


def _load_ladder():
    try:
        d = json.load(open(LADDER_PATH))
        return {"seasons": dict(d.get("seasons", {})),
                "claimed": dict(d.get("claimed", {}))}
    except (OSError, ValueError):
        return {"seasons": {}, "claimed": {}}


LADDER = _load_ladder()
_ladder_pending = {}      # (winner, loser) -> ts of the WINNER's report
_ladder_confirm = {}      # (winner, loser) -> ts of the LOSER's agreeing report
_ladder_pair_hour = {}    # (a, b, "YYYY-MM-DDTHH") -> credits this hour


def _save_ladder():
    try:
        tmp = LADDER_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(LADDER, f)
        os.replace(tmp, LADDER_PATH)
    except OSError:
        LOG.warning("ladder: disk refused %s", LADDER_PATH)


def _season_key(now=None):
    return time.strftime("%Y-%m", time.gmtime(now))


def _season_days_left(now=None):
    import calendar
    tm = time.gmtime(now)
    return calendar.monthrange(tm.tm_year, tm.tm_mon)[1] - tm.tm_mday


def _ladder_credit(winner, loser, now=None):
    now = time.time() if now is None else now
    pair = tuple(sorted((winner, loser))) + (time.strftime("%Y-%m-%dT%H", time.gmtime(now)),)
    if _ladder_pair_hour.get(pair, 0) >= LADDER_PAIR_CAP:
        return False
    _ladder_pair_hour[pair] = _ladder_pair_hour.get(pair, 0) + 1
    if len(_ladder_pair_hour) > 2048:            # old hours never come back
        _ladder_pair_hour.clear()
    season = LADDER["seasons"].setdefault(_season_key(now), {})
    season[winner] = season.get(winner, 0) + 1
    _save_ladder()
    return True


def _ladder_report(name, won, opp, now=None):
    """Half of a match report; the other half confirms it within the window."""
    now = time.time() if now is None else now
    if not opp or opp == name:
        return
    key = (name, opp) if won else (opp, name)    # always (winner, loser)
    mine = _ladder_pending if won else _ladder_confirm
    theirs = _ladder_confirm if won else _ladder_pending
    ts = theirs.get(key)
    if ts is not None and now - ts <= LADDER_CONFIRM_S:
        theirs.pop(key, None)
        _ladder_credit(key[0], key[1], now)
        return
    mine[key] = now
    if len(mine) > 512:                          # shed stale halves, oldest first
        for k in sorted(mine, key=mine.get)[:256]:
            mine.pop(k, None)


def _ladder_award(name, now=None):
    """The newest PAST season where this player podiumed and hasn't claimed."""
    now = time.time() if now is None else now
    cur = _season_key(now)
    for season in sorted(LADDER["seasons"], reverse=True):
        if season >= cur or name in LADDER["claimed"].get(season, []):
            continue
        top = sorted(LADDER["seasons"][season].items(), key=lambda kv: (-kv[1], kv[0]))
        for rank, (who, wins) in enumerate(top[:3], start=1):
            if who == name:
                return {"season": season, "rank": rank, "wins": wins,
                        "bits": LADDER_PAYOUT[rank]}
    return None


def _ladder_view(name, now=None):
    now = time.time() if now is None else now
    season = _season_key(now)
    table = LADDER["seasons"].get(season, {})
    top = sorted(table.items(), key=lambda kv: (-kv[1], kv[0]))
    you = next((i + 1 for i, (who, _w) in enumerate(top) if who == name), 0)
    return {"t": "ladder", "season": season, "days_left": _season_days_left(now),
            "top": top[:10], "you": [you, table.get(name, 0)],
            "award": _ladder_award(name, now)}


def _ladder_claim(name, season):
    a = _ladder_award(name)
    if a and a["season"] == season:
        LADDER["claimed"].setdefault(season, []).append(name)
        _save_ladder()


async def _send(client, obj):
    try:
        await client.ws.send(json.dumps(obj))
    except Exception:
        pass


async def _close_quiet(ws):
    """Close an evicted session's socket without letting a dead peer's close
    handshake stall the login that displaced it."""
    try:
        await ws.close()
    except Exception:
        pass


async def _broadcast(obj, exclude=None):
    if CLIENTS:
        msg = json.dumps(obj)
        await asyncio.gather(*(
            c.ws.send(msg) for c in CLIENTS.values() if c.id != exclude
        ), return_exceptions=True)


def _roster():
    """Everyone ONLINE, not just the lobby room (presence 2026-07-05): lobby
    logins are `live` (chat/invitable); a player whose app merely holds its
    sync connection appears as a playing ghost (live false, PM-able).  One
    entry per account -- the live connection wins the slot."""
    by_key = {}
    for c in CLIENTS.values():
        if not c.logged:
            continue
        key = c.name.lower()
        cur = by_key.get(key)
        if cur is None or (c.live and not cur.live):
            by_key[key] = c
    return {"t": "roster", "players": [
        {"id": c.id, "name": c.name, "pet": c.pet, "live": c.live}
        for c in by_key.values()]}


def _account_conns(name):
    """Every logged-in connection of an account (the lobby login AND the
    home-screen sync ghost) -- a PM lands on all of them."""
    key = name.lower()
    return [c for c in CLIENTS.values() if c.logged and c.name.lower() == key]


async def _push_roster():
    await _broadcast(_roster())


async def _handle_bug(client, m):
    """Append an anonymous bug report to bugs.jsonl and ack it (no login
    required -- a player hits a bug before they ever open the lobby).
    Abuse-capped (audit 2026-07-10): a few reports per connection, only the
    known pet fields stored, and the file stops growing past a hard size."""
    client.bugs_sent += 1
    text = (str(m.get("text") or "")).strip()[:MAX_BUG_TEXT]
    if not text or client.bugs_sent > MAX_BUGS_PER_CONN:
        await _send(client, {"t": "bug_ok", "ok": False})
        return
    pet = m.get("pet") if isinstance(m.get("pet"), dict) else {}
    pet = {k: (pet[k] if isinstance(pet[k], int) else str(pet[k])[:24])
           for k in ("num", "name", "stage", "gen") if k in pet}
    rec = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "from": (str(m.get("name") or "").strip() or "anon")[:MAX_NAME],
        "version": str(m.get("version") or "")[:24],
        "platform": str(m.get("platform") or "")[:60],
        "pet": pet,
        "text": text,
    }
    ok = True
    try:
        if os.path.exists(BUGS_PATH) and os.path.getsize(BUGS_PATH) > MAX_BUG_FILE:
            ok = False                       # the disk-fill backstop
        else:
            with open(BUGS_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
    except OSError:
        ok = False
    LOG.info("bug from %s (%d chars) ok=%s", rec["from"], len(text), ok)
    await _send(client, {"t": "bug_ok", "ok": ok})


def _feed(kind, **kw):
    """Append one PUBLIC room event to the live feed (best-effort)."""
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()), "kind": kind}
    rec.update(kw)
    try:
        if os.path.exists(FEED_PATH) and os.path.getsize(FEED_PATH) > MAX_FEED:
            os.replace(FEED_PATH, FEED_PATH + ".1")
        with open(FEED_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass


async def _handle_admin(client, m):
    """Key-authed admin ops (no login): `who` reads the room, `announce`
    broadcasts a server line to every connection (lobby + home-screen ghosts)."""
    key = _admin_key()
    if not key or not hmac.compare_digest(str(m.get("key") or ""), key):
        LOG.info("admin REFUSED conn=%s cmd=%r", client.id, m.get("cmd"))
        await _send(client, {"t": "error", "msg": "Nope."})
        return
    cmd = m.get("cmd")
    if cmd == "who":
        roster = [{"name": c.name, "live": c.live,
                   "pet": (c.pet or {}).get("name", ""),
                   "stage": (c.pet or {}).get("stage", "")}
                  for c in CLIENTS.values() if c.logged]
        await _send(client, {"t": "admin_ok", "cmd": "who",
                             "online": len(roster), "roster": roster})
    elif cmd == "announce":
        text = _clean(m.get("text"), MAX_ANNOUNCE)
        if not text:
            await _send(client, {"t": "admin_ok", "cmd": "announce", "sent": 0})
            return
        out = {"t": "announce", "text": text}
        CHAT_BACKLOG.append(out)              # late joiners see it on entry
        await _broadcast(out)
        _feed("announce", text=text)
        LOG.info("announce (%d chars) to %d conns", len(text), len(CLIENTS))
        await _send(client, {"t": "admin_ok", "cmd": "announce",
                             "sent": sum(1 for c in CLIENTS.values() if c.logged)})
    else:
        await _send(client, {"t": "error", "msg": "Unknown admin cmd."})


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
                    # pbkdf2 off the event loop: 100k iterations is tens of ms,
                    # and the loop is the whole relay — a login flood must not
                    # freeze every live chat/battle session
                    if not await asyncio.to_thread(_verify, pw, acc):
                        await asyncio.sleep(0.4)          # slow down brute force
                        await _send(client, {"t": "login_failed", "msg": "Wrong password for that name."})
                        return
                    name = acc["name"]                    # canonical capitalisation
                else:                                     # new name -> claim it
                    if not pw:
                        await _send(client, {"t": "login_failed", "msg": "Pick a password to claim this name."})
                        return
                    ACCOUNTS[key] = await asyncio.to_thread(_make_account, name, pw)
                    _save_accounts()
                    LOG.info("registered account %s", name)
                # A sync_only connection just pulls/pushes the cloud save; it never
                # joins the live roster, so it can coexist with a lobby login on the
                # same account (and won't trip the live-session handling below).
                sync_only = bool(m.get("sync_only"))
                try:
                    boot = float(m.get("boot") or 0)
                except (TypeError, ValueError):
                    boot = 0.0
                if not sync_only:
                    # The room slot follows the save-lease doctrine (message
                    # audit 2026-07-06): the password already verified, so an
                    # "already online" conflict is either OUR OWN stale session
                    # (a back-out/re-enter racing a slow close, or a half-dead
                    # socket the ping reaper won't fell for ~40s) or an older
                    # app launch.  The newest launch WINS the room -- refusing
                    # it locked the account out of its own lobby.
                    stale = [c for c in CLIENTS.values()
                             if c is not client and c.live and c.name.lower() == key]
                    if any(c.boot > boot for c in stale):
                        await _send(client, {"t": "login_failed",
                                             "msg": "Signed in on a newer session."})
                        return
                    for c in stale:
                        CLIENTS.pop(c.id, None)
                        await _send(c, {"t": "error", "msg": "Signed in from a newer session."})
                        asyncio.ensure_future(_close_quiet(c.ws))
                        LOG.info("evicted stale session id=%s name=%s", c.id, c.name)
                    client.boot = boot
                client.name = name
                client.pet = m.get("pet") or {}
                client.live = not sync_only
                if sync_only:                     # the newest APP LAUNCH owns the saves
                    _take_lease(client, key, boot)
                logged_in = True
                client.logged = True
                await _send(client, {"t": "welcome", "id": client.id, "name": client.name,
                                     "save": SAVES.get(key)})       # cloud save (or null) for cross-device load
                if not sync_only:
                    for f in CHAT_BACKLOG:        # rejoin the conversation, not a void
                        await _send(client, f)
                await _push_roster()          # sync ghosts show as "playing" (presence 2026-07-05)
                LOG.info("login id=%s name=%s sync_only=%s (%d online)",
                         client.id, client.name, sync_only, len(CLIENTS))
                _feed("join", name=client.name, ghost=sync_only)

            elif t == "bug":
                await _handle_bug(client, m)

            elif t == "admin":
                await _handle_admin(client, m)

            elif not logged_in:
                await _send(client, {"t": "error", "msg": "Log in first."})

            elif t == "pet":
                client.pet = m.get("pet") or {}
                if client.live:
                    await _push_roster()

            elif t == "save":
                key = client.name.lower()
                ok = False
                if _lease_ok(client, key):
                    ok = await _store_save(key, m.get("save"))
                else:                             # a newer session took over
                    LOG.info("stale-lease save dropped: %s conn=%s", client.name, client.id)
                # the ack makes quit-pushes honest: a dropped push must not
                # report True back to the quitting client
                await _send(client, {"t": "saved", "ok": ok})

            elif t == "ladder_report":
                _ladder_report(client.name, bool(m.get("won")), str(m.get("opp") or "")[:24])

            elif t == "ladder_get":
                await _send(client, _ladder_view(client.name))

            elif t == "ladder_claim":
                _ladder_claim(client.name, str(m.get("season") or ""))

            elif t == "chat":
                text = _clean(m.get("text"), MAX_CHAT)
                if text and client.live:          # a sync_only ghost isn't in the room
                    out = {"t": "chat", "from_id": client.id,
                           "from_name": client.name, "text": text}
                    CHAT_BACKLOG.append(out)      # the re-entry replay window
                    await _broadcast(out)
                    _feed("chat", name=client.name, text=text)

            elif t == "pm":
                # a private message reaches EVERY connection of the target
                # account -- their lobby login and the sync ghost their app
                # holds at the home screen (the alert channel; 2026-07-05)
                text = _clean(m.get("text"), MAX_CHAT)
                target = CLIENTS.get(m.get("to"))
                if not text:
                    continue
                if target is None or not target.logged:
                    await _send(client, {"t": "error", "msg": "That player just left."})
                    continue
                out = {"t": "pm", "from_id": client.id,
                       "from_name": client.name, "text": text}
                for c in _account_conns(target.name):
                    await _send(c, out)
                await _send(client, {"t": "pm_ok", "to_name": target.name, "text": text})

            elif t in ("invite", "invite_resp", "relay"):
                if not client.live:               # sessions are for roster members only
                    continue
                target = CLIENTS.get(m.get("to"))
                if target is None or not target.live:
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
            _feed("leave", name=client.name, ghost=not client.live)
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
