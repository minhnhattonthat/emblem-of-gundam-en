# Text ranges, pointers, free space

## Where the text is
1. **BBQ string tables** (`bbq.md`): 332 archive entries start with `.BBQ1.00`; 328 carry a type-7 string table
   (the 4 that don't — LANDTABLE, COMBATTABLE, CRITICALTABLE, AGLMOVIETABLE — are numeric record tables).
   66,451 strings / 583,558 chars. Referenced by index from the file's own sections; offsets only in the type-7
   index. This is ~99% of the text. Every string's pool is the index's concatenation padded with 0-3 zero bytes to a
   multiple of 4 (checked for all 328), so the table has no hidden bytes.
2. **arm9.bin**: 351 strings, NUL-terminated Shift-JIS, file 0x72170-0x770F4 (RAM 0x02072170-0x020770F4, inside the
   main section which ends at file 0x77140): shop, team-building, save/load, options, turn prompts, level-up and the
   leftover debug menu. **Verified**: each is reached by at least one 4-byte literal pointer in arm9 (ARM literal
   pools, plus small pointer tables for the menus), and no pointer into that region lands inside binary data or on a
   string we don't extract (`tests/test_extract.py`). Pointers are 4-aligned words holding `0x02000000 + file offset`,
   so a string can be moved by rewriting them (needed from phase 5 on; see below).
3. **Graphics** (`graphics.md`): stage cards and a handful of UI screens.
4. Not text: LGA node names (internal: `鳥00`, `百式00`), SDAT, and the 1-2 byte runs the pointer scan hits in
   binary tables (not drawable strings).

## Control codes
None in-band besides `\n` (0x0A), `$L`, `$P01`-style placeholders, `%`/`%d`/`%s`. Line breaks in story text are
separate strings (`bbq.md`). 317 strings are empty and must stay empty.

## Extraction format (phase 4)
- `script/bbq/<ez index>_<archive name>.json`: `{"ez_index": n, "name": "ST01OPEN.BBQ", "strings": [...]}`, one
  string per id, in order. Written by `tools/extract.py`, applied by `tools/insert.py` through `bbq.rebuild()`
  (type 7 is the last section, so a table may grow or shrink freely — only the EZ entry's size changes).
- `script/arm9.json`: `{"strings": [{"at": "0x02072170", "text": "..."}]}`. `arm9.replace()` writes a string back in
  place; it must not grow past its original slot for now.
- An untouched `script/` rebuilds the ROM byte-identically (`tests/test_extract.py`, `tools/build.py`), so the
  insert path can't corrupt what it doesn't touch.

## Free space
- Archive files are rebuilt whole, so any file may grow; EZ_DAT can grow into the ROM's free tail
  (0x03558000-0x03FFFFFF, ~10.6 MB of 0xFF, inside the 64 MiB chip). ndspy rebuilds the FAT.
- arm9 strings: length is the constraint, not space. Growing one means moving it and rewriting its pointer(s); the
  safe home is a new autoload section (ITCM has ~27 KiB free after 0x01FF9160, see `archive.md`), or the 0x4 KiB
  slack between 0x770F4 and the main section end. Decide at phase 5 (VWF/font decision).
