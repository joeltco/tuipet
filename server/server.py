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
        return json.load(open(PENDING_PATH))
    except (OSError, ValueError):
        return {}


PENDING = _load_pending()
_pending_lock = asyncio.Lock()


async def _save_pending():
    async with _pending_lock:
        tmp = PENDING_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(PENDING, f)
        os.replace(tmp, PENDING_PATH)


async def _queue_pm(key, from_name, text):
    q = PENDING.setdefault(key, [])
    q.append({"from_name": from_name, "text": text,
              "ts": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime())})
    del q[:-MAX_PENDING_PER_ACCT]
    await _save_pending()


async def _flush_pending(client, key):
    q = PENDING.pop(key, None)
    if not q:
        return
    for rec in q:
        await _send(client, {"t": "pm", "from_id": 0,
                             "from_name": rec.get("from_name", "?"),
                             "text": rec.get("text", "")})
    await _save_pending()
    LOG.info("flushed %d queued pm(s) to %s", len(q), client.name)


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


class Client:
    __slots__ = ("id", "ws", "name", "pet", "live", "lease", "logged", "boot",
                 "bugs_sent", "room")

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
        self.room = None       # None = the main lobby; else a room code (str)


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
RAID_HP_PER_ENERGY = 5_500_000
RAID_COOLDOWN_S = 1440 * 60          # 24h "Incoming Boss..."
RAID_WINDOW_S = 10080 * 60           # 7 days standing
RAID_ATTEMPTS_PER_DAY = 3
RAID_MAX_RAW = 20                    # 10 rounds x 2 damage: the honest ceiling
#                                      (back to the clone's own number -- the
#                                      0.5 HP race landed client-side 2026-07-17)
RAID_DMG_MULT = 5000
# num -> raid multiplier, precomputed from the atlas (tools regen it).  The
# damage mult binds to the pet's NUM, not the free-text stage string a client
# can forge: claiming x20 now means claiming a real super-ultimate species,
# which shows on the forger's own roster sprite -- the same tradeoff the client
# _clamp_card fix accepted (round-3 audit 2026-07-16).
RAID_MULT_BY_NUM_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "raid_stage_mult.json")
try:
    with open(RAID_MULT_BY_NUM_PATH) as _f:
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


def _load_raid():
    try:
        with open(RAID_PATH) as f:
            d = json.load(f)
        d.setdefault("boss", None)
        d.setdefault("board", {})
        d.setdefault("history", [])
        d.setdefault("claimed", {})
        d.setdefault("attempts", {})
        return d
    except Exception:
        return {"boss": None, "board": {}, "history": [], "claimed": {},
                "attempts": {}}


RAID = _load_raid()


def _save_raid():
    try:
        tmp = RAID_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(RAID, f)
        os.replace(tmp, RAID_PATH)
    except OSError:
        LOG.warning("raid: disk refused %s", RAID_PATH)


def _raid_pool():
    try:
        with open(RAID_POOL_PATH) as f:
            return json.load(f)
    except Exception:
        return [{"num": 0, "name": "Unknown Boss", "energy_max": 65}]


def _raid_mult_for_num(num):
    """The raid multiplier for a claimed species num.  Non-int / unknown num
    -> x1 (the map ships only non-trivial entries).  An empty map (data file
    missing on the box) also yields x1 -- fail CLOSED, never x20."""
    try:
        return RAID_MULT_BY_NUM.get(int(num), 1)
    except (TypeError, ValueError):
        return 1




def _raid_stage_next(now):
    """Pick the next boss: 24h cooldown, then a 7-day window."""
    import random as _r
    pick = _r.choice(_raid_pool())
    hp = int(pick.get("energy_max", 65)) * RAID_HP_PER_ENERGY
    start = now + RAID_COOLDOWN_S
    if RAID["boss"] is None and not RAID["history"]:
        start = now                       # a fresh install opens immediately
    return {"num": int(pick["num"]), "name": str(pick["name"]),
            "hp": hp, "max_hp": hp,
            "start": start, "end": start + RAID_WINDOW_S}


def _raid_rotate(now=None):
    """Archive a finished raid and stage the next boss (idempotent)."""
    now = time.time() if now is None else now
    b = RAID["boss"]
    if b is not None and b["hp"] > 0 and now <= b["end"]:
        return                            # still standing
    if b is not None:
        RAID["history"].append({
            "id": str(int(b["end"])), "boss_name": b["name"], "num": b["num"],
            "defeated": b["hp"] <= 0, "ended": now,
            "board": dict(RAID["board"]),
        })
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
    if not rec or rec.get("date") != day:
        rec = {"date": day, "left": RAID_ATTEMPTS_PER_DAY}
        RAID["attempts"][name] = rec
        if len(RAID["attempts"]) > 4096:
            # drop only STALE (previous-day) rows -- `= {name: rec}` wiped every
            # OTHER player's TODAY count, refunding their used attempts on the
            # next hit (round-3 audit 2026-07-16)
            RAID["attempts"] = {n: r for n, r in RAID["attempts"].items()
                                if r.get("date") == day}
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
    for rec in sorted(RAID["history"], key=lambda r: r["id"], reverse=True):
        if name in RAID["claimed"].get(rec["id"], []):
            continue
        if name not in rec["board"]:
            continue
        rank = _raid_rank(rec["board"], name)
        if rec["defeated"]:
            bits = RAID_RANK_BITS.get(rank, RAID_PART_BITS)
            items = RAID_RANK_ITEMS.get(rank, RAID_PART_ITEMS)
        else:
            bits, items = RAID_CONSOLATION, 0
        return {"id": rec["id"], "rank": rank, "defeated": rec["defeated"],
                "boss": rec["boss_name"], "bits": bits, "items": items}
    return None


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
            "award": _raid_award(name)}


def _raid_hit(name, raw, num, now=None):
    """One attempt's damage report.  The server owns the attempt count and
    the ceiling: raw battle damage is bounded by what 10 rounds can deal, and
    the stage multiplier binds to the claimed species NUM (not a forgeable
    stage string)."""
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
    except (TypeError, ValueError):
        raw = 0
    raw = max(0, min(raw, RAID_MAX_RAW))
    dealt = raw * RAID_DMG_MULT * _raid_mult_for_num(num)
    b["hp"] = max(0, b["hp"] - dealt)
    entry = RAID["board"].setdefault(name, {"damage": 0, "ts": now})
    entry["damage"] += dealt
    entry["ts"] = now
    if b["hp"] <= 0:
        _raid_rotate(now)                 # the kill archives immediately
    _save_raid()
    return {"t": "raid_hit", "ok": True, "dealt": dealt}


def _raid_claim(name, raid_id, now=None):
    now = time.time() if now is None else now
    a = _raid_award(name)
    if not a or a["id"] != str(raid_id):
        return {"t": "raid_reward", "ok": False}
    import random as _r
    bits = a["bits"]
    wd = time.localtime(now).tm_wday
    if wd >= 5:
        bits = int(bits * 1.5)            # weekend claims pay half again
    items = [_r.choice(RAID_ITEM_POOL) for _ in range(a["items"])]
    RAID["claimed"].setdefault(a["id"], []).append(name)
    if len(RAID["claimed"]) > RAID_HISTORY_KEEP * 4:
        keep = {r["id"] for r in RAID["history"]}
        RAID["claimed"] = {k: v for k, v in RAID["claimed"].items() if k in keep}
    _save_raid()
    return {"t": "raid_reward", "ok": True, "bits": bits, "items": items,
            "defeated": a["defeated"], "rank": a["rank"], "boss": a["boss"]}


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

            elif t == "pet":
                client.pet = m.get("pet") or {}
                if client.live:
                    await _push_roster()

            elif t == "save":
                key = client.name.lower()
                ok, why = False, None
                if _lease_ok(client, key):
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
                await _send(client, ack)

            elif t == "ladder_report":
                _ladder_report(client.name, bool(m.get("won")), str(m.get("opp") or "")[:24])

            elif t == "ladder_get":
                await _send(client, _ladder_view(client.name))

            elif t == "ladder_claim":
                _ladder_claim(client.name, str(m.get("season") or ""))

            elif t == "raid_get":
                await _send(client, _raid_view(client.name))
            elif t == "raid_hit":
                # the multiplier binds to the roster card's NUM, resolved to a
                # real species' stage in RAID_MULT_BY_NUM -- a forged stage
                # STRING doesn't buy x20 (clone round-3 audit 2026-07-16)
                r = _raid_hit(client.name, m.get("damage"),
                              (client.pet or {}).get("num"))
                await _send(client, r)
                await _send(client, _raid_view(client.name))
            elif t == "raid_claim":
                await _send(client, _raid_claim(client.name, m.get("raid")))
                await _send(client, _raid_view(client.name))

            elif t == "chat":
                text = _clean(m.get("text"), MAX_CHAT)
                if text and client.live:          # a sync_only ghost isn't in the room
                    out = {"t": "chat", "from_id": client.id,
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
                            await _send(client, f)
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
