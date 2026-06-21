"""DVPet TUI — a terminal virtual pet rendered with halfblock sprites."""
from __future__ import annotations
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Footer
from textual.reactive import reactive

from . import data
from . import egg as egg_mod
from . import training
from . import battlescreen
from . import adventurescreen
from . import shopscreen
from . import persistence
from . import jogressscreen
from . import jogress
from . import tournamentscreen
from .pet import Pet
from .render import render_screen

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
SCREEN_COLS, SCREEN_ROWS = 26, 12


def hearts(n, total=4):
    return "[red]" + "●" * n + "[/red]" + "[dim]" + "○" * (total - n) + "[/dim]"


def bar(v, width=12, color="green"):
    fill = round(v / 100 * width)
    return f"[{color}]" + "█" * fill + "[/]" + "[dim]" + "─" * (width - fill) + "[/dim]"


class Screen(Static):
    """The animated LCD screen."""
    def on_mount(self):
        self.frame_i = 0
        self.walk_x = 0
        self.walk_dir = 1

    def paint(self, pet: Pet):
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
        if pet.anim in ("idle", "walk") and pet.num != -1:
            rows = first                       # whole frame-0 sprite, no bob flicker
            sw = max(len(r) for r in rows)
            bound = max(0, (SCREEN_COLS - sw) // 2)
            xshift = max(-bound, min(bound, self.walk_x))
            mirror = self.walk_dir > 0         # mirror=True faces right (battle-consistent)
        else:
            xshift = 0
            mirror = pet.anim in data.MIRROR_ROLES and self.frame_i % 2 == 1
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, LCD_ON, LCD_BG,
                                  mirror=mirror, xshift=xshift))

    def advance(self):
        self.frame_i += 1
        self.walk_x += self.walk_dir
        if abs(self.walk_x) >= 5:
            self.walk_dir = -self.walk_dir
            self.walk_x = max(-5, min(5, self.walk_x))


class Stats(Static):
    def paint(self, pet: Pet):
        deco = []
        if pet.asleep: deco.append("[blue]Zzz[/]")
        if pet.sick: deco.append("[red]+ sick[/]")
        if pet.poop: deco.append(f"[yellow]~poop x{pet.poop}[/]")
        mins, secs = divmod(int(pet.age_seconds), 60)
        lines = [
            f"[b]{pet.name}[/b]",
            f"[dim]{pet.stage} · {pet.attribute}[/dim]",
            "",
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
        width: 28; height: 14;
    }
    #stats { border: round #444; padding: 0 1; width: 30; height: 14; margin-left: 1; }
    #msg { height: 1; color: $text-muted; margin-top: 1; }
    """
    BINDINGS = [
        ("f", "feed", "Feed"), ("t", "train", "Train"), ("b", "battle", "Battle"),
        ("p", "play", "Play"), ("c", "clean", "Clean"), ("h", "heal", "Heal"),
        ("a", "adventure", "Adventure"), ("o", "shop", "Shop"),
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
        yield Footer()

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
        self.pet.tick(1.0)
        if (self.pet.num, self.pet.stage) != prev:
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
        self.pet = Pet.new_egg()
        persistence.save(self.pet)
        self._do("A new egg appeared!")


def main():
    TuiPetApp().run()


if __name__ == "__main__":
    main()
