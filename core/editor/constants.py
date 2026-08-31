"""Editor constants — colors, field type names, help text."""

H_REF = 8
G_REF = 12
C_SEL = (255, 220, 50)
C_GLO = (50, 200, 255)
C_GLO_ACT = (255, 100, 50)
C_OUT = (100, 120, 160)
C_IBG = (0, 0, 0, 180)
C_ITX = (200, 210, 230)
C_ASN = (50, 255, 50)
C_FTX = (170, 180, 200)
C_HELP_BG = (8, 12, 24, 230)
C_HELP_KEY = (255, 220, 80)
C_HELP_TXT = (180, 190, 210)
C_HELP_HDR = (100, 200, 255)
FIELD_TYPES = {0: "Button", 1: "Radio", 7: "Click", 8: "Dynamic",
               12: "MapArea", 13: "Sidebar"}
GLOW_KEYS = ["tl", "tr", "bl", "br"]

HELP_SECTIONS = [
    ("General", [
        ("F5", "Toggle editor on/off"),
        ("H", "Toggle this help"),
        ("Ctrl+S / F2", "Save boxes.json"),
        ("Esc", "Deselect / close panel"),
    ]),
    ("Create & Delete", [
        ("Ctrl+N", "New button at cursor"),
        ("Ctrl+I", "New inner panel at cursor"),
        ("Del", "Delete selected box"),
    ]),
    ("Move & Resize", [
        ("Click+Drag", "Move selected box"),
        ("Shift+Click", "Cycle overlapping boxes"),
        ("Corner/Edge Drag", "Resize box"),
        ("Arrow Keys", "Nudge 1px (Shift: 5px)"),
        ("Alt+Arrow", "Move content inside box"),
    ]),
    ("View", [
        ("Tab", "Field list"),
    ]),
    # The ping is listed here because the help sheet is where anyone
    # looks for "which key does what", but it is NOT an editor
    # function: it works with the editor closed and is the one key on
    # the galaxy map that is not the game's own (see
    # screens/galaxy_map/ping.py — an invention, marked as such).
    ("Galaxy Map (no editor needed)", [
        ("S", "Star field on/off (editor only)"),
        ("Pos1 / Home", "Ping own home system for ~3 s"),
    ]),
    ("Font & Scroll", [
        ("Ctrl+Scroll", "Change font scale"),
    ]),
    ("Image box (style: pannable)", [
        ("Scroll", "Zoom in/out"),
        ("Shift+Scroll / Alt+Scroll", "Pan vertical / horizontal"),
        ("Right-Drag", "Pan with the mouse"),
    ]),
    ("Portrait (select race_grid)", [
        ("Scroll on portrait", "Zoom in/out"),
        ("Shift+Scroll", "Pan vertical"),
        ("Alt+Scroll", "Pan horizontal"),
    ]),
    ("Buttons", [
        ("G", "Cycle glow corner (tl/tr/bl/br)"),
        ("R", "Rotate glow 90 degrees"),
        ("Arrows (glow)", "Nudge glow offset"),
    ]),
    ("Fields", [
        ("Tab", "Show/hide field list"),
        ("Click field", "Assign to selected box"),
    ]),
]
