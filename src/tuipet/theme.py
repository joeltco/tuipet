"""Central UI palette + runtime theme switching (no green).

One source of truth for every colour in the app. Screens import the derived
names (LCD_ON/LCD_BG/INK/INK_B/DIM/SEL/...) from here. `apply()` swaps the live
theme by rewriting those names in this module AND in every already-loaded screen
module, so a switch takes effect on the next repaint.
"""
import os
import sys

# Each theme: ink/screen/mid + accent, pos/neg (affinity), border (bezel),
# silhouette ink over scene art, and the STATUS readout colours
# (heart/energy/mood/life/coin).  The per-weather tints, precip inks and
# per-phase palettes retired with their systems (Great Simplification
# 2026-07-15).
THEMES = {
    "grey": {
        "on": "#2b2e31", "bg": "#c6c9cc", "mid": "#7d8186",
        "accent": "#b04a3a", "pos": "#3a6ea5", "neg": "#a23b2f", "border": "#7a7e78",
        "sil_day": "#2b2e31", "sil_night": "#e4e7ea",
        "heart": "#c25a4a", "energy": "#4a90c2", "mood": "#a06ac2", "life": "#3f9a86", "coin": "#c2a24a",
        "void": "#000000", "flash": ("#f2f6fa", "#1a2026", "#e8eef2"),
    },
    "mono": {
        "on": "#e8e8e8", "bg": "#0c0c0c", "mid": "#808080",
        "accent": "#d05a3a", "pos": "#7fa8d8", "neg": "#d05a3a", "border": "#333333",
        "sil_day": "#101010", "sil_night": "#f0f0f0",
        "heart": "#d8d8d8", "energy": "#b8b8b8", "mood": "#a8a8a8", "life": "#c8c8c8", "coin": "#e8e8e8",
        "void": "#000000", "flash": ("#ffffff", "#0c0c0c", "#e8e8e8"),
    },
    "amber": {
        "on": "#ffb000", "bg": "#1a1206", "mid": "#9a6b18",
        "accent": "#ff6a3a", "pos": "#8fd0ff", "neg": "#ff6a3a", "border": "#3a2a0c",
        "sil_day": "#2a1c06", "sil_night": "#ffd877",
        "heart": "#ff7a3a", "energy": "#ffb000", "mood": "#e0923a", "life": "#ffc24a", "coin": "#ffd877",
        "void": "#000000", "flash": ("#ffe8b0", "#1a1206", "#ffd890"),
    },
    "midnight": {
        "on": "#a9c8ee", "bg": "#101826", "mid": "#5d7491",
        "accent": "#e0884a", "pos": "#7fb0e0", "neg": "#e06a5a", "border": "#2a3850",
        "sil_day": "#16202e", "sil_night": "#cfe0f5",
        "heart": "#e0884a", "energy": "#6fb0e0", "mood": "#9a8fe0", "life": "#5fc7b0", "coin": "#e0c060",
        "void": "#000000", "flash": ("#dce8f8", "#101826", "#c8d8f0"),
    },
    # the classic 4-shade DMG pea-soup LCD (the default stays grey; this is
    # an option).  NB the v0.2.284 putty-shell chrome experiment was REVERTED
    # (Joel 2026-07-05: "this looks bad") -- gameboy rides the fallbacks.
    "gameboy": {
        "on": "#0f380f", "bg": "#9bbc0f", "mid": "#306230",
        "accent": "#7a3a22", "pos": "#2a5a8a", "neg": "#8a3a2a", "border": "#4a5a28",
        "sil_day": "#0f380f", "sil_night": "#d8e8a0",
        "heart": "#8a4a2a", "energy": "#2a6a8a", "mood": "#6a4a8a", "life": "#306230", "coin": "#8a7a1a",
        "void": "#0f380f", "flash": ("#e0f0c0", "#0f380f", "#d8e8a0"),
        # GB layering (redo 2026-07-05: 4-shade backgrounds ATE the sprites --
        # "their blending into the background"): backgrounds get the LIGHT
        # three shades only; the darkest DMG green belongs to sprites alone,
        # so the mon is always the darkest thing on the LCD
        "bg_ramp": ("#306230", "#8bac0f", "#9bbc0f"),
    },
    "paper": {
        "on": "#2a2620", "bg": "#efe9dc", "mid": "#8a8274",
        "accent": "#a04a2a", "pos": "#3a6a8a", "neg": "#a03a2a", "border": "#b8ac97",
        "sil_day": "#2a2620", "sil_night": "#f4efe4",
        "heart": "#a04a2a", "energy": "#3a6a8a", "mood": "#7a5a92", "life": "#567a68", "coin": "#967a2a",
        "void": "#000000", "flash": ("#ffffff", "#2a2620", "#faf6ec"),
        # paper layering (Joel 2026-07-12: "apply this to the paper theme --
        # white instead of green"): backgrounds get the light ink-wash trio,
        # the near-black ink stays sprite-only, same law as gameboy
        "bg_ramp": ("#8a8274", "#d5cdbb", "#efe9dc"),
    },
    "sakura": {
        "on": "#f0b8c8", "bg": "#241820", "mid": "#8a5a6c",
        "accent": "#ff8a5a", "pos": "#8ac8e8", "neg": "#ff6a6a", "border": "#4a2a3a",
        "sil_day": "#2a1a24", "sil_night": "#ffd0dc",
        "heart": "#ff7a8a", "energy": "#8ac8e8", "mood": "#c89ae8", "life": "#7ad0b0", "coin": "#f0c86a",
        "void": "#000000", "flash": ("#ffe8f0", "#241820", "#f8d8e4"),
    },
    "ocean": {
        "on": "#7fd8d0", "bg": "#0a1e22", "mid": "#3f7a78",
        "accent": "#f0a05a", "pos": "#8ab8f0", "neg": "#f07a5a", "border": "#1c3a3e",
        "sil_day": "#0f2a2e", "sil_night": "#c8f0e8",
        "heart": "#f07a6a", "energy": "#6ac8e0", "mood": "#9a9ae8", "life": "#5ad0a0", "coin": "#e8c86a",
        "void": "#000000", "flash": ("#e0f8f4", "#0a1e22", "#c8ece6"),
    },
}
_DEFAULT = "grey"
_ORDER = list(THEMES)
_current = _DEFAULT

_NAMES = ("LCD_ON", "LCD_BG", "MID", "INK", "INK_B", "DIM", "SEL", "ACCENT",
          "POS", "NEG", "BORDER", "SIL_DAY", "SIL_NIGHT",
          "HEART", "ENERGY", "MOOD", "LIFE", "COIN", "VOID", "FLASH",
          "BEZEL", "SHELL", "LABEL", "KEY")
# (the hand-maintained _SCREEN_MODULES registry is gone -- apply() discovers
# palette-bound modules from sys.modules; hardening 2026-07-05)

# Static declarations of the palette names so linters/type-checkers can see them.
# apply(_DEFAULT) runs at import (bottom of file) and overwrites these with the live
# theme via globals().update(_derive(...)); they are never actually the empties below.
LCD_ON = LCD_BG = MID = INK = INK_B = DIM = SEL = ACCENT = POS = NEG = BORDER = ""
SIL_DAY = SIL_NIGHT = HEART = ENERGY = MOOD = LIFE = COIN = VOID = ""
BEZEL = SHELL = LABEL = KEY = ""
FLASH: tuple = ("", "", "")



def _derive(t):
    on, bg, mid = t["on"], t["bg"], t["mid"]
    return {
        "LCD_ON": on, "LCD_BG": bg, "MID": mid,
        "INK": f"{on} on {bg}", "INK_B": f"bold {on} on {bg}",
        "DIM": f"{mid} on {bg}", "SEL": f"bold {bg} on {on}",
        "ACCENT": t["accent"], "POS": t["pos"], "NEG": t["neg"], "BORDER": t["border"],
        "SIL_DAY": t["sil_day"], "SIL_NIGHT": t["sil_night"],
        "HEART": t["heart"], "ENERGY": t["energy"], "MOOD": t["mood"],
        "LIFE": t["life"], "COIN": t["coin"],
        "VOID": t["void"], "FLASH": t["flash"],
        # shell chrome (optional per theme; the plain themes keep border/mid):
        # bezel = the LCD's thick frame, shell = the outer boxes, label = the
        # printed titles/key-hint text, key = the action-bar shortcut letters
        # (the DMG shell polish, 2026-07-05)
        "BEZEL": t.get("bezel", t["border"]),
        "SHELL": t.get("shell", t["border"]),
        "LABEL": t.get("label", t["mid"]),
        "KEY": t.get("key", "cyan"),
    }


_BG_QUANT: dict = {}         # (theme, frame) -> quantized frame memo


def themed_bg(frame):
    """Background art under the active theme: full colour normally; a theme
    that declares `bg_ramp` (gameboy: the light DMG shades; paper: the ink-
    wash whites) gets the frame clustered onto the ramp as CLEAN SHAPES --
    per-frame colour clustering with a majority-vote smoothing pass, so
    scenery reads like hand-tiled GB art.  (The redo history, all Joel:
    flat absolute bands = mud; Bayer dither = static at 40x24 -- "it looks
    like garbage" [2026-07-05]; luminance banding = hue-blind flattening --
    "some backgrounds look like shit" [2026-07-12].)  Frame-level and
    memoized; render._paint_cells is the one caller, so weather tints,
    cross-fades and lightning blends all inherit the palette."""
    ramp = THEMES[_current].get("bg_ramp")
    if not ramp or not frame:
        return frame
    key = (_current, tuple(frame))
    v = _BG_QUANT.get(key)
    if v is None:
        if len(_BG_QUANT) > 512:              # cross-fades mint transient frames
            _BG_QUANT.clear()
        v = _quant_frame(frame, ramp)
        _BG_QUANT[key] = v
    return v


def _quant_frame(frame, ramp):
    """Deterministic per-frame COLOUR clustering onto the ramp (redo
    2026-07-12).  The old luminance banding was hue-blind: features that
    differ in colour but not brightness merged into one flat shade (the
    desert\'s dunes vs its sky, digicoreDa\'s dark core vs its blue bricks),
    and its contrast stretch amplified near-flat texture noise into random
    blotches.  Now: k-means (k = ramp size) in RGB, seeded at luminance
    percentiles so runs are stable, finds the frame\'s actual colour
    structure; clusters whose centres nearly coincide MERGE (a flat frame
    renders flat, not blotchy); groups rank dark-to-light onto the ramp --
    a luminance near-tie goes to the group sitting higher on screen, so
    skies read light (the GB idiom) -- and the 3x3 majority vote on the
    shade indices keeps the chunky authored look."""
    n = len(ramp)
    h = len(frame)
    w = len(frame[0]) // 6
    pts = []
    for row in frame:
        for x in range(0, w * 6, 6):
            pts.append((int(row[x:x + 2], 16), int(row[x + 2:x + 4], 16),
                        int(row[x + 4:x + 6], 16)))

    def lum(c):
        return (299 * c[0] + 587 * c[1] + 114 * c[2]) / 255000.0

    # deterministic k-means, farthest-point seeded: hue-diverse starts even
    # when luminance is narrow (percentile-of-luminance seeds collapsed the
    # savanna/underwater scenes to one flat shade -- same-brightness hues
    # need seats too)
    def d2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2

    fit = pts[::4] if len(pts) >= 4 * n else pts   # centres fit on a sample --
    mean = (sum(p[0] for p in fit) / len(fit),     # cross-fades quantize a fresh
            sum(p[1] for p in fit) / len(fit),     # transient frame every tick
            sum(p[2] for p in fit) / len(fit))
    seeds = [max(fit, key=lambda p: d2(p, mean))]
    while len(seeds) < n:
        seeds.append(max(fit, key=lambda p: min(d2(p, q) for q in seeds)))
    centers = [tuple(float(v) for v in q) for q in seeds]
    for _ in range(10):
        sums = [[0.0, 0.0, 0.0, 0] for _ in range(n)]
        for p in fit:
            j = min(range(n), key=lambda k: d2(p, centers[k]))
            s_ = sums[j]
            s_[0] += p[0]; s_[1] += p[1]; s_[2] += p[2]; s_[3] += 1
        moved = 0.0
        for j, (r, g, b, cnt) in enumerate(sums):
            if not cnt:
                continue                     # empty seat: parked, excluded below
            c = (r / cnt, g / cnt, b / cnt)
            moved += sum(abs(c[i] - centers[j][i]) for i in range(3))
            centers[j] = c
        if moved < 1.0:
            break
    assign = [min(range(n), key=lambda k: d2(p, centers[k])) for p in pts]
    counts = [0] * n
    for j in assign:
        counts[j] += 1
    # a farthest-point seed can be a lone outlier pixel: a cluster under 1%
    # of the frame is noise, not a shape -- fold it into its nearest neighbour
    floor = max(4, len(pts) // 100)
    live = [j for j in range(n) if counts[j]]
    for j in range(n):
        if counts[j] and counts[j] < floor and len(live) > 1:
            near = min((k for k in live if k != j),
                       key=lambda k: d2(centers[j], centers[k]))
            for i, a in enumerate(assign):
                if a == j:
                    assign[i] = near
            counts[near] += counts[j]
            counts[j] = 0
            live.remove(j)

    # merge near-coincident clusters: ~10/channel is texture noise, not shape
    MERGE = 30.0
    root = list(range(n))

    def find(a):
        while root[a] != a:
            a = root[a]
        return a

    for a in range(n):
        for b in range(a + 1, n):
            if not counts[a] or not counts[b]:
                continue
            d = sum((centers[a][i] - centers[b][i]) ** 2 for i in range(3)) ** 0.5
            if d < MERGE:
                root[find(b)] = find(a)

    rowsum = [0] * n
    for i, j in enumerate(assign):
        rowsum[j] += i // w
    groups = {}
    for j in range(n):
        if counts[j]:
            groups.setdefault(find(j), []).append(j)
    ginfo = []                               # [members, luma, mean row, size]
    for members in groups.values():
        cnt = sum(counts[j] for j in members)
        gl = sum(lum(centers[j]) * counts[j] for j in members) / cnt
        ry = sum(rowsum[j] for j in members) / cnt
        ginfo.append([members, gl, ry, cnt])
    ginfo.sort(key=lambda g: g[1])
    for i in range(len(ginfo) - 1):          # sky idiom: on a luma near-tie the
        a, b = ginfo[i], ginfo[i + 1]        # group sitting HIGHER on screen
        if b[1] - a[1] < 0.05 and a[2] < b[2]:   # takes the lighter shade
            ginfo[i], ginfo[i + 1] = b, a

    m = len(ginfo)
    if max(g[3] for g in ginfo) > 0.60 * len(pts):
        # a flat field with accents (one colour owns the frame): every group
        # sits at its ABSOLUTE lightness and groups may share a shade -- a
        # near-flat frame renders flat.  Rank-spreading here manufactured
        # contrast that is not in the art (digicoreVb, a faint white-on-white
        # glow, grew a dark ring).  Accent groups take the ADJACENT shade in
        # their true direction -- features stay visible (egg10Back, a door on
        # a wall), at neighbour contrast, never across the whole ramp
        fi = max(range(m), key=lambda i: ginfo[i][3])
        base = min(n - 1, round(ginfo[fi][1] * (n - 1)))
        slots = [max(0, min(n - 1, base + (1 if g[1] > ginfo[fi][1] else -1)))
                 for g in ginfo]
        slots[fi] = base
    elif m >= n:                             # balanced scenery: full-span rank
        slots = list(range(n))
    else:                                    # fewer shapes than shades: place by
        slots = [min(n - 1, round(g[1] * (n - 1))) for g in ginfo]   # absolute luma,
        for i in range(1, m):                                        # keep distinct
            slots[i] = max(slots[i], slots[i - 1] + 1)
        over = slots[-1] - (n - 1)
        if over > 0:
            slots = [max(0, s_ - over) for s_ in slots]
            for i in range(1, m):
                slots[i] = max(slots[i], slots[i - 1] + 1)
    slot_of = {}
    for (members, _, _, _), sl in zip(ginfo, slots):
        for j in members:
            slot_of[j] = sl

    idx = [[slot_of[assign[y * w + x]] for x in range(w)] for y in range(h)]
    strip = [c[1:] for c in ramp]            # bare 6-hex cells for row concat
    out = []
    for y in range(h):                       # 3x3 majority vote: chunky, authored
        cells = []
        for x in range(w):
            votes = [0] * n
            for yy in range(max(0, y - 1), min(h, y + 2)):
                for xx in range(max(0, x - 1), min(w, x + 2)):
                    votes[idx[yy][xx]] += 1
            best = max(range(n), key=lambda i: (votes[i], i == idx[y][x]))
            cells.append(strip[best])
        out.append("".join(cells))
    return out


def apply(name, propagate=True):
    """Make `name` the live theme. Rewrites this module's colour names and (when
    propagate) pushes them into every already-loaded screen module.

    Screens are DISCOVERED, not listed: any loaded tuipet module that bound
    LCD_ON or INK at import gets retinted.  The old hand-maintained
    _SCREEN_MODULES tuple failed SILENTLY when a new screen wasn't registered
    -- it kept its import-time colours on theme switch (hardening 2026-07-05)."""
    global _current
    if name not in THEMES:
        name = _DEFAULT
    _current = name
    vals = _derive(THEMES[name])
    globals().update(vals)
    if propagate:
        pkg = __name__.rsplit(".", 1)[0] + "."
        for mname, mod in list(sys.modules.items()):
            if (mod is None or not mname.startswith(pkg)
                    or mname == __name__
                    or not (hasattr(mod, "LCD_ON") or hasattr(mod, "INK"))):
                continue
            for k in _NAMES:
                if hasattr(mod, k):
                    setattr(mod, k, vals[k])
    return name


def current():
    return _current


def names():
    return list(_ORDER)



def blend_frame(frame, hexcol, a):
    """Blend a full-colour frame (rows of 6-hex-char cells) toward `hexcol` by
    alpha `a`.  Used by the arena's background cross-fade."""
    tr, tg, tb = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    out = []
    for row in frame:
        cells = []
        for i in range(0, len(row), 6):
            r = int(row[i:i + 2], 16); g = int(row[i + 2:i + 4], 16); b = int(row[i + 4:i + 6], 16)
            cells.append("%02x%02x%02x" % (int(r + (tr - r) * a), int(g + (tg - g) * a), int(b + (tb - b) * a)))
        out.append("".join(cells))
    return out


def blend_frames(fa, fb, a):
    """Cell-wise lerp between two equal-shaped frames (rows of 6-hex-char
    cells) -- the interpolant for the background cross-fade."""
    if a <= 0:
        return fa
    if a >= 1:
        return fb
    out = []
    for ra, rb in zip(fa, fb):
        cells = []
        for i in range(0, len(ra), 6):
            r1, g1, b1 = int(ra[i:i + 2], 16), int(ra[i + 2:i + 4], 16), int(ra[i + 4:i + 6], 16)
            r2, g2, b2 = int(rb[i:i + 2], 16), int(rb[i + 2:i + 4], 16), int(rb[i + 4:i + 6], 16)
            cells.append("%02x%02x%02x" % (int(r1 + (r2 - r1) * a), int(g1 + (g2 - g1) * a), int(b1 + (b2 - b1) * a)))
        out.append("".join(cells))
    return out


# --- persistence of the chosen theme ---
_CONF = os.path.expanduser("~/.local/share/tuipet/theme.txt")


def save_choice(name):
    try:
        os.makedirs(os.path.dirname(_CONF), exist_ok=True)
        with open(_CONF, "w") as fh:
            fh.write(name)
    except OSError:
        pass


def load_choice():
    try:
        n = open(_CONF).read().strip()
        return n if n in THEMES else _DEFAULT
    except OSError:
        return _DEFAULT


# initialise module-level names at import (default theme); don't propagate yet.
apply(_DEFAULT, propagate=False)
