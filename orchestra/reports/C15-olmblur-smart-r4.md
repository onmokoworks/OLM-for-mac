status: partial

summary:
- Closed two clusters: PF16 Legacy CVTTSS2SI/low-word storage and PF8 Legacy's undefined exceptional integer conversion, with bounded small-frame admissions.
- Seed 1 Smart 180/4/116 -> 211/3/86; fresh seed 6 189/13/98 -> 217/13/70 (exact/mismatch/refusal).
- All original exact cases and Classic results preserved; corpus 39/39 unchanged, 37 exact / 2 mismatch.
- Each commit passes sanitizer campaigns, independent matrices and 92 retained controls; PF8's additional 216-row matrix fixes 55 sanitizer errors.
- Corrected native-expf trace registration; PF16 writer conclusions survive, and the previously unbound coefficient residual is now located. Third cluster remains in progress.

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

**Second cluster — PF8 Legacy (`ae8e3030` predecessor).** Machine evidence: `reports/fuzz/olmblur_C15_pf8.json`. The normal writer now uses the original floorf -> CVTTSS2SI -> low-byte rule, including int32 indefinite for nonrepresentable values, instead of an undefined direct float-to-uint8 conversion. Read-only instruction trace: index 112, pixel 2/red, `0x180007fe3` stores AL after EAX=`80000000`, rounded input bits `0000807f`; AEX stores `00`, old Mac O2 stores `ff`. Both indices 77/112 previously abort under UBSan; 77 happens to be final-output exact in the ordinary build, which does not make its undefined conversion valid.

The paired helper trace also observes negative-vs-positive invalid NaN sign differences before the writer (77: helper event 97, 15 words; 112: event 43, 9 words). These remain unchanged and are not claimed fixed. The integer writer converts either NaN to the same architecturally specified indefinite integer. No NaN payload rule or floating helper was changed. Complete direct AEX outputs bind to the cached worker and both corrected full PF8 outputs are exact.

| Campaign | PF16 predecessor E/M/R | PF8 E/M/R | Newly admitted exact |
|---|---|---|---:|
| Seed 1 | 196/3/101 | 211/3/86 | 15 |
| Seed 6 | 201/13/86 | 217/13/70 | 16 |

All 397 predecessor exact campaign cases and both Classic result sets are byte-identical. O2/sanitized complete result objects agree for 600 cases, 1,200 route executions, zero sanitizer findings. Gate-off has no PF8 Legacy error or mismatch on either seed. Admission now permits all legal small PF8 Legacy tuples with arbitrary uint8 source; all previous geometry/storage/budget/lifecycle guards remain.

The broad typed matrix is 720/720 exact before and after under sanitizers. An additional independent seed-15102026 matrix uses 4x9/7x11/18x18, Amount 1/1.5, Smoothness 1/25/45/66/84/100, Repeat 2/6/10, both Bias values and independently generated sparse-alpha random bytes with odd stride: 161 exact->exact and **55 sanitizer error->exact**, 216/216 corrected exact. These independent invalid-conversion witnesses supplement the two original fuzz cases. Production corpus is still 39/39, with 37 exact and 2 unchanged mismatches. Retained positives 12+80 and seven unit checks pass.

**Trace-scaffold correction (supersedes the unexplained PF16 oracle boundary above).** Inspection showed `AexLoader.register_libm_impls` installs expf by a direct dictionary update, bypassing the tracer's overridden registration method. Thus the first-commit direct fixture used Python binary64 `math.exp` rounded to float for expf, while the cached worker uses native binary32 expf. The tracer now explicitly registers all three observed native imports after the base table is created. The original AEX instructions, cached worker and external emulator source are unchanged.

Corrected native-import traces of 31/115/141 still bind to the cached oracle, have all helper stages identical and confirm the writer boundary. The original first-cluster correction stands. Matrix 292 now also binds: its **first** differing helper input is weights at event 0, word 1 (byte 4), AEX `3d9b0f3f`, Mac `3c9b0f3f`. Two symmetric coefficient words differ. Native expf import records are captured; the Mac PF16 Legacy worker computes binary64 exp and rounds it to float. That remaining operation is not changed by the PF8 commit. The older direct/cached discrepancy is retained as historical diagnostic evidence, with this measured explanation rather than a claim of an unexplained Windows/native dependency. `native-pf16-before`, `native-pf16-after` and `native-coeff-pf16` are included in second-commit machine evidence.

inference:
- The three paired witnesses locate the output mismatch at the PF16 Legacy conversion, after exact intermediate planes. The saturation is a port bug.
- The general PF16 one/two-pass and PF8 all-schedule admissions are supported by two seeds and independent matrices. Broader PF16 schedules remain unproven; corrected tracing locates a native expf versus binary64-exp coefficient boundary.
- Results are original CPU AEX emulation versus public Mac fake-host renders. They do not establish native Windows UCRT, installed/native AE, GPU, arbitrary ROI/downsample or full-domain compatibility.

changed_files:
- `core/olmblur_worker8_legacy.cpp`
- `core/olmblur_worker16_legacy.cpp`
- `mac/OLMBlur/OLMBlur.cpp`
- `tests/test_olmblur_generic_beta_lane_20260820.py`
- `tools/emulation/trace_olmblur_legacy_C15.py`
- `tools/fuzz/verify_blur_legacy_C15.py`
- `tools/fuzz/verify_blur_C15.py`
- `tools/fuzz/recheck_blur_C15.sh`
- `reports/fuzz/olmblur_C15_pf8.json`
- `reports/fuzz/olmblur_C15_pf16.json`
- `orchestra/reports/C15-olmblur-smart-r4.md`

verify:

At PF16 commit `ae8e3030`, from the worktree root:
```sh
bash tools/fuzz/recheck_blur_C15.sh 8567a0d base pf16 16
```
Expected: the campaign table above; 369 original exact cases preserved; matrix 71 exact->exact / 169 mismatch->exact; corpus 39/39 unchanged; retained 12+80 and seven unit checks pass. Driver writes only ticket scratch and does not rebaseline unless `C15_REBASELINE` is explicitly set.

At the PF8 commit:
```sh
bash tools/fuzz/recheck_blur_C15.sh ae8e3030 pf16 pf8 8
```
Expected PF8 campaign table, 397 predecessor exact preserved; matrix 720 exact->exact; conversion matrix 161 exact->exact / 55 error->exact; strict replay 39/39 unchanged; retained 12+80 and seven unit checks pass. The complete PF8 driver runs sequentially with jobs=2.

Additional diagnostic reproduction at this revision (the corrected tracer now exits 0):
```sh
s="$PWD/orchestra/state/C15-olmblur-smart-r4"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_blur_legacy_C15.py --scratch "$s" --report "$s/matrix-off-pf16.json" --before 8567a0d --depth 16 --diagnostic-after > "$s/matrix-off-pf16.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/trace_olmblur_legacy_C15.py --scratch "$s" --report "$s/native-coeff-pf16.json" --matrix-depth 16 --indices 292 > "$s/native-coeff-pf16.log" 2>&1
```
Expected matrix 207/509/4; tracer cached_binding=true, first_difference=event 0 weights, two words, AEX `3d9b0f3f` vs Mac `3c9b0f3f`.

next:
- Continue the remaining Smart coefficient/refusal cluster using the corrected native-import tracer.
- PF16 Legacy broader schedules remain gated; its measured expf/binary64-exp boundary is not repaired here. Audit the analogous expf registration pattern in the earlier C12 non-Legacy tracer before relying on its unbound-oracle interpretation.
