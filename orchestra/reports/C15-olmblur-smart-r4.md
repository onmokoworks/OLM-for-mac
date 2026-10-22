status: done

summary:
- Closed three clusters in separate commits: PF16 Legacy writer/one-two-pass admission, PF8 Legacy defined conversion/full admission, and bounded signed-HDR PF32 non-Legacy admission.
- Seed 1 Smart 180/4/116 -> 220/3/77; fresh seed 6 189/13/98 -> 226/13/61 (exact/mismatch/refusal).
- All 369 original exact campaign cases and Classic results preserved; corpus remains 39/39, 37 exact / 2 mismatch, with no expectation edits.
- Each commit passes sanitizer campaigns, independent matrices, 92 retained controls and seven unit checks; no newly admitted mismatch.
- Rejected PF32 Legacy native-expf substitution because it changes a frozen fixture; corrected tracing records the math-contract split. Stop at three closed clusters.

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

**Third cluster — bounded signed HDR PF32 non-Legacy (`293f9947` predecessor).** Machine evidence: `reports/fuzz/olmblur_C15_hdr.json`. No numerical core changes. The existing small-source range scan now accepts every active ARGB component in [-16,16], including negative zero/subnormals; unordered, infinite and larger finite components still refuse. The existing PF32 generic small-frame tuple remains non-Legacy, Repeat <= 2, with all prior legal parameter/storage/geometry/work/lifecycle checks. This widens the source domain without clamping, rescaling, changing arithmetic, copying a reference, or unlocking higher repeats/Legacy.

| Campaign | PF8 predecessor E/M/R | Final E/M/R | Newly admitted exact |
|---|---|---|---:|
| Seed 1 | 211/3/86 | 220/3/77 | 9 |
| Seed 6 | 217/13/70 | 226/13/61 | 9 |

All 428 predecessor exact cases and both Classic result sets remain byte-identical. O2/sanitized full result objects match for 600 cases (1,200 sanitized routes); zero findings. Every newly admitted result equals both original Smart AEX and gate-off. Transitive preservation covers all 369 ticket-baseline exact cases. Total seed-1 gain is 39 refusal->exact plus one mismatch->exact; seed-6 gain is 37 refusal->exact.

Independent bounded-HDR matrix: seed 15321026, six geometries, ten Amount boundaries including float neighbours and 1000, Repeat 1/2, both Bias values, three Smoothness values, random/edge/opaque/transparent inputs. Every ARGB channel includes independently generated signed/HDR values; edge values include ±16, ±1, signed zeros, both-sign smallest subnormal and normal floats. All 240 gate-off and all 240 final production rows are exact with sanitizers. Odd strides and source/destination guards are retained. All 64 one-away boundary rows (each channel x Repeat 1/2 x ±16's outward float neighbour, ±largest finite, ±infinity, quiet/signaling NaN) remain clean refusals at both revisions. This conservative range deliberately does not admit arbitrary finite float magnitudes.

Final corpus table:

| Saved Smart status | Baseline | PF16 | PF8 | Bounded HDR final |
|---|---:|---:|---:|---:|
| Exact | 37 | 37 | 37 | 37 |
| Mismatch | 2 | 2 | 2 | 2 |
| Refusal | 0 | 0 | 0 | 0 |

Every corpus result object and all original input/parameter/reduction/history data remain unchanged; no rebaseline was needed. Final sanitized replay is 39/39 against the explicit cached-worker hash. Remaining saved mismatches are indices 40 (PF16 non-Legacy Repeat 9) and 99 (PF32 nonfinite). The unshrunk seed-1 campaign also retains Legacy PF32 index 272. Final retained controls are 12/12 plus 80/80 with sanitizers. Seven unit checks and `git diff --check` pass.

**Rejected experiment, recorded before moving to the HDR cluster.** Native-import tracing of PF32 Legacy indices 220/272 binds to the cached worker and first differs in weights at events 0/48 respectively: 220 AEX `e6507f3f` vs Mac `e5507f3f` (word 16), 272 AEX `dca97d3f` vs Mac `dba97d3f` (word 17), two symmetric coefficient words each. The original builder `0x180009e10` calls expf; the production PF32 Legacy implementation currently evaluates binary64 exp then converts to float.

A scratch candidate substituting native expf was **rejected**, not promoted: retained controls fall from 80/80 to 78/80. Both failing checks are optional-checkin variants of `legacy_24x24_smooth37_5` (24x24, Amount 11, Smoothness 37.5, Repeat 3, Bias 2, Legacy on). Baseline output SHA256 is `fb2b0d121cf6ee7c789ed8be03635f5a92942779574ed99475b9a9dea0bfaf33`; candidate is `d4ae8a9620d6745054d4fcdd28c0419d2b33bf8d505f4082cd31025731acd19e`. There are 473 differing bytes / 469 float words; first byte 24, original retained word `69b87dbe` versus candidate `66b87dbe`. Both public calls return zero and preserve source/guards; this is a numeric regression, not a sanitizer failure. The initial production experiment was immediately reverted; the committed `probe_blur_expf_C15.py` reproduces the experiment entirely in scratch. Final `core/olmblur_worker32_legacy.cpp` is unchanged from the ticket baseline.

This establishes a new frozen-fixture boundary and prevents replacing one reference contract with another. The stored fixture is not rebaselined and no per-case coefficient selection is introduced. Native Windows UCRT behavior is not established by changing the host libm callback. The coefficient investigation is left for a separate ticket.

Final execution note: the HDR driver initially stopped in the diagnostic output collector because the adapter intentionally strips environment variables prefixed `OLM`; the observer variable was renamed, the probe and remaining validation steps reran successfully with explicit worker binding. No failing collector output is accepted as numerical evidence. All final fuzz/regression commands are serial campaigns with jobs=2. Scratch build directories/objects were removed; remaining scratch is 38,086,859 bytes of logs/reports/corpora, below 5 GiB. No task build/emulator process remains.

inference:
- The three paired witnesses locate the output mismatch at the PF16 Legacy conversion, after exact intermediate planes. The saturation is a port bug.
- The PF16 one/two-pass, PF8 all-schedule and bounded-HDR PF32 one/two-pass admissions are supported by two seeds and independent matrices. Broader schedules/source magnitudes remain unproven. Native-expf substitution conflicts with an existing exact fixture and is not an acceptable global fix.
- Results are original CPU AEX emulation versus public Mac fake-host renders. They do not establish native Windows UCRT, installed/native AE, GPU, arbitrary ROI/downsample or full-domain compatibility.

changed_files:
- `core/olmblur_worker8_legacy.cpp`
- `core/olmblur_worker16_legacy.cpp`
- `mac/OLMBlur/OLMBlur.cpp`
- `tests/test_olmblur_generic_beta_lane_20260820.py`
- `tools/emulation/trace_olmblur_legacy_C15.py`
- `tools/fuzz/verify_blur_legacy_C15.py`
- `tools/fuzz/probe_blur_expf_C15.py`
- `tools/fuzz/verify_blur_C15.py`
- `tools/fuzz/recheck_blur_C15.sh`
- `reports/fuzz/olmblur_C15_hdr.json`
- `reports/fuzz/olmblur_C15_pf8.json`
- `reports/fuzz/olmblur_C15_pf16.json`
- `orchestra/reports/C15-olmblur-smart-r4.md`

verify:

At PF16 commit `ae8e3030`, from the worktree root:
```sh
bash tools/fuzz/recheck_blur_C15.sh 8567a0d base pf16 16
```
Expected: the campaign table above; 369 original exact cases preserved; matrix 71 exact->exact / 169 mismatch->exact; corpus 39/39 unchanged; retained 12+80 and seven unit checks pass. Driver writes only ticket scratch and does not rebaseline unless `C15_REBASELINE` is explicitly set.

At PF8 commit `293f9947`:
```sh
bash tools/fuzz/recheck_blur_C15.sh ae8e3030 pf16 pf8 8
```
Expected PF8 campaign table, 397 predecessor exact preserved; matrix 720 exact->exact; conversion matrix 161 exact->exact / 55 error->exact; strict replay 39/39 unchanged; retained 12+80 and seven unit checks pass. The complete PF8 driver runs sequentially with jobs=2.

At the final bounded-HDR commit:
```sh
bash tools/fuzz/recheck_blur_C15.sh 293f9947 pf8 hdr 32
```
Expected final 220/3/77 and 226/13/61; 428 predecessor exact cases unchanged; 240/240 signed-HDR matrix exact; 64/64 clean boundary refusals; corpus 39/39 unchanged; retained 12+80 and seven unit checks pass. The diagnostic expf candidate intentionally fails two retained checks; its probe exits 0 only when that known rejection is reproduced. No source edit or corpus rebaseline is performed by the driver.

Additional diagnostic reproduction at the final revision (the corrected tracer exits 0):
```sh
s="$PWD/orchestra/state/C15-olmblur-smart-r4"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_blur_legacy_C15.py --scratch "$s" --report "$s/matrix-off-pf16.json" --before 8567a0d --depth 16 --diagnostic-after > "$s/matrix-off-pf16.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/trace_olmblur_legacy_C15.py --scratch "$s" --report "$s/native-coeff-pf16.json" --matrix-depth 16 --indices 292 > "$s/native-coeff-pf16.log" 2>&1
```
Expected matrix 207/509/4; tracer cached_binding=true, first_difference=event 0 weights, two words, AEX `3d9b0f3f` vs Mac `3c9b0f3f`.

next:
- Three clusters closed; stop under the ticket threshold. Final seed-1 residual is 3 mismatches / 77 refusals, not full compatibility.
- Reconcile the frozen PF32 Legacy fixture's binary64-exp behavior with the cached oracle's native expf before changing coefficients; retain the measured 473-byte regression as a negative control.
- Investigate PF16 higher-repeat coefficient domains and remaining PF32 nonfinite NaN propagation; audit the analogous expf registration pattern in the older C12 tracer before using its unbound-oracle interpretation.
- Larger finite float magnitudes, higher-repeat small PF32/PF16 and other remaining refusal families require new bounded evidence. No release-gate or native AE promotion is requested.
