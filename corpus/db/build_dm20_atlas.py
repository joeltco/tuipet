#!/usr/bin/env python3
"""Build the DM20 sprite atlas from the authentic DVPet 16x16 LCD art.

The roster (which mons, num order, stage, attribute) comes from the humulos DM20
corpus (dm20.json).  The ART comes from the DVPet sprite rips (dvpet_sprites.json.gz)
-- clean, hand-authored 16x16 LCD sprites -- looked up by name (+ a romanization /
dub alias table for the 42 names the corpus spells differently).

NOTE: the wayland fan PNGs were tried first but are hand-drawn at ~3px stroke pitch
on a 64px canvas; crushing them to 16x16 turns every mon to mush.  The DVPet rips are
already native 16x16 and crisp, so we use those.

DVPet frames are in DVPet pose order (11 frames):
  0 idle      1 idle-B/walk-B  2 sleep   3 stretch/yawn  4 cheer-down  5 excited
  6 attack/cheer-up  7 eat-chew  8 eat-swallow  9 dejected/fail  10 collapse/dying

We keep frames in DVPet NATIVE order (species.ROLES + the pose constants + anim.py
all index this order, exactly as they did before the rebuild).

Output: src/tuipet/data/dm20_sprites.json.gz  (list of {num,id,name,stage,attribute,w,h,frames,source})
Run: python3 corpus/db/build_dm20_atlas.py
"""
import gzip
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(CORPUS, ".."))
DB = os.path.join(CORPUS, "db", "dm20.json")
ART = os.path.join(CORPUS, "db", "dvpet_sprites.json.gz")
OUT = os.path.join(REPO, "src", "tuipet", "data", "dm20_sprites.json.gz")

# DVPet native frame names, by index (the order species.ROLES / pose constants / anim.py
# all index into — verified against DVPet View/SpriteAnim drawNum() args).
FRAME_NAMES = ["idle", "idle_b", "sleep", "stretch", "cheer_down", "excited",
               "attack", "eat_chew", "eat_swallow", "dejected", "collapse"]

# Corpus name -> DVPet sprite name, for the 42 mons the two sources spell differently
# (romanization, dub names, and partner skins that fall back to their base form).
ALIASES = {
    "Beelzebumon": "Beelzemon", "Belial Vamdemon": "MaloMyotismon",
    "Belphemon: Rage Mode": "Belphemon", "Centalmon": "Centarumon",
    "Cockatrimon": "Kokatorimon", "Coredramon (Blue)": "Coredramon",
    "Coredramon (Green)": "Coredramon", "Craniummon": "Craniumon",
    "Dark Tyranomon": "DarkTyrannomon", "DORUguremon": "DoruGreymon",
    "Dukemon": "Gallantmon", "Ex-Tyranomon": "ExTyrannomon",
    "Imperialdramon: Paladin Mode": "Imperialdramon PM",
    "Lord Knightmon": "Crusadermon", "Lucemon: Falldown Mode": "Lucemon FM",
    "Metal Tyranomon": "MetalTyrannomon", "Mugendramon": "Machinedramon",
    "Murmukusmon": "Murmuxmon", "Nanomon": "Datamon", "Omegamon": "Omnimon",
    "Omegamon Alter S": "Omnimon Alter-S", "Piccolomon": "Piximon",
    "Pinochimon": "Puppetmon", "Pitchmon": "Pickmon", "Piyomon": "Biyomon",
    "Plotmon": "Salamon", "Pukamon": "Pukumon", "Rust Tyranomon": "RustTyrannomon",
    "Scumon": "Sukamon", "Skull Mammon": "SkullMammothmon",
    "Taichi's Agumon": "Agumon", "Taichi's Greymon": "Greymon",
    "Taichi's Metal Greymon": "MetalGreymon", "Taichi's War Greymon": "WarGreymon",
    "Tunomon": "Tsunomon", "Tyranomon": "Tyrannomon",
    "Ulforce V-dramon": "UlforceVeedramon", "Yamato's Gabumon": "Gabumon",
    "Yamato's Garurumon": "Garurumon", "Yamato's Metal Garurumon": "MetalGarurumon",
    "Yamato's Were Garurumon": "WereGarurumon", "Yukidarumon": "Frigimon",
}

BLANK = ["0" * 16] * 16


def _norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def _load_art():
    with gzip.open(ART, "rt", encoding="utf-8") as fh:
        data = json.load(fh)
    sp = data["sprites"] if isinstance(data, dict) else data
    by = {}
    for r in sp:
        by.setdefault(_norm(r["name"]), r)
    return by


def main():
    db = json.load(open(DB))
    art = _load_art()
    recs, miss = [], []
    for i, r in enumerate(db["digimon"]):
        name = r["name"]
        src = art.get(_norm(ALIASES.get(name, name))) or art.get(_norm(name))
        if src:
            frames = src["frames"] or [BLANK]    # native DVPet order, positions preserved (runtime fills empties)
            source = "dvpet:" + src["name"]
        else:
            frames = []
            miss.append(name)
            source = None
        recs.append({
            "num": i, "id": r["id"], "name": name, "stage": r["stage"],
            "attribute": r.get("attribute"), "w": 16, "h": 16,
            "frames": frames, "source": source,
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as fh:
        json.dump({"_meta": {"device": "dm20", "count": len(recs),
                             "frame_names": FRAME_NAMES, "missing": miss}, "sprites": recs}, fh,
                  ensure_ascii=False)
    print(f"wrote {OUT}: {len(recs)} sprites")
    print(f"missing art: {miss or 'none'}")


if __name__ == "__main__":
    main()
