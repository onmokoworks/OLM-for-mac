status: blocked

summary:
- Re-measured seed-1 n300 Smart: 241 exact / 0 mismatch / 59 refusal, unchanged from C17.
- PF32 off-frame-center admission makes 12 campaign refusals exact, but fails an independent matrix; not promoted.
- Finite Rotation admission repeats four HDR/subnormal counterexamples; not promoted.
- Work-budget bypass makes two campaign refusals exact; no general budget change was validated.
- Stopped after two rejected admission hypotheses without a new first-divergent-stage boundary. No production cluster closed.

facts:

FACT: Started at `c4a0b92a535bd3c5c4141ffef1b0eaa7d8039ab5` on
`orch/C26-radial-smart-r4`. Read the shared guide, RadialBlur ledger restrictions,
compatibility plan, emulator GOTCHAS and radial triage/fix reports, particularly
C11/C17 and T03/T05/F08. All scratch is in this worktree's ticket directory.
No MAIN/cache/emulator write, worker rebuild, release-gate/ledger change, push,
stash, history rewrite or permission rejection occurred.

FACT: Original AEX SHA256:
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Pinned `radial_offset_reference_20261002` worker SHA256:
`93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
Source/core and harness bindings are in the accompanying evidence JSON.
The archived calibration remains 4/6; fresh original-AEX Smart raw hashes are
the comparison oracle. Native Windows UCRT/AE equivalence is not claimed.

FACT: The ordinary seed-1 command below completed 300 cases in 184.107 seconds.
Smart: 241 exact / 0 mismatch / 59 refusal. Original Smart: 279 ok / 20 reject /
1 budget. The 38 original-renderable refused rows split as follows:

| Guard | Count |
|---|---:|
| generic-world-not-admitted | 14 |
| smartrender-generic-budget | 8 |
| unadmitted-zoom-profile | 6 |
| type3-zero-noise | 5 |
| zoom-noise-plane-failure | 4 |
| host checkout | 1 |

FACT: The largest generic-world group includes known external math boundaries.
C11/C17 already trace the B680 scalar-tail `expf` import at RVA
`0xb760..0xb7b5`: length 10/index 8 returns `a5ed653d` in the host-expf reference
versus `a4ed653d` with double-exp-cast. This retained boundary is `ucrt-math`,
awaiting F28; it was not chased or changed here. New untraced mismatches below
are not automatically assigned to that cause.

FACT: Scratch-only PF32 center admission preserves all other guards. On the
38 rendered-refusal rows it gives 12 exact / 26 refusal / 0 mismatch, all
sanitizer-clean. Newly exact indices: 2,20,23,28,52,82,100,106,124,227,295,298.
The independent C11-derived center matrix has 72 PF32 references and three
layouts each: **207/216 exact, 216/216 clean**. Three inputs fail:

| Matrix index | Geometry / family / Center | Differing words | First word: AEX → Mac |
|---|---|---:|---|
| 62 | 11x7 Rotation / (5.5,-1/65536) | 4 | 120: `06bff53e` → `04bff53e` |
| 66 | 11x7 Rotation / (5.5,-5.75) | 1 | 11: `a703c63e` → `a803c63e` |
| 70 | 11x7 Rotation / (5.25,3.25) | 5 | 121: `6d3e993e` → `6c3e993e` |

All use Strength 4, Outer/Inner Fade 25/50 and Quality 1. Index 70 is an
in-frame control, not a newly admitted center. No claim is made that the center
predicate causes its numerical error. The matrix does not support unrestricted
PF32 center promotion; it does not establish a new first-divergent stage.

FACT: A separate scratch hypothesis replaces Rotation's SDR-only input check
with finite-only input admission. The independent signed/HDR/subnormal matrix
has 72 references (Zoom controls included), three layouts each:
**204/216 exact, 216/216 clean**. These reproduce C11's four failed inputs:

| Matrix index | Geometry / profile / family | Differing words | First word: AEX → Mac |
|---|---|---:|---|
| 44,45,46 | 3x5 tiny / Rotation | 3 each | 25: `0000803f` → `00000000` |
| 62 | 11x7 HDR / Rotation with Fade | 3 | 28: `514b2846` → `4f4b2846` |

No arbitrary typed input was rounded into PNG and presented as the same trace.
No new first-divergent-stage value was obtained for either failed hypothesis.
The stop condition therefore prevents further numerical experiments this ticket.

FACT: The work-budget diagnostic ran before that stop decision, while the
center matrix was pending. It removes only the work cap, retaining the 1 GiB
memory bound. Of 38 rendered refusals, **2 exact / 36 refusal / 0 mismatch**, all
clean. Indices 48 (PF8 Rotation) and 104 (PF8 Zoom) become exact. Other former
budget rows reach existing downstream guards: 62/108/148/235 generic-world;
76/77 invalid noise-plane generation. Removing a resource cap is not a safe
production rule. No budget admission or fresh-seed proof is claimed.

Production verification and corpus accounting:

| Check | Result |
|---|---|
| Production source/core versus starting revision | identical |
| Seed-1 ASan/UBSan production replay | 300/300 same and clean |
| Existing smoke tests | 8/8 pass |
| Corpus Smart before → after | 35 exact → 35 exact, identical hashes |
| Corpus complete saved result objects | 35/35 unchanged |
| Corpus rebaseline | unnecessary; no changes |

The sanitizer replay and smoke tests are closeout verification, not additional
hypothesis testing. No fresh seed was run because neither numerical admission
survived its independent matrix. No base-exact output changed.

inference:

INFERENCE: Existing generic-world refusals cannot be lifted together based on
seed-1's exact pockets. Center, finite input, imported math and typed Rotation
boundaries remain separate. The inherited UCRT boundary explains why a host
math substitution would be an invalid shortcut, but does not prove the cause
of every newly observed output delta.

INFERENCE: The work estimate may overcount Zoom propagation because the render
loops bound propagation by remaining radial extent. A separately proven
geometry-based work upper bound is a promising follow-up for case 104. This
was inspected in code, not implemented or accepted in this ticket.

changed_files:
- `tools/fuzz/probe_radialblur_smart_C26.py`: reproducible scratch-only center, finite-Rotation and work-cap experiments.
- `tools/fuzz/verify_radialblur_centers_C26.py`: PF32 independent center matrix using original AEX and sanitizer/layout verification.
- `tools/fuzz/audit_radialblur_C26.py`: bind measurements, rejected matrices, source identity and unchanged corpus.
- `orchestra/reports/C26-radial-smart-r4.evidence.json`.
- This report. No production or corpus files changed.

verify:

Run from this worktree, with a new `$S` (experiment directories are exclusive).
The finite source was originally generated by importing the same
`candidate_source('finite-rotation')`; the snapshot command below reproduces it.
All long commands redirect output to scratch logs. Use jobs 1 throughout.

```sh
PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
W='/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker'
S="$PWD/orchestra/state/C26-radial-smart-r4/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S"
"$PY" -u tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 1 --worker "$W" --case-timeout 30 --budget-minutes 120 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/base-build" --corpus "$S/corpus" --report "$S/base.json" > "$S/base.log" 2>&1
for E in centers32 budget; do
  "$PY" -u tools/fuzz/probe_radialblur_smart_C26.py --experiment "$E" --campaign "$S/base.json" --output "$S/$E" > "$S/$E.log" 2>&1
done
"$PY" tools/fuzz/probe_radialblur_smart_C26.py --experiment finite-rotation --snapshot-only --output "$S/finite-source" > "$S/finite-source.log" 2>&1
"$PY" -u tools/fuzz/verify_radialblur_smart_C11.py --source "$S/finite-source/experiment.cpp" --finite-inputs --all-depths --independent --output "$S/finite-matrix" > "$S/finite-matrix.log" 2>&1
# Expected exit 1, 12 failed layouts. Continue explicitly.
"$PY" -u tools/fuzz/verify_radialblur_centers_C26.py --source "$S/centers32/experiment.cpp" --independent --output "$S/centers32-matrix" > "$S/centers32-matrix.log" 2>&1
# Expected exit 1, 9 failed layouts. Continue explicitly.
"$PY" -u tools/fuzz/verify_radialblur_smart_C06.py --campaign "$S/base.json" --smoke --output "$S/production-verify" > "$S/production-verify.log" 2>&1
"$PY" -u tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 1 --worker "$W" --case-timeout 30 --scratch "$S/replay-build" --corpus "$S/replay-corpus" --report "$S/replay.json" > "$S/replay.log" 2>&1
"$PY" tools/fuzz/audit_radialblur_C26.py --state "$S" --output "$S/evidence.json" > "$S/audit.log" 2>&1
```

Expected audit: unchanged 241/0/59; production 300 same/clean; smoke 8; corpus
35 unchanged; finite matrix 204/216 and center matrix 207/216 exact. Oracle
wall-time budgets and rendered-refusal diagnostic counts may vary; never count
a timeout as an exact result.

next:
- F28 owns the retained B680 scalar-tail `ucrt-math` boundary.
- A typed raw trace path is needed for finite Rotation's subnormal/HDR witnesses;
  the pinned worker exposes watches only through PNG transport. Do not rebuild
  the worker without a ticket authorizing that infrastructure change.
- Prove a tighter Zoom work bound from clipped radial propagation, then apply
  seed-1 plus a fresh seed, independent boundaries and sanitizer acceptance.
- Type3/NV0 host allocation and prepass ownership remain C17's open boundaries.
