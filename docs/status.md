# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 (translate) **done** 2026-11-01; next is phase 7 (insert, fit, check: width/overflow lint against
  `tbl/windows.json`, control codes, `romdiff.py`, `jp_left.py`).
- **Done:**
  - Step 0: DeSmuME QA fork qa-2 in `tools/desmume/`, smoke boots the original ROM (title -> menu -> opening card),
    Lua probe logs, pre-commit rejects a failing test, guard hook blocks `sed -i`, `rom.sha1` pinned, `tools/check.py`.
  - Phase 1: `docs/re/` (archive, bbq, font, text, graphics). Text = Shift-JIS in .BBQ string tables (66,451
    strings, one string per displayed line) + 351 arm9 strings; fonts NFTR 0336/0337 with ASCII; static graphics
    sweep found 68 stage title cards + 6 UI screens + title subtitle/© + credit card.
  - Phase 2: `tools/debug/` warp tool on the game's own developer menu (script 0x1000) + the map-menu デバッグ item.
    `warp_all.py` reaches all 291 scenes from cold boot with proof sheets; `work/states/<scene>.dst`.
  - Phase 3: `ez.repack()` + `tools/build.py` give a byte-identical ROM (`tests/test_identity.py`), ~1 s a build.
  - Phase 4: `tools/extract.py` -> `script/bbq/<ez index>_<name>.json` (328 tables) + `script/arm9.json` (351 strings);
    `tools/insert.py` puts them back; roundtrip + coverage tests; BBQ insert and arm9 insert verified in-game.
  - **Phase 5 (this session):**
    - **Font/VWF: done, no new font ships.** The renderer honours each glyph's CWDH advance and adds 1 px
      (measured: advance 6 -> 7 px pitch, 2 -> 3, 10 -> 11). `tools/font.py` sets every printable ASCII advance to
      its ink width (space 3): all printable ASCII goes from 665 to 508 px (76 %), ~25 % more English per line. The
      build installs the table in both fonts. Validated by a glyph torture line (every glyph draws, ink extent
      matches `tools/font.py` `width()` to the pixel) and `tests/test_font.py`. Details `docs/re/font.md`.
    - **arm9 growth: done.** `arm9.relocate()` moves long strings into the free ITCM autoload tail
      (0x01FF9160, 28,320 bytes), growing the ITCM section and sliding the DTCM source + autoload list (kept
      4-aligned) while rewriting the 4-byte literals; `insert.arm9_edit` falls back to it automatically. Verified
      in-game (a moved string renders on the chart footer). `tests/test_arm9.py`. Details `docs/re/text.md`.
    - **Marker build: done.** `tools/mark.py` marks 66,135 strings (`TTT:IIII|` + a 6 px-digit ruler), leaves 667
      non-text strings alone in 5 classes (empty 317, blank 100, numeric 158, key 90, path 2 - a marked
      `./EZ_DAT.BIN` black-screened the boot), and writes `work/marker/map.tsv`. A marker ROM with the ruler
      reaches **291/291 scenes** (`work/qa/markers/`, ids visible in every text box) and an id-only build
      (`--ruler 0`, `work/qa/markers_id/`) proves the same where text is centred (ids would be pushed out).
    - **Width gate: started, 3 variants measured.** `tbl/windows.json` + `docs/re/width.md`: stage-card narration
      180 px / 3 lines (x=33), command-menu row 130 px, chart footer hint 114 px. Measured with
      `tools/textband.py` off ruler shots. **Story dialogue with a portrait is NOT reached by any warp yet** - that
      is the phase 6 blocker (`tbl/windows.json` `story_dialogue` is a placeholder).
    - **Warp tool hardened:** stage scenes boot straight into the stage-jump script 0x1002 (the dev menu ignores
      input for ~1 s after it is drawn, which silently dropped presses and hung ~1 warp in 3); dev-menu scenes wait
      180 frames. 291/291 scenes pass on both the marker build and the VWF build.
- **Phase 6 (translate) - in progress:**
  - Story box measured: the portrait message window (MILITARY tables) is 180 px x 3 lines, same 180 px line buffer as
    the stage card (`tbl/windows.json` story_dialogue, shots `work/qa/dlg3/`; reached by warping `st01_open` and
    mashing A for ~5250 frames).
  - Tooling: `tools/batches.py split|check|merge|status` (dedups whole blocks: 29,650 unique JP strings / 312k chars
    -> 160 batches b001-b160 of <=200 lines; `work/tl/dups.json` maps each first block to its copies; merge writes EN
    into `script/` and copies it to every duplicate; a string counts as done once script/ differs from the ROM JP,
    so `split` only queues what is left). `tools/fit.py` (px per line, `tbl/vwf336.json` cache), `tools/pairs.py`
    (reviewer input). Briefs: `docs/translator-brief.md`, `docs/reviewer-brief.md`; `docs/style-reference.md`,
    `docs/synopsis.md`, glossary seeded with official names (rulings D10, D11).
  - Progress 2026-11-01: b001-b060 translated; b001-b042 reviewed (sonnet reviewers, all Approved/Needs-fixes,
    no open Critical), their Important items collected in `work/tl/fixes.md` and applied by a fixer agent; b043-b060
    reviewed by **review-and-fix agents** (`docs/review-fix-brief.md`: translator type, reviews batches it didn't
    write, fixes Critical/Important itself, logs Minors to `work/tl/minors_<batch>.md` -> fold into docs/polish.md).
    Use review-and-fix for the rest: reviewer agents can't write files and their full reports flood the controller.
  - **Done 2026-11-01:** b001-b160 translated, every batch review-fixed (no open Critical/Important), all merged:
    `batches.py status` = 66033/66033 (100 %), `check` 0 errors on all 161 batches, build + 28 tests + smoke green,
    English renders in the st56 story box (`work/qa/p6_st56/`). b161 = 58 punctuation-only strings the splitter
    skips (「……」, 、。, Ⅱ) converted mechanically. Rulings D15 (navy 中佐/大佐/中将; Colonel Bask/M'Quve/Char,
    General Revil kept). Stage labels normalised: 敵全滅 "All Enemies Destroyed", 自軍全滅 "All Allies Destroyed",
    敵機N機以上撃破 "Destroy N+ enemy units", 味方機N機以上撃破 "N+ allied units destroyed".
    Check now accepts glossary terms wrapped across lines and y->ies plurals; a literal ％ in a printf string must
    be `%%`. Dedup fix: the tail of a sentence cut at 8 lines no longer dedups across tables (0292:0150 had got
    another scene's "a nuisance.").
  - **Open from phase 6 (for phase 7/8 QA):** `docs/polish.md` has 291 unticked Minors (release blocks on them).
    a9:02072b9c `%d%%` - confirm in-game the formatter prints one `%`. a9:02072bc4 `〆` left as the game's glyph
    (context unknown). arm9 labels over their JP width (Artillery/Transform/Organize, Left/Right) need an in-game
    width check. Debug-only screens (0017/0018 ●○【EXE】) left as is.
  - Workflow: translator agents (3-5 batches each) -> `batches.py check` OK -> reviewer (sonnet) on
    `pairs.py work/tl/pairs_<x>.txt <batches>` -> Critical/Important fixed by the same translator -> `merge` ->
    commit. Minors go to `docs/polish.md`. work/tl is gitignored: **merge + commit after every wave**, a lost
    `work/tl` is rebuilt by `split` (it only queues what script/ still has in Japanese; delete `work/tl` first).
  - Graphics text is phase 8: stage title cards (68), the 6 UI screens, the credits caption
    `- エンブレム オブ ガンダム -`, `GAME OVER`, and the title's katakana subtitle are **not** in `script/` (confirmed
    with the marker build: they stayed Japanese).
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) series logo art on stage cards (Gundam/08th/0080/0083/Zeta, with small
  Japanese inside the logo) planned to stay as official logo art per D5; title katakana subtitle under the English
  logo planned to be replaced by nothing or English.
- **Tooling gotchas:**
  - **The cards and message windows type the text on.** A width shot taken at the default `--frames 300` measures
    typing progress, not the box: three lines of the same 60-digit string read 96/192/42 px at 300 frames and
    180/180/180 at 1500. Use `--frames 1200+` for any width measurement (`docs/re/width.md`).
  - The dev menu drops input for ~1 s after it appears; boot stage scenes into 0x1002 and give dev-menu presses
    ~180 frames (`tools/debug/warp.lua`, `docs/re/debug.md`).
  - Non-text strings that must never be marked: arm9 `./EZ_DAT.BIN` (the file loader), `%`/`$L`/`$P01` token-only
    strings, half-width-katakana `&` keys, counters. `tools/mark.py --report` lists every one with its class.
  - Python HTTPS fails cert verification on this machine; set `SSL_CERT_FILE` to certifi (AGENTS.md).
  - A script in `work/exp/` shadows a stdlib module for every script run from that folder (`bisect.py` broke
    Pillow's import); keep throwaway names specific.
  - **EZ size word = align16(unpacked length)**: writing the exact length hangs the game at the developer menu
    (reproduced on entry 85, `archive.md`). `ez.repack` and `insert.ez_edits` handle it; never pass a rebuilt entry
    straight to `ez.repack` without padding it to 16.
