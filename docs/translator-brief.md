# Translator brief - Emblem of Gundam (NDS, Bandai 2007)

You translate part of the Japanese script of *Emblem of Gundam* (Bandai Namco Games, a turn-based tactics game that retells Universal Century history from the One Year War (0079) through 0083, Zeta and
later, with the player choosing at branch points whose side carries "the baton of history"). Tone: sober war-chronicle
narration between stages, and the anime casts' own voices in battle and event dialogue.
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before the
next. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - rulings, character voices, example pairs. Match it.
2. `work/tl/terms_<batch>.txt` - binding glossary rows for this batch (`glossary.md` has the full table).
3. `docs/synopsis.md` - what the game is and the stage list.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>jp`. `# <table>` lines name the table the rows come from (skip them).
- **One id = one drawn line.** The game draws every string as its own line and never wraps; the number of strings
  is fixed. So your English has exactly one output line per id.
- `form`: `name` (a speaker label shown above a speech), `dlgK/N` (line K of an N-line speech, 「...」),
  `narrationK/N` (line K of an N-line sentence of narration), `menu` (a label, item, description or message, alone).
- **Reflow inside a block is allowed and expected:** the N lines of one `dlgK/N` / `narrationK/N` block are one
  utterance; translate it as a whole and spread the English over the same N lines so each reads naturally (break at
  phrase boundaries, never mid-word, no hyphenation). If the English needs fewer lines, write `<empty>` for a trailing
  line (rare; prefer balanced lines). You cannot add lines.
- `limit`: `180px` is a hard budget per line (story text: dialogue and narration boxes, measured in-game). `~NNNpx`
  is the width of the Japanese in a box we have not measured: a soft target, go over it only when the meaning needs
  it (the check warns, it does not fail). 180 px is about 36-40 characters of mixed English; measure, don't guess:
  `python -X utf8 tools/fit.py "line one / line two"` prints each line's px.
- Text in a story table that has no `「` is narration (third person, past tense chronicle voice).
- `\n` inside a `menu` string is a forced line break inside one box (skill and unit descriptions, prompts). Keep the
  same number of `\n`; each part is one line of that box.
- Codes to copy exactly: `%s` (a name the game inserts), `%d` (a number), `$L` (skill level), `$P01`/`$P11` (a
  parameter value), `%` (a literal percent sign).

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (never a shell heredoc)
`id<TAB>English`, every input id exactly once, same order, nothing else (no header, no `#` lines needed).
Plain ASCII only: straight quotes `"` and `'`, `...` for …/・・・, `--` for a dash, no tabs inside the English, no
Japanese or full-width characters (【攻撃】 -> `[ATK]`, ＋ -> `+`, × -> `x`, ～ -> `~`, ① -> `(1)`), no `\uXXXX`.
`\n` written as the two characters backslash-n.

## Validate
`python -X utf8 tools/batches.py check <batch>` from the repo root. Fix every ERROR until it prints OK. WARN lines
(soft limits) are fine when the meaning needs the room.

## Style (full rulings in docs/style-reference.md)
- Faithful: keep the information and the order of ideas; adapt idiom, not meaning. Don't add what the Japanese
  doesn't state; don't summarise or skip. Keep jokes and famous lines landing (Amuro's "Not even my father has ever
  hit me!"-class quotes use their well-known English form).
- Official English Gundam names and terms (Bandai/Sunrise English releases): Amuro Ray, Char Aznable, Sayla Mass,
  Kycilia, M'Quve, Ramba Ral, Zaku II, Gouf, GM, White Base, Jaburo, Odessa, A Baoa Qu, Side 7... The glossary wins
  over your memory; when a name is not in it, use the official English form and report it as `NEW TERM`.
- Honorifics (owner ruling D1): keep さん/くん/ちゃん as `-san`/`-kun`/`-chan`; 様 on Zeon nobility and superiors ->
  `Lord X` / `Lady X` (the series' official English); 閣下 -> `Your Excellency` (third person
  `His/Her Excellency`); ranks as English ranks, navy forms for space forces (D12/D13/D15: 大尉 Lieutenant, 少佐
  Lieutenant Commander, 中佐 Commander, 大佐 Captain; army forms for ground units) - the rank table in docs/style-reference.md is the only authority. `batches.py check`
  rejects a dropped honorific or 閣下. Name order is Western (given name first).
- Speech: 「...」 -> `"..."`. JP continuation lines of a speech start with a full-width space; start your
  continuation lines with one space (` response sluggish...?"`). A speech that spans lines opens `"` on its first line
  and closes on its last.
- Keep the speaker audible: rough soldiers (ぜ/ねぇ/っス) sound rough, nobles formal, kids like kids, Char cool and
  ironic, Amuro a sulky teenager in 0079. A line any speaker could have said is a mistake.
- Placeholders: no suffix glued to a variable (`No. %d`, never `%dth`); no a/an right before `%s`.
- Never abbreviate a name or term to fit (owner ruling D4); rephrase. If it really can't fit, keep the meaning, write
  your best version and report `LONG: id`.

## Consistency
Never edit `glossary.md` or any file but your own `.out.tsv`. For a recurring name or term not in the glossary, pick
the official form, use it consistently, and report it.

## Report (reply with only this)
Batches written and entry counts; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
