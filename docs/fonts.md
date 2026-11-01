# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| ROM NFTR 0336/0337 | the game's own fonts | - (game data, already on the cartridge) | not shipped (patch edits the advance table only) | all text, VWF | per-glyph advances (tools/font.py) |
| fonts/LiberationSans-Bold.ttf | https://github.com/liberationfonts/liberation-fonts release 2.1.5 | SIL OFL 1.1 (`fonts/LICENSE-Liberation.txt`) | yes, as rendered pixels | stage title card captions (tools/gfx.py), 20 px | - |
| fonts/LiberationSerif-Bold.ttf | same release | SIL OFL 1.1 | yes, as rendered pixels | 0083 stage card captions (dark Mincho in the original), 20 px | - |
| fonts/LiberationSans-Regular.ttf | same release | SIL OFL 1.1 | yes, as rendered pixels | spare (UI screens) | - |
