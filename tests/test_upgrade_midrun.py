"""pip upgrading tuipet under a RUNNING game must not crash it on a lazy
read of the new install (bug reports 2026-10-17 Windows 0.6.32
"No module named 'tuipet.web.storage'", 2026-10-18 Termux 0.5.350
"unknown rule atom: 'FRAG'")."""
import asyncio
import json
import sys

from tuipet import lines, persistio
from tuipet.app import TuiPetApp
from tuipet.pet import Pet


def test_desktop_save_never_imports_web_storage(tmp_path, monkeypatch):
    # None in sys.modules makes the import raise ModuleNotFoundError, the
    # same as the half-swapped package dir pip leaves mid-upgrade
    monkeypatch.setitem(sys.modules, "tuipet.web.storage", None)
    path = str(tmp_path / "save.json")
    persistio._atomic_write_json(path, {"ok": 1})
    assert json.load(open(path, encoding="utf-8")) == {"ok": 1}


def test_line_charts_read_at_boot_not_mid_session(tmp_path, monkeypatch):
    lines.load_lines.cache_clear()
    lines.egg_bound_lines.cache_clear()
    seen = {}

    async def go():
        app = TuiPetApp(pet=Pet(num=-1, stage="Egg"))
        async with app.run_test(size=(82, 32)):
            seen["lines"] = lines.load_lines.cache_info().currsize
            seen["eggs"] = lines.egg_bound_lines.cache_info().currsize
    asyncio.run(go())
    assert seen == {"lines": 1, "eggs": 1}
