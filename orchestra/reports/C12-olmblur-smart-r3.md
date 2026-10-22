status: partial

summary:
- Closed PF8 and PF16 non-Legacy repeated-radius clusters in separate commits; PF32 is next.
- Seed 1 Smart 122/13/165 -> 173/5/122; fresh seed 5 125/10/165 -> 170/8/122 (exact/mismatch/refusal).
- Restored AEX double -> float -> integer radius conversion; PF8 small non-Legacy and PF16 Repeat <= 2 gain proven admissions.
- Base-exact campaigns and Classic outputs preserved; eight saved mismatches improve, with history retained. Sanitizer campaigns and retained controls pass.
- Two clusters completed; broader PF16 admission is rejected by nine independent residuals and a direct/cached-oracle boundary.

facts:

Base `044f9b0a884e618d3750f2d293e8ff6437193b0a`, branch `orch/C12-olmblur-smart-r3`. Read AGENT_GUIDE, plugin ledger restrictions, emulator GOTCHAS, compatibility plan, T09/C05/C10/F15/F17/F18 and F10/F12 reports. MAIN, SDK, AEX, external emulator source and cached workers were read-only. No reference worker rebuild, release-gate/ledger/other-plugin/installed-bundle change, push or history rewrite. Scratch stays under `orchestra/state/C12-olmblur-smart-r3` (under 20 MiB for this commit); temporary builds are automatically deleted.

Original MAIN `plugins_2025/OLMBlur.aex` SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. INDEX worker `/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker` SHA256 `9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7`. Per-build/source/core hashes and full machine evidence are in `reports/fuzz/olmblur_C12_pf8.json`.

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

inference:
- Missing binary32 materialization is the measured common cause of the repeated-radius boundary mismatch, not a final-byte/rounding tolerance adjustment.
- Paired stages, static instructions, two seeds and the independent matrix support the PF8 non-Legacy small-frame admission. Finite exact tests do not prove arbitrary input/native Windows UCRT/AE/GPU/ROI/downsample equivalence.
- PF32 contains the same missing conversion and is the next typed cluster. Broader PF16 admission remains unproven because of the recorded oracle/coefficients boundary; Legacy nonfinite conversions remain separate work.

changed_files:
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

At the corresponding commit, from the worktree root (the PF8 predecessor is `f7925d21`):

```sh
# At the PF8 commit:
bash tools/fuzz/recheck_blur_C12.sh 044f9b0a884e618d3750f2d293e8ff6437193b0a base pf8 8
# At this PF16 commit:
bash tools/fuzz/recheck_blur_C12.sh f7925d21 pf8 pf16 16
```

The driver executes the exact n300/seed1+5/jobs2 campaigns, diagnostic gate-off, production/sanitizers, 720 independent cases, paired traces, predecessor/current corpus replay, monotonic verifier with retained controls, and seven unit checks. It writes only C12 scratch and never rebaselines. Expected results are the PF8 table above, matrix 689 exact->exact / 31 mismatch->exact, 247 base-exact campaign cases preserved, corpus 2 mismatch->exact / 28 exact unchanged / 9 mismatch unchanged, retained 12/12, final replay 39/39 and tests OK. The initial baseline was additionally measured using ordinary `tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 2` with explicit scratch/report/corpus/worker and shrinking disabled. The driver reconstructs old Mac AND core sources without checking out or modifying the worktree.

For this PF16 commit, expected counts are the PF16 table; production matrix 235 exact->exact / 5 mismatch->exact, full diagnostic matrix 667/44/9 as above, 316 predecessor exact preserved, corpus 6 mismatch->exact / 30 exact unchanged / 3 mismatch unchanged, retained 12+80, strict replay 39/39. The diagnostic direct/cached boundary command intentionally exits 1; the driver checks that result and continues. This is the measured boundary, not a passing comparison.

next:
- Continue the observed PF32 radius conversion repair, with a separate commit and the same monotonicity requirements.
- Leave the existing PF8 Legacy sanitizer cases and PF16 Legacy/nonfinite/PF32 coefficient/payload residuals for their own first-stage investigations.
