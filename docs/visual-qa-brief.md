# Visual-QA reviewer brief - Emblem of Gundam (NDS)

You review contact sheets from the translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file (`work/qa/chunks/chunk_NNN.txt`): one `id<TAB>path` line per sheet. Read every sheet in it;
  none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Each sheet is up to 24 tiles, one per warp scene (the label above a tile is the scene: `st13_open` = stage 13
  opening, `_battle`, `_end`, `_prep` battle preparation, `briefNN` win/lose conditions, plus menus). Each tile is
  the DS's two screens stacked (top 256x192 over bottom 256x192), shot 900 frames after the warp.
- The Japanese original's sheets, same ids and tile order: `work/qa/warps/` (an older tour of the untranslated
  build; tiles may differ by a few frames). `glossary.md` has the binding names.

## How to look
- Read each sheet whole first. Text is small: zoom into each tile you can't read with
  `python -X utf8 "$(python tools/skill.py)/scripts/sheet.py" SHEET.png --crop x,y,w,h --zoom 3 --out C:/Users/Nathan/AppData/Local/Temp/vqa_<chunk>.png`
  and read that. Single full-size frames are in `work/qa/tour/shots/<scene>.png` (256x384).
- When something looks wrong, open the same scene in `work/qa/warps/shots/<scene>.png` (`sheet.py EN.png --compare JP.png`).
  If the original shows the same thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible (text, labels, banners, title cards);
- text overflowing a box, clipped by a frame, or running off screen;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters, smears where text was erased;
- broken line breaks: a word split mid-line, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- text still typing out (the story boxes and stage cards type their text on), a box mid-fade or mid-scroll, a
  cursor mid-blink, a scene still loading;
- anything identical in the original's shot;
- the series logos on stage cards (official logo art, ruling D5) and the "EMBLEM of GUNDAM" logo;
- developer-menu screens (`devmenu`, `debugmenu`, `sysflags`, `mapview`, `battle_movies`, `event_movies`) keep
  some debug labels; still report Japanese there, as `issue` with "dev screen" in the note.

## Verdicts
Write your verdict file once you have read every sheet, one line per sheet id:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which scene tile, which text, what is wrong; several issues
on one sheet go in the same note, separated by ` ; `).
Then return a short summary: counts, and the issues one per line.
