"""Blocking cloud-save helpers for the launch/quit edges — the CARTRIDGE model.

The pet save lives on the lobby server keyed by account (see server.py), and
the server tracks ONE HOLDER device per account: the pet is a cartridge,
checked out to one device at a time.  A non-holding device gets exactly one
question at launch ("Your pet is on phone. Take it onto this device?") and is
otherwise a spectator; the holder plays with no new friction at all.

Why: "newest save wins" decided by wall clock, so an actively-relaunched
device holding a STALE FORK of the pet legitimately out-stamped the real one
— the gen-10 loss (2026-07-27, a desktop's gen-3 over a phone's gen-10) and
the GPD fork war (2026-07-29, twice in one night).  The guard stack built in
0.5.290-293 was cut by 0.5.294's plain-and-simple revert; the cartridge is
its replacement — the one question no algorithm can answer (WHICH copy do
you mean?) goes to the player, once, at the only moment it matters.

Everything here is fail-soft: offline / bad password / timeout simply returns
without syncing, so the game always runs — except a device whose LAST cloud
contact said "another device holds the pet": that one stays a spectator until
it can reach the cloud and take.
"""
from __future__ import annotations
import json
import time

from . import persistence

_TIMEOUT = 3.0
# The BOOT gate is the one call that must not give up early: it decides whether
# the player is even asked "take the pet onto this device?", and a skipped
# question means playing the wrong copy for an evening.  3s lost that race on a
# just-logged-in machine -- cold DNS + TLS to the lobby -- and the session's own
# sync client, connecting seconds later with its retry loop, sailed through and
# pushed into the void (Joel's PC, 2026-07-30).  Patience here costs a slow
# launch at worst; impatience costs the question.
BOOT_TIMEOUT = 12.0

# The app-launch stamp: every sync login carries it, and the server grants the
# save lease only to the NEWEST launch — so a backgrounded device's reconnect
# can't steal save ownership back from the session the player actually opened.
BOOT = time.time()


def _connect(uri, timeout):
    # imported lazily so a missing optional dep never blocks startup
    from websockets.sync.client import connect
    return connect(uri, open_timeout=timeout, close_timeout=1)


def _login_msg(name, pw):
    """Every sync login names its DEVICE — the cartridge's holder is a device,
    not an account, so the server must be able to tell two machines apart."""
    return {"t": "login", "name": name, "pw": pw, "sync_only": True,
            "boot": BOOT, "device": persistence.device_id(),
            "dlabel": persistence.device_label()}


def pull_save(uri, name, pw, timeout=_TIMEOUT):
    """Return the account's stored cloud save dict, or None. Never raises."""
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps(_login_msg(name, pw)))
            for _ in range(5):                       # welcome is the first/early frame
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "welcome":
                    return m.get("save")
                if m.get("t") == "login_failed":
                    return None
    except Exception:
        return None
    return None


def probe(uri, name, pw, timeout=_TIMEOUT):
    """Login check for the account switcher: ('ok', save_or_None) on a welcome
    (an unknown name is CREATED by the server, like the first-launch flow),
    ('badpw', None) when the server rejects the login — pull_save can't tell
    that apart from no-save, and switching onto a typo'd password would
    silently strand the player on a fresh start — ('offline', None) when the
    lobby can't be reached. Never raises."""
    st, save, _holder = gate(uri, name, pw, timeout)
    return (st, save)


def gate(uri, name, pw, timeout=_TIMEOUT):
    """probe(), plus the welcome's holder: ('ok'|'badpw'|'offline', save,
    holder) where holder is {'device','label'} or None (no holder yet — the
    server auto-claims for the first device that syncs, so 'ok' with a holder
    that isn't us is the ONLY case that needs the take-question)."""
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps(_login_msg(name, pw)))
            for _ in range(5):                       # welcome is the first/early frame
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "welcome":
                    return ("ok", m.get("save"), m.get("holder"))
                if m.get("t") == "login_failed":
                    return ("badpw", None, None)
    except Exception:
        return ("offline", None, None)
    return ("offline", None, None)


def take(uri, name, pw, timeout=_TIMEOUT):
    """Claim the cartridge for THIS device.  Returns (ok, cloud_save_or_None):
    on ok the server now routes pushes here and the returned save (if any) is
    the pet to install locally. Never raises."""
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps(_login_msg(name, pw)))
            ws.send(json.dumps({"t": "take"}))
            for _ in range(6):
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "holder":
                    return (bool(m.get("ok")), m.get("save"))
                if m.get("t") == "login_failed":
                    return (False, None)
    except Exception:
        return (False, None)
    return (False, None)


def wipe(uri, name, pw, timeout=_TIMEOUT):
    """Erase this account's cloud save and free its cartridge (OPTIONS ->
    Erase all data).  True only on the server's confirmation. Never raises."""
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps(_login_msg(name, pw)))
            ws.send(json.dumps({"t": "wipe"}))
            for _ in range(8):
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "wiped":
                    return bool(m.get("ok"))
                if m.get("t") == "login_failed":
                    return False
    except Exception:
        return False
    return False


def push_save(uri, name, pw, save, timeout=_TIMEOUT):
    """Upload one save dict, blocking. Returns True on a clean send. Never raises.

    The pre-push check is MANDATORY: a device that cannot READ the cloud may
    not WRITE it.  0.5.294's best-effort compare silently skipped itself when
    its own pull failed — the same broken network that missed the startup
    pull — and the quit flush poisoned the cloud with a stale fork (the GPD
    incident).  An EMPTY cloud is st=='ok' with cloud None, so a fresh
    account's first upload still flows (the 0.5.293 lesson)."""
    try:
        from .net import SAVE_WIRE_MAX
        if len(json.dumps(save)) > SAVE_WIRE_MAX:
            return False       # the server would silently drop the frame (64KB cap)
    except Exception:
        return False
    st, cloud = probe(uri, name, pw, timeout)
    if st != "ok":
        return False                                 # unreadable cloud: no blind writes
    # sync audit 2026-10-14: malformed stamps cannot authorize a blind quit write.
    try:
        if cloud and float(cloud.get("_saved_at") or 0) > float(save.get("_saved_at") or 0):
            return False
    except (TypeError, ValueError, AttributeError):
        return False                                 # the cloud moved on without us
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps(_login_msg(name, pw)))
            ws.send(json.dumps({"t": "save", "save": save}))
            for _ in range(5):                   # wait for the server's verdict --
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "saved":        # fire-and-forget used to report
                    return bool(m.get("ok"))     # True on drops (stale lease etc.)
                if m.get("t") == "login_failed":
                    return False
            return False
    except Exception:
        return False


def sync_down_at_startup(uri, name, pw, timeout=_TIMEOUT):
    """Pull the cloud save and, if it's newer than the local one, write it to the
    local save file so the app loads the synced pet. Returns a short status string
    for logging/tests ('' when nothing changed).  HOLDER-side only — the boot
    gate in __main__ asks the take-question first on a non-holding device."""
    if not name:
        return ""
    save = pull_save(uri, name, pw, timeout)
    if not save:
        return ""
    cloud_ts = float(save.get("_saved_at") or 0)
    if cloud_ts <= persistence.local_saved_at():
        return ""                                    # local is as new or newer
    # never clobber a valid local save with a blob that can't even become a
    # pet (a malformed cloud payload used to mean a silent fresh-egg wipe) --
    # and never accept a FOREIGN-format save (strict: an outdated client's
    # push must not replace this build's pet; 2026-07-04 'Child' incident)
    probe_pet, _ = persistence.pet_from_save(dict(save), strict=True)
    if probe_pet is None:
        return "cloud-save-invalid"
    persistence.rescue_copy()        # the one write that replaces bytes this
    persistence.write_save_dict(save)   # device never played gets a copy that STAYS
    return "pulled"
