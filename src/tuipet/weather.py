"""The calendar — all that survives of the weather system (BASIC VPET,
2026-07-16: Joel had the whole weather/temperature sim removed; the classic
devices have neither).  The seasons stay because the cup schedule, the town
greeters and the egg gates speak them.

config.csv FirstSpringDay 0 / FirstSummerDay 13 / FirstFallDay 26 /
FirstWinterDay 39, wrapping past MaxFastClockDays 51: a season lasts THIRTEEN
game days and the year is a 52-day cycle.
"""
from __future__ import annotations

SEASONS = ["Spring", "Summer", "Fall", "Winter"]
SEASON_DAYS = 13
YEAR_DAYS = 52


def season_for_day(day_index):
    return SEASONS[(day_index % YEAR_DAYS) // SEASON_DAYS]
