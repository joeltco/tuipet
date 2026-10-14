"""Write tools/promo/trailer.tape: title cards + REAL tuipet footage (vhs).
Run from the repo root:  python3 tools/promo/make_trailer_tape.py && vhs tools/promo/trailer.tape"""
PY = ".venv-dev/bin/python"
OUT = []
w = OUT.append
w('Output "demo.gif"')
for k, v in (("Shell", '"bash"'), ("Width", 1000), ("Height", 640), ("FontSize", 14),
             ("Padding", 8), ("Framerate", 15), ("TypingSpeed", "1ms"),
             ("Theme", '{"background":"#101010","foreground":"#e6e6e6","black":"#101010","red":"#e8423f","green":"#3fae5a","yellow":"#e2b93b","blue":"#4a90d9","magenta":"#b06fd0","cyan":"#3cc7c7","white":"#e6e6e6","brightBlack":"#555555","brightRed":"#ff6b6b","brightGreen":"#6fdc8c","brightYellow":"#ffd866","brightBlue":"#78b6ff","brightMagenta":"#d39cff","brightCyan":"#7fe7e7","brightWhite":"#ffffff","selection":"#333333","cursor":"#101010"}')):
    w(f"Set {k} {v}")
w("Hide")
w('Type "cd ~/projects/tuipet && export TUIPET_SAVE_DIR=/tmp/tp-trailer TUIPET_NO_SYNC=1 && clear"')
w("Enter")


def card(head, sub="", hold="2200ms"):
    w("Hide")
    w("Ctrl+c")                     # end any card still holding
    w(f'Type `clear && {PY} tools/promo/card.py "{head}" "{sub}"`')
    w("Enter")
    w("Sleep 900ms")
    w("Show")
    w(f"Sleep {hold}")


def launch(seed, settle="3s"):
    w("Hide")
    w("Ctrl+c")                     # end a holding card (harmless at a bare prompt)
    w("Sleep 200ms")
    w(f'Type "clear && {PY} tools/demo_seed.py {seed} >/dev/null && clear && {PY} -m tuipet"')
    w("Enter")
    w(f"Sleep {settle}")
    w("Enter")                      # past the title screen
    w("Sleep 500ms")


def quit_():
    w("Hide")
    w("Ctrl+q")
    w("Sleep 400ms")


card("TUIPET 0.6", "THE GODZILLA LINE IS HERE")
# the Godzilla Egg cracks -> Botamon G
launch("godzilla_egg")
w("Sleep 1200ms")
w("Show")
w("Sleep 2200ms")
quit_()
card("28 NEW KAIJU", "Botamon G to Burning Godzilla")
for dex in range(1623, 1651):           # every form, real game, walking its scene
    launch(f"mon {dex}")
    w("Show")
    w("Sleep 800ms")
    quit_()
card("THE G-CELL METER", "decides what they become")
launch("mon 1628 1.5")                  # Little Godzilla, live evolution on camera
w("Show")
w("Sleep 3500ms")
quit_()
launch("mon 1644")
w('Type "d"')
w("Sleep 300ms")
w("Right")
w("Sleep 300ms")
w("Show")
w("Sleep 1800ms")
quit_()
card("EVERY KAIJU FIRES ITS OWN SHOT")
launch("mon 1644")
w('Type "m"')
w("Sleep 400ms")
w("Show")
w("Space")
w("Sleep 900ms")
w("Space")
w("Sleep 2600ms")
quit_()
card("G-CELL FRAGMENTS", "left where a kaiju falls")
launch("fragment")
w("Show")
w("Sleep 2200ms")
quit_()
card("pip install tuipet", "reach Mega to earn the egg", hold="2600ms")
open("tools/promo/trailer.tape", "w").write("\n".join(OUT) + "\n")
print("wrote tools/promo/trailer.tape,", len(OUT), "lines")
