status: partial

summary:
- Two clusters closed: finite unblurred PF32 admission and Smart Gaussian field operations.
- Seed1 Smart E/M/R/U: 246/3/44/7 -> 266/3/24/7 -> 268/1/24/7; all base-exact hashes and Classic results unchanged.
- Fresh seed5: 249->269 exact; fresh seed4 PF32: 51->69 exact. Zero admitted mismatches.
- Independent matrix864 newly admitted exact/432 unchanged refusal; sanitizer equality; corpus145 unchanged exact.
- Gaussian independent successful-reference matrix214/214 exact; two original sqrt-import failures remain uncompared. Bilateral investigation continues.

facts:
- Base `7d0b64fad8c5e5909404853e0264537352fcb7e0`, branch `orch/C14-dg-smart-r3`. Read AGENT_GUIDE, GOTCHAS, DG ledger restrictions, compatibility plan, T07/F01/F02/C03/C08 and F10/F12 method. MAIN and emulator sources/workers remain read-only; no rebuild.
- Original AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. Retained worker `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Cache INDEX inspected; differently hashed RadialBlur workers not substituted.
- Initial/final `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0` complete: original Smart290 success/8 reject/2 budget. Before246/3/44/7, after266/3/24/7. Transitions: exact unchanged246, refusal->exact20, refusal unchanged24, mismatch unchanged3, uncompared unchanged7. Classic dictionaries unchanged300/300 (10 exact/290 mismatch).

Cluster 1, finite unblurred PF32:
- Initial finite-only gate-off matrix:104/144 exact,40 mismatch. Mixed negative-alpha Outside first output alpha: original `0000003f` (0.5), Mac `0000403f` (0.75), first byte18. Uniform-HDR RGB differs from original transparent black. Broad finite-only admission rejected.
- Original callback `181170df8..181170e00` computes `min(1,1-alpha)` for Outside. Owner `18117339f..1811733ba` sets refcon+0x90 when converted-mask count is zero or width*height, independently of source alpha range. Mac omitted that upper clamp and disabled uniform-mask early exit for extended alpha.
- Nine callback replays capture actual public-builder state/field from a same-mask SDR proxy, relocate world pointers and replace typed source bytes, then reproduce the separate typed original-AEX public hash9/9. This is **not a natural full-owner HDR capture**: retained worker traces PNG8 only. Mixed signed field/source boundaries agree; original Outside ownership for negative alpha is `0000803f` (1). After fixing ownership and census, all9 outputs agree. Recorded uniform-mask field differences are unconsumed: refcon+0x90 exits before field load.
- Domain: finite channels, `alpha*255 < 2^31`, existing layout/alignment/disjointness/geometry bounds retained. Extended samples use only the existing Constant/Linear/Sphere identity-filter predicate: None or Size0 Box/Gaussian/Median. Effective filters, Power, Bilateral and nonfinite retain prior boundaries. Positive mask-conversion overflow is excluded.
- Scratch restored broad matrix1296/1296 exact with ASan/UBSan equality. It spans signed/HDR RGB/alpha, uniform masks, maximum finite RGB/negative alpha, positive alpha8421504, subnormals/cutoff neighbors,7x1/7x3, all ownership modes, RGB/Layer, backgrounds, inversion, interpolation, identity/small effective filters and odd byte padding.
- Broader promotion rejected: seed1 case192 PF32 Median Size19 throws the original `cv::opt_SSE4_1::medianBlur` CV_8U assertion. Independent Median Size1/2 renders succeed, Size3 rejects. Fresh seed4 case162 HDR Gaussian Size11 also remains nonexact under the broad candidate. These are concrete new boundaries; neither case is admitted. Final rule excludes all effective-filter extended inputs.
- Production matrix: **864 refusal->exact,432 unchanged refusal**, zero admitted mismatches. All864 admitted hashes equal corresponding broad gate-off/original hashes. Ten negative/boundary controls pass: Power, Bilateral, positive mask overflow, maximum alpha, alpha infinity, RGB infinity/NaN, Median Size1/2/3. Original Median1/2 succeed but stay outside this promotion; Median3 rejects.
- Before/current/ASan+UBSan current comparison completes seed1 all300, fresh seed5 299, matrix1296, corpus145 and negative10. Every base-exact output is unchanged; no sanitizer diagnostic or ordinary/sanitized disagreement. Leak checking disabled. Public host checks source/padding preservation, no output writes on refusal and balanced checkout/checkin.
- Fresh seed5 has one existing Mac timeout: index288 PF8 138x53 Median Size971; original also rejects. Explicit verifier option records/skips it; it is **not** counted exact or sanitizer-clean. All249 base-exact cases are included;20 refusals become exact. Fresh seed4 has three existing non-PF32 timeouts, so its gate-off admission check covers all92 PF32 inputs:51 exact unchanged,18 refusal->exact. No skipped case is newly admitted.
- Two existing tests initially expected signed/HDR RGB refusal. Updated their shared existing test to accept these finite inputs with source preservation, retaining infinity/NaN/layout negatives. Re-run beta9 and transactional2 pass, including existing sanitizer test.

| Corpus | Before | After | Expectation changes |
|---|---|---|---|
| All145 Smart cases |145 exact|145 exact, identical bytes/status|None|

- Strict public corpus replay exits0, completed145, `replay_matches_saved=true`. Diff check passes. Full records/hashes: `reports/fuzz/olmdistancegradation_C14_domain.json`.

Cluster 2, Gaussian (base `73ed1b95`):
- Original case45 PF8 14x20 Gaussian Size4: pre-blur280/280 words equal; first post-blur original `4c730943`, old Mac `02590943` at word0. All280 post words differ; final6 bytes differ, first byte32 original `e9`, Mac `ea`.
- Original case214 PF16 34x23 Gaussian Size10: pre-blur782/782 words equal; first post original `b4358346`, old Mac `b3358346`, word0. Post522/782 differ; final one word differs at byte4042: original `b956`, Mac `ba56`.
- PF8 trace is a natural public PNG/source capture with typed-public hash binding. PF16 uses a same-mask PNG8 proxy because retained trace command decodes PNG8; all23 typed field rows and real builder state are captured, then the original PF16 callback with the actual source reproduces the complete6256-byte typed public output. No numerical AEX detours. This limitation is explicit in the trace tool/evidence.
- `FUN_181285230` contains sigma-zero tables for1/3/5/7/9 taps, including 9-tap numerators4/13/30/51/60/51/30/13/4 over256. Larger kernels retain double weights through symmetric normalization before float conversion. The old Mac path only had the3-tap table and rounded exponentials/reciprocal prematurely. Original Gaussian also collapses singleton replicated-border axes (`181282d1d..181282d8e`); the column pass accumulates the center followed by symmetric neighbor pairs.
- Restored those Smart operations, preserving Classic kernel/filter arithmetic. Smart blurred PF8 now normalizes directly into the original0..255 float workspace and packs after filtering. This removes the normalize-to-one/filter/multiply rounding; no final-byte adjustment is used.
- Diagnostic kernel-table-only candidate fixes case45 final bytes but leaves160 post words different. Restored kernel/column operations fix case214 all782 post words; PF8 still has148 post differences until native-range staging is restored. Final source matches both pre/post planes (280+782 words each) and both full outputs exactly. These measured boundaries distinguish kernel/accumulation/staging effects.
- Independent216 matrix spans all3 depths,7x1/1x7/13x7, Size1/2/3/4/5/10/11/25, Inside/Outside/Both, inversion, RGB/Layer/background, Linear/Sphere, colors and odd strides. **214 original successes:136 prior exact unchanged,78 mismatch->exact,0 remaining mismatch**. Two PF32 Sphere/Both Size10 controls fail in original worker on unsupported Win64 CRT `sqrt` import; recorded as uncompared, never successful. No worker/import change is made.
- Initial candidate retained a redundant singleton-axis pass and exposed4 additional PF32 output differences in the matrix. Original singleton-axis branch and paired values grounded its removal; final successful-reference matrix is214/214 exact. This is new boundary evidence, not repeated hypotheses without a boundary.
- Before/current/sanitized-current replay: seed1 all300, seed5 299 (same original-rejected pre-existing PF8 timeout excluded), matrix214 successful-reference cases and corpus145. No sanitizer discrepancy/diagnostic; every before-exact byte preserved. Seed1 exact266->268; seed5 exact269->270.
- Fresh full seed1 census: **268 exact/1 mismatch/24 refusal/7 uncompared**; original290/8/2 unchanged. Every266 base-exact result and all300 Classic dictionaries unchanged. Corpus145 exact unchanged, no expectation edit; strict replay145/145 matches saved. Beta9+transactional2 pass; diff check passes.
- Case200 PF8 Bilateral remains a45-byte mismatch (first byte28 original `de`, Mac `dd`). Its pre-blur scaling now matches239/239 words, but128 post-filter words still differ because the typed Bilateral operation remains absent. It is not counted closed.
- Machine evidence: `reports/fuzz/olmdistancegradation_C14_gaussian.json`. Kernel/exp restoration is supported by these finite typed witnesses; arbitrary softdouble/native-libm equivalence is not claimed.

| Cluster2 corpus | Before | After | Expectation changes |
|---|---|---|---|
| All145 Smart cases |145 exact|145 exact, identical bytes/status|None|

inference:
- Uniform-mask census and Outside clamp are original general operations, not output-byte corrections.
- Finite-domain promotion is supported only for identity filters. Small-filter diagnostic success does not resolve arbitrary Gaussian rounding, unsupported Median combinations, Power/UCRT or nonfinite conversion.
- Import failures/deadline exhaustion remain evidence boundaries, never numerical matches.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tests/test_olmdistancegradation_generic_production_beta_20260820.py`
- `tools/fuzz/verify_distancegradation_smart_C14.py`
- `tools/emulation/trace_distancegradation_smart_C14.py`
- `reports/fuzz/olmdistancegradation_C14_domain.json`
- `reports/fuzz/olmdistancegradation_C14_gaussian.json`
- `tools/emulation/trace_distancegradation_blur_C14.py`
- `orchestra/reports/C14-dg-smart-r3.md`

verify:
Run from the worktree; all long-command output goes to ticket scratch.
```sh
s="$PWD/orchestra/state/C14-dg-smart-r3"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$s" --report "$s/check1.json" --corpus "$s/check-corpus" > "$s/check1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 5 --jobs 2 --case-timeout 30 --shrink-attempts 0 --scratch "$s" --report "$s/check5.json" --corpus "$s/check5-corpus" > "$s/check5.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 7d0b64fa --strict-admission --campaign "$s/check1.json" --campaign "$s/check5.json" --skip-original-rejected-timeouts --extended-matrix --negative --corpus --scratch "$s/check-domain" --report "$s/check-domain.json" > "$s/check-domain.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 7d0b64fa --experiment finite-restored --strict-admission --campaign "$s/check1.json" --campaign "$s/check5.json" --skip-original-rejected-timeouts --scratch "$s/check-gate" --report "$s/check-gate.json" > "$s/check-gate.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --source-ref 7d0b64fa --scratch "$s/check-trace-before" --report "$s/check-trace-before.json" > "$s/check-trace-before.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --scratch "$s/check-trace" --report "$s/check-trace.json" > "$s/check-trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --scratch "$s" --report "$s/check-replay.json" > "$s/check-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/check-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/check-transactional.log" 2>&1
git diff --check
```
At this cluster commit: seed1 266/3/24/7, fresh5 exact269 on recorded reference set, matrix864 exact/432 refusal, corpus145 unchanged exact, trace9 exact, tests9+2 pass. Completion/timeouts depend on load; inspect explicit statuses. No skipped/failed execution counts as exact or sanitized success.

Cluster2 verification at this commit:
```sh
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 73ed1b95 --campaign "$s/check1.json" --campaign "$s/check5.json" --skip-original-rejected-timeouts --gaussian-matrix --corpus --scratch "$s/check-gaussian" --report "$s/check-gaussian.json" > "$s/check-gaussian.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_blur_C14.py --index 45 --index 214 --index 200 --scratch "$s/check-blur-trace" --report "$s/check-blur-trace.json" > "$s/check-blur-trace.log" 2>&1
```
Expected: seed1 exact266->268, seed5 exact269->270 on captured oracle sets; matrix214 exact/2 original import failures; corpus145 unchanged;45/214 pre/post/output exact;200 post/output mismatch retained. The earlier strict-admission command describes cluster1: to replay that specific source from later HEAD, export `git show 73ed1b95:mac/OLMDistanceGradation/OLMDistanceGradation.cpp` into ticket scratch and pass it with `--candidate-source`.

next:
- Gaussian cases45/214 closed within the paired/matrix evidence; arbitrary Gaussian softdouble/native-host behavior remains unclaimed.
- Investigate PF32 Bilateral Size0/1, not promoted by this commit.
- Keep PF8 Bilateral case200 separate: its pre-blur scaling difference and missing effective filter are not fixed here.
