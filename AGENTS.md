# Emblem of Gundam (NDS) English translation

Skill: translate-retro-game; `python tools/skill.py` prints its folder. Read its SKILL.md before ROM, text or QA work. `"$(python tools/skill.py)"` works in bash and PowerShell; never paste a `plugins/cache/<hash>` path.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py`  -> build/eog_en.nds (checks the dump against `rom.sha1` first; applies `script/`, `--no-script` skips it)
- Extract:  `python -X utf8 tools/extract.py` (ROM -> `script/`; `--check` lists holes, exit 1)
- Check:    `python -X utf8 tools/check.py`  (unittest suite in tests/ + lint; the pre-commit hook runs this; hooks: `git config core.hooksPath tools/hooks`)
- Smoke:    `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/eog_en.nds --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/eog_en.nds --out work/qa/warp --script tools/debug/scenes.lua --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (frames count after the warp; scenes `stNN_open|battle|prep|end` NN 00-67, `shop save chart map mapmenu debugmenu victory gameover title title_menu load extras credits`...: `tools/debug/scenes.lua`, notes `docs/re/debug.md`; never ask the user to play to a scene)
- Warp all: `python -X utf8 tools/debug/warp_all.py [ROM] [--only REGEX]` (every scene from cold boot -> `work/states/<scene>.dst` + `work/qa/warps/sheet_*.png`; rerun after code/font/graphics changes). play.py sessions: `--script tools/debug/devmenu.lua` boots the dev menu.
- Marker:   `python -X utf8 tools/mark.py [--ruler 0] [--out work/marker/marker.nds]` (every drawn string -> `TTT:IIII` (+ ruler); `--report` lists the non-text classes; `--torture EZ INDEX` writes the glyph torture line)
- Width:    `python -X utf8 tools/textband.py SHOT --all` reads a text line's ink span out of a shot; `tbl/windows.json` holds the per-box px budgets (`docs/re/width.md`). Width shots need `--frames 1200`: the cards type the text on
- Release:  `python -X utf8 tools/release.py` (xdelta patch + verify; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Emblem of Gundam (Japan).nds` (YEGJ, 64 MiB; gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: DeSmuME QA fork in `tools/desmume/` (release qa-2, https://github.com/minhnhattonthat/desmume/releases/download/qa-2/desmume-qa-51b26329-win64.zip; gitignored; emu.py writes a fresh ini per run). Savestates: `work/states/`.
- Text: `script/` (JSON: `bbq/<ez index>_<name>.json` = one string per id, `arm9.json` = strings keyed by RAM address; tools `extract.py`/`insert.py`). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.
- Python deps: `pip install ndspy capstone keystone-engine Pillow`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Python downloads on this machine fail SSL verification: `export SSL_CERT_FILE=$(python -c "import certifi;print(certifi.where())")` first (fetch_emu.py).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
