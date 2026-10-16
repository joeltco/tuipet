"""Trailer title card: a black screen with big centred block-letter text.
Usage: card.py "HEADLINE" ["subline"]   (holds until Ctrl+C, no shell prompt)"""
import shutil
import sys
import time

import pyfiglet
from rich.console import Console
from rich.text import Text

cols, rows = shutil.get_terminal_size()
c = Console()


def fig(text, font):
    return pyfiglet.figlet_format(text, font=font, width=999).rstrip("\n")


def widest(art):
    return max(len(r) for r in art.split("\n"))


def wrap(text, font):
    """Greedy word-wrap so every figlet line fits the terminal width."""
    lines, cur = [], ""
    words = []
    for word in text.split():             # an unbreakable URL breaks after its "/"
        while widest(fig(word, font)) > cols - 2 and "/" in word[1:]:
            i = word.index("/", 1)
            words.append(word[:i])
            word = word[i:]
        words.append(word)
    for word in words:
        trial = (cur + " " + word).strip()
        if widest(fig(trial, font)) <= cols - 2 or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return [fig(l, font) for l in lines if l]


def block(art):
    """Centre a figlet block AS A BLOCK -- per-row centring shifts rows of
    different lengths against each other and scrambles the letters."""
    rs = art.split("\n")
    w = max(len(r) for r in rs)
    left = max(0, (cols - w) // 2)
    return "\n".join(" " * left + r.ljust(w) for r in rs)


head = "\n".join(block(a) for a in wrap(sys.argv[1].upper(), "ansi_shadow"))
sub = ""
if len(sys.argv) > 2 and sys.argv[2]:
    # a SOLID block font reads at GIF size (the outlined "small" smeared)
    sub = "\n".join(block(a) for a in wrap(sys.argv[2].upper(), "ansi_regular"))

n = len(head.split("\n")) + (len(sub.split("\n")) + 1 if sub else 0)
c.clear()
c.print("\n" * max(0, (rows - n) // 2), end="")
c.print(Text(head, style="bold #e8423f"), no_wrap=True, overflow="crop")
if sub:
    c.print()
    c.print(Text(sub, style="bold #f2f2f2"), no_wrap=True, overflow="crop")
sys.stdout.write("\033[?25l")           # hide the cursor for the hold
sys.stdout.flush()
try:
    time.sleep(120)                       # hold the card until the tape's Ctrl+C
except KeyboardInterrupt:
    pass
sys.stdout.write("\033[?25h")
