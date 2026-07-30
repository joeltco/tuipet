"""Every text file we touch is utf-8, on every machine.

A bare open() decodes with the MACHINE'S locale codepage, not utf-8.  On a
Traditional-Chinese Windows install that is cp950, and towns.csv carries a
single en dash (byte 379) that cp950 cannot decode -- so the game crashed on
boot, before the pet appeared, for a player whose only sin was a Chinese
Windows (bug report 2026-07-30, v0.5.315).  Our data files are ours; their
encoding must not depend on where the game is played.

Two pins, because one alone is a hole:
  * a STATIC sweep: no text open() in the package may omit encoding=
  * a RUNTIME sweep: import + load every data table under
    -X warn_default_encoding -W error::EncodingWarning, which turns any
    locale-defaulted open into an exception no matter how it's spelled
"""
import ast
import os
import subprocess
import sys

import tuipet

_SRC = os.path.dirname(os.path.abspath(tuipet.__file__))
_DATA = os.path.join(_SRC, "data")


def _py_files():
    for root, _dirs, files in os.walk(_SRC):
        if "__pycache__" in root:
            continue
        for f in sorted(files):
            if f.endswith(".py"):
                yield os.path.join(root, f)


def _opens_text(call):
    """True when this ast Call is a text-mode builtin/gzip open with no
    encoding.  AST, not a regex: prose in a docstring mentioning open() is
    not a call, and a two-line call is still one call."""
    fn = call.func
    if isinstance(fn, ast.Name):
        if fn.id != "open":
            return False
    elif isinstance(fn, ast.Attribute):
        if fn.attr != "open" or getattr(fn.value, "id", "") != "gzip":
            return False          # wave.open et al are binary by definition
    else:
        return False
    kw = {k.arg for k in call.keywords}
    if "encoding" in kw:
        return False
    mode = ""
    if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
        mode = str(call.args[1].value)
    for k in call.keywords:
        if k.arg == "mode" and isinstance(k.value, ast.Constant):
            mode = str(k.value.value)
    return "b" not in mode         # binary opens take no encoding


def test_every_text_open_names_utf8():
    offenders = []
    for path in _py_files():
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=path)
        lines = src.split("\n")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _opens_text(node):
                offenders.append(f"{os.path.basename(path)}:{node.lineno}: "
                                 f"{lines[node.lineno - 1].strip()}")
    assert not offenders, (
        "text open() without encoding='utf-8' -- these read as the player's "
        "locale codepage, not utf-8:\n  " + "\n  ".join(offenders))


def test_towns_csv_still_holds_the_byte_that_broke_it():
    """Not a curiosity: it's the fixture.  If this dash ever leaves the file
    the utf-8 sweep above stops being load-bearing, so keep a real non-ascii
    byte in the corpus (any file will do) and know why it's there."""
    raw = open(os.path.join(_DATA, "towns.csv"), "rb").read()
    assert any(b > 127 for b in raw), "no non-ascii left in towns.csv"
    raw.decode("utf-8")                              # utf-8 is the truth
    try:
        raw.decode("cp950")
    except UnicodeDecodeError:
        pass                                         # exactly the player's crash
    else:
        raise AssertionError("towns.csv now decodes as cp950 -- fixture is stale")


def test_data_loads_with_locale_defaults_treated_as_errors():
    """The runtime half: -X warn_default_encoding makes every encoding-less
    text open emit EncodingWarning, and -W error turns it into a traceback.
    This walks the real boot-path loaders, so it catches sites the regex
    can't see (helpers, third-party calls, anything spelled oddly)."""
    code = (
        "import tuipet.data as d, tuipet.lines, tuipet.shop, tuipet.egg, "
        "tuipet.training, tuipet.battlescreen, tuipet.theme, tuipet.sound;"
        "[getattr(d, n)() for n in dir(d) if n.startswith('load_')];"
        "print('ok')"
    )
    env = dict(os.environ, PYTHONPATH=os.path.dirname(_SRC),
               TUIPET_NO_SYNC="1")
    r = subprocess.run(
        [sys.executable, "-X", "warn_default_encoding",
         "-W", "error::EncodingWarning", "-c", code],
        capture_output=True, text=True, env=env, timeout=180)
    assert "ok" in r.stdout, (
        "loading game data tripped a locale-default open:\n" + r.stderr[-3000:])
