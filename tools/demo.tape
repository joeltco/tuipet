# tuipet demo — regenerate with:  vhs tools/demo.tape  (from the repo root)
# Records: hatch -> feed -> play -> quit, then a Rookie heading out on an
# adventure.  tools/demo_seed.py stages the saves so nothing waits real-time.
Output demo.gif
Set Shell "bash"
Set Width 1000
Set Height 760
Set FontSize 13
Set Padding 12
Set TypingSpeed 60ms

Hide
Type "cd ~/projects/tuipet && rm -rf /tmp/tuipet-demo && TUIPET_SAVE_DIR=/tmp/tuipet-demo .venv-dev/bin/python tools/demo_seed.py egg && clear && TUIPET_SAVE_DIR=/tmp/tuipet-demo TUIPET_NO_SYNC=1 .venv-dev/bin/python -m tuipet"
Enter
Sleep 5s
Show
Sleep 2s
Enter
Sleep 12s
Type "f"
Sleep 2s
Enter
Sleep 7s
Type "p"
Sleep 6s
Type "q"
Sleep 2s
Hide
Type "TUIPET_SAVE_DIR=/tmp/tuipet-demo .venv-dev/bin/python tools/demo_seed.py rookie && clear && TUIPET_SAVE_DIR=/tmp/tuipet-demo TUIPET_NO_SYNC=1 .venv-dev/bin/python -m tuipet"
Enter
Sleep 5s
Show
Sleep 1s
Enter
Sleep 3s
Type "a"
Sleep 24s
Type "q"
Sleep 3s
