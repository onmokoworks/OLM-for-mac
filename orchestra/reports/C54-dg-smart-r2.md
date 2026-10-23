status: partial

summary:
- Closed the AEX-rendered PF8 large-Box Mac timeout with a certified exact-sum fast path.
- Seed1/105 baseline reproduces C52: 290/283 Smart exact, zero mismatch; all prior exact dictionaries preserved.
- Timed seed105/150 improves 22.068s to 0.229s, identical original/baseline/candidate/sanitized output.
- Direct arithmetic 432 cases and independent public matrix 198 cases pass; 745 before/current/sanitized comparisons preserve outputs.
- Investigating an independently discovered, pre-existing PF16 large-Box precision boundary next.

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
