"""No message is ever clipped (Joel 2026-07-15: the bag cut off "Too early to
lay out the Futon — it's not bedtime").  menu.note marquees ANY over-wide
message — panels pass their own frame counter or inherit menu.TICK, which
app.on_frame advances at 10 Hz.  Panels that had no animation (shop/bag,
assistant, themes) carry a heartbeat anim() so the scroll actually renders.
"""
from tuipet import menu


def test_long_note_scrolls_instead_of_clipping():
    msg = "Too early to lay out the Futon — it's not bedtime."
    assert len(msg) > menu.W
    old_tick = menu.TICK
    try:
        menu.TICK = 0
        head = menu.note(msg).plain
        assert "…" not in head, "clipping is retired: the marquee owns overflow"
        assert head.rstrip("\n") == msg[:menu.W]      # holds on the head first
        seen = set()
        for t in range(0, (len(msg) + 40) * menu.NOTE_STEP, menu.NOTE_STEP):
            menu.TICK = t + menu.NOTE_HOLD * menu.NOTE_STEP
            seen.add(menu.note(msg).plain.rstrip("\n"))
        joined = "".join(sorted(seen))
        assert "bedtime" in joined, "the tail must come into view"
    finally:
        menu.TICK = old_tick


def test_short_note_untouched():
    assert menu.note("Fed Meat.").plain == "Fed Meat.\n"


def test_every_panel_heartbeats_for_the_marquee():
    """A panel without anim() never repaints, so its note could never scroll.
    Every screen panel the app can open must carry one."""
    import importlib
    import inspect
    for mod_name, cls_name in (
            ("shopscreen", "ShopPanel"), ("assistscreen", None),
            ("themescreen", None), ("habitatscreen", "HabitatPanel"),
            ("feedscreen", None), ("dnascreen", None), ("optionsscreen", None)):
        mod = importlib.import_module(f"tuipet.{mod_name}")
        panels = [c for n, c in inspect.getmembers(mod, inspect.isclass)
                  if n.endswith("Panel") and c.__module__ == mod.__name__]
        assert panels, f"{mod_name}: no panel class found"
        for c in panels:
            assert hasattr(c, "anim"), f"{mod_name}.{c.__name__} has no anim(): its notes can never scroll"
