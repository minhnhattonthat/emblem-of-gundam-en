# Native text destinations and transport — 2026-11-01

This continues `width-callers.md`. Addresses refer to the pinned original ARM9, except explicitly
documented patches. `tools/armdump.py START END` reproduces disassembly and literal targets.
Read-only review reports are retained locally in `work/width-review-next-result.md` and
`work/native-review-result.md`; this document preserves their actionable evidence.

## Measured native destinations

Exact ID selectors are in `tbl/windows.json`.

| Family | Measured bound | Native evidence and proof |
|---|---|---|
| Small dialogs | 176 px | Dispatcher `0204f90c`, flags bit 1; constructor `0204faa0–0204fad0` creates x40/y64, 176×64. Save ruler ink x40–215 in `work/qa/coverage_ui/save/final.png`; this prompt uses `strcpy`, so its ruler is not cut by a fixed literal copy. |
| Large dialogs | 208 px | Flags bit 2 without bit 1; `0204fae4–0204fb18` creates x24/y40, 208×112. `work/qa/large_dialog/save/final.png` has ink x24–231. QA-only `LARGE_DIALOG=1` changes save descriptor 9's selector to the existing error variant; no backup failure is induced. |
| Unit traits | 88 px, 31 bytes | Original 80 px fields clipped the 88 px “Sub-Flight System”. Three width operands now create 11×2 tiles at x168/y32,48,64. `work/qa/trait_width/prep_upunits/final.png` shows the complete term in both occupied slots. See allocation constraints below. |
| Option labels / values | 144 / 48 px | Descriptor table `020748f4`; constructors `020504b4–020504e4` and `020504e8–02050524`. Row-two ruler ink x32–175 / x176–223 in `work/qa/coverage_ui/options/final.png`. |
| Shop/upgrade headings | 120 px conservative | Nominal x8/y0, 152×16 (`0202a9f8–0202aa28`, `0202b6fc–0202b72c`), but Merit graphics occupy the right side. First 21 ruler digits (120 px) are whole before x136 in `work/qa/header_ruler/prep_assign/final.png` and `prep_upunits/final.png`. |
| Character-list heading | 80 px conservative, 16 bytes | Full 14-letter ruler in `work/qa/basket_width/st01_after/f000720.png`. Constructor `020551b8–020551e8` is 240×16; fixed copy `02054c70–02054ca4` copies 17 bytes including NUL. |
| Area modifier cells | 42 px conservative, 7 bytes | Complete seven-W ruler in all three cells, `work/qa/area_cells/map/final.png`. Native map `02055da4` and team `02059584` consume the same structure; fields are8 bytes apart despite16-byte copies. |
| Save/load title | 64 px | `02053360–02053398`, draws `020533f4/02053408`; ruler ink x96–159 in `work/qa/load_seeded/final.png`. |
| Save-slot details | 240 px, 3 lines | Constructor `0205339c–020533d0`, x16/y128,240×40; formatted/empty paths `020530c0/020530d0`. Ruler ink x16–255 in the same seeded load shot. |

Small-dialog groups and flags:

- Shop `0202abcc–0202aee0`, upgrade `0202b990–0202bb94`, swap `0202d388–0202d5f4`: flags 1.
- Map messages `0202f830–0202f84c`, `0203180c–0203182c`, `02035ad0–02035b7c`: flags 1;
  give-up/end-turn `02035a00–02035a6c`: 0x11.
- Save/load confirmations: dispatcher `02043d14`, descriptors `02073e18`, flags 0x2011.
- Level-up `0204ba88–0204bab8` and empty load slot `02053920–02053960`: flags 1.

Large-dialog groups: organization flags 0x42 at `0202c018`, flags 2 at `0202c098/0202c100`;
retirement flags 0x102 at `02052530–02052544`; save error descriptors 0,1,2,3,4,7,8,10 use 0x2002.
The dispatcher copies strings into a text member beginning at +8; its next accessed member is +0x110.
A conservative 255-byte text limit leaves space for NUL. Literal-specific narrower limits remain enforced.

Additional verified mappings: level-up title `020744c4`, backlog `02077118`, and option-status IDs
`02074934/40/4c/58/8c/a4/bc/d4` use the measured 177 px one-icon footer (`0204d218`). Confirm Move
`02072f0c` uses two icons through `02023720`, so 114 px. Individual-debug title/row `02072a34/02072758`
and other debug headers `02072e28/02072dbc` use mode 3 (128 px); these are mappings, not unused exclusions.

## Native copy repairs

Two English literals exceeded compiled copies that had been sized for Japanese:

- `02072550`: English 71 bytes; original `0202c110–0202c13c` copies only 63 including the old NUL.
- `0207480c`: English 61 bytes; original `0204f174–0204f19c` copies only 61 including the old NUL.

`tools/layout.py` replaces each complete loop with argument setup, a call to the existing `strcpy`
helper `020102ec`, and NOPs. The organization path restores r0=sp for the following dispatcher.
Original instructions are checked byte-for-byte. `insert.py` applies these only for changed source
literals; `romcheck.py` authorizes their exact preimages and replacement bytes. Build and lint enforce
at most 255 bytes of text. Simply increasing pair-copy counts was rejected in review: its odd tail
would read one byte past an even-sized relocated string allocation.

Other fixed-copy text caps (excluding NUL): shop/upgrade errors 26 bytes; swap errors 45,43,20 bytes
by exact ID; empty load text 18; organization confirmation 60 and character-only error 70; character
list title 16. The declarations in `native_bytes` are independent of the pixel variant.

## Trait allocation and action buttons

Trait constructors `02049a8c/02049acc/02049b0c` take widths from instructions
`02049a5c/02049a9c/02049adc`, changed from mov r1,#10 to #11. Both unit-info producer paths converge
on `0204a210`; fields are copied into 32-byte buffers at `0204a2a4–0204a2c4` and drawn at `0204a2dc`.
The exact trait indices are 0x3a–0x4d in table `02073380` (index 0x39 is the empty/default trait).

Allocator `020448d4` rounds to four tiles. Each field grows from 20 to 24 allocated tiles: +12 total;
the eight surfaces created by `02049a10` grow from 276 to 288. Screen 1 has 496 tiles starting at tile16.
Static headroom alone does not prove peak concurrent usage. `tools/debug/text_alloc.lua` traps the
allocator's failure return for targeted cold boots; the complete normal tour is also rerun.

Do **not** widen the mode-2 command-width table alone. Its 16-bit width at `02070d08` controls text,
touch bounds, edge clamping and cursor corners, but LGA/DLG 2162/2163 nodes 3/11/19 and 7/15/23 retain
independent 32×16 background textures 8/9. The proposed 40 px table-only patch was rejected.
The second Attack label (`02072c44`, selector2/action4) now uses the already approved “Fight” (D18).
Move and Info use the existing measured 28 px usable inset. The complete accessor-domain audit
excludes Discard for valid game state; see `native-domains.md`.

## Runtime format domains

`tools/runtime_text.py` checks complete expansions, not an eight-W stand-in:

- Unit-name templates use BBQ5 type-5 record +0: 141 records, stride0x34, start0x8c. Current maximum
  name is 112 px /22 bytes, “Gundam NT-1 Full Armor”. Character-name templates use BBQ3 +0:147 records,
  stride0x24; maximum110 px /22 bytes, “Gabriel Ramirez Garcia”.
- Level-up `%s` comes from four pointers at `020743c8`, values “1” or “2”. The fragment IDs are checked
  in their host expansion. Percentage formats use signed FORCETABLE values80,90,100,110,120.
- Save detail uses byte stage number+1 (up to256), table0 stage names, and unsigned frame count.
  Hours may reach19884; minutes/seconds reach59. The widest valid integer spellings are checked.
- Native139 formats `020770cc`; MAKERLOGO3350/336c/33a8 supplies a leading space and passes the
  result to helper10018/native116/`0204e630`. The complete row must fit160 px and31 bytes.
  Weapon numbers1–8, four environment pointers `02076f5c`, and eleven valid direction pointers
  `02076f6c` are enumerated. Current maximum is141 px /26 bytes, “ Weapon 8-Underwater-Front”.
- Environment/direction fragments also have a developer-template consumer (`020770b4`), native136.
  Both calls are in developer STAGEJUMP (1ac4/327c); the player host is native139 above.
- Team-name suffixes are expanded with every named-team provider. Reorganization's complete
  result also has a63-byte stack-scratch cap (`0206bbec/0206bc10`).

## Additional destinations

Named teams: table `02073380` indices0x4e–0x9b. Organization cells (0202d9c0/0202da90), paired
labels (020260b8/0202610c), and team selector (0202eb08/0202ee50) all use80×16; the information namebar
uses256×16 with31-byte transport. The targeted80 px ruler is visible in both organization headings
at `work/qa/team_width/map_team/final.png`. The complete caller-domain review is in `native-domains.md`.

The four special pool names (indices0x9c–0x9f) share80px organization headings. Exact orphan
selectors3/4/0x36, skipped action header2, unreachable action0x0f and intermediate area field
`02074746` are excluded with full consumer/domain evidence in `native-domains.md`.

Temporary map notifications are256×32 at x0/y80, centered for all modes0–2. They disappear at
frame120, so the native-call probe captures60frames after initialization. The alphabetic ruler
in `work/qa/notification_width/final.png` fills/clips at both screen edges. The QA-only thunk
preserves registers and flags, invokes the actual0202305c, restores its one-shot AreaInfoUpdater
hook and replays the displaced instruction. It checks scratch is unused; no release bytes change.
Materiel uses `%s%d` at020350ec and rejects nonpositive signed32-bit values at020350cc; lint checks
the widest positive value and the31-byte stack limit. Reorganization checks the whole team-name
concatenation and63-byte stack limit. No fixed eight-character name placeholder remains.

The new trait allocations passed a read-only exhausted-pool guard at02044a60 from cold boot on
map_unit, prep_upunits and prep_assign (`work/qa/alloc_*`),1200frames each, with no failure.

Native162's selector is reached by `BASKET_PROBE=true` on the same QA thunk, with `HOLD_BASKET=true`
from `width_scenes.lua`. The normal wrapper0205a4d8 passes an input structure with mode byte+2 to
02057730, which allocates/initializes its own0x8c object. The hold changes only input processing,
not constructors or drawing. Ruler proof: `work/qa/basket_native/final.png`; the160px title clips
at x48/207. Basket labels have80px fields with local2px offset and decorative sprites; a conservative
56px unobstructed bound is enforced instead of the nominal80px. Existing level-up consumers are wider.
The initial st01_after route never reached this selector; its BasketA level-up is a different screen.

Yes/No suffix020747f4 is appended at0204f14c–0204f15c when dialog flag0x10 is set. It has no standalone
surface: lint composes it with both map prompts and all four save confirmations before width/byte checks.
The smallest host remains176px. Layout spaces remain checked and the fixed cursor alignment is visible
in the normal save route.

Retirement headings are128×16 at x16/y0 (constructor020517fc–0205182c, draws02052030/02052404).
Both native ruler shots show127px of ink ending at x142: `work/qa/retirement_width/characters.png`
and `final.png`. The normal purchase/retirement route and its guarded QA-only patches are documented
in `retirement-route.md`; it uses a real purchased character rather than fabricated record entries.

## Save-probe initialization gotcha

The cold developer-stage warp with a blank64KiB battery image reaches the backup-write error on
**both** original and translated ROMs (`work/qa/save_original_blank`, `work/qa/save_blank`). A save
generated by the original game lets the same translated route complete, and `load` reaches its list.
Use `emu.py --sav` with that generated save for these probes; it copies the input into the run and
does not modify the source. Merely padding a blank DSV to the known size does not initialize the game.
This is a debug-route limitation, not evidence that the translation broke normal saving. The list
measurement comes from the actual load screen, not the confirmation/warning/error dialogs.
