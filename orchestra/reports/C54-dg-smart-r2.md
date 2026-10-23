status: done

summary:
- Closed three clusters: Smart Box timeout, PF8/PF16 Box area precision, and finite large-radius PF32 scalar Bilateral.
- Final seed1 remains290 exact; seed105 improves283→285 exact. Zero Smart mismatches or prior exact/hash losses.
- Seed105/150 improves22.07s→0.229s;292 refusal→exact. Independent PF16 witness32 differing words→0.
- Public matrices594 exact plus432 arithmetic comparisons and IPP leaf checks pass with sanitizers; corpus147/147 unchanged.
- All successful originals in both measured seeds now have exact Smart outputs; three-cluster stop reached.

facts:
- Base `8056458b0c71ba76130066c449c9eb9578faebfd`, branch `orch/C54-dg-smart-r2`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, DG ledger row and DG triage/fix reports (C52 first); F10/F12 admission method. No MAIN, emulator sources/workers, ledger, release-gate or other-plugin edits.
- Original worker is retained F46, SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`; original AEX `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. All builds use scratch and single-case execution. No subagents, worker rebuild, push, stash or history rewrite.
- Full compressed evidence and SHA256 manifest are in `C54-evidence/`. Original assets/environments are accessed by absolute path in MAIN without copying.

| Baseline n300, timeout10s | exact | mismatch | refusal | Mac budget | uncompared | AEX ok/reject/budget |
|---|---:|---:|---:|---:|---:|---|
| seed1 |290|0|3|1|6|290/8/2|
| seed105 |283|0|3|3|11|285/12/3|

- Both `run.py` campaigns exit0, complete300. All290+283 previous C52 exact result dictionaries are identical.
- Seed105/150: PF8,23x16, Box Size3896 (kernel7793), successful original output SHA256 `0312dc03b105c756cd1be132719c825ff9698339db880d19f314b8ae22110588`. Before and candidate are identical across all1472 bytes. Measured public process wall times22.067587s and0.228657s respectively; current/sanitized outputs and status identical. Timed comparison used the first scratch fast path; the subsequent signed-zero initialization correction is covered by final independent/campaign verification.
- `sample <baseline-pid> 1 -file <scratch>/box-profile.txt` captured850/850 samples in build_distance_field (inlined Box loop). Static implementation performs one ksize² scan per output pixel; no arithmetic changes to the divisor or writer are part of this first cluster.
- The fast path is Smart-only. It computes a common binary grid for finite binary32 samples and proves `max_abs_in_grid <= floor(2^53 / kernel_area)` using integer division. Every intermediate product/sum in the separable rolling sums is then exactly representable in binary64; borders, divisor, final float conversion are unchanged. Uncertified/nonfinite inputs retain the original sequential loop. No gate is relaxed.
- Initial arithmetic differential exposed profile4/kernel3/1x1 (negative zero), before any promotion. Starting both rolling sums from positive zero restores the old accumulation semantics. Final432 leaf cases (248 certified/184 fallback) are bit-identical at O2 and ASan/UBSan, including signed zero, subnormals, mixed exponents, very large finite values and nonfinite fallback. No sanitizer diagnostic; leak detection disabled.
- Independent public Box matrix:198/198 exact and sanitizer-identical, covering8/16/32bpc,3 geometries plus23x16, sizes3/31/501/3896, ownership/interpolation/render/background variations and odd strides. PF16 Size3896 is separately investigated below rather than counted exact.
- Initial wider matrix finds a pre-existing PF16 Size3896 difference after134 exact cases:32 words differ, first word46/byte92 original `7a35`, Mac `7935`. Fresh baseline reproduces the identical result (`before_equal=true`,21.755862s). The optimization does not introduce this mismatch. Retained full failing report and exact case make it reproducible.
- `verify_distancegradation_smart_C14.py --before-ref 8056458b... --campaign seed1.json --campaign seed105.json --skip-original-rejected-timeouts --corpus --strict-improvement --case-timeout 180`: exit0, completed; seed1 290 exact+10 nonexact unchanged; seed105284 exact+14 nonexact unchanged. The longer allowance renders case150 at both revisions; this is not credited as a numerical gain. Two original-rejected Median Mac timeouts205/296 are explicitly skipped, not sanitizer-certified or counted exact. All598 compared campaign cases and147 corpus cases have identical before/current bytes/status and sanitized equality.

| Saved Smart corpus | Before | After | Expectation edits |
|---|---|---|---|
|147 cases|147 exact|147 exact, same hashes|None|

inference:
- The measured timeout is algorithmic redundant summation; exact representability permits faster evaluation without modifying any rounded result. Bounded tests plus the arithmetic certificate support this operation, not all native AE compatibility.
- The independently found PF16 post-filter discrepancy is a separate existing numerical issue, not a reason to hide or rebaseline a mismatch. It is investigated next in its own commit.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`: Smart certified exact-sum Box path.
- `tools/fuzz/probe_distancegradation_C54.py`: independent public matrix, timings, baseline comparison and sanitizers.
- `tools/fuzz/check_distancegradation_box_C54.py`: direct retained-operation arithmetic differential.
- `tools/fuzz/audit_distancegradation_C54.py`.
- This report and `orchestra/reports/C54-evidence/`.

verify:
```sh
python3 tools/fuzz/audit_distancegradation_C54.py
git diff --check
s="$PWD/orchestra/state/C54-dg-smart-r2/recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
git show 8056458b0c71ba76130066c449c9eb9578faebfd:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/base.cpp"
python3 tools/fuzz/check_distancegradation_box_C54.py --scratch "$s/leaf" --report "$s/leaf.json" > "$s/leaf.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C54.py --mode target --before "$s/base.cpp" --scratch "$s/target" --report "$s/target.json" > "$s/target.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C54.py --mode box --exclude-large-pf16 --scratch "$s/box" --report "$s/box.json" > "$s/box.log" 2>&1
for seed in 1 105; do
  python3 tools/fuzz/run.py --plugin olmdistancegradation --seed "$seed" --n 300 --jobs 1 --shrink-attempts 0 --scratch "$s/seed$seed-work" --corpus "$s/seed$seed-corpus" --report "$s/seed$seed.json" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 8056458b0c71ba76130066c449c9eb9578faebfd --campaign "$s/seed1.json" --campaign "$s/seed105.json" --skip-original-rejected-timeouts --corpus --strict-improvement --case-timeout 180 --scratch "$s/verify" --report "$s/verify.json" > "$s/verify.log" 2>&1
```
Expected: audit pass,432 arithmetic comparisons per build,198 public exact, target exact and fast, zero previous exact loss,147 corpus unchanged. Machine-load-sensitive wall budgets are not numerical evidence. Initial wider matrix is reproduced by omitting `--exclude-large-pf16` (expected mismatch before the subsequent area fix).

next:
- Finish fresh campaign remeasurements, then independently verify and trace the PF16 large-Box area fix.
- Remaining seed105292 finite large-radius Bilateral refusal follows; original Median/assertion/timeouts remain non-comparable.

Cluster1 final campaigns (commit14eb5a5b; evidence-log follow-upfed8f0e3):

FACT: Fresh seed1 remains290/0/3/1/6, all300 result dictionaries identical. Fresh seed105 is284/0/3/2/11; only Smart index150 changes budget→exact. All Classic result dictionaries are unchanged, every prior exact Smart hash preserved. Both complete300/exit0. This is the measured10-second improvement, separate from the longer verifier allowance.

Cluster2 — retain exact Box area for every Smart typed path (base14eb5a5b):

facts:
- PF16 independent witness23x16/Size3896 first diverges after Box, not in its source field: all368 pre-filter FLOAT32 words equal;110 post-filter words differ, first original `5ad67f46` versus Mac `5bd67f46`. Output32 words differ, first word46 original `7a35`, Mac `7935`.
- Kernel7793 area60730849 rounds to60730848 in binary32. Area boundary facts: Size2047/kernel4095 area16769025 is exactly representable; Size2048/kernel4097 area16785409 rounds to16785408; Size4096/kernel8193 area67125249 rounds to67125248.
- Existing C52 exact-area normalization was selected only for PF32 Smart. Select that same double-precision integer-area normalization for PF8/PF16 Smart too. Classic keeps its existing rounded divisor. No accumulator, admission, field generation, source mask or writer change in this cluster.
- Corrected trace matches368/368 pre words,368/368 post words, and2944/2944 output bytes. Both traces have identical original input/public-output hashes; typed original callback replay equals the full public original output. PF16 plane capture uses the existing same-mask PNG proxy plus typed public/callback binding, not a native AE capture.
- Independent public matrix216/216 exact and sanitizer-identical; boundary matrix162/162 exact and sanitizer-identical. The latter covers all3 depths, sizes2047/2048/4096, geometries7x3/3x1/1x7, all ownership/interpolation/render choices with background/invert variation and padded strides. The former includes every originally failing PF16 Size3896 case. No tolerance or expectation adjustment.
- Before/current/sanitized verifier passes597 campaign cases and147 corpus cases, with no byte/status change at all. Seed1 remains290 exact+9 unchanged nonexact; seed105284 exact+14 unchanged nonexact. Explicitly skipped: seed1/10(original timeout) and seed105/205,296(original Median assertion), each a baseline Mac timeout. These3 cases do not supply successful originals and are not counted exact or sanitizer-clean. A new optional verifier flag records these skips; ordinary/default behavior remains unchanged. The first cluster did execute seed1/10 under the longer allowance.

| Smart comparison | Before cluster2 | After cluster2 |
|---|---|---|
| seed1 fixed-oracle exact/mismatch/refusal/budget/uncompared |290/0/3/1/6|290/0/3/1/6|
| seed105 fixed-oracle exact/mismatch/refusal/budget/uncompared |284/0/3/2/11|284/0/3/2/11|
| saved corpus147 |147 exact|147 exact, identical hashes|
| independent failing PF16 witness |32 output words differ|0 output words differ|

inference:
- Retaining the true integer area explains and closes the first divergent filter stage. This is the same general normalization precision boundary C52 established for PF32, now independently witnessed for PF16 and checked for PF8. Finite matrices do not prove native AE or arbitrary unsupported inputs.

changed_files (additional):
- `tools/emulation/trace_distancegradation_blur_C14.py`: generic explicit typed-case input; public/callback binding and full-word comparisons remain mandatory.
- `tools/fuzz/verify_distancegradation_smart_C14.py`: explicit optional skip for baseline Mac timeouts whose originals also failed, with recorded reason.
- C54 probe/audit, report and evidence; production divisor selector/comment only beyond cluster1.

verify (cluster2; same scratch environment as above):
```sh
python3 tools/fuzz/probe_distancegradation_C54.py --mode box --scratch "$s/area" --report "$s/area.json" > "$s/area.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C54.py --mode area-boundaries --scratch "$s/area-boundaries" --report "$s/area-boundaries.json" > "$s/area-boundaries.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 14eb5a5b --campaign "$s/seed1.json" --campaign "$s/seed105.json" --skip-original-failed-timeouts --corpus --strict-improvement --case-timeout 180 --scratch "$s/area-verify" --report "$s/area-verify.json" > "$s/area-verify.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 14eb5a5b:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/performance.cpp"
"$py" tools/emulation/trace_distancegradation_blur_C14.py --case-json orchestra/reports/C54-evidence/box16-case.json --source "$s/performance.cpp" --scratch "$s/trace16-before" --report "$s/trace16-before.json" > "$s/trace16-before.log" 2>&1
"$py" tools/emulation/trace_distancegradation_blur_C14.py --case-json orchestra/reports/C54-evidence/box16-case.json --scratch "$s/trace16-after" --report "$s/trace16-after.json" > "$s/trace16-after.log" 2>&1
```
Expected:216+162 exact/sanitized-identical; zero prior exact losses, corpus147 unchanged; paired trace before0/110/32 and after0/0/0 differing pre/post/output words. The trace exits0 on successful capture even when differences exist; audit checks the actual counts.

next:
- Two clusters closed. Remeasuring seed1 and testing large-radius PF32 scalar Bilateral in scratch before any admission change.

Cluster2 remeasurement:

FACT: Fresh seed1 after cluster2 completes300,290 exact/0 mismatch/3 refusal/1 budget/6 uncompared; every result dictionary is identical to its post-performance campaign.

Cluster3 — finite PF32 scalar Bilateral through radius500 (baseaffd91da):

facts:
- Original successful-reference residual seed105/292 is1x1 PF32 HDR Bilateral Size392. Its gate-off zero output alone was already insufficient in C52; this ticket uses independent nonzero fields instead.
- Independent7x3/radius33 gate-off trace: pre-filter21/21 words equal; post-filter and final field21/21 words differ, first original `8f71373f`, Mac `0000803f`. Output54 words/181 bytes differ, first word1/byte4 original `2690c53d`, Mac `e1e0e03d`. The ungated baseline skips the filter beyond the existing dispatch bound.
- Selecting the existing scalar IPP body for that shape/radius makes every pre/post/final field word and all336 output bytes exact. Original public and relocated typed callback remain bound. No exponent, tap order, border handling, accumulation, normalization or writer operation is changed.
- Import-free original IPP init/filter at radius33 dispatches `0x1806be1e0` once and reproduces the captured public post-plane.21 filtered words and8217 exponential inputs match O2 strict, O3 requesting contraction, and ASan/UBSan; no original imports. Diagnostic harness cap extends32→64, within its existing1MiB spec/8MiB scratch allocation; no reference worker is modified or rebuilt.
- New general rule: full-resolution Smart PF32 scalar-shape radius3..500 (width<=2*radius OR height<=2*radius), using the existing finite/source/control/Power predicates. PF8 retains its previous radius32 scalar selector and general-dispatch behavior; PF16 and vector-shape radius bound remain unchanged. Existing finite Power[0.01,5] admission applies; nonfinite samples and positive alpha-to-int32 overflow still refuse.
- Independent ordinary108 plus extreme108 public-original comparisons are all exact and sanitizer-identical. Radii33/392/500; geometries7x3/1x7/7x3; all ownership modes, RGB/Layer, background/inversion variation, Constant/Linear/Sphere and Power0.01/2.25/5. Ordinary sources include HDR/signed RGB and alpha; extremes include maximum finite signed RGB, maximum negative alpha, alpha8421504 at the mask-conversion edge, subnormals and signed zero. Padded strides throughout.
- Eight independent negative controls remain refused and sanitizer-identical: radius2, radius501,67x67/radius33 non-scalar shape, Power0.005/5.01, positive alpha conversion overflow, RGB infinity and NaN. No original output is claimed for negative controls.
- Before/current/sanitized verifier:185 PF32 campaign cases plus147 corpus cases, exit0. Seed1 remains91 exact+4 nonexact. Seed10587 exact+2 nonexact unchanged, only292 refusal→exact. All147 corpus outputs are exact and unchanged; no expectation edits and no sanitizer diagnostic (leak detection disabled).

| Smart fixed-oracle comparison | Before cluster3 | After cluster3 |
|---|---|---|
| seed1 exact/mismatch/refusal/budget/uncompared |290/0/3/1/6|290/0/3/1/6|
| seed105 exact/mismatch/refusal/budget/uncompared |284/0/3/2/11|285/0/2/2/11|
| corpus147 |147 exact|147 exact, identical hashes|

inference:
- This residual is an omitted bounded dispatch/admission range. Independent filter-plane and import-free IPP evidence support reuse of the existing general scalar operation. The radius500 cap is the tested admission boundary, not a claim that the original rejects501 or that all larger radii are incorrect.
- All successful originals in the fixed seed1/105 reference sets now have exact Smart outputs. Original assertion/timeout domains remain unresolved and are not converted into exact evidence.

changed_files (additional):
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`: PF32-only scalar-radius selector bound/comment.
- `tools/emulation/trace_distancegradation_bilateral_C19.py`: diagnostic radius cap64.
- C54 negative/ordinary/extreme probe, audit, report and bound evidence.

verify (cluster3; same scratch environment):
```sh
python3 tools/fuzz/probe_distancegradation_C54.py --mode bilateral --scratch "$s/bilateral" --report "$s/bilateral.json" > "$s/bilateral.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C54.py --mode bilateral --extreme --scratch "$s/bilateral-extreme" --report "$s/bilateral-extreme.json" > "$s/bilateral-extreme.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C54.py --mode bilateral --negative --scratch "$s/bilateral-negative" --report "$s/bilateral-negative.json" > "$s/bilateral-negative.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref affd91da --campaign "$s/seed1.json" --campaign "$s/seed105.json" --campaign-pf32-only --corpus --strict-admission --case-timeout 180 --scratch "$s/bilateral-verify" --report "$s/bilateral-verify.json" > "$s/bilateral-verify.log" 2>&1
"$py" tools/emulation/trace_distancegradation_smart_C14.py --case-json orchestra/reports/C54-evidence/bilateral33-case.json --scratch "$s/bilateral-trace" --report "$s/bilateral-trace.json" > "$s/bilateral-trace.log" 2>&1
"$py" tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/bilateral-trace.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --width 7 --height 3 --radius 33 --scratch "$s/bilateral-leaf" --report "$s/bilateral-leaf.json" > "$s/bilateral-leaf.log" 2>&1
```
Expected:108+108 exact,8 refused; only292 newly exact versus cluster2,147 corpus unchanged; pre/post/field/output all exact,8217 exp/21 plane words exact in all3 leaf builds. To reproduce the pre-admission diagnostic, apply `candidate_source('gate-off', <affd91da source>)` from `tools/fuzz/probe_distancegradation_C19.py` in scratch and pass it as `--source` to the trace. The gate-off source is never production.

next:
- Three clusters closed; final full campaigns and strict saved-corpus replay are completing before handoff.


Final verification and handoff:

FACT: Final production source SHA256 `8b787fe2a9003f09becaea3b7aa55b3b8e91234b7b248cf414464bcfc0bb8744`. Both final full n300 campaigns exit0, complete300. Every seed1 result dictionary is identical to the starting campaign. Every seed105 Classic result dictionary is identical; the only changed Smart dictionaries are150 (budget→exact) and292 (refusal→exact). All290+283 initially exact Smart hashes remain identical. Input hashes, geometry, depth, parameters, profile and padding are unchanged. The final audit asserts these facts.

| Final measured Smart, timeout10s | exact | mismatch | refusal | Mac budget | uncompared |
|---|---:|---:|---:|---:|---:|
| seed1 |290|0|3|1|6|
| seed105 |285|0|2|2|11|

FACT: Final strict saved-corpus replay exits0,147 completed,147 `matches_saved=true`, honoring the saved worker bindings without override. No corpus expectation changes. The first cluster's retained198 public matrix is superseded by the final216 Box+162 area-boundary checks; together with216 Bilateral checks this is594 final independent public comparisons, all exact and sanitizer-identical. O2/ASan432 direct arithmetic cases and O2/O3/ASan8217-exp/21-plane-word IPP comparisons also pass. The corpus and finite campaigns do not establish native AE or all-input conformance.

FACT: All launched render/build/profile processes have completed. Regenerable scratch build trees and duplicate generated corpus directories were removed; retained scratch files total13,036,676 bytes (<5GiB). Six edited/new Python files parse, evidence audit and `git diff --check` pass. No permission rejection occurred. No MAIN, emulator source/worker, installed bundle, release-gate, ledger, other-plugin or corpus expectation changes; no push/stash/history rewrite/subagents.

Final quick verification:
```sh
python3 tools/fuzz/audit_distancegradation_C54.py
git diff --check
```
Expected exit0: manifests match; all previous exact outputs preserved; only150/292 improve; all matrix/trace/sanitizer assertions and corpus147 pass. Full reproduction commands are above. Strict corpus replay can also be independently repeated:
```sh
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s/corpus-final" --report "$s/corpus-final.json" > "$s/corpus-final.log" 2>&1
```
Expected exit0,147/147 matches saved. Fresh wall-time outcomes may vary with shared-machine load and are never counted as numerical evidence.

next:
- Stop: three clusters closed. No AEX-successful nonexact Smart case remains in the measured seed1/105 sets.
- Follow-up domains: PF32 Bilateral radius2, scalar radius>500 and larger vector/HDR/Power combinations; original Median assertion and oracle-timeout domains. Seed1/10 Mac Bilateral timeout also has an original timeout; seed105/205,296 Mac Median timeouts have original assertions. They remain unresolved, not exact, and need their own performance/oracle work.
- Native AE/host/ROI and existing Classic mismatches remain outside this ticket. No newly identified original undefined-memory bug or deterministic-oracle change is claimed.
