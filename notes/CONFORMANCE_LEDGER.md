# OLM Conformance Ledger

This ledger replaces percentage-style progress tracking. The only completion
status is `AE exact`; all other states are evidence or work states.

See `notes/AE_EXACT_CONFORMANCE.md` for definitions.

## Current Feature Status

| Plug-in / feature | 8bpc Software status | 16bpc status | 32bpc status | Evidence | Next required proof |
| --- | --- | --- | --- | --- | --- |
| ColorKeep synthetic helper | guarded | untested | untested | Synthetic CLI smoke only. | Real Windows Software reference or keep as support utility. |
| OLMBlur exact slices `case_0001..0005` | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0005` with `max_diff=0`; local verification report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmblur_exact_20260619/reports/ae_pixel_all_exact.json`. Non-legacy output writeback still uses a compatibility round-to-nearest-even shim while Legacy keeps `floor(x+0.5)`, so the implementation still needs binary-grounding even though the current AE cases pass. Current forecast IR: `notes/IR_OLMBlur.md`. | Binary-ground the true accumulation/writeback order behind the passing cases; then add 16/32bpc references. |
| OLMBlur residual slices `case_0006..0007` | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for the formerly residual `case_0006..0007` with `max_diff=0`. 2026-06-20 runtime trace proves the remaining CLI residual is present before byte writeback: `case_0006` Windows pre-writeback red is `185.49998474121094` while Mac CLI is exactly `185.5`; `case_0007` uses the Legacy `OLMBlur+0x7FDF` writeback family. Current IR: `notes/IR_OLMBlur.md`. | Do not change the passing AE behavior from this trace alone. Only continue the CLI residual if a later proof isolates the helper accumulation/border state. |
| OLMColorKey core RGB/color-space/Replace | AE exact for core packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0008` except the Edge Blur stress case `case_0009`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmcolorkey_exact_20260619/reports/ae_pixel_all_exact.json`. Normalized CLI is exact for core `case_0001..0004` and `case_0007`. | Add 16/32bpc references for the core path after Edge Blur is isolated. |
| OLMColorKey Edge Thin erode / Edge Blur | guarded residual / partly binary-grounded | untested | untested | 2026-06-19 AE pixel return has Edge Thin erode `case_0005/0006` exact and Edge Blur `case_0008` exact; `case_0009` still fails (`max=47 mean=0.069921`). AE-free CLI residuals remain: C++ `case_0008 max=15 mean=1.1104`, `case_0009 max=255 mean=1.2503`, Edge Thin `case_0005/0006 max=255 mean=0.3031`. Mac baseline trace logs are stored under `refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/`; Edge Thin top-edge witnesses are exactly `edge_thin_dist=17` / `edge_thin_limit=17`. | Windows runtime trace for Edge Blur `case_0009` seed/distance/weight/apply values; compare against Mac baseline before changing semantics. |
| OLMToonDilate cases `1..3` | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0003` with `max_diff=0`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmtoondilate_exact_20260619/reports/ae_pixel_all_exact.json`. AEX-style two-pass chamfer propagation plus semi-alpha RGB premultiply also makes the normalized Windows AE Software refs exact in Python and C++ CLI. Current IR: `notes/IR_OLMToonDilate.md`. | Add 16/32bpc references and keep the IR tied to the two-pass/premultiply evidence. |
| OLMDistanceGradation basic/extended/blur | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for all packaged basic/extended/blur cases (`12 + 16 + 1` cases, `max_diff=0`); local reports live under `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_*`. CLI residuals still indicate the AE plug-in path and AE-free harness are not yet described by a fully binary-grounded shared spec. Ghidra confirms 8bpc compose is an AE iterate callback over a prebuilt field world and reads the field green byte. Current forecast IR: `notes/IR_OLMDistanceGradation.md`. | Binary-ground field prep/OpenCV args enough to make the CLI harness explain the AE exact result; then add 16/32bpc references. |
| OLMSmoother v1 via Smoother2 compatibility | AE exact for packaged 8bpc v1 slices | untested | untested | 2026-06-20 AE pixel rerun corrected the v1 comp to `960x540`; `case_0001..0003` are exact with `max_diff=0`. Local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother_v1_20260619/reports/ae_pixel_exact.json`. | Decide whether v1 remains an independent compatibility path or is formally mapped to Smoother2; add 16/32bpc refs if v1 remains supported. |
| OLMSmoother2 no-key grid | AE exact for packaged 8bpc grid | untested | untested | 2026-06-19 and 2026-06-20 AE pixel returns are exact for all 12 no-key grid cases with `max_diff=0`; latest local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother2_no_key_grid_20260619/reports/ae_pixel_no_key_grid_exact.json`. This supersedes the earlier AE-free near-exact residual as an AE-host conformance fact. Current IR: `notes/IR_OLMSmoother2.md`. | Optional runtime trace only for binary-grounding if it returns; do not spend the next Windows trip on no-key tuning. |
| OLMSmoother2 legacy current-AEX witness / full recapture | current-reference pending | untested | untested | 2026-06-21 recapture confirms the current Windows AE 2026 Software AEX output for `case_0001 (712,406)` is `[106,106,106,135]`, matching runtime trace and Mac CLI with the included source input. The old `20260605_extra/OLMSmoother2/case_0001.png` has `[207,207,207,207]` and is retired as a correctness target. AE-saved before/control PNGs premultiply the source to `[168,168,168,207]`, so source-equivalence CLI checks must use the returned source input. Full 12-case current-AEX recapture request is `refs/reference_requests/smoother2_legacy_full_current_aex_recapture_20260621.json`. | Send/import the full current-AEX recapture package, then classify Smoother2 legacy against that current Software reference. |
| OLMDirectionalBlur | blocked | untested | untested | Broad PNG toggles rejected; binary facts partly documented. | New concrete asm/runtime evidence before more tuning. |
| OLMRadialBlur Zoom / tiny Rotation | guarded | untested | untested | Latest C++ guards pass: Zoom `case_0009 max=1 mean=0.0046`; tiny Rotation `case_0010 max=255 mean=0.0104` under a mean guard. These are not exact gates. Current IR: `notes/IR_OLMRadialBlur.md`. | AE exact check for Zoom slices and binary-ground the tiny Rotation high-max residual before claiming compatibility. |
| OLMRadialBlur Inner | binary-grounded / guarded | untested | untested | Runtime trace confirmed `rb_inner_only_strength_small` helper effective span resolves to `31`; C++ CLI default now mirrors the span-31 population and the span-stat guard passes. Old Inner remains expected-red: `case_0011 max=255 mean=23.0495`, `case_0012 max=255 mean=16.0039`, `case_0013 max=238 mean=18.0193`. Current IR: `notes/IR_OLMRadialBlur.md`. | Binary-ground remaining sampler/prepass/writeback residual, then Mac AE exact check. |
| OLMKiraKira strength0 / single-ray slices | binary-grounded / guarded | untested | untested | Runtime trace confirmed first `boxFilter` FilterEngine branch is OpenCV 4.5.5 AVX2 `FUN_1812e39d0`. IR now lives at `notes/IR_OLMKiraKira.md`. 2026-06-20 OpenCV 4.5.5 rerun keeps the same shape: single-ray guarded residuals `max=13/23/66`, old three-case OpenCV two-temp `case_0003 max=26 mean=1.0477`, and alias ROI byte-equivalent to ordinary two-temp. 2026-06-20 wrapper trace confirmed two `warpAffine` hits, three `boxFilter` hits, dsize `1924x1924`, length `50`, and ksize `(50,1)`, but did not isolate matrices, ROI rectangles, stage floats, aggregation, or compose values. | Need a deeper storage/sample-site trace or an AVX2 helper microprobe before changing implementation. More broad PNGs are low-value for this path. |

## Imported Runtime Proofs

- Imported `~/Downloads/olm_runtime_trace_return_windows_20260618.zip`
  with `refs/runtime_trace_packages/olm_runtime_trace_requests_20260618_075454.zip`.
- Summary files:
  - `refs/reports/runtime_trace_summary.json`
  - `refs/reports/runtime_trace_summary.md`
- Runtime facts now answered:
  - `radialblur_inner_runtime_trace_20260618`: Inner helper effective span
    resolves to `31`, matching `RCX+0x3a9ec = 31`.
  - `kirakira_opencv455_primitive_fact_20260618`: selected first
    `boxFilter` branch is `FUN_1812e39d0` / `CV_CPU_AVX2`.

- Imported `~/Downloads/olm_windows_action_bundle_20260620_overnight_blur_kirakira_return.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_1408_blur_kirakira/`.
- Summary/comparison files:
  - `refs/reports/runtime_trace_summary_olmblur_repeat_threshold_20260620.md`
  - `refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold_20260620/olmblur_repeat_threshold.md`
  - `refs/reports/runtime_trace_summary_kirakira_stage_values_20260620.md`
  - `refs/reports/runtime_trace_comparisons/kirakira_stage_values_20260620/olmkirakira_stage_values.md`
- Runtime facts now answered:
  - `olmblur_repeat_threshold_runtime_trace_20260619`: `case_0006`
    residual is pre-writeback accumulation/helper drift, not only byte
    rounding; `case_0007` uses the Legacy `+0x7FDF` writeback family.
  - `kirakira_fun_181150790_stage_values_20260620`: wrapper choreography is
    confirmed, but stage values are still `trace-too-sparse`.

- Imported `~/Downloads/olm_runtime_trace_dense_all_20260620_164214_return_windows.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_dense_all_runtime_trace/olm_runtime_trace_dense_all_20260620_164214_return_windows.zip`.
- Summary/comparison files:
  - `refs/reports/dense_runtime_trace_20260620/runtime_trace_summary_dense_all_20260620_184543.md`
  - `refs/reports/dense_runtime_trace_20260620/runtime_trace_comparisons/dense_all_20260620_184543/index.md`
- Audit result: the zip is machine-readable and non-blank, but it mostly merges
  existing Windows trace evidence. The included
  `DENSE_RUNTIME_TRACE_RETURN_AUDIT_20260620.md` says no new live debugger trace
  was captured for `OLMSmoother2` legacy key/gamma, `OLMRadialBlur`,
  `OLMDirectionalBlur`, or `OLMToonDilate`; those placeholders were converted
  to explicit `not traced / not isolated` strings.
- Useful classifier outputs from the merged evidence:
  - `OLMBlur`: `legacy-border-or-all-same`.
  - `OLMColorKey Edge`: `edge-thin-border-threshold`.
  - `OLMDistanceGradation`: `constant-field-prep`.
  - `OLMKiraKira`: still `trace-too-sparse`.
  - `OLMSmoother2` legacy: still needs actual key/mask/class-plane/writeback
    live values despite the formal `answered` status.
- Follow-up package generated to make that boundary explicit:
  `refs/runtime_trace_packages/olm_runtime_trace_dense_live_followup_20260620_184655.zip`.
  This package forbids satisfying the request by merging old templates or
  replacing requested values with `not isolated`.

- Imported `~/Downloads/olm_runtime_trace_dense_live_followup_20260620_184655_return_windows_all_attempts.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_dense_live_followup_all_attempts/olm_runtime_trace_dense_live_followup_20260620_184655_return_windows_all_attempts.zip`.
- Summary/comparison files:
  - `refs/reports/dense_live_followup_20260620/runtime_trace_summary_dense_live_followup_20260620_213031.md`
  - `refs/reports/dense_live_followup_20260620/runtime_trace_comparisons/dense_live_followup_20260620_213031/index.md`
- Audit result: this return is materially better than the earlier dense-all
  return. It attempted all 9 request IDs under Windows AE/CDB, did not merge
  older return zips as answers, and did not use `not isolated` placeholders to
  fill values.
- Useful runtime facts:
  - `OLMSmoother2` legacy: breakpoints at `+0x36e0`, `+0x10550`, and
    `+0xc280` were armed. Hit counts are `2`, `6440`, and `44451`
    respectively before the run was stopped for timeout/log growth. The
    included excerpt preserves hit markers/counts but not the actual
    register/stack dumps around the two `+0x36e0` writeback-candidate hits.
  - `OLMBlur`: `case_0006` `(498,940)` watchpoint hit and recorded
    `xmm0=[0,0,0,185]`, `xmm6=[0,0,0,0.5]`, output bytes `ff b9 00 00`;
    `case_0007` rendered but the selected watchpoint timed out.
  - `OLMRadialBlur`: Inner rerun hit `+0x26e5` and `+0x1d18`, with
    `ctx+0x3a9ec=0x1f`, `r14d=0x1f`, `edx=1`, `r8d=0`, `r9d=0`, and
    `eax=0xbb8`, reinforcing the span-31 fact.
  - `OLMColorKey`: Edge rerun hit `+0x94b0` and `+0x8c90`; CDB logs contain
    register/stack snapshots, but AE later exited with an OLMColorKey access
    violation.
  - `OLMKiraKira`: `warpAffine`, `boxFilter`, and AVX2 branch breakpoints hit;
    the intended `FUN_181150790` entry did not hit before an OLMKiraKira access
    violation.
  - `OLMSmoother2` no-key: `FUN_180010550` D7CA entry/return hits were captured
    for key `0x50000001`; this is optional binary-grounding because the AE grid
    already passes.
- Failed-but-useful attempts:
  - `OLMDistanceGradation`: module loaded and breakpoints were armed, but no
    requested breakpoint hit before AE exit/crash.
  - `OLMDirectionalBlur`: AE hit a WINHTTP access violation before the module
    resolved/loaded for the request.
  - `OLMToonDilate`: module loaded and breakpoints were armed, but they did not
    hit before an OLMToonDilate access violation.
- Next runtime package generated from this result:
  `refs/runtime_trace_packages/olm_runtime_trace_smoother2_legacy_writeback_extract_20260620_*.zip`.
  This asks Windows to extract the actual register/stack windows around the two
  `OLMSmoother2+0x36e0` hits from the existing 192 MB full log, instead of
  rerunning the full all-plugin trace.

- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_writeback_extract_20260620_213629_return_windows.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_smoother2_legacy_writeback_extract/olm_runtime_trace_smoother2_legacy_writeback_extract_20260620_213629_return_windows.zip`.
- Summary file:
  `refs/reports/smoother2_legacy_writeback_extract_20260620/runtime_trace_summary_smoother2_legacy_writeback_extract_20260620_231855.md`.
- Result: `failed_no_writeback_hits_found`, but this is useful proof. The
  existing full log was available, but its two `HIT_FUN_1800036e0_writeback_candidate`
  matches were only breakpoint setup/listing lines, not actual hits. A scoped
  rerun of `ae_pixel_olmsmoother2_legacy_20260619` completed the legacy cases,
  but `OLMSmoother2+0x36e0` never fired.
- Interpretation: `+0x36e0` / `FUN_1800036e0` is the float writer, not the
  active 8bpc writer for this AE pixel validation path. The 8bpc writer target
  is `+0x3370` / `FUN_180003370`, via wrapper `+0x3d00` / `FUN_180003d00`.
- Next package generated from this failed trace:
  `refs/runtime_trace_packages/olm_runtime_trace_smoother2_legacy_u8_writer_trace_20260620_*.zip`.
  This asks Windows to trace the actual 8bpc writer instead of repeating the
  failed float-writer breakpoint.

- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_u8_writer_trace_20260620_232223_return_windows.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_smoother2_legacy_u8_writer_trace/olm_runtime_trace_smoother2_legacy_u8_writer_trace_20260620_232223_return_windows.zip`.
- Summary/comparison files:
  - `refs/reports/smoother2_legacy_u8_writer_trace_20260620/runtime_trace_summary_smoother2_legacy_u8_writer_trace_20260620_233427.md`
  - `refs/reports/smoother2_legacy_u8_writer_trace_20260620/runtime_trace_comparisons/smoother2_legacy_u8_writer_trace_20260620_233427/index.md`
- Runtime facts:
  - `OLMSmoother2+0x3370` / `FUN_180003370` hit 26 times for
    `ae_pixel_olmsmoother2_legacy_20260619 case_0001`; first 20 entry hits
    were returned with register, stack, and p5-p9 memory dumps.
  - `OLMSmoother2+0x3d00` / `FUN_180003d00` wrapper hit once.
  - This confirms the active 8bpc writer path. It is still entry-level proof:
    loop locals, `FUN_18000cce0` output floats, and packed store bytes were not
    decoded from the entry breakpoints.
- Local diff witness selected for the next conditional trace:
  `case_0001` pixel `(712,406)`, expected RGBA `[207,207,207,207]`, current
  candidate RGBA `[106,106,106,135]`, max diff `101`.
- Next package generated:
  `refs/runtime_trace_packages/olm_runtime_trace_smoother2_legacy_u8_pixel_trace_20260620_*.zip`.
  This asks Windows to break inside `FUN_180003370` at `+0x3510` and `+0x360e`
  only when local x/y equals `(712,406)`.

- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_u8_pixel_trace_20260620_233732_return_windows.zip`.
- Stored copy:
  `handoffs/windows_returns/20260621_smoother2_legacy_u8_pixel_trace/olm_runtime_trace_smoother2_legacy_u8_pixel_trace_20260620_233732_return_windows.zip`.
- Summary files:
  - `refs/reports/smoother2_legacy_u8_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_u8_pixel_trace_20260621_0040.md`
  - `refs/reports/smoother2_legacy_u8_pixel_trace_20260621/cdb_console_final_entrycmd_utf16.txt`
- Runtime fact:
  - The high-diff pixel trace partially answered the request. It did not
    capture the earlier `+0x3510` float snapshot, but it captured the packed
    writer value at `OLMSmoother2+0x3610`, immediately after the final
    `MOV dword ptr [RSI],EAX` for the target output address.
  - Observed packed value: `EAX=c8c8c887`, little-endian bytes
    `87 c8 c8 c8`, interpreted as A/R/G/B `[135,200,200,200]`.
  - AE PNG candidate at `(712,406)` is `[106,106,106,135]`, which matches
    premultiplying the stored straight-ish RGB by alpha:
    `round(200 * 135 / 255) = 106`.
- Interpretation: the case_0001 max residual is not a byte rounding/store
  problem. The writer is receiving alpha/RGB that already imply the failing
  PNG value. The next proof should move upstream to `FUN_18000cce0` /
  polygon/composite output for `(712,406)`, or to the class-plane/polygon
  inputs that feed that composite.

- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_cce0_pixel_trace_20260621_005332_return_windows.zip`.
- Stored copy:
  `handoffs/windows_returns/20260621_smoother2_legacy_cce0_pixel_trace/olm_runtime_trace_smoother2_legacy_cce0_pixel_trace_20260621_005332_return_windows.zip`.
- Summary files:
  - `refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_cce0_pixel_trace_20260621_0145.md`
  - `refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/cdb_console_final_datwatch_utf16.txt`
- Runtime fact:
  - The target-pixel trace answered the upstream composite question at the
    `FUN_18000cce0` return boundary. For `case_0001 (712,406)`, cce0 returned
    floats `[0.57797289, 0.57797289, 0.57797289, 0.52794117]`.
  - The same writer frame packed `EAX=c8c8c887`, i.e. little-endian bytes
    `87 c8 c8 c8` / A/R/G/B `[135,200,200,200]`.
  - Writer flag byte `[RBP+0x19]` was `00`; no writer-side premultiply branch
    explains the residual.
  - The PNG candidate `[106,106,106,135]` follows from AE/export
    premultiplication of the stored straight RGB (`round(200 * 135 / 255)`).
- Interpretation: final u8 writeback, writer premultiply selection, and the
  RGB gamma/OETF packing step are no longer the primary suspects for this
  witness pixel. The remaining mismatch is inside `FUN_18000cce0` or earlier:
  polygon construction (`FUN_18000c280`), class-plane/key setup, or the
  bb10/c0d0/ab00/b120 composite stages.
- Next package generated:
  `refs/runtime_trace_packages/olm_runtime_trace_smoother2_legacy_cce0_internals_trace_*.zip`.
  It asks Windows for the same target pixel but with stage-level cce0 internals:
  after `FUN_18000c280`, before/after `FUN_18000bb10`, after
  `FUN_18000c0d0`, after `FUN_18000ab00`, after `FUN_18000b120`, and final
  cce0 output.

- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_cce0_internals_trace_20260621_011845_return_windows.zip`.
- Stored copy:
  `refs/returns/windows/20260621_011845_smoother2_cce0_internals/olm_runtime_trace_smoother2_legacy_cce0_internals_trace_20260621_011845_return_windows.zip`.
- Summary files:
  - `refs/reports/runtime_trace_summary.json`
  - `refs/reports/runtime_trace_summary.md`
- Result: `failed_partial`, and intentionally not an answered internals trace.
  The target-pixel `FUN_18000cce0` stage chain for `case_0001 (712,406)` was
  not captured.
- Useful facts:
  - `OLMSmoother2+0xcd5f` is reachable; an unconditional probe hit 64 times.
  - `RSI` at `+0xcd5f` points to x/y dwords, but the target qword
    `00000196\`000002c8` was not seen by the attempted coordinate conditions.
  - At `+0xcd5f`, `mov r14,[rbp+0x90]` has not executed yet; polygon count
    should be read from `[rbp+0x90]` or after stepping the instruction.
- Interpretation: the next trace should not repeat broad coordinate filters at
  `+0xcd5f`. It should drive from the already successful writer/data-watch
  target or a target output-address watchpoint back into `FUN_18000cce0` and
  then collect the stage internals.
- Next package supersedes the failed broad internals request with
  `olmsmoother2_legacy_cce0_internals_r9_callsite_trace_20260621`: break at
  `OLMSmoother2+0x350b` when `dwo(@r9)==0x2c8` and `dwo(@r9+4)==0x196`, then
  collect one-shot `FUN_18000cce0` stage values.

- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_cce0_internals_r9_callsite_20260621_022708_return_windows.zip`.
- Stored copy:
  `refs/returns/windows/20260621_022708_smoother2_cce0_internals_r9_callsite/olm_runtime_trace_smoother2_legacy_cce0_internals_r9_callsite_20260621_022708_return_windows.zip`.
- Summary files:
  - `refs/reports/runtime_trace_summary.json`
  - `refs/reports/runtime_trace_summary.md`
- Result: `failed_partial`. The `OLMSmoother2+0x350b` breakpoint with
  `dwo(@r9)==0x2c8 && dwo(@r9+4)==0x196` was installed exactly as requested,
  but the target callsite condition did not hit before AE completed and reached
  the known shutdown AV.
- Interpretation: coordinate-only filtering is still too fragile for this
  target. The next request should reuse the successful writer-entry/data-watch
  anchor: compute `$t3` at `OLMSmoother2+0x3370`, stop at `+0x34b0` when
  `@rsi == @$t3`, then trace the same `FUN_18000cce0` internal stages before
  the final `+0x3610` store.

- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_cce0_internals_targetaddr_20260621_025613_return_windows.zip`.
- Stored copy:
  `refs/returns/windows/20260621_025613_smoother2_cce0_internals_targetaddr/olm_runtime_trace_smoother2_legacy_cce0_internals_targetaddr_20260621_025613_return_windows.zip`.
- Summary files:
  - `refs/reports/runtime_trace_summary.json`
  - `refs/reports/runtime_trace_summary.md`
- Result: `failed_partial`. Writer entry `+0x3370` did execute and computed
  latest candidate addresses `$t1=000001cd\`22545c20`,
  `$t2=000001cd\`23c1a020`, `$t3=000001cd\`2145a020`, but the requested
  `+0x34b0 @rsi == @$t3` condition did not hit.
- Interpretation: `$t3` must not be assumed as the sole output-world owner in
  this run. The next request should arm write watchpoints for all `$t1/$t2/$t3`
  and compare `+0x34b0` against all three candidates. If internals still do
  not hit, the return must at least identify which candidate receives the
  target final write.
- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_cce0_internals_multiaddr_probe_20260621_031230_return_windows.zip`.
- Stored copy:
  `refs/returns/windows/20260621_031230_smoother2_cce0_internals_multiaddr_probe/olm_runtime_trace_smoother2_legacy_cce0_internals_multiaddr_probe_20260621_031230_return_windows.zip`.
- Result: `failed_partial`, but with a useful new fact: `$t3=00000272\`2244a020`
  receives the target pixel write at `OLMSmoother2+0x3610`; the store value is
  still `EAX=00000000c8c8c887` and stack xy is `(712,406)`.
- Interpretation: `+0x34b0` is the wrong/too-fragile anchor for this witness.
  The next package uses the confirmed `$t3` output address at the actual
  pre-call site: break at `OLMSmoother2+0x350b` when `@rsi == @$t3`, then arm
  the `FUN_18000cce0` internal stage probes.
- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_cce0_internals_t3_rsi_callsite_20260621_032645_return_windows.zip`.
- Stored copy:
  `refs/returns/windows/20260621_032645_smoother2_cce0_internals_t3_rsi_callsite/olm_runtime_trace_smoother2_legacy_cce0_internals_t3_rsi_callsite_20260621_032645_return_windows.zip`.
- Result: `failed_partial`. The `+0x350b @rsi == @$t3` pre-call breakpoint did
  not hit, and the independent `+0x350b @rdi==0x2c8 && @r14==0x196` check also
  completed without a hit. This makes `+0x350b` unsuitable as the next anchor.
- Interpretation: the next package anchors on the reliable `+0x3610` writer
  stop and asks Windows to dump/replay the reconstructed `FUN_18000cce0`
  arguments from that writer frame.
- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_cce0_internals_replay_from_writer_20260621_132250_return_windows.zip`.
- Stored copy:
  `refs/returns/windows/20260621_132250_smoother2_cce0_internals_replay_from_writer/olm_runtime_trace_smoother2_legacy_cce0_internals_replay_from_writer_20260621_132250_return_windows.zip`.
- Result: `failed_partial`, but useful. Windows skipped unsafe live replay and
  returned the reconstructed `FUN_18000cce0` argument block plus returned floats.
  Mac CLI stage trace now matches the Windows CPU AEX witness:
  Windows `cce0=[0.57797289,0.57797289,0.57797289,0.52794117]`; Mac
  `cce0_after_b120=[0.57797277,0.57797277,0.57797277,0.52794117]`.
- Interpretation: the old `case_0001` legacy PNG residual is now a reference
  provenance problem, not a proven algorithm bug. A new Windows reference
  request was added:
  `refs/reference_requests/smoother2_legacy_current_aex_recapture_20260621.json`.
- Imported `~/Downloads/olm_reference_return_windows_smoother2_legacy_current_aex_recapture_20260621.zip`.
- Stored copy:
  `refs/returns/windows/20260621_smoother2_legacy_current_aex_recapture/olm_reference_return_windows_smoother2_legacy_current_aex_recapture_20260621.zip`.
- Imported reference:
  `refs/win_references/olm_reference_return_windows_smoother2_legacy_current_aex_recapture_20260621/OLMSmootherv2/reference_manifest.json`.
- Result: current Windows AE 2026 Software AEX output at `(712,406)` is
  `[106,106,106,135]`, matching Mac CLI direct-source output and the runtime
  trace. The old legacy PNG `[207,207,207,207]` should not be used as a CPU
  Software correctness target for this witness.

Re-import command:

```sh
python3 scripts/intake_olm_return.py ~/Downloads/olm_runtime_trace_return_windows_20260618.zip --runtime-package refs/runtime_trace_packages/olm_runtime_trace_requests_20260618_075454.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md
python3 refs/scripts/smoke_runtime_trace_return.py
```

## Pending Runtime Trace Requests

- OLMSmoother2 legacy key/gamma setup/writeback package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_legacy_key_gamma_20260620_154802.zip`
  (ignored local artifact, stored in the project folder for handoff). This is
  now the priority Smoother trace. It asks Windows to trace `case_0001`,
  `case_0002`, `case_0003`, and `case_0010` at top-edge witness pixels so the
  remaining `0/7` legacy failures can be classified as Color Key polarity,
  premultiply/unpremultiply, gamma setup, class-plane generation, or final
  writeback.
- OLMSmoother2 no-key grid scan/append/writeback package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_no_key_grid_idx7_context_with_mac_baseline_20260619_041000.zip`
  (ignored local artifact, stored in the project folder for handoff). This is
  now optional/historical because the AE-host no-key grid is exact. If it
  returns, use it only to tighten binary-grounded IR and avoid PNG tuning.
- OLMBlur repeat/writeback threshold package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_with_mac_baseline_20260619_030743.zip`
  (ignored local artifact, stored in the project folder for handoff). This
  supersedes the earlier `olm_runtime_trace_olmblur_repeat_threshold_20260619_011208.zip`
  because it includes Mac baseline trace logs. It asks Windows to trace
  `case_0006` at `(498,940)` and `case_0007` at `(0,0)`, `(488,941)`,
  `(488,942)` to distinguish pre-writeback accumulation, exact tie writeback,
  and Legacy border/all_same state.
- ColorKey Edge Thin / Edge Blur package:
  `refs/runtime_trace_packages/olm_runtime_trace_colorkey_edge_erode_blur_with_mac_baseline_20260619_031350.zip`
  (ignored local artifact, stored in the project folder for handoff). This
  supersedes `olm_runtime_trace_colorkey_edge_erode_blur_20260619_025301.zip`
  because it includes Mac baseline trace logs. It traces both Edge Thin erode
  witnesses (`case_0005/0006`) and Edge Blur witnesses (`case_0008/0009`)
  around `FUN_1800094b0`, `FUN_180008c90`, `FUN_180008320`,
  `FUN_1800085b0`, and `FUN_1800049a0`.
- OLMDistanceGradation field prep / Constant mode package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_field_prep_opencv_args_20260619_030427.zip`
  (ignored local artifact, stored in the project folder for handoff). This asks
  Windows to trace `case_0020`, `case_0022`, and `case_0029` field construction,
  OpenCV `distanceTransform` / `GaussianBlur` arguments, threshold/minmax
  normalization, Constant-mode binarization, `FUN_181170870` input field bytes,
  and final compose/writeback values.

## Pending AE-Host Pixel Validation Requests

- OLMBlur exact-only request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmblur_exact_20260619_033243.zip`
  (7 normalized Software cases, exact-only thresholds).
- OLMColorKey exact-only request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmcolorkey_exact_20260619_032431.zip`
  (9 legacy ColorKey cases, exact-only thresholds). This is the ColorKey final
  gate shape; it must return `max_diff=0` for all cases to count as Mac AE
  exact evidence.
- OLMToonDilate exact-only request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmtoondilate_exact_20260619_033243.zip`
  (3 normalized Software cases, exact-only thresholds).
- OLMDistanceGradation basic exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_basic_exact_20260619_032933.zip`
  (12 normalized Software cases, exact-only thresholds).
- OLMDistanceGradation extended exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_extended_exact_20260619_032933.zip`
  (16 normalized Software cases, exact-only thresholds).
- OLMDistanceGradation blur exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_blur_exact_20260619_032933.zip`
  (`case_0029`, normalized Software reference, exact-only threshold).
- OLMSmoother v1 exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother_v1_20260619_031933.zip`
  (3 original v1 cases, exact-only thresholds).
- OLMSmoother2 legacy key/gamma request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother2_legacy_20260619_031933.zip`
  (7 legacy Smoother2 cases covering key/gamma/no-key slices, exact-only
  thresholds).
- OLMSmoother2 no-key grid request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother2_no_key_grid_20260619_031933.zip`
  (12 no-key grid cases, exact-only thresholds).

These are validation packages, not implementation proof by themselves. A pass
means the returned Mac AE render PNGs match the packaged Windows Software
reference PNGs with `max_diff=0`.

## Imported AE-Host Exact Proofs

- Imported `~/Downloads/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260620_1425.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_1425_smoother_priority/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260620_1425.zip`.
- Local verification directory:
  `refs/reports/ae_host_validation_20260620_1425/`.
- Exact-only result: `62/70` cases exact.
- New result relative to the previous return:
  - `OLMSmoother v1`: corrected `960x540` rerun is `3/3` exact.
- Still failing:
  - `OLMColorKey`: Edge Blur `case_0009` remains `max=47 mean=0.069921`.
  - `OLMSmoother2` legacy key/gamma slices remain `0/7` exact, with max diff
    up to `254`.
- No runtime trace result was included in this return; the runtime trace zips in
  the bundle are request packages only.

- Imported `~/Downloads/olm_windows_action_bundle_20260619_smoother2_legacy_followup_addendum_20260620.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_smoother2_legacy_followup_addendum/olm_windows_action_bundle_20260619_smoother2_legacy_followup_addendum_20260620.zip`.
- Local verification directory:
  `refs/reports/ae_host_validation_20260620_smoother2_legacy_followup/`.
- This addendum is AE pixel validation evidence, not a CDB/runtime trace.
- Exact-only result: the adjustment-layer rerun keeps
  `OLMSmoother2` legacy key/gamma at `0/7` exact (`case_0001 max=101`,
  other cases up to `254`).
- `case_0001` parameter sweep did not improve the original result:
  `Gamma Correction=0` and `GPU Rendering=2` matched original metrics,
  while `Smoother Version=1`, `Gamma Correction=2`, `Smooth Range=1`, and
  `Smoother Version=1 + Gamma Correction=0` were worse.
- Interpretation: the residual is stable and unlikely to be caused by direct
  layer vs adjustment layer, transient AE rendering, or those gross UI toggles.
  The priority remains runtime/static proof around legacy key/gamma setup and
  final writeback.

- Imported `~/Downloads/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260619_2335.zip`.
- Stored copy:
  `handoffs/windows_returns/20260619_2335/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260619_2335.zip`.
- Local verification directory:
  `refs/reports/ae_host_validation_20260619_2335/`.
- Exact-only result: `59/70` cases exact.
- AE exact in this return:
  - `OLMBlur`: `7/7`.
  - `OLMToonDilate`: `3/3`.
  - `OLMDistanceGradation`: basic `12/12`, extended `16/16`, blur `1/1`.
  - `OLMSmoother2` no-key grid: `12/12`.
  - `OLMColorKey`: `8/9`; `case_0009` remains a real Edge Blur residual.
- Not meaningful as algorithm failure:
  - `OLMSmoother v1`: `3/3` shape mismatches because returned candidates are
    `1920x1080` while the references are `960x540`.
- Still failing:
  - `OLMSmoother2` legacy key/gamma slices: `0/7` exact, with max diff up to
    `254`.

- Imported `~/Downloads/olm_port_handoff_ae_host_validation_20260618_172339_1_windows_result.zip`.
- Stored copy:
  `handoffs/ae_host_validation_returns/ae_host_validation_return_20260618_232926_windows.zip`.
- Summary files:
  - `refs/reports/ae_host_validation_20260618_232926/exact_return/AE_HOST_EXACT_SUMMARY.md`
  - `refs/reports/ae_host_validation_20260618_232926/exact_return/reports/AE_VALIDATION_EXACT_REPORT.md`
- Render context: Windows AE Software, `project_gpu_accel_type.current_name=SOFTWARE`, raw `1816`.
- Exact-only result: `33/48` cases exact. This is evidence, not overall
  completion, and does not replace final Mac AE exact validation.
- Failure classification:
  `refs/reports/ae_host_validation_20260618_232926/ae_host_exact_failure_classification_20260619_003051.md`.
  The main split is:
  `OLMColorKey case_0009` is a real Edge residual, `OLMDistanceGradation`
  extended/basic normalized CLI residuals still need binary-grounding, while
  `OLMBlur case_0001..0004` and `OLMToonDilate case_0001..0003` are likely
  stale packaged-reference or host-package drift because normalized returned
  Software refs are already CLI exact for those slices.
- Normalized-reference CLI triage:
  - `refs/reports/ae_host_validation_20260618_232926/normalized_refs/`
  - `refs/reports/ae_host_validation_20260618_232926/cli_checks/`
  - `OLMBlur case_0001..0005` are exact against returned Software PNGs after
    the current non-Legacy writeback shim, so the old AE-host mismatch for
    `case_0001..0004` is stale-reference drift. This is still not the final
    binary-grounded explanation because the AEX writeback constant is `0.5`.
  - `OLMToonDilate` is exact in the normalized Software CLI checks after the
    two-pass propagation/premultiply fix.
  - `OLMColorKey` Edge paths and `OLMDistanceGradation` still have
    implementation/spec residuals after normalization.
  - `OLMDistanceGradation` Blur Mode was probed under
    `refs/reports/ae_host_validation_20260618_232926/distancegradation_blur_probe/`;
    no production change was justified.

## AE Exact Proofs Still Needed

- Return AE-host pixel renders for the packaged request zips under
  `AE_PIXEL_VALIDATION/`.
- Current normalized AE-host handoff package:
  `handoffs/ae_host_validation/olm_port_handoff_ae_host_validation_normalized_20260619_003640.zip`.
  This package uses `pixel_reference_profile=normalized-20260618` so the
  OLMBlur/OLMToonDilate stale-reference drift from the first AE-host return is
  not reintroduced.
- Treat these as AE wiring and exactness checks, not as automatic completion of
  guarded slices.
- Add 16bpc and 32bpc Windows Software references after the 8bpc IR is stable.
