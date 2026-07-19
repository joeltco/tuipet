"""Atomic save IO (tier-4 split, 2026-07-17): the save-dir pick, the
tmp+replace JSON writer, the instance lock and the crash log.  Owns the
mutable `save_failed` flag; persistence delegates reads of it via module
__getattr__ so `persistence.save_failed` stays truthful."""
from __future__ import annotations

import json
import os
import time  # noqa: F401


def _can_use(d):
    """True if we could actually WRITE here -- without creating anything yet
    (an import-time mkdir would litter every dev box and test run)."""
    if os.path.isdir(d):
        return os.access(d, os.W_OK)
    parent = os.path.dirname(d)
    while parent and not os.path.isdir(parent):
        parent = os.path.dirname(parent)
    return bool(parent) and os.access(parent, os.W_OK)

def _pick_save_dir():
    """Where the pet lives.  iOS (a-Shell, our official iPhone/iPad target)
    CANNOT write to `~` -- only ~/Documents, ~/Library and ~/tmp are writable.
    tuipet wrote to ~/.local/share/tuipet and _atomic_write_json swallows
    OSError, so on iOS every save failed SILENTLY: the pet never persisted and
    the player was never told (iOS support 2026-07-13).  Pick the first
    location we can actually write, and let TUIPET_SAVE_DIR override."""
    env = os.environ.get("TUIPET_SAVE_DIR")
    if env:
        return os.path.expanduser(env)
    cands = []
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        cands.append(os.path.join(os.path.expanduser(xdg), "tuipet"))
    cands.append(os.path.expanduser("~/.local/share/tuipet"))   # Linux/Termux/macOS
    cands.append(os.path.expanduser("~/Documents/tuipet"))      # iOS: the writable home
    for d in cands:
        if _can_use(d):
            return d
    return cands[0]              # nothing writable: saves will fail LOUDLY now

SAVE_DIR = _pick_save_dir()

SAVE_PATH = os.path.join(SAVE_DIR, "save.json")

MAX_OFFLINE = 36 * 3600  # cap catch-up at 36h of real time

SETTINGS_PATH = os.path.join(SAVE_DIR, "settings.json")

# set by _atomic_write_json when the disk refuses us -- the app surfaces it once
# so a silently-unsaveable install (iOS's read-only ~) can never eat a pet
save_failed = ""
_failed_path = ""    # WHICH file refused: only its own later success clears the flag

def _atomic_write_json(path, data, keep_bak=False):
    """Atomic JSON write (tmp + os.replace); keep_bak rotates one generation
    back first.  This dance lived in three hand-rolled copies (settings, save,
    cloud-pull; refactor 2026-07-05)."""
    global save_failed, _failed_path
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(data, fh)
        if keep_bak and os.path.exists(path):
            os.replace(path, path + ".bak")   # keep one generation back
        os.replace(tmp, path)
        # a transient refusal used to stick forever -- the exit banner
        # printed "couldn't save" over a pet that had been saving fine
        # every 10s since (persistence audit 2026-07-18).  Clear it only
        # when the SAME file writes clean: a settings write succeeding
        # must not mute a save.json that is still refusing.
        if path == _failed_path:
            save_failed, _failed_path = "", ""
    except OSError as e:
        # best-effort, mirroring the read side (load/load_settings both swallow
        # OSError): a full / read-only / quota'd disk must never crash the 10s
        # autosave timer or on_unmount teardown (hardening 2026-07-12).  A
        # non-serializable payload still raises TypeError -- that is a bug, not
        # a disk problem, and must surface.
        #
        # ...but it must not be SILENT either (iOS support 2026-07-13): a
        # read-only save dir meant the pet quietly never persisted and the
        # player only found out by losing it.  Record it; the app warns.
        save_failed = "%s: %s" % (os.path.dirname(path) or path, e.strerror or e)
        _failed_path = path
        return

_LOCK_NAME = "running.pid"

def _live_save_dir():
    """SAVE_DIR through the persistence module, AT CALL TIME -- the
    test sandbox (conftest) patches persistence.SAVE_DIR, and the
    injectable-paths law says every path resolves when used."""
    from . import persistence as _p
    return _p.SAVE_DIR


def acquire_instance_lock():
    """Claim the save dir for this process.  Returns the OTHER live pid when a
    second copy already runs (two instances autosave over one file,
    last-write-wins -- sweep 2026-07-14), else records our pid and returns
    None.  Doubt resolves to 'not locked': wrongly blocking a player is worse
    than the old free-for-all."""
    p = os.path.join(_live_save_dir(), _LOCK_NAME)
    try:
        other = int(open(p).read().strip())
    except (OSError, ValueError):
        other = None
    if other and other != os.getpid():
        try:
            os.kill(other, 0)
            return other             # alive: the save is claimed
        except PermissionError:
            return other             # alive, just not ours to signal
        except OSError:
            pass                     # stale lock from a dead run
    try:
        os.makedirs(_live_save_dir(), exist_ok=True)
        with open(p, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass                         # unwritable dir: nothing to fight over either
    return None

def release_instance_lock():
    """Drop the pid file, but only if it is ours (best-effort)."""
    p = os.path.join(_live_save_dir(), _LOCK_NAME)
    try:
        if int(open(p).read().strip()) == os.getpid():
            os.remove(p)
    except (OSError, ValueError):
        pass

def write_crash_log(exc):
    """Write the full traceback to crash.log in the save dir (one file, newest
    crash wins).  Returns the path, or None when the disk refused."""
    import traceback
    try:
        os.makedirs(_live_save_dir(), exist_ok=True)
        p = os.path.join(_live_save_dir(), "crash.log")
        with open(p, "w", encoding="utf-8") as f:
            f.write("tuipet crash — %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        return p
    except OSError:
        return None
