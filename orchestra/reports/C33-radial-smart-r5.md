status: partial

summary:
- Closed PF32 off-frame-center admission against the current F32 original-AEX oracle.
- Seed 1 Smart: 240/0/59/1 -> 252/0/47/1; fresh seed 2: 240/0/60/0 -> 250/0/50/0 (exact/mismatch/refusal/uncompared).
- All 480 baseline-exact campaign hashes and all 35 saved corpus results are preserved; 22 newly admitted rows are exact.
- Independent center matrix: 72 references, 216/216 exact and sanitizer-clean layouts, including C26's three former failures.
- Further cluster investigation is in progress; no resource-cap change.

facts:

FACT: Started at `c1d1f1943e2e3c9ab6e62e1094ba279643f73385`, branch
`orch/C33-radial-smart-r5`. Read AGENT_GUIDE, RadialBlur ledger restrictions,
compatibility plan, GOTCHAS, radial triage/fix reports (especially C17/C26), and
F10/F12 admission methodology. MAIN/cache/emulator sources remain read-only.
No worker rebuild, release-gate/ledger edits, push, stash or history rewrite.

FACT: F32 worker SHA256 is
`c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
Original AEX SHA256 is
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Compact measurements and provenance are in `C33-radial-smart-r5.evidence.json`.
Fresh original CPU AEX output is the oracle; archived calibration is 4/6 and
is not used as a replacement for fresh output. Native Windows/AE equivalence
is not claimed.

FACT: The requested ordinary seed-1 n300 baseline completed in 169.3893 seconds,
with Smart 240 exact / 0 mismatch / 59 refusal / 1 uncompared. Original Smart
was 276 ok / 20 reject / 4 budget. Case 4 is the uncompared row. Of 36
AEX-rendered refused cases: generic-world 14, work-budget 8, Zoom profile 5,
Type3/NV0 4, noise-plane failure 4, host checkout 1. Work-budget is counted
without bypassing or changing the cap.

FACT: The scratch PF32 gate experiment adds PF32 to the existing off-frame
center predicate, retaining signed-16.16 center bounds, topology, source
profile, negative-noise-phase and resource guards. It executes the same
original-radius-builder path already established by C11. No arithmetic,
writer, sample value, or per-case rule is changed. C26's independent PF32
matrix now passes all 216 layouts, including indices 62/66/70 that previously
failed. No new first-divergent-stage claim is made from this output agreement.

| Check | Before | Center candidate |
|---|---:|---:|
| Seed 1 Smart E/M/R/U | 240/0/59/1 | 252/0/47/1 |
| Seed 2 Smart E/M/R/U | 240/0/60/0 | 250/0/50/0 |
| Baseline-exact hashes retained | 480 | 480 |
| Saved corpus complete results | 35 | 35 identical |
| Corpus Smart exact | 35 | 35 |
| Independent PF32 center layouts | — | 216 exact / 216 clean |

FACT: Both candidate campaigns run ASan/UBSan and report zero Smart sanitizer
findings. The initial production sanitizer replay is 300/300 same and clean.
The eight legacy smoke tests return 3 pass / 5 build failures: all five fail
linking `_ucrt_atan2f` / `_ucrt_expf` because those standalone test commands do
not link libucrtmath. They fail on the starting production source, before the
admission edit. Public harness builds and independent sanitizer renders link
the library successfully. No smoke failure is counted as a numerical pass.

FACT: Two initial diagnostic builds failed because relocating the plugin source
also required resolving its quoted includes and companion header/strings files.
The committed driver resolves includes and links companion files to this
worktree. Failed builds produced no numerical evidence. Corpus expectations
were not rewritten; both before and candidate replay match all saved results.

inference:

INFERENCE: The earlier center-matrix rejection no longer applies to the current
F32/UCRT port pair. The general off-frame center admission is supported by two
seed campaigns, the independent boundary matrix and unchanged corpus. This
is bounded evidence, not a proof for every representable input. The original
C17/C26 expf observations are historical; this ticket does not attribute every
former difference to a particular import without a new paired trace.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: PF32 center admission only.
- `tools/fuzz/probe_radialblur_C33.py`: F32-bound scratch experiments, sanitizer matrices/campaigns and replay.
- `tools/fuzz/summarize_radialblur_C33.py`: compact measured provenance and comparisons.
- `orchestra/reports/C33-radial-smart-r5.evidence.json`.
- This report.

verify:

Run from this worktree. Use a fresh directory beneath the ticket state root;
individual experiment output directories must not exist. Long-command output
must be redirected as below. All campaigns use jobs 1.

```sh
S="$PWD/orchestra/state/C33-radial-smart-r5/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
B=c1d1f1943e2e3c9ab6e62e1094ba279643f73385
python3 tools/fuzz/probe_radialblur_C33.py --experiment production --source-revision "$B" --seed 1 --output "$S/base-seed1" > "$S/base-seed1.log" 2>&1
python3 tools/fuzz/probe_radialblur_C33.py --experiment production --source-revision "$B" --seed 2 --output "$S/base-seed2" > "$S/base-seed2.log" 2>&1
python3 tools/fuzz/probe_radialblur_C33.py --experiment centers32 --source-revision "$B" --output "$S/centers32-final" > "$S/centers32-final.log" 2>&1
python3 tools/fuzz/probe_radialblur_C33.py --experiment centers32 --source-revision "$B" --seed 1 --output "$S/center-seed1" > "$S/center-seed1.log" 2>&1
python3 tools/fuzz/probe_radialblur_C33.py --experiment centers32 --source-revision "$B" --seed 2 --output "$S/center-seed2" > "$S/center-seed2.log" 2>&1
python3 tools/fuzz/probe_radialblur_C33.py --experiment production --replay tests/fuzz_corpus/radialblur --output "$S/corpus-final" > "$S/corpus-final.log" 2>&1
```

Expected: matrix 216/216 exact/clean; two campaigns with the table above;
corpus 35/35 saved matches. Oracle wall-time/instruction-budget outcomes can
vary; preserve those observations instead of counting them as exact. The
original baseline used `python3 tools/fuzz/run.py --plugin radialblur --n 300
--seed 1 --jobs 1 --scratch orchestra/state/C33-radial-smart-r5/baseline
--corpus orchestra/state/C33-radial-smart-r5/corpus --report
orchestra/state/C33-radial-smart-r5/baseline.json`, redirected to baseline.log.

next:
- Complete separate PF16 Rotation center campaign qualification; its 36-reference/108-layout F32 matrix has passed, but it is not yet promoted.
- Keep work-budget refusals unchanged. Type3 missing-layer allocation/prepass remains C17's host-contract boundary.
- Investigate the remaining source-profile/noise-plane refusals under the ticket stop rule.
