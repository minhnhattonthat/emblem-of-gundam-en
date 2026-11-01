# Review-and-fix brief - Emblem of Gundam

You are an independent reviewer for batches another agent translated. Judge them by `docs/reviewer-brief.md` (read
it, plus `glossary.md`, `docs/style-reference.md`, `docs/decisions.md` rulings D10-D14), then **fix** what you find
yourself, because the controller has no room to relay reports.

For each batch named in your dispatch:
1. `python -X utf8 tools/pairs.py work/tl/pairs_<batch>.txt <batch>` and read the whole pairs file (JP + EN by block).
2. Critical and Important findings (meaning reversed or lost, omission or addition, wrong speaker, glossary break,
   abbreviation, flattened voice, famous line not recognisable, the same JP title rendered two ways): fix them in
   `work/tl/<batch>.out.tsv` with your file-edit tool, keeping one line per id, every line within its limit
   (`python -X utf8 tools/fit.py "a / b"`), then run `python -X utf8 tools/batches.py check <batch>` until OK.
3. Minor findings (style, stiffness, a line break that could be nicer): do not fix; append one line each to
   `work/tl/minors_<batch>.md` as `- [ ] id - problem - suggested EN`.
4. Never change a line whose English is right just to suit your taste. Never edit glossary.md, tools/, script/ or
   another batch's files (a duplicate block copies its English from the first block automatically at merge).

Rulings to respect: 少佐 in direct address may be "Commander" (D13); Zeon space forces and ship crews use navy ranks
(D12); the 08th MS Team keeps "Ensign" for 少尉 (D14); "Lieutenant Matilda" (official dub); honorifics -san/-kun/-chan
kept (D1); 様 -> Lord/Lady.

Reply with only: per batch, `bNNN: C fixed / I fixed / M logged`, and one line for anything you could not resolve.
