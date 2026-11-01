# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8 (QA in the emulator) **in progress** 2026-11-01. Phase 6 review (`.harness/reviews/...phase6.md`)
  fixed: I1 `batches.units()` keeps the JP apart from the dedup key (+ test), I2 a literal percent is its own
  token (`batches.codes`, shared by lint, + test), I3 honorific/閣下 check in `batches.check` and `lint.py` (per
  block: each distinct katakana-name+さん/くん/ちゃん needs a -san/-kun/-chan, 閣下 needs "Excellency") + the 4
  lines, I4/I5 the named voice lines + Scirocco, M1 brief ranks. A translator agent ran a **voice pass** over the
  ~65 deferred voice/joke/stiff polish items (`work/tl/voice_pass.md` lists every changed string).
- **Phase 8 so far:**
  - **Stage title cards: done** (`tools/gfx.py`, in the build): 67 cards redrawn from each `STnnSTAGE` string 351
    (lint now keeps it identical to the 0000 stage list; 6 mismatches fixed), Liberation Sans/Serif Bold 20 px
    (`fonts/`, OFL, `docs/fonts.md`), caption ramp of each card, re-tiled into the same 256-tile NCGR; logo rows
    untouched (`tests/test_gfx.py`). Card 1129 "06" kept. Seen in-game (st13/st20 warps, `work/qa/cards/`).
  - **UI labels** (`gfx.LABELS`: pixel bbox of the Japanese, font = game NFTR 336/337 or a TTF tuple; works in
    RGB so cells on other extended-palette slots snap to their own slot; shared/flipped tiles get never-referenced
    slots and the NSCR is repointed; "" = erase, blended from the rows above/below): 0375 stage info (**seen
    in-game**, `work/qa/ui/map_top.png`), title 0360 (reading erased + "© SOTSU・SUNRISE", D16, **seen in-game**),
    credits 2121 "BANDAI NAMCO Games Inc." (preview), 0378 forecast, 0444 team info, 0450 scenario menu (preview
    only: no warp reaches them yet). `python -X utf8 tools/gfx.py preview` -> `work/gfx_en/ui_*.png` (preview
    colours are wrong on extended-palette cells; trust the emulator); `tools/gfxgrid.py ID` = tile grid view.
  - **QA tour:** `warp_all.py build/eog_en.nds --frames 900 --out work/qa/tour` = 359/359 scenes ok (16 sheets,
    one final shot per scene; `--only` reruns now keep the other rows and rebuild full sheets). Gate:
    `qa_gate.py init work/qa/manifest.tsv work/qa/tour --glob "sheet_*.png"`, 4 chunks, verdicts in
    `work/qa/verdicts/` from visual-qa agents (`docs/visual-qa-brief.md`; JP reference = `work/qa/warps/`).
  - **Banner source:** VRAM dump at brief01 f5400 (`work/qa/brief_dump/`): not a BG file; the 勝利条件/敗北条件
    banners are OBJ sprites, most likely from sprite sheet 0340 (+ its cells 0343, 1D-mapped 4bpp) - edit needs
    the NCER cells (which tiles form each banner).
  - **Next:** warp scenes for forecast/team info/scenario menu/credits card (debug tool) and check them in-game;
    0444 terrain strip 隠蔽/水/空/宇 (16 px boxes, not done); 0340/0344 sprite tile sheets (zoom), 0402 建物;
    the end caption `- エンブレム オブ ガンダム -` (source unknown: last credits frame); the **win/lose banners
    勝利条件/敗北条件** (briefNN scene; missing from the phase 1 survey, source not found). GAME OVER is already
    English art. Then `qa_gate.py init` over the tour sheets (`work/qa/tour/`, warp_all at 900 frames on the
    EN build), visual-QA verdicts (fresh read-only pass), smoke.
- **Phase 7 (this session):**
  - Gates green: build, `tools/check.py` 37 tests (incl. `test_lint` = `tools/lint.py` 0 errors: font chars, control
    codes JP==EN, trailing space, width vs `tbl/windows.json`, stub last lines), `tools/romcheck.py` 0 unexpected
    changes (per-component diff; the NDS filesystem is re-laid out, so this replaces a flat `romdiff.py`), smoke ok,
    `extract.py --check` 0 holes. Build sha1 44c2f7fd... (2026-11-01 16:16).
  - Leftover Japanese: every BBQ string and arm9 string in the built ROM is English except the 90 `ｶﾂ&ﾚﾂ&ｷｯｶ` keys
    (data). Raw scan: `jp_left.py work/arm9_en.bin --orig work/arm9_jp.bin --sjis [--halfwidth] --range 72000-78000`
    = 0 (it found ユニットの売却/購入 at 0x02072150/60 below the old region start; `arm9.LO` now 0x72150, 359 strings).
    No overlays; the only files are EZ_DAT/EZ_TBL/sound_data.sdat.
  - Fixes: script VM string pushes widened to fit English (`bbq.widen`, win/lose condition text spilled into the
    defeat line); stage-record name field copied from the pool (`bbq.stage_name`, stage-info panel kept Japanese);
    6 arm9 strings glued to binary data now extracted; **arm9 writable buffers** (`未設定` x7, `鳥00`) must never be
    relocated: moving them blanked the stage-info panel (found by `tools/a9bisect.py`). `arm9.BUFFERS` + a test that
    every strcpy/strncpy/memset destination is listed (`docs/re/text.md`). Story stubs rewritten, dev-menu titles
    shortened to their VM slot.
  - Widths: measured `char_name` 118, `skill_name` 104, `unit_name` 118, `terrain_cell` 57 px (`Underwater` fits
    exactly). **Not measured** (lint warns, phase 8 visual QA covers them): `arm9_ui` 371 lines, `unit_desc`/`char_desc`
    (placeholder fields like `About Amuro`, `Gundam description text`, maybe never drawn), `stage_name_list`,
    `sound_list`, `gallery_list`, `series_name`, `extras`; guessed `stage_info_panel`, `prep_condition_row`,
    `list_row`, `area_info`.
  - Tools: `tools/lint.py`, `tools/romcheck.py`, `tools/stress.py ID=TEXT|@ruler` (one-string stress ROM for widths),
    `tools/a9bisect.py` (bisects arm9 edits against a scene region's ink), `tools/lua/writelog.lua`,
    `tools/lua/vmalloc.lua`, scenes `briefNN` (win/lose screen).
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
- **Open bugs:** none in the build. Unverified: a `mark.py --arm9-move` ruler build timed out on the `load` scene;
  likely the moved `鳥00`/`未設定` buffers (now kept in place), not re-run.
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
