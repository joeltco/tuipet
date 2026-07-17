"""iOS support (a-Shell is the official iPhone/iPad target, 2026-07-13).

iOS CANNOT write to ~ -- only ~/Documents, ~/Library and ~/tmp.  tuipet saved
to ~/.local/share/tuipet and _atomic_write_json swallows OSError, so on iOS
every save failed SILENTLY: the pet never persisted and the player was never
told.  These pin the save-dir chooser, the loud warning, and the platform tag
that makes iOS players visible in the bug feed.
"""
import importlib
import os
import tempfile


from tuipet import persistence


def _reload(**env):
    for k in ('TUIPET_SAVE_DIR', 'XDG_DATA_HOME'):
        os.environ.pop(k, None)
    os.environ.update(env)
    from tuipet import persistio
    importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
    importlib.reload(persistence)
    return persistence


def test_ios_read_only_home_falls_back_to_documents(monkeypatch):
    home = tempfile.mkdtemp()
    os.makedirs(os.path.join(home, 'Documents'))
    os.chmod(home, 0o555)                       # iOS: ~ is read-only
    try:
        monkeypatch.setenv('HOME', home)
        p = _reload()
        assert p.SAVE_DIR == os.path.join(home, 'Documents', 'tuipet')
        from tuipet.pet import Pet
        pet = Pet(num=100, stage='Champion', attribute='Vaccine', obedience=500)
        pet.world_seconds = 600.0
        p.save(pet)
        assert os.path.exists(p.SAVE_PATH), 'the pet must actually persist on iOS'
        assert not p.save_failed
    finally:
        os.chmod(home, 0o755)
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)


def test_an_unwritable_disk_is_reported_not_swallowed(monkeypatch):
    home = tempfile.mkdtemp()
    os.chmod(home, 0o555)                       # nothing writable at all
    try:
        monkeypatch.setenv('HOME', home)
        p = _reload()
        from tuipet.pet import Pet
        pet = Pet(num=100, stage='Champion', attribute='Vaccine', obedience=500)
        pet.world_seconds = 600.0
        p.save(pet)
        assert p.save_failed, 'a silently unsaveable install used to eat the pet'
    finally:
        os.chmod(home, 0o755)
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)


def test_save_dir_override_wins(monkeypatch):
    d = tempfile.mkdtemp()
    monkeypatch.setenv('TUIPET_SAVE_DIR', d)
    p = _reload(TUIPET_SAVE_DIR=d)
    try:
        assert p.SAVE_DIR == d
    finally:
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)


def test_the_normal_linux_home_is_unchanged(monkeypatch):
    home = tempfile.mkdtemp()
    monkeypatch.setenv('HOME', home)
    p = _reload()
    try:
        assert p.SAVE_DIR == os.path.join(home, '.local', 'share', 'tuipet')
    finally:
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)


def test_ios_players_are_visible_in_the_bug_feed(monkeypatch):
    from tuipet import app as appmod
    monkeypatch.setattr('platform.system', lambda: 'Darwin')
    monkeypatch.setattr('platform.machine', lambda: 'iPhone15,2')
    assert appmod.host_platform() == 'iOS'
    monkeypatch.setattr('platform.machine', lambda: 'arm64')
    monkeypatch.setenv('SHORTCUTS', '1')
    assert appmod.host_platform() == 'iOS'


def test_module_launch_exists():
    """python3 -m tuipet is the launch we document for iOS (a-Shell's PATH
    does not reliably carry pip console scripts)."""
    import tuipet.__main__ as m
    assert callable(m.main)
