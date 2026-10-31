# ROM layout and the EZ archive

Dump: YEGJ, 64 MiB cartridge, ROM data used up to 0x03558000 (header 0x80), rest 0xFF.

## NitroFS (verified: ndspy listing, `tools/fsls.py`)
Only three files:

| id | path | size | what |
|---|---|---|---|
| 0 | `EZ_DAT.BIN` | 51,658,004 | "EZP\0" packed data, every game asset |
| 1 | `EZ_TBL.BIN` | 50,240 | "EZT\0" index into EZ_DAT |
| 2 | `SOUND/sound_data.sdat` | 3,554,304 | SDAT, no text |

No ARM9 overlays. arm9.bin is 0x78318 bytes, uncompressed (strings readable), RAM 0x02000000, entry 0x02000800.
Autoload sections (ndspy MainCodeFile): main 0x02000000 len 0x77140; ITCM 0x01FF8000 len 0x1160 (32 KiB ITCM, so ~27 KiB
free for hook code, see the skill's platform-nds.md; **guess** until the tail is checked zero at runtime); DTCM 0x027E0000 len 0x60 + bss 0xCC0.

## EZ_TBL.BIN (verified: every entry decompresses, offsets monotonic, `tools/ez.py unpack`)
- 0x00 "EZT\0", 0x04 u32 0x07D70904 (date 2007-09-04?), 0x08 u32 0x000C2112, 0x0C u32 0x10, then 0x10..0x93 a small
  header of counts/offsets (not yet needed; **guess**: 16 directory groups).
- 0x94: 4174 entries of 12 bytes: `u32 key, u32 offset in EZ_DAT, u32 (flags << 24) | unpacked size`.
  - key: increasing, looks like a name-table offset or hash; 0x00340758 on directory markers. Not needed to read.
  - flags 0x10 = LZ10 compressed (stored block = standard `10 ss ss ss` LZ10 header + stream); flags 0 = stored raw.
  - size 0 = directory marker (28 of them); the stored length of an entry = next entry's offset - this offset.
- EZ_DAT.BIN: "EZP\0", same date words, u32 at 0x0C = offset of the end marker (0x0313468C); data from 0x10.

- The last entry (offset 0x0313468C = EZ_DAT 0x0C, size 0) points at a **name table** at the end of EZ_DAT: NUL-padded
  ASCII names (`STAGETABLE.BBQ`, `STAFF_19.AGL`...); an entry's key is its name's offset there (verified for the first
  and last entries). Names aren't needed to read or repack.
- Stored blocks start 4-aligned except 11 pairs of empty entries at odd offsets (e.g. 15/16 at 0x8832); LZ blocks
  carry 0-4 bytes of zero padding.

Repack (phase 3/4, verified): `ez.repack(tbl, dat, {index: bytes})` copies untouched blocks as stored (padding
included), recompresses replaced ones with ndspy LZ10, keeps each block's length mod 4 so every later offset keeps
its alignment, shifts the offsets and EZ_DAT 0x0C. No edits = byte-identical ROM (`tests/test_identity.py`).

**The size word is the unpacked length rounded up to 16.** All 4,146 entries obey it (`tests/test_extract.py`
checks the 328 text tables; a one-off scan covered the rest). The whole-file loader at 0x0203BD34 does
`malloc(size & 0xFFFFFF)` and calls the decompressor with only (dest, src) — the decompressor reads the LZ10 header
and writes in 16-byte units, so a size word that isn't align16 makes it write past the block. Symptom (phase 4,
reproduced on entry 85 BTLDIR): the game boots to the developer menu (script 0x1000) and hangs on the next press.
Fix: `ez.repack` writes `align16(len(data))`, and `tools/insert.py` pads changed tables to 16 so the parser sees
zeros instead of heap garbage. `frame diff empty` is not enough to catch this: entry 0/191 edits loaded fine, 85
didn't — the hang is per-entry, not per-build.

Verified end-to-end in the emulator after the fix (shots `work/qa/textproof/`): BTLDIR's three narration lines
replaced with ASCII show up on the ST00 opening card (`bbq_narration_ascii.png`), and arm9's `ステージを選択` replaced
in place shows "STAGE SELECT" on the scenario chart (`arm9_label_ascii.png`). So the game draws our inserted
cp932/ASCII from both sources.
The ROM has ~10.6 MB free after 0x03558000, so growth is fine.

## Content by type (decompressed, `work/ez/index.tsv`)
| magic | count | what |
|---|---|---|
| `.BBQ1.00` | 332 | tables + scripts with Shift-JIS string tables: **all story/menu/data text** (`bbq.md`) |
| RGCN/RLCN/RCSN | 584/584/581 | NCGR/NCLR/NSCR graphics (`graphics.md`) |
| RNAN/RECN | 3/3 | sprite animations/cells |
| RTFN | 2 | NFTR fonts, ids 336 (11x11) and 337 (9x9) (`font.md`) |
| `\0DLG` / `\0LGA` | 1019/1019 | 3D model/animation pairs (ids ~2100-4130); LGA holds internal ASCII/SJIS node names (百式00, 柱01): **guess** not shown on screen |
| EMAP | 19 | map data |
