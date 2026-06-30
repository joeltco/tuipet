"""Calendar helper.

The DVPet weather + temperature simulation was STRIPPED (2026-06-29): authentic
mono v-pets (DM/DM20/Pen/Pen20/DMX) have no weather or temperature mechanic — care
is feed / train / clean / sleep / heal, and mood is driven by those, not climate.
All that survives is the cosmetic season label (status line + per-season trophies).
"""
from __future__ import annotations

SEASONS = ["Spring", "Summer", "Fall", "Winter"]


def season_for_day(day_index):
    return SEASONS[day_index % len(SEASONS)]
