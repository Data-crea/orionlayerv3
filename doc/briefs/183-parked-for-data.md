# Work order 183 — parked for Data

Ordered as the order asks: 1. the proposed decision, 2. new open fixes,
3. everything else. Every item names the default this run continued with.

## 1. Proposed decision (number left free for you)

> **Players skip the original intro; the engine window stays hidden from
> the start.** A player starts the game with `python play.py`, which starts
> orion2re through the same `tools/engine_start.start` the live tools use:
> the original's logos are ended by one key to the engine's own window
> (the original's own skip, jim.cpp:59-61) and the intro is never played
> (jim.cpp:150-152), so nothing of it is seen or heard, and OrionLayer
> opens in the HD main menu without a key. The engine's window is created
> hidden and never shown (open fix 41, applied by work order 183), so the
> player sees only OrionLayer's window; a hidden window presents without
> VSync. Closing OrionLayer stops the engine it started. Measured: with the
> key the engine plays nothing before the main menu's music, which begins
> after READY; without it, 108 s of intro sound from 5.0 s on
> (`doc/briefs/183-progress.md`, Part 2). Held by smoke checks 090r (fix 41
> required and documented) and 090v (the player's start).

**Default this run continued with:** built and documented as if decided;
the decision's number and its place in the fundament are yours.

## 2. New open fixes

**None.** The measurement found no intro audio once the key is sent, so
no engine change was needed for the sound, and none was written.

One engine change was considered and NOT written, for the record: an
engine switch that skips the intro without a key (the unused
`MOX2::_skip_intro`, mox2.cpp:301). It would make even a by-hand start
silent (see 3.3). **Default:** not written — `play.py` covers the player,
and the order allows only necessary engine changes.

## 3. Everything else

1. **Your system stores orion2re's sound MUTED at 0 %.** WirePlumber
   remembers each application's volume, and
   `~/.local/state/wireplumber/stream-properties` holds
   `Output/Audio:application.name:orion2re` with `"mute":true` and both
   channels at 0.0. So today you hear NOTHING from the engine — no intro,
   but no music and no sound effects either, whichever way you start it.
   No session set it (the only `pactl`/`wpctl` calls in any transcript are
   this run's measurement). If it is not what you want: GNOME Settings →
   Sound → Volume Levels → the orion2re row, while the game runs, or
   `wpctl set-mute <id> 0` and `wpctl set-volume <id> 1.0` on its stream.
   **Default:** left exactly as it is; this run measured under another
   stream name so as not to touch it.
2. **Your desktop launchers start nothing.** `OrionLayer_Start.desktop`
   (on the desktop and in `~/.local/share/applications/`, both 3 August)
   run `cd ~/orionlayer && ./launcher.sh edit main_menu` — that folder no
   longer exists. A line that would start the game now:
   `Exec=alacritty -e bash -c "cd ~/orionlayerv3 && python play.py"`
   (`OrionLayer_Stop.desktop` is not needed any more: closing OrionLayer
   stops the engine). **Default:** not touched — they are your files,
   outside the tree.
3. **Started by hand, the intro plays out, with its sound.** README keeps
   the two-terminal way and says so: the key would have to go to the
   engine's window, which fix 41 keeps hidden, so nothing can press it —
   113 s of logos and intro (silent on your machine while 3.1 holds).
   **Default:** `play.py` is the documented start; the by-hand way stays
   for debugging.
4. **`play.py` needs `xdotool`** for the key (on another machine too); it
   warns at the start if it is missing. **Default:** a warning, no fallback.
5. **Native crashes today, in several programs.** Three smoke runs of this
   order ended with exit 139 — segfaults inside CPython 3.14.7 (`ast`,
   check 059) and numpy (`_multiarray_umath`, checks 006f and a HUD block),
   each in code this order did not touch; each rerun was green.
   `coredumpctl` also lists pairs of small python3.14 crashes during green
   runs all day (child processes, 182's session too), Borderlands' Proton
   preloader at 17:21 and a Chromium renderer at 14:23. The cause is not
   established here. **Default:** recorded, nothing changed; every gate
   run that counted was a clean exit 0. If it keeps happening, a memory
   test is the cheap next step.
