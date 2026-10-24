status: done
summary:
- Restored Smart request/result rectangles, inverse-size distance staging, and integer per-axis blur sizing.
- Realistic-v1 seed 1: 96 exact / 4 unavailable; seed 20261024: 100 exact. Zero Mac-only refusals or mismatches.
- Added 226 separately labelled geometry witnesses; 30 independent witnesses include expanded requests and reverse-asymmetric scales.
- Default seed 1/n300 has zero exact-to-non-exact regressions; all 147 existing corpus cases replay as saved.
- Smart sanitizer checks pass; the same 15 historical unit failures and 59 errors remain across 140 tests.

facts:

Base commit: `5bb598413d4a40fc8b23480c7bc3a1a6b036ff18`.
The original CPU AEX ran in the retained Unicorn workers. No oracle rebuild,
MAIN edit, installation, native AE run, release-gate edit, or ledger edit occurred.
Classic behavior was preserved; all 300 default Classic candidate output hashes
match the baseline, including its existing mismatches.

Identities:

- AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- F52c worker: `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
- Default F46 worker: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- Final plugin source: `0c49669c3c6393a4f1b3381263fc1ce38197a25742aef756beefe7d19cc7836c`.
- Final fieldgen source: `9a758fe4ba0b2da7f62d42f373439dec30f87a3964adca519793a4b837611525`.

Static findings, checked against read-only MAIN disassembly/decompilation:

1. Public command `0x17` forwards the output request unchanged, then unions
   checkout `result_rect` and `max_result_rect` through `FUN_181175fb0`.
   It neither forces a full output rectangle nor rejects downsample.
2. Typed owners reconstruct dimensions using uint32 world-size × denominator,
   FLOAT32 conversion/division by numerator, and truncation. The supplied
   `0x18117176d..0x1811717bb` block and PF8/PF32 owners agree.
3. `FUN_181174760` allocates the reconstructed mask, uses nearest-neighbor
   resize, computes precise L2 distance, then linearly resizes distance back
   **before** threshold and normalization. Raw UI thresholds are unchanged.
4. Blur apertures use integer multiply/divide separately for X and Y, then
   `2*radius+1`. Box/Gaussian consume both apertures; Median/Bilateral retain
   their square/horizontal aperture behavior.
5. Typed owners copy the packed field prefix into the output using output row
   width. The iterator consumes source local coordinates. The port reproduces
   this ordering for smaller allocated outputs, rather than inventing a spatial
   crop of the completed full-size image.

Selected original excerpts and the complete decompilation hash are in
[P02b-evidence/static.json](P02b-evidence/static.json).

Implementation preserves Classic scale handling and thresholds. Smart uses
validated independent source/destination layouts, tight staging for unaligned
rowbytes, and commits only requested active rows after parameter/layer cleanup.
Original-style result negotiation bounds expanded requests to input content;
this does not claim an output allocation larger than the original's max result.
Extent hints and pixel aspect are not used in the numerical body; the retained
original comparisons include their varied values and nonzero result origins.

Measurements (serial oracle calls, 10-second call limit):

| Campaign | Smart exact | mismatch | Mac-only refusal | unavailable |
|---|---:|---:|---:|---:|
| Baseline seed 1/n100 realistic | 10 | 3 | 83 | 4 |
| Final seed 1/n100 realistic | 96 | 0 | 0 | 4 |
| Final seed 20261024/n100 realistic | 100 | 0 | 0 | 0 |
| Independent geometry witnesses | 30 | 0 | 0 | 0 |
| Default seed 1/n300, baseline and final | 290 | 0 | 0 | 10 |

Unavailable takes precedence over candidate refusal. Seed-1 indices
10/31/53/55 are the retained unavailable cases (timeout or guest rejection),
not evidence of faithful original PF errors. They remain in campaign evidence
but are excluded from the new replay corpus.

The geometry-only intermediate probe made index 12 exact: both output rectangles
are `[1,0,2,1]`, raw SHA-256
`3c99d30a8b0d8e7d4f9b6cc08ca6bc061ec9f5d08cd1bc7f5f9b2d6d51d47f42`.
Its index-0 alpha was still Mac `b4` versus original `cd`; restoring the actual
resize sequence removed this numerical boundary. The resize probe's first 20
cases were 19 exact / 1 unavailable. No two-refuted-hypotheses stop condition arose.

The initial fresh-seed run had one refusal, index 21: PF32 1×1, Gaussian UI Size
2550, downsample 1/3, sampled radius 850. The original returned normally, raw
SHA-256 `374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb`.
The Mac's 500-radius Gaussian admission ceiling caused the refusal. Gaussian now
uses the existing 4096 UI bound (as Box does); Median retains its existing bound.
Final-source replay makes this witness exact. Independent cases also exercise
large Gaussian apertures and the reverse-asymmetric X1/3-Y1/2 geometry.

Commands actually run are the verification commands below, plus the baseline
campaign (`--label baseline`), the two 20-case intermediate probes, and baseline
unit discovery. Long outputs went to ticket scratch. An initial resize build
missed a forward-declaration signature, and the first sanitizer wrapper passed
compiler flags to the recursive shell build; both harness/build errors were
fixed before the recorded successful checks.

Evidence:

- `baseline.jsonl`, `seed1.jsonl`, `seed20261024.jsonl`: original AEX hashes,
  geometry, controls, and initial candidate observations. The two latter files
  deliberately retain their acquisition-time candidate observations, including
  fresh index 21's old refusal; `final.json` is the final-source result.
- `default.jsonl`, `default-summary.json`: same-oracle baseline/candidate
  comparison, 290 Smart and 10 Classic exact preserved; no regressions.
- `final.json`: final source matches all 600 baseline default raw hashes and all
  196 available Smart realistic oracle hashes, including result rectangles.
- `sanitizer.json`: final Smart source repeats the 196 geometry comparisons and
  all 300 default outputs under ASan/UBSan without a failing Smart comparison.
- `witnesses.json`, `witnesses-sanitizer.json`: 30/30 exact each, no sanitizer
  failure. PF8/PF16/PF32, odd padding, partial and expanded requests, reverse
  asymmetric scales, zero-radius axes, Box/Gaussian, and large radii.
- `replay-default.json`: all **147/147** saved expectations match, using each
  corpus's recorded hash-bound worker. Existing expectations were not edited.
- `replay-realistic.json`: all **226/226** new corpus expectations replay exactly.
- New corpus: `tests/fuzz_corpus/olmdistancegradation_realistic_P02b/`, containing
  196 available sampled cases plus 30 independent cases, with original hashes.

Unit baseline and final both ran **140 tests: 66 passed, 15 failed, 59 errors**.
All failing test IDs are identical; [unit-summary.json](P02b-evidence/unit-summary.json)
lists every historical failure/error, with complete before/after logs beside it.
These include absent untracked historical evidence, stale source/identity hashes,
and old admission expectations (including generic sanitizer probe exit 75).
Only two intentional source-text assertions were updated: Gaussian's bound and
the final output-copy location after lifecycle cleanup. The existing executable
transactional ASan/UBSan test passes. The full historical suite is not claimed green.
An exploratory sanitizer run of Classic exposed misaligned typed accesses on
odd strides; Classic is outside this ticket, and final sanitizer checks target
Smart. No Classic stride repair was introduced.

inference:

The observed black/error boundary was caused by Mac geometry admission and
missing host staging, not by unsupported original downsample rendering. The
original's packed-prefix ROI behavior is unusual, but reproducing its public
Smart output is the contract. These measurements establish source-host versus
emulated-AEX equality for the stated cases, not native Windows, installed-bundle,
or native-AE equality, nor arbitrary controls/scales.

changed_files:

- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `core/olmdistancegradation_fieldgen.{cpp,h}` (plugin-only helper)
- `mac/OLMDistanceGradation/tests/{geometry_campaign,geometry_witnesses,regress_default,verify_retained_geometry}.py`
- `tests/test_olmdistancegradation_{pf32_smart_unblurred_beta_20260820,smart_transactional_20260822}.py`
- `tests/fuzz_corpus/olmdistancegradation_realistic_P02b/`
- This report and `orchestra/reports/P02b-evidence/`.

verify:

From the worktree, run serially:

```sh
export TMPDIR="$PWD/orchestra/state/P02b-distancegradation-geometry"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 mac/OLMDistanceGradation/tests/verify_retained_geometry.py
python3 mac/OLMDistanceGradation/tests/verify_retained_geometry.py --sanitize
python3 mac/OLMDistanceGradation/tests/geometry_campaign.py --label verify --seed 1 --n 100
python3 mac/OLMDistanceGradation/tests/geometry_campaign.py --label verify --seed 20261024 --n 100
python3 mac/OLMDistanceGradation/tests/geometry_witnesses.py
python3 mac/OLMDistanceGradation/tests/geometry_witnesses.py --sanitize
python3 mac/OLMDistanceGradation/tests/regress_default.py --n 300
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1 --replay tests/fuzz_corpus/olmdistancegradation --scratch "$TMPDIR/recheck-default" --report "$TMPDIR/recheck-default.json"
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1 --replay tests/fuzz_corpus/olmdistancegradation_realistic_P02b --scratch "$TMPDIR/recheck-realistic" --report "$TMPDIR/recheck-realistic.json"
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*.py'
git diff --check
```

The campaign wrapper calls unchanged `measure_F52c.main()` with
`--geometry realistic --jobs 1` defaults, overriding only the seed and scratch.
Expected counts are above; timeouts can vary with machine load. Retained-hash
verification does not invoke the emulator and is deterministic. Unit discovery
is expected to retain the recorded historical failures.

next:

- Qualify the rebuilt installed bundle in real AE with preview downsampling and
  ROI; no bundle was built/installed by this ticket.
- Resolve the four unavailable original cases in the oracle tooling separately.
- Repair historical DistanceGradation unit evidence and obsolete admission tests
  in a dedicated ticket; do not rewrite historical numerical expectations here.
- Classic odd-stride sanitizer behavior and broader rational-scale/large-kernel
  coverage remain separate follow-up work.
