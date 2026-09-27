"""The Ship Designer's own words, by a stable key — work order 185, decision
73 (`core/modtexts`): replaceable from the player's mod folder
(`texts/ship_design/<rest>.txt`).

Only OrionLayer's words are here — the title, the button words and the
pickers' headlines the original paints into DESIGN.LBX's art ("own"; the
pickers' in `screens/design_box/layout.json`). Every other word on the page
is the game's, read from the player's own extracted files by the original's
ids (HESTRNGS, TECHNAME, TECHDESC, KENTEXT), and is never written into the
tree.
"""
TEXTS = {
    "ship_design.title": ("Ship Design", "own"),
    "ship_design.button.clear": ("CLEAR", "own"),
    "ship_design.button.cancel": ("CANCEL", "own"),
    "ship_design.button.build": ("BUILD", "own"),
    "ship_design.button.accept": ("ACCEPT", "own"),
    # The shield / computer box wears the special box's headline art in
    # the original (the same top sprite); the word is the one it shows.
    "ship_design.box.generic": ("Select Special System", "own"),
    "ship_design.box.weapon": ("Select Weapon System", "own"),
    "ship_design.box.special": ("Select Special System", "own"),
}
