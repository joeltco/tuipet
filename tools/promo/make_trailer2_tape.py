"""Write tools/promo/trailer2.tape: the 0.6.31 'best of' trailer -- black title cards between
fast REAL gameplay (Joel's format: card, footage, card, footage).  Run from the repo root:
  python3 tools/promo/make_trailer2_tape.py [--shots] && vhs tools/promo/trailer2.tape
--shots also writes a PNG per beat (tools/promo/shots/) for the frame strip Joel sees first."""
import sys

PY = ".venv-dev/bin/python"
SHOTS = "--shots" in sys.argv
OUT = []
w = OUT.append
n_shot = [0]
w('Output "/tmp/tuipet-trailer2.gif"')
for k, v in (("Shell", '"bash"'), ("Width", 1000), ("Height", 640), ("FontSize", 14),
             ("Padding", 8), ("Framerate", 15), ("TypingSpeed", "1ms"),
             ("Theme", '{"background":"#101010","foreground":"#e6e6e6","black":"#101010","red":"#e8423f","green":"#3fae5a","yellow":"#e2b93b","blue":"#4a90d9","magenta":"#b06fd0","cyan":"#3cc7c7","white":"#e6e6e6","brightBlack":"#555555","brightRed":"#ff6b6b","brightGreen":"#6fdc8c","brightYellow":"#ffd866","brightBlue":"#78b6ff","brightMagenta":"#d39cff","brightCyan":"#7fe7e7","brightWhite":"#ffffff","selection":"#333333","cursor":"#101010"}')):
    w(f"Set {k} {v}")
w("Hide")
w('Type "cd ~/projects/tuipet && export TUIPET_SAVE_DIR=/tmp/tp-trailer2 TUIPET_NO_SYNC=1 && clear"')
w("Enter")


def shot(tag):
    if SHOTS:
        n_shot[0] += 1
        w(f'Screenshot "tools/promo/shots/{n_shot[0]:02d}_{tag}.png"')


def card(head, sub="", hold="2000ms"):
    w("Hide")
    w("Ctrl+c")
    w(f'Type `clear && {PY} tools/promo/card.py "{head}" "{sub}"`')
    w("Enter")
    w("Sleep 900ms")
    w("Show")
    w("Sleep 400ms")
    shot("card")
    w(f"Sleep {hold}")


def launch(seed, settle="3s"):
    w("Hide")
    w("Ctrl+c")
    w("Sleep 200ms")
    w(f'Type "clear && rm -rf /tmp/tp-trailer2 && {PY} tools/demo_seed.py {seed} >/dev/null && clear && {PY} -m tuipet"')
    w("Enter")
    w(f"Sleep {settle}")
    w("Enter")                      # past the title screen
    w("Sleep 500ms")


def quit_():
    w("Hide")
    w("Ctrl+q")
    w("Sleep 400ms")


card("TUIPET", "raise - battle - evolve")
card("1,250 MONSTERS", "every one animated", hold="1600ms")
for dex in (29, 34, 40, 64, 62, 59, 1074, 93, 155, 280, 279, 294, 330, 298, 310, 1651, 1653, 1655):
    launch(f"pet {dex}", settle="2600ms")
    w("Show")
    w("Sleep 500ms")
    quit_()
card("THE GODZILLA LINE", "28 kaiju")
for dex in (1625, 1628, 1632, 1633, 1644):
    launch(f"mon {dex}", settle="2600ms")
    w("Show")
    w("Sleep 600ms")
    quit_()
launch("mon 1644")
w('Type "m"')
w("Sleep 400ms")
w("Show")
w("Space")
w("Sleep 900ms")
w("Space")
w("Sleep 2000ms")
shot("gz_battle")
quit_()
card("83 EGGS TO HATCH", "36 Vital Bracelet lines")
for egg in (75,):
    launch(f"egg {egg} 0.3", settle="1200ms")
    w("Show")
    w("Sleep 4800ms")
    shot(f"hatch{egg}")
    quit_()
card("30-MAP ADVENTURE", "rare mons and loot")
launch("pet 93")
w('Type "a"')
w("Sleep 500ms")
w("Show")
w("Sleep 1200ms")
shot("maps")
w("Enter")
w("Sleep 3000ms")
quit_()
card("SHOPS", "112 items to find and buy")
launch("pet 280")
w('Type "s"')
w("Sleep 500ms")
w("Show")
w("Sleep 900ms")
w("Down")
w("Sleep 400ms")
w("Down")
w("Sleep 900ms")
shot("shop")
quit_()
card("EVOLVE AND FUSE", "your care decides")
launch("pet 155")
w('Type "d"')
w("Sleep 400ms")
w("Show")
w("Sleep 1500ms")
shot("digicore")
quit_()
card("ONLINE MULTIPLAYER", "battle - raid - fuse - chat")
card("PLAY ANYWHERE", "terminal or browser")
card("pip install tuipet", "ff3mmo.com/tuipet", hold="2800ms")
open("tools/promo/trailer2.tape", "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("wrote tools/promo/trailer2.tape,", len(OUT), "lines")
