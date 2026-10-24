status: done
summary:
- Restored original horizontal float32 distance scaling and sampled-world geometry for public DirectionalBlur renders.
- Smart downsample campaigns: seed 1 and seed 20261024 each 100/100 exact, no refusal or mismatch.
- Added 72 typed downsample/partial-request witnesses; all exact in O2 and ASan/UBSan.
- Default 2,000-case before/after comparison has zero exact-to-non-exact regressions; corpus replay matches 83/83.
- Unit tests were run; historical DirectionalBlur failures remain and are reported below, not claimed green.

facts:

Base: `22f8f8023645f6299abe6a19f2f596eae7157148`. Ground truth is the original
CPU AEX in the retained Unicorn worker, compared to the source-recompiled Mac
public EffectMain host. No native AE / installed bundle claim is made.

AEX SHA256: `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
F52 worker SHA256: `1be0cb14f6e68ab9276ef37be3a381aae9fb0306914987eb91e1a9d23dd94f4b`.
Default F46 worker SHA256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
Workers and AEX were used by absolute path; no rebuild or asset copy.

Static confirmation from MAIN `disasm/OLMDirectionalBlur.aex.asm.txt`:

| Builder slot | Meaning | Context destination |
|---|---|---|
| 5, checkout at `0x180006e2b` | Front Strength | `+0x48`, store `0x180006e50` |
| 6, checkout at `0x180006e8f` | Front Alpha Fade | `+0x4c`, store `0x180006eb4` |
| 10, checkout at `0x180006f65` | Back Strength | `+0x50`, store `0x180006f8a` |
| 11, checkout at `0x180006fc9` | Back Alpha Fade | `+0x54`, store `0x180006fee` |
| 20, checkout at `0x180007281` | Thickness | `+0x8110`, double-to-float then store `0x1800072ac` |

`0x180003d39..0x180003db8` reads X numerator/denominator at InData
`+0x11c/+0x120`, converts to FLOAT32, DIVSS, then MULSS and CVTTSS2SI for
each of the four integer fields. CVTTSS2SI truncates toward zero. Thickness
uses MULSS without integer conversion. The matching PF16/PF32 blocks start
at `0x180004ac9` and `0x180005854`. No angle projection or Y ratio enters
these distance multiplications. The four post-scale integers also control
the all-zero early exit at `0x180003dc0..0x180003dd4`.

Implementation:

- Materialize these sampled distances once in `InfoFromParams`; existing cores
  and budgets then receive unit-scale, sampled-pixel values. This avoids the
  previous PF8 angle projection and deep-path unit-scale refusal.
- Compute sampled layer bounds with integer ceiling from the two rational
  factors, instead of comparing sampled worlds to full-resolution InData.
- Request the entire sampled input for a partial output request, since the
  rotated workspace uses the global input. Removed the fixed-dimension
  exceptions and pre-render partial-request refusal.
- Accept positive sampled Thickness below 1 in the DirectionalBlur budget;
  check FLOAT32 grid sizes before integer conversion. Zero, nonfinite, and
  unrepresentable grid dimensions remain rejected.

Measured results (serial, 10-second oracle call limit):

| Measurement | Smart E / M / R / U |
|---|---|
| Seed 1, n100, before | 20 / 0 / 80 / 0 |
| Seed 1, geometry + scaling only | 94 / 0 / 6 / 0 |
| Seed 1, final | 100 / 0 / 0 / 0 |
| Seed 20261024, final | 100 / 0 / 0 / 0 |
| Default seed 1, n2000, before AND after | 1991 / 0 / 2 / 7 |

The six intermediate refusals were indices 7, 11, 53, 64, 67, 86: Noise
Thickness UI 1 became sampled 0.5, 1/3 or 0.25 and failed the old minimum-1
budget check. This supplied a new boundary; allowing the valid sampled value
closed all six without numerical changes. No two-refuted-hypotheses stop
condition occurred.

`regress_default.py` compares both revisions to the same oracle result for each
route, using unchanged default generation/max-size256/seed1/n2000. All 1,991
Smart exact and all 31 Classic exact cases stay exact. Classic retains 1,967
mismatches and 2 refusals; Smart retains 2 refusals and 7 unavailable oracles.
No exact-to-non-exact transitions. First new Smart mismatch: none.
The separate `tools/fuzz/run.py --replay` run matches all **83/83** saved cases
and their hash-bound workers. Saved expectations were not edited.

`witness_downsample.py`: **72/72 exact**, independently repeated **72/72 exact
under ASan/UBSan**, with no sanitizer diagnostic. These cover PF8/PF16/PF32,
39x27 odd full dimensions, 1/2, 1/3, 1/8 and asymmetric X1/2-Y1/3, angle37,
Front/Back Fade, generated Noise at UI Thickness1, and integer truncation to
zero. Half request rect `1,1,2,2`; half request the full sampled frame. Both
original and candidate return full allocated worlds. F52 does not implement
cropped output allocation, so these are partial-request witnesses, not proof
for separately allocated cropped/nonzero-origin output worlds.

Unit results:

- `OLM_TEST_JOBS=1 python3 -m unittest discover -s tools/fuzz -p 'test_*.py'`:
  **34 tests, OK, 2 skipped**.
- Initial DirectionalBlur test discovery lacked the untracked SDK paths and
  still expected Thickness0.5 and partial requests to be refused. Added local
  absolute read-only SDK symlinks and updated only those intentional contract
  assertions. SDK links are removed after validation.
- Final DirectionalBlur discovery: **18 tests, 8 failures, 4 errors** (6 pass).
  Logs and the baseline diagnosis are retained in `P01b-evidence/`.
  The final base-source/base-assertion run has **17 tests, 8 failures, 4 errors**
  (5 pass; the intentionally changed budget test is excluded). The 12 failing
  test IDs exactly match the final candidate run. Historical source/report hashes, old numerical
  hashes and old nonfinite/budget-refusal expectations are not rewritten.
- The baseline overlay runner uses the base plugin and base budget without
  editing tracked source. It reproduces the same old numerical hash mismatch
  `e27c16ee...` versus retained `f05d4c86...`, stale dependency hashes, and obsolete
  rejection expectations. Poisoned-source budget probes SIGSEGV on the base
  too. These are existing unit-suite issues, not successful rejection tests.
- The first baseline span probe had an overlay include-resolution error;
  the corrected isolated rerun reproduces the base `layerbudget` SIGSEGV.

inference:

The 80 refusals were adapter unit/geometry errors, not evidence of unsupported
original downsample rendering. The original distance rule is horizontal-only,
even when Y scale differs. Ceiling bounds follow the F52 host allocation policy
and the SDK full-vs-sampled dimension distinction; native AE allocation/ROI
negotiation still needs host validation. Passing finite witnesses is not an
all-input or native-Windows claim.

changed_files:

- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `core/dblur_generic_budget.h`
- `mac/OLMDirectionalBlur/tests/{measure_downsample,witness_downsample,regress_default,unit_baseline}.py`
- `tests/test_directionalblur_general_feature_budget_20261001.py`
- `tests/test_directionalblur_layer_general_effectmain_20261001.py`
- `tests/test_directionalblur_layer_geometry_effectmain_20261001.py`
- This report and `orchestra/reports/P01b-evidence/`.

verify:

From the worktree, run serially (the scripts use only ticket scratch):

```sh
export TMPDIR="$PWD/orchestra/state/P01b-directionalblur-downsample"
mkdir -p "$TMPDIR"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
export OLM_FUZZ_TEST_SCRATCH="$TMPDIR/unit"
python3 mac/OLMDirectionalBlur/tests/measure_downsample.py --label verify --seed 1 --n 100
python3 mac/OLMDirectionalBlur/tests/measure_downsample.py --label verify --seed 20261024 --n 100
python3 mac/OLMDirectionalBlur/tests/witness_downsample.py
python3 mac/OLMDirectionalBlur/tests/witness_downsample.py --sanitize
python3 mac/OLMDirectionalBlur/tests/regress_default.py --n 2000
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 1 --replay tests/fuzz_corpus/olmdirectionalblur --scratch "$TMPDIR/replay" --report "$TMPDIR/replay.json"
python3 -m unittest discover -s tools/fuzz -p 'test_*.py'
```

The measurement wrapper calls the unchanged `measure_F52.main()` with
`--plugin olmdirectionalblur --n 100`; it overrides only scratch and the seed
passed to the unchanged generator (the original CLI hardcodes seed1). It also
records the actual seed and changed budget-header hash in the summary.
Expected: Smart100 exact twice; witness72 exact twice; zero default regressions;
83/83 replay; 34 unit tests OK with 2 skips. Oracle timeouts can vary with load.

For the historical unit suite, make local ignored `Headers`, `Util`, `Resources`
symlinks to their absolute MAIN locations, then run:

```sh
python3 -m unittest discover -s tests -p 'test_directionalblur_*.py'
python3 mac/OLMDirectionalBlur/tests/unit_baseline.py
python3 mac/OLMDirectionalBlur/tests/unit_baseline.py test_directionalblur_layer_span_budget_20261001.py
```

Expect the recorded historical failures; do not treat this suite as green.
The baseline runner loads both production source and assertions from the base
commit, so it does not apply the new partial-request assertions to old code.

next:

- Follow up the historical DirectionalBlur unit suite: stale source/numerical
  evidence, obsolete nonfinite and budget refusal expectations, and poisoned
  source budget probes. Rebind to the current oracle rather than changing bytes.
- Qualify real AE / an extended oracle with cropped output allocation and
  nonzero output origins. Full-world validation remains; no cropped-output
  conformance claim is made here.
- Classic's existing mismatches and the two default Smart refusals are outside
  this downsample ticket and remain visible in evidence.
