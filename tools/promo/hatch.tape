# tuipet promo — take B: title -> egg -> hatch -> first feed -> idle
Output "/tmp/claude-1000/-home-joeltco/be4ca9c0-50d9-4ece-adff-08135cef962a/scratchpad/promo/take_hatch.mp4"
Set FontSize 20
Set Padding 0
Set Width 1080
Set Height 700
Set Shell "bash"
Set Framerate 30
Hide
Type "cd /home/joeltco/projects/tuipet && rm -rf /tmp/tuipet-promo && TUIPET_SAVE_DIR=/tmp/tuipet-promo .venv-dev/bin/python tools/promo/seed.py egg >/dev/null && clear && TUIPET_SAVE_DIR=/tmp/tuipet-promo TUIPET_NO_SYNC=1 .venv-dev/bin/python -m tuipet"
Enter
Sleep 6s
Show
Sleep 2s
Screenshot "/tmp/claude-1000/-home-joeltco/be4ca9c0-50d9-4ece-adff-08135cef962a/scratchpad/promo/b1_title.png"
Enter
Sleep 3s
Screenshot "/tmp/claude-1000/-home-joeltco/be4ca9c0-50d9-4ece-adff-08135cef962a/scratchpad/promo/b2_egg.png"
Sleep 6s
Screenshot "/tmp/claude-1000/-home-joeltco/be4ca9c0-50d9-4ece-adff-08135cef962a/scratchpad/promo/b3_hatch.png"
Sleep 3s
Type "f"
Sleep 2s
Screenshot "/tmp/claude-1000/-home-joeltco/be4ca9c0-50d9-4ece-adff-08135cef962a/scratchpad/promo/b4_feedmenu.png"
Enter
Sleep 4s
Screenshot "/tmp/claude-1000/-home-joeltco/be4ca9c0-50d9-4ece-adff-08135cef962a/scratchpad/promo/b5_eating.png"
Sleep 4s
Screenshot "/tmp/claude-1000/-home-joeltco/be4ca9c0-50d9-4ece-adff-08135cef962a/scratchpad/promo/b6_idle.png"
Sleep 2s
