# tuipet demo — regenerate with:  vhs tools/demo.tape  (from the repo root)
# Records the BASIC VPET loop: hatch -> feed (meat, then the pill -- both ride
# their ripped bite strips) -> quit, then a Rookie running the training drill,
# browsing the shop tabs and its DigiCore page.  tools/demo_seed.py stages the
# saves so nothing waits real-time.
Output demo.gif
Set Shell "bash"
Set Width 1000
Set Height 760
Set FontSize 13
Set Padding 12
Set TypingSpeed 60ms

Hide
Type "cd ~/projects/tuipet && rm -rf /tmp/tuipet-demo && TUIPET_SAVE_DIR=/tmp/tuipet-demo .venv-dev/bin/python tools/demo_seed.py egg && clear && TUIPET_SAVE_DIR=/tmp/tuipet-demo .venv-dev/bin/python -m tuipet"
Enter
Sleep 5s
Show
Sleep 2s
Enter
Sleep 12s
Type "f"
Sleep 2s
Enter
Sleep 6s
Type "f"
Sleep 1s
Down
Sleep 1s
Enter
Sleep 6s
Type "q"
Sleep 2s
Hide
Type "TUIPET_SAVE_DIR=/tmp/tuipet-demo .venv-dev/bin/python tools/demo_seed.py rookie && clear && TUIPET_SAVE_DIR=/tmp/tuipet-demo .venv-dev/bin/python -m tuipet"
Enter
Sleep 5s
Show
Sleep 1s
Enter
Sleep 3s
Type "t"
Sleep 4s
Space
Sleep 12s
Type "o"
Sleep 3s
Right
Sleep 2s
Right
Sleep 2s
Escape
Sleep 1s
Type "d"
Sleep 4s
Escape
Sleep 1s
Type "q"
Sleep 3s
