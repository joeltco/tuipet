"""Cache raster scanlines and invalidate only LCD rows whose pixels changed."""
from functools import lru_cache
from itertools import groupby

from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from textual.geometry import Region
from textual.strip import Strip


class Raster(Text):
    def __init__(self, lines, colors):
        super().__init__()
        self.lines, self.colors = lines, colors


@lru_cache(maxsize=2048)
def _style(top, bottom):
    return Style(color=top, bgcolor=bottom)


@lru_cache(maxsize=256)
def _line(colors):
    segments = []
    for pair, run in groupby(colors):
        segments.append(Segment('▀' * sum(1 for _ in run), _style(*pair)))
    return Strip(segments, len(colors))


def paint_cells(buf, cols, rows, on, bg, bgimg, free_ink=None):
    fi = free_ink or on
    lines, all_colors = [], []
    for cy in range(rows):
        ty, by = cy * 2, cy * 2 + 1
        colors = []
        for cx in range(cols):
            tv, bv = buf[ty][cx], buf[by][cx]
            tc = (fi if tv == 2 else on) if tv else ('#'+bgimg[ty][cx*6:cx*6+6] if bgimg else bg)
            bc = (fi if bv == 2 else on) if bv else ('#'+bgimg[by][cx*6:cx*6+6] if bgimg else bg)
            colors.append((tc, bc))
        colors = tuple(colors)
        all_colors.append(colors)
        lines.append(_line(colors))
    return Raster(lines, all_colors)


def update_raster(widget, content):
    previous = getattr(widget, '_web_lines', None)
    from js import bridgeRaster, bridgeRasterHide
    if not isinstance(content, Raster):
        bridgeRasterHide()
        widget._web_lines = None
        return False
    widget._web_lines = content.lines
    changes = [y for y, line in enumerate(content.lines)
               if previous is None or previous[y] is not line]
    region = widget.content_region
    if previous is None:
        widget.refresh()
    if region.width == 40 and region.height == 12 and widget.screen.is_current:
        # Draw the real compositor's pixel colors on a 2D canvas over the LCD.
        # xterm otherwise rebuilds/rasterizes many styled glyphs for one pet step.
        # Textual retains matching strips for resize, themes and screen overpaint.
        from pyodide.ffi import to_js
        if changes:
            bridgeRaster(region.x, region.y, to_js(content.colors), to_js(changes))
        for y in changes:
            widget._styles_cache.set_dirty(Region(widget.gutter.left, y + widget.gutter.top, 40, 1))
    else:
        for y in changes:
            widget.refresh(Region(0, y, widget.size.width, 1))
    return True


def render_screen(frame_rows, cols, rows, on="#2b2e31", bg="#c6c9cc", baseline=True,
                  mirror=False, xshift=0, yshift=0, overlay=None, bgimg=None,
                  clip=None, overlay_free=None, free_ink=None):
    from ..render import fill_buf
    buf = fill_buf(frame_rows, cols, rows * 2, baseline=baseline, mirror=mirror,
                   xshift=xshift, yshift=yshift, overlay=overlay, clip=clip,
                   overlay_free=overlay_free)
    return paint_cells(buf, cols, rows, on, bg, bgimg, free_ink)
