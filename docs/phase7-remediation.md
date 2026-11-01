# Phase 7 remediation — 2026-11-01

All Critical/Important findings from the phase7 review are repaired. Measured-width coverage is
complete: `tools/width_coverage.py --ids` exits0 with **zero unresolved lines**. The full check passes
all67 tests, including strict merged-script lint. Phase7 is complete; phase8 visual acceptance and
phase9 release packaging remain separate gates.

| Review item | Repair |
|---|---|
| I1 width coverage | Every changed player line selects a measured destination; exact non-player exclusions have native/record evidence. Runtime formats expand actual names, counters and suffixes before byte/pixel checks. The ordinary check and commit hook now enforce strict coverage; `--phase7` is the same check. |
| I2 ROM integrity | Exact component write plans check preimages, overlaps, pointer targets, relocated text and unchanged metadata. Container checks additionally reject changed header fields, checksums, filenames and padding. Builds validate before writing and emit516 component logs under `build/writes/`. |
| I3 stale baseline | Each process extracts the pinned original with the current extractor; stale disk caches cannot hide new IDs. Table/ID coverage is checked before iteration. |
| I4 glossary | Batch and merged-script lint share block-level required/Avoid checks and approved menu-only alternatives. Missing Kycilia restored; negative Amro regression retained. |
| I5 erased blocks | A whole nonempty source block cannot disappear through reflow without a committed keep-list ID. Legitimate redistribution still passes. |
| M1 whitespace | Source label padding normalizes fullwidth spaces to ASCII. Speech continuation indentation follows nonempty lines after reflow, with the documented Alex narration exception (D20). |

The first repairs were committed/pushed as `e94e1dc`. This continuation closes the remaining width
audit and native transport defects. Durable evidence is indexed in `docs/re/README.md`:

- `width-callers.md`: record-derived unused descriptions/series, debug-only consumers and shared fields.
- `native-widths.md`: measured native UI families, runtime inputs and buffer capacities.
- `native-domains.md`: all41 native label-accessor calls, valid team domains and dormant area-field consumers.
- `retirement-route.md`: independently reviewed, then emulated normal-purchase retirement capture.

No generic guessed ARM9 fallback is accepted. Exclusions waive width only, preserving translation,
encoding, control-code, glossary and whitespace checks. Dynamic names come from actual pinned records;
save details cover the unsigned32-bit frame counter; gallery rows include every valid environment,
direction and weapon number; notification and Yes/No host concatenations are checked in full.

Native fixes found while measuring:

- Three trait surfaces grew from80 to88px, retaining “Sub-Flight System” and their31-byte copy cap.
- Two fixed Japanese-sized literal loops now call the game's NUL-terminated copy helper. Exact
  instruction preimages and a255-byte destination bound are checked. The earlier count-only proposal
  was rejected because its odd tail read could overrun even-sized relocated allocations.
- The second Attack action now says “Fight”, matching D18. Widening its mode-2 table alone was rejected
  because the32px artwork would still clip.
- Earlier sound-button, gallery row and AREA INFO buffer repairs remain in the build.

Validation evidence:

- ROM: `build/eog_en.nds`,64MiB, SHA-1 `d48ac934d5ee96de573963c6080cff84f8cb2536`,
  built **2026-11-01 11:24:08 UTC**; exact integrity check passed.
- Smoke: `work/qa/native_remediation_smoke`, exit0.
- Full cold-boot tour: `work/qa/native_remediation_tour`, **373/373** routes at1200frames, exit0.
- Native allocation-exhaustion guard: map_unit, prep_upunits, prep_assign and retirement all pass.
- Targeted normal captures: basket selector and both retirement headings pass; rulers establish
  notification256px, basket labels56px conservative/title160px, and retirement headings128px.
- Final full test suite: **67 passed**,266.772s, exit0. Log: `work/remediation-final-check.txt`.

Fresh read-only visual pass of the targeted normal captures found complete Sound Effects buttons,
aligned save Yes/No choices, complete basket/retirement labels and intact unit/prep info screens.
This is a targeted phase7 verdict, **not** approval of every full-tour sheet. Existing phase8 issue
verdicts stay unresolved; combat graphics and the remaining graphics survey must be completed before
manifest approval. Phase9 still needs story verdicts, polish closure and a verified patch+README zip.

Probe gotchas to carry forward: WARP_DONE can precede actual task readiness, so retirement waits for
the assignment state and then180frames before A. Blank-save developer warps fail backup access on
both original and translated ROMs; use a game-generated battery copy for save/load probes. These
belong in the skill's emulator-QA reference; no skill files were modified. QA-only RAM patches and
ruler ROMs are separate from the release candidate.
