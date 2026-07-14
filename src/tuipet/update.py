"""Check PyPI for a newer tuipet release, so the HUD can nudge the player.

Network- and dependency-free (stdlib urllib only) and fail-soft: any error —
offline, PyPI down, source/dev install with no package metadata — returns None
so the game never blocks or crashes on the check.
"""
from __future__ import annotations
import json
import os
import subprocess  # nosec B404 - fixed argv from our own detection, no shell, no user input
import sys
import urllib.request
from importlib.metadata import version, PackageNotFoundError

from . import hostinfo

PYPI_JSON = "https://pypi.org/pypi/tuipet/json"

# the one place we actually shell out.  Indirected so the test suite can block
# it outright (conftest.never_run_pip): a test that forgot to mock the updater
# REALLY RAN pip once and upgraded tuipet inside .venv-dev mid-suite.  Patching
# `update.subprocess.run` would hit the shared module and break every other
# subprocess user (sound, the lobby harness), so the hook lives here.
_RUN = subprocess.run


def current_version():
    """Installed tuipet version, or None when running from source (no metadata)."""
    try:
        return version("tuipet")
    except PackageNotFoundError:
        return None


def _key(v):
    """Loose version tuple: numeric lead of each dotted part ('0.2.0' -> (0,2,0))."""
    out = []
    for part in v.split("."):
        digits = ""
        for c in part:
            if c.isdigit():
                digits += c
            else:
                break
        out.append(int(digits) if digits else 0)
    return tuple(out)


def latest_if_newer(timeout=4.0):
    """Return the PyPI version string if it is newer than the installed one,
    else None.  Never raises."""
    cur = current_version()
    if not cur:
        return None                      # dev/source run: nothing to compare against
    try:
        req = urllib.request.Request(PYPI_JSON, headers={"User-Agent": "tuipet-update-check"})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310 - constant https PyPI URL, not user input
            latest = json.load(r)["info"]["version"]
    except Exception:
        return None                      # offline / PyPI hiccup / parse error -> stay quiet
    try:
        return latest if _key(latest) > _key(cur) else None
    except Exception:
        return latest if latest != cur else None


# ---- actually installing it (Joel 2026-07-13: "make the update option
# actually update the game") -------------------------------------------------
# The right command depends on HOW tuipet was installed, and getting it wrong
# either does nothing or upgrades the wrong environment.  We detect rather than
# guess, and refuse honestly when we cannot do it.

def install_method():
    """('pipx' | 'uv' | 'pip' | 'source' | 'blocked'), plus why.

    * source  -- running from a checkout: there is no release to install over.
    * blocked -- iOS (a-Shell) gives Python no way to spawn a process at all,
                 so the player must run pip themselves.
    """
    if not current_version():
        return "source"
    if hostinfo.is_ios():
        return "blocked"
    prefix = (sys.prefix or "").replace("\\", "/")
    # pipx and uv keep each tool in its OWN venv; upgrading with the venv's own
    # python hits exactly that venv, which is what we want in both cases.
    if "/pipx/" in prefix or "/pipx-" in prefix:
        return "pipx"
    if "/uv/tools/" in prefix:
        return "uv"
    return "pip"


def upgrade_argv():
    """The exact command to run, or None when we must not run one."""
    how = install_method()
    if how in ("source", "blocked"):
        return None
    # `<this venv's python> -m pip` upgrades the environment tuipet ACTUALLY
    # runs in -- true for a plain pip install and for a pipx/uv tool venv alike
    # -- where a bare `pip` might belong to some other python entirely.
    return [sys.executable, "-m", "pip", "install", "-U", "--no-input", "tuipet"]


def manual_command():
    """What to tell the player to type when we cannot do it for them."""
    how = install_method()
    if how == "source":
        return "git pull (you are running from source)"
    if how == "pipx":
        return "pipx upgrade tuipet"
    if how == "uv":
        return "uv tool upgrade tuipet"
    return "pip install -U tuipet"


def run_upgrade(timeout=180.0):
    """Install the newest tuipet into the environment we are running in.

    Returns (ok, message).  Never raises.  The running process keeps executing
    the OLD code -- Python has already imported it -- so a successful upgrade
    always ends with 'restart tuipet', never a silent half-swap.
    """
    argv = upgrade_argv()
    if argv is None:
        return False, "Update by hand: " + manual_command()
    try:
        r = _RUN(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,  # nosec B603 - fixed argv, no shell
                 stdin=subprocess.DEVNULL, timeout=timeout,
                 env=dict(os.environ, PIP_DISABLE_PIP_VERSION_CHECK="1"))
    except subprocess.TimeoutExpired:
        return False, "Update timed out. Try: " + manual_command()
    except Exception:
        # no pip in this environment, a locked-down host, whatever it was: say
        # so and hand back the command, rather than pretending we updated
        return False, "Couldn't run the updater. Try: " + manual_command()
    if r.returncode != 0:
        tail = (r.stdout or b"").decode("utf-8", "replace").strip().splitlines()
        why = tail[-1][:60] if tail else "pip failed"
        return False, f"Update failed ({why}). Try: " + manual_command()
    return True, "Updated — restart tuipet to play the new version."
