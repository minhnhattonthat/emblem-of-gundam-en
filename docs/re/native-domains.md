# Native selector and rendering domains

Independent read-only review, 2026-11-01. Reproduce disassembly with `tools/armdump.py`.
The following evidence backs the exact classifications in `tbl/windows.json`.

**Assessment: the native evidence supports excluding the three orphan labels and the dormant area field for legitimate game state, and maps all four special pool names to the measured 80 px organization headings. No concrete additional destination below 80 px was found.** Native VM wrappers do not enforce team-number bounds; this is a valid-state classification, not exhaustive verification of every script assignment.

Inspection was read-only. No files, ROMs, emulator sessions, agents, orchestration, or external services were changed or started. The ROM SHA-1 is `c60906c2084281daf2c948b17443c25040f3d365`; its decompressed ARM9 matches `work/arm9_jp.bin`.

**1. Complete classification of the 41 accessor calls**

I rescanned main ARM9 and correctly mapped autoload sections. There are **41 direct branches** to `0203AB10`, no stored pointer to that accessor, and one table-base reference: `0203AB1C → 02073380`.

All selector values below are hexadecimal.

| Accessor call PC(s) | Valid selector domain |
|---|---|
| `020293EC` | `02` |
| `020294CC` | `{08,0A,0B,0D}` |
| `020295C4` | `01` |
| `02029634` | `{1F,20,21,22,23}`; existing debug-menu QA patch additionally admits `25` |
| `020297B8 / 020297DC / 020297FC` | `33 / 34 / 32`, respectively |
| `0202B874` | `1C` |
| `0202B8B4` | `{1D,1E}` |
| `0202DA90` | `{00} ∪ [4E,67] ∪ [82,9F]`; organization selector explained below |
| `0202F838` | `2A` |
| `0202FA24 / 02031FD4` | `35` |
| `02031818` | `31` |
| `020328B4` | `07` |
| `02034774` | `57` |
| `020350D8` | `2F` |
| `02035A08 / 02035A54` | `38 / 37` |
| `02035AE8 / 02035B10 / 02035B38 / 02035B68` | `2C / 2B / 2D / 2E` |
| `020388D4 / 020388E0` | `26` |
| `02038BAC / 02038BC4 / 02038BD4` | `28 / 29 / 27` |
| `02038E78 / 0204DB38` | `39 + {1,2,4,5,7}` |
| `02038E88 / 0204DB48` | `39 + {0,2,3,7…19}` — additions in this row are decimal |
| `02038E98 / 0204DB58` | `39 + {0,2,6,12,14…20}` — additions in this row are decimal |
| `020394E4` | `[4E,81]`, explicit 52-iteration loop |
| `020395F8` | `[4E,81]` for valid battle-team records |
| `0203B2B8` | `05` |
| `0203B334` | `{12,11,10,13,14,15,17}` |
| `0203B444` | `06` |
| `0203B4A8` | `{1B,19,1A,18}` |
| `0206BBFC` | `30` |

The six trait calls use the three signed-halfword fields in the 141 unit records. Their combined valid values are decimal `0–20`, giving selectors `39–4D`.

The action selector is closed natively: `020292F8` returns `1–6`; `02029478` supplies `7` for the other case. Rows at `02072016` select action IDs `{1,3,4,6}`, which `02072004` maps to `{08,0A,0B,0D}`.

**Battle-team numbers are 0–51, not 0–77 or 0–81.**

The allocation and initialization establish this precisely:

- `0203415C–02034174` allocates and clears the containing `0x2D20C`-byte runtime object.
- `02032450–0203245C` clears **`0x5FE0` bytes** starting at runtime base `+0x34`.
- `02032460–02032484` initializes **52 records**, runtime stride **`0x1D8`**, each pointing to a saved record of stride **`0x26`**, starting at save base `+0x151E`.
- `52 × 0x1D8 = 0x5FE0`. The team region ends exactly at runtime base **`+0x6014`**, where the next record family begins.
- `02039630` calculates `runtime_base + 0x34 + team_number × 0x1D8`; it performs **no bounds check**.
- `020395A8` dereferences that record’s backing pointer and clears both records **before** selecting `team_number + 0x4E`.

The three callers of `020395A8` are:

| Call PC | Domain |
|---|---|
| `02034734` | Constant team `9` |
| `0203A278` | Organization commit loop `0–25`; bound at `0203A430` |
| `0203A548` | Team argument to `0203A4B0`, including VM natives 266/267 |

VM wrappers `0205D658` and `0205D68C` load integer arguments without checking them. Nevertheless, a legitimate team argument must identify one of the 52 initialized records. To select orphan indices `03`, `04`, or `36` through this path would require team numbers **−75, −74, or −24** respectively. Those already address and clear memory before the team array. They are not additional valid team-name cases.

Thus the unclosed script-local analysis is **not a concrete orphan-label rendering path**. Proving that every script assignment respects the native precondition would be additional script correctness work; I found no legitimate out-of-range producer establishing such a failure.

**The four special names belong to the separate organization pool.**

Organization storage begins at runtime base `+0x2B614`; `02039C5C` clears its `0x1A2C` bytes.

- `02039CA0–02039CF8` initializes **30 organization slots**.
- `02039D14–02039D5C` enables slots **26–27** for characters.
- `02039D6C–02039DB4` enables slots **28–29** for units.
- Character insertion searches only slots 26–27 (`02039DF0–02039EB0`); unit insertion searches only 28–29 (`02039EF4–02039FE0`).
- Ordinary team-ID assignment at `0203A0B0` receives slots below 26 from its four callers. The special slots retain zero in the team-ID array.
- Organization navigation wraps within 30 slots at `0202C970` and `0202C9B4`; selection reaches field `+0x214` through `0202CCA4` and the navigation functions.

At `0202DA6C–0202DA90`, the heading selector is:

```text
slot == -1             → index 0
team_id[slot] != 0      → 0x4E + slot
team_id[slot] == 0      → 0x82 + slot
```

Therefore:

| Slot | Index | String address | Destination |
|---:|---:|---|---|
| 26 | `9C` | `02072D2C`, Character A | Organization heading |
| 27 | `9D` | `02072E1C`, Character B | Organization heading |
| 28 | `9E` | `02072ED0`, Unit A | Organization heading |
| 29 | `9F` | `02073128`, Unit B | Organization heading |

All four pass directly from `0202DA90` to draw `0202DAA0`. Both heading surfaces are **10 × 2 tiles**, constructed at `0202D9DC–0202DA20`. This supplies the native mapping to the caller-reported **80 px measurements**; it does not rely on screenshot absence or require each special name to have appeared individually.

**Resulting exclusions and limits:**

- `02073074` / index `03`, `0207308C` / index `04`, and `02073020` / index `36`: **unused within the valid native selector domains above**. Each string has only its accessor-table pointer.
- `02072D5C` / index `02`: **assigned but not drawn**. `020293FC` sets flag `2`; `02025308–02025310` skips header text and `02025518–02025520` skips header artwork.
- Indices `9C–9F`: **80 px organization-heading mapping supported**.
- No additional concrete team-name destination below **80 px** was found. Retain the six established destinations and their transport constraints, including the **31-byte namebar field** and **63-byte complete reorganization expansion**. This pass does not claim a formal whole-program proof over every alias of a team-record pointer.

**2. Intermediate area field `02074746`: dormant data**

**Exclusion is supported for the pinned native consumers.**

The only literal pointer to `02074746` is at `0204D948`, used by the known writer. The only pointer to source `02074778` is `0204D944`. The writer copies three bytes at `0204D8D8–0204D8F4`.

I followed the exported shared-base accessor `0204D858`, including its indirect graphics consumers:

| Accessor call PC(s) | Consumption of shared structure |
|---|---|
| `02049DEC`, `02050D24`, `02055970`, `0205827C`, `02058F84` | Numeric/status graphic objects in offsets below `+0x200` |
| `02055504`, `02055EEC` | Stage-name text at `+0x204` |
| `020556D4`, `02055864` | Halfword at `+0x224` |
| `020559A4`, `02055ABC` | Scalar at `+0x200`; latter also uses graphic objects below `+0x200` |
| `02055A7C`, `02055B98`, `020593C0` | Scalars at `+0x278`, `+0x27C` |
| `02055DA8`, `02059588` | Text at `+0x226`, `+0x246`, `+0x256`, `+0x25E`, `+0x266` |
| `02058E2C`, `02058E3C`, `02058E48` | Return graphic-array pointers at `+0xF8`, `+0x128`, `+8` |

These account for **all 19 direct accessor calls**. Neither the accessor nor the secondary pointer-returning function `02058E20` has a stored function pointer.

The secondary exporter has five callers—`02058E74`, `02058EB0`, `02058EEC`, `02058F28`, `02058F58`—which pass its result to numeric renderer `02044E54`. That renderer selects decimal-digit objects. Related signed-number rendering uses `02045098 → 02044F40`, selecting digit/sign objects within the supplied graphic arrays.

The potentially broad indexed uses also remain below the text fields:

- Status icons use `+0x54 + 4 × index`, with index `0–31`.
- Numeric-label tables at `020749F4`, `020749FC`, and `02074A06` select graphic indices through **125**, relative to `+8`; the last object starts at **`+0x1FC`**.
- The shared graphic initialization/destruction loops operate on **126 four-byte objects** beginning at `+8`, ending before `+0x200`.

No full-record copy, retained whole-record pointer, or forwarding of the area-text span was present in these consumers. The remaining literal shared-base users manage resource headers or write the known fields.

Consequently, **`+0x24E` is initialized storage with no native render consumer**. Both its writable default and source `02074778` can receive a non-rendered exclusion. Preserve the existing seven-byte termination constraint on the preceding `+0x246` field; the exclusion does not authorize text to spill across that boundary.

**3. Basket selector: concrete QA-only hold patch**

The constructor `020577B4` has **no option-availability branch** around these draws:

- Title: `020578C4`
- Basket labels 0–3: `02057910`, `02057960`, `020579AC`, `020579FC`

All five draws execute during initialization. The inspected selector therefore does not deliberately omit its labels based on the stage-1 state.

For a geometry-preserving hold, patch this instruction in QA RAM before entering native 162:

```text
Address:   02057424
Original:  840097E5    ldr r0, [r7, #0x84]
QA word:   E3A00001    mov r0, #1
QA bytes:  0100A0E3
```

The following `cmp r0,#0; popne ...` returns before touch/button processing can accept or cancel the selector. Background updates preceding that guard, construction, text surfaces, artwork, and cursor drawing remain intact.

Equivalent instrumentation: after `02057334` initializes the selector object, set its word at **object `+0x84` to 1**.

This should retain the native title and all four labels for measurement. It is a static QA proposal, not emulator-verified here. If the held scene remains empty, check whether `020578C4` and the four label draw PCs execute; that would distinguish scene-entry/display-state trouble from rapid input dismissal.
