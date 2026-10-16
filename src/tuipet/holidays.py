"""Seasonal home notices and colors. Calendar authority lives in tournament."""
from functools import lru_cache

from . import tournament


def notice():
    from . import persistence
    season = tournament.holiday_season()
    if not season:
        return None
    stamp = f"{tournament._today().year}:{season}"
    d = persistence.load_settings()
    seen = d.setdefault("progress", {}).setdefault("holiday_notice_seen", [])
    if stamp in seen:
        return None
    seen.append(stamp)
    persistence.save_settings(d)
    if season == "halloween":
        return "Halloween is here! A: ghost trail. Festival fun all month. Oct 31: 2x road bits."
    return "Christmas is here! A: snow hunts. Festival fun all month. Dec 25: 2x road bits."


def tint(frame):
    from . import persistence
    season = tournament.holiday_season()
    if not frame or not season or not persistence.load_settings().get("seasonal_colors", True):
        return frame
    return list(_tinted(tuple(frame), season, bool(tournament.holiday())))


@lru_cache(maxsize=64)
def _tinted(frame, season, peak):
    accent = (184, 111, 50) if season == "halloween" else (113, 141, 150)
    amount = .20 if peak else .15
    return tuple("".join(f"{round(int(row[i + c:i + c + 2], 16) * (1 - amount) + accent[c // 2] * amount):02x}"
                    for i in range(0, len(row), 6) for c in (0, 2, 4)) for row in frame)
