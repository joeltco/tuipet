#!/usr/bin/env bash
# build_short.sh — cut the vertical "it's alive" Short from the raw vhs takes.
#
# Everything here is REAL CAPTURE: take_install.mp4 is an actual `pip install
# tuipet` into a throwaway venv, take_hatch.mp4 an actual play session seeded by
# tools/promo/seed.py.  Nothing is generated or re-enacted -- the only liberties
# are cuts, speed ramps and captions laid over the footage.
#
# Geometry (MEASURED off a frame, not guessed; FontSize 20 / Padding 0 /
# 1080x700 = 81 cols x 28 rows, so 13.33px per col and 25px per row):
#   LCD plate   575x345 at +45+50   bezel INCLUDING its "TUIPET" tab and the
#                                   "● on" lamp -- a tighter crop clipped both
#                                   and the shot read as a mistake
#   arena       534x296 at +66+78   the screen inside the bezel
#   status      395x200 at +645+50  (8 clean 25px rows: name..Energy)  the live stat panel, the lower third
#   burst      352x198 at +157+150  centred on the hatch (measured at t=11.0)
set -euo pipefail
P="${1:?usage: build_short.sh <workdir>}"
FONT=/usr/share/fonts/TTF/JetBrainsMonoNLNerdFont-ExtraBold.ttf
FONT_R=/usr/share/fonts/TTF/JetBrainsMonoNLNerdFont-SemiBold.ttf
SND=/home/joeltco/projects/tuipet/src/tuipet/data/sounds
BG=0x0b0b0b
mkdir -p "$P/seg" "$P/cap"

cap() { printf '%s' "$2" > "$P/cap/$1.txt"; }   # via file: drawtext eats quotes
cap c1 "one command"
cap c2 "your terminal has a pet"
cap c3 "the egg hatches in real time"
cap c4 "it's alive"
cap c5 "feed it. clean it. train it."
cap c6 "it can die."
cap cta "pip install tuipet"

# seg <out> <src> <in> <dur> <speed> <lcdcrop> <caption> <show_cta 0|1>
seg() {
  local out=$1 src=$2 ss=$3 dur=$4 spd=$5 crp=$6 cp=$7 cta=$8
  local sub=""
  # the CTA belongs on the LAST card only.  Stamped on every segment it read as
  # a watermark and stopped being a call to anything.
  [ "$cta" = 1 ] && sub=",drawtext=fontfile=$FONT:textfile=$P/cap/cta.txt:fontcolor=0xd8dcd6:fontsize=52:x=(w-text_w)/2:y=1600"
  local FC
  if [ "$out" = s1 ]; then                 # terminal-only beat: no stat panel
    FC="[0:v]${crp},setpts=PTS/${spd},scale=1080:-2:flags=neighbor,\
pad=1080:1920:(ow-iw)/2:700:color=${BG}[o2];\
[o2]drawtext=fontfile=${FONT}:textfile=${P}/cap/${cp}.txt:fontcolor=white:fontsize=62:x=(w-text_w)/2:y=280${sub},fps=30[v]"
    ffmpeg -v error -y -ss "$ss" -t "$dur" -i "$src" -filter_complex "$FC" \
      -map "[v]" -an -c:v libx264 -pix_fmt yuv420p -crf 18 "$P/seg/$out.mp4"
    printf 'file %q\n' "$P/seg/$out.mp4" >> "$P/seg/list.txt"
    return
  fi
  ffmpeg -v error -y -ss "$ss" -t "$dur" -i "$src" -filter_complex "\
[0:v]split=2[a][b];\
[a]${crp},setpts=PTS/${spd},scale=1080:-2:flags=neighbor,\
pad=1080:1920:(ow-iw)/2:430:color=${BG}[o1];\
[b]crop=395:200:645:50,setpts=PTS/${spd},scale=760:-2:flags=neighbor[st];\
[o1][st]overlay=(W-w)/2:1150[o2];\
[o2]drawtext=fontfile=${FONT}:textfile=${P}/cap/${cp}.txt:fontcolor=white:fontsize=62:x=(w-text_w)/2:y=280${sub},fps=30[v]" \
    -map "[v]" -an -c:v libx264 -pix_fmt yuv420p -crf 18 "$P/seg/$out.mp4"
  printf 'file %q\n' "$P/seg/$out.mp4" >> "$P/seg/list.txt"
}

LCD="crop=575:345:45:50"
PUNCH="crop=352:198:157:150"
rm -f "$P/seg/list.txt"
# -ss/-t BEFORE -i on purpose: as OUTPUT options they seek the POST-filter
# timeline, so every speed-ramped segment gets cut from the wrong place
# (setpts=PTS/2.6 puts input t=10.4 at output t=4.0)
seg s1 "$P/take_install.mp4" 19.5 3.5 1.4 "crop=1080:500:0:200" c1 0
seg s2 "$P/take_hatch.mp4"    0.2 1.8 1.0 "$LCD"   c2 0
seg s3 "$P/take_hatch.mp4"    4.0 6.4 2.6 "$LCD"   c3 0
seg s4 "$P/take_hatch.mp4"   10.6 1.2 0.6 "$PUNCH" c4 0
seg s5 "$P/take_hatch.mp4"   11.9 1.8 1.0 "$LCD"   c4 0
seg s6 "$P/take_hatch.mp4"   13.6 6.2 1.8 "$LCD"   c5 0
seg s7 "$P/take_hatch.mp4"   20.6 4.0 1.0 "$LCD"   c6 1

ffmpeg -v error -y -f concat -safe 0 -i "$P/seg/list.txt" -c copy "$P/short_mute.mp4"

# --- real game SFX on the beats they belong to -------------------------------
d() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$P/seg/$1.mp4"; }
ms() { python3 -c "print(int(($1)*1000))"; }
T_BOOT=$(ms "$(d s1)")
T_HATCH=$(ms "$(d s1)+$(d s2)+$(d s3)")
T_EAT=$(ms "$(d s1)+$(d s2)+$(d s3)+$(d s4)+$(d s5)+0.9")
T_ALARM=$(ms "$(d s1)+$(d s2)+$(d s3)+$(d s4)+$(d s5)+$(d s6)+0.5")
ffmpeg -v error -y -i "$P/short_mute.mp4" \
  -i "$SND/boot.wav" -i "$SND/hatch.wav" -i "$SND/eat.wav" -i "$SND/alarm.wav" \
  -filter_complex "\
[1:a]adelay=${T_BOOT}|${T_BOOT},volume=0.45[a1];\
[2:a]adelay=${T_HATCH}|${T_HATCH},volume=0.95[a2];\
[3:a]adelay=${T_EAT}|${T_EAT},volume=0.6[a3];\
[4:a]adelay=${T_ALARM}|${T_ALARM},volume=0.5[a4];\
[a1][a2][a3][a4]amix=inputs=4:normalize=0,aresample=48000,apad[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -shortest "$P/short_alive.mp4"
#   apad keeps the mix alive to the last frame; without it -shortest trimmed the
#   VIDEO down to the final SFX and the ending card vanished
echo "==> $P/short_alive.mp4"
ffprobe -v error -show_entries stream=codec_type,width,height,duration -of csv "$P/short_alive.mp4"
