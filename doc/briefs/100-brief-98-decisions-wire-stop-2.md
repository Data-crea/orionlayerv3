Brief 98, Data's decisions: (a) help always wins, the right-click pick
discard is removed and _hd_extension_cancel updated (drop any note that
no longer fires). Column regions merge each column's heading plate. 520
stays unreachable with its note. Wire Stop 2: right click walks the table
in order on the existing popup, smoke test green, one right-click popup
screenshot at 1080p beside the native help box. No push.

The popup and the right-click walk are the shared ones from
core/screenhelp.py / helppopup.py — the same the galaxy map uses. Do not
build a colony-specific popup; the colony screen only supplies help.json.
