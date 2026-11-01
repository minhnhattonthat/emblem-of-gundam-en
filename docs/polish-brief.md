# Polish-pass brief - Emblem of Gundam

You resolve the reviewer Minors in one chunk of `docs/polish.md`: `work/tl/polish_chunkK.md` (K in your dispatch).
Each line there is `<polish.md line number><TAB>- [ ] id - note - suggested EN`. Every line ends fixed or waived;
the release refuses to ship while any stays open. Read `docs/translator-brief.md` (style, width, line rules),
`glossary.md`, `docs/style-reference.md` and `docs/decisions.md` first.

Per item:
1. Look: `python -X utf8 tools/ctx.py EEEE:IIII 8` (JP + EN around the id, with every copy of the same Japanese).
   Story notes on lowercase starts, broken sentences or dashes are often **shared page lines** (the VM shows one
   line on several pages): `python -X utf8 tools/pages.py | grep -A6 "^EEEE_"` lists them; a line shared by two pages
   must read right on both, or leave it and waive.
2. Decide: fix when the note is right and a fix fits the box; waive when it is a false positive (the line is fine
   in context, a borrowed/shared line, a ruling in decisions.md or the glossary says otherwise), no wording fits the
   width, or it is pure taste. Never change correct English just to suit taste. Cross-cutting notes (one term or
   label everywhere, rank forms): grep `script/bbq/*.json` for every copy and fix them all in your batch.
3. Fix: collect every id you will change (each whole block: all lines of the speech), then
   `python -X utf8 tools/batches.py polish polK ID ID ...` (writes `work/tl/polK.tsv` + `polK.out.tsv` pre-filled
   with today's English; if you need more ids later, make `polKb`, `polKc`). Edit only the lines you change in
   the `.out.tsv` with your file-edit tool (`\n` = line break inside a string, keep the JP's line count unless the
   form allows `<empty>`), check widths with `python -X utf8 tools/fit.py "line one / line two"`, then
   `python -X utf8 tools/batches.py check polK` until OK. Do not merge; the controller merges.
4. Record: `work/tl/polK.res`, one line per chunk item: `<line number><TAB>fixed` or
   `<line number><TAB>waived: <short reason>`. Every line number in your chunk appears exactly once.

Never edit `docs/polish.md`, `script/`, `glossary.md`, `tools/` or another chunk's files. An item you cannot judge
without seeing the game (speaker of a line, in-game label): waive with the reason "needs in-game check: ..." so the
controller sees it.

Rulings: 少佐 in direct address may be "Commander" (D13); Zeon space forces and ship crews use navy ranks (D12, D15);
the 08th MS Team keeps "Ensign" for 少尉 (D14); "Lieutenant Matilda"; honorifics -san/-kun/-chan kept (D1);
様 -> Lord/Lady; 駐留 = [Station], 保持 = [Hold].

Reply with only: `chunk K: N fixed, M waived, batches polK[,polKb..]`, then one line per "needs in-game check".
