"""Central UI palette - a clean grey pocket-LCD look (no green).

The whole app themes from here: screens import these names instead of
redefining LCD colours locally, so the look changes in ONE place.
"""

# Grey reflective LCD: dark cool-grey ink on a light cool-grey screen.
LCD_ON = "#2b2e31"      # on-pixel / ink
LCD_BG = "#c6c9cc"      # screen (off pixel / panel background)
MID = "#7d8186"         # dim / secondary text + meter track

INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"{MID} on {LCD_BG}"
SEL = f"bold {LCD_BG} on {LCD_ON}"      # selected row (inverted)

ACCENT = "#b04a3a"      # muted clay-red accent (training marker, alerts)
POS = "#3a6ea5"         # positive (habitat thrives) - cool blue, not green
NEG = "#a23b2f"         # negative (habitat suffers)
BORDER = "#7a7e78"      # device bezel (LCD box border)

# Sprite silhouette ink when drawn over a full-colour habitat background.
SIL_DAY = "#2b2e31"     # dark ink by day
SIL_NIGHT = "#e4e7ea"   # pale ink at night (readable on a dimmed screen)

# Screen tint per time of day (creature ink, screen background): greyscale,
# the screen just dims toward night like an LCD backlight fading. No green.
PHASE_PALETTE = {
    "dawn":  ("#33363a", "#d2d5d8"),
    "day":   ("#2b2e31", "#c6c9cc"),
    "dusk":  ("#39352f", "#bdb8b2"),
    "night": ("#9aa0a6", "#23262a"),
}
