"""Check PyPI for a newer tuipet release, so the HUD can nudge the player.

Network- and dependency-free (stdlib urllib only) and fail-soft: any error —
offline, PyPI down, source/dev install with no package metadata — returns None
so the game never blocks or crashes on the check.
"""
from __future__ import annotations
import json
import urllib.request
from importlib.metadata import version, PackageNotFoundError

PYPI_JSON = "https://pypi.org/pypi/tuipet/json"


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
        with urllib.request.urlopen(req, timeout=timeout) as r:
            latest = json.load(r)["info"]["version"]
    except Exception:
        return None                      # offline / PyPI hiccup / parse error -> stay quiet
    try:
        return latest if _key(latest) > _key(cur) else None
    except Exception:
        return latest if latest != cur else None
