"""DigiCore — DVPet's EvolutionState page + tuipet's paged data book.

The CORE page is the canon Digicore (SpriteAnim setupDigicore): the field-
flavoured core backdrop (ViewUtil.getDigicoreBackground picks it by the pet's
HIGHEST DNA field, falling back to its own), the core badge (a special core
from digicoreMenuConfig.csv, else the X-antibody state badge), and the core
NUMBER — with a pending evolution it counts DOWN from DigicoreBaseRate 14 as
the growth period elapses; past growth (or a final form) it counts UP through
the days toward the elder line (age-based since the DSprite mortality port
2026-07-22).  Pressing the core plays the silhouette teaser
(EvolSilhouetteTransition): the next natural evolution as a blacked-out shape.
The data-book pages after it are tuipet's own readout (kept adaptation).
"""
from __future__ import annotations
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
        self.evo_sel = 0          # EVOLVES page: the highlighted candidate
        self.detail = None        # (num, name): the open requirement checklist
        self.det_off = 0          # ...and its scroll offset

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
        if k in ("right", "l") or (k == "space" and self.i > 0):
            self.i = (self.i + 1) % len(self.pages)
        elif k in ("left", "h"):
            self.i = (self.i - 1) % len(self.pages)
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
        growth = p.STAGE_DURATION.get(p.stage)
        # ONE predicate for the whole page (digicore audit 2026-07-18):
        # the Meter row and core_number must never disagree again
        pending = (growth is not None and p.stage_seconds < growth
                   and core.has_next(p))
        x = getattr(p, "x_antibody", "None")
        rows = [
            ("Core", f"{chr(0x25C6)} {n}"),
            ("Meter", "evolution nears at 1" if pending else "counts the days"),
            ("Field", data.pretty_field(getattr(p, "field", "") or "None")),
            ("X-State", "none" if x == "None" else x.lower()),
            ("Mode", ("ready — press M" if p.can_mode_change() else chr(0x2014))),
        ]
        out = menu.header("DIGICORE  CORE", self._dots())
        for label, val in rows:
            out.append(f" {label:<9}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        out.append_text(menu.blanks(9 - len(rows) - 3))
        out.append(" gaze into the core to glimpse\n", style=DIM)
        out.append(" what stirs within…\n", style=DIM)
        # the door wears its key in BOLD (menu polish 2026-07-21: the gaze
        # was easy to look over in dim prose) -- the EVOLVES "ENTER: what it
        # takes" / TROPHIES "ENTER: the album" teaching line, gaze verdicts
        # still take the slot when one is pending
        out.append_text(menu.note(self.note if self.note != "the core stirs…"
                                  else "SPACE: gaze into the core",
                                  tick=self.frame_i))
        out.append_text(menu.footer("SPACE gaze  ←→ page  ESC out"))
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
        if not self.teaser:
            return menu.hints(("SPACE", "gaze"), ("\u2190\u2192", "page"),
                              ("ESC", "out"))
        t = self.teaser_t
        if t < MON_T:
            return "the core stirs…"
        if t < MON_T + EXPAND_T:
            return "the core opens…"
        return ("Nothing stirs — this is its final form."
                if next_evolution(self.pet) is None
                else "A shape looms in the core…")

    def _detail_scene(self):
        """One candidate's requirement checklist (evolution.requirement_report):
        met gates dim out of the way, the unmet ones are the raising guide."""
        from rich.text import Text
        num, name = self.detail
        if num == evolution.divergence_target(self.pet):
            # the steer's own sheet: lines.requirement_report would say
            # "not in this line" -- true, and exactly the point; what
            # fires this jump is the charge (gameplay audit B3)
            report = core.divergence_report(self.pet)
        else:
            report = (lines.requirement_report(self.pet, num) if lines.active(self.pet)
                      else evolution.requirement_report(self.pet, num))
        vis = DET_VIS
        out = menu.header(f"DIGICORE  {name[:16].upper()}", "req")

        def fmt(r, i):
            met, txt = r
            mark = {True: " " + chr(0x2713) + " ", False: " " + chr(0x2717) + " ",
                    None: "   "}[met]
            t = Text()
            t.append(mark, style=DIM if met else INK_B)
            t.append(txt[:35] + "\n", style=DIM if met is not False else INK_B)
            return t

        self.det_off = menu.scroll_window(out, report, self.det_off, vis, fmt)
        more = "" if len(report) <= vis else f"  ({self.det_off + 1}-{min(len(report), self.det_off + vis)}/{len(report)})"
        out.append_text(menu.footer(f"↑↓ scroll{more}   ESC back"))
        return out

    def _evolves_scene(self, rows, dots):
        from rich.text import Text
        out = menu.header("DIGICORE  EVOLVES", dots)
        if isinstance(rows, str):                      # "(final form)"
            out.append(f" {rows}\n", style=DIM)
            out.append_text(menu.blanks(8))
            out.append_text(menu.footer("←→ page    ESC out"))
            return out

        div = evolution.divergence_target(self.pet)

        def fmt(r, j):
            num, name, ready, unmet = r
            cur = j == self.evo_sel
            # the armed DNA steer wears its own word: it isn't "gates met",
            # it's the charge overriding the chart (gameplay audit B3)
            tag = (chr(0x2713) + " armed" if num == div
                   else chr(0x2713) + " ready" if ready else f"{unmet} to go")
            t = Text()
            t.append(("▸" if cur else " ") + f" {name[:20]:<21}", style=INK_B if cur else INK)
            t.append(f"{tag:>10}\n", style=INK_B if ready else DIM)
            return t

        self.evo_sel = menu.list_window(out, rows, self.evo_sel, 8, fmt)
        out.append_text(menu.note("ENTER: what it takes"))
        out.append_text(menu.footer("↑↓ pick  ENTER req  ←→ page  ESC out"))
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
        for label, val in rows:
            out.append(f" {label:<9}", style=DIM)
            out.append(f"{val}\n", style=INK_B)
        if title == "TROPHIES":
            # the Album row fronts a browsable book (2026-07-21): teach the
            # door the way EVOLVES teaches its checklist
            out.append_text(menu.blanks(9 - len(rows) - 1))
            out.append_text(menu.note("ENTER: the album"))
            out.append_text(menu.footer("ENTER album  ←→ page  ESC out"))
        else:
            out.append_text(menu.blanks(9 - len(rows)))
            out.append_text(menu.footer("←→ page    ESC out"))
        return out
