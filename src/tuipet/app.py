"""DVPet TUI — a terminal virtual pet rendered with halfblock sprites."""
from __future__ import annotations
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from . import data
from . import egg as egg_mod
from . import training
from . import battlescreen
from . import adventurescreen
from . import shopscreen
from . import habitatscreen
from . import digicorescreen
from . import eggselectscreen
from . import persistence
from . import jogressscreen
from . import jogress
from . import tournamentscreen
from . import titlescreen
from . import themescreen
from . import deathscreen
from . import sound
from .pet import Pet
from .render import render_screen
import os

from . import theme
from .theme import LCD_ON, LCD_BG, PHASE_PALETTE, SIL_DAY, SIL_NIGHT
SCREEN_COLS, SCREEN_ROWS = 40, 12
SPRITE_W = 16                                   # native creature sprite width
WALK_RANGE = (SCREEN_COLS - SPRITE_W) // 5      # how far the pet paces from centre (stays central)


def hearts(n, total=4, color=None):
    color = color or theme.HEART
    return f"[{color}]" + "●" * n + "[/][dim]" + "○" * (total - n) + "[/dim]"


def bar(v, width=12, color=None):
    color = color or theme.LIFE
    fill = round(v / 100 * width)
    return f"[{color}]" + "█" * fill + "[/][dim]" + "─" * (width - fill) + "[/dim]"


_FX = data.load_effects()
GRAVESTONE = _FX.get("grave", [None])[0]      # real DVPet death.png
SUN = _FX.get("sun", [None])[0]               # real DVPet noon.png
MOON = _FX.get("moon", [None])[0]             # real DVPet night.png

_POOP_FR = (_FX.get("poop") or [None])[0]
POOP_W = len(_POOP_FR[0]) if _POOP_FR else 5
_FROZEN_FR = (_FX.get("frozen") or [None])[0]

WEATHER_GLYPH = {
    "Clear": "", "Cloudy": chr(0x2601), "Drizzling": chr(0x2602),
    "Raining": chr(0x2602), "HeavyRain": chr(0x2614),
    "LightSnow": chr(0x2744), "Snowing": chr(0x2744), "HeavySnow": chr(0x2744),
}
_RAIN = {"Drizzling", "Raining", "HeavyRain"}
_SNOW = {"LightSnow", "Snowing", "HeavySnow"}
_PRECIP = _RAIN | _SNOW
_PRECIP_N = {"Drizzling": 5, "LightSnow": 6, "Raining": 11, "Snowing": 10,
             "HeavyRain": 18, "HeavySnow": 16}
CLOUD = ["0011100", "0111111", "1111111"]

_K = "b cyan"
KEYS = (
    f"[{_K}]f[/] feed   [{_K}]p[/] play   [{_K}]c[/] clean   [{_K}]h[/] heal   [{_K}]s[/] sleep\n"
    f"[{_K}]t[/] train  [{_K}]b[/] battle  [{_K}]a[/] adventure  [{_K}]u[/] cup  [{_K}]j[/] jogress\n"
    f"[{_K}]o[/] shop  [{_K}]e[/] habitat  [{_K}]d[/] data  [{_K}]g[/] theme  [{_K}]m[/] sound  [{_K}]n[/] new  [{_K}]q[/] quit"
)


def _sound_path():
    return os.path.join(persistence.SAVE_DIR, "sound.txt")


def _load_sound():
    try:
        return open(_sound_path()).read().strip() != "off"
    except OSError:
        return True


def _save_sound(on):
    try:
        os.makedirs(persistence.SAVE_DIR, exist_ok=True)
        with open(_sound_path(), "w") as fh:
            fh.write("on" if on else "off")
    except OSError:
        pass


def _scale_hex(hexcol, f):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    cl = lambda v: max(0, min(255, int(v * f)))
    return "#%02x%02x%02x" % (cl(r), cl(g), cl(b))


def _weather_overlay(weather, frame_i, cols, px_h):
    pts = []
    if weather == "Cloudy" or weather in _RAIN or weather in _SNOW:
        for y, line in enumerate(CLOUD):          # a cloud bank, top-left
            for x, ch in enumerate(line):
                if ch == "1":
                    pts.append((1 + x, 1 + y))
    n = _PRECIP_N.get(weather, 0)
    if n:
        snow = weather in _SNOW
        for i in range(n):
            x0 = (i * 7 + 3) % cols
            base = (i * 5) % px_h
            if snow:
                y = (base + frame_i) % px_h                  # slow, drifting
                x = (x0 + ((frame_i // 2 + i) % 3 - 1)) % cols
                pts.append((x, y))
            else:
                y = (base + frame_i * 2) % px_h              # fast, slanted streaks
                x = (x0 + y // 2) % cols
                pts.append((x, y))
                pts.append((x, (y - 1) % px_h))
    return pts


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _effect_overlay(pet, frame_i, cols, px_h):
    """Auxiliary status sprites overlaid on the LCD (poop/Zzz/frost/food/emotes)."""
    E = data.load_effects()
    pts = []
    if pet.dead:
        return pts
    pm = E.get("poop", [None])[0]
    if pet.poop and pm:                                   # a row of piles, bottom-left (DVPet filth)
        pw = len(pm[0])
        for i in range(min(pet.poop, 3)):
            pts += _blit(pm, 2 + i * (pw + 1), px_h - len(pm) - 2)
    if pet.num == -1:
        return pts
    if pet.asleep and E.get("zzz"):                       # Zzz above a sleeper
        z = E["zzz"][frame_i % len(E["zzz"])]
        pts += _blit(z, cols // 2 + 5, 0)   # float above the sleeper's head
    emo = ("happy" if pet.anim == "happy" else
           "unhappy" if pet.anim in ("sad", "refuse") else
           "depressed" if pet.anim in ("angry", "tantrum") else None)
    if emo and E.get(emo):                                # emote bubble on reactions
        ef = E[emo][frame_i % len(E[emo])]
        pts += _blit(ef, cols - len(ef[0]) - 2, 1)
    elif (pet.anim in ("idle", "walk") and frame_i % 2 == 0 and E.get("attention")
          and (pet.hunger == 0 or pet.sick or pet.poop >= 3 or pet.energy <= 0)):
        pts += _blit(E["attention"][0], cols - len(E["attention"][0][0]) - 2, 1)  # '!' call for care
    return pts


class Screen(Static):
    """The animated LCD screen."""
    def on_mount(self):
        self.frame_i = 0
        self.walk_x = 0
        self.walk_dir = 1
        self.fx = None        # active care-action animation

    def paint(self, pet: Pet):
        if self.fx:
            return self._paint_fx(pet)
        on, bg = PHASE_PALETTE.get(pet.day_phase, (LCD_ON, LCD_BG))
        bgimg = self._background(pet)
        corner = None                      # DVPet shows time via bg frame + palette, no corner icon
        if bgimg:
            on = SIL_NIGHT if pet.day_phase == "night" else SIL_DAY   # silhouette ink
        else:
            w = pet.weather
            if w in _RAIN:
                bg = _scale_hex(bg, 0.78)
            elif w in _SNOW:
                bg = _scale_hex(bg, 0.85)
            elif w == "Cloudy":
                bg = _scale_hex(bg, 0.9)
        overlay = (_weather_overlay(pet.weather, self.frame_i, SCREEN_COLS, SCREEN_ROWS * 2)
                   + _effect_overlay(pet, self.frame_i, SCREEN_COLS, SCREEN_ROWS * 2))
        if pet.dead:                           # a grave marker
            self.update(render_screen(GRAVESTONE, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                      corner=corner, overlay=overlay, bgimg=bgimg))
            return
        if pet.num == -1:                      # egg
            rec = egg_mod.record(pet.egg_type)
            roles = egg_mod.ROLES
        else:
            _, by_num = data.load_sprites()
            rec = by_num[pet.num]
            roles = data.ROLES
        frames = roles.get(pet.anim, [0])
        first = next((f for f in rec["frames"] if f), rec["frames"][0])
        idx = frames[self.frame_i % len(frames)]
        rows = rec["frames"][idx] or first
        xshift, mirror = 0, False
        if pet.anim in ("idle", "walk") and (pet.is_geriatric or pet.sick):
            rows = rec["frames"][9] or first   # elderly/sick: stand still in the weary pose
        elif pet.anim in ("idle", "walk") and pet.num != -1:
            # pace back and forth; poop on the floor shrinks the free space -- the
            # pet still walks, just in the room to the right of the pile (DVPet
            # stepFrame uses filthLabel width as the left walk bound)
            sw = max(len(r) for r in rows)
            base = (SCREEN_COLS - sw) // 2
            poop_right = (2 + min(pet.poop, 3) * (POOP_W + 1)) if pet.poop else 0
            lo = max(base - WALK_RANGE, poop_right)
            hi = min(SCREEN_COLS - sw - 1, max(base + WALK_RANGE, lo + 6))
            lo = min(lo, hi)
            self.walk_lo, self.walk_hi = lo - base, hi - base
            xshift = max(self.walk_lo, min(self.walk_hi, self.walk_x))
            mirror = self.walk_dir > 0         # mirror=True faces right (sprites face left by default)
        else:
            mirror = pet.anim in data.MIRROR_ROLES and self.frame_i % 2 == 1
        if pet.num != -1 and pet.status_word() == "freezing" and _FROZEN_FR:
            rows, xshift, mirror = _FROZEN_FR, 0, False    # encased in ice
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  mirror=mirror, xshift=xshift, corner=corner, overlay=overlay, bgimg=bgimg))

    def _background(self, pet):
        return pet.background()

    def advance(self):
        self.frame_i += 1
        lo = getattr(self, "walk_lo", -WALK_RANGE)
        hi = getattr(self, "walk_hi", WALK_RANGE)
        self.walk_x += self.walk_dir
        if self.walk_x >= hi:                   # hit a wall (screen edge or poop): turn around
            self.walk_x, self.walk_dir = hi, -1
        elif self.walk_x <= lo:
            self.walk_x, self.walk_dir = lo, 1

    # ---- care-action animations (DVPet SpriteAnim eat/clean/cheer) -----------
    def start_fx(self, kind, icon=None, poop=0, old_num=None):
        steps = {"eat": 16, "cheer": 14, "clean": 16, "spit": 11, "evolve": 18, "dying": 18}.get(kind, 12)
        self.fx = {"kind": kind, "step": 0, "steps": steps, "icon": icon, "poop": poop, "old_num": old_num}

    def advance_fx(self):
        if not self.fx:
            return False
        self.fx["step"] += 1
        if self.fx["step"] < self.fx["steps"]:
            return True
        kind = self.fx["kind"]
        self.fx = None
        if kind in ("eat", "clean"):   # eating and a good wash end in the happy 'sunshine'
            self.start_fx("cheer")
        return self.fx is not None

    def _pose_rows(self, pet, role, phase):
        if pet.num == -1:
            rec = egg_mod.record(pet.egg_type)
            roles = egg_mod.ROLES
        else:
            _, by_num = data.load_sprites()
            rec = by_num[pet.num]
            roles = data.ROLES
        frames = roles.get(role, [0])
        first = next((f for f in rec["frames"] if f), rec["frames"][0])
        return rec["frames"][frames[phase % len(frames)]] or first

    def _food_frames(self, key):
        raw = data.load_icons().get(key)
        if not raw:
            return None
        return [[r[::3] for r in fr[::3]] for fr in raw]   # 24px (3x) -> native 8px

    def _paint_fx(self, pet):
        fx = self.fx
        on, bg = PHASE_PALETTE.get(pet.day_phase, (LCD_ON, LCD_BG))
        bgimg = self._background(pet)
        if bgimg:
            on = SIL_NIGHT if pet.day_phase == "night" else SIL_DAY
        px_h = SCREEN_ROWS * 2
        step = fx["step"]
        pose = {"eat": "eat", "clean": "idle", "cheer": "happy", "spit": "refuse", "dying": "exhausted"}.get(fx["kind"], "idle")
        rows = self._pose_rows(pet, pose, step // 2)
        overlay = _weather_overlay(pet.weather, self.frame_i, SCREEN_COLS, px_h)
        xshift = 0
        if fx["kind"] == "eat":
            xshift = 9                                         # pet sits right, faces its food
            food = self._food_frames(fx.get("icon") or "f:0")
            if food:
                if step < 5:
                    fi, fy = 0, 4 + step                       # food drops in on the left
                else:
                    fi, fy = min(3, 1 + (step - 5) // 3), 9     # ...monster chomps it away
                overlay += _blit(food[min(fi, len(food) - 1)], 12, fy)
        elif fx["kind"] == "clean":
            E = data.load_effects()
            wash = E.get("wash", [None])[0]
            wx = SCREEN_COLS - 3 - step * 3                    # wash sweeps the screen R -> L
            pm = E.get("poop", [None])[0]
            if pm and fx.get("poop"):                          # filth squeegeed left, off-screen
                pw = len(pm[0])
                for i in range(min(fx["poop"], 3)):
                    px = i * (pw + 1)
                    if wx <= px + pw:                          # wash front reached this pile
                        px = wx - pw                           # ...so it rides off to the left
                    if px + pw > 0:
                        overlay += _blit(pm, px, px_h - len(pm) - 2)
            if wash:
                overlay += _blit(wash, wx, max(0, (px_h - len(wash)) // 2))
            sw = max(len(r) for r in rows)
            xshift = min(0, wx - sw - (SCREEN_COLS - sw) // 2)  # pet swept left in lockstep with the wash
        elif fx["kind"] == "cheer":
            hap = data.load_effects().get("happy")
            if hap and (step // 2) % 2 == 0:                   # pulsing happy sparkle
                hf = hap[(step // 2) % len(hap)]
                overlay += _blit(hf, SCREEN_COLS - len(hf[0]) - 2, 1)
        elif fx["kind"] == "spit":
            xshift = 9                                         # too full: rejected food
            food = self._food_frames(fx.get("icon") or "f:0")
            if food:
                overlay += _blit(food[0], 12, 5 + step * 2)    # ...drops away off-screen
        elif fx["kind"] == "evolve":
            n = fx["steps"]
            if step < n // 3:                                  # 1) the old form shakes
                old = fx.get("old_num")
                if old not in (None, -1):
                    rec = data.load_sprites()[1].get(old)
                    if rec and rec["frames"][0]:
                        rows = rec["frames"][0]
                xshift = -2 if step % 2 else 2
            elif step < 2 * n // 3:                            # 2) dither / static transition
                overlay = overlay + [(x, y) for y in range(px_h) for x in range(SCREEN_COLS)
                                     if (x + y + step) % 2 == 0]
            # 3) reveal: rows is already the evolved form
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  xshift=xshift, overlay=overlay, bgimg=bgimg,
                                  mirror=(fx["kind"] == "dying")))


class Stats(Static):
    def paint(self, pet: Pet):
        if pet.dead:
            return self._paint_grave(pet)
        if pet.num == -1 or pet.stage == "Egg":
            return self._paint_egg(pet)
        T = theme
        div = f"[dim]{'─' * 26}[/]"
        deco = []
        if pet.asleep: deco.append("[blue]Zzz[/]")
        if pet.sick: deco.append(f"[{T.NEG}]+sick[/]")
        if pet.poop: deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
        mins, secs = divmod(int(pet.age_seconds), 60)
        picon = chr(0x2600) if pet.is_daytime else chr(0x263E)
        wglyph = WEATHER_GLYPH.get(pet.weather, "")
        aff = pet._affinity()
        amark = (f"[{T.POS}]" + chr(0x2665) + "[/]" if aff > 0
                 else (f"[{T.NEG}]" + chr(0x2716) + "[/]" if aff < 0 else "[dim]·[/dim]"))
        xm = f" [b {T.ACCENT}]X[/]" if pet.x_antibody != "None" else ""
        lifepct = max(0, int((pet.lifespan - pet.age_seconds) / max(1, pet.lifespan) * 100))
        lifecol = T.NEG if pet.is_geriatric else T.LIFE
        self.border_subtitle = f"gen {pet.generation}"
        lines = [
            f"[b]{pet.name[:22]}[/]{xm}",
            f"[dim]{pet.stage} · {pet.attribute}[/]",
            div,
            f"Hunger  {hearts(pet.hunger)}",
            f"Effort  {hearts(pet.strength)}",
            f"Energy  {bar(pet.energy, 12, T.ENERGY)}",
            f"Mood    {bar(pet.mood, 12, T.MOOD)}",
            div,
            f"Power   [{T.POS}]V{pet.vaccine}[/] [{T.ENERGY}]D{pet.data_power}[/] [{T.MOOD}]Vi{pet.virus}[/]",
            f"Weight {pet.weight}g   [{T.COIN}]{pet.bits}b[/]",
            f"Battle {pet.wins}W/{pet.battles}   [{T.COIN}]\u2605{pet.trophies}[/]",
            div,
            f"@{pet.habitat_obj()['name'][:14]} {amark} [dim]{pet.season}[/]",
            f"[{T.COIN}]{picon}[/][dim]{pet.day_phase} {wglyph}{pet.weather} {int(pet.temp)}\u00b0[/] [dim]{mins}m{secs:02d}s[/]",
            f"Life    {bar(lifepct, 12, lifecol)}",
            f"[b]{pet.status_word()}[/]   " + "  ".join(deco),
        ]
        self.update("\n".join(lines))

    def _paint_egg(self, pet):
        mins, secs = divmod(int(pet.age_seconds), 60)
        self.border_subtitle = f"gen {pet.generation}"
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            "[b]Digitama[/] [dim]· egg[/]",
            div,
            "[dim]a new life is warming[/]",
            "",
            "Destined to hatch",
            f"  [b]{egg_mod.hatch_name(pet.egg_type)}[/]",
            div,
            f"Age     {mins}m{secs:02d}s",
            "",
            "[dim]keep it cosy — it[/]",
            "[dim]hatches on its own[/]",
        ]
        self.update("\n".join(lines))

    def _paint_grave(self, pet):
        mins = int(pet.age_seconds) // 60
        self.border_subtitle = f"gen {pet.generation}"
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            f"[b]{pet.name[:16]}[/] [dim]· rest[/]",
            div,
            "[dim]a life remembered[/]",
            "",
            f"Lived    {mins}m",
            f"Reached  {pet.stage}",
            f"Attrib   {pet.attribute}",
            f"Record   {pet.wins}W / {pet.battles}",
            div,
            "[dim]gone, but not[/]",
            "[dim]forgotten.[/]",
            "",
            "[dim]press N for a new egg[/]",
        ]
        self.update("\n".join(lines))


class TuiPetApp(App):
    CSS = """
    Screen { align: center middle; }
    #wrap { width: auto; height: auto; }
    #top { width: auto; height: auto; }
    #left { width: 44; height: auto; }
    #lcd { border: thick #7a7e78; padding: 0 1; background: #c6c9cc; width: 44; height: 14; }
    #msg {
        border: round #7a7e78; padding: 0 1; width: 44; height: 3; margin-top: 1;
        color: #7d8186; content-align: left middle;
    }
    #stats { border: round #7a7e78; padding: 0 1; width: 30; height: 18; margin-left: 1; }
    #keys {
        border: round #7a7e78; padding: 0 1; width: 75; height: 5; margin-top: 1; color: #7d8186;
    }
    """
    BINDINGS = [
        ("f", "feed", "Feed"), ("t", "train", "Train"), ("b", "battle", "Battle"),
        ("p", "play", "Play"), ("c", "clean", "Clean"), ("h", "heal", "Heal"),
        ("a", "adventure", "Adventure"), ("o", "shop", "Shop"), ("e", "habitat", "Habitat"),
        ("d", "digicore", "DigiCore"),
        ("j", "jogress", "Jogress"), ("u", "tournament", "Cup"),
        ("s", "sleep", "Sleep"), ("g", "theme", "Theme"), ("m", "sound", "Sound"), ("n", "new", "New pet"), ("q", "quit", "Quit"),
    ]

    def __init__(self, pet: Pet | None = None):
        super().__init__()
        self._welcome = "Welcome! Raise your pet."
        self._new_game = False
        if pet is None:
            loaded, msg = persistence.load()
            if loaded is not None:
                pet, self._welcome = loaded, (msg or "Welcome back!")
            else:
                self._new_game = True
        self.pet = pet or Pet.new_egg()
        self.mode = None            # active in-display panel (no pop-up screens)
        self._dying_fx = False      # playing the death animation before the memorial
        self._mode_close = None
        self.sound = _load_sound()
        self._needs = False

    def compose(self) -> ComposeResult:
        with Vertical(id="wrap"):
            with Horizontal(id="top"):
                with Vertical(id="left"):
                    yield Screen(id="lcd")
                    yield Static("Welcome! Raise your pet.", id="msg")
                yield Stats(id="stats")
            yield Static(KEYS, id="keys")

    def on_mount(self):
        self.screen_w = self.query_one("#lcd", Screen)
        self.stats_w = self.query_one("#stats", Stats)
        self.msg_w = self.query_one("#msg", Static)
        self.keys_w = self.query_one("#keys", Static)
        self.screen_w.border_title = "TUIPET"
        self.stats_w.border_title = "STATUS"
        self.keys_w.border_title = "ACTIONS"
        self.screen_w.border_subtitle = "● on"
        self.msg_w.update(self._welcome)
        theme.apply(theme.load_choice())
        self._restyle()
        self.repaint()
        self._open_mode(titlescreen.TitlePanel(), self._after_title)
        self.msg_w.update("[b]▸ PRESS ENTER ◂[/b]")
        self.set_interval(0.45, self.on_anim)
        self.set_interval(0.12, self.on_fast)
        self.set_interval(1.0, self.on_tick)
        self.set_interval(10.0, self.autosave)

    def _after_title(self, _=None):
        if self._new_game:
            self._open_mode(eggselectscreen.EggSelectPanel(), self._after_egg_pick)
        else:
            self.msg_w.update(self._welcome)
            self.repaint()

    def _after_death(self, result):
        if result == "new":
            self.action_new()
        else:
            self.repaint()

    def _after_egg_pick(self, egg_type):
        if egg_type is not None:
            self.pet = Pet.new_egg(egg_type=egg_type)
        self.flash("Take good care of your egg!")
        self.repaint()

    def autosave(self):
        persistence.save(self.pet)

    def on_unmount(self):
        persistence.save(self.pet)

    def on_key(self, event):
        if self.mode is not None:
            event.stop()
            result = self.mode.key(event.key)
            if result is not None and result[0] == "done":
                self._close_mode(result[1])
            else:
                self.repaint()

    def _open_mode(self, panel, on_close=None):
        self.mode = panel
        self._mode_close = on_close
        self.repaint()

    def _close_mode(self, result):
        cb = self._mode_close
        self.mode = None
        self._mode_close = None
        if cb:
            cb(result)
        else:
            self.repaint()

    def action_quit(self):
        persistence.save(self.pet)
        self.exit()

    def beep(self, name=None, bell=True):
        if not self.sound:
            return
        if name and sound.play(name):
            return
        if bell:
            self.bell()

    def action_sound(self):
        self.sound = not self.sound
        _save_sound(self.sound)
        self.flash(f"Sound: {'on' if self.sound else 'off'}")
        if self.sound:
            self.bell()

    def _restyle(self):
        try:
            for w in (self.screen_w, self.stats_w, self.msg_w, self.keys_w):
                w.styles.border = ("round", theme.BORDER)
                w.styles.border_title_color = theme.MID
            self.screen_w.styles.border = ("thick", theme.BORDER)
            self.screen_w.styles.border_subtitle_color = theme.ACCENT
            self.screen_w.styles.background = theme.LCD_BG
            self.msg_w.styles.color = theme.MID
            self.keys_w.styles.color = theme.MID
        except Exception:
            pass

    def action_theme(self):
        self._open_mode(themescreen.ThemePanel(on_change=self._restyle), self._after_theme)

    def _after_theme(self, _=None):
        self._restyle()
        self.flash(f"Theme: {theme.current()}")
        self.repaint()

    def _center(self, text):
        from rich.text import Text
        n = text.plain.count("\n") + 1
        pad = max(0, (SCREEN_ROWS - n) // 2)
        if not pad:
            return text
        out = Text("\n" * pad)
        out.append_text(text)
        return out

    def repaint(self):
        if self.mode is not None:
            self.screen_w.update(self._center(self.mode.text()))
        else:
            self.screen_w.paint(self.pet)
        if isinstance(self.mode, titlescreen.TitlePanel):
            self._status_card("TUIPET", ["[dim]a terminal v-pet[/]", "", "",
                                         "[dim]a creature awaits[/]", "",
                                         "[dim]press ENTER[/]", "[dim]to begin[/]"])
        elif isinstance(self.mode, eggselectscreen.EggSelectPanel):
            i = self.mode.i
            self._status_card("New Egg", [f"[dim]{i + 1} of {egg_mod.count()} eggs[/]", "",
                                          "Destined to hatch", f"  [b]{egg_mod.hatch_name(i)}[/]", "",
                                          "[dim]←→ ↑↓ browse[/]", "[dim]ENTER to choose[/]"])
        elif isinstance(self.mode, adventurescreen.AdventurePanel):
            self._status_adventure()
        elif isinstance(self.mode, tournamentscreen.TournamentPanel):
            self._status_tournament()
        elif isinstance(self.mode, training.TrainingPanel):
            self._status_training()
        elif isinstance(self.mode, digicorescreen.DigiCorePanel):
            dp = self.mode
            toc = [(f"[b]▸ {t}[/]" if j == dp.i else f"[dim]  {t}[/]")
                   for j, (t, _) in enumerate(dp.pages)]
            self._status_card("Data Book", [
                f"[b]{self.pet.name[:14]}[/]",
                f"[dim]{self.pet.stage} · {self.pet.attribute}[/]",
                "",
            ] + toc + ["", "[dim]←/→ flip   ESC close[/]"])
        else:
            self.stats_w.paint(self.pet)

    def _status_card(self, title, lines):
        self.stats_w.border_subtitle = ""
        body = [f"[b]{title}[/]", f"[dim]{'─' * 26}[/]"] + lines
        self.stats_w.update("\n".join(body))

    def _status_tournament(self):
        p, t, T = self.pet, self.mode.tourney, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'─' * 26}[/]"
        if t.over and t.champion:
            lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                     f"[b]{t.name[:24]}[/]", "",
                     f"[{T.POS}]\u2605 CHAMPION \u2605[/]", "",
                     f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]",
                     f"Reward   [{T.COIN}]+{t.reward_bits}b[/]", div,
                     "[dim]you took the cup![/]"]
        elif t.over:
            lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                     f"[b]{t.name[:24]}[/]", "",
                     f"[{T.NEG}]eliminated[/]",
                     f"[dim]in the {t.round_name}[/]", "",
                     f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]", div,
                     "[dim]train up, try again[/]"]
        else:
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                f"[b]{t.name[:24]}[/]",
                f"Match    {t.round + 1} / 3",
                f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]",
                div,
                f"Effort   {hearts(p.strength)}",
                f"Energy   {bar(p.energy, 11, T.ENERGY)}",
                f"Power    [{T.POS}]V{p.vaccine}[/] [{T.ENERGY}]D{p.data_power}[/] [{T.MOOD}]Vi{p.virus}[/]",
                div,
                "[dim]fight for the cup[/]",
            ]
        self.stats_w.update("\n".join(lines))

    def _status_training(self):
        from .training import (GAMES, VACCINE_HITS_MIN, VACCINE_WINDOW,
                               HP_ROUNDS, DATA_REPS, VIRUS_BAR_MIN)
        p, tp, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'-' * 26}[/]".replace("-", "\u2500")
        eff = hearts(p.strength)
        energy = bar(p.energy, 11, T.ENERGY)
        power = f"[{T.POS}]V{p.vaccine}[/] [{T.ENERGY}]D{p.data_power}[/] [{T.MOOD}]Vi{p.virus}[/]"
        label = GAMES[tp.gi][1]
        gk = tp.gkey
        if tp.phase == "menu":
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     "[b]choose a drill[/]", "",
                     f"Effort   {eff}", f"Power    {power}", f"Energy   {energy}",
                     div, "[dim]pick what to build[/]"]
        elif tp.phase == "done":
            verdict = f"[{T.POS}]drill complete[/]" if tp.success else f"[{T.NEG}]needs work[/]"
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     f"[b]{label}[/]", "", verdict, "",
                     f"Effort   {eff}", f"Energy   {energy}", div,
                     f"[dim]{(tp.result or '')[:24]}[/]"]
        else:
            if gk == "hp":
                dots = "\u25cf" * tp.rounds_won + "\u25cb" * (HP_ROUNDS - tp.rep) + "\u00b7" * (tp.rep - tp.rounds_won)
                prog, prog2 = f"Round    {min(tp.rep + 1, HP_ROUNDS)} / {HP_ROUNDS}", f"Won      {dots}"
                target, flav = f"Effort   {eff}", "build your effort"
            elif gk == "vaccine":
                tpct = max(0, tp.timer) / VACCINE_WINDOW * 100
                prog, prog2 = f"Hits     {tp.taps} / {VACCINE_HITS_MIN}", f"Time     {bar(tpct, 11, T.MOOD)}"
                target, flav = f"Vaccine  [{T.POS}]{p.vaccine}[/]", "mash it up!"
            elif gk == "data":
                dots = "\u25cf" * tp.hits + "\u25cb" * (DATA_REPS - tp.rep) + "\u00b7" * (tp.rep - tp.hits)
                prog, prog2 = f"Shot     {min(tp.rep + 1, DATA_REPS)} / {DATA_REPS}", f"Hits     {dots}"
                target, flav = f"Data     [{T.ENERGY}]{p.data_power}[/]", "shoot the frame"
            else:
                prog, prog2 = f"Power    {int(tp.pos)}", f"Need     {VIRUS_BAR_MIN}"
                target, flav = f"Virus    [{T.MOOD}]{p.virus}[/]", "stop it high"
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     f"[b]{label}[/]", prog, prog2, div,
                     target, f"Energy   {energy}", div, f"[dim]{flav}[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_adventure(self):
        p, a, T = self.pet, self.mode.adv, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'─' * 26}[/]"
        lives = "♥" * a.lives + "[dim]·[/]" * (3 - a.lives)
        power = f"[{T.POS}]V{p.vaccine}[/] [{T.ENERGY}]D{p.data_power}[/] [{T.MOOD}]Vi{p.virus}[/]"
        if self.mode.sub is not None:                       # mid-encounter battle
            e = self.mode.sub.battle.enemy
            tag = f" [{T.NEG}]BOSS[/]" if e.get("boss") else ""
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· battle[/]",
                div,
                f"vs [b]{e['name'][:14]}[/]{tag}",
                f"Lives    {lives}",
                div,
                f"Effort   {hearts(p.strength)}",
                f"Energy   {bar(p.energy, 11, T.ENERGY)}",
                f"Power    {power}",
                div,
                "[dim]a wild foe blocks[/]",
                "[dim]the path — fight![/]",
            ]
        else:                                               # travelling
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· away[/]",
                div,
                f"Map      {a.mi + 1}-{a.zi + 1}",
                f"Lives    {lives}",
                f"Progress {a.pct}%",
                f"Bag      {sum(p.inventory.values())}   [{T.COIN}]{p.bits}b[/]",
                div,
                f"Hunger   {hearts(p.hunger)}",
                f"Energy   {bar(p.energy, 11, T.ENERGY)}",
                f"Power    {power}",
                div,
                "[dim]out exploring —[/]",
                "[dim]survive the zone[/]",
            ]
        self.stats_w.update("\n".join(lines))

    def on_anim(self):                         # slow tick: idle pet bob
        if self.mode is None and not self.screen_w.fx:
            self.screen_w.advance()
            self.screen_w.paint(self.pet)

    def on_fast(self):                         # fast tick: panel + care-action animation
        if self.mode is not None:
            if hasattr(self.mode, "anim"):
                self.mode.anim()
                self.screen_w.update(self._center(self.mode.text()))
                if isinstance(self.mode, adventurescreen.AdventurePanel):
                    self._status_adventure()
                elif isinstance(self.mode, training.TrainingPanel):
                    self._status_training()
        elif self.screen_w.fx:
            self.screen_w.advance_fx()
            self.screen_w.paint(self.pet)
        if self._dying_fx and not self.screen_w.fx:        # dying beat finished -> memorial
            self._dying_fx = False
            self._open_mode(deathscreen.DeathPanel(self.pet), self._after_death)

    def on_tick(self):
        if self.mode is not None:
            return  # a sub-screen is open -> pause the life-sim (resumes in the main view)
        prev = (self.pet.num, self.pet.stage)
        was_dead = self.pet.dead
        poop0 = self.pet.poop
        self.pet.tick(1.0)
        p = self.pet
        if p.dead and not was_dead:
            self.beep("death")            # death.wav, like DVPet's dying() sound
            self.flash("")
            self.screen_w.start_fx("dying")   # exhausted pose beat, then the memorial
            self._dying_fx = True
        elif (p.num, p.stage) != prev:
            if prev[1] == "Egg":
                self.beep("hatch")
                self.flash(f"[b]{p.name}[/] hatched!")
            else:
                self.beep("evolve")
                self.flash(f"[b]{p.name}![/] evolved to {p.stage}!")
            self.screen_w.start_fx("evolve", old_num=prev[0])
        elif p.poop > poop0:
            self.beep("poop", bell=False)
        # care-need call (classic V-pet nag): alert on onset, then every ~90s
        needs = (not p.dead and p.stage != "Egg" and not p.asleep
                 and (p.hunger == 0 or p.sick or p.poop >= 3 or p.energy <= 0))
        if needs and not self._needs:
            self.beep("alarm")
            self._nag_t = 0.0
        elif needs:
            self._nag_t = getattr(self, "_nag_t", 0.0) + 1.0
            if self._nag_t >= 90:
                self._nag_t = 0.0
                self.beep("alarm")
        self._needs = needs
        self.repaint()

    def flash(self, text):
        self.msg_w.update(text)

    def _do(self, result):
        self.flash(result)
        self.repaint()

    def action_feed(self):
        msg = self.pet.feed()
        if self.pet.anim == "eat":
            self.screen_w.start_fx("eat", "f:0")
            self.beep("eat", bell=False)
        elif "too full" in msg:
            self.screen_w.start_fx("spit", "f:0")
            self.beep("refuse", bell=False)
        self._do(msg)
    def action_train(self):
        reason = self.pet.can_train()
        if reason:
            self._do(reason); return
        self._open_mode(training.TrainingPanel(self.pet), self._after_train)

    def _after_train(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_battle(self):
        reason = self.pet.can_battle()
        if reason:
            self._do(reason); return
        self._open_mode(battlescreen.BattlePanel(self.pet), self._after_battle)

    def _after_battle(self, battle):
        if battle is not None:
            self.flash(battle.reward)
            self.beep("win") if battle.won else self.beep("lose", bell=False)
        self.repaint()

    def action_tournament(self):
        if self.pet.stage in ("Egg", "Fresh", "InTraining"):
            self._do("Too young for the cup."); return
        if self.pet.asleep:
            self._do("zzz... asleep"); return
        self._open_mode(tournamentscreen.TournamentPanel(self.pet), self._after_cup)

    def _after_cup(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_jogress(self):
        reason = jogress.can_jogress(self.pet)
        if reason:
            self._do(reason); return
        self._open_mode(jogressscreen.JogressPanel(self.pet), self._after_jogress)

    def _after_jogress(self, msg):
        if msg:
            self.flash(msg)
            self.beep("jogress")
        self.repaint()

    def action_shop(self):
        self._open_mode(shopscreen.ShopPanel(self.pet), self._after_shop)

    def action_habitat(self):
        self._open_mode(habitatscreen.HabitatPanel(self.pet), self._after_habitat)

    def action_digicore(self):
        self._open_mode(digicorescreen.DigiCorePanel(self.pet), lambda _=None: self.repaint())

    def _after_habitat(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def _after_shop(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_adventure(self):
        if self.pet.stage in ("Egg", "Fresh"):
            self._do("Too young to adventure."); return
        if self.pet.asleep:
            self._do("zzz... asleep"); return
        self._open_mode(adventurescreen.AdventurePanel(self.pet), lambda _=None: self.repaint())

    def action_play(self):
        msg = self.pet.play()
        if self.pet.anim == "play":
            self.screen_w.start_fx("cheer")
            self.beep("happy", bell=False)
        self._do(msg)
    def action_clean(self):
        poop = self.pet.poop
        msg = self.pet.clean()
        if self.pet.anim == "wash":
            self.screen_w.start_fx("clean", poop=poop)
            self.beep("wash", bell=False)
        self._do(msg)
    def action_heal(self):
        msg = self.pet.heal()
        if self.pet.anim == "heal":
            self.screen_w.start_fx("cheer")
            self.beep("happy", bell=False)
        self._do(msg)
    def action_sleep(self): self._do(self.pet.toggle_sleep())
    def action_new(self):
        gen = self.pet.generation + 1
        self._open_mode(eggselectscreen.EggSelectPanel(),
                        lambda et: self._hatch_new(et, gen))

    def _hatch_new(self, egg_type, gen):
        self.pet = Pet.new_egg(generation=gen, egg_type=egg_type)
        persistence.save(self.pet)
        self._do(f"A new egg appeared! (generation {gen})")


def main():
    TuiPetApp().run()


if __name__ == "__main__":
    main()
