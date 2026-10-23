status: done
summary:
- Closed three clusters: Bilateral zero-tap work, large Median work, and PF32 scalar radius-two reduction/admission.
- Final seeds1/105/156:290/285/284 Smart exact; zero Smart mismatches/timeouts and all859 prior exact hashes preserved.
- Four Mac timeout cases now finish in0.139–0.206s with unchanged bytes; original failures remain uncompared.
- Independent scalar radius-two360 refusals become exact, with binary-grounded loop-state equality.
- Corpus147/147 unchanged; sanitizer comparisons and retained-evidence audit pass.

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

Cluster 1 completed remeasurements:

FACT: Candidate seed1 completes300/exit0 with290 exact/0 mismatch/3 refusal/0 budget/7 uncompared. Only case10 changes from Mac budget to uncompared; all original successful cases retain exact hashes. Fresh seed156 completes300/exit0 with284 exact/0 mismatch/0 refusal/1 budget/15 uncompared; all284 successful originals are exact. Its one Mac budget is PF16 Median case51, Size3416. These full reports are retained.

Cluster 2 — weighted Median order statistic (base77e7ccb5):

facts:
- Replicated borders cause the old Median to materialize ksize² samples for every output. The new path sorts source sample indices once, counts each sample's replicated-border multiplicity per output coordinate, and selects rank floor(ksize²/2). No field arithmetic or sample conversion changes.
- Selection applies only when ksize²>4*pixel_count and every field value is finite without negative zero. Under this predicate numerically equal samples have identical float bits. Nonfinite/signed-zero cases and smaller apertures retain the old nth_element path. No render admission predicate changes.
- Direct retained-operation differential:324 cases per O2 and ASan/UBSan build, zero differing words; radii1/2/3/7/16/33, geometries1/3/19 by1/17, nine profiles including fallback controls. No sanitizer diagnostic, leak detection disabled.
- Public Smart targets, including original AEX diagnostics and sanitized results:

| Seed/index | Geometry/Size | Before seconds | After seconds | Baseline/sanitized bytes |
|---|---|---:|---:|---|
|105/205|24x27/3600|36.622668|0.193578|identical|
|105/296|18x24/2237|11.787950|0.206331|identical|
|156/51|11x20/3416|11.592270|0.145050|identical|

- Every target's original throws the CV_8U Median assertion. These faster Mac outputs remain uncompared, not exact. Output hashes are in the full target reports.
- Before/current/sanitized verifier on seeds1/105/156:299+298+299 cases, preserving290+285+284 exact hashes and all compared nonexact bytes/statuses. All147 saved corpus outputs remain exact/identical. Four original-failed timeout rows are explicitly skipped; three Median targets and Bilateral1/10 are separately measured with baseline equality.
- Independent small-Median matrix initially passed144 PF8/PF16 cases, then met the unchanged PF32 HDR refusal. This is a probe-domain error, not a newly admitted mismatch. The retained report shows the refusal. Restricting only the probe's PF32 source to SDR gives216/216 public-original exact and sanitized-identical results (all3 depths, sizes1/2, four geometries, ownership/render/interpolation combinations).

| Saved Smart corpus | Before cluster2 | After cluster2 | Rebaseline |
|---|---|---|---|
|147 cases|147 exact|147 exact, identical hashes|None|

inference:
- Weighted selection is the same order statistic over the same replicated multiset. The finite/no-negative-zero condition also guarantees equal numeric selections preserve their original bit pattern. Baseline and sanitizer comparisons support accelerating these original-failed domains without certifying their Mac outputs against absent original outputs.

changed_files (additional):
- Production Median helper/dispatch; `tools/fuzz/check_distancegradation_median_C56.py`; C56 public probe target/Median options.
- `notes/KNOWN_ORIGINAL_BUGS.md`: original Median assertion facts and explicit native-AE uncertainty; no invented deterministic reference semantics.
- C56 report/evidence.

verify (cluster2, same scratch environment):
```sh
python3 tools/fuzz/check_distancegradation_median_C56.py --scratch "$s/median-leaf" --report "$s/median-leaf.json" > "$s/median-leaf.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C56.py --mode box --median --scratch "$s/median-matrix" --report "$s/median-matrix.json" > "$s/median-matrix.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C56.py --mode target --target-case 105 205 --before "$s/base.cpp" --allow-existing-mismatch --scratch "$s/median205" --report "$s/median205.json" > "$s/median205.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C56.py --mode target --target-case 105 296 --before "$s/base.cpp" --allow-existing-mismatch --scratch "$s/median296" --report "$s/median296.json" > "$s/median296.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C56.py --mode target --target-case 156 51 --before "$s/base.cpp" --allow-existing-mismatch --scratch "$s/median51" --report "$s/median51.json" > "$s/median51.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 77e7ccb5 --campaign "$s/seed1.json" --campaign "$s/seed105.json" --campaign "$s/seed156.json" --skip-original-failed-timeouts --corpus --strict-improvement --case-timeout 180 --scratch "$s/median-verify" --report "$s/median-verify.json" > "$s/median-verify.log" 2>&1
```
Expected:324 arithmetic comparisons per build,216 original exact, three targets baseline/sanitizer-identical and under10s; no previously exact loss or corpus change. Timing is load-sensitive. Final full campaign timing census follows after cluster3.

next:
- Two performance clusters closed. Radius-two PF32 scalar admission is still scratch-only: generic-loop experiment fails20 output words; paired pre-filter plane is exact and post-filter first diverges. A specialized grouped reduction is being checked against original IPP arithmetic before admission.

Cluster 3 — original scalar radius-two Bilateral reduction (basebecd26a2):

facts:
- Scratch gate/dispatch extension to radius2 is refuted by the first independent Linear case:7x3 PF32,20 output words differ; first word13/byte52 original `d3f27c3e`, candidate `d5f27c3e`. Constant cases preceding it were exact and did not establish general correctness.
- Paired public/callback-bound trace establishes the FIRST divergent stage:21/21 pre-filter words exact,11/21 post-filter words differ, first word3 original `d3f27c3e`, candidate `d5f27c3e`. Exponential leaf inputs are8201/8201 exact in O2/O3/ASan+UBSan; swapping an exp implementation is not indicated.
- Original dispatch table `1815c7540` selects scalar radius2 entry25=`1806bd9a0`, distinct from radius>=3 entry26=`1806be1e0`. The radius2 body groups four taps each at squared distances4,2,1, multiplies each group sum by its spatial coefficient, and adds center separately. Generic row-major accumulation is not equivalent.
- First grouped candidate exposes a NEW boundary: only post word19 differs, original `081e013f`, candidate `071e013f`;2 final output words differ. Paired pre-divide hooks at `1806be0e3` isolate the numerator: word38 of42 original `8a582240`, candidate `89582240`; all denominators match in all3 builds.
- Original `1806be06b` adds first+second group numerators, then `1806be095` adds that result to center. Restoring that general operation closes all21 pre/post/final field words and all336 output bytes. All42 numerator/denominator words and8201 exponential results match original IPP in O2 strict, O3 requesting contraction, and ASan/UBSan. Original dispatch count `1806bd9a0`:1; no imports. No coordinate/value patch, tolerance or output-byte adjustment.
- New admission: full-resolution Smart PF32 radius2 with scalar tile shape(width<=4 OR height<=4), retaining existing finite-source, ownership/control, positive alpha-conversion-overflow and Power[0.01,5] checks. PF8/PF16, vector tiles and radius>500 are unchanged. Radius2 uses a separate specialized function; existing generic arithmetic remains unchanged.
- Independent final matrices180 ordinary +180 extreme all original-public exact and sanitizer-identical. Shapes7x3,1x7,4x9,19x3,3x19; all ownership/render choices, background/inversion variation, Constant/Linear/Sphere and Power0.01/2.25/5; padded strides. Extremes cover maximum finite signed RGB, subnormals, signed zero, negative maximum alpha and alpha8421504 at the conversion boundary.
- Dedicated fixed-reference admission verifier confirms all360 cases were refused by basebecd26a2, now exact, with sanitized equality and identical input/parameter/geometry binding. Eight negative controls remain refused/sanitizer-identical:5x5 radius2 vector shape,radius501,67x67/radius33,Power0.005/5.01,positive alpha overflow,infinity,NaN. Historical C54's radius2 negative control is intentionally superseded by this newly certified positive domain; the new non-scalar negative retains the unverified boundary.
- Three-seed before/current/sanitized verifier preserves all859 exact campaign hashes and compared nonexact results;896 campaign rows plus147 corpus rows are unchanged. No saved-corpus expectation changes. Original-failed timeout skips and separate target proofs remain explicit.

| Smart exact | Before cluster3 | After cluster3 (fixed references) |
|---|---:|---:|
|seed1|290|290|
|seed105|285|285|
|fresh seed156|284|284|
|saved corpus|147|147, same hashes|
|independent scalar radius2 matrix|0 (360 refused)|360|

inference:
- The operation is a distinct IPP reduction topology, not a generic-kernel admission-only change. Successive failure investigations produced a new post-filter boundary and then a new numerator boundary before refinement. The final cause fix follows the actual instruction order and reproduces the original loop state.
- Finite matrices plus binary-grounded arithmetic support the bounded scalar rule, not arbitrary vector radius2, arbitrary controls or native AE compatibility.

changed_files (additional):
- Production scalar radius2 operation/selector; `tools/emulation/trace_distancegradation_bilateral_C19.py` radius2 dispatch and numerator/denominator hooks.
- C56 probe boundary/extreme/negative support; `tools/fuzz/verify_distancegradation_radius2_C56.py`; evidence audit.
- Full independent reports, failed scratch sources, paired traces and explicit case retained under `C56-evidence/` with manifest hashes.

verify (cluster3; same scratch environment):
```sh
python3 tools/fuzz/probe_distancegradation_C56.py --mode bilateral --radius-two --scratch "$s/radius2" --report "$s/radius2.json" > "$s/radius2.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C56.py --mode bilateral --radius-two --extreme --scratch "$s/radius2-extreme" --report "$s/radius2-extreme.json" > "$s/radius2-extreme.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C56.py --mode bilateral --radius-two --negative --scratch "$s/radius2-negative" --report "$s/radius2-negative.json" > "$s/radius2-negative.log" 2>&1
python3 tools/fuzz/verify_distancegradation_radius2_C56.py --reference "$s/radius2.json" --reference "$s/radius2-extreme.json" --scratch "$s/admission" --report "$s/admission.json" > "$s/admission.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/trace_distancegradation_smart_C14.py --case-json orchestra/reports/C56-evidence/radius2-case.json --scratch "$s/radius2-trace" --report "$s/radius2-trace.json" > "$s/radius2-trace.log" 2>&1
"$py" tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/radius2-trace.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --width 7 --height 3 --radius 2 --radius-two --loop-trace --scratch "$s/radius2-leaf" --report "$s/radius2-leaf.json" > "$s/radius2-leaf.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref becd26a2 --campaign "$s/seed1.json" --campaign "$s/seed105.json" --campaign "$s/seed156.json" --skip-original-failed-timeouts --corpus --strict-admission --case-timeout 180 --scratch "$s/radius2-verify" --report "$s/radius2-verify.json" > "$s/radius2-verify.log" 2>&1
```
Expected:180+180 exact,360 baseline refusal->exact,8 unchanged refusals; paired trace all planes/output exact, leaf8201 exp/21 post/42 loop words exact in all3 builds; all prior exact hashes/corpus preserved. Reproduce failed traces by decompressing retained `radius2.cpp.gz` (generic) or `radius2-grouped.cpp.gz` (initial grouping) to scratch and passing `--source`; traces succeed but report11/1 differing post words. The grouped-loop source and `--allow-mismatch` reproduce the captured numerator difference.

next:
- Three-cluster stop reached. Finish final three full campaigns, strict corpus replay, audit and cleanup. Remaining original failures and larger/vector Bilateral domains are follow-up work.


Final verification and handoff:

FACT: All three final full n300 campaigns complete300/exit0 on production source SHA256
`e1d5c652e1a716448bf9f79dc1452b6899d58d6114c12bfa509e5ac75a92fa8a`.
Original AEX SHA256 is `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
Final source dependency hashes equal the source used by the third-cluster sanitizer verifier.

| Final Smart (10s timeout) | Exact | Mismatch | Refusal | Mac budget | Uncompared | AEX ok/reject/budget |
|---|---:|---:|---:|---:|---:|---|
|seed1|290|0|3|0|7|290/8/2|
|seed105|285|0|2|0|13|285/12/3|
|fresh seed156|284|0|0|0|16|284/13/3|

FACT: Every successful original in these900 cases has an exact Smart output.
All859 prior exact result records/hashes are identical. Geometry, depth, parameters,
source profile, padding and input hashes are unchanged. Only Smart indices1/10,
105/205,105/296 and156/51 change, each budget->uncompared; no original failure is
credited as exact. Classic retains its existing mismatches; Median acceleration
also removes its corresponding timeout statuses, which is not a Classic exact claim.

FACT: Final production arithmetic comparisons again pass648 Bilateral and324 Median
cases in each normal/sanitized build. Final radius-two negative checks directly use
radius2 for invalid Power, alpha overflow, infinity and NaN controls (rather than
only reusing the old radius33 controls); all8 negatives refuse and are sanitizer-identical.
No further production change followed these checks.

FACT: Strict full saved-corpus replay completes147/147, `replay_matches_saved=true`,
exit0. Before/after corpus remains147 exact with identical hashes; no rebaseline.
`python3 tools/fuzz/audit_distancegradation_C56.py` exits0, verifies39 manifest-bound
files, traces, sanitizer comparisons, admission changes, final source binding and
all final per-case preservation rules, and prints `acceptance_met: true`.
`git diff --check` passes.

FACT: All launched build/render processes completed; no background process remains.
Removed42 regenerable scratch directories, including build trees and generated corpus
copies. Remaining scratch logs/reports/source diagnostics total15,278,800 bytes before
this final report update, below5GiB. No worker was rebuilt, no durable oracle was created,
and no MAIN/emulator source, release gate, ledger forbidden-action list, other-plugin
code, installed bundle or saved-corpus expectation was modified. No permission rejection,
push, stash, history rewrite or subagent occurred.

Final quick verification:
```sh
python3 tools/fuzz/audit_distancegradation_C56.py
git diff --check
```
Expected exit0; `acceptance_met: true` and the final counts above. Full reproduction
commands are retained in each cluster section. To repeat strict corpus replay:
```sh
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s/corpus-final" --report "$s/corpus-final.json" > "$s/corpus-final.log" 2>&1
```
Expected147/147 `matches_saved`; use the same scratch environment defined above.

next:
- Three clusters closed; stop C56 work. Remaining follow-up domains are radius-two
  vector tiles, scalar radii>500 and larger vector/HDR/Power combinations.
- Original Median assertions and other oracle rejection/time-budget domains remain
  non-comparable. Native AE exception presentation and native full-host compatibility
  are not established by these CPU-emulator/SDK-shim results.
