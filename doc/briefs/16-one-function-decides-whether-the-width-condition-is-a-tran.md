One function decides whether the width condition is a transcription or
a deviation.

_Squeeze_Print_Paragraph_ loops on max_height >= height only, and
fmtpara.cpp offers Get_Formatted_Paragraph_Max_Width_ right beside the
height function - which the squeeze does not call. So either
_Print_Formatted_Paragraph_ breaks inside an over-wide token, in which
case height alone is sufficient and our width condition transcribes
the same guarantee by other means; or it breaks only at spaces, in
which case a 15-glyph ship design overflows 85px in the original too
and our refusal to overflow is a marked deviation.

Read _Print_Formatted_Paragraph_ (fmtpara.cpp) and settle it. Mark
accordingly.

Two smaller things:
- The buy control deviates twice: the label "Buy" is ours, and so is
  drawing text where the original draws a sprite (E_Strings_(12) empty,
  colsum.cpp:302). Name both in the marker.
- colsum.cpp:621 passes height 0x16 = 22 into a 31px row, so the
  original budgets two lines in that box itself. Record that: the
  two-line column is the same place, not just the same technique.