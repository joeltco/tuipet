"""Seasonal home notices. Calendar authority lives in tournament.  (The seasonal
home tint was removed 2026-10-17 -- Joel couldn't see it, and stronger it read as
an old brown photo, not Halloween.)"""
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
