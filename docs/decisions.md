# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

All of D1-D7 came from the owner's standing answers for one-shot runs (Orca dispatch, 2026-11-01).

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-01 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). |
| D2 | 2026-11-01 | Romanization source for names | official art, earlier patch, Hepburn | Official English names (Gundam franchise) where they exist, else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-01 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-01 | Abbreviations | engine work first (default), abbreviate | Skill default: full names and terms, engine work before abbreviating. |
| D5 | 2026-11-01 | Graphics text left in Japanese | none (default), list | Translate all (titles, menus, banners, cards); keep the Japanese logo only if no official English version exists. |
| D6 | 2026-11-01 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-11-01 | Existing saves / savestates | user's files, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-01 | Git identity | - | Already set (minhnhattonthat); don't change it. |
| D9 | 2026-11-01 | Font approach (phase 5) | keep fixed half-width; VWF via the CWDH advance; redraw a new font; tiny 2-letters-per-tile font | VWF via CWDH: the renderer honours the per-glyph advance (measured), so ASCII advances become each glyph's ink width and a line holds ~25 % more English. The existing glyphs stay (5x10 condensed, legible); no new font file ships, so nothing to license. Redrawing the glyphs is a phase 7/8 polish item if the playtest wants it. |
| D10 | 2026-11-01 | Honorific details under D1 (controller default, owner pre-approved D6) | romanised 様 (-sama); Lord/Lady; ranks in JP | -san/-kun/-chan kept; 様 -> Lord/Lady X and ranks as English ranks, because that is how the official English Gundam releases render them and players know those forms. |
| D11 | 2026-11-01 | Story text line model (phase 6, controller default) | one EN line per JP line, verbatim; reflow within a block | One output line per string (the engine draws one string per line and the string count is fixed), but a speech/sentence block may reflow across its own lines; each line <= 180 px (story box measured: work/qa/dlg3). Speech continuation lines start with one space, like the JP full-width indent. |
| D12 | 2026-11-01 | Rank set for Zeon space forces and ship crews (reviewer question) | navy; army | Navy ranks (大尉 Lieutenant, 少佐 Lieutenant Commander), matching the official English 0079 subtitles (Lieutenant Commander Char); army ranks only for ground units (08th MS Team, Odessa). |
| D13 | 2026-11-01 | 少佐 in direct address (reviewer question) | always "Lieutenant Commander"; "Commander" | Direct address may be "Commander" (the naval convention for a Lieutenant Commander, and it fits 180 px); the full rank "Lieutenant Commander" in narration and first mentions. |
| D14 | 2026-11-01 | 少尉 in the 08th MS Team (reviewer r13 asked for army "second lieutenant") | second lieutenant; ensign | Ensign: the official English 08th MS Team release calls Shiro "Ensign Amada", and players know that form; this exception to D12 covers the 08th MS Team cast and its narration. |
| D15 | 2026-11-01 | 中佐/大佐/中将 for space forces (translator b085-b090 found the style table clashing with D12: 中佐 and 少佐 both "Lieutenant Commander") | army forms; navy forms | Navy forms as D12: 中佐 Commander (Cima), 大佐 Captain (Synapse), 中将 Vice Admiral (Cowen); army forms for ground units; "General Revil", "Colonel Char", "Colonel M'Quve" and "Colonel Bask" keep their established English forms. |
