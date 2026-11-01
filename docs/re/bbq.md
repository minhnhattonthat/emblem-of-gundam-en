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

## VM strings (phase 7: why English came out cut or glued to other text)
Type 6 is the script VM's bytecode. Decoder at arm9 0x02046E84: each instruction is `[op][source line][args..]`,
`op = code | type << 10 | nargs << 16` (code = `op & 0x3FF`, dispatch table of 0x33 handlers at 0x02046F58). Types
0-7 are 4-byte values; 8-12 are strings of 16/32/64/128/256 bytes (size table arm9 0x02070F6C). Every table
decodes cleanly with this (`tests/test_vm.py`).
- **Op 0 with a string type pushes pool string #arg** (0x020472B0): strlen-copy into the scratch buffer 0x021A0B00,
  then a stack temp of the type's size gets that many bytes - **no NUL if the string is longer**.
- **Op 0x0E hands the top string to a native function** (0x02047738) as its own type: it copies that many bytes
  from the temp, so a cut temp is followed by whatever lies next on the VM stack (brief05's victory text ran into the
  defeat text: `in 'SatelliteVictory conditioVictory conditions c`). A temp bigger than the op's type is a VM type
  error (code 0xD via ctx+0x8C).
- The compiler picked each push's type from the Japanese (`敵全滅` -> str16, story lines str32/str64). 10,258
  English strings outgrew their push. **Fix (`bbq.widen`, run by `insert.ez_edits`)**: raise the push's type to
  the smallest that holds bytes + NUL, capped by the consuming 0x0E op's type (str64 for message lines and win/lose
  conditions, str32 for location headings). Pushes that feed a script-function call (ops 0x2D/0x2E) keep their type
  (the callee's frame is declared): the build fails with the string id, and the English has to fit (25 strings
  were shortened, mostly the dev stage-jump list). Probes: `tools/lua/vmalloc.lua` (logs every string temp the VM
  allocates, with its size, source and bytecode), `tools/lua/writelog.lua`.

## Stage record (type 5, entry 0)
90 stage tables have an 84-byte record: `char name[64]` + 5 words. The map's stage-info panel shows this name (not
the pool string). Each record's name equals a pool string (#351 mostly); `bbq.stage_name` writes that string's
English into the field (max 63 bytes) at build time.

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
