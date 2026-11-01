# Translation reviewer brief - Emblem of Gundam

You review a few batches of a JP->English fan translation of *Emblem of Gundam* (NDS tactics game retelling the
Universal Century wars). Read-only: no edits, no git, no subagents. Mechanical validity (ids, codes, ASCII, 180 px
line width, glossary terms present) is already enforced by `tools/batches.py check` - judge translation quality.
Return the report as your final message.

## Inputs (paths in your dispatch)
- Pairs file `work/tl/pairs_<name>.txt`: one entry per block (a speech 「...」, a sentence of narration split over
  several lines, or one menu/data string): `>> first-id [form] (speaker) | JP lines / joined` then the English lines
  joined the same way. `/` is a line break in the game (each line max 180 px, so a sentence is split across lines on
  purpose). Speech continuation lines start with a space by rule. Read ALL of it, in passes if large.
- `glossary.md` (rulings at the top), `docs/style-reference.md` (voices, rank/honorific rules), `docs/synopsis.md`.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means. The narrator's irony and asides must survive.
- Consistency: glossary names/terms exactly; official English Gundam names (Kycilia, M'Quve, Z'Gok...); ranks and
  honorifics per the style reference.
- Voice: Char's cool irony, Amuro's 0079 sulkiness, Dozle's bluster, rough soldiers' slang (ぜ/ねぇ/っス), old-man
  わし/じゃ, feminine わ/のね/かしら - flattened voice is Important, not Minor. Famous lines should be recognisable.
- Naturalness: English that reads like a translation; awkward line breaks (a break mid-phrase, a dangling article at
  a line end).
- Menu/data strings: concise UI English, consistent capitalisation within a table.

## Report
### Issues
#### Critical (meaning reversed, broken placeholder grammar, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, voice flattened, joke/famous line dead)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN (with / line breaks, each line short enough)`.
### Assessment
Approved | Needs fixes - one sentence why.
