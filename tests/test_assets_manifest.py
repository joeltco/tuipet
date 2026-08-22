"""A damaged install has to be caught at the DOOR, not mid-session.

eddy, 0.5.345, Windows (2026-08-22): tuipet's own tournies.csv would not open
on his machine.  The game booted, he raised a Champion, and the install only
announced itself when he pressed the tournament key -- as a traceback, because
nothing between load_tournies() and Textual's action dispatcher has an ear for
AssetsError.  The message it carries ("Reinstall it: pip install
--force-reinstall tuipet") is written for a player, and a player never saw it.

_preflight() was supposed to be that door.  It opened sprites.json.gz and
orbs.json.gz -- two of the eighteen files the game cannot run without -- and
passed everything else through.

These pin the door shut: every required file is checked before the UI takes
the terminal over, the optional ones still degrade quietly, and the manifest
cannot drift away from what the code actually opens.
"""
import ast
import os

import pytest

import tuipet
from tuipet import appboot, data_core
from tuipet.data_core import OPTIONAL_DATA, REQUIRED_DATA, AssetsError

_SRC = os.path.dirname(os.path.abspath(tuipet.__file__))
_DATA = os.path.join(_SRC, "data")


def _install(tmp_path, without=()):
    """A mirror of the shipped data dir with some files left out -- a damaged
    install, without touching the real one."""
    d = tmp_path / "data"
    d.mkdir(parents=True)
    for fn in os.listdir(_DATA):
        if fn in without:
            continue
        os.symlink(os.path.join(_DATA, fn), d / fn)
    return str(d)


# --- the bug ---------------------------------------------------------------

def test_a_missing_required_file_stops_the_boot(tmp_path, monkeypatch, capsys):
    """THE REPORT. tournies.csv gone must end the launch with the reinstall
    line, not hand the player a game that will ambush them later."""
    monkeypatch.setattr(data_core, "_DATA", _install(tmp_path, {"tournies.csv"}))
    monkeypatch.setattr("time.sleep", lambda *_: None)
    with pytest.raises(SystemExit) as exc:
        appboot._preflight()
    assert exc.value.code == 1
    said = capsys.readouterr().out
    assert "tournies.csv" in said, said
    assert "force-reinstall" in said, "the player is told how to fix it, or the check is just a crash with manners"


def test_the_check_covers_every_file_the_game_cannot_run_without(tmp_path, monkeypatch):
    """Not just the one eddy lost -- each required file, one at a time."""
    for name in REQUIRED_DATA:
        monkeypatch.setattr(data_core, "_DATA", _install(tmp_path / name.replace(".", "_"), {name}))
        with pytest.raises(AssetsError) as exc:
            data_core.verify_assets()
        assert name in str(exc.value), f"{name} went missing and the message named something else"


def test_an_empty_file_counts_as_damaged(tmp_path, monkeypatch):
    """An interrupted download leaves 0-byte files behind; those OPEN fine.
    An empty csv parses to zero rows, which silently deletes a whole system
    instead of saying the install is broken."""
    d = _install(tmp_path, {"tournies.csv"})
    open(os.path.join(d, "tournies.csv"), "w").close()
    monkeypatch.setattr(data_core, "_DATA", d)
    with pytest.raises(AssetsError, match="tournies.csv"):
        data_core.verify_assets()


def test_a_complete_install_boots(tmp_path, monkeypatch):
    monkeypatch.setattr(data_core, "_DATA", _install(tmp_path))
    monkeypatch.setattr("time.sleep", lambda *_: None)
    appboot._preflight()                      # no SystemExit


def test_an_optional_atlas_going_missing_never_blocks_a_player(tmp_path, monkeypatch):
    """The trimming degrades on purpose. Promoting one of these into the
    preflight would lock someone out of a game that runs fine without it."""
    monkeypatch.setattr(data_core, "_DATA", _install(tmp_path, set(OPTIONAL_DATA)))
    monkeypatch.setattr("time.sleep", lambda *_: None)
    appboot._preflight()
    data_core.verify_assets()


# --- the manifest cannot drift ---------------------------------------------

def _data_filename_literals():
    """Every string constant in the package that names a file we actually
    ship.  Save-dir names (save.json, sound.txt) aren't bundled data and so
    never match.  Files only: data/sounds is a directory, and sound.py already
    treats every clip in it as optional (a silent game still plays)."""
    shipped = {f for f in os.listdir(_DATA)
               if os.path.isfile(os.path.join(_DATA, f))}
    out = {}
    for root, _dirs, files in os.walk(_SRC):
        if "__pycache__" in root or os.path.basename(root) == "data":
            continue
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), path)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and node.value in shipped):
                    out.setdefault(node.value, f"{fn}:{node.lineno}")
    return out


def test_every_bundled_file_the_code_opens_is_classified():
    """Add a data file, open it, forget the manifest -> it is unguarded and
    nothing says so. This is the line that notices."""
    known = set(REQUIRED_DATA) | set(OPTIONAL_DATA)
    stray = {n: w for n, w in _data_filename_literals().items() if n not in known}
    assert not stray, (
        f"{stray} -- the code opens these but data_core's manifest doesn't "
        f"classify them; put each in REQUIRED_DATA (its loader raises) or "
        f"OPTIONAL_DATA (its loader degrades)")


def test_the_manifest_only_names_files_we_ship():
    missing = [n for n in REQUIRED_DATA + OPTIONAL_DATA
               if not os.path.exists(os.path.join(_DATA, n))]
    assert not missing, f"{missing} are in the manifest but not in the wheel"


def test_required_and_optional_never_overlap():
    both = set(REQUIRED_DATA) & set(OPTIONAL_DATA)
    assert not both, f"{both} is listed as both required and degradable"


def test_the_files_that_ambushed_us_are_required():
    """Named on purpose: tournies.csv is eddy's, and the other lazy loaders
    sit behind the same kind of key -- a menu the player may not press for
    hours. Demoting one of these to OPTIONAL puts the ambush back."""
    for name in ("tournies.csv", "towns.csv", "zones.csv", "enemies.csv",
                 "titles.csv", "items.csv", "foods.csv"):
        assert name in REQUIRED_DATA, f"{name} is reached from a menu, late"
