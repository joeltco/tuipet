#!/usr/bin/env bash
# build_feature.sh — the SCOPE cut.  The first short showed one Fresh blob eating
# one piece of meat and sold none of the game (Joel 2026-08-18: "doesnt show any
# of the actuql features, how many mons, eggs there are").  Every caption here is
# a COUNT read straight out of src/tuipet/data, and every shot is the screen that
# count belongs to:
#   1547 species with real art      data.load_sprites(), placeholders excluded
#   1423 evolutions.csv rows          46 eggs.json.gz entries
#    462 enemies.csv rows              84 items + 59 foods
#     26 zones.csv rows                41 backgrounds.json.gz keys
# Numbers go stale when content lands -- re-run tools/promo/counts.py before a cut.
set -euo pipefail
P="${1:?usage: build_feature.sh <workdir>}"
FONT=/usr/share/fonts/TTF/JetBrainsMonoNLNerdFont-ExtraBold.ttf
SND=/home/joeltco/projects/tuipet/src/tuipet/data/sounds
BG=0x0b0b0b
mkdir -p "$P/seg2" "$P/cap"
cap() { printf '%s' "$2" > "$P/cap/$1.txt"; }
cap f1  "1,547 creatures"
cap f2  "46 eggs to crack"
cap f3  "1,423 ways to evolve"
cap f4  "462 things that fight back"
cap f5  "time the strike"
cap f5b "then land it"
cap f6  "win and it grows"
cap f7  "26 zones to walk"
cap f8  "84 items. 59 foods."
cap f9  "41 places to live"
cap f10 "and it can die."
cap cta "pip install tuipet"

LCD="crop=575:345:45:50"
PUNCH="crop=352:198:157:150"
rm -f "$P/seg2/list.txt"
# seg <out> <src> <in> <dur> <speed> <crop> <caption> <cta?>
seg() {
  local out=$1 src=$2 ss=$3 dur=$4 spd=$5 crp=$6 cp=$7 cta=$8 sub=""
  [ "$cta" = 1 ] && sub=",drawtext=fontfile=$FONT:textfile=$P/cap/cta.txt:fontcolor=0xd8dcd6:fontsize=52:x=(w-text_w)/2:y=1600"
  ffmpeg -v error -y -ss "$ss" -t "$dur" -i "$src" -filter_complex "\
[0:v]split=2[a][b];\
[a]${crp},setpts=PTS/${spd},scale=1080:-2:flags=neighbor,\
pad=1080:1920:(ow-iw)/2:430:color=${BG}[o1];\
[b]crop=395:200:645:50,setpts=PTS/${spd},scale=760:-2:flags=neighbor[st];\
[o1][st]overlay=(W-w)/2:1150[o2];\
[o2]drawtext=fontfile=${FONT}:textfile=${P}/cap/${cp}.txt:fontcolor=white:fontsize=58:x=(w-text_w)/2:y=280${sub},fps=30[v]" \
    -map "[v]" -an -c:v libx264 -pix_fmt yuv420p -crf 18 "$P/seg2/$out.mp4"
  printf 'file %q\n' "$P/seg2/$out.mp4" >> "$P/seg2/list.txt"
}

# beat order: the roster number over the hatch (the best image we own), then the
# collection, then depth, then FIGHTING (the part that reads as a game), then
# breadth, then the stake that makes any of it matter
seg g1  "$P/take_hatch.mp4"  10.6 1.2 0.6 "$PUNCH" f1  0   # hatch burst
seg g2  "$P/take_screens.mp4" 20.0 2.4 1.0 "$LCD"  f2  0   # DIGITAMA GUIDE 9/46
seg g3  "$P/take_screens.mp4"  5.0 2.4 1.0 "$LCD"  f3  0   # DIGICORE, page 1 of 9
# battle timings MEASURED off the take, not guessed: an arena-ink scan put the
# two-sprite face-off at 2.5-4.5, the hit flash (arena inverts, 38% ink) at
# 11.0-11.5, and "VICTORY! training +2" at 26.2-29.0.  The first pass guessed
# and landed on a lone idle sprite for "462 things that fight back"
seg g4  "$P/take_action.mp4"   2.4 2.4 1.0 "$LCD"  f4  0   # both mons, the face-off
seg g5  "$P/take_action.mp4"   4.8 2.2 1.0 "$LCD"  f5  0   # the HIT timing bar
seg g5b "$P/take_action.mp4"   9.6 2.8 1.0 "$LCD"  f5b 0   # the volley + hit flash
seg g6  "$P/take_action.mp4"  26.2 2.6 1.0 "$LCD"  f6  0   # VICTORY! training +2
seg g7  "$P/take_action.mp4"  41.0 2.6 1.0 "$LCD"  f7  0   # ADVENTURE 1/26
seg g8  "$P/take_screens.mp4" 13.2 2.4 1.0 "$LCD"  f8  0   # the shop, tabs + prices
seg g9  "$P/take_screens.mp4"  9.2 2.4 1.0 "$LCD"  f9  0   # SCENES 1 of 31
seg g10 "$P/take_hatch.mp4"   20.6 3.4 1.0 "$LCD"  f10 1   # idle, then the CTA

ffmpeg -v error -y -f concat -safe 0 -i "$P/seg2/list.txt" -c copy "$P/feature_mute.mp4"
d() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$P/seg2/$1.mp4"; }
ms() { python3 -c "print(int(($1)*1000))"; }
T_HATCH=0
T_HIT=$(ms "$(d g1)+$(d g2)+$(d g3)+$(d g4)+0.4")
T_HIT2=$(ms "$(d g1)+$(d g2)+$(d g3)+$(d g4)+$(d g5)+1.4")
T_WIN=$(ms "$(d g1)+$(d g2)+$(d g3)+$(d g4)+$(d g5)+$(d g5b)+0.2")
T_END=$(ms "$(d g1)+$(d g2)+$(d g3)+$(d g4)+$(d g5)+$(d g5b)+$(d g6)+$(d g7)+$(d g8)+$(d g9)+0.4")
ffmpeg -v error -y -i "$P/feature_mute.mp4" \
  -i "$SND/hatch.wav" -i "$SND/attackHit.wav" -i "$SND/strongHit.wav" \
  -i "$SND/win.wav" -i "$SND/alarm.wav" \
  -filter_complex "\
[1:a]adelay=${T_HATCH}|${T_HATCH},volume=0.95[a1];\
[2:a]adelay=${T_HIT}|${T_HIT},volume=0.8[a2];\
[3:a]adelay=${T_HIT2}|${T_HIT2},volume=0.8[a3];\
[4:a]adelay=${T_WIN}|${T_WIN},volume=0.7[a4];\
[5:a]adelay=${T_END}|${T_END},volume=0.5[a5];\
[a1][a2][a3][a4][a5]amix=inputs=5:normalize=0,aresample=48000,apad[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -shortest "$P/feature.mp4"
echo "==> $P/feature.mp4"
ffprobe -v error -show_entries stream=codec_type,width,height,duration -of csv "$P/feature.mp4"
