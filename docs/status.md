# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4 (extract) done 2026-11-01. Next: phase 5 (engine spike + marker build). All text is in `script/`
  (66,802 strings) and `python tools/build.py` inserts it; an untouched `script/` builds a byte-identical ROM.
- **Done:**
  - Step 0: DeSmuME QA fork qa-2 in `tools/desmume/`, smoke boots the original ROM (title -> menu -> opening card),
    Lua probe logs, pre-commit rejects a failing test, guard hook blocks `sed -i`, `rom.sha1` pinned, `tools/check.py`.
  - Phase 1: `docs/re/` (archive, bbq, font, text, graphics). Text = Shift-JIS in .BBQ string tables (66,451
    strings, one string per displayed line) + 351 arm9 strings; fonts NFTR 0336/0337 with ASCII; static graphics
    sweep found 68 stage title cards + 6 UI screens + title subtitle/© + credit card.
  - Phase 2: `tools/debug/` warp tool on the game's own developer menu (script 0x1000, booted by patching one RAM
    literal; stage jump ST00-ST67 x opening/battle/ending) + the map-menu デバッグ item (forced win/lose, damage
    toggles). `warp_all.py` reaches all 291 scenes from cold boot (67 stages x open/battle/prep/end, all
    68 title cards seen; prep screens, shop, save, chart, map, map menu, debug menu, victory, game over, title,
    load, extras, credits, viewers; proof sheets `work/qa/warps/sheet_*.png`, states `work/states/`), ~15 min
    at --jobs 6. ST06 is a scrapped stage (no opening; battle/end jump to ST07/ST08), left out. Notes:
    `docs/re/debug.md`.
  - Phase 3: `ez.repack()` + `tools/build.py` (ndspy save, restores the 0x1000 word and 0xFF pad) give a
    byte-identical ROM, tested in `tests/test_identity.py` (also checks an edited repack keeps every other entry and
    alignment). Build takes ~1 s.
  - Phase 4: `tools/extract.py` writes `script/bbq/<ez index>_<name>.json` (328 tables, 66,451 strings) and
    `script/arm9.json` (351 strings keyed by RAM address); `tools/insert.py` + `bbq.rebuild()` + `arm9.replace()`
    put them back, `tools/build.py` applies `script/` by default (`--no-script` for the identity build).
    `tests/test_extract.py` (9 tests): every string re-encodes to the ROM's bytes, every table's pool is its index
    plus its strings plus <4 zero bytes, rebuild is byte-identical and grows/shrinks, `extract.py --check` reports
    0 holes, every arm9 pointer-visible string is extracted, an untouched script/ builds the original ROM.
  - **Verified in the emulator** (`work/qa/textproof/`): BBQ insert -> ASCII narration on the ST00 opening card
    (`bbq_narration_ascii.png`); arm9 in-place insert -> "STAGE SELECT" for ステージを選択 on the scenario chart
    (`arm9_label_ascii.png`). Stage-card titles and the chart's green banner are *graphics*, not strings — they
    change nothing in `script/` (phase 8).
- **Next (phase 5, engine spike + marker build):**
  - Font/VWF: NFTR 0336 (11x11) / 0337 (9x9) have ASCII; decide whether to widen/space glyphs and whether the
    engine can wrap/merge the one-line-per-string layout (English is wider than Japanese; boxes are fixed width).
  - Marker build: every string -> `[id]`-style marker, cold boot + `warp_all.py`, every box shows its id, non-text
    "strings" found and excluded (half-width katakana keys like `ｶﾂ&ﾚﾂ&ｷｯｶ`, `%d`/`%s` formats, 317 empty strings).
  - Width gate: measure every box variant's width in-game.
  - arm9 growth: `arm9.replace()` only shrinks for now. Marker text will not fit 2-byte strings, so add relocation:
    move arm9 strings and rewrite their 4-aligned pointers, or append a new autoload section (ITCM tail
    0x01FF9160..0x01FF9160+27 KiB, or the 0x4 KiB slack before the main section ends at 0x77140) — `archive.md`.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) series logo art on stage cards (Gundam/08th/0080/0083/Zeta, with small
  Japanese inside the logo) planned to stay as official logo art per D5; title katakana subtitle under the English
  logo planned to be replaced by nothing or English.
- **Tooling gotchas:** Python HTTPS fails cert verification on this machine; set `SSL_CERT_FILE` to certifi
  (AGENTS.md). emu.py `--mash` fires during scripted routes whenever its press queue is empty (warp.lua defers it).
  A warp scene costs ~2-2.5 min wall at the default `--timeout 300`; run them in the background.
  **EZ size word = align16(unpacked length)**: writing the exact length hangs the game at the developer menu
  (reproduced on entry 85, `archive.md`). `ez.repack` and `insert.ez_edits` handle it; never pass a rebuilt entry
  straight to `ez.repack` without padding it to 16.
