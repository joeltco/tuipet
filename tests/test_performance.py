"""Hot-loop performance guards (Workstream D).

The 10 Hz frame loop and 1 Hz tick repeatedly call data loaders (e.g. background()
-> load_habitats() every frame). Every loader must be memoized so the CSV/asset is
parsed once, not re-read per frame. A missing @lru_cache on load_habitats was
costing a fresh CSV parse + open() syscall ~10-30x/second; this pins the invariant.
"""
from tuipet import data


def _public_loaders():
    out = []
    for name in dir(data):
        if name.startswith("load_") and callable(getattr(data, name)):
            out.append((name, getattr(data, name)))
    return out


def test_all_data_loaders_are_memoized():
    uncached = [name for name, fn in _public_loaders() if not hasattr(fn, "cache_info")]
    assert not uncached, f"data loaders missing @lru_cache (re-parse every call): {uncached}"


def test_load_foods_is_cached_and_stable():
    a = data.load_foods()
    b = data.load_foods()
    assert a is b, "load_foods must return the cached object, not re-parse"
    assert hasattr(data.load_foods, "cache_info")


def test_loaders_actually_hit_cache():
    """After one warm call, a second call must be a cache hit (hits increment)."""
    data.load_foods()
    info0 = data.load_foods.cache_info()
    data.load_foods()
    info1 = data.load_foods.cache_info()
    assert info1.hits > info0.hits
