# Text ranges, pointers, free space

## Where the text is
1. **BBQ string tables** (`bbq.md`): 328 archive files, 66,451 strings / 583,558 chars. Referenced by index from
   the file's own sections; offsets only in the type-7 index. This is ~99% of the text.
2. **arm9.bin** (verified by `jpscan.py work/fs/arm9.bin 4 0x02000000`, `work/arm9_jp.txt`): NUL-terminated
   Shift-JIS strings from RAM 0x02072170 to ~0x020778xx: team-building, shop, save/load, turn prompts
   (キャラクターの配属, セーブをしますか？, ターンを終了しますか？ ...). **Not yet done:** find the pointers to each (4-byte
   LE 0x0207xxxx words in arm9; literal pools) in phase 4.
   - A **leftover debug menu** is in there: イベントトリガー, キャラレベル操作, `Ａ=%d,Ｂ=%d,Ｃ=%d,Ｄ=%d`,
     自軍ダメージ:無効/有効, 敵軍ダメージ:無効/有効, 自軍 補給値－100 (0x02072A0C-0x02072B04). Phase 2 candidate.
   - printf-style codes in arm9 strings: `%d`, `%s` (keep).
3. **Graphics** (`graphics.md`): stage cards and a handful of UI screens.
4. Not text: LGA node names (internal), SDAT.

## Control codes
None in-band besides `\n` (0x0A), `$L`, `$P01`-style placeholders, `%`/`%d`. Line breaks in story text are separate
strings (`bbq.md`).

## Free space
- Archive files are rebuilt whole, so any file may grow; EZ_DAT can grow into the ROM's free tail
  (0x03558000-0x03FFFFFF, ~10.6 MB of 0xFF, inside the 64 MiB chip). ndspy rebuilds the FAT.
- arm9 strings: grow by moving them (into BBQ? or a new area) and repointing; ITCM tail ~27 KiB for hook code (guess,
  check at runtime).
