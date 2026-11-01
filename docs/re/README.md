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
| `font.md` | Shift-JIS encoding, NFTR fonts 0336/0337, the CWDH advance rule (VWF) | encoding verified by font CMAP; advance rule measured in-game (phase 5) |
| `text.md` | text ranges (BBQ, arm9), pointers, script/ format, control codes, free space, growing arm9 strings into the ITCM tail | verified (roundtrip + coverage + relocation tests, corrupt-and-boot shots) |
| `debug.md` | script engine (file ids, current script), developer menu + stage jump, map-menu debug item; warp tool | verified (291/291 warps from cold boot) |
| `graphics.md` | graphics-text survey (static sweep of 584 images) | sweep done; tour pending |
| `width.md` | measured text-box budgets, marker classes, text-layout facts | zero unresolved width lines |
| `width-callers.md` | exact native/BBQ render destinations, record-derived exclusions and byte transport caps | reviewed mappings |
| `native-widths.md` | native buffers, runtime formats, measured UI families and code fixes | phase7 evidence |
| `native-domains.md` | complete accessor domains and exact dormant-field exclusions | independent read-only audit |
| `retirement-route.md` | guarded normal-purchase retirement capture | both headings measured cold |

Prior work (web search 2026-11-01): no finished English patch; only a GBAtemp request thread and an old GameFAQs
menu-translation post (gamefaqs board 943464, topic 42918861). Nothing to build on.

Tools: `tools/fsls.py` (NitroFS list/unpack), `tools/ez.py unpack` (archive -> work/ez), `tools/bbq.py` (sections,
string table, `rebuild`), `tools/bbqstr.py` (all strings of a BBQ), `tools/arm9.py` (arm9 strings, pointers, in-place
replace, ITCM relocation), `tools/extract.py` (ROM -> script/, `--check` for holes), `tools/insert.py` (script/ ->
patches), `tools/font.py` (VWF advance table + width model, `--sheet`), `tools/mark.py` (marker/stress/torture ROMs,
`--report` for the string classes), `tools/textband.py` (measure a text line in a shot),
`tools/vmdump.py` (script bytecode words), `tools/debug/ezlog.lua`
(probe: log EZ loads + callers, needs --debugger),
`tools/nftr.py`, `tools/nitro2d.py survey` (graphics sheets).
