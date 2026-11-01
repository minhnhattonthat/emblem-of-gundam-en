# Width gate: how wide each text box is, in px (phase 5)

Translators need a per-box budget, not a guessed character count (`references/pipeline.md` §Width gate). The engine
**clips** a line at the box edge (it never wraps), so an over-long English line loses its tail silently: the budget has
to be measured, and the lint in phase 7 checks every line against `tbl/windows.json`.

## How to measure
1. Build a stress ROM: `python -X utf8 tools/mark.py --out work/marker/id.nds` (every string -> its id) or write a
   ruler into one string (`tools/mark.py --torture EZ INDEX`, or a throwaway script that rewrites one table).
2. Warp the screen: `python -X utf8 tools/debug/warp_all.py ROM --only SCENE --frames 1200 --out work/qa/x`.
3. Read the span: `python -X utf8 tools/textband.py work/qa/x/SCENE/final.png --all --thr 170`. The ruler is
   `0123456789...`. Use `fit.px()` for the current font: `1` advances 3 px and the other digits 6 px, so a
   31-digit ruler is 177 px. Do not assume every digit advances 6 px.

**Gotcha that cost an hour:** the cards and message windows **type the text on**. With `--frames 300` (the default)
a long marker is still being typed when the shot is taken, so the "clip" you measure is typing progress: three lines
of the same 60-digit string gave 96/192/42 px at 300 frames and 180/180/180 px at 1500. Always run the width shots
with `--frames 1200` or more, and re-shoot if two frames differ.

## Measured budgets

| variant | px | lines | notes | shot |
|---|---|---|---|---|
| stage-card narration (BBQ 0085 BTLDIR + `<NNN>STAGE`) | 180 | 3, 15 px pitch, x=33 | 30 ASCII digits fill it; the card is the most common story screen | `work/qa/w85c/st00_open/final.png` |
| command-menu row (map menu, shop, prep menu) | 128 | 1 | corrected: native mode-3 surface is 128 px, ruler reaches x64–191 | `work/qa/a9r/mapmenu/final.png` |
| chart footer hint (arm9 `ステージを選択`) | 114 | 1 | clipped where the B button starts | `work/qa/a9r/chart/final.png` |

The initial table above is historical. `tbl/windows.json` now also records the measured story dialogue,
character/unit/skill names, terrain cells, and the phase 7 remediation measurements below.

## Phase 7 review remediation (2026-11-01)

Strict coverage is now mandatory for phase acceptance: `python -X utf8 tools/lint.py` or
`python -X utf8 tools/check.py --phase7`. The ordinary unit suite also tests the validators with invalid
inputs; passing that suite is not evidence that all width research is finished. `tools/width_coverage.py`
lists the unresolved categories quickly, with `--ids` for every affected line.

| Variant | Budget | Evidence |
|---|---|---|
| stage-name list | 150 px | Same names as the already measured STnnSTAGE prep name bar; use the smaller shared destination. |
| music/SFX lists | 160 px, 31 bytes | `work/qa/coverage_all/extras_music/final.png`, `extras_sfx/final.png`: full-table alphabetic ruler clips at x48..207; VM transport bound in `width-callers.md`. |
| battle/event gallery lists | 160 px, 31 bytes | `work/qa/coverage_all/extras_battle/final.png`, `extras_event/final.png`: same x48..207 list and 32-byte VM transport. |
| extras headers/help | 177 px | Full 31-digit ruler visible in `work/qa/coverage_lists/{extras,extras_sound,extras_event}/final.png`. This is a demonstrated lower bound, not the full clip width. |
| extras buttons | 112 px | Conservative limit below the medium-layout ruler's 114 px of visible ink; `work/qa/coverage_lists/extras_sound/final.png`. The wider main extras buttons use the same smaller limit. |
| AREA INFO map-name bar | 177 px, 31 bytes | Full ruler visible at `work/qa/area_bound/map/final.png`; bound deliberately smaller than the 200 px panel. |

The 52-character alphabetic area-name stress overran a 32-byte copy and continued into `Ranged` in the
adjacent field (`work/qa/coverage_lists/map/final.png`). That is not a terrain suffix to concatenate to the
name. The 31-byte ruler terminates correctly; current names are at most 27 bytes. Lint now enforces 31 bytes
as well as pixels for MAP tables, including narrow strings that would fit in pixels but overrun that copy.

The original sound submenu's narrow layout clipped `Sound Effects`. `tools/layout.py` changes MAKERLOGO's
setup-mode operand at 0x20c0 from 0 to 1 (the same medium layout used by the title menu). The readable result
is `work/qa/sound_medium/extras_sound/final.png`; neither label is abbreviated.

Remaining: 286 ARM9 lines. `width-callers.md` records the native/BBQ evidence for excluding unused
description/series fields and hidden map-debug labels, and mapping 19 further ARM9 strings. Exact
description-ID sets are tested against record fields; neither wording nor index parity establishes
an exclusion. Give remaining rows measured destinations or reviewed non-player exclusions with a
concrete reason. Do not substitute a guessed generic ARM9 limit. Known chart-footer and command-menu
addresses are mapped to 114/128 px; nine proven one-icon footers use a conservative 177 px bound.

## What the marker build showed about the text system

- A string is one line; `\n` inside it moves the pen down one line (285 strings use it) and the following strings
  then start one line lower.
- Each string is drawn with its own background clear: a 4th string drawn into a 3-line box erases the tail of the
  3rd line (reproduced with the torture line, `work/marker/torture.nds`); it is not a box width.
- Text is *clipped*, never wrapped: a 40-digit line shows ~32 digits and stops.
- Centred fields push a long marker's id out of view (the stage-info panel); the id-only marker build
  (`--ruler 0`) is what to read those from.
- Text that stays Japanese in the marker build is either a graphic (stage title cards, the `ステージ情報` panel
  headers, the credits caption `- エンブレム オブ ガンダム -`, `GAME OVER`) or one of the excluded classes below.

## Non-text strings (excluded from the marker build, `tools/mark.py --report`)

| class | count | rule | why |
|---|---|---|---|
| empty | 317 | `""` | must stay empty; the engine draws nothing and advances a line |
| blank | 100 | only spaces | layout padding |
| numeric | 158 | digits, spaces, `+-./:%` | counters and percentage signs (`  0`..` 30`, `【消費】$P01%`) |
| key | 90 | half-width katakana with `&` | internal data keys (`ｶﾂ&ﾚﾂ&ｷｯｶ`), compared against table data |
| path | 2 | `./EZ_DAT.BIN`-style names | arm9 passes them to the file loader; marking one black-screens the boot |

Everything else (66,135 strings) is drawn text.
