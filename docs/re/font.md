# Fonts, text encoding and the VWF (phase 5)

## Encoding: Shift-JIS (cp932)
- **verified:** both NFTR fonts declare encoding 2 (Shift-JIS) and their CMAPs map SJIS codes (0x8140...) plus ASCII
  0x20-0x7E and half-width katakana; the strings seen on screen at boot (stage card "オープニングセレモニー") are the
  cp932 bytes in BBQ 0000. No custom table needed: `tbl/` holds only control-code notes.

## NFTR fonts (`tools/nftr.py`, `tools/font.py`)
| id | cell | bpp | glyphs | where it draws | ASCII advance before | after VWF |
|---|---|---|---|---|---|---|
| 0336 | 11x11 | 1 | 7111 | dialogue, stage-card narration, menus, footers (11 px tall) | 6 px | ink width |
| 0337 | 9x9 | 1 | 7111 | the small labels on the lower screen (9 px tall) | 5 px | ink width |

Both fonts carry a full half-width ASCII set, ink 5 px wide and 10 px tall (lowercase with descenders, 4 px cap
width in 0337), with per-glyph CWDH entries `(left, width, advance)`.

## The renderer honours the CWDH advance: VWF is free (measured in-game, phase 5)
The advance of a glyph's CWDH entry is what the renderer moves the pen by, **plus 1 px**:

- default ASCII (advance 6) -> 7 px pitch, measured on the narration line, the chart footer and the dev menu;
- a test font with 'i' set to advance 2 -> 3 px pitch, 'W' set to 10 -> 11 px pitch (shots
  `work/qa/retry2_v_adv336/`, `work/qa/adv336/chart/final.png`);
- full-width kana (advance 12) -> 13 px pitch.

It ignores the CWDH *left/width* fields and there is no kerning. The same table serves both fonts (0337 measured the
same way).

`tools/font.py` builds the table the build installs: every printable ASCII glyph's advance becomes its **ink width**
(the renderer's own +1 px is the letter gap), the space glyph gets 3 (-> 4 px), and kana and everything else are left
alone. All printable ASCII goes from 665 px to 508 px (76 %) in 0336 and 570 -> 439 in 0337, so a line holds ~25 %
more English characters. The bitmaps are unchanged; they are a legible 5x10 condensed design.

Validated in-game with the glyph torture line (`tools/mark.py --torture 85 1`, shot `work/qa/torture/`): every
printable ASCII glyph draws, and the measured ink extent matches `font.width()` to the pixel (e.g. 30 digits = 171 px,
first ink at pen + 0, last ink ends at pen + 170). `tests/test_font.py` pins the advance table and the width model.

## Text layout facts the marker build proved
- A string is one line. `\n` inside a string moves the pen down one line (285 strings use it, e.g. the arm9
  `%sを\n購入しました。`); the following strings then start one line lower.
- Drawing **clips** at the box edge, it does not wrap (a 40-digit line shows ~32 digits, then stops).
- Each string is drawn with its own background clear: a 4th string drawn over a 3-line box erases the tail of the
  3rd line (found while testing; see `work/marker/torture.nds`).

## Font licensing
Both NFTRs are the game's own; the VWF change only rewrites their advance table, no new font files ship, so
`docs/fonts.md` stays unchanged (no third-party font is added).
