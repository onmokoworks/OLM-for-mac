status: partial

summary:
- First cluster: repair PF16 Legacy's saturating writer to the original CVTTSS2SI/low-word store and admit independently verified small one/two-pass Legacy frames.
- Seed 1 Smart 180/4/116 -> 196/3/101; fresh seed 6 189/13/98 -> 201/13/86 (exact/mismatch/refusal).
- All 369 baseline exact campaign cases and Classic results preserved; corpus 39/39 unchanged, 37 exact / 2 mismatch.
- Production sanitizer campaigns, 240 independent matrix rows and 92 retained controls pass.
- Broad Legacy admission is not promoted: a 720-row diagnostic exposes four cached/direct oracle residuals. Further clusters are still in progress.

facts:

Base `8567a0d047659ffceee7b641a730556ec6fdb160`, branch `orch/C15-olmblur-smart-r4`. Resumed with no production diff and an unfinished untracked Legacy tracer. Read shared guide, OLMBlur ledger restrictions, GOTCHAS, compatibility plan and T09/F15/F17/F18/C05/C10/C12/F10/F12 evidence. MAIN, external emulator and cached workers remain read-only. No release-gate/ledger/other-plugin/install/push/history changes.

Original MAIN `plugins_2025/OLMBlur.aex`: SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. Accepted campaign/matrix/trace/replay worker: `/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker`, SHA256 `9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7`.

Machine evidence: `reports/fuzz/olmblur_C15_pf16.json`, including hashes, transitions, changed cases, all corpus records, full matrices, paired traces, oracle-boundary evidence and retained controls.

First divergent operation: PF16 Legacy seed-1 indices 31/115/141 have identical flags, weights and complete helper input/output planes at every observed call. Direct exported AEX output binds to the cached worker in all three. At the first differing final word, the original writer at `0x180006cf7` receives XMM0 bits `0000807f` (+infinity, little endian), after `CVTTSS2SI EAX,XMM0` at `0x180006cf3` produces EAX `80000000`. `MOV [RBX+2],AX` stores `0000`; Mac previously stores `0080` because of its 32768 saturation. First differing pixels/red channels: 2/0/1 respectively. Index 115's unshrunk output differs in 117 words/bytes, first byte 3 before repair. All three full outputs are exact after repair, with no helper differences.

Static confirmation: original `FUN_180005f20` typed writer (`decomp/OLMBlur.aex.c.txt` lines 2937–2942); read-only Capstone disassembly confirms `CALL floorf; CVTTSS2SI EAX,XMM0; MOV word ptr [RBX+2],AX`. The implementation now performs the defined int32 conversion, including the architectural indefinite result for NaN/infinity/out-of-int32-range inputs, then preserves the low word. This is the same general operation already used by the non-Legacy PF16 writer; no output-coordinate, fixture-value or final-byte correction is added.

| Campaign | Before E/M/R | After E/M/R | Refusal -> exact | Mismatch -> exact |
|---|---|---|---:|---:|
| Seed 1, n300 | 180/4/116 | 196/3/101 | 15 | 1 |
| Seed 6, n300 | 189/13/98 | 201/13/86 | 12 | 0 |

All original-route oracle result objects and all Classic results are unchanged. Every newly admitted case is exact and equals the gate-off result. O2 and ASan/UBSan result objects agree for all 600 cases (1,200 sanitized route executions); no production sanitizer finding. Gate-off PF16 Legacy is 41/41 exact for seed 1 and 23/23 for seed 6. Unrelated PF8 Legacy gate-off cases 77/112 still abort under UBSan and are not admitted by this commit.

Admission: small frames, PF16, Legacy on, Repeat <= 2; arbitrary legal Amount, Smoothness, Bias and full uint16 source values. Existing geometry/storage/full-frame/downsample/work-budget/parameter guards and retained-owner precedence remain. The renderer still performs the normal Legacy operation.

Independent matrix: six geometries (singleton, 7x5, 25x1, 1x25, 25x7, 7x25), ten Amount boundaries including adjacent float values and 1000, both Bias values, Repeat 1/2, Smoothness 1/62.5/100 and deterministic random/edge/opaque/transparent full-uint16 samples, odd row padding. All 240 production rows are exact under ASan/UBSan: 71 old exact preserved, 169 writer mismatches fixed. Host checks source/padding/guards and callback lifecycle.

Broad diagnostic matrix (Repeat 1/2/3/4/9/10): 207 exact->exact, 509 mismatch->exact, 4 mismatch->mismatch, sanitizer clean. Residual indices 292/538/652/658 have Amount `3.000000238418579`, Smoothness 62.5, Bias 1, Repeat 3 or 10, geometries 25x1/25x7/7x25. First residual 292 differs at byte 90, AEX `b76f`, Mac `b66f` (one word/byte). Direct AEX tracing of 292 observes no helper difference and exactly equals Mac hash `ea5d456b97a957e2d2a3fb2085d7064a7e7907b66263ebaaccf5e7fec0120715`, but does not bind to the cached worker. The tracer correctly exits 1; that row is not accepted as a first-stage explanation of the cached residual. No oracle replacement/rebuild or coefficient adjustment was made. These observations are not generalized into an Amount-specific exclusion.

Corpus before/after: 37 exact->exact and 2 mismatch->mismatch, no updates. Sanitized strict replay 39/39. Original retained positives 12/12 and expanded typed controls 80/80 pass with sanitizers. Seven existing Classic/generic unit checks pass; `git diff --check` passes.

Execution notes: resumed ordinary `run.py --plugin olmblur --n 300 --seed 1 --jobs 2` with explicit ticket scratch/corpus reproduced all 300 prior result objects. An initial diagnostic matrix attempt hit a 60-second oracle timeout; its incomplete run is not counted. A baseline build was accidentally started while that matrix was active, then interrupted; subsequent validation is serialized with two jobs. Retried matrix uses 180-second per-oracle limits. The first driver hit macOS Bash 3's empty-array/nounset behavior at corpus replay; fixed and resumed the remaining checks. An initial manual replay used the default worker, matched all saved results, and was replaced by the explicit hash-pinned worker replay before accepting the evidence. These failed/incomplete attempts are not numerical evidence.

inference:
- The three paired witnesses locate the output mismatch at the PF16 Legacy conversion, after exact intermediate planes. The saturation is a port bug.
- The general one/two-pass admission is supported by two seeds and the independent matrix; broader schedules remain unproven due to the measured oracle boundary.
- Results are original CPU AEX emulation versus public Mac fake-host renders. They do not establish native Windows UCRT, installed/native AE, GPU, arbitrary ROI/downsample or full-domain compatibility.

changed_files:
- `core/olmblur_worker16_legacy.cpp`
- `mac/OLMBlur/OLMBlur.cpp`
- `tests/test_olmblur_generic_beta_lane_20260820.py`
- `tools/emulation/trace_olmblur_legacy_C15.py`
- `tools/fuzz/verify_blur_legacy_C15.py`
- `tools/fuzz/verify_blur_C15.py`
- `tools/fuzz/recheck_blur_C15.sh`
- `reports/fuzz/olmblur_C15_pf16.json`
- `orchestra/reports/C15-olmblur-smart-r4.md`

verify:

At this PF16 commit, from the worktree root:
```sh
bash tools/fuzz/recheck_blur_C15.sh 8567a0d base pf16 16
```
Expected: the campaign table above; 369 original exact cases preserved; matrix 71 exact->exact / 169 mismatch->exact; corpus 39/39 unchanged; retained 12+80 and seven unit checks pass. Driver writes only ticket scratch and does not rebaseline unless `C15_REBASELINE` is explicitly set.

Additional diagnostic reproduction (the final tracer command intentionally exits 1):
```sh
s="$PWD/orchestra/state/C15-olmblur-smart-r4"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_blur_legacy_C15.py --scratch "$s" --report "$s/matrix-off-pf16.json" --before 8567a0d --depth 16 --diagnostic-after > "$s/matrix-off-pf16.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/trace_olmblur_legacy_C15.py --scratch "$s" --report "$s/coeff-pf16.json" --matrix-depth 16 --indices 292 > "$s/coeff-pf16.log" 2>&1
```
Expected matrix 207/509/4 as above; tracer cached_binding=false, first_difference=null, direct-AEX hash equals Mac.

next:
- Continue PF8 Legacy exceptional float-to-integer conversion and remaining Smart refusal clusters.
- Separate follow-up: reconcile direct/cached oracle math for PF16 matrix 292 and previous C12 higher-repeat witnesses without replacing the authoritative oracle.
