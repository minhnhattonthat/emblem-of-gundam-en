# Shared-line review brief - Emblem of Gundam (NDS)

Background: `docs/shared-lines-brief.md`. A first pass rewrote lines so that pages borrowing a line from another
page read correctly, but some rewrites follow the Japanese word order too closely and read badly, e.g.
"Earlier I wrote that by the [Baton] / would be affected.", "First, to the unit to move, / the Saberfish, / move
the cursor.", "Also, 'Edit' does not just merge / into one.". You are a fresh reviewer: judge the English as a player
reads it, page by page, and fix what reads wrong.

## Input
`python -X utf8 tools/pages.py --narration > work/odd_narration.txt` (99 pages: narration and tutorial pages that
borrow a line; each with JP | EN and, under `also`, every other page that shows one of its lines).

## Task
For every page in the file, read the page and each `also` page as the player sees them (each one alone, in order).
Each must be grammatical, natural English that says what its Japanese page says; a sentence may continue onto the
next page, as in the Japanese. Where a page fails, rewrite the lines involved so every page that shows them reads
well. A shared id has one English text for all its pages: make it a phrase that stands on its own in each (a
complete clause, a noun phrase, an adverbial opener), the way the Japanese line does; then fit the rest of each page
around it. Keep each page's line count; one string = one line; no line left empty that had text.

Rules: edit `script/bbq/<table>.json` with the file-edit tool only (a string's index is its id); never run
`tools/extract.py` (it overwrites script/); names/terms per `glossary.md`; style `docs/style-reference.md`; lines
<= 180 px (`python -X utf8 tools/fit.py "text"`); keep each line's leading space / quote shape like its neighbours.
When done: rerun the command above and re-read every page you touched with its `also` pages; then
`python -X utf8 tools/pages.py --shape` and `python -X utf8 tools/lint.py` must both report 0.

## Report
Counts (pages read / pages fixed), then one line per fix: table, ids, old -> new. Then anything you were unsure of.
