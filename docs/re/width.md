# Width gate: how wide each text box is, in px (phase 5)

Translators need a per-box budget, not a guessed character count (`references/pipeline.md` §Width gate). The engine
**clips** a line at the box edge (it never wraps), so an over-long English line loses its tail silently: the budget has
to be measured, and the lint in phase 7 checks every line against `tbl/windows.json`.

## How to measure
1. Build a stress ROM: `python -X utf8 tools/mark.py --out work/marker/id.nds` (every string -> its id) or write a
   ruler into one string (`tools/mark.py --torture EZ INDEX`, or a throwaway script that rewrites one table).
2. Warp the screen: `python -X utf8 tools/debug/warp_all.py ROM --only SCENE --frames 1200 --out work/qa/x`.
3. Read the span: `python -X utf8 tools/textband.py work/qa/x/SCENE/final.png --all --thr 170`. The ruler is
   `0123456789...`, each digit 6 px wide with the VWF table, so the px budget is `span + 6` at most and the last
   fully drawn digit's column is exact.

**Gotcha that cost an hour:** the cards and message windows **type the text on**. With `--frames 300` (the default)
a long marker is still being typed when the shot is taken, so the "clip" you measure is typing progress: three lines
of the same 60-digit string gave 96/192/42 px at 300 frames and 180/180/180 px at 1500. Always run the width shots
with `--frames 1200` or more, and re-shoot if two frames differ.

## Measured budgets

| variant | px | lines | notes | shot |
|---|---|---|---|---|
| stage-card narration (BBQ 0085 BTLDIR + `<NNN>STAGE`) | 180 | 3, 15 px pitch, x=33 | 30 ASCII digits fill it; the card is the most common story screen | `work/qa/w85c/st00_open/final.png` |
| command-menu row (map menu, shop, prep menu) | 130 | 1 | 22 ASCII digits fit, the 23rd clips | `work/qa/a9r/mapmenu/final.png` |
| chart footer hint (arm9 `ステージを選択`) | 114 | 1 | clipped where the B button starts | `work/qa/a9r/chart/final.png` |

Guessed until measured (flagged `"measured": false` in `tbl/windows.json`): `prep_condition_row`,
`stage_info_panel`, `list_row`, and `story_dialogue` — **no scene in the warp list reaches a story dialogue window
with a portrait yet.** That one is the phase 6 blocker: the warp list needs a scene that shows a dialogue page
(candidates: a later narration page inside a stage intro, or the leftover message-window test script 0x1006,
`docs/re/debug.md`).

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
