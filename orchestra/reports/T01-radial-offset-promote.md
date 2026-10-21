status: partial

summary:
- Round 5 attribution and repair are complete: the three forbidden exact→refusal routes are exact again.
- The guard is `RenderWorld:generic-world-not-admitted`, not the Offset work budget.
- Preserve the pre-expansion Zoom dispatch when newly covered controls fail the generic world contract; F08 worker selection remains unchanged.
- 37 cases / 74 routes reproduce the base statuses and raw hashes: 61 exact, 2 existing mismatches, 11 refusals.
- Full promotion remains unaccepted: this short round did not repeat 390 / finish 9,645 / rerun seed-1 n=500 or rebaseline the corpus.

facts:

Round-5 scope is the orchestrator's latest instruction. The earlier merge and
Offset promotion already exist on this branch. No new merge, budget change,
worker rebuild, expectation edit, corpus rewrite, or release-gate edit occurred.
The previous Round-4 report is available at
`git show ee80fabc:orchestra/reports/T01-radial-offset-promote.md`.

Bindings in `T01-round5-dispatch.json`:

- Base `95b185eb` source: `66ed2aeb5132e0a5670b3801a781e8d3e5a77c142533911c9b497b1b4b30db85`.
- Before repair `ee80fabc` source: `7cc086b942e9febe858c1a451d2047224bcbda1dc6e2163d79fdf4a7da5d57ea`.
- Repaired production: `bbe3731138805156ed487136e70dad5c39731fc560a284956b9f47e44d0297d8`.
- Offset worker: `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
- Original AEX: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.

The committed verification command below exited 0. It first replayed **18/18**
recorded original-AEX hashes from Strength, Rotation-neutral and Gain, then built
base / before / after with the existing public compiler helper. No experiment
bypass was enabled. It measured the two unreduced Round-4 witnesses plus all 35
saved corpus cases against the same calibrated original-AEX worker. Builds and
raw scratch frames were deleted. The adapter also records its older six-row
calibration (4/6, the same PF32 reference epoch limitation as Round 4); those older
PF32 hashes are not used as acceptance truth or claimed as production fixes.

`Adapter.candidate` sets `OLM_REFUSAL_TRACE` for every route. Both unreduced
witnesses returned 516 on both before-repair routes, with the exact trace
`RenderWorld:generic-world-not-admitted@5362`. The fresh AEX runs succeeded,
with intact guards and clean sessions. No work-budget guard was reached.

Cause from the source and witness values:

- #193: PF16 Zoom, 12×8, Strength29, Outer Max/0, zero Size/Noise variation.
  Input/output rowbytes are 103/97; both are odd and violate the generic typed
  world alignment test. The old generic Offset predicate excluded Max/0;
  promotion included it and imposed that world test before the existing Zoom
  renderer could run. Both repaired routes reproduce all 768 AEX bytes.
- #425: PF32 Zoom, 14×18, Outer Add/5, zero Size/Noise variation. Classic's
  output rowbytes are 229 (not float-aligned). Independently, 696/1,008 input
  channels fall outside [0,1]; the first is word1 = 5.17056941986084. Thus the
  generic SDR test excludes this input even when Smart stages aligned output.
  Add/5 previously selected the older Zoom dispatch. Repaired Smart reproduces
  all 4,032 AEX bytes using F08's worker selection.

The production repair preserves the old generic Zoom Offset ownership boundary
(Outer Add/0 or Max/Override 2/4, Inner Add/0). If a newly included Zoom profile
fails generic world admission, its existing typed Zoom renderer decides admission
and dispatch, as on the base. Generic-admitted worlds retain the promoted path.
Previously generic-owned Zoom requests and all Rotation requests retain the
world guard and budget. There is no pixel-coordinate, geometry or witness-hash
special case, and no change to numerical kernels or F08.

E=exact, M=mismatch, R=refusal. All current rows below are fresh measurements;
“before” means the promoted candidate before this repair, not the old saved
corpus expectations.

| Suite / route | Base 95b185eb | Before repair | After repair |
| --- | --- | --- | --- |
| Unreduced #193 Classic | E | R 516 | E, same bytes |
| Unreduced #193 Smart | E | R 516 | E, same bytes |
| Unreduced #425 Classic | M | R 516 | M, same bytes as base |
| Unreduced #425 Smart | E | R 516 | E, same bytes |
| Saved 35-case corpus Classic | 23 E / 1 M / 11 R | 23 E / 12 R | 23 E / 1 M / 11 R |
| Saved 35-case corpus Smart | 35 E | 35 E | 35 E |
| Combined 74 routes | 61 E / 2 M / 11 R | 58 E / 16 R | 61 E / 2 M / 11 R |
| Worker recorded-hash calibration | — | — | 18/18 exact |
| Existing smoke tests | Same UI assertion fails | Round 4: 10 pass / 1 fail | 10 pass / 1 fail |
| Offset 390 | Historical base differs | Round 4: 390 E / 2,340 exact replays | Not rerun this short round |
| Retained 9,645 | Historical 9,645 E | Round 4: 1,056 conditions / 6,336 replays reported | Not completed |
| Seed1 n500 Classic | Round 4: 85 E / 1 M / 413 R / 1 U | Round 4: 137 E / 362 R / 1 U | Full campaign not rerun |
| Seed1 n500 Smart | Round 4: 109 E / 390 R / 1 U | Round 4: 180 E / 319 R / 1 U | Full campaign not rerun |

The current 74 route states and raw hashes all equal base. All 58 before-repair
exact routes also retain their hashes. The three forbidden routes are recovered:

- #193 AEX/base/repaired Classic and Smart:
  `61419588ac096ac05cd390e83bc6a71aa4f6db1c7b50b1d36ab130dc272ccde8`.
- #425 AEX/base/repaired Smart:
  `8405927c8b78605ecd5b76dd15eb2a7b5d0b85df52ce708a410305069cd117dc`.

Policy / residual mismatches, each listed separately:

- Unreduced #425 Classic recovers the base's known wrong output, rather than
  becoming newly exact: 520 differing bytes, first byte16; output
  `3be601058ea8a661745bda9e8d090ffee90ac05a1e5d21bb9bdef628ab7846b6`.
- Reduced saved `seed1_case000425_df3690c920ab.json` Classic likewise recovers
  the base mismatch: 90 differing bytes, first byte80; output
  `e6fc9f007de8a3a8427b8626113abb2d35e7520b1f83ade411b925850aa67945`.

These are base M→M, allowed by the Round-4 base-relative rule. Relative to the
intermediate promoted candidate they are R→M; they are explicitly not claimed
as correctness improvements. No additional mismatches or base-exact losses were
observed. The restored Classic behavior remains a follow-up defect.

The budget cap remains 350,000,000. Estimated-work comparisons and cap-removal
proposals from conditional step 2 are inapplicable because step 3's other-guard
condition was confirmed. Recorded timings are subprocess wall measurements,
not isolated kernel benchmarks; no budget diagnosis is inferred from them.

`validate_radialblur_tests_T01.py` exited 1: 11 tests, 10 pass, 1 failure, 0 errors.
Passing tests include generic ASan/UBSan, budget, Type3 sanitizer, Smart world
contract, Size/Noise EffectMain, and typed geometry guards. The sole failure is
`test_windows_control_types_and_ui_ranges_are_preserved`, which expects Thickness
`PF_Precision_HUNDREDTHS, 0, 0` but the source has `0x40`. Executing that same
function with SOURCE loaded from `git show 95b185eb:...` also raises AssertionError.
No UI expectation was edited. These sanitizer tests cover their existing matrices,
not the restored odd-stride witnesses. `git diff --check` passes.

inference:

The measured loss of exact output was dispatch ownership theft from the older
Zoom path, not an overly conservative budget. Restoring its pre-expansion entry
conditions is sufficient for the reported regressions and the saved corpus.
The unchanged generic-admitted path suggests the prior Offset gates should be
retained, but that is an inference, not a replacement for rerunning the full gates.
No new Windows-native / AE-host exactness or arbitrary HDR/odd-stride coverage
is claimed from these bounded fake-host measurements.

changed_files:

- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: preserve older Zoom dispatch for newly
  covered Offset profiles outside generic world admission.
- `tools/fuzz/verify_radialblur_offset_round5_T01.py`: reproducible bounded
  calibration, three-source replay and refusal attribution; no corpus writes.
- `orchestra/reports/T01-round5-dispatch.json`: 37 cases, three sources, both
  routes, hashes, guards, timings, provenance and 18 recorded-hash calibrations.
- `orchestra/reports/T01-round5-tests.json`: unchanged existing test outcomes.
- `orchestra/reports/T01-round5-verify.log`, `T01-round5-tests.log`: small logs.
- `orchestra/reports/T01-radial-offset-promote.md`: this Round-5 report.

verify:

Run from the worktree root, using a fresh disposable scratch subdirectory:

```sh
export TMPDIR="$PWD/orchestra/state/T01-radial-offset-promote/round5-recheck"
mkdir -p "$TMPDIR"
probe_python='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
worker=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
"$probe_python" -u tools/fuzz/verify_radialblur_offset_round5_T01.py \
  --worker "$worker" --scratch "$TMPDIR/verify" \
  --report "$TMPDIR/dispatch.json" > "$TMPDIR/verify.log" 2>&1
"$probe_python" tools/emulation/validate_radialblur_tests_T01.py \
  --report "$TMPDIR/tests.json" > "$TMPDIR/tests.log" 2>&1
git diff --check
```

Expected: verification exits 0, 18 calibration successes, 37 completed rows,
three restored exact routes and the table above. Smoke tests exit 1 for only
the pre-existing Thickness string assertion (10 pass / 1 fail). `diff --check`
exits 0. Actual execution used `round5` instead of `round5-recheck`, and retained
the two JSON reports in `orchestra/reports/`; all other arguments were identical.
The worker is used by absolute path and MAIN remains read-only. All individual
new evidence files are below 2 MB; ticket scratch remains below 5 GiB.

next:

Round-5 repair is reviewable, but do not mark the overall promotion accepted.
Resume the 390 and 9,645 gates with `--jobs 2`, then seed1 n500 with the same
calibrated worker. Rebaseline only after the complete base-relative acceptance
check. Preserve both unreduced witnesses: corpus-only replay misses the original
exact-loss cases. Separately investigate the existing Classic #425 mismatch and
the stale UI flag assertion; neither was changed in this short round.
