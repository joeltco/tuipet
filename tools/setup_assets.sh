#!/usr/bin/env bash
# Regenerate tuipet's game data from your own copy of DVPet.
# DVPet (free): https://theundersigned.itch.io/dvpet
#
# Usage: tools/setup_assets.sh /path/to/DVPet.jar
#
# These assets are NOT distributed with tuipet — they are derived from DVPet
# (a Digimon fan game) and remain the property of their respective creators.
set -euo pipefail
JAR="${1:-}"
if [ -z "$JAR" ] || [ ! -f "$JAR" ]; then
  echo "Usage: $0 /path/to/DVPet.jar"; exit 1
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -rf _extract && mkdir -p _extract/jar
( cd _extract/jar && unzip -oq "$JAR" )
ln -sfn _extract/jar/resources raw_resources
ln -sfn _extract/jar/Model raw_model
mkdir -p src/tuipet/data
for f in digimon evolutions foods items enemies maps zones towns shopConsumable habitats; do
  cp "raw_model/$f.csv" "src/tuipet/data/$f.csv"
done
python tools/extract_sprites.py
python tools/extract_effects.py
echo "Done. Game data written to src/tuipet/data/ — you can now run: tuipet"
