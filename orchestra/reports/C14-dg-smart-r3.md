status: done

summary:
- Three clusters closed: finite unblurred PF32, Smart Gaussian, and PF32 radius-one Bilateral.
- Seed1 Smart E/M/R/U: 246/3/44/7 -> 266/3/24/7 -> 268/1/24/7 -> 274/1/18/7; base-exact bytes and Classic results unchanged.
- Fresh seed5 exact:249->269->270->275; domain fresh seed4 PF32:51->69. Zero admitted mismatches.
- Independent matrix864 newly admitted exact/432 unchanged refusal; sanitizer equality; corpus145 unchanged exact.
- Gaussian214/214 successful references and Bilateral432/432 exact; original import failures/timeouts remain explicit.

facts:
- Base `7d0b64fad8c5e5909404853e0264537352fcb7e0`, branch `orch/C14-dg-smart-r3`. Read AGENT_GUIDE, GOTCHAS, DG ledger restrictions, compatibility plan, T07/F01/F02/C03/C08 and F10/F12 method. MAIN and emulator sources/workers remain read-only; no rebuild.
- Original AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. Retained worker `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Cache INDEX inspected; differently hashed RadialBlur workers not substituted.
- Initial/cluster1 `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0` complete: original Smart290 success/8 reject/2 budget. Before246/3/44/7, after266/3/24/7. Transitions: exact unchanged246, refusal->exact20, refusal unchanged24, mismatch unchanged3, uncompared unchanged7. Classic dictionaries unchanged300/300 (10 exact/290 mismatch).

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

Cluster 3, PF32 Bilateral radius one (base `4db924aa`):
- Initial gate-off with Size0/1 admission and existing direct-host-exp IPP reproduction admits six seed1 cases and passes432 independent controls. It is **rejected for promotion** by fresh seed5 case179, PF32 45x2 Inside/invert, thresholds28/128, Linear, RGB/no background, Size0. Original output SHA256 `96bfcd24f480d6bc9833288fef58ee7297aec64893e1669e6776a3499b813b57`; candidate `4268357fef63627d784b6bd4229975f6bbdf9dda4340c4ccce256f8b7f5db729`.
- Paired public-bound trace: all90 pre-filter words equal;40 post-filter words differ, first word10 original `8741923e`, Mac `8841923e`;59 output words differ, first byte160 original `9309ed3d`, Mac `9409ed3d`. Original call `1812c97d3` enters IPP and changes the destination to the final filtered plane; fallback `1812c9930` is not reached. This refutes a portable-backend explanation and establishes the IPP producer boundary.
- The lower original APIs `18000c280` (initialize) and `18000c2f0` (filter), with retained CPU dispatch index2, reproduce all90 original post-filter words. Both complete with zero imports; no numerical/code detour is installed. The radius-one body `1806bd740` calls scalar exp through `1802997a0 -> 18144ee30` four times per pixel.
- First divergent operation: exponent input bits `bd4ccccd` yields original exp bits `3f7383c6`, host `expf` bits `3f7383c5`. This is a newly measured scalar boundary, not an inferred final-byte correction. All other distinct exponent inputs in this case agree with host expf.
- Restored the original scalar exp's256-entry binary64 power table (`18144f000`), range reduction and quadratic polynomial (`18144f800..18144f817`), with original separately rounded double operations. The helper is confined to bilateral's finite exponent interval[-0.5,0]. Restored original exponent multiplication order as well. No coordinate/fixture/output-value lookup is used.
- Independent original-function check:8204 distinct exponent bit patterns, including endpoints, subnormals, seeded samples, uniform samples and the measured boundary's neighbors. Every value matches original AEX under O2, O3 with contraction requested, and ASan/UBSan. The helper disables contraction locally. The entire case179 pre/post/output is now exact; callback replay still binds to the full typed-public original hash.
- Original `1812ca750` clamps diameter1/3 to radius1 and zero sigmas to1. Size0 therefore invokes an effective filter. Added a shared effective-blur predicate for this Smart PF32 lane, so field filtering, Constant binarization and auxiliary-channel selection agree. Admission is SDR-only, Constant/Linear/Sphere, Size0/1 with actual scaled radius at most1. Larger radii, Power, extended/nonfinite channels and existing unsafe layouts remain refused.
- Production before/current/sanitized-current comparison: seed1 **268->274 exact**; fresh seed5 **270->275 exact** on299 cases, with the same original-rejected pre-existing PF8 timeout explicitly excluded. All base-exact bytes preserved; no admitted mismatch. Independent432 controls are all newly exact; seven negative controls remain refusal (Power, Size2, alpha/RGB above1, negative RGB, infinity, NaN). Existing beta test also checks that Size1 with a scale yielding radius2 refuses without writing output.
- Full seed1 census: **274 exact/1 mismatch/18 refusal/7 uncompared**, original290 successes/8 rejects/2 budget. All268 previous exact route dictionaries and all300 Classic dictionaries unchanged. No corpus expectation changes:145 Smart cases retain identical output/status; strict replay matches saved145/145. Beta9+transactional2 pass, including sanitizer execution.
- Machine evidence: `reports/fuzz/olmdistancegradation_C14_bilateral.json`; paired-stage and direct-original-function tools are committed. The full-owner PF32 trace retains the earlier PNG-proxy limitation; lower IPP replay independently reproduces its entire post-filter plane without proxy arithmetic or imported exp.

| Cluster3 corpus | Before | After | Expectation changes |
|---|---|---|---|
| All145 Smart cases |145 exact|145 exact, identical bytes/status|None|

inference:
- Uniform-mask census and Outside clamp are original general operations, not output-byte corrections.
- Finite-domain promotion is supported only for identity filters. Small-filter diagnostic success does not resolve arbitrary Gaussian rounding, unsupported Median combinations, Power/UCRT or nonfinite conversion.
- Import failures/deadline exhaustion remain evidence boundaries, never numerical matches.
- Bilateral residuals were caused by the retained host-exp substitution, not the compose callback. The repaired original operation supports only the stated radius-one SDR domain; broader radii/backend/codegen equivalence is not inferred.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tests/test_olmdistancegradation_generic_production_beta_20260820.py`
- `tools/fuzz/verify_distancegradation_smart_C14.py`
- `tools/emulation/trace_distancegradation_smart_C14.py`
- `reports/fuzz/olmdistancegradation_C14_domain.json`
- `reports/fuzz/olmdistancegradation_C14_gaussian.json`
- `tools/emulation/trace_distancegradation_blur_C14.py`
- `tools/emulation/trace_distancegradation_ipp_C14.py`
- `tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py`
- `reports/fuzz/olmdistancegradation_C14_bilateral.json`
- `orchestra/reports/C14-dg-smart-r3.md`

verify:
Run from this worktree. The prebuilt worker and MAIN assets are used read-only. All long-command output goes to ticket scratch.
```sh
s="$PWD/orchestra/state/C14-dg-smart-r3"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$s" --report "$s/check1.json" --corpus "$s/check-corpus" > "$s/check1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 5 --jobs 2 --case-timeout 30 --shrink-attempts 0 --scratch "$s" --report "$s/check5.json" --corpus "$s/check5-corpus" > "$s/check5.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 4db924aa --strict-admission --campaign "$s/check1.json" --campaign "$s/check5.json" --skip-original-rejected-timeouts --bilateral-matrix --bilateral-negative --corpus --scratch "$s/check-bilateral" --report "$s/check-bilateral.json" > "$s/check-bilateral.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --seed 5 --case-index 179 --scratch "$s/check-trace" --report "$s/check-trace.json" > "$s/check-trace.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_ipp_C14.py --trace "$s/check-trace.json" --width 45 --height 2 --scratch "$s/check-ipp" --report "$s/check-ipp.json" > "$s/check-ipp.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --scratch "$s" --report "$s/check-replay.json" > "$s/check-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/check-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/check-transactional.log" 2>&1
git diff --check
```
Expected: seed1 E/M/R/U274/1/18/7; before268 exact preserved plus6 admitted exact; seed5 before270 preserved plus5 admitted exact. Matrix432 exact, seven unchanged refusals, corpus145 unchanged exact; case179 pre/post/output exact; direct IPP90 words and exp8204 words exact in all three builds; tests9+2 pass. Completion/timeouts depend on load; explicit failed/skipped runs never count as exact or sanitizer success.

Historical cluster1/2 rechecks must pin their respective candidate sources, since later commits intentionally improve additional outputs:
```sh
git show 73ed1b95:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/domain.cpp"
git show 4db924aa:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/gaussian.cpp"
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 7d0b64fa --candidate-source "$s/domain.cpp" --strict-admission --campaign "$s/check1.json" --campaign "$s/check5.json" --skip-original-rejected-timeouts --extended-matrix --negative --corpus --scratch "$s/check-domain" --report "$s/check-domain.json" > "$s/check-domain.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 73ed1b95 --candidate-source "$s/gaussian.cpp" --campaign "$s/check1.json" --campaign "$s/check5.json" --skip-original-rejected-timeouts --gaussian-matrix --corpus --scratch "$s/check-gaussian" --report "$s/check-gaussian.json" > "$s/check-gaussian.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_blur_C14.py --source "$s/gaussian.cpp" --index 45 --index 214 --index 200 --scratch "$s/check-blur" --report "$s/check-blur.json" > "$s/check-blur.log" 2>&1
```
Expected domain: seed1246->266, seed5249->269, matrix864 newly exact/432 refusal, negative10, corpus145 unchanged. Expected Gaussian: seed1266->268, seed5269->270, matrix214 exact/2 original sqrt-import failures, corpus145 unchanged; cases45/214 pre/post/output exact, case200 post/output remains mismatch.

The rejected host-exp counterfactual can be reproduced without editing production:
```sh
python3 - "$s/bilateral-host-exp.cpp" <<'PY_REPRO'
import subprocess, sys
from pathlib import Path
sys.path.insert(0, 'tools/fuzz')
from verify_distancegradation_smart_C14 import bilateral_source
source = subprocess.check_output(['git', 'show', '4db924aa:mac/OLMDistanceGradation/OLMDistanceGradation.cpp']).decode()
Path(sys.argv[1]).write_text(bilateral_source(source))
PY_REPRO
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --source "$s/bilateral-host-exp.cpp" --seed 5 --case-index 179 --scratch "$s/check-counterfactual" --report "$s/check-counterfactual.json" > "$s/check-counterfactual.log" 2>&1
```
Expected pre0/post40/output59 differing words. The committed machine evidence retains that counterfactual and both final boundaries.

next:
- Three clusters closed; stop this ticket's loop. Follow-up: PF8 Bilateral case200 (45 final differing bytes; pre-filter239/239 words already exact) and remaining18 PF32 refusals.
- Preserve Power/UCRT, larger Bilateral radii, effective-blur extended samples, unsupported original Median, nonfinite and layout boundaries until independently resolved.
- No claim of arbitrary Gaussian host-libm equivalence, native AE host execution, or global conformance closure. Original reference failures remain separate follow-up work.
