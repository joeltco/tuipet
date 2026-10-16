"""Optional browser platform. Importing this module never imports JavaScript."""
import sys


def is_browser():
    return sys.platform == "emscripten"
