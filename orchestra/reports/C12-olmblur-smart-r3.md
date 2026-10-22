status: partial

summary:
- Closed the PF8 non-Legacy repeated-radius cluster and its small-frame refusals; PF16/PF32 follow next.
- Seed 1 Smart 122/13/165 -> 157/11/132; fresh seed 5 125/10/165 -> 159/8/133 (exact/mismatch/refusal).
- Restored AEX double -> float -> integer radius materialization in the PF8 worker; no coefficient/writer/output correction.
- All 247 original campaign exact cases and Classic outputs preserved. Two saved mismatches become exact; independent 720-row matrix is exact and sanitizer clean.
- This is the first cluster commit; the ticket is still in progress.

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

inference:
- Missing binary32 materialization is the measured common cause of the repeated-radius boundary mismatch, not a final-byte/rounding tolerance adjustment.
- Paired stages, static instructions, two seeds and the independent matrix support the PF8 non-Legacy small-frame admission. Finite exact tests do not prove arbitrary input/native Windows UCRT/AE/GPU/ROI/downsample equivalence.
- PF16/PF32 contain the same missing conversion and are the next typed clusters. Legacy nonfinite conversions and residual coefficient differences remain separate work.

changed_files:
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

At this PF8 commit, from the worktree root:

```sh
bash tools/fuzz/recheck_blur_C12.sh 044f9b0a884e618d3750f2d293e8ff6437193b0a base pf8 8
```

The driver executes the exact n300/seed1+5/jobs2 campaigns, diagnostic gate-off, production/sanitizers, 720 independent cases, paired traces, predecessor/current corpus replay, monotonic verifier with retained controls, and seven unit checks. It writes only C12 scratch and never rebaselines. Expected results are the PF8 table above, matrix 689 exact->exact / 31 mismatch->exact, 247 base-exact campaign cases preserved, corpus 2 mismatch->exact / 28 exact unchanged / 9 mismatch unchanged, retained 12/12, final replay 39/39 and tests OK. The initial baseline was additionally measured using ordinary `tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 2` with explicit scratch/report/corpus/worker and shrinking disabled. The driver reconstructs old Mac AND core sources without checking out or modifying the worktree.

next:
- Continue the observed radius conversion repair in PF16/PF32, with separate commits and the same monotonicity requirements.
- Leave the existing PF8 Legacy sanitizer cases and PF16 Legacy/nonfinite/PF32 coefficient/payload residuals for their own first-stage investigations.
