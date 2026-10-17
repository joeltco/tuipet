"""Bounded panel cue transport; reading a cue remains compatible with old panels."""
from collections import deque


class CueQueue:
    @property
    def sfx(self):
        cues = getattr(self, "_sfx_queue", ())
        return cues[-1] if cues else None

    @sfx.setter
    def sfx(self, cue):
        if cue is None:
            self._sfx_queue = deque(maxlen=8)
        else:
            if not hasattr(self, "_sfx_queue"):
                self._sfx_queue = deque(maxlen=8)
            self._sfx_queue.append(cue)


def drain(panel):
    cues = list(getattr(panel, "_sfx_queue", ()))
    if not cues:
        cue = getattr(panel, "sfx", None)
        cues = [cue] if cue else []
    panel.sfx = None
    return cues


def bubble(parent, child):
    for cue in drain(child):
        parent.sfx = cue


def position(panel):
    """Only menu position/ownership counts as generic keyboard feedback."""
    fields = ("cursor", "top", "off", "offset", "page", "tab", "scroll", "phase", "sel", "pos", "i", "section")
    values = tuple(getattr(panel, key, None) for key in fields)
    child = getattr(panel, "sub", None)
    return values, id(child), position(child) if child is not None else None


def passive(panel):
    child = getattr(panel, "sub", None) or getattr(panel, "bshow", None)
    return passive(child) if child is not None else getattr(panel, "phase", None) in (
        "intro", "anim", "show")


def crossed(fx):
    for beat in range(fx.get("prev", fx["step"] - 1) + 1, fx["step"] + 1):
        for field in ("bite_snds", "snds"):
            cue = fx.get(field, {}).get(beat)
            if cue:
                yield cue


def discard(panel):
    drain(panel)
    for field in ("sub", "bshow"):
        child = getattr(panel, field, None)
        if child is not None:
            discard(child)
