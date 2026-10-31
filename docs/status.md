# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1 (recon) done 2026-11-01. Next: phase 2 (debug tool). No build yet.
- **Done:**
  - Step 0: DeSmuME QA fork qa-2 in `tools/desmume/`, smoke boots the original ROM (title -> menu -> opening card),
    Lua probe logs, pre-commit rejects a failing test, guard hook blocks `sed -i`, `rom.sha1` pinned, `tools/check.py`.
  - Phase 1: `docs/re/` (archive, bbq, font, text, graphics). Text = Shift-JIS in .BBQ string tables (66,451
    strings, one string per displayed line) + ~100 arm9 strings; fonts NFTR 0336/0337 with ASCII; static graphics
    sweep found 68 stage title cards + 6 UI screens + title subtitle/© + credit card.
- **Next (phase 2, debug tool):** arm9 holds a leftover debug menu (イベントトリガー, キャラレベル操作, damage toggles,
  supply ±100 near 0x02072A0C): find how it is reached (xrefs to those strings), else build `tools/debug/warp.lua`
  from RAM (stage id from BBQ 0000 order, scenario select). Scenes: every stage card, intermission menus, shop/team
  build, save/load, game over, ending, credits.
- **Then:** phase 3 identity build (`ez.py` repack + ndspy save, restore 0x1000 word and 0xFF pad); corrupt-and-boot
  a BBQ 0000 string to promote the SJIS draw path to verified.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) series logo art on stage cards (Gundam/08th/0080/0083/Zeta, with small
  Japanese inside the logo) planned to stay as official logo art per D5; title katakana subtitle under the English
  logo planned to be replaced by nothing or English.
- **Tooling gotcha:** Python HTTPS fails cert verification on this machine; set `SSL_CERT_FILE` to certifi (AGENTS.md).
