"""2026-10-15 themed road: earned scene history follows its scene."""
ROAD_ORDER_V = 1
OLD_TO_NEW = (4, 2, 3, 1, 5, 0, 6, 13, 9, 19, 14, 15, 16, 7, 10, 27, 24, 20, 12, 11, 25, 17, 22, 18, 8, 21, 26, 23, 28, 29)


def road_index(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return value
    return OLD_TO_NEW[n] if 0 <= n < len(OLD_TO_NEW) else value


def migrate_road(prog):
    """Return a normalized copy; version travels with each account and sync block."""
    out = dict(prog)
    if out.get("road_order_v", 0) >= ROAD_ORDER_V:
        return out
    cleared = prog.get("maps_cleared")
    if isinstance(cleared, list):
        out["maps_cleared"] = [road_index(n) for n in cleared]
    # Legacy whole-area clears implied the OLD scenes, never the new slots.
    areas = prog.get("maps")
    if isinstance(areas, list):
        implied = [road_index(n) for n in range(30)
                   if any(isinstance(a, int) and 6 * (a + 1) > n for a in areas)]
        out["maps_cleared"] = sorted(set(out.get("maps_cleared", [])) | set(implied))
    wilds = prog.get("wilds_beaten")
    if isinstance(wilds, list):
        out["wilds_beaten"] = [f"{road_index(v.split(':', 1)[0])}:{v.split(':', 1)[1]}"
                               if isinstance(v, str) and ':' in v else v for v in wilds]
    for key in ("map_bests", "road_bounty"):
        if isinstance(prog.get(key), dict):
            out[key] = {str(road_index(k)): v for k, v in prog[key].items()}
    seen = prog.get("animations_seen")
    if isinstance(seen, list):
        out["animations_seen"] = [f"map_clear:{road_index(v.split(':', 1)[1])}"
                                  if isinstance(v, str) and v.startswith("map_clear:") else v
                                  for v in seen]
    if isinstance(prog.get("town_bought"), dict):
        out["town_bought"] = {}
        for key, value in prog["town_bought"].items():
            prefix, sep, item = key.partition(":")
            out["town_bought"][f"{road_index(prefix)}:{item}" if sep else key] = value
    if isinstance(prog.get("last_gen"), dict):
        out["last_gen"] = migrate_road(prog["last_gen"])
    # adv_progress/frontier is a COUNT of cleared slots, not a scene index.
    out["road_order_v"] = ROAD_ORDER_V
    return out
