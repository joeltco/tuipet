#!/usr/bin/env bash
# tuipet — one-command installer (Termux-first).
#
#   curl -fsSL https://raw.githubusercontent.com/joeltco/tuipet/main/install.sh | bash
#
# Installs Python + tuipet (with all sprites/sounds vendored) and, on Termux,
# the termux-api package needed to play sound on the phone.
set -e

REPO="git+https://github.com/joeltco/tuipet"

echo "==> Installing tuipet (terminal Digimon V-Pet)…"

# ---- system deps -----------------------------------------------------------
if [ -n "$PREFIX" ] && command -v pkg >/dev/null 2>&1; then
    echo "==> Termux detected — installing python, git, termux-api…"
    pkg install -y python git termux-api
elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip git
fi

# ---- tuipet ----------------------------------------------------------------
echo "==> pip install $REPO"
pip install --upgrade "$REPO"

echo
echo "==> Done!  Start your pet with:"
echo
echo "      tuipet"
echo
if [ -n "$PREFIX" ] && command -v pkg >/dev/null 2>&1; then
    echo "    Sound: also install the 'Termux:API' app (F-Droid or Play store) —"
    echo "    the termux-api package alone is not enough to hear the beeps."
fi
