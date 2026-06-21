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
from . import persistence
from . import jogressscreen
from . import jogress
from . import tournamentscreen
from .pet import Pet
from .render import render_screen

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
SCREEN_COLS, SCREEN_ROWS = 26, 12
SPRITE_W = 16                                   # native creature sprite width
WALK_RANGE = (SCREEN_COLS - SPRITE_W) // 2      # how far the pet paces from centre


def hearts(n, total=4):
    return "[red]" + "●" * n + "[/red]" + "[dim]" + "○" * (total - n) + "[/dim]"


def bar(v, width=12, color="green"):
    fill = round(v / 100 * width)
    return f"[{color}]" + "█" * fill + "[/]" + "[dim]" + "─" * (width - fill) + "[/dim]"


GRAVESTONE = [
    "......1111......", "....11111111....", "...1111111111...",
    "..111111111111..", ".11111111111111.", ".111111111111111",
    ".111111..1111111", ".11111....111111", ".111111..1111111",
    ".111111..1111111", ".111111111111111", ".11111111111111.",
    ".11111111111111.", ".11111111111111.", "1111111111111111",
    "1111111111111111",
]

SUN = ["01110", "11111", "11111", "11111", "01110"]
MOON = ["01110", "11100", "11000", "11100", "01110"]

# LCD palette per time of day (creature ink, screen background)
PHASE_PALETTE = {
    "dawn":  ("#3a5a2a", "#c0d89b"),   # pale morning green
    "day":   ("#0f380f", "#9bbc0f"),   # classic bright Game Boy green
    "dusk":  ("#5a2d00", "#e0913a"),   # warm amber sunset
    "night": ("#6f8f4f", "#0d1f1a"),   # dim glow on near-black
}

WEATHER_GLYPH = {
    "Clear": "", "Cloudy": chr(0x2601), "Drizzling": chr(0x2602),
    "Raining": chr(0x2602), "HeavyRain": chr(0x2614),
    "LightSnow": chr(0x2744), "Snowing": chr(0x2744), "HeavySnow": chr(0x2744),
}
_RAIN = {"Drizzling", "Raining", "HeavyRain"}
_SNOW = {"LightSnow", "Snowing", "HeavySnow"}
_PRECIP_N = {"Drizzling": 5, "LightSnow": 6, "Raining": 11, "Snowing": 10,
             "HeavyRain": 18, "HeavySnow": 16}
CLOUD = ["0011100", "0111111", "1111111"]

_K = "b cyan"
KEYS = (
    f"[{_K}]f[/] feed   [{_K}]p[/] play   [{_K}]c[/] clean   [{_K}]h[/] heal   [{_K}]s[/] sleep\n"
    f"[{_K}]t[/] train  [{_K}]b[/] battle  [{_K}]a[/] adventure  [{_K}]u[/] cup  [{_K}]j[/] jogress\n"
    f"[{_K}]o[/] shop   [{_K}]e[/] habitat  [{_K}]d[/] data   [{_K}]n[/] new   [{_K}]q[/] quit"
)


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
    if pet.poop and pm:                                   # poop piles on the floor
        pw, ph = len(pm[0]), len(pm)
        for i in range(min(pet.poop, 3)):
            ox = cols - pw - 1 - i * (pw + 1)
            if ox > cols // 2:
                pts += _blit(pm, ox, px_h - ph)
    if pet.num == -1:
        return pts
    if pet.asleep and E.get("zzz"):                       # Zzz above a sleeper
        z = E["zzz"][frame_i % len(E["zzz"])]
        pts += _blit(z, cols // 2 + 5, 1)
    elif pet.status_word() == "freezing" and E.get("frozen"):   # frost overlay
        fr = E["frozen"][0]
        pts += _blit(fr, (cols - len(fr[0])) // 2, px_h - len(fr) - 2)
    elif pet.anim == "eat":                               # food shrinks as it eats
        from .render import downsample
        food = data.load_icons().get("f:40")
        if food:
            fb = downsample(food[min(frame_i % 4, len(food) - 1)], 3)
            if fb:
                pts += _blit(fb, cols // 2 - len(fb[0]) - 2, px_h - len(fb) - 5)
    elif pet.anim == "wash" and E.get("wash"):            # soapy splash while washing
        w = E["wash"]
        pts += _blit([r[:9] for r in w[0][:10]], 1, px_h - 13)
    emo = ("happy" if pet.anim in ("happy", "play") else
           "unhappy" if pet.anim in ("sad", "refuse") else
           "depressed" if pet.anim == "angry" else None)
    if emo and E.get(emo):                                # emote bubble on reactions
        ef = E[emo][frame_i % len(E[emo])]
        pts += _blit(ef, cols // 2 - len(ef[0]) // 2, 1)
    elif (pet.anim in ("idle", "walk") and frame_i % 2 == 0 and E.get("attention")
          and (pet.hunger == 0 or pet.sick or pet.poop >= 3 or pet.energy <= 0)):
        pts += _blit(E["attention"][0], cols // 2 + 7, 1)  # '!' call for care
    return pts


class Screen(Static):
    """The animated LCD screen."""
    def on_mount(self):
        self.frame_i = 0
        self.walk_x = 0
        self.walk_dir = 1

    def paint(self, pet: Pet):
        on, bg = PHASE_PALETTE.get(pet.day_phase, (LCD_ON, LCD_BG))
        corner = SUN if pet.is_daytime else MOON
        w = pet.weather
        if w in _RAIN:
            bg = _scale_hex(bg, 0.78)          # overcast dims the screen
        elif w in _SNOW:
            bg = _scale_hex(bg, 0.85)
        elif w == "Cloudy":
            bg = _scale_hex(bg, 0.9)
        overlay = (_weather_overlay(w, self.frame_i, SCREEN_COLS, SCREEN_ROWS * 2)
                   + _effect_overlay(pet, self.frame_i, SCREEN_COLS, SCREEN_ROWS * 2))
        if pet.dead:                           # a grave marker
            self.update(render_screen(GRAVESTONE, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                      corner=corner, overlay=overlay))
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
        if pet.is_geriatric and pet.anim in ("idle", "walk"):
            rows = rec["frames"][9] or first   # elderly: stand still in the tired pose
        elif pet.anim in ("idle", "walk") and pet.num != -1:
            # pace back and forth, facing the way it moves
            xshift = max(-WALK_RANGE, min(WALK_RANGE, self.walk_x))
            mirror = self.walk_dir > 0         # mirror=True faces right (sprites face left by default)
        else:
            mirror = pet.anim in data.MIRROR_ROLES and self.frame_i % 2 == 1
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  mirror=mirror, xshift=xshift, corner=corner, overlay=overlay))

    def advance(self):
        self.frame_i += 1
        self.walk_x += self.walk_dir
        if abs(self.walk_x) >= WALK_RANGE:     # reached an edge: turn around
            self.walk_dir = -self.walk_dir
            self.walk_x = max(-WALK_RANGE, min(WALK_RANGE, self.walk_x))


class Stats(Static):
    def paint(self, pet: Pet):
        deco = []
        if pet.asleep: deco.append("[blue]Zzz[/]")
        if pet.sick: deco.append("[red]+ sick[/]")
        if pet.poop: deco.append(f"[yellow]~poop x{pet.poop}[/]")
        mins, secs = divmod(int(pet.age_seconds), 60)
        picon = chr(0x2600) if pet.is_daytime else chr(0x263E)
        wglyph = WEATHER_GLYPH.get(pet.weather, "")
        env = (f"[yellow]{picon}[/] [dim]{pet.day_phase}[/dim]   "
               f"{wglyph} [dim]{pet.weather} {int(pet.temp)}\u00b0[/dim]")
        aff = pet._affinity()
        amark = ("[green]" + chr(0x2665) + "[/]" if aff > 0
                 else ("[red]" + chr(0x2716) + "[/]" if aff < 0 else "[dim]·[/dim]"))
        xm = " [b magenta]X[/]" if pet.x_antibody != "None" else ""
        lines = [
            f"[b]{pet.name}[/b]{xm}  [dim]gen {pet.generation}[/dim]",
            f"[dim]{pet.stage} · {pet.attribute}[/dim]",
            f"[dim]@{pet.habitat_obj()['name']}[/dim] {amark} [dim]{pet.season}[/dim]",
            env,
            f"Hunger  {hearts(pet.hunger)}",
            f"Effort  {hearts(pet.strength)}",
            f"Energy  {bar(pet.energy, color='cyan')}",
            f"Mood    {bar(pet.mood, color='magenta')}",
            "",
            f"Weight  {pet.weight}g",
            f"Power   [green]V{pet.vaccine}[/] [cyan]D{pet.data_power}[/] [magenta]Vi{pet.virus}[/]",
            f"Battle  {pet.wins}W/{pet.battles}   [yellow]{pet.bits}b[/]",
            f"Trophy  [yellow]{chr(0x25CF) * min(pet.trophies, 8)}[/] {pet.trophies}" if pet.trophies else "",
            f"Age     {mins}m{secs:02d}s",
            f"Life    {bar(max(0, int((pet.lifespan - pet.age_seconds) / max(1, pet.lifespan) * 100)), color=('red' if pet.is_geriatric else 'green'))}",
            f"Care x  {pet.care_mistakes}",
            "",
            f"State: [b]{pet.status_word()}[/b]",
            "  ".join(deco),
        ]
        self.update("\n".join(lines))


class TuiPetApp(App):
    CSS = """
    Screen { align: center middle; }
    #wrap { width: auto; height: auto; }
    #lcd {
        border: heavy #5a7a1a; padding: 0 1; background: #9bbc0f;
        width: 30; height: 14;
    }
    #stats { border: round #444; padding: 0 1; width: 30; height: 21; margin-left: 1; }
    #msg { height: 1; color: $text-muted; margin-top: 1; }
    #keys { height: 3; color: $text-muted; margin-top: 1; }
    """
    BINDINGS = [
        ("f", "feed", "Feed"), ("t", "train", "Train"), ("b", "battle", "Battle"),
        ("p", "play", "Play"), ("c", "clean", "Clean"), ("h", "heal", "Heal"),
        ("a", "adventure", "Adventure"), ("o", "shop", "Shop"), ("e", "habitat", "Habitat"),
        ("d", "digicore", "DigiCore"),
        ("j", "jogress", "Jogress"), ("u", "tournament", "Cup"),
        ("s", "sleep", "Sleep"), ("n", "new", "New pet"), ("q", "quit", "Quit"),
    ]

    def __init__(self, pet: Pet | None = None):
        super().__init__()
        self._welcome = "Welcome! Raise your pet."
        if pet is None:
            loaded, msg = persistence.load()
            if loaded is not None:
                pet, self._welcome = loaded, (msg or "Welcome back!")
        self.pet = pet or Pet.new_egg()

    def compose(self) -> ComposeResult:
        with Vertical(id="wrap"):
            with Horizontal():
                yield Screen(id="lcd")
                yield Stats(id="stats")
            yield Static("Welcome! Raise your pet.", id="msg")
            yield Static(KEYS, id="keys")

    def on_mount(self):
        self.screen_w = self.query_one("#lcd", Screen)
        self.stats_w = self.query_one("#stats", Stats)
        self.msg_w = self.query_one("#msg", Static)
        self.msg_w.update(self._welcome)
        self.repaint()
        self.set_interval(0.45, self.on_anim)
        self.set_interval(1.0, self.on_tick)
        self.set_interval(10.0, self.autosave)

    def autosave(self):
        persistence.save(self.pet)

    def on_unmount(self):
        persistence.save(self.pet)

    def action_quit(self):
        persistence.save(self.pet)
        self.exit()

    def repaint(self):
        self.screen_w.paint(self.pet)
        self.stats_w.paint(self.pet)

    def on_anim(self):
        self.screen_w.advance()
        self.screen_w.paint(self.pet)

    def on_tick(self):
        prev = (self.pet.num, self.pet.stage)
        was_dead = self.pet.dead
        self.pet.tick(1.0)
        if self.pet.dead and not was_dead:
            mins = int(self.pet.age_seconds) // 60
            self.flash(f"[b red]{self.pet.name} passed away[/] (gen {self.pet.generation}, lived {mins}m). Press N for a new egg.")
        elif (self.pet.num, self.pet.stage) != prev:
            self.flash(f"[b green]{self.pet.name}![/] evolved to {self.pet.stage}!")
        self.repaint()

    def flash(self, text):
        self.msg_w.update(text)

    def _do(self, result):
        self.flash(result)
        self.repaint()

    def action_feed(self): self._do(self.pet.feed())
    def action_train(self):
        reason = self.pet.can_train()
        if reason:
            self._do(reason); return
        self.push_screen(training.TrainingScreen(self.pet), self._after_train)

    def _after_train(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_battle(self):
        reason = self.pet.can_battle()
        if reason:
            self._do(reason); return
        self.push_screen(battlescreen.BattleScreen(self.pet), self._after_battle)

    def _after_battle(self, battle):
        if battle is not None:
            self.flash(battle.reward)
        self.repaint()

    def action_tournament(self):
        if self.pet.stage in ("Egg", "Fresh", "InTraining"):
            self._do("Too young for the cup."); return
        if self.pet.asleep:
            self._do("zzz... asleep"); return
        self.push_screen(tournamentscreen.TournamentScreen(self.pet), self._after_cup)

    def _after_cup(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_jogress(self):
        reason = jogress.can_jogress(self.pet)
        if reason:
            self._do(reason); return
        self.push_screen(jogressscreen.JogressScreen(self.pet), self._after_jogress)

    def _after_jogress(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_shop(self):
        self.push_screen(shopscreen.ShopScreen(self.pet), self._after_shop)

    def action_habitat(self):
        self.push_screen(habitatscreen.HabitatScreen(self.pet), self._after_habitat)

    def action_digicore(self):
        self.push_screen(digicorescreen.DigiCoreScreen(self.pet), lambda _=None: self.repaint())

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
        self.push_screen(adventurescreen.AdventureScreen(self.pet), lambda _=None: self.repaint())

    def action_play(self): self._do(self.pet.play())
    def action_clean(self): self._do(self.pet.clean())
    def action_heal(self): self._do(self.pet.heal())
    def action_sleep(self): self._do(self.pet.toggle_sleep())
    def action_new(self):
        gen = self.pet.generation + 1
        self.pet = Pet.new_egg(generation=gen)
        persistence.save(self.pet)
        self._do(f"A new egg appeared! (generation {gen})")


def main():
    TuiPetApp().run()


if __name__ == "__main__":
    main()
