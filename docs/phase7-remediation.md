# Phase 7 remediation checkpoint — 2026-11-01

The phase is **not complete**. Important finding I1 still has 286 lines without measured width coverage;
the strict phase gate rejects them. Phase 8 acceptance and release packaging must wait for that gate.
No owner decision is needed to continue the technical work.

| Review item | Result |
|---|---|
| I1 width coverage | Partly repaired. Known ARM9 chart/menu addresses now select their measured variants; new list, extras, and map-name measurements are enforced. Unresolved or guessed coverage fails `lint.py` by default and `check.py --phase7`. The unit suite's explicit content-only audit is diagnostic, not phase acceptance. |
| I2 ROM integrity | Replaced broad ARM9/BBQ permissions with planned exact writes, expected original bytes, overlap checks, and exact relocated targets/content. All three review mutations are regression tests. Builds validate the result before writing the ROM and emit 516 component write logs under `build/writes/`. |
| I3 stale baseline | Authoritative extraction reads the pinned original ROM with the current extractor each process; the old disk cache is ignored. Table and ID coverage must match before any zip/get loop can skip a string. Both added ARM9 IDs are regression-tested with an old cache present. |
| I4 glossary | Batch and merged-script lint share the same block validator, including required forms and Avoid spellings. Menu-only approved alternatives use an optional sixth glossary column. A dropped Kycilia name was restored; `Amro` is a negative regression. |
| I5 erased blocks | Reflow can leave a line empty, but a whole nonempty source block cannot disappear without a committed keep-list ID. Tests cover a single erased line/block and legitimate reflow. |
| M1 whitespace | Leading/trailing label padding is checked with fullwidth-to-ASCII normalization. Speech indentation follows nonempty lines after reflow; quoted narration is distinguished by source layout, with the Alex acronym exception recorded by ID (D20). |

Two visible issues found while closing coverage were fixed: the sound submenu now uses the medium button
layout so `Sound Effects` is whole, and gallery labels use `Land` instead of `Ground` to fit the measured
row without abbreviating Southeast Asia. AREA INFO strings now have a 31-byte native-copy limit as well
as a pixel limit; the current longest name is 27 bytes. Music, SFX, gallery and unit-name paths also
enforce a 31-byte VM transport limit. The command-menu budget was corrected from 130 to 128 px.

A read-only caller review resolved 324 more lines: 263 description/series lines and 42 hidden debug
labels have evidenced non-player exclusions; 19 ARM9 labels now select measured destinations.
Exact record-derived selectors are regression-tested, since deduplicated pools do not follow index
parity. `docs/re/width-callers.md` records the native and script call evidence. Exclusions waive only
width checks, not the other content checks.

The integrity checker works in original component coordinates. ARM9 plans include individual string slots,
every original pointer slot, the exact appended text pool, autoload metadata, and unchanged relocated DTCM.
BBQ plans preserve executable opcodes/arguments except enumerated VM string-type bits and the one checked
sound-menu layout operand; type-7 indexes/pools and stage-name fields must match the source. Font/graphics
spans come from the approved deterministic rendering, never from whichever bytes the candidate ROM changed.
Resized component tails are normalized with FF only for `romdiff`; logical lengths are checked separately.

Reproduce the remaining work:

1. `python -X utf8 tools/width_coverage.py --ids` lists the 286 unresolved ARM9 lines.
2. Resolve their screen-specific destinations, including runtime format-argument limits; do not apply
   a broad fallback. Save/error-dialog dispatch evidence is in `docs/re/width-callers.md`.
3. `python -X utf8 tools/check.py --phase7` must exit 0 before the phase is declared repaired.
4. Resume the phase 8 graphics/combat work recorded in `docs/status.md`, then refresh manifests and perform
   a fresh visual pass. Existing round-one issue verdicts have not been turned into approvals.

Evidence is under `work/qa/coverage*`, `work/qa/area_bound`, `work/qa/sound_medium`,
`work/qa/remediation_smoke`, and `work/qa/remediation_tour`. The broad all-ARM9 stress image caused native
buffer overreads and timeouts in map/title scenes; those are probe failures, not evidence against the
normal build. Use targeted IDs for those fields. The new extras routes reach sound, music, SFX, battle,
and event lists without a user save.

Read-only review of the final source changes: the corruption cases are covered by negative tests; ordinary
test success is explicitly distinguished from the failing strict phase gate. The remaining Important
finding is I1. No full-tour visual approval or release readiness is claimed.

Normal-build evidence: SHA-1 `07bc293ccb9b0d85dc298e16474fd194e2cf8428`, built 2026-11-01
09:58:02 UTC. Exact component integrity validation passed, the smoke run exited 0, and the cold-boot
tour completed 373/373 routes at 1200 frames. Completion of routes alone is not a visual approval.

Validation checkpoint: `tools/check.py` passed all 59 tests (297.747 s); strict `tools/lint.py`
exited 1 with exactly 286 unmeasured-width errors. Targeted follow-up routes live in
`tools/debug/width_scenes.lua` (load between `scenes.lua` and `warp.lua`); their probe ROMs and
shots do not replace the normal-build tour or its savestates.
