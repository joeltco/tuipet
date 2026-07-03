"""Blocking cloud-save helpers for the launch/quit edges.

The pet save lives on the lobby server keyed by account (see server.py). To make
a pet follow you across devices we:
  * pull synchronously at startup, BEFORE the pet is loaded, and mirror a newer
    cloud save down to the local file — so the normal load path just picks it up
    (no mid-session pet swapping);
  * push synchronously on quit so the final state is captured.
During the session the app pushes incrementally via net.SyncClient (autosave).

Everything here is fail-soft: offline / bad password / timeout simply returns
without syncing, so the game always runs.
"""
from __future__ import annotations
import json

from . import persistence

_TIMEOUT = 3.0


def _connect(uri, timeout):
    # imported lazily so a missing optional dep never blocks startup
    from websockets.sync.client import connect
    return connect(uri, open_timeout=timeout, close_timeout=1)


def pull_save(uri, name, pw, timeout=_TIMEOUT):
    """Return the account's stored cloud save dict, or None. Never raises."""
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps({"t": "login", "name": name, "pw": pw, "sync_only": True}))
            for _ in range(5):                       # welcome is the first/early frame
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "welcome":
                    return m.get("save")
                if m.get("t") == "login_failed":
                    return None
    except Exception:
        return None
    return None


def push_save(uri, name, pw, save, timeout=_TIMEOUT):
    """Upload one save dict, blocking. Returns True on a clean send. Never raises.
    Compares timestamps first: a device that missed its startup pull (offline
    at launch) must not stomp a newer cloud save on quit."""
    try:
        cloud = pull_save(uri, name, pw, timeout)
        if cloud and float(cloud.get("_saved_at") or 0) > float(save.get("_saved_at") or 0):
            return False                             # the cloud moved on without us
    except Exception:
        pass                                         # compare is best-effort; the send decides
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps({"t": "login", "name": name, "pw": pw, "sync_only": True}))
            ws.send(json.dumps({"t": "save", "save": save}))
            return True
    except Exception:
        return False


def sync_down_at_startup(uri, name, pw, timeout=_TIMEOUT):
    """Pull the cloud save and, if it's newer than the local one, write it to the
    local save file so the app loads the synced pet. Returns a short status string
    for logging/tests ('' when nothing changed)."""
    if not name:
        return ""
    save = pull_save(uri, name, pw, timeout)
    if not save:
        return ""
    cloud_ts = float(save.get("_saved_at") or 0)
    if cloud_ts <= persistence.local_saved_at():
        return ""                                    # local is as new or newer
    # never clobber a valid local save with a blob that can't even become a
    # pet (a malformed cloud payload used to mean a silent fresh-egg wipe)
    probe, _ = persistence.pet_from_save(dict(save), catch_up=False)
    if probe is None:
        return "cloud-save-invalid"
    persistence.write_save_dict(save)
    return "pulled"
