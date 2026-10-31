# .BBQ1.00 tables and scripts (the text container)

332 archive entries start with `.BBQ1.00`; 328 of them carry a string table. Parser: `tools/bbq.py`.

## Layout (verified on all 332 files: descriptors resolve, every pool rebuilds byte-exact)
- 0x00 `.BBQ1.00`, 0x08 u32 timestamp, 0x0C u32 1, 0x10 u32 0x18 (descriptor table offset), 0x14 u32 section count.
- 0x18 + 20*i: section descriptor `type, index_off, count, data_off, data_size`. **Both offsets are relative to the
  descriptor's own start.**
- Section types and layouts seen: (2,3,5,6,7) x258, (3,6,7) x59, (2,5,6,7) x11, (2,5,6) x4. Data is laid out in
  descriptor order; the type-7 section is always last.
- **Type 7 = string table:** `count` u32 offsets into a pool, then the pool of NUL-terminated Shift-JIS strings.
  Offsets are strictly increasing, no string shared, pool = exact concatenation of the strings. After the pool the
  file ends with 24 zero bytes.
- Type 6 is the largest section in script files (e.g. 0x19C6C bytes in 0240): **guess** the event bytecode, which
  refers to strings by index (string offsets live only in the type-7 index, so the script needs no pointer fixes).
- Types 2/3/5: small tables (record arrays); not decoded yet.

## Repack (done, phase 4: `bbq.rebuild`)
Rewrite the type-7 index + pool; the type-7 section is last, so only its index (`count * u32`, at the section's
`index` offset) and pool move. The index stays where it is, the pool is padded with zeros to a multiple of 4 like the
original, the file's 24-byte zero tail is kept, and the descriptor's size word is updated. The string count is fixed
(one string per id), but any string may change length, so a table can grow or shrink freely — the EZ entry's size
changes with it (`tools/insert.py` rounds the file up to 16, `archive.md`). `bbq.rebuild(raw, unchanged)` returns the
original bytes exactly, which is what keeps an untouched script/ a byte-identical build.

## Text facts
- 66,451 strings, 583,558 characters, all valid cp932.
- **One string per displayed line** in story text: a dialogue page is several consecutive strings, e.g. 0240 #0-#2
  `デラーズフリートによる / 観艦式襲撃は地球連邦を / 文字通り震撼させた。`. English must fit per line, or the engine must
  be changed to wrap/merge lines (phase 5 decision).
- Inline codes (verified by scan): `\n` (0x0A, 286 strings, descriptions), `$L`, `$P01` (value placeholders in skill
  descriptions, e.g. `【攻・防】＋（Lv$L×$P01）`), `%` literal. Half-width katakana with `&` in a few data strings
  (`ｶﾂ&ﾚﾂ&ｷｯｶ`, 0024 #204): **guess** internal keys.
- File 0000: stage names (67), 0001: scenario names, 0002: cursor/labels, 0003: character names, 0004: skills.
- Biggest scripts: 0240, 0232, 0210, 0228, 0089 (16-20 KB of SJIS each).
