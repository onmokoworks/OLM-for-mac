status: partial
summary:
- Cluster 1: eliminate exactly-zero spatial taps for finite Smart Bilateral fields.
- Seed1/10 Mac wall time 19.390s -> 0.139s, identical bytes; original still fails.
- Seeds1/105 preserve 290/285 exact; 744 before/current/sanitized comparisons pass.
- Independent 108 public cases exact; 648 arithmetic cases per build identical.
- Fresh seed156 and final remeasurements are in progress; no numerical admission changed.

facts:
- Base `f3da6fe1f89f0742a0c57d2c7a41399128c62c14`, branch `orch/C56-dg-smart-r3`. Read shared guide, emulator GOTCHAS, compatibility plan, DG ledger row and prior triage/fix reports, especially C52/C54.
- Retained F46 reference worker SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`; original AEX identity remains in each compressed campaign provenance. MAIN and emulator workers/sources are read-only.
- Baseline seed1 n300 completes, exit0: Smart290 exact/0 mismatch/3 refusal/1 budget/6 uncompared. Candidate seed105 n300 completes, exit0:285 exact/0 mismatch/2 refusal/2 budget/11 uncompared. Every successful original in these campaigns has an exact Smart result.
- Existing scalar/general Bilateral operations explicitly set spatial weight to +0 for squared distance >=50. For finite source values, these taps add only signed zero to accumulators starting at +0. Candidate bounds traversal to [-7,7] and skips squared distances>=50; it preserves every retained tap's arithmetic, order, borders and vector/scalar dispatch. Nonfinite source fields retain full traversal.
- `check_distancegradation_bilateral_C56.py`: O2 and ASan/UBSan each648 comparisons, zero differing words. Radii2/3/6/7/8/33, geometries1/3/19 by1/17, scalar/general bodies, integer/fractional/mixed exponent/signed-zero/subnormal/extreme finite/infinity/NaN profiles. Nonfinite fallback is included; leak checking disabled.
- `probe_distancegradation_C56.py --mode target --before <base.cpp> --allow-existing-mismatch`: seed1/10 (PF8,6x38,Size3834) current0.138758s versus before19.389542s, status and all912 bytes identical; output SHA256 `582f84f5cd2350ad78f2ba038254996c5c0413f9647cd9710216471ef6265136`. Sanitized output/status identical. Original with180s allowance reports execution stopped at `0x18144ee30`; no successful original output, no new exact claim.
- `verify_distancegradation_smart_C14.py --before-ref f3da6fe1 --campaign seed1.json --campaign base105.json --skip-original-failed-timeouts --corpus --strict-improvement --case-timeout 180`: exit0,299+298 campaign cases and147 corpus cases unchanged in status/bytes and sanitizer-identical. All575 previously exact campaign hashes preserved. Explicitly skipped original-failed baseline timeouts1/10 and105/205,296; target1/10 separately checked above.
- `probe_distancegradation_C56.py --mode bilateral`:108/108 original-public exact and sanitizer-identical, radii33/392/500, ownership/render/interpolation/Power combinations and HDR/signed source fields. No sanitizer diagnostic.

| Saved Smart corpus | Before | After | Rebaseline |
|---|---|---|---|
|147 cases|147 exact|147 exact, identical hashes|None|

inference:
- Removing redundant zero additions explains the performance gain without changing floating-point reduction order. Arithmetic proof plus independent differentials support this optimization; the original's timeout is not proof of matching native AE output.
- Median residuals105/205,296 have original `cv::Exception` assertions requiring `CV_8U` at median_blur.simd.hpp:985. They are not AEX-rendered mismatches. Native AE's exception presentation is not established by the emulator.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/check_distancegradation_bilateral_C56.py`
- `tools/fuzz/probe_distancegradation_C56.py`
- `orchestra/reports/C56-dg-smart-r3.md` and `C56-evidence/`

verify:
```sh
s="$PWD/orchestra/state/C56-dg-smart-r3/recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/check_distancegradation_bilateral_C56.py --scratch "$s/leaf" --report "$s/leaf.json" > "$s/leaf.log" 2>&1
git show f3da6fe1:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/base.cpp"
python3 tools/fuzz/probe_distancegradation_C56.py --mode target --before "$s/base.cpp" --allow-existing-mismatch --scratch "$s/target" --report "$s/target.json" > "$s/target.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C56.py --mode bilateral --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
for seed in 1 105 156; do
 python3 tools/fuzz/run.py --plugin olmdistancegradation --seed "$seed" --n 300 --jobs 1 --shrink-attempts 0 --scratch "$s/seed$seed-work" --corpus "$s/seed$seed-corpus" --report "$s/seed$seed.json" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref f3da6fe1 --campaign "$s/seed1.json" --campaign "$s/seed105.json" --skip-original-failed-timeouts --corpus --strict-improvement --case-timeout 180 --scratch "$s/verify" --report "$s/verify.json" > "$s/verify.log" 2>&1
git diff --check
```
Expected:648 bit-identical arithmetic cases per build;108 public exact; target baseline/current/sanitized equal and current under10s (timing depends on load); no prior exact loss or corpus changes. Original failures remain non-comparable. Compressed complete evidence is retained with a SHA256 manifest.

next:
- Finish fresh seed and post-performance seed1 measurement. Investigate Median timeout and PF32 Bilateral residual domains separately; do not count original failures as exact.
