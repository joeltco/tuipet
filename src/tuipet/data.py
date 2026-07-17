"""Load extracted sprites + game data — the FAÇADE (tier-1 split,
2026-07-17).  The loaders live in four domain modules; every name is
re-exported here so the ~100 `data.X` call sites (and the tests) never
moved.  Patching note: monkeypatching `data.load_x` still intercepts every
`data.load_x()` call site, but code INSIDE a domain module calls its own
module-local name — patch the owning module (`data_core`, `data_shop`,
`data_world`, `data_meta`) when you need to reach those, and patch the
owning module's `_DATA` to redirect its files.
"""
from __future__ import annotations

from . import data_core as _core
from . import data_meta as _meta
from . import data_shop as _shop
from . import data_world as _world

for _m in (_core, _shop, _world, _meta):
    globals().update({k: v for k, v in vars(_m).items()
                      if not k.startswith("__") and k not in
                      ("annotations", "csv", "gzip", "json", "os", "re",
                       "lru_cache")})
del _m
