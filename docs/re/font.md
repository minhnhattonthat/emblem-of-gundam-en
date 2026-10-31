# Fonts and text encoding

## Encoding: Shift-JIS (cp932)
- **verified:** both NFTR fonts declare encoding 2 (Shift-JIS) and their CMAPs map SJIS codes (0x8140...) plus ASCII
  0x20-0x7E and half-width katakana; the strings seen on screen at boot (stage card "オープニングセレモニー") are the
  cp932 bytes in BBQ 0000. Still to do: corrupt-and-boot once the archive repacker exists (phase 3).
- No custom table needed: `tbl/` will hold only control-code notes.

## NFTR fonts (`tools/nftr.py`)
| id | cell | bpp | glyphs | ASCII advance |
|---|---|---|---|---|
| 0336 | 11x11 | 1 | 7111 | 6 px (full-width kana 12 px) |
| 0337 | 9x9 | 1 | 7111 | 5 px (full-width 10 px) |

Both carry a full half-width ASCII set with per-glyph CWDH widths (left, glyph width, advance). Whether the renderer
honours the CWDH advance (a free VWF) or uses a fixed cell is **unknown**: test in the phase 5 marker build. The
ASCII glyphs are crude (W is 5 px); redrawing them is cheap since the fonts are plain 1bpp files in the archive.
