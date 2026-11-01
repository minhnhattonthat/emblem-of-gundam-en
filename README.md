# Emblem of Gundam English translation

Unofficial English fan translation of **Emblem of Gundam** (Nintendo DS, Bandai Namco Games, 2007): the source text and tools
that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Story, briefings, battle dialogue, tutorial | Translated |
| Menus, units, characters, skills, system messages | Translated |
| Stage title cards, UI graphics with text | Translated |
| Staff roll | Translated |
| Title logo | Kept |

Known issues: see [Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/emblem-of-gundam-en
cd emblem-of-gundam-en
# copy your dump to: rom/Emblem of Gundam (Japan).nds
#   (67108864 bytes, SHA-1 c60906c2084281daf2c948b17443c25040f3d365; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/eog_en.nds
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Bandai Namco Games' and is included only so
the translation can be checked against it. Emblem of Gundam is (c) SOTSU / SUNRISE and Bandai Namco Games; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
