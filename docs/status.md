# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2 (debug tool) done 2026-11-01. Next: phase 3 (identity build). No build yet.
- **Done:**
  - Step 0: DeSmuME QA fork qa-2 in `tools/desmume/`, smoke boots the original ROM (title -> menu -> opening card),
    Lua probe logs, pre-commit rejects a failing test, guard hook blocks `sed -i`, `rom.sha1` pinned, `tools/check.py`.
  - Phase 1: `docs/re/` (archive, bbq, font, text, graphics). Text = Shift-JIS in .BBQ string tables (66,451
    strings, one string per displayed line) + ~100 arm9 strings; fonts NFTR 0336/0337 with ASCII; static graphics
    sweep found 68 stage title cards + 6 UI screens + title subtitle/© + credit card.
  - Phase 2: `tools/debug/` warp tool on the game's own developer menu (script 0x1000, booted by patching one RAM
    literal; stage jump ST00-ST67 x opening/battle/ending) + the map-menu デバッグ item (forced win/lose, damage
    toggles). `warp_all.py` reaches all 291 scenes from cold boot (67 stages x open/battle/prep/end, all
    68 title cards seen; prep screens, shop, save, chart, map, map menu, debug menu, victory, game over, title,
    load, extras, credits, viewers; proof sheets `work/qa/warps/sheet_*.png`, states `work/states/`), ~15 min
    at --jobs 6. ST06 is a scrapped stage (no opening; battle/end jump to ST07/ST08), left out. Notes:
    `docs/re/debug.md`.
- **Next (phase 3, identity build):** `ez.py` repack + ndspy save, restore the 0x1000 word and 0xFF pad; test
  byte-identical. Then phase 4 extract (BBQ string tables + arm9 strings with pointers), corrupt-and-boot a BBQ
  0000 string to verify the SJIS draw path.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) series logo art on stage cards (Gundam/08th/0080/0083/Zeta, with small
  Japanese inside the logo) planned to stay as official logo art per D5; title katakana subtitle under the English
  logo planned to be replaced by nothing or English.
- **Tooling gotchas:** Python HTTPS fails cert verification on this machine; set `SSL_CERT_FILE` to certifi
  (AGENTS.md). emu.py `--mash` fires during scripted routes whenever its press queue is empty (warp.lua defers it).
