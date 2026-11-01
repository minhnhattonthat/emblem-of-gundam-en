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
   **Phase 7 correction:** 357 strings. Six follow binary data with no NUL in between, so the run didn't decode and
   the old scan skipped them: `セーブをしますか？` (0x02073CBC, the save prompt, glued to a pointer table), the save
   warning 0x02073E78, `バックログ`, `バスケットＤ`, `%s %s`, `./EZ_TBL.BIN`. `arm9.strings` now also takes the
   first pointed-at offset inside an undecodable run. Then 359: `jp_left.py` on the built arm9 found
   `ユニットの売却`/`ユニットの購入` at 0x02072150/60, below the old 0x72170 start (pointer table 0x0207207C);
   the region now starts at 0x72150.
   **Writable buffers:** `未設定` x7 (0x020746FC-0x0207475E) and `鳥00` (0x02072814) are RAM buffers the code
   strcpy/strncpy/memsets into and reads as struct fields. Relocating one moved only the default text (the stage-info
   panel went blank). `arm9.BUFFERS` lists them; `relocate` refuses them, so their English must fit in place;
   `tests/test_arm9.py` checks every strcpy/strncpy/memset destination string is listed.
   **Also:** each stage table's type-5 record holds a second copy of the stage name (`bbq.md` §Stage record) that the
   map panel shows; the build fills it from the pool string.
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
- **arm9 strings grow into the ITCM autoload tail** (phase 5, `arm9.relocate`, verified in-game): the arm9 file is
  laid out `[main section][ITCM source][DTCM source][autoload list]`; the autoload list at file 0x78300 holds 12-byte
  entries (RAM address, size, bss):
  `0x01FF8000/0x1160/0` (ITCM) and `0x027E0000/0x60/0xCC0` (DTCM). The module params at file 0xBA0 point at it
  (+0x00 list address, +0x04 list end, then 0x02077140 twice, 0x021A95A0, 0, 0x04017530, footer magic). ITCM is
  32 KiB and the game loads only 0x1160, so **0x6EA0 (28,320) bytes are free** from RAM 0x01FF9160.
  `relocate()` appends the moved strings after the ITCM source, grows that section's size, lets the DTCM source and
  the list slide up (the list must stay 4-aligned), rewrites the params, and points the old 4-byte literals at the new
  address; the old slot is zeroed. A line's worth of strings fits easily; the whole 351-string set as `aN` markers
  takes 1.7 KB. `insert.arm9_edit` uses it for every string that no longer fits in place.
- The 0x4 KiB between 0x770F4 and the main section end is only 0x4C bytes — not free space.
