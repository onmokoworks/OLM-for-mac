status: done

summary:
- Closed three typed non-Legacy repeated-radius clusters (PF8, PF16, PF32), each in its own commit, with bounded small-frame admissions.
- Seed 1 Smart 122/13/165 -> 180/4/116; fresh seed 5 125/10/165 -> 184/4/112 (exact/mismatch/refusal).
- All 247 original base-exact campaign cases and Classic results remain byte-identical; nine saved mismatches become exact with history retained.
- Production sanitizer campaigns, independent matrices, 92 final retained controls, strict corpus replay 39/39 and seven unit checks pass.
- Stop at three typed clusters. Higher-repeat oracle/coefficients differences and Legacy/nonfinite residuals remain explicitly recorded.

facts:

Base `044f9b0a884e618d3750f2d293e8ff6437193b0a`, branch `orch/C12-olmblur-smart-r3`. Read AGENT_GUIDE, plugin ledger restrictions, emulator GOTCHAS, compatibility plan, T09/C05/C10/F15/F17/F18 and F10/F12 reports. MAIN, SDK, AEX, external emulator source and cached workers were read-only. No reference worker rebuild, release-gate/ledger/other-plugin/installed-bundle change, push or history rewrite. Scratch stays under `orchestra/state/C12-olmblur-smart-r3` (under 30 MiB at final verification); temporary builds are automatically deleted.

Original MAIN `plugins_2025/OLMBlur.aex` SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. INDEX worker `/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker` SHA256 `9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7`. Per-build/source/core hashes and full machine evidence are in `reports/fuzz/olmblur_C12_{pf8,pf16,pf32}.json`. PF8 commit `f7925d21`, PF16 commit `4787f193`, PF32 is this final commit.

**First divergent stage.** The new paired tracer reuses the exported SmartPreRender/SmartRender ABI fixture and observes original helper entries without patching AEX instructions. Mac diagnostic copies record validated helper inputs before any arithmetic. Both use the same generated active input; the complete direct-AEX output must bind to the cached original worker. All four initial traces bind. Staging/previous helper buffers and coefficients agree before the first radius difference:

| Seed-1 index | Depth | First helper-call index | AEX radius | Mac radius | Reconstructed binary64 product from observed pow result |
|---:|---:|---:|---:|---:|---:|
| 19 | 8 | 12 | 3 | 2 | 2.999999962177924 |
| 13 | 16 | 24 | 3 | 2 | 2.9999999596692373 |
| 66 | 32 | 2 | 3 | 2 | 2.999999940642084 |
| 196 | 16 | 21 | 3 | 2 | 2.9999999954059158 |

All products round to binary32 bits `00004040` (3.0, little endian). The product column is a reconstruction from captured import values and the materialized Amount, not a claimed direct register capture. Static disassembly confirms `MULSD; CVTPD2PS; CVTTSS2SI`: PF8 `180003df0..180003df8` / `180004120..180004128`; PF16 `180002963..18000296b` / `180002c90..180002c98`; PF32 `18000521f..180005227` / `18000553f..180005547`. The decompiler's direct `(int)dVar19` expression loses the intermediate float conversion. The fix changes the general worker operation, using the same float radius for integer truncation and sigma.

**PF8 gate-off and promotion.** Original gate-off seed 1: 257 exact / 41 mismatch / 2 PF8 Legacy sanitizer aborts; seed 5: 273/27/0. After PF8 radius repair the PF8 non-Legacy subset is 66/66 exact on each seed, with no sanitizer findings. All 33/32 formerly refused cases in this domain become exact. Small PF8 non-Legacy now uses the existing legal parameter/storage/geometry/work-budget rules, with arbitrary uint8 source samples and all legal Amount/Repeat/Bias/Smoothness. Legacy and other depths retain their prior admission. No original exact-fixture source is replaced by an output shortcut.

| Seed / production | Before E/M/R | PF8 E/M/R | New exact from mismatch | New exact from refusal |
|---|---|---|---:|---:|
| 1 | 122/13/165 | 157/11/132 | 2 | 33 |
| 5 | 125/10/165 | 159/8/133 | 2 | 32 |

The arithmetic-only step (before admission) was separately measured: seed 1 124/11/165 and seed 5 127/8/165. Ordinary and ASan/UBSan final result objects agree in full, with 1,200 sanitized campaign route executions, no production sanitizer findings. Leak checking is disabled. Classic remains 13/0/287 and 26/0/274; all original route oracles are unchanged.

Independent matrix: 6 geometries (singleton, small rectangle, rows, columns, and both one-dimension >24 orientations), 10 Amount boundaries including float neighbors, Repeat 1/2/3/4/9/10, both Bias values, three Smoothness values distributed over random/edge/opaque/transparent typed sources and odd row padding. All 720 PF8 original Smart renders and production sanitizer renders are exact: 689 baseline exact retained, 31 mismatches corrected. The matrix baseline bypasses the small gate to isolate arithmetic; the final matrix uses the unmodified production admission. Public harness assertions check source/guards/padding and callbacks.

Nine additional corrected PF8 gate-off traces bind to cached AEX and have exact final output. Seven have every observed helper stage exact. Two large-Amount cases (indices 0/285) retain three coefficient-word differences at the first stage, although final output is exact; e.g. index 285 weight 73 AEX `dffa743f`, Mac `defa743f`. These differences are recorded, not patched or claimed resolved. Native libSystem expf/powf/pow imports are used to match the cached emulator's host-libm boundary; this is not native Windows UCRT proof.

Corpus replay before: 39/39 saved results, 28 exact / 11 mismatch. Initial candidate: 37/39 saved results because indices 4/236 improve; after retaining history in `C12_updates`, strict sanitized replay is 39/39, 30 exact / 9 mismatch. All original inputs/parameters/reductions/Classic/oracles remain unchanged. The 12 retained 24x24 depth/Legacy/checkin controls pass with sanitizers. Existing Classic/generic unit checks: 7 passed. `git diff --check` passes.

**PF16 second cluster (predecessor `f7925d21`).** The same general conversion is corrected in `core/olmblur_worker16_nonlegacy.cpp`. Seven paired small/public PF16 witnesses (13/70/158/207/212/243/196) now have all observed helper inputs exact, cached/direct AEX output binding, and exact full output. No coefficient, helper or writer arithmetic was changed. Machine evidence: `reports/fuzz/olmblur_C12_pf16.json`.

| Seed / production | PF8 predecessor E/M/R | PF16 E/M/R | New exact from mismatch | New exact from refusal |
|---|---|---|---:|---:|
| 1 | 157/11/132 | 173/5/122 | 6 | 10 |
| 5 | 159/8/133 | 170/8/122 | 0 | 11 |

All 316 predecessor exact campaign results and both Classic result sets remain identical. Ordinary/sanitized campaigns match in full (1,200 route executions, zero production sanitizer findings). Gate-off PF16 non-Legacy is 72 exact / 1 mismatch for seed 1, 66 / 1 for seed 5; residual indices are 40 and 6. Thus full PF16 non-Legacy admission is NOT promoted.

The 720-row full diagnostic PF16 matrix is 667 exact->exact, 44 mismatch->exact, 9 mismatch->mismatch, sanitizer clean; none of the nine residual output objects change. First residual is matrix index 225 (7x5, Amount 30, Repeat 9, Bias 2, edge/full uint16 input): 3 differing words/bytes, first byte 6, AEX `6398` vs Mac `6298`. Other residuals are indices 344/584/585/596/669/704/705/717. They all use Repeat 9 in this sampled matrix; that observation is not turned into a per-case Repeat-9 exception.

The positive rule is instead the general single-decay schedule, non-Legacy Repeat <= 2 (Repeat 1 was already admitted), where powf's exponent is exactly 1 for Repeat 2. Production keeps all existing parameter/domain/storage/budget limits. The independently regenerated production matrix for that rule is **240/240 exact**, 235 old exact retained and 5 numerical mismatches corrected, with ASan/UBSan. Both seeds have zero newly admitted mismatches. This bounded rule does not claim arbitrary fractional-exponent libm equivalence.

The first residual received a separate read-only direct AEX trace. It has **no observed helper-input difference versus Mac**, but direct AEX hash `14ea9109d893558f65e128e4d3a457c702f61d90c06c7f038e18609937c75ea2` differs from cached-worker hash `f436d88ce8e62f5252c905466f27a6b800ebdfd7bbfa9fb4a53a9ceceafd16d3`. The tracer correctly exits 1 for failed binding; that evidence is stored separately as `coeff-pf16` and is NOT accepted as a first-stage explanation of the cached residual. The external worker was not rebuilt, changed, or replaced, and the cached oracle remains authoritative for the campaigns. Pinpointing the two oracle scaffolds' difference is follow-up work, not a production workaround.

PF16 corpus: six saved mismatch->exact records (93/127/196/235/261/268), 30 predecessor exact unchanged, 3 remaining mismatches unchanged. Initial replay 33/39 saved matches becomes strict **39/39** after preserving previous results in `C12_updates`; final distribution 36 exact / 3 mismatch. Original input bytes/parameters/Classic/oracles are unchanged. An expanded sanitizer replay now also runs **80/80 retained typed public positive controls**, including large-Amount/repeated non-Legacy PF8/PF16/PF32 fixture owners, both Legacy values and optional checkin present/absent. This supplements the original 12/12 controls and retrospectively verifies PF8 preservation. The host's obsolete source-mutation refusal tests are deliberately not counted as positive regressions. Existing unit checks: 7 passed; `git diff --check` passes.

**PF32 third cluster (predecessor `4787f193`).** The same general conversion is corrected in `core/olmblur_worker32_nonlegacy.cpp`. The three corrected witnesses (66/262/270) bind complete direct AEX output to the cached worker and have no observed helper-input difference after the repair. All three full outputs are exact, including the unshrunk production index 270 (57x1 HDR source), which previously differed in 81 float words. No exp/expf, helper, NaN payload or final-store operation was changed. Machine evidence: `reports/fuzz/olmblur_C12_pf32.json`.

| Seed / production | PF16 predecessor E/M/R | PF32 final E/M/R | New exact from mismatch | New exact from refusal |
|---|---|---|---:|---:|
| 1 | 173/5/122 | 180/4/116 | 1 | 6 |
| 5 | 170/8/122 | 184/4/112 | 4 | 10 |

All 343 predecessor exact campaign results remain identical. Ordinary/sanitized results match in full, with 1,200 sanitized route executions and no production sanitizer finding. Transitive preservation across all three commits covers every one of the initial 247 exact cases; Classic and original-route oracles are unchanged throughout. Seed-1 final residual mismatch indices are 40/99/115/272. One already-admitted nonfinite seed-5 case (index 79, 127x214) improves partially: differing bytes 89,856 -> 89,743 and float words 35,599 -> 35,572, first byte 8 remains AEX `4623c1ff` vs Mac `4523c17f`. It remains a mismatch and is not rebaselined or counted exact. The verifier initially rejected this transition under its stricter mismatch->exact-only rule; it now follows the C05 numerical-repair method, allowing an existing mismatch only when both byte and word differences strictly decrease, while newly admitted cases must always be exact. No base-exact change is permitted and corpus rebaseline remains exact-only. Total new exact counts are 58 (9 numerical fixes + 49 new admissions) and 59 (6 numerical fixes + 53 new admissions) for seeds 1/5.

Full diagnostic PF32 matrix: 652 exact->exact, 43 mismatch->exact, 25 mismatch->mismatch, sanitizer clean. All 25 remaining output objects are unchanged. First residual: matrix index 188 (7x5), first byte 4, 2 differing bytes/float words, AEX `93080a3f` vs Mac `92080a3f`. The sampled remaining tuples are Amount 5/30/1000 with Repeat 9, and Amount 1000 with Repeat 10. Broad PF32 admission is therefore not promoted. The production single-decay rule (Repeat <= 2, all ARGB finite in [0,1]) is **240/240 exact**, preserving 235 old exact and fixing 5 mismatches. Both seeds have zero admitted mismatches. The existing storage-validated memcpy-based source scan also rejects **56/56** one-away typed source boundaries at both predecessor and final revision: every channel, Repeat 1 and 2, negative subnormal, 1+ULP, largest finite float, both infinities, quiet/signaling NaNs. Signed zero/subnormal SDR values are in the positive matrix.

Residual tracing records two distinct boundaries without a production workaround. Indices 71/182/258 have complete direct-AEX output equal to Mac and no observed helper-input difference, but fail binding to the cached worker; the tracer correctly exits 1 and these records are stored separately. Indices 116/290 *do* bind to the cached worker; the first observed difference is the next helper's input plane at call 6 after the first axis, with different NaN payloads (`4623c1ff` vs `4523c17f`). That localizes a helper-output boundary, not the first individual arithmetic instruction. These inputs remain outside the new finite-SDR admission. No coefficient or payload adjustment was made.

PF32 corpus: only saved index 270 improves. Table across commits:

| Saved Smart cases | Initial | PF8 | PF16 | PF32 final |
|---|---:|---:|---:|---:|
| Exact | 28 | 30 | 36 | 37 |
| Mismatch | 11 | 9 | 3 | 2 |
| Refusal | 0 | 0 | 0 | 0 |

Initial PF32 replay is 38/39 saved matches for that one intentional improvement; after preserving history, final strict sanitized replay is **39/39**, 37 exact / 2 mismatch. The 12 original controls plus 80 expanded retained positives are all sanitizer-clean at this final revision, including repeated large-Amount PF32 fixture owners. Existing unit checks: 7 passed. No installed/native AE run or release-gate change is claimed.

Final admission rules added by this ticket: arbitrary legal non-Legacy PF8 tuples; non-Legacy PF16 Repeat <= 2; non-Legacy PF32 Repeat <= 2 with all active ARGB components in [0,1]. The original integer singleton/default/retained-owner rules still apply. Existing dimensions, source/destination storage, geometry, full-frame/downsample, callbacks, memory/work budgets and exact-fixture precedence remain intact.

inference:
- Missing binary32 materialization is the measured common cause of the repeated-radius boundary mismatch, not a final-byte/rounding tolerance adjustment.
- Paired stages, static instructions, two seeds and the independent matrix support the PF8 non-Legacy small-frame admission. Finite exact tests do not prove arbitrary input/native Windows UCRT/AE/GPU/ROI/downsample equivalence.
- All three typed workers had the same binary32 conversion omission. Broader PF16/PF32 admission remains unproven because of the recorded oracle/coefficients boundaries; Legacy nonfinite conversions remain separate work. Three typed clusters have been completed; this is not a claim that all Smart inputs are exact.

changed_files:
- `core/olmblur_worker32_nonlegacy.cpp`
- `reports/fuzz/olmblur_C12_pf32.json`
- `tests/fuzz_corpus/olmblur/seed1_case000270_8214084afb2c.json`
- `core/olmblur_worker16_nonlegacy.cpp`
- `tools/fuzz/verify_blur_retained_C12.py`
- `reports/fuzz/olmblur_C12_pf16.json`
- `tests/fuzz_corpus/olmblur/seed1_case000{093,127,196,235,261,268}_*.json`
- `core/olmblur_worker_orchestration.cpp`
- `mac/OLMBlur/OLMBlur.cpp`
- `tests/test_olmblur_generic_beta_lane_20260820.py`
- `tools/emulation/trace_olmblur_stages_C12.py`
- `tools/fuzz/blur_campaign_C12.py`
- `tools/fuzz/verify_blur_radius_C12.py`
- `tools/fuzz/verify_blur_C12.py`
- `tools/fuzz/recheck_blur_C12.sh`
- `tests/fuzz_corpus/olmblur/seed1_case000004_adfc483da30a.json`
- `tests/fuzz_corpus/olmblur/seed1_case000236_fac8522494e3.json`
- `reports/fuzz/olmblur_C12_pf8.json`
- `orchestra/reports/C12-olmblur-smart-r3.md`

verify:

At the corresponding commit, from the worktree root (PF8 is `f7925d21`, PF16 is `4787f193`):

```sh
# At the PF8 commit:
bash tools/fuzz/recheck_blur_C12.sh 044f9b0a884e618d3750f2d293e8ff6437193b0a base pf8 8
# At the PF16 commit:
bash tools/fuzz/recheck_blur_C12.sh f7925d21 pf8 pf16 16
# At this final PF32 commit:
bash tools/fuzz/recheck_blur_C12.sh 4787f193 pf16 pf32 32
```

The driver executes the exact n300/seed1+5/jobs2 campaigns, diagnostic gate-off, production/sanitizers, the independent matrices described above, paired traces, predecessor/current corpus replay, monotonic verifier with retained controls, and seven unit checks. It writes only C12 scratch and never rebaselines. Expected results are the PF8 table above, matrix 689 exact->exact / 31 mismatch->exact, 247 base-exact campaign cases preserved, corpus 2 mismatch->exact / 28 exact unchanged / 9 mismatch unchanged, retained 12/12, final replay 39/39 and tests OK. The initial baseline was additionally measured using ordinary `tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 2` with explicit scratch/report/corpus/worker and shrinking disabled. The driver reconstructs old Mac AND core sources without checking out or modifying the worktree.

For the PF16 commit, expected counts are the PF16 table; production matrix 235 exact->exact / 5 mismatch->exact, full diagnostic matrix 667/44/9 as above, 316 predecessor exact preserved, corpus 6 mismatch->exact / 30 exact unchanged / 3 mismatch unchanged, retained 12+80, strict replay 39/39. The diagnostic direct/cached boundary command intentionally exits 1; the driver checks that result and continues. This is the measured boundary, not a passing comparison.

For the final PF32 commit, expected counts are 180/4/116 and 184/4/112; production matrix 235 exact->exact / 5 mismatch->exact, diagnostic matrix 652/43/25, source boundaries 56 refusal->refusal, 343 predecessor exact preserved, corpus 1 mismatch->exact / 36 exact unchanged / 2 mismatch unchanged, retained 12+80, strict replay 39/39. Diagnostic residual tracing intentionally exits 1 for the recorded direct/cached binding differences. The complete final command `bash tools/fuzz/recheck_blur_C12.sh 4787f193 pf16 pf32 32` was also executed end-to-end and exited 0; its regenerated transitions, changed-case results and corpus table equal the initial final-stage verification. `bash -n tools/fuzz/recheck_blur_C12.sh` and `git diff --check` pass. No `--rebaseline` is needed for review. The committed reports retain all before/after transitions, exact source/AEX/worker hashes and unchanged diagnostic residuals.

next:
- Reconcile the cached worker/direct public-AEX math/host boundary for higher repeats (PF16 matrix 225, PF32 seed-1 71/182/258) before attempting broader admission. No cached-worker rebuild was authorized or performed here.
- Trace the first arithmetic divergence for PF16 Legacy index 115 (writer saturation hypothesis remains unproven here), PF32 Legacy 99/272, PF8 Legacy gate-off sanitizer cases 77/112, and non-Legacy NaN payload propagation. Final seed-1 production still has 4 mismatches and 116 refusals.
