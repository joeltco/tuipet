"""DigiCore — tuipet's core readout and paged data book.

The CORE page uses the imported field-
flavoured core backdrop (ViewUtil.getDigicoreBackground picks it by the pet's
HIGHEST DNA field, falling back to its own), the core badge (a special core
from digicoreMenuConfig.csv, else the X-antibody state badge), and the core
NUMBER — with a pending evolution it counts DOWN from DigicoreBaseRate 14 as
the growth period elapses; past growth (or a final form) it counts UP through
the days toward the elder line (age-based since the DSprite mortality port
2026-07-22).  Pressing the core plays the silhouette teaser
(EvolSilhouetteTransition): a potential evolution as a blacked-out shape.
The data-book pages after it are tuipet's own readout (kept adaptation).
"""
from __future__ import annotations
from rich.console import Console
from rich.text import Text
from rich.cells import cell_len, set_cell_size
from . import data
from . import digicore as core
from . import grid, evolution, lines  # noqa: F401  (the gaze + checklists read them)
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_SCENE, SIL_LIGHTSOFF, VOID  # noqa: F401  (theme.apply propagation)
from . import menu

SCENE_ROWS = 12                    # the core/teaser pages own the WHOLE arena now --
#                                    Joel 2026-07-05: the 8-row band crammed a 16px mon
#                                    against the chrome; scene-only + strip() instead
EXPAND_T = 8                       # digicoreExpand: the badge zooms in (canon beats 6-14)
MON_T = 10                         # the gaze opens ON the current mon before the core turns
BACK_T = 6                         # evolSilhouetteBack: the dark blink on the way out
DET_VIS = 8                        # requirement-checklist rows shown at once
_WRAP = Console()


def _wrapped(txt, width):
    # DigiCore audit 2026-10-14: wrap terminal cells, never discard a tail.
    return Text(str(txt)).wrap(_WRAP, width, overflow="fold", no_wrap=False)


def _data_lines(rows):
    out = []
    for label, val in rows:
        gutter = max(10, min(menu.W - 2, cell_len(label) + 2))
        for i, part in enumerate(_wrapped(val, menu.W - gutter)):
            text = Text(set_cell_size(" " + label if i == 0 else "", gutter), style=DIM)
            text.append(part.plain + "\n", style=INK_B)
            out.append(text)
    return out

# the data model lives in digicore.py (modularized 2026-07-17); the old
# names stay importable for callers and the test suite
DIGICORE_BASE_RATE = core.DIGICORE_BASE_RATE
core_number = core.core_number
core_badge_key = core.core_badge_key
core_background = core.core_background
silhouette = core.silhouette
ghost = core.ghost
next_evolution = core.next_evolution
_mins = core._mins
_evo_rows = core._evo_rows
_trophy_rows = core._trophy_rows
_legacy_rows = core._legacy_rows
build_pages = core.build_pages


class DigiCorePanel:
    def __init__(self, pet, start="CORE"):
        self.pet = pet
        self.pages = [("CORE", None)] + build_pages(pet)
        # start lands on a page by TITLE (the album round-trip reopens the
        # book on TROPHIES, not the cover); unknown titles fall to the cover
        self.i = next((j for j, (t, _) in enumerate(self.pages) if t == start), 0)
        self.teaser = False       # EvolSilhouette view (SPACE on the core)
        self.teaser_t = 0         # ticks into the digicoreExpand zoom
        self._back_t = 0          # evolSilhouetteBack dark-blink ticks left
        self.frame_i = 0
        self.note = "the core stirs…"
        self._keys = [("SPACE", "gaze"), ("←→", "page"), ("ESC", "back")]  # set by text()
        self.evo_sel = 0          # EVOLVES page: the highlighted candidate
        self.detail = None        # (num, name): the open requirement checklist
        self.det_off = 0          # ...and its scroll offset
        self.row_off = 0          # wrapped data rows share the book's scroll keys

    def anim(self):
        self.frame_i += 1
        if self.teaser:
            self.teaser_t += 1
        if self._back_t:
            self._back_t -= 1

    def key(self, k):
        if self.teaser:
            if k in ("escape", "space", "enter", "d"):
                self.teaser = False           # EvolSilhouetteBack: dark blink out
                self._back_t = BACK_T
                self.sfx = "wash"             # _silhouetteFade has no rip; wash substitutes
            return None
        if k in ("space", "enter") and self.i == 0:
            # onDigicore -> EvolSilhouetteTransition (the fade sound has no rip;
            # the dna-wash sweep substitutes, like heal's click/confirm cues)
            self.teaser = True
            self.teaser_t = 0                 # the badge zooms in first (digicoreExpand)
            self.sfx = "wash"
            return None
        if k == "m" and self.i == 0:
            # the tModeChange button on the EvolutionState page
            if not self.pet.can_mode_change():
                return None
            old_num, msg = self.pet.mode_change()
            if old_num is not None:
                return ("done", ("evolve", old_num, msg))
            self.note = msg
            # DigiCore audit 2026-10-14: refusals can spend manners/disturb.
            self.pages = [("CORE", None)] + build_pages(self.pet)
            self.sfx = "error"
            return None
        if self.detail is not None:                    # the requirement checklist
            if k in ("up", "k"):
                self.det_off = max(0, self.det_off - 1)
            elif k in ("down", "j"):
                self.det_off += 1                      # text() clamps to the list
            elif k == "pageup":                        # page jumps, lobby-chat style
                self.det_off = max(0, self.det_off - (DET_VIS - 1))
            elif k == "pagedown":
                self.det_off += DET_VIS - 1            # text() clamps to the list
            elif k in ("escape", "enter", "space", "d"):
                self.detail = None
                self.det_off = 0
            return None
        on_evo = self.pages[self.i][0] == "EVOLVES"
        rows = self.pages[self.i][1] if on_evo else None
        if on_evo and isinstance(rows, list) and rows:
            if k in ("up", "k"):
                self.evo_sel = (self.evo_sel - 1) % len(rows)
                return None
            if k in ("down", "j"):
                self.evo_sel = (self.evo_sel + 1) % len(rows)
                return None
            if k == "enter":
                num, name = rows[self.evo_sel][0], rows[self.evo_sel][1]
                self.detail = (num, name)
                self.det_off = 0
                return None
        if k == "enter" and self.pages[self.i][0] == "TROPHIES":
            # the album count's book (2026-07-21): ENTER opens it, SPACE
            # keeps paging — the EVOLVES enter-picks/space-pages split
            return ("done", ("album",))
        if k == "enter" and self.pages[self.i][0] == "LEGACY":
            # the headstones' room (Joel 2026-07-26): ENTER opens the HALL
            # OF MEMORY — the TROPHIES→ALBUM door's exact grammar
            return ("done", ("hall",))
        if k in ("up", "k", "pageup"):
            self.row_off = max(0, self.row_off - (7 if k == "pageup" else 1))
            return None
        if k in ("down", "j", "pagedown"):
            self.row_off += 7 if k == "pagedown" else 1
            return None
        if k in ("right", "l") or (k == "space" and self.i > 0):
            self.i = (self.i + 1) % len(self.pages)
            self.row_off = 0
        elif k in ("left", "h"):
            self.i = (self.i - 1) % len(self.pages)
            self.row_off = 0
        elif k in ("escape", "d"):
            return ("done", None)
        return None

    def _pet_rows(self, num, idx=None):
        if idx is None or num == -1:
            # WALK_BEAT bob; bob_frame owns the egg's shell art (num -1 has
            # no roster sheet -- the gaze rendered an empty LCD, audit 2026-07-05)
            return data.bob_frame(num, self.frame_i,
                                  egg_type=getattr(self.pet, "egg_type", 0))
        rec = data.load_sprites()[1].get(num)
        if not rec:
            return None
        return rec["frames"][idx] or next((f for f in rec["frames"] if f), None)

    @staticmethod
    def _core_place(rows, cell=None):
        """Centre the FULL sprite on the core scene (cell 0/1 = that 16px cell,
        None = whole grid).  grid.center(ph=16) rides the grounded-2px floor
        rule (band_h = 14) and box-mushes every 16px-tall mon -- Joel's Devimon
        read as a broken blob (2026-07-04).  The core has no floor; native
        pixels, bottom on the scene edge."""
        s = grid._crop(rows)
        span, x0 = (grid.W, grid.X0) if cell is None else (grid.CELL, grid.X0 + cell * grid.CELL)
        return (s, x0 + (span - grid.width(s)) // 2, False)

    def _dots(self):
        return " ".join((chr(0x25CF) if j == self.i else chr(0x25CB))
                        for j in range(len(self.pages)))

    def _core_scene(self):
        """The CORE landing page -- a data-menu page like every other digicore
        page (Joel 2026-07-05: one layout language for the whole data book;
        the scene experiment read as inconsistent).  SPACE opens the core
        gaze, where the visuals live."""
        p = self.pet
        n = core_number(p)
        # DigiCore audit 2026-10-14: number and label use the game's clock.
        pending = core.growth_pending(p)
        x = getattr(p, "x_antibody", "None")
        # the number wears its own meaning (gameplay polish #16, 2026-07-22):
        # a bare "◆ 7" was a countdown-to-evolve on a growing pet and an
        # age-count on a final form -- same glyph, opposite directions,
        # with only the Meter row to disambiguate
        if pending:
            core_val = f"{chr(0x25C6)} {n} until {'hatching' if p.num == -1 else 'evolution'}"
        elif p.is_geriatric:
            core_val = f"{chr(0x25C6)} {n} — elder"
        else:
            core_val = f"{chr(0x25C6)} {n} of {DIGICORE_BASE_RATE} to elder"
        meter = "hatches at 1" if p.num == -1 else "can evolve at 1"
        if p.num == -1 and p.stage_seconds >= p.EGG_DURATION:
            meter = "incubation complete"
        if not pending:
            meter = "counts the days"
        if p.num != -1:
            if p.dead:
                meter = "growth ended"
            elif p.is_geriatric:
                meter = "growth held: elder"
            elif getattr(p, "evo_blocked", False):
                meter = "growth held: anti-evo"
            elif p.asleep:
                meter = "growth waits for waking"
        rows = [
            ("Core", core_val),
            ("Meter", meter),
            ("Field", data.pretty_field(getattr(p, "field", "") or "None")),
            ("X-State", "none" if x == "None" else x.lower()),
            ("Mode", ("press M" if p.can_mode_change() else chr(0x2014))),
        ]
        out = menu.header("DIGICORE  CORE", self._dots())
        rendered = _data_lines(rows)
        rendered += [Text("\n"), Text(" gaze into the core to glimpse\n", style=DIM),
                     Text(" what stirs within…\n", style=DIM)]
        # the door wears its key in BOLD (menu polish 2026-07-21: the gaze
        # was easy to look over in dim prose) -- the EVOLVES "ENTER: what it
        # takes" / TROPHIES "ENTER: the album" teaching line, gaze verdicts
        # still take the slot when one is pending
        # DigiCore audit 2026-10-14: mode verdict tails must not need a marquee.
        note = self.note if self.note != "the core stirs…" else "SPACE: gaze into the core"
        rendered += [Text(part.plain + "\n", style=INK_B) for part in _wrapped(note, menu.W)]
        self.row_off = menu.scroll_window(out, rendered, self.row_off, 9,
                                          lambda text, i: text)
        # keys live in ONE place, the hint strip (menus call #12 = A, 2026-10-15)
        self._keys = ([("↑↓", "scroll"), ("SPACE", "gaze"), ("ESC", "back")] if len(rendered) > 9
                      else [("SPACE", "gaze"), ("←→", "page"), ("ESC", "back")])
        out.append_text(menu.footer(""))
        return out

    def _teaser_scene(self):
        """EvolSilhouetteTransition: the core badge ZOOMS IN (digicoreExpand,
        canon beats 6-14 grow it 1.5x each), then the next natural evolution
        holds as a STATIC blacked-out shape (canon draws frame 0 -- the old
        pose-flicker here was the 10Hz flutter class)."""
        """The gaze (Joel 2026-07-05 round 3): the WHOLE LCD, nothing else --
        background, the current mon, the circle animation, the silhouette.
        Boom boom boom.  The narration rides the message box (it IS a
        message); no key hints anywhere."""
        p = self.pet
        bgimg = core_background(p)
        on = menu.scene_ink(bgimg)
        t = self.teaser_t
        if t < MON_T:                                     # beat one: the mon itself
            rows = self._pet_rows(p.num)
            placements = [self._core_place(rows)] if rows else []
            return render_scene(placements, 40, SCENE_ROWS, on, LCD_BG, bgimg=bgimg, clip=grid.WINDOW)
        if t < MON_T + EXPAND_T:                          # beat two: the core turns
            badge = data.load_effects().get(core_badge_key(p) or "core_xnone", [None])[0]
            overlay = []
            if badge:
                k = 1 + (t - MON_T) // (EXPAND_T // 2)    # 1x -> 2x zoom
                k = min(k, 2)
                big = ["".join(ch * k for ch in r) for r in badge for _ in range(k)]
                bw, bh = max(len(r) for r in big), len(big)
                ox, oy = (40 - bw) // 2, (SCENE_ROWS * 2 - bh) // 2
                overlay = [(ox + x, oy + y) for y, row in enumerate(big)
                           for x, c in enumerate(row) if c == "1" and oy + y >= 0]
            return render_scene([], 40, SCENE_ROWS, on, LCD_BG,
                                overlay=overlay, bgimg=bgimg)
        nxt = next_evolution(p)                           # beat three: what stirs
        if nxt is None:
            rows = self._pet_rows(p.num, idx=0)
            placements = [self._core_place(rows)] if rows else []
            return render_scene(placements, 40, SCENE_ROWS, on, LCD_BG, bgimg=bgimg, clip=grid.WINDOW)
        sil = ghost(silhouette(self._pet_rows(nxt, idx=0) or []),
                    phase=(self.frame_i // 5) % 2)
        placements = [self._core_place(sil)] if sil else []
        return render_scene(placements, 40, SCENE_ROWS, on, LCD_BG, bgimg=bgimg, clip=grid.WINDOW)

    def strip(self):
        """Narration only -- the gaze speaks through the message box; every
        other digicore state leaves it alone."""
        if self.detail is not None and not self.teaser:
            return menu.hints(("↑↓", "scroll"), ("ESC", "back"))
        if not self.teaser:
            self.text()                    # the page's keys are set as it draws
            return menu.hints(*self._keys)
        t = self.teaser_t
        if t < MON_T:
            return "the core stirs…"
        if t < MON_T + EXPAND_T:
            return "the core opens…"
        options = evolution.divergence_options(self.pet)
        if len(options) > 1:
            return f"One of {len(options)} DNA road forms may follow."
        return ("Nothing stirs — this is its final form."
                if next_evolution(self.pet) is None
                # a hint, never a promise: chance, care and partner doors can
                # all change the real road (Joel 2026-10-15, DigiCore call #7 = A)
                else "One possible future looms…")

    def _detail_scene(self):
        """One candidate's requirement checklist (evolution.requirement_report):
        met gates dim out of the way, the unmet ones are the raising guide."""
        from rich.text import Text
        num, name = self.detail
        if self.pet.num == -1:
            report = core.hatch_report(self.pet)
        elif num in evolution.divergence_options(self.pet):
            # the steer's own sheet: lines.requirement_report would say
            # "not in this line" -- true, and exactly the point; what
            # fires this jump is the charge (gameplay audit B3)
            report = core.divergence_report(self.pet)
        else:
            report = (lines.requirement_report(self.pet, num) if lines.active(self.pet)
                      else evolution.requirement_report(self.pet, num))
        vis = DET_VIS
        out = menu.header(f"DIGICORE  {name[:16].upper()}", "req")
        # DigiCore audit 2026-10-14: scroll every wrapped checklist fragment.
        report = [(met, part.plain) for met, txt in report
                  for part in _wrapped(txt, menu.W - 3)]

        def fmt(r, i):
            met, txt = r
            mark = {True: " " + chr(0x2713) + " ", False: " " + chr(0x2717) + " ",
                    None: "   "}[met]
            t = Text()
            t.append(mark, style=DIM if met else INK_B)
            t.append(txt + "\n", style=DIM if met is not False else INK_B)
            return t

        self.det_off = menu.scroll_window(out, report, self.det_off, vis, fmt)
        more = "" if len(report) <= vis else f"  ({self.det_off + 1}-{min(len(report), self.det_off + vis)}/{len(report)})"
        out.append_text(menu.footer(more.strip()))    # the position, not the keys
        return out

    def _evolves_scene(self, rows, dots):
        from rich.text import Text
        out = menu.header("DIGICORE  EVOLVES", dots)
        if isinstance(rows, str):                      # "(final form)"
            out.append(f" {rows}\n", style=DIM)
            out.append_text(menu.blanks(8))
            self._keys = [("←→", "page"), ("ESC", "back")]
            out.append_text(menu.footer(""))
            return out

        options = evolution.divergence_options(self.pet)

        def fmt(r, j):
            num, name, ready, unmet = r
            cur = j == self.evo_sel
            # the armed DNA steer wears its own word: it isn't "gates met",
            # it's the charge overriding the chart (gameplay audit B3)
            # DNA audit 2026-10-14: every option stays tagged; growth alone rolls.
            tag = (chr(0x2713) + (" armed" if len(options) == 1 else " road") if num in options
                   else core.route_tag(self.pet, num)
                   or (chr(0x2713) + " ready" if ready else f"{unmet} to go"))
            t = Text()
            t.append(("▸" if cur else " ") + " " + set_cell_size(name, 21), style=INK_B if cur else INK)
            t.append(f"{tag:>10}\n", style=INK_B if ready else DIM)
            return t

        self.evo_sel = menu.list_window(out, rows, self.evo_sel, 8, fmt)
        out.append_text(menu.note("ENTER: what it takes"))
        self._keys = [("↑↓", "pick"), ("ENTER", "req"), ("←→", "page"), ("ESC", "back")]
        out.append_text(menu.footer(""))
        return out

    def text(self):
        if self.teaser:
            return self._teaser_scene()
        if self._back_t:                              # evolSilhouetteBack: dark blink
            return render_scene([], 40, SCENE_ROWS, SIL_LIGHTSOFF, VOID, clip=grid.WINDOW)
        if self.detail is not None:
            return self._detail_scene()
        if self.i == 0:
            return self._core_scene()
        title, rows = self.pages[self.i]
        dots = self._dots()
        if title == "EVOLVES":
            return self._evolves_scene(rows, dots)
        out = menu.header(f"DIGICORE  {title}", dots)
        rendered = _data_lines(rows)
        vis = 8 if title in ("TROPHIES", "LEGACY") else 9
        self.row_off = menu.scroll_window(out, rendered, self.row_off, vis,
                                          lambda text, i: text)
        scroll = "↑↓ scroll  " if len(rendered) > vis else ""
        if title == "TROPHIES":
            # the Album row fronts a browsable book (2026-07-21): teach the
            # door the way EVOLVES teaches its checklist
            out.append_text(menu.note("ENTER: the album"))
            self._keys = ([("↑↓", "scroll")] if scroll else []) + [("ENTER", "album")] \
                + ([] if scroll else [("←→", "page")]) + [("ESC", "back")]
            out.append_text(menu.footer(""))
        elif title == "LEGACY":
            # the headstones front their room now too (2026-07-26)
            out.append_text(menu.note("ENTER: the hall of memory"))
            self._keys = ([("↑↓", "scroll")] if scroll else []) + [("ENTER", "hall")] \
                + ([] if scroll else [("←→", "page")]) + [("ESC", "back")]
            out.append_text(menu.footer(""))
        else:
            self._keys = ([("↑↓", "scroll")] if scroll else []) + [("←→", "page"), ("ESC", "back")]
            out.append_text(menu.footer(""))
        return out
