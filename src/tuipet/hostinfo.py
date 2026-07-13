"""Which machine are we actually on?

One place for the host questions the app and the sound backend both ask, so
they can never disagree (and so sound.py needn't import app.py, which imports
sound.py).  iOS support 2026-07-13.
"""
from __future__ import annotations

import os
import platform


def is_ios():
    """a-Shell on iPhone/iPad -- our official iOS target.

    iOS reports itself as 'Darwin', exactly like a Mac, so this has to look
    harder: the machine string (iPhone15,2), a-Shell's $SHORTCUTS, or a HOME
    that sits inside an app container.
    """
    if platform.system() != "Darwin":
        return False
    if (platform.machine() or "").startswith(("iPhone", "iPad", "iPod")):
        return True
    if os.environ.get("SHORTCUTS"):
        return True
    home = os.path.expanduser("~")
    return "/Containers/" in home or "/Application/" in home


def is_termux():
    return os.environ.get("PREFIX", "").endswith("com.termux/files/usr")


def is_ssh():
    return bool(os.environ.get("SSH_CONNECTION")
                or os.environ.get("SSH_TTY")
                or os.environ.get("SSH_CLIENT"))


def host_platform():
    """The platform name for bug reports -- iOS players reported as 'Darwin'
    were indistinguishable from Macs, so they were invisible in the feed."""
    if is_ios():
        return "iOS"
    if is_termux():
        return "Termux"
    return platform.system()
