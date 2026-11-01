# Shared-line fix brief - Emblem of Gundam (NDS)

The script VM builds each message page from string ids, and some pages borrow a line from another page: the
Japanese wrote "この状態で、" once (0093:0412) and three tutorial pages open with it. The translation reflowed the
lines of each block as if every page were a consecutive run, so a borrowing page now shows a line from another
sentence ("In this state, press left / Here you can move units / ..."). `tools/pages.py` lists every page whose ids
are not one consecutive run, with the Japanese, the English and, under `also`, every other page that shows one of
its lines.

## Task
1. Run `python -X utf8 tools/pages.py > work/odd_pages.txt` and read the whole file.
2. For each listed page, make **every page that shows a shared line read as correct, natural English**, with the
   meaning of its Japanese page. Usually: give the shared id a self-contained English line that fits each page it
   appears in (as the Japanese line does), then re-split the neighbouring lines of the home page and of the borrowing
   page around it. Change only the lines those pages need; keep each page's line count (one string = one line).
3. Edit `script/bbq/<table>.json` with the file-edit tool (never a script that rewrites the file). A string's index in
   `strings` is its id.
4. Rules: names/terms per `glossary.md`; style per `docs/style-reference.md`; keep leading-space speech indentation
   as in the surrounding lines (D20); keep control codes; each line must fit its box: the tutorial and story boxes
   are 180 px (`python -X utf8 tools/fit.py "text"` prints px, if unsure). No line may be left empty that had text.
5. Leave as is (not player text, or already fine): 0023_MAPVIEWER, 0026_TAKESHITA, 0028_KOYAMA (debug tables),
   pages that already read correctly in every context (e.g. a shared `Bright-san."` closing line, the blank lines
   around "Good luck.", the victory/defeat condition pairs in 0113/0116). Say which you left and why.
6. When done: rerun `tools/pages.py`, re-read every listed page and its `also` pages; then run
   `python -X utf8 tools/lint.py` and fix anything it reports in lines you touched.

## Report
Per page: table, ids changed, old -> new text in one line each. Then the pages left unchanged with a reason.
