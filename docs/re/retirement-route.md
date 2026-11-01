# Retirement capture route

**Emulator verification:** `work/qa/retirement_width` reached both native draw PCs from cold boot.
Both rulers show127px ink at x16–142, establishing the128px heading budget. The probe must wait for
shop mode2/first option62, then another180frames before A; WARP_DONE precedes actual task readiness.
Character and unit pool counts are guarded as zero before purchase. The purchase inserts one real
Fraw Bow entry; native retirement sees mask0/characters1/units0. Capture each heading after1200frames.
`work/qa/retirement_normal` exercises the same route on the release candidate with an allocation guard.

Independent read-only static review, 2026-11-01. QA implementation: `tools/debug/retirement_probe.lua`.

**Use the normal assignment purchase, then intercept its return.** This avoids inventing pool entries. Statically verified against original ROM SHA-1 `c60906c2084281daf2c948b17443c25040f3d365`; no emulator validation performed.

The callable retirement entry is **`02052a94`**, not `020517fc`.

- `r0`: ignored; the function allocates its own `0x7c4`-byte object.
- `r1`: eligibility mask; `0` accepts all otherwise eligible entries.
- `r2`: nonzero requests the initial fade.
- `02051bcc` checks eligibility before allocation. Empty pools return `0`.
- `020517fc` is inside initializer `020516d0`, with an established stack and object in `r4`.

**Suggested QA patches**

| Address | Original word | Replacement | Effect |
|---|---|---|---|
| `02030258` | `E3A00001` | `E3A01000` | Set retirement mask `r1=0` after assignment closes |
| `020302c0` | `EB001FB4` | `EB0089F3` | Replace `bl 02038198` with `bl 02052a94` |

`r2=0` is verified: assignment’s task wrapper sets it at `0203b1e8`, then returns through `02030258–02030260` without changing it. Retirement does not use the displaced `r0=1`.

**Cold-boot sequence**

1. Follow existing `prep_assign`.
2. Apply those guarded instruction patches. Supply a separate **16-bit Merit fixture at `02195b22`: `0000 → 002d`**.
3. Purchase the first character with A, dismiss the purchase notification, then press B to close assignment normally.
4. Capture Retire Characters after the retirement banner finishes. Press A once and capture Retire Units. Stop there.

Offline inspection of existing `work/states/prep_assign.dst` confirms: zero Merit, empty persistent pools, first option character **62 / Fraw Bow**, cost **45**, eligibility flags `0`, and nonzero portrait. Guard these conditions in the eventual probe. This requires **two instruction patches plus one funding write**.

**Normal-flow evidence**

- Purchase inserts the selected character through `02042424` at `0202ae8c`, then increments the pool count at `0202ae98`.
- B follows `0202a3e4–0202a400`, closing the assignment task and its graphics normally.
- The intercepted call ordinarily consumes the persistent pools through `02038198`; replacing it preserves the purchased entry for retirement.
- Retirement registers callback `02052a2c`, which initializes through `020529cc → 020516d0`.
- Normal character initialization reaches **`02052030`**, using heading `02074b18`.
- A transitions through `02052150–02052160` to unit initialization, reaching **`02052404`**, using `02074b30`. An empty unit pool still reaches this heading.

Treat this as a **capture-only candidate**, not a verified return-to-game route.

Optional findings: material notification `020350b0` reserves exactly **32 stack bytes**; `020350ec` formats `%s%d` using table index `0x2f`, which resolves to `02072c6c`. Yes/No suffix `020747f4` is appended at `0204f15c` when flags contain `0x10`; exhaustive host coverage was not established.

No files edited, agents spawned, or emulator sessions started.
