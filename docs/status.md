# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase 9 (release): in progress (2026-11-02).**
  - **Story pass done:** `tools/story.py` -> `work/qa/story/chapters/` (23 chapters x 3 stages; complete line
    blocks plus `[page in game ...]` notes for borrowed-line pages; `pages.py`'s page split misses some lines, so
    never build chapter files from pages alone). 23 reviewer reports `work/tl/review_story_chNN.md`; gate
    `qa_gate.py check work/qa/story/manifest.tsv work/qa/story/verdicts` = 23/23 current (13 fixed, 10 ok).
    Caveat: ch01-ch16 were read on earlier chapter-file versions (missing lines/pages caused false "broken
    sentence" reports, triaged against the JP); fixed chapters were restamped by the controller, not re-reviewed.
    Recurring bug found: dedup copied one rendering of 「はい！」/「ハッ！」 to every speaker ("Yes, ma'am!" to men,
    "No, sir!" as assent); all copies checked. 駐留 = [Station], 保持 = [Hold] (ST05 tutorial) in conditions.
  - **Release script:** `tools/release.py [--version 1.0] [--force]` (gates: build, check.py, smoke, script/ +
    arm9 jp_left, every `work/qa/**/manifest.tsv`, no `- [ ]` in polish.md, boot literal 0x02022DAC == 0x1042,
    then xdelta3 patch, re-apply compare, `release/EmblemOfGundam_EN_v<ver>.zip` = patch + README.txt from
    `docs/release-readme.txt`). Not yet run end to end. README.md placeholders filled.
  - **Polish pass done (2026-11-02):** 446/446 ticked (299 fixed, 147 waived with reasons) by 6 translator agents
    (`docs/polish-brief.md`, chunks `work/tl/polish_chunkN.md`, results `polN.res`). New `batches.py polish NAME
    ID..` (fix batch of whole blocks, current EN pre-filled); `merge` now overwrites a duplicate only while it still
    equals the head (keeps per-speaker copy fixes). Per-agent batches folded into one `polall` (conflicting blocks:
    one winner each) and merged: 898 lines + copies, 172 files. Win/lose labels now sentence case ("All enemies
    destroyed"), Solar Ray System in 0198. Build + 71 tests + smoke green. Waived "needs in-game check": 0316:0241
    speaker, 0333:0147 addressee, debug-only labels (0019, 0035), "Discard"/options-row widths (lint passes).
  - **Next:** re-tour (`warp_all.py build/eog_en.nds --frames 900 --out work/qa/tour`, text changed), `qa_gate.py
    init` + visual-qa round + `check`, then `tools/release.py`. Never publish without the user.
- **Phase 8 (2026-11-02): complete.** Build `9b51ba44d3285e109252c43e71d04705e9c50c06`: 70 tests pass, lint 0,
  smoke ok, cold tour `work/qa/tour` 373/373 scenes (ST06 is a scrapped stage, no scenes), `qa_gate.py check
  work/qa/manifest.tsv work/qa/verdicts` = 18/18 sheets ok (visual-QA rounds r3-r5, `work/qa/verdicts/r*_*.tsv`).
  Graphics rows not reachable in-game (preview only): 0450 scenario menu, 0402 building placeholder, 2239 portrait
  tags. Combat English end to end (playtests `work/play/combat2`, `combat3`, cold check `fc3`). Fixed:
  - **Shared page lines** (D23): the VM reuses a line across pages (ST02 tutorial "In this state, press left / Here
    you can move units"); `tools/pages.py` lists them (`--narration`, `--shape`), `tests/test_pages.py` gates
    quote/indent shape. Two translator passes rewrote ~100 tutorial/narration pages (`docs/shared-lines-*brief.md`).
    Stiff but left: 0088:0427 "Earlier I wrote that by the [Baton]" (every clearer version > 180 px), 0093:0520-0521.
  - OBJ sprites (`gfx.OBJ_LABELS`, `tools/ncer.py`): Team Formation stat icons 攻防移消補機 -> 32x16 Atk..Mob (D22);
    forecast odds 前進/後退/連戦 -> 3x5 caps ADVANCE/RETREAT/CHAIN (`gfx.CAPS`; the 9 px font hid the 1 of 100%),
    battle 攻/防 -> Atk/Def. DLG 2177 move-cost popup 物資量 -> SUPPLIES; 2183/2185 Attacker/Defender caption kept
    inside x 2-45 (was "Defende Retreat"). 0402 placeholder 建物 -> Building.
  - arm9 region starts at 0x71FD4 (戦闘開始/戦闘終了 status bar -> Battle Start/End). Skill names capped at 19 bytes
    (forecast skill list copies 20 bytes, no NUL): Matilda's Guard, All-Round Piloting, Transform Piloting.
  - Font ' and " redrawn as straight ticks (read as ´). `extract.py` needs `--overwrite` now (a bare run wiped
    script/ this session; restored from git, the JP dump is in `git stash`).
  - Credits end caption: gone with the D16 erase (checked to the Produced-by card, `work/qa/credits_end`).
  - **Gotcha:** a savestate only works on the ROM build that made it (the game caches the EZ file table: an old
    state on a new build hangs DeSmuME). Regenerate with `warp_all.py --only` after each build; play sessions from
    a frozen ROM copy (`work/play/rom_p8*.nds`).
  - Visual-QA round 3 (fresh tour): Team Formation "Cost" label forced white ink (`gfx` 0444, left column read
    faint); ST28/ST56 conditions use the map names Lunar Gravity Well / Closed-Type Colony; st45 opening rewrap;
    **tutorial boxes** (fn 201) size at 7 px a byte, so 97 English boxes ran off screen: the build now moves each
    box's X left to fit (`bbq.tutorial_boxes`, `docs/re/bbq.md`), verified on 61 st01_prep pages (`work/qa/tut3`);
    Scenario Chart title bar (DLG 2227) erases both halves to the middle teal (`dlg` style `seamT:X`).
  - Not surveyed: DLG 2248-4131 (battle sprites/cut-ins); the combat playtests saw no Japanese there.
  - Every tour re-hashes ~17 of 18 sheets (frame timing): after any build change, the gate needs a fresh round of
    4 visual-qa agents (`qa_gate.py todo --size 5`); a text-only fix can rerun just its scene with `--only`.
- **Phase 7:** review remediation **complete** (2026-11-01).
  See `docs/phase7-remediation.md`. I1-I5 and M1 repaired; width coverage reports zero unresolved lines.
  Native call/domain evidence is in `docs/re/native-widths.md`, `native-domains.md` and `retirement-route.md`.
  Caller evidence excludes 263 unused BBQ description/series lines and 42 hidden debug labels, and maps
  another 19 ARM9 labels (`docs/re/width-callers.md`). `tools/lint.py` now fails on
  unmeasured budgets; the ordinary `tools/check.py` and commit hook now enforce the same strict gate
  (`--phase7` is a legacy alias). M1 now checks
  layout padding and reflowed speech indentation (D20).
  New measurements: sound/gallery 160 px, extras headers/help 177 px, buttons 112 px, MAP names 177 px/31 bytes.
  Fixed sound-menu clipping via the checked VM layout operand, gallery label overflow, and a missing Kycilia.
  Command rows/headers are 128 px (corrected); gallery/unit-name VM strings also have a 31-byte cap.
  Build SHA-1 `d48ac934d5ee96de573963c6080cff84f8cb2536` (2026-11-01 11:24:08 UTC); integrity and smoke
  pass; normal cold-boot tour `work/qa/native_remediation_tour` completed 373/373 at 1200 frames. No fresh full-tour
  visual approval is claimed; the earlier issue verdicts remain unresolved.
  Full strict check: **67 tests pass**,266.772s, including the current merged-script width gate.
  Native fixes: trait fields80→88px (full Sub-Flight System), two fixed-copy loops replaced by the game's
  NUL-terminated helper, second Attack→Fight per D18. Allocator guards pass map_unit/prep_upunits/prep_assign.
  Complete runtime formats now enforce actual name/value domains and native byte caps, including save details,
  gallery rows, team notifications and Yes/No host concatenation. Targeted basket and retirement captures pass.
  No release script/zip exists yet; phase8 visual/graphics acceptance must precede phase9.
- **Phase 6 review** (`.harness/reviews/...phase6.md`)
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
  - **Visual-QA round 1 (4 chunks, all `issue`):** fixed since: stage names over the 150 px name bar (8 shortened,
    lint check); **3D-layer textures** (`tools/dlg.py`, `\0DLG`+`\0LGA`): 17 staff-roll pages, win/lose banners
    (2233), result panel/buttons (2139), battle/skill banners, phase labels, chart/baton headers, save popups,
    retirement notice (2179-2245), seen in-game; "Weapon" W (5 px W for font 337); "Shooting" -> "Ranged"; one-word
    lines st40/st52; **0444 all four quadrants** (TL team info, BL prep 編成チーム情報, TR ユニット情報 = scene
    `map_unit`, BR キャラクター情報 = `map_chara`; D18 short forms Atk/Def/.../Mob, Lnd/Rgh/Wtr/Air/Spc; title bars
    whose glyphs reuse the glow colours use the `h` erase); save dialog "Yes      /      No" spaced under the fixed
    はい/いいえ cursor brackets; extras top art 0372 reading erased (D16); font 0336 `>`/`<` redrawn as chevrons
    (`font.GLYPHS`: "->" read as "-)"); dev wipe names "NW -> SE". Left as is: extras help bar starts at x=0 like
    the Japanese.
  - 2239 portrait tags (preview only: no warp state has a deployed/full team): 出撃中 "Sortie", 配属/配備/強化限界
    "Assign/Deploy/Upgr." over "Max" (`dlg` style `z` blanks an overlay sub-texture first). Font 337 graphics
    labels: 5 px M and W. New scenes: map_unit, map_chart, map_ops, prep_upgrade, prep_assign, prep_upunits,
    st01_after (level-up + save screen after the stage 1 result).
  - **Next:** combat screens (forecast 0378, battle sprites 0340/0344 with 前進/後退/連戦/攻/防 cells) via a
    playtester (`docs/playtester-brief.md`, session `work/play/combat1`); 0402 建物 (check whether drawn); 0450
    scenario menu: labels done, no path found (title, extras, map menu, prep, stage end all checked); 2177 (6 px
    kanji bars) and 2169 (red glyph tiles): too small, leave unless seen in-game; end caption
    `- エンブレム オブ ガンダム -`. Then re-tour
    (`warp_all.py build/eog_en.nds --frames 900 --out work/qa/tour`), `qa_gate.py init` + verdicts (fresh read-only
    pass) + `check`, smoke, then release zip.
- **Earlier phase 7 work (completion claim superseded by the review above):**
  - Historical results: build, `tools/check.py` 37 tests (incl. `test_lint` = old `tools/lint.py` 0 errors: font chars, control
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
    exactly). Missing budgets were previously treated as warnings; that was not sufficient to complete phase 7.
    Current unresolved coverage and new measurements are at the top of this file and in `docs/re/width.md`.
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
  logo planned to be replaced by nothing or English. Staff roll (D2/D3, Hepburn, given name first,
  `tools/dlg.py` CREDITS): readings guessed for 重信康 Ko Shigenobu, 華南恋 Ren Kanan, 山本眞生 Mao Yamamoto,
  福家真広 Masahiro Fuke, 小野剛 Tsuyoshi Ono, 久野綾子 Ayako Kuno, 太田東孝 Harutaka Ota, 経塚斗茂 Tomo Kyozuka,
  小松央典 Hisanori Komatsu, 黒澤豪 Go Kurosawa, 野澤芽与 Meyo Nozawa, 松田宙 Sora Matsuda, 田村烈 Retsu Tamura;
  correct any you know (one edit in CREDITS).
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
