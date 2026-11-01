# Story reviewer brief - Emblem of Gundam (NDS)

You read one chapter of a JP->English fan translation straight through, in story order, the way a player
meets it. Per-batch reviewers already judged single lines with +-2 lines of context; your job is what they can't see.
Read-only: no edits, no git, no subagents. Write the full report to the path in your dispatch (`work/tl/review_story_<chapter>.md`), then reply with the Assessment line and the Critical/Important/Minor counts.

## Inputs (paths in your dispatch)
- Chapter file: every line of the chapter in story order, `>> id | speaker | JP` / `EN`. Read ALL of it, in passes if
  large, before judging.
- `docs/synopsis.md` (plot, who is who, late reveals), `docs/style-reference.md` (voice per character),
  `glossary.md` (rulings at the top).

## Judge, across the whole chapter
- Continuity: each line follows from the one before; setups, callbacks and references back are kept; who knows what
  stays coherent; nothing gives a later reveal away early.
- Voice: each character sounds like the same person all chapter and matches their style-reference row: speech quirks,
  register, how they address others. Name the line where a voice drifts or goes neutral.
- Emotion: anger, fear, grief and comedy beats are as strong as the Japanese; a running gag keeps its punchline.
- Accuracy only where a line breaks one of the above; single-line accuracy was reviewed already.

## Report
### Issues
#### Critical (continuity break, reveal given away, wrong speaker)
#### Important (voice drift or flattened, emotional beat lost, setup or callback dropped, joke dead)
#### Minor (deferred to the polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
`ok` (no Critical/Important) | `issue` - one sentence why. The controller writes this word into the chapter's verdict.

## This game
- A chapter = 3 stages. Per stage: STAGE file (stage card narration, briefings, tutorial, unit barks), EV events,
  then BATTLE/MILITARY. Many speeches are short battle barks (retreat, defeat, level-up lines) not story-ordered:
  judge their voice, not continuity between them.
- The speaker column comes from the name label before a speech; it may be blank or carried over wrongly. Don't
  report speaker-column errors as translation errors.
- English lines are capped at 180 px (~30 chars): line breaks and continuation-line spaces are layout, not errors.
  Rulings: `docs/decisions.md` (ranks D12-D14, honorifics D10).
- One entry = one message page as the game shows it. `(page 605,606,465,607)` marks a page that borrows a line from
  another page (the engine reuses lines, D23): read it in that order; a page that looks broken only without the
  borrowed line is fine.
