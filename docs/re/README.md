# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| `archive.md` | NitroFS, EZ_TBL/EZ_DAT archive, LZ10, file types, arm9 sections | verified (all entries unpack) |
| `bbq.md` | .BBQ1.00 tables: sections, string table, line-per-string text | string table verified; other sections guessed |
| `font.md` | Shift-JIS encoding, NFTR fonts 0336/0337 | encoding verified by font CMAP; renderer widths unknown |
| `text.md` | text ranges (BBQ, arm9), control codes, free space, debug-menu strings | ranges verified; arm9 pointers todo |
| `graphics.md` | graphics-text survey (static sweep of 584 images) | sweep done; tour pending |

Prior work (web search 2026-11-01): no finished English patch; only a GBAtemp request thread and an old GameFAQs
menu-translation post (gamefaqs board 943464, topic 42918861). Nothing to build on.

Tools: `tools/fsls.py` (NitroFS list/unpack), `tools/ez.py unpack` (archive -> work/ez), `tools/bbq.py`,
`tools/nftr.py`, `tools/nitro2d.py survey` (graphics sheets).
