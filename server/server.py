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
import copy
import functools
import uuid
import hashlib
import hmac
import itertools
import json
import logging
import math
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
HOLDERS_PATH = os.environ.get(
    "TUIPET_HOLDERS",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "holders.json"))
# account -> wall-clock of its last Erase all data (saves call #27 = A,
# Joel 2026-10-15): a save whose pet was BORN before it is the erased pet
# coming back from a device that was still signed in -- refused, never stored
ERASE_CLOCK_SLACK = 6 * 3600.0  # a device clock this far behind still hatches fresh
WIPED_PATH = os.environ.get(
    "TUIPET_WIPED",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiped.json"))
MAX_BUG_TEXT = 2000
MAX_BUGS_PER_CONN = 5           # a real player files one or two, not a firehose
MAX_BUGS_PER_IP = 6             # ...and a reconnect must not hand out a fresh five
BUG_IP_WINDOW = 3600.0          # seconds the per-IP budget covers
MAX_BUG_IPS = 512               # tracked IPs before expired ones are swept
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
        return open(ADMIN_KEY_PATH, encoding="utf-8").read().strip()
    except OSError:
        return ""

MAX_CLIENTS = 200
MAX_NAME = 24
MAX_PW = 128
MAX_CHAT = 400
MAX_MSG_BYTES = 64 * 1024
PBKDF2_ITERS = 100_000

_ids = itertools.count(1)


def _durable_json(path, value):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    for target in (path + ".bak", path):
        with open(target + ".tmp", "w", encoding="utf-8") as f:
            json.dump(value, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(target + ".tmp", target)
        fd = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _load_mapping(path):
    # Backup is written first, so prefer it after an interrupted mirror write.
    found = False
    for target in (path + ".bak", path):
        try:
            with open(target, encoding="utf-8") as f:
                found = True
                value = json.load(f)
            if not isinstance(value, dict):
                raise ValueError("expected object")
            return value
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            found = True
            LOG.exception("invalid snapshot %s", target)
    if found:
        raise RuntimeError("Restore unreadable ledger: " + path)
    return {}


# ---- accounts (name -> {name, salt, hash}, keyed by lowercased name) --------
def _load_accounts():
    return _load_mapping(ACCOUNTS_PATH)


ACCOUNTS = _load_accounts()


def _save_accounts():
    _durable_json(ACCOUNTS_PATH, ACCOUNTS)


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, PBKDF2_ITERS).hex()


def _make_account(name, pw):
    salt = os.urandom(16)
    return {"name": name, "salt": salt.hex(), "hash": _hash(pw, salt)}


def _verify(pw, acc):
    return hmac.compare_digest(_hash(pw, bytes.fromhex(acc["salt"])), acc["hash"])


# ---- the cartridge HOLDER ledger (name.lower() -> {device,label,ts}) --------
# One pet, checked out to ONE device (2026-07-29, the GPD fork war): only the
# holder device's pushes land; any synced device may pull.  The first device
# to sync an unheld account claims it (migration); "take" moves it on the
# player's explicit yes.  Legacy clients (no device id) can pull but never
# push to a held account -- they predate the question.
def _load_holders():
    try:
        return json.load(open(HOLDERS_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


HOLDERS = _load_holders()


def _load_wiped():
    try:
        with open(WIPED_PATH, encoding="utf-8") as f:
            d = json.load(f)
        return {str(k): float(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except Exception:
        return {}


WIPED = _load_wiped()


def _save_wiped():
    try:
        tmp = WIPED_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(WIPED, f)
        os.replace(tmp, WIPED_PATH)
    except OSError:
        LOG.warning("wiped: disk refused %s", WIPED_PATH)


def _erased_pet(key, save):
    """Is this save the pet the account ERASED?  Born before the erase (a
    pre-0.6.20 save carries no birth stamp: it predates every erase too)."""
    at = WIPED.get(key)
    if at is None:
        return False
    try:
        born = float((save or {}).get("born_at") or 0)
    except (TypeError, ValueError):
        born = 0.0
    return born < at - ERASE_CLOCK_SLACK


def _save_holders():
    try:
        tmp = HOLDERS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(HOLDERS, f)
        os.replace(tmp, HOLDERS_PATH)
    except OSError:
        LOG.warning("holders.json write failed")


def _claim_holder(key, device, label):
    HOLDERS[key] = {"device": device, "label": label or "another device",
                    "ts": time.time()}
    _save_holders()
    LOG.info("holder: %s -> %s (%s)", key, device[:8], label)


def _holder_view(key):
    h = HOLDERS.get(key)
    return {"device": h["device"], "label": h.get("label", "")} if h else None


# ---- cloud saves (name.lower() -> full pet save dict incl. _saved_at) --------
def _load_saves():
    return _load_mapping(SAVES_PATH)


SAVES = _load_saves()

# ---- SAVES pruning policy (2026-07-18, closing the old backlog item) --------
# A cloud save untouched for a YEAR is dropped: the account itself stays
# (name + password are identity, and accounts.json is tiny), and the pet
# still lives on its own device -- only the stale cloud copy goes.  Saves
# that predate the _srv_at stamp get stamped on first sight, so nothing
# ages out until a real year of silence has passed.
SAVE_RETENTION_S = 365 * 86400


def _prune_saves(now=None):
    now = time.time() if now is None else now
    changed = False
    for k, sv in list(SAVES.items()):
        if not isinstance(sv, dict):
            del SAVES[k]
            changed = True
            continue
        ts = sv.get("_srv_at")
        if not ts:
            sv["_srv_at"] = now              # grace-stamp the pre-stamp era
            changed = True
            continue
        try:
            stale = now - float(ts) > SAVE_RETENTION_S
        except (TypeError, ValueError):
            sv["_srv_at"] = now
            changed = True
            continue
        if stale:
            del SAVES[k]
            changed = True
    if changed:
        try:
            _durable_json(SAVES_PATH, SAVES)
        except OSError:
            LOG.warning("saves prune: disk refused %s", SAVES_PATH)


_prune_saves()                               # once per process start
_saves_lock = asyncio.Lock()


# ---- offline PM queue (store-and-forward, 2026-07-12) ------------------------
# A PM to an account with no LIVE lobby session is held here and delivered on
# that account's next lobby login, so messaging a player who has stepped away is
# not lost.  Persisted so a server restart keeps the backlog.
PENDING_PATH = os.environ.get(
    "TUIPET_PENDING",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "pending_pms.json"))
MAX_PENDING_PER_ACCT = 50          # newest kept; a flooded queue sheds its oldest


def _load_pending():
    try:
        return json.load(open(PENDING_PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


PENDING = _load_pending()
_pending_lock = asyncio.Lock()


async def _save_pending():
    async with _pending_lock:
        tmp = PENDING_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(PENDING, f)
        os.replace(tmp, PENDING_PATH)


async def _queue_pm(key, from_name, text):
    q = PENDING.setdefault(key, [])
    q.append({"from_name": from_name, "text": text,
              "ts": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())})
    del q[:-MAX_PENDING_PER_ACCT]
    await _save_pending()


async def _flush_pending(client, key):
    """Deliver-then-delete (server audit 2026-07-18): the old pop-then-send
    ran the sends through _send's swallow-everything, so a socket dying
    mid-flush persisted an EMPTIED queue -- store-and-forward lost mail
    exactly when connections were worst.  Now each PM leaves the queue only
    after its send really completed; a dead socket keeps the rest queued."""
    q = PENDING.get(key)
    if not q:
        return
    sent = 0
    for rec in list(q):
        try:
            await client.ws.send(json.dumps(
                {"t": "pm", "from_id": 0,
                 "from_name": rec.get("from_name", "?"),
                 "text": rec.get("text", "")}))
        except Exception:
            break                          # died mid-flush: the rest waits
        sent += 1
    if not sent:
        return
    del q[:sent]
    if not q:
        PENDING.pop(key, None)
    await _save_pending()
    LOG.info("flushed %d queued pm(s) to %s", sent, client.name)


_STAGES = {"Egg", "Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"}


def _valid_save(save):
    """Vocabulary check (2026-07-04 'Child' incident): an OUTDATED client once
    pushed a rebuild-era save (stage 'Child', empty name) and last-write-wins
    served it to every device.  The server now refuses formats it doesn't
    speak; clients also reject on pull, but the cloud must not carry them."""
    if not isinstance(save, dict):
        return False
    stage = save.get("stage")
    if not isinstance(stage, str) or stage not in _STAGES:
        return False
    # sync audit 2026-10-14: hostile JSON types get a verdict, not a disconnect.
    if stage != "Egg" and (not isinstance(save.get("name"), str)
                           or not save["name"].strip()):
        return False
    return True


SAVE_STAMP_SLACK = 120.0   # max seconds a client _saved_at may run AHEAD of us


async def _store_save(key, save):
    """Store the lease-holder's save.  Only the lease holder ever reaches
    here, and pushes arrive causally ordered per connection, so arrival
    order IS save order -- the old client-stamp compare (`incoming < have`)
    could only ever reject the legitimate holder, and did exactly that when
    another device's fast wall-clock had stamped the stored save in the
    FUTURE (skew audit 2026-07-18: real cross-device progress silently
    dropped).  The client stamp is kept for the CLIENT-side compares but
    clamped so a fast clock can't poison them more than SLACK ahead.
    Returns True when the save was stored."""
    if not _valid_save(save):
        return False
    now = time.time()
    try:
        if float(save.get("_saved_at") or 0) > now + SAVE_STAMP_SLACK:
            save["_saved_at"] = now               # a runaway clock is clamped to ours
    except (TypeError, ValueError):
        save["_saved_at"] = now
    save["_srv_at"] = now                         # our own receipt stamp rides along
    async with _saves_lock:
        updated = dict(SAVES, **{key: save})
        try:
            _durable_json(SAVES_PATH, updated)
        except OSError:
            SAVES.clear()
            SAVES.update(_load_saves())
            raise
        SAVES[key] = save
    return True


async def _wipe_account(key):
    """Clear an account's cloud save and free its cartridge (the client's
    Erase all data).  Returns whether a save existed."""
    # sync audit 2026-10-14: connected uploaders must not resurrect a wiped save.
    LEASES.pop(key, None)
    for c in CLIENTS.values():
        if c.name.lower() == key:
            c.lease = None
    WIPED[key] = time.time()             # saves call #27 = A: the erased pet stays erased
    _save_wiped()
    had = SAVES.pop(key, None) is not None
    if had:
        async with _saves_lock:
            _durable_json(SAVES_PATH, SAVES)
    if HOLDERS.pop(key, None) is not None:
        _save_holders()
    return had


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
BOOT_SEEN: dict[str, dict[float, float]] = {}  # key -> {boot: OUR first-seen time}
MAX_SEEN_BOOTS = 8                             # per-account launch memory (pruned)


def _take_lease(client, key, boot):
    cur = LEASES.get(key)
    # Seniority is decided by OUR first-seen time for each launch stamp, not
    # by comparing the devices' own wall-clocks (skew audit 2026-07-18: a
    # device with a lagging clock that launched LATER presented a smaller
    # boot and was wrongly denied the lease).  The boot value itself is just
    # the launch's identity; a reconnect of the same launch keeps its
    # original seniority, so a backgrounded phone still can't re-take the
    # lease on a wifi blip.
    seen = BOOT_SEEN.setdefault(key, {})
    if boot and boot not in seen:
        seen[boot] = time.time()
        while len(seen) > MAX_SEEN_BOOTS:
            del seen[min(seen, key=seen.get)]
    # boot 0.0 = a legacy client with no stamp: it keeps last-login-wins (and
    # stores 0.0, so any stamped login can take over) — otherwise un-upgraded
    # devices would be silently locked out of saving until their next update
    if cur and boot and cur[0] and cur[0] != boot \
            and seen.get(boot, 0) < seen.get(cur[0], 0):
        client.lease = None            # an older app LAUNCH may not push saves
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
MODERATION_PATH = os.environ.get("TUIPET_MODERATION", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "moderation.json"))
MODERATION = _load_mapping(MODERATION_PATH)


def _moderated(name, banned=False):
    record = MODERATION.get(name.lower(), {})
    return bool(record.get("ban")) if banned else record.get("mute", 0) > time.time()


def _new_name_ok(name):
    return (bool(name) and any(c.isalnum() for c in name)
            and name.lower() not in ("admin", "server", "system", "tuipet", "mod")
            and not name.startswith(("📢", "✉", "—", "!", "→")))



class Client:
    __slots__ = ("id", "ws", "name", "pet", "live", "lease", "logged", "boot",
                 "bugs_sent", "room", "device", "dlabel")

    def __init__(self, ws):
        self.id = str(next(_ids))
        self.ws = ws
        self.name = f"guest{self.id}"
        self.pet = {}
        self.live = False
        self.lease = None
        self.logged = False
        self.boot = 0.0
        self.bugs_sent = 0
        self.room = None       # None = the main lobby; else a room code (str)
        self.device = ""       # install identity (cartridge holder routing)
        self.dlabel = ""       # its human name for the take-question


CLIENTS: dict[str, Client] = {}

# Per-IP bug budget.  MAX_BUGS_PER_CONN counts on ONE socket, so one connection
# per report walked straight through it: 2026-10-01 took 46 reports in 46
# seconds, every one on its own connection with bugs_sent==1.  nginx hands us
# the real peer in X-Real-IP; ws.remote_address is always the proxy (127.0.0.1),
# so keying on that would have pooled every player on earth into one budget.
_BUG_IPS: dict[str, deque[float]] = {}


def _peer_ip(ws):
    req = getattr(ws, "request", None)
    if req is not None:
        for h in ("X-Real-IP", "X-Forwarded-For"):
            v = req.headers.get(h)
            if v:
                return v.split(",")[0].strip()[:64]
    addr = getattr(ws, "remote_address", None)
    return str(addr[0])[:64] if addr else "?"


def _bug_budget_ok(ip):
    """True if this IP may file one more report, charging it when it may."""
    now = time.monotonic()
    if len(_BUG_IPS) > MAX_BUG_IPS:
        for k in [k for k, v in _BUG_IPS.items()
                  if not v or now - v[-1] > BUG_IP_WINDOW]:
            del _BUG_IPS[k]
    hits = _BUG_IPS.setdefault(ip, deque())
    while hits and now - hits[0] > BUG_IP_WINDOW:
        hits.popleft()
    if len(hits) >= MAX_BUGS_PER_IP:
        return False
    hits.append(now)
    return True


def _clean(s, limit):
    # None must clean to "" -- str(None) minted the literal name "None"
    # (a raid client with no cached account logged in as it)
    import unicodedata
    return "".join(c for c in str(s or "")
                   if unicodedata.category(c) not in ("Cc", "Cf")).strip()[:limit]


def _clamp_pet(p):
    """Bound an UNTRUSTED presence card to the fields clients actually read
    (lobbyscreen._card: name/stage/num/attr/title).  The card was stored and
    REBROADCAST verbatim: a handful of crafted 64KB cards pushed every roster
    frame past the clients' 256KB read cap, so one bad actor killed the whole
    room with 1009 closes (MED audit 2026-07-19)."""
    if not isinstance(p, dict):
        return {}
    out = {}
    for k in ("name", "stage", "attr", "title"):
        v = p.get(k)
        if isinstance(v, (str, int, float)) and not isinstance(v, bool):
            s = _clean(v, MAX_NAME)
            if s:
                out[k] = s
    try:
        out["num"] = max(0, min(int(p.get("num") or 0), 10 ** 6))
    except (TypeError, ValueError):
        out["num"] = 0
    return out



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
SMOKE_PREFIX = "smk"      # tools/pvp_smoke.py account tag -- test bouts are real
#                           lobby traffic but must never rank (Joel 2026-07-28:
#                           11 smoke rigs sat on the live season the day the
#                           Facebook ads went out)


def _load_ladder():
    try:
        d = json.load(open(LADDER_PATH, encoding="utf-8"))
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
        with open(tmp, "w", encoding="utf-8") as f:
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
    if len(_ladder_pair_hour) > 2048:
        # shed STALE hours only -- .clear() also wiped the CURRENT hour's
        # counts, re-opening the pair cap mid-hour (server audit 2026-07-18)
        hour = time.strftime("%Y-%m-%dT%H", time.gmtime(now))
        for k in [k for k in _ladder_pair_hour if k[2] != hour]:
            del _ladder_pair_hour[k]
    season = LADDER["seasons"].setdefault(_season_key(now), {})
    season[winner] = season.get(winner, 0) + 1
    _save_ladder()
    return True


def _ladder_report(name, won, opp, now=None):
    """Half of a match report; the other half confirms it within the window."""
    now = time.time() if now is None else now
    if not opp or opp == name:
        return
    if (name.lower().startswith(SMOKE_PREFIX)
            or opp.lower().startswith(SMOKE_PREFIX)):
        return                    # smoke rigs never touch the season
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
    """Mark the award claimed and RETURN the server-confirmed reward, the
    raid_claim pattern (server audit 2026-07-18: the old fire-and-forget
    left the client self-paying off the view, so a lost claim or a second
    device could re-collect)."""
    a = _ladder_award(name)
    if not a or a["season"] != season:
        return {"t": "ladder_reward", "ok": False}
    LADDER["claimed"].setdefault(season, []).append(name)
    _save_ladder()
    return {"t": "ladder_reward", "ok": True, "season": a["season"],
            "rank": a["rank"], "wins": a["wins"], "bits": a["bits"]}


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


# ---- password rooms (2026-07-14) ---------------------------------------------
# A room is just a shared secret phrase: everyone who types the same phrase
# lands in the same private scope (chat + roster; battles/jogress follow the
# roster naturally).  No room registry, no membership state, no cleanup -- the
# room "exists" exactly while clients carry its code.  PMs and 📢 announcements
# stay global; invites/relays are id-addressed and unaffected.
MAX_ROOM = 32


def _room_code(raw):
    """Normalize a room phrase: trimmed, inner whitespace collapsed, lowercased
    (so 'Sea  Food' and 'sea food' meet).  Empty -> None (the main lobby)."""
    code = " ".join(str(raw or "").split()).lower()[:MAX_ROOM]
    return code or None


async def _broadcast_room(room, obj, exclude=None):
    """Broadcast to one scope: a room's members, or (room=None) the main lobby
    (which keeps including sync ghosts, exactly like the old global cast --
    their client ignores chat, and their PM channel is separate)."""
    targets = [c for c in CLIENTS.values()
               if c.id != exclude and c.room == room]
    if targets:
        msg = json.dumps(obj)
        await asyncio.gather(*(c.ws.send(msg) for c in targets),
                             return_exceptions=True)


def _roster(room=None):
    """Everyone ONLINE in the given scope (presence 2026-07-05): lobby logins
    are `live` (chat/invitable); a player whose app merely holds its sync
    connection appears as a playing ghost (live false, PM-able).  One entry
    per account -- the live connection wins the slot.  Ghosts never join a
    room, so they show only in the main lobby (rooms 2026-07-14)."""
    by_key = {}
    for c in CLIENTS.values():
        if not c.logged or c.room != room:
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
    """Each connection gets ITS scope's roster (per-room since 2026-07-14)."""
    for room in {c.room for c in CLIENTS.values()}:
        await _broadcast_room(room, _roster(room))


async def _handle_bug(client, m):
    """Append an anonymous bug report to bugs.jsonl and ack it (no login
    required -- a player hits a bug before they ever open the lobby).
    Abuse-capped (audit 2026-07-10): a few reports per connection, only the
    known pet fields stored, and the file stops growing past a hard size.
    Also per-IP across reconnects (2026-10-01), which is the cap that bites."""
    client.bugs_sent += 1
    text = (str(m.get("text") or "")).strip()[:MAX_BUG_TEXT]
    if not text or client.bugs_sent > MAX_BUGS_PER_CONN:
        await _send(client, {"t": "bug_ok", "ok": False})
        return
    # charged only once the report is real, so empty frames cost nobody a slot
    ip = _peer_ip(client.ws)
    if not _bug_budget_ok(ip):
        LOG.info("bug refused: %s over %d/%ds", ip, MAX_BUGS_PER_IP,
                 int(BUG_IP_WINDOW))
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
        out = {"t": "announce", "id": uuid.uuid4().hex, "text": text}
        CHAT_BACKLOG.append(out)              # late joiners see it on entry
        await _broadcast(out)
        _feed("announce", text=text)
        LOG.info("announce (%d chars) to %d conns", len(text), len(CLIENTS))
        await _send(client, {"t": "admin_ok", "cmd": "announce",
                             "sent": sum(1 for c in CLIENTS.values() if c.logged)})
    elif cmd in ("kick", "mute", "unmute", "ban", "unban"):
        name = _clean(m.get("name"), MAX_NAME)
        target = name.lower()
        if target not in ACCOUNTS:
            await _send(client, {"t": "error", "msg": "No such player."})
            return
        record = dict(MODERATION.get(target, {}))
        if cmd == "mute":
            try:
                minutes = max(1, min(int(m.get("minutes", 10)), 525600))
            except (ValueError, TypeError):
                await _send(client, {"t": "error", "msg": "Minutes must be a number."})
                return
            record["mute"] = time.time() + minutes * 60
        elif cmd == "unmute":
            record.pop("mute", None)
        elif cmd == "ban":
            record["ban"] = True
        elif cmd == "unban":
            record.pop("ban", None)
        previous = MODERATION.get(target)
        MODERATION[target] = record
        try:
            _durable_json(MODERATION_PATH, MODERATION)
        except OSError:
            if previous is None:
                MODERATION.pop(target, None)
            else:
                MODERATION[target] = previous
            await _send(client, {"t": "error", "msg": "Moderation storage unavailable."})
            return
        _feed(cmd, name=ACCOUNTS[target]["name"], **record)
        for c in list(CLIENTS.values()):
            if c.logged and c.name.lower() == target:
                await _send(c, {"t": "error", "msg": {
                    "mute": "You are muted; please wait before messaging.",
                    "unmute": "Your mute has ended.",
                    "kick": "You were kicked by an administrator.",
                    "ban": "This account is banned.",
                    "unban": "Your ban has ended."}[cmd]})
                if cmd in ("kick", "ban"):
                    await _close_quiet(c.ws)
        await _send(client, {"t": "admin_ok", "cmd": cmd})
    else:
        await _send(client, {"t": "error", "msg": "Unknown admin cmd."})


# ---- raid boss (2026-07-15): the weekly community damage race ---------------
# One shared boss for the whole server: a random top-stage species with
# energy_max x 5,500,000 HP, standing for 7 days after a 24h "incoming"
# cooldown.  Every player gets 3 attempts a day; an attempt's RAW battle
# damage (<= 20) submits as raw x 5000 x stage-mult (Mega x20 / Ultimate
# x5 / Champion x2, bound to the card's NUM).  When the boss falls
# (or escapes at the window's end) the contributor board archives and pays
# on claim: rank 1/2/3 = 5000/3000/2000 bits + 3/2/1 items, everyone else
# 500 + 1; an ESCAPED boss pays a flat 100 consolation.  Weekend claims pay
# x1.5.  All numbers are the source rule set's, verbatim; the ledger is
# SERVER-authoritative here (the original trusted clients).
RAID_PATH = os.environ.get(
    "TUIPET_RAID",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "raid.json"))
RAID_POOL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "raid_pool.json")
# ---- ADAPTIVE HP (Joel 2026-07-18: "adaptive HP") -------------------------
# The flat 440M pool needed ~13 dedicated Mega players to fell inside its
# week; smaller communities watched every boss escape and the raid-gated
# eggs were unreachable.  Bosses now size themselves to the crowd that
# actually shows up: a FELLED boss grows the next one; an ESCAPED boss
# shrinks the next to ~what the community proved it can deal in a window.
RAID_HP_FLOOR = 5_000_000            # one solid week for a single mid roster
RAID_HP_CAP = 30_000_000             # mixed-stage ten-regular capacity; see FIXES.md
RAID_GROW = 1.5                      # felled -> the bar rises
RAID_FIT = 0.9                       # escaped -> sized to proven output
RAID_COOLDOWN_S = 1440 * 60          # 24h "Incoming Boss..."
RAID_WINDOW_S = 10080 * 60           # 7 days standing
RAID_ATTEMPTS_PER_DAY = 3
RAID_MAX_RAW = 20                    # 10 rounds x 2 damage: the honest ceiling
#                                      (back to the clone's own number -- the
#                                      0.5 HP race landed client-side 2026-07-17)
RAID_DMG_MULT = 5000
# Species multipliers are resolved from the held cloud save at the wire boundary.
RAID_MULT_BY_NUM_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "raid_stage_mult.json")
# battle audit 2026-10-14: raid text I/O names the save/catalog encoding.
try:
    with open(RAID_MULT_BY_NUM_PATH, encoding="utf-8") as _f:
        RAID_MULT_BY_NUM = {int(k): int(v) for k, v in json.load(_f).items()}
except (OSError, ValueError):
    RAID_MULT_BY_NUM = {}
RAID_RANK_BITS = {1: 5000, 2: 3000, 3: 2000}
RAID_RANK_ITEMS = {1: 3, 2: 2, 3: 1}
RAID_PART_BITS, RAID_PART_ITEMS = 500, 1
RAID_CONSOLATION = 100
# the TUIPET catalog tier (2026-07-18): rank purses roll real prizes --
# no traps, no duds -- from the shelf the client actually sells now
RAID_ITEM_POOL = ["energy_drink", "vitamin", "textbook", "dna_crystal",
                  "steak", "cake", "dumbbell", "x_antibody", "ball"]
RAID_HISTORY_KEEP = 5


def _validate_raid(d):
    if not isinstance(d, dict):
        raise ValueError("raid ledger must be an object")
    for key, default in (("boss", None), ("board", {}), ("history", []),
                         ("claimed", {}), ("attempts", {}), ("paid", {}),
                         ("rewards", {}), ("receipts", {})):
        d.setdefault(key, copy.deepcopy(default))
        if key != "boss" and not isinstance(d[key], type(default)):
            raise ValueError("invalid raid " + key)
    def board(rows):
        if not isinstance(rows, dict):
            raise ValueError("invalid board")
        for row in rows.values():
            if not isinstance(row, dict) or not isinstance(row.get("damage"), int) or row["damage"] < 0:
                raise ValueError("invalid contribution")
    board(d["board"])
    boss = d["boss"]
    if boss is not None:
        if not isinstance(boss, dict) or not isinstance(boss.get("name"), str):
            raise ValueError("invalid boss")
        for k in ("num", "hp", "max_hp", "start", "end"):
            if not isinstance(boss.get(k), (int, float)) or not math.isfinite(boss[k]):
                raise ValueError("invalid boss " + k)
        boss.setdefault("id", str(int(boss["end"])))
        if boss["max_hp"] > RAID_HP_CAP:
            boss["hp"] = max(1, round(boss["hp"] * RAID_HP_CAP / boss["max_hp"])) if boss["hp"] > 0 else 0
            boss["max_hp"] = RAID_HP_CAP
    for row in d["history"] + list(d["rewards"].values()):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not isinstance(row.get("boss_name"), str):
            raise ValueError("invalid archived raid")
        board(row.get("board"))
        if (type(row.get("defeated")) is not bool
                or not isinstance(row.get("ended"), (int, float)) or not math.isfinite(row["ended"])
                or not isinstance(row.get("max_hp", 0), (int, float))):
            raise ValueError("invalid archive metadata")
    for row in d["history"]:
        d["rewards"].setdefault(row["id"], copy.deepcopy(row))
    for rec in d["attempts"].values():
        if not isinstance(rec, dict) or not isinstance(rec.get("date"), str) or not isinstance(rec.get("left"), int) or not 0 <= rec["left"] <= RAID_ATTEMPTS_PER_DAY:
            raise ValueError("invalid attempts")
    for who in d["paid"].values():
        if not isinstance(who, dict) or any(not isinstance(r, dict) or not isinstance(r.get("bits"), int)
                                             or not isinstance(r.get("items"), list) for r in who.values()):
            raise ValueError("invalid paid rewards")
    if any(not isinstance(v, list) for v in d["claimed"].values()):
        raise ValueError("invalid claims")
    for who in d["receipts"].values():
        if not isinstance(who, dict) or any(not isinstance(r, dict) or r.get("t") != "raid_hit"
                                           for r in who.values()):
            raise ValueError("invalid receipts")
    if not isinstance(d.get("revision", 0), int):
        raise ValueError("invalid revision")
    return d


def _load_raid():
    candidates = []
    exists = False
    for path in (RAID_PATH, RAID_PATH + ".bak"):
        try:
            with open(path, encoding="utf-8") as f:
                exists = True
                candidates.append(_validate_raid(json.load(f)))
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, KeyError):
            exists = True
            LOG.exception("raid: invalid snapshot %s", path)
    if candidates:
        return max(candidates, key=lambda d: d.get("revision", 0))
    if exists:
        raise RuntimeError("Raid ledger and backup unreadable; restore a snapshot")
    return _validate_raid({})


RAID = _load_raid()
_RAID_DEPTH = 0


def _save_raid():
    if _RAID_DEPTH:
        return
    os.makedirs(os.path.dirname(RAID_PATH) or ".", exist_ok=True)
    RAID["revision"] = RAID.get("revision", 0) + 1
    # Both copies contain the committed revision before a success is sent.
    for path in (RAID_PATH + ".bak", RAID_PATH):
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(RAID, f, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(path + ".tmp", path)
        fd = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _raid_transaction(fn):
    @functools.wraps(fn)
    def run(*args, **kwargs):
        global RAID, _RAID_DEPTH
        if _RAID_DEPTH:
            return fn(*args, **kwargs)
        RAID.setdefault("rewards", {})
        RAID.setdefault("receipts", {})
        for row in RAID["history"]:
            RAID["rewards"].setdefault(row["id"], copy.deepcopy(row))
        before = copy.deepcopy(RAID)
        _RAID_DEPTH += 1
        try:
            result = fn(*args, **kwargs)
        except Exception:
            RAID = before
            raise
        finally:
            _RAID_DEPTH -= 1
        if RAID != before:
            try:
                _save_raid()
            except OSError:
                # A replace may have landed before failure: recover its receipt.
                RAID = _load_raid() if os.path.exists(RAID_PATH + ".bak") else before
                LOG.exception("raid: durable write failed")
                return {"t": "raid_reward" if fn.__name__ == "_raid_claim" else "raid_hit",
                        "ok": False, "why": "Storage unavailable; retry the same request.",
                        "retryable": True, "request": args[1].get("request")
                        if fn.__name__ == "_raid_verified_hit" else None}
        return result
    return run


def _raid_pool():
    try:
        with open(RAID_POOL_PATH, encoding="utf-8") as f:
            rows = json.load(f)
        valid = [row for row in rows if isinstance(row, dict) and type(row.get("num")) is int
                 and isinstance(row.get("name"), str)] if isinstance(rows, list) else []
        if valid:
            return valid
        raise ValueError("empty raid pool")
    except (OSError, ValueError, TypeError):
        raise RuntimeError("Raid catalog unavailable; restore raid_pool.json")


def _raid_mult_for_num(num):
    """The raid multiplier for a claimed species num.  Non-int / unknown num
    -> x1 (the map ships only non-trivial entries).  An empty map (data file
    missing on the box) also yields x1 -- fail CLOSED, never x20."""
    try:
        return RAID_MULT_BY_NUM.get(int(num), 1)
    except (TypeError, ValueError):
        return 1




def _adaptive_hp():
    """Size the next pool from the last cycle (adaptive HP, 2026-07-18):
    no history -> the floor; felled -> last max_hp x RAID_GROW; escaped ->
    RAID_FIT x the damage the community actually dealt.  Always clamped
    [floor, cap].  Old history rows (pre-adaptive) may lack max_hp -- fall
    back to the board sum."""
    if not RAID["history"]:
        return RAID_HP_FLOOR
    last = RAID["history"][-1]
    dealt = sum(int(e.get("damage", 0)) for e in (last.get("board") or {}).values())
    if last.get("defeated"):
        base = int(last.get("max_hp") or dealt or RAID_HP_FLOOR) * RAID_GROW
    else:
        base = dealt * RAID_FIT
    return int(max(RAID_HP_FLOOR, min(RAID_HP_CAP, base)))


def _raid_stage_next(now):
    """Pick the next boss: 24h cooldown, then a 7-day window.  The species
    is cosmetic variety; the pool is the community-sized _adaptive_hp()."""
    import random as _r
    pick = _r.choice(_raid_pool())
    hp = _adaptive_hp()
    start = now + RAID_COOLDOWN_S
    if RAID["boss"] is None and not RAID["history"]:
        start = now                       # a fresh install opens immediately
    return {"id": uuid.uuid4().hex, "num": int(pick["num"]), "name": str(pick["name"]),
            "hp": hp, "max_hp": hp,
            "start": start, "end": start + RAID_WINDOW_S}


@_raid_transaction
def _raid_rotate(now=None):
    """Archive a finished raid and stage the next boss (idempotent)."""
    now = time.time() if now is None else now
    b = RAID["boss"]
    if b is not None and b["hp"] > 0 and now <= b["end"]:
        return                            # still standing
    if b is not None:
        RAID["history"].append({
            "id": b.get("id", str(int(b["end"]))), "boss_name": b["name"], "num": b["num"],
            "defeated": b["hp"] <= 0, "ended": now if b["hp"] <= 0 else b["end"],
            "max_hp": b.get("max_hp", 0),      # the adaptive sizer reads this
            "board": dict(RAID["board"]),
        })
        archived = RAID["history"][-1]
        RAID["rewards"][archived["id"]] = copy.deepcopy(archived)
        RAID["history"] = RAID["history"][-RAID_HISTORY_KEEP:]
        RAID["board"] = {}
    RAID["boss"] = _raid_stage_next(now)
    _save_raid()


def _raid_attempts(name, now=None):
    now = time.time() if now is None else now
    # UTC like the ladder season and the raid window -- the localtime day key
    # reset attempts at a different boundary than everything else displayed
    # (audit 2026-07-15)
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    rec = RAID["attempts"].get(name)
    if not rec:
        rec = {"date": day, "left": RAID_ATTEMPTS_PER_DAY}
        RAID["attempts"][name] = rec
    # A backwards UTC step cannot refund attempts or move the high-water day.
    if day > rec["date"]:
        rec["date"], rec["left"] = day, RAID_ATTEMPTS_PER_DAY
    return rec


def _raid_rank(board, name):
    """1-based rank by damage (ties by earliest report), 0 if absent."""
    top = sorted(board.items(), key=lambda kv: (-kv[1]["damage"],
                                                kv[1].get("ts", 0)))
    return next((i + 1 for i, (who, _v) in enumerate(top) if who == name), 0)


def _raid_award(name):
    """The newest archived raid this player contributed to and hasn't
    claimed -> {id, rank, defeated, bits, items} (weekend x1.5 applies at
    CLAIM time, not here)."""
    for rec in sorted(RAID["rewards"].values(), key=lambda r: r.get("ended", 0), reverse=True):
        if name in RAID["claimed"].get(rec["id"], []):
            continue
        # battle audit 2026-10-14: an old zero-damage row is not a contribution.
        if int((rec["board"].get(name) or {}).get("damage", 0)) <= 0:
            continue
        rank = _raid_rank(rec["board"], name)
        if rec["defeated"]:
            bits = RAID_RANK_BITS.get(rank, RAID_PART_BITS)
            items = RAID_RANK_ITEMS.get(rank, RAID_PART_ITEMS)
        else:
            # an ESCAPED boss pays by CONTRIBUTION (adaptive arc 2026-07-18):
            # the flat 100 told a top contributor their week meant nothing.
            # Share of the pool -> up to rank-3 defeated money, never more.
            pool = int(rec.get("max_hp") or 0)
            mine = int((rec["board"].get(name) or {}).get("damage", 0))
            share = (mine / pool) if pool > 0 else 0.0
            bits = max(RAID_CONSOLATION,
                       min(RAID_RANK_BITS[3], int(RAID_RANK_BITS[3] * share * 5)))
            items = 0
        preview = int(bits * 1.5) if time.gmtime(rec.get("ended", time.time())).tm_wday >= 5 else bits
        return {"preview_bits": preview, "id": rec["id"], "rank": rank, "defeated": rec["defeated"],
                "boss": rec["boss_name"], "bits": bits, "items": items,
                "ended": rec.get("ended")}
    return None


def _raid_pending(name):
    """A reward PAID but not yet acknowledged by the client (battle call
    #23 = A, Joel 2026-10-15): a dropped socket used to lose it for good.
    Shaped like an award so the client's claim flow re-collects it."""
    for rid, who in sorted(RAID.get("paid", {}).items(), reverse=True):
        r = who.get(name)
        if r:
            return dict(r, id=rid, pending=True)
    return None


@_raid_transaction
def _raid_view(name, now=None):
    now = time.time() if now is None else now
    _raid_rotate(now)
    b = RAID["boss"]
    top = sorted(RAID["board"].items(),
                 key=lambda kv: (-kv[1]["damage"], kv[1].get("ts", 0)))
    you = next(((i + 1, v["damage"]) for i, (who, v) in enumerate(top)
                if who == name), (0, 0))
    return {"t": "raid",
            "boss": dict(b),
            "now": now,
            "top": [(who, v["damage"]) for who, v in top[:10]],
            "you": list(you),
            "attempts": _raid_attempts(name, now)["left"],
            "award": _raid_pending(name) or _raid_award(name),
            "protocol": 2}


@_raid_transaction
def _raid_hit(name, raw, num, now=None):
    """Apply a trusted computed volley. Wire traffic must use _raid_verified_hit."""
    now = time.time() if now is None else now
    _raid_rotate(now)
    b = RAID["boss"]
    if b["start"] > now or b["hp"] <= 0:
        return {"t": "raid_hit", "ok": False, "why": "The boss is not standing."}
    rec = _raid_attempts(name, now)
    if rec["left"] <= 0:
        return {"t": "raid_hit", "ok": False, "why": "No attempts left today."}
    rec["left"] -= 1
    try:
        raw = int(raw or 0)                # wire-supplied: "abc" was a crash
    except (TypeError, ValueError, OverflowError):
        # battle audit 2026-10-14: Infinity is malformed damage too.
        raw = 0
    raw = max(0, min(raw, RAID_MAX_RAW))
    dealt = min(b["hp"], raw * RAID_DMG_MULT * _raid_mult_for_num(num))
    b["hp"] = max(0, b["hp"] - dealt)
    # battle audit 2026-10-14: whiffs spend attempts but earn no claim rank.
    if dealt > 0:
        entry = RAID["board"].setdefault(name, {"damage": 0, "ts": now})
        entry["damage"] += dealt
    # the ts is the FIRST report's stamp (the rank tie-break is "earliest
    # report", as _raid_rank documents) -- refreshing it on every hit turned
    # the tie-break into last-hit
    if b["hp"] <= 0:
        _raid_rotate(now)                 # the kill archives immediately
    _save_raid()
    return {"t": "raid_hit", "ok": True, "dealt": dealt}


@_raid_transaction
def _raid_claim(name, raid_id, now=None, acks=False):
    """`acks`: the client ledgers applied raid ids and sends raid_ack (0.6.20+).
    Only such a client gets its payout HELD for re-send -- an older build
    would re-claim the pending row and apply it twice."""
    now = time.time() if now is None else now
    paid = RAID.setdefault("paid", {}).get(str(raid_id), {}).get(name)
    if paid:
        # already paid, never acknowledged: RE-SEND the same reward (the
        # client's ledger of raid ids it applied stops a double payout)
        return dict(paid, t="raid_reward", ok=True, id=str(raid_id))
    a = _raid_award(name)
    if not a or a["id"] != str(raid_id):
        return {"t": "raid_reward", "ok": False}
    import random as _r
    bits = a["bits"]
    # the weekend half-again rides the day the raid ENDED, not the day it
    # is claimed (shop/loot audit 2026-10-14: holding a weekday claim to
    # Saturday was a free +50%).  UTC like the attempt ledger and the
    # ladder season: ONE day-clock (two-clocks audit 2026-07-18)
    ended = a.get("ended")
    wd = time.gmtime(ended if ended is not None else now).tm_wday
    if wd >= 5:
        bits = int(bits * 1.5)
    items = [_r.choice(RAID_ITEM_POOL) for _ in range(a["items"])]
    RAID["claimed"].setdefault(a["id"], []).append(name)
    reward = {"bits": bits, "items": items, "defeated": a["defeated"],
              "rank": a["rank"], "boss": a["boss"]}
    if acks:
        RAID["paid"].setdefault(a["id"], {})[name] = reward   # held until raid_ack
    _save_raid()
    return dict(reward, t="raid_reward", ok=True, id=a["id"])


@_raid_transaction
def _raid_ack(name, raid_id):
    """The client APPLIED the reward: drop the held copy."""
    who = RAID.get("paid", {}).get(str(raid_id))
    if who and who.pop(name, None) is not None:
        if not who:
            RAID["paid"].pop(str(raid_id), None)
        _save_raid()


def _raid_peer_ip(ws):
    addr = getattr(ws, "remote_address", None)
    if addr and addr[0] in ("127.0.0.1", "::1"):
        return _peer_ip(ws)
    return str(addr[0])[:64] if addr else "?"


_RATE_BUCKETS = {}


def _wire_ok(m):
    target = m.get("to")
    if isinstance(target, int) and not isinstance(target, bool):
        # pre-0.6.42 clients send their offline-thread sentinel as a number
        m["to"] = target = str(target)
    if "to" in m and not isinstance(target, str):
        return False
    if m.get("t") == "relay":
        payload = m.get("payload")
        return isinstance(payload, dict) and ("card" not in payload or isinstance(payload["card"], dict))
    return True


def _message_budget(kind, key):
    if kind in ("chat", "pm"):
        return _token_allow(kind, key, 8, 0.5)
    if kind in ("invite", "invite_resp"):
        return _token_allow("invites", key, 6, 0.1)
    return _token_allow(kind, key, 60 if kind == "relay" else 12, 6 if kind == "relay" else 1)


def _token_allow(scope, key, burst, refill, now=None):
    now = time.monotonic() if now is None else now
    bucket = _RATE_BUCKETS.setdefault(("token-" + scope, key), deque([(burst, now)]))
    tokens, last = bucket[0]
    tokens = min(burst, tokens + max(0, now - last) * refill)
    bucket[0] = (tokens - 1 if tokens >= 1 else tokens, now)
    return tokens >= 1


def _rate_allow(scope, key, limit, window, now=None):
    now = time.monotonic() if now is None else now
    bucket = _RATE_BUCKETS.setdefault((scope, key), deque())
    while bucket and bucket[0] <= now - window:
        bucket.popleft()
    if len(bucket) >= limit:
        LOG.warning("rate rejected scope=%s key=%s", scope, key)
        return False
    bucket.append(now)
    if len(_RATE_BUCKETS) > 4096:
        for k, q in list(_RATE_BUCKETS.items()):
            stamp = q[-1][1] if q and isinstance(q[-1], tuple) else (q[-1] if q else 0)
            if not q or stamp < now - 86400:
                del _RATE_BUCKETS[k]
    return True


@_raid_transaction
def _raid_verified_hit(client, m, now=None):
    now = time.time() if now is None else now
    reject = lambda why: {"t": "raid_hit", "ok": False, "why": why,
                          "request": m.get("request"), "raid": m.get("raid")}
    request = m.get("request")
    rid = m.get("raid")
    if not isinstance(request, str) or not 16 <= len(request) <= 64 or not isinstance(rid, str):
        return reject("Update tuipet to throw safely; viewing and claiming still work.")
    key = client.name.lower()
    receipts = RAID["receipts"].setdefault(key, {})
    if request in receipts:
        return receipts[request]
    _raid_rotate(now)
    if rid != RAID["boss"]["id"]:
        return reject("That raid has ended; refresh before throwing.")
    save = SAVES.get(key)
    holder = HOLDERS.get(key)
    if not holder or holder.get("device") != client.device or not isinstance(save, dict):
        return reject("Sync this device's held cloud save before raiding.")
    try:
        from raid_combat import volley
        raw, num = volley(save, RAID["boss"]["num"])
    except (ValueError, TypeError, KeyError, OverflowError):
        return reject("Cloud pet cannot raid; sync a living fighting-stage pet.")
    result = _raid_hit(client.name, raw, num, now=now)
    result.update(request=request, raid=rid, authoritative=True)
    if result.get("ok"):
        receipts[request] = result
    return result


async def handler(ws):
    if sum(_raid_peer_ip(c.ws) == _raid_peer_ip(ws) for c in CLIENTS.values()) >= 20:
        await ws.send(json.dumps({"t": "error", "msg": "Too many connections; try later."}))
        return
    if len(CLIENTS) >= MAX_CLIENTS:
        await ws.send(json.dumps({"t": "error", "msg": "Lobby is full."}))
        return
    client = Client(ws)
    CLIENTS[client.id] = client
    logged_in = False
    try:
        async for raw in ws:
            if len(raw) > MAX_MSG_BYTES:
                # never silent: an oversized save would otherwise "sync"
                # forever without ever landing (audit 2026-07-18)
                LOG.info("oversize frame dropped: %dB conn=%s", len(raw), client.id)
                continue
            try:
                m = json.loads(raw)
                t = m.get("t")
            except (ValueError, AttributeError):
                continue

            if t == "login":
                # A login_failed closes the socket (return): this client always
                # retries on a fresh connection, so keeping the old one open leaks it.
                # Look up legacy identity before cleaning so old accounts remain usable.
                legacy = str(m.get("name") or "").replace("\n", " ").replace("\r", " ").strip()[:MAX_NAME]
                name = legacy if legacy.lower() in ACCOUNTS else _clean(legacy, MAX_NAME)
                pw = str(m.get("pw") or "")[:MAX_PW]
                if not name:
                    await _send(client, {"t": "login_failed", "msg": "Name required."})
                    return
                key = name.lower()
                if _moderated(key, banned=True):
                    await _send(client, {"t": "login_failed", "msg": "This account is banned."})
                    return
                ip = _raid_peer_ip(ws)
                if any(len(_RATE_BUCKETS.get((scope, value), ())) >= 10
                       and _RATE_BUCKETS[(scope, value)][0] > time.monotonic() - 600
                       for scope, value in (("login-ip", ip), ("login-name", key))):
                    await _send(client, {"t": "login_failed", "msg": "Too many failed passwords; try later."})
                    return
                acc = ACCOUNTS.get(key)
                if acc:                                   # existing name -> must match
                    # pbkdf2 off the event loop: 100k iterations is tens of ms,
                    # and the loop is the whole relay — a login flood must not
                    # freeze every live chat/battle session
                    attempt = time.monotonic()
                    if not (_rate_allow("login-ip", ip, 10, 600, now=attempt)
                            and _rate_allow("login-name", key, 10, 600, now=attempt)):
                        await _send(client, {"t": "login_failed", "msg": "Too many failed passwords; try later."})
                        return
                    if not await asyncio.to_thread(_verify, pw, acc):
                        await asyncio.sleep(0.4)          # slow down brute force
                        await _send(client, {"t": "login_failed", "msg": "Wrong password for that name."})
                        return
                    for scope, value in (("login-ip", ip), ("login-name", key)):
                        bucket = _RATE_BUCKETS[(scope, value)]
                        if attempt in bucket:
                            bucket.remove(attempt)
                    name = acc["name"]                    # canonical capitalisation
                else:                                     # new name -> claim it
                    if not _new_name_ok(name):
                        # 2026-10-16: "-" was claimed as an account; a NEW name must
                        # carry a letter or digit (existing names keep working)
                        await _send(client, {"t": "login_failed",
                                             "msg": "Names need a letter or number."
                                             if not any(ch.isalnum() for ch in name)
                                             else "That name is reserved."})
                        return
                    if not pw:
                        await _send(client, {"t": "login_failed", "msg": "Pick a password to claim this name."})
                        return
                    if not (_rate_allow("registration-ip", _raid_peer_ip(ws), 20, 3600)   # 20/h: carriers share one IP among many phones (CGNAT)
                            and _rate_allow("registration-name", key, 3, 86400)):
                        await _send(client, {"t": "login_failed", "msg": "Registration limit; try again later."})
                        return
                    candidate = await asyncio.to_thread(_make_account, name, pw)
                    # sync audit 2026-10-14: hashing yields; another login may claim first.
                    acc = ACCOUNTS.get(key)
                    if acc:
                        if not await asyncio.to_thread(_verify, pw, acc):
                            await _send(client, {"t": "login_failed",
                                                 "msg": "Wrong password for that name."})
                            return
                        name = acc["name"]
                    else:
                        ACCOUNTS[key] = candidate
                        try:
                            _save_accounts()
                        except OSError:
                            ACCOUNTS.clear()
                            ACCOUNTS.update(_load_accounts())
                            await _send(client, {"t": "login_failed", "msg": "Account storage unavailable; retry."})
                            return
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
                client.pet = _clamp_pet(m.get("pet"))
                client.live = not sync_only
                client.device = str(m.get("device") or "")[:64]
                client.dlabel = str(m.get("dlabel") or "")[:24]
                client.boot = boot
                if sync_only:                     # the newest HOLDER launch owns the saves
                    # sync audit 2026-10-14: a spectator read cannot revoke the holder.
                    hold = HOLDERS.get(key)
                    if not hold or hold.get("device") == client.device:
                        _take_lease(client, key, boot)
                    if client.device and key not in HOLDERS:
                        # migration: the first device that syncs an unheld
                        # account becomes its holder (cartridge 2026-07-29)
                        _claim_holder(key, client.device, client.dlabel)
                logged_in = True
                client.logged = True
                await _send(client, {"t": "welcome", "id": client.id, "name": client.name,
                                     "save": SAVES.get(key),        # cloud save (or null) for cross-device load
                                     "holder": _holder_view(key)})  # who holds the cartridge
                if not sync_only:
                    for f in CHAT_BACKLOG:        # rejoin the conversation, not a void
                        await _send(client, {**f, "replay": True})  # marked: clients skip lines already on the pane
                    await _flush_pending(client, key)   # deliver PMs held while they were away
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

            elif t in ("raid_get", "raid_hit", "raid_claim", "raid_ack") and not (
                    _rate_allow("raid-account", client.name.lower(), 90, 60)
                    and _rate_allow("raid-ip", _raid_peer_ip(ws), 900, 60)):
                await _send(client, {"t": "raid_reward" if t == "raid_claim" else "raid_hit",
                                     "ok": False, "why": "Raid request limit; wait a minute.",
                                     "request": m.get("request"), "retryable": True})

            elif t in ("chat", "pm", "invite", "invite_resp", "relay", "pet") and (
                    _moderated(client.name, banned=True) or
                    (t != "pet" and _moderated(client.name))):
                await _send(client, {"t": "error", "msg": "You are muted or banned; messaging is unavailable."})

            elif t in ("chat", "pm", "invite", "invite_resp", "relay", "pet") and not _message_budget(t, client.name.lower()):
                await _send(client, {"t": "error", "msg": "Please slow down; try again shortly."})

            elif t in ("pm", "invite", "invite_resp", "relay") and not _wire_ok(m):
                await _send(client, {"t": "error", "msg": "Invalid message envelope."})

            elif t == "pet":
                client.pet = _clamp_pet(m.get("pet"))
                if client.live:
                    await _push_roster()

            elif t == "take":
                # the player's explicit YES to the take-question: this device
                # becomes the cartridge's holder.  Legacy clients (no device
                # id) cannot take -- they predate the question.
                key = client.name.lower()
                if client.device:
                    _claim_holder(key, client.device, client.dlabel)
                    # sync audit 2026-10-14: an explicit take outranks launch seniority.
                    for c in CLIENTS.values():
                        if c.name.lower() == key:
                            c.lease = None
                    LEASES.pop(key, None)
                    _take_lease(client, key, client.boot)
                    await _send(client, {"t": "holder", "ok": True,
                                         "save": SAVES.get(key)})
                else:
                    await _send(client, {"t": "holder", "ok": False})

            elif t == "wipe":
                # OPTIONS -> Erase all data, "for keeps" (Joel 2026-10-14:
                # "erasing my data didnt reset my monster" -- the cloud copy
                # survived the local wipe and the sign-in card brought it
                # back).  The logged-in account (password proven) clears its
                # own cloud save and frees the cartridge.
                had = await _wipe_account(client.name.lower())
                LOG.info("wipe: %s (had save: %s)", client.name, had)
                await _send(client, {"t": "wiped", "ok": True})

            elif t == "save":
                key = client.name.lower()
                ok, why = False, None
                hold = HOLDERS.get(key)
                if hold and hold.get("device") != client.device:
                    # the cartridge lives on another device: this push is a
                    # fork, whatever its timestamp says (GPD war 2026-07-29)
                    why = "holder"
                    LOG.info("non-holder save dropped: %s conn=%s dev=%s",
                             client.name, client.id, client.device[:8] or "-")
                elif isinstance(m.get("save"), dict) and _erased_pet(key, m.get("save")):
                    # the account erased THIS pet; a device still signed in
                    # must not bring it back (saves call #27 = A)
                    why = "erased"
                    LOG.info("erased-pet save dropped: %s conn=%s", client.name, client.id)
                elif _lease_ok(client, key):
                    ok = await _store_save(key, m.get("save"))
                    if not ok:
                        why = "invalid"           # failed _valid_save, not a lease matter
                else:                             # a newer session took over
                    why = "lease"
                    LOG.info("stale-lease save dropped: %s conn=%s", client.name, client.id)
                # the ack makes quit-pushes honest: a dropped push must not
                # report True back to the quitting client -- and `why` lets it
                # warn for the RIGHT reason (the old single flag showed "newer
                # session" for format rejections too; audit 2026-07-18)
                ack = {"t": "saved", "ok": ok}
                if why:
                    ack["why"] = why
                if why == "holder":
                    # name the device holding the cartridge: the client can only
                    # tell the player WHERE the pet is if we say (2026-07-30 --
                    # .313 dropped these pushes silently and the game, knowing
                    # nothing, kept pushing into the void every 10s)
                    ack["holder"] = _holder_view(key)
                await _send(client, ack)

            elif t == "ladder_report":
                _ladder_report(client.name, bool(m.get("won")), str(m.get("opp") or "")[:24])

            elif t == "ladder_get":
                await _send(client, _ladder_view(client.name))

            elif t == "ladder_claim":
                # ack + refreshed view, like raid_claim (the award row clears)
                await _send(client, _ladder_claim(client.name, str(m.get("season") or "")))
                await _send(client, _ladder_view(client.name))

            elif t == "raid_get":
                await _send(client, _raid_view(client.name))
            elif t == "raid_hit":
                r = _raid_verified_hit(client, m)
                await _send(client, r)
                await _send(client, _raid_view(client.name))
            elif t == "raid_claim":
                await _send(client, _raid_claim(client.name, m.get("raid"),
                                                acks=bool(m.get("acks"))))
                await _send(client, _raid_view(client.name))
            elif t == "raid_ack":
                if m.get("protocol") == 2:
                    key = client.name.lower()
                    save = m.get("save")
                    hold = HOLDERS.get(key)
                    rid = str(m.get("raid"))
                    if client.name not in RAID.get("paid", {}).get(rid, {}):
                        continue  # A retried ACK must never overwrite a newer cloud save.
                    if (not hold or hold.get("device") != client.device
                            or LEASES.get(key, (None,))[0] != client.boot or not isinstance(save, dict)
                            or not isinstance(save.get("progress"), dict)
                            or not isinstance(save["progress"].get("raids_paid"), list)
                            or rid not in save["progress"]["raids_paid"] or _erased_pet(key, save)):
                        await _send(client, {"t": "raid_reward", "ok": False,
                                             "why": "Reward held: sync the holding device to finish."})
                        continue
                    try:
                        cloud_receipts = ((SAVES.get(key) or {}).get("progress") or {}).get("raids_paid", [])
                        stored = rid in cloud_receipts or await _store_save(key, save)
                    except OSError:
                        stored = False
                    if not stored:
                        await _send(client, {"t": "raid_reward", "ok": False,
                                             "why": "Reward held: cloud save failed; retry C."})
                        continue
                _raid_ack(client.name, m.get("raid"))

            elif t == "chat":
                text = _clean(m.get("text"), MAX_CHAT)
                if text and client.live:          # a sync_only ghost isn't in the room
                    out = {"t": "chat", "id": uuid.uuid4().hex, "from_id": client.id,
                           "from_name": client.name, "text": text}
                    if client.room is None:
                        CHAT_BACKLOG.append(out)  # the re-entry replay window (main only)
                    await _broadcast_room(client.room, out)
                    # room chats still land in the admin feed (abuse handling >
                    # absolute privacy on a hobby relay), marked with their room
                    _feed("chat", name=client.name, text=text, room=client.room)

            elif t == "room":
                # join-or-create by shared phrase; empty code -> the main lobby.
                # No password check beyond the phrase ITSELF: the phrase is the
                # password (DSprite's private 🔒 rooms, tuipet-shaped).
                if not client.live:
                    # still ack: a 0.6.42+ sender holds its queue until room_ok
                    await _send(client, {"t": "room_ok", "room": client.room})
                    continue
                code = _room_code(m.get("code"))
                if code != client.room:
                    client.room = code
                    # room_ok FIRST: the client resets its roster-diff baseline
                    # on it, so the scoped roster that follows must not race it
                    # (else the whole old scope prints as a wave of "left"s)
                    await _send(client, {"t": "room_ok", "room": code})
                    if code is None:              # rejoining main replays the window
                        for f in CHAT_BACKLOG:
                            await _send(client, {**f, "replay": True})
                    await _push_roster()
                    _feed("room", name=client.name, room=code or "(main)")
                else:
                    await _send(client, {"t": "room_ok", "room": code})

            elif t == "pm":
                # A private message reaches every live connection of the target
                # account -- their lobby login and the sync ghost at the home
                # screen (the alert channel; 2026-07-05).  If NO live lobby
                # session is there to persist it, the PM is queued and delivered
                # on their next lobby login (store-and-forward, 2026-07-12), so
                # messaging someone who stepped away is not lost.  The sender is
                # always acked, so their own copy of the thread saves either way.
                text = _clean(m.get("text"), MAX_CHAT)
                if not text:
                    continue
                target = CLIENTS.get(m.get("to"))
                if target is not None and target.logged:
                    name = target.name
                else:                              # stale/gone id -> address by name
                    name = _clean(m.get("to_name"), MAX_NAME)
                key = name.lower() if name else ""
                if not key or key not in ACCOUNTS:
                    await _send(client, {"t": "error", "msg": "No such player."})
                    continue
                out = {"t": "pm", "from_id": client.id,
                       "from_name": client.name, "text": text}
                conns = _account_conns(name)
                for c in conns:
                    await _send(c, out)
                if not any(c.live for c in conns):     # no lobby session to persist it now
                    await _queue_pm(key, client.name, text)
                await _send(client, {"t": "pm_ok",
                                     "to_name": ACCOUNTS[key]["name"], "text": text})

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
