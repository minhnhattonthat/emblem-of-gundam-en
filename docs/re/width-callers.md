# Width caller audit — 2026-11-01

Read-only native/BBQ inspection supplements the ruler evidence in `width.md`. These are exact
destination mappings and non-player exclusions, not a phase-7 approval. The pinned original ROM is
the source of every address below; ARM9 addresses are RAM addresses. The independent review output
is retained locally at `work/width-review-result.md`.

## Non-player record fields

Character-description IDs in BBQ 3 are `{2}` plus the distinct `u32(0x94 + 0x24*r)` values for
`r=0..146`. Unit-description IDs in BBQ 5 are `{2}` plus `u32(0x94 + 0x34*r)` for `r=0..140`.
These are the type-5 record field at +8, not alternating string indices: deduplication makes an
index-modulo rule incorrect. `tests/test_lint.py` compares the committed exact-ID selectors against
the ROM's record fields. Together they resolve 257 previously unmeasured changed lines.

- Character initializer `02042be8` resolves descriptions at `02042c30–02042c40`. Reviewed consumers
  of accessor `02042fc0` do not draw +8. Character-info `0204da54–0204daf4` instead displays skill
  descriptions through `02038c30`, reading CHARTABLE +4.
- Unit initializer `02042b7c` resolves +8 at `02042bc4–02042bd4`. Native 145 (`0205ab58`) can return
  that description for selector 2 (`0205abb0–0205abb8`). Scanning all 332 BBQ containers finds only
  three calls: BBQ 20 offsets `16a8` and `31d4` use selector 1; BBQ 81 offset `2dc8` uses selector 0.
  The normal unit-info path gets weapon descriptions through `02038c78`, reading CHARTABLE +4.
- Pool default ID 2 is unreferenced in both tables; both have empty type-6 bytecode sections.
- BBQ 14 LEVELTABLE has five type-5 records at `0x8c`, stride 4, referencing IDs 1–5. ID 0 is
  unreferenced. Initializer `02042e50` resolves the strings; accessor `02043088` has only its
  initialization caller `02042e70`. Thus IDs 0–5 have no downstream rendering consumer.

These exclusions waive width checks only; glossary, encoding, control-code and empty-text checks remain.

## Hidden map-debug labels

The exact 42 addresses selected by `hidden_map_debug` in `tbl/windows.json` have literal consumers
and pointer tables leading to `020327ec–02032e68`. The release menu builder stops at item 4
(`02029678: cmp r8,#4`); entry to `02032890` requires item 5 at `020357f4–020357fc`. Debug warps
deliberately change that bound. `02072758` and `02072a34` remain unresolved: individual-debug
function `0203269c` also consumes them from a separate path at `02035d18`.

## Shared render destinations

Exact address lists live in `tbl/windows.json`; this table explains why their budgets transfer.

| Variant | Call evidence | Measurement |
|---|---|---|
| one_icon_footer, 9 IDs | Setter `0204d218`; shop table `02072070` at `0202afa0`, upgrade `0202bc34`, character info `0204add4`, Baton `0204c04c`, save/load `020533fc`/`02053410`, character list `02054cc8`. Only icon slot 0 is populated. | Full 177 px ruler in `work/qa/coverage_ui/prep_assign/final.png` and `prep_upunits/final.png`. |
| chart_footer_hint, 8 additional IDs | Swap table `02072438` at `0202def4–0202df00`, info `0202e410`, chart item `02057310`, movement `020297bc`/`020297e0`/`02029800`. Same two-icon configuration as measured `02076d98`. | 114 px from `work/qa/a9r/chart/final.png`. |
| menu_row, headers `02072d38` and `02072cc0` | Installed at `020295c8`/`0203b2bc`, mode 3. Header and items share construction loop `02024dd4–02024e70`. `02024ca4` reads width table `02070d04`: (80,96,32,128). | Ruler reaches x64–191 in `work/qa/a9r/mapmenu/final.png`: 128 px. |

Footer slots occupy x192, x128, x64 (`0204ceb4–0204ced4`); a shared text setter alone does not
justify assigning 177 px to every footer. The old menu claim of 130 px assumed constant-width digits:
22 current ruler digits advance 123 px, 23 advance 129 px, and 30 advance 171 px.

## Transport limits

MAKERLOGO native calls at `24d4`, `25b8`, `29dc`, `2dc8`, `3d4c` return VM type 9 (32 bytes) and
pass strings through a 32-byte helper argument. Native return copies are at `02048774–02048784` /
`0204640c`. Sound/gallery labels and unit names therefore need a 31-byte text cap as well as a pixel
budget. All current values fit. A long ruler cannot demonstrate that bytes past this transport survived.

## Remaining research

286 lines remain unresolved, all ARM9. Save/error messages `02073cbc`, `02073cd0`, `02073ce8`,
`02073d00`, `02073d1c`, `02073d38`, `02073d7c`, `02073e78`, `02073ed0`, `02073f2c`, `02073f88`,
`02073fe4` share dispatcher `02043d14` and descriptors `02073e18`, but invoke `0204f90c` with
different configurations (`0x2002`/`0x2011`). The broad save stress shot does not establish their limits.
Other unknowns include headers, team names, traits, options, format strings and writable defaults.
The current eight-W `%s` approximation is not proof of the widest runtime name.
