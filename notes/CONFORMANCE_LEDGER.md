# OLM Conformance Ledger

This ledger replaces percentage-style progress tracking. The only completion
status is `AE exact`; all other states are evidence or work states.

See `notes/AE_EXACT_CONFORMANCE.md` for definitions.

This ledger tracks three separate questions:

1. Is a declared case set `AE exact` against Windows AE Software?
2. Is Mac AE hands-on testing meaningful yet for this plug-in?
3. Which work lane is allowed next?

Do not assume a passing packaged case set means the plug-in is already safe to
eyeball in AE. Host usability and algorithm correctness are tracked separately.

Parameter-default and range sanity is tracked separately too. The current
source-backed Mac UI schema snapshot is
`refs/reports/mac_plugin_param_schema_20260629.md` /
`refs/reports/mac_plugin_param_schema_20260629.json`.
Use that report to answer "what UI value should this parameter have?" before
treating a mismatch as algorithm drift.

## Current Decision Matrix

Use this table to choose the next action. It is intentionally stricter than a
progress summary: if a row says a class of work is forbidden, do not spend time
there unless new evidence changes the row.

| Plug-in / feature | correctness_status | host_status | work_lane | next allowed action | forbidden action |
| --- | --- | --- | --- | --- | --- |
| ColorKeep | `guarded` | `host-smoke` | `parked` | Keep as support/helper unless a real Windows Software reference is requested. | Treat synthetic helper output as OLM compatibility. |
| OLMColorKey | 8bpc and 16bpc covered slices are `AE exact`; 32bpc untested | `host-stable` | `bitdepth-expand` | Preserve the passing 8/16bpc behavior; use the 32bpc float-output probe preview only when intentionally scheduled. | Visual/look tuning, broad algorithm changes, or PNG-only 32bpc exact claims. |
| OLMBlur | 8bpc `AE exact`; 16bpc narrow residual only | `host-visual-tuning-ready` | `binary-proof` | Preserve the new decomp-backed Legacy carry-prev rule. For `case_0006`, treat the answered 2026-07-01 witness as proof that Windows and Mac agree on pre-store float and stored word at the active points; next work is reference/export provenance, not writer surgery. `case_0007` remains the narrow Legacy family. | Broad rewrites, global rounding swaps, helper rewrites from the answered `case_0006` witness alone, or kernel tuning that risks the passing 8bpc slice. |
| OLMToonDilate | 8bpc `AE exact` | `host-stable` | `bitdepth-expand` | Add or validate 16/32bpc references for the existing exact slice. | Reopen the 8bpc two-pass dilation algorithm without new evidence. |
| OLMDistanceGradation | 8bpc `AE exact`; 16bpc not exact | `host-debuggable` | `binary-proof` | Preserve the 2026-06-29 Power and Constant binary-threshold fixes plus the new narrow Layer/no-bg source-ownership patch; use the new stable batch wrapper for future 16bpc reruns, but keep follow-ups witness-bounded (`case_0012/0016` Layer ownership, `case_0020/0022` Constant boundary) because the authoritative extended rerun is still only `1/16 exact`. | Revert the Power/Constant fixes, broaden Layer/no-bg changes outside the proven `render_mode=Layer && use_bg=0` path, or retune from broad PNGs / 8-bit viewer-space numbers without witness support. |
| OLMSmoother v1 | 8bpc `AE exact` | `host-stable` | `parked` | Leave v1 policy/bit-depth expansion until higher-priority plug-ins have stronger 16/32bpc coverage; then decide whether v1 remains independent or maps to Smoother2 compatibility. | Mix v1/v2 behavior without an explicit policy, or spend early 32bpc effort here before broader plugins are grounded. |
| OLMSmoother2 no-key | 8bpc `AE exact` | `host-debuggable` | `ae-validate` | Preserve no-key exact behavior; use only bounded regression checks. | Spend Windows/runtime trips on no-key tuning. |
| OLMSmoother2 legacy/key/gamma | `guarded` / writer-grounded residual | `host-debuggable` | `binary-proof` | Trace the 0004/0012 witness paths and keep the Smooth Range threshold fix. | Global fallback, alpha, index, curve-index, or `f270` changes without proof. |
| OLMDirectionalBlur | `blocked` | `host-debuggable` | `binary-proof` | Capture angle-0 rowdriver/valid-alpha and diagonal rotate/validity witnesses. | PNG-only exploration or broad AE look matching. |
| OLMRadialBlur | `guarded` / `blocked` | `host-debuggable` | `binary-proof` | Treat the remaining lanes separately: Zoom needs caller-collapse proof on `sampler -> +0xf252 -> +0xf250 -> +0xe -> final byte`, while tiny Rotation now points to upstream polar RGB / substitute-path population rather than validity-only alpha collapse. The current Mac source still lacks an explicit preserved-validity plane, and a 2026-07-01 propagated-validity probe showed that simply blurring the validity bits with the same kernel does not move either focused witness. | AE visual matching, blind alpha tuning, treating tiny Rotation as a validity-alpha issue, promoting propagated-validity-alpha as a fix, or global span/wrap toggles. |
| OLMKiraKira | `binary-grounded` / `blocked` | `host-smoke` | `parked` | Defer until the endgame unless a returned Windows witness makes the compose/writeback blocker cheap to close. Also keep in mind that the current Mac source still leaves several UI controls nonfunctional (`Merge Mode`, `Approximated Input`, `Brightness Gain`, `Highlight Radius`, ramps, and non-BlurMode-2 dispatch). | Pull it forward ahead of wider 16/32bpc expansion on stronger plug-ins, or re-tune luma/boxFilter/ray-helper/gain from broad PNGs. |

Current priority order:

1. `OLMBlur` 16bpc `binary-proof`, because the 2026-06-30 Windows 4pack return
   turned Legacy witness `(345,672)` into a direct pre-store proof and shrank
   the open space to non-Legacy `case_0006` plus old normalized 8bpc
   `(488,941)`.
2. `OLMRadialBlur` narrow proof, because the current Ghidra facts and the
   2026-07-01 caller-plane diagnostic now split the blocker cleanly into two
   different lanes: Zoom still needs the caller-side collapse chain
   (`sampler -> +0xf252 -> +0xf250 -> +0xe -> final byte`), while tiny
   Rotation is no longer a validity-alpha question and instead points to
   upstream polar RGB / substitute-path population. The current Mac source
   still substitutes one blurred alpha plane for the AEX caller-collapse model,
   and same-day local probes reject the simplest direct substitutions:
   `--outer-caller-collapse-mode binary-validity` broadens both outer witness
   lanes into top-edge alpha staircases, while the row-probe diagnostic shows
   tiny Rotation already has fully live validity alpha across the failing
   witness neighborhood.
3. `OLMDirectionalBlur` narrow runtime witness only.
4. Bit-depth expansion on already-strong plug-ins:
   `OLMColorKey`, `OLMToonDilate`, and then other slices that are already
   `AE exact` or close enough to validate safely.
5. `OLMDistanceGradation` / `OLMSmoother2 legacy` bounded binary proofs.
6. `OLMKiraKira` last among the hard plugins unless a returned witness suddenly
   makes it cheap.
7. `OLMSmoother v1` true endgame work only; do not spend early bit-depth budget
   here while broader plugins still need 16/32bpc coverage.

Current pending Windows runtime queue:

1. `olmradialblur_caller_collapse_followup_20260701`
   - package:
     `refs/runtime_trace_packages/olm_runtime_trace_radialblur_caller_collapse_followup_20260701.zip`
   - current share copy:
     `/Volumes/onmk/olm_pr/new/olm_runtime_trace_radialblur_caller_collapse_followup_20260701.zip`
2. `olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630`
   - package:
     `refs/runtime_trace_packages/olm_runtime_trace_requests_20260630_182750.zip`
   - current share copy:
     `/Volumes/onmk/olm_pr/new/olm_runtime_trace_requests_20260630_182750.zip`
   - why this one is still live:
     the broader 2026-06-30 Constant boundary return already proved the general
     lane (`case_0020` plateau edge and family-level `answered_partial` for
     `case_0022/0023`), but `case_0023` remains the only focused Constant case
     with `In/Out=Both` plus `Outside Threshold=0`, so the next Windows ask is
     intentionally narrowed to that one ownership rule.

Historical but presently answered/superseded 2026-06-30 4pack requests:

- `olmradialblur_caller_collapse_witness_20260630`
- `olmblur_final_word_witness_20260630`
- `olmdirectionalblur_helper_coverage_witness_20260630`
- `kirakira_compose_writeback_witness_20260630`
- `olmdistancegradation_16bpc_constant_boundary_witness_20260630`

Queue note:

- `olmblur_case0006_helper_prestore_witness_20260630` remains historically useful,
  but the first focused return is already imported and classified as
  `failed_breakpoint_watchpoint`, not a live pending request.
- `kirakira_compose_writeback_witness_20260630` remains historically useful,
  but current user priority is to defer active KiraKira work behind broader
  16/32bpc expansion and the other hard-plugin proofs.
- `olmdistancegradation_16bpc_constant_boundary_witness_20260630` is no longer
  pending as a broad family request. The imported return classifies the
  remaining Constant/background 16bpc lane as threshold ownership / plateau
  membership before compose-writeback, and the active follow-up is now the
  narrower `case_0023` / `Outside Threshold=0` witness rather than another
  broad Constant-boundary package.

Authoritative queue report:
`refs/reports/pending_runtime_trace_packages.md`.

Machine-generated M0 summary:

- Manifest: `refs/conformance/packaged_8bpc_manifest.json`
- Local generated summary:
  `refs/reports/conformance_summary_packaged_8bpc.md`
- Scope: packaged 8bpc AE-host validation, 70 cases.
- Current machine count: `AE exact=62`, `reference-generation split=1`,
  `known-red=7`.
- OLMBlur 8bpc decision:
  `refs/conformance/olmblur_8bpc_decision.md`
- OLMColorKey Edge 8bpc decision:
  `refs/conformance/olmcolorkey_edge_8bpc_decision.md`
- OLMDistanceGradation 8bpc decision:
  `refs/conformance/olmdistancegradation_8bpc_decision.md`
- OLMRadialBlur 8bpc decision:
  `refs/conformance/olmradialblur_8bpc_decision.md`
- OLMKiraKira 8bpc decision:
  `refs/conformance/olmkirakira_8bpc_decision.md`
- OLMDirectionalBlur 8bpc decision:
  `refs/conformance/olmdirectionalblur_8bpc_decision.md`
- OLMSmoother2 current-AEX 8bpc decision:
  `refs/conformance/olmsmoother2_current_aex_8bpc_decision.md`

Final randomized holdout set:

- Windows Software return:
  `refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return/`
- Shape: 9 plug-ins x 10 random cases = 90 total cases, split into per-plug-in
  manifests on import.
- Summary:
  `refs/reports/olm_final_random_per_plugin_10cases_20260629_summary.md`
- Tracked request JSONs:
  `refs/reference_requests/olm_final_random10_*.json`
- Mac AE request directories:
  `handoff/ae_pixel_validation_20260618/requests/ae_pixel_olm_final_random10_*`
- Batch request-id list:
  `refs/reports/final_random_holdout_request_ids_20260629.txt`
- Use: final confidence / regression set after the narrow witness-led work is
  in place. Do not promote it to a primary spec-discovery source when a
  residual still lacks binary proof.

## Current Feature Status

| Plug-in / feature | 8bpc Software status | 16bpc status | 32bpc status | Evidence | Next required proof |
| --- | --- | --- | --- | --- | --- |
| ColorKeep synthetic helper | guarded | untested | untested | Synthetic CLI smoke only. | Real Windows Software reference or keep as support utility. |
| OLMBlur exact slices `case_0001..0005` | AE exact for packaged 8bpc slices | not AE exact; current 16bpc Mac AE output is sign-mixed one-word | untested | 2026-06-19 AE pixel return is exact for `case_0001..0005` with `max_diff=0`; local verification report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmblur_exact_20260619/reports/ae_pixel_all_exact.json`. 2026-06-22 provenance audit classifies OLMBlur as `normalized-software-exact-with-legacy-drift`: all seven AE-host candidates are exact against the 20260618 normalized Software refs; latest report: `refs/reports/olmblur_reference_provenance_20260622_025614/audit.md`. Cross-feature canonicalization also reports OLMBlur `normalized-software-exact` in `refs/reports/software_reference_canonicalization_8bpc.md`. 2026-06-26 reverify after fixing 16-bit ImageMagick endian decoding in `refs/scripts/verify_manifest.py` shows 16bpc `case_0001..0005` at `max_diff=2` with tiny means, not the previously reported 512-step family. 2026-06-28 current Mac AE rerun preserves that shape and shows mixed signed deltas; report: `refs/conformance/olmblur_16bpc_mac_ae_rerun_20260628.md`. 2026-06-28 word-delta audit infers only `+/-1` PF_Pixel16 word deltas for this family; report: `refs/conformance/olmblur_16bpc_word_delta_audit_20260628.md`. 2026-06-29 asm writer audit grounds the standard 16bpc writer as `round-add-helper-truncate-word-store`; report: `refs/conformance/olmblur_16bpc_asm_writer_audit_20260629.md`. 2026-06-29 writer-contract audit then proves current Mac non-Legacy `store16` still uses `nearbyintf(v)` rather than the Windows standard add-half/truncate family, but because all non-Legacy 16bpc cases remain sign-mixed one-word residuals this is not yet enough to justify a blind global writer swap; report: `refs/conformance/olmblur_16bpc_writer_contract_audit_20260629.md`. 2026-06-29 bounded live Mac AE probing on `case_0006` confirms the installed plug-in stores `1100.5 -> 1100` and `363.5 -> 364`, matching ties-to-even `nearbyint`; the live-probe audit then ties those witnesses to the exported `-2/+2` PNG deltas through `2 * stored_word - 1`; report: `refs/conformance/olmblur_16bpc_live_probe_audit_20260629.md`. A new current-baseline audit now freezes the exact Mac-side witness bundle across 16bpc non-Legacy, 16bpc Legacy, and old normalized 8bpc Legacy: `case_0006` stays sign-mixed (`314,14 => 2199 vs 2201`, `29,71 => 727 vs 725`), `case_0007` 16bpc keeps the one-word blue half-step (`345,672 => 25089 vs 25087`), and old normalized 8bpc `case_0007` keeps only one red pixel low at `(488,941)` while `(488,942)` matches exactly. Report: `refs/conformance/olmblur_current_word_baseline_20260629.md`. Current forecast IR: `notes/IR_OLMBlur.md`. | Preserve passing normalized 8bpc AE behavior. Next proof is final 16bpc pre-writeback float/helper/store order, not kernel tuning. |
| OLMBlur residual slices `case_0006..0007` | AE exact for packaged 8bpc slices | not AE exact; `case_0006` is sign-mixed one-word, `case_0007` is down to a one-pixel family | untested | 2026-06-19 AE pixel return is exact for the formerly residual `case_0006..0007` with `max_diff=0`. 2026-06-20 runtime trace proves the remaining CLI residual is present before byte writeback: `case_0006` Windows pre-writeback red is `185.49998474121094` while Mac CLI is exactly `185.5`; `case_0007` uses the Legacy `OLMBlur+0x7FDF` writeback family. 2026-06-28 current Mac AE rerun originally kept `case_0006 max_diff=2` and `case_0007 max_diff=383` at `(0,0)`; word-delta audit separated the one-word family from the Legacy witness. 2026-06-29 bounded Mac AE probing then proved the old `(0,0)` anomaly was pre-store, and the stage probe localized it to the horizontal Legacy pass. A same-day decomp-backed carry-prev port based on `FUN_1800014f0` / `FUN_180001ea0` materially improves the active residual: old 8bpc `case_0007` drops from 3 residual pixels to 1, and the live Mac AE 16bpc probe now has `(0,0) raw=0 stored=0` with normalized Windows comparison at `max=1`, one pixel remaining; report: `refs/conformance/olmblur_legacy_carry_prev_probe_20260629.md`. Current IR: `notes/IR_OLMBlur.md`. | Keep the carry-prev rule. Next proof is the final one-word family for `case_0006` plus the single remaining Legacy witness pixel for `case_0007`. |
| OLMColorKey core RGB/color-space/Replace | AE exact for core packaged 8bpc slices | reference covered / compare pending | untested | 2026-06-19 AE pixel return is exact for `case_0001..0008`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmcolorkey_exact_20260619/reports/ae_pixel_all_exact.json`. Normalized CLI is exact for core `case_0001..0004` and `case_0007`. | Add 16/32bpc references for the core path after Edge Blur reference generation is fixed. |
| OLMColorKey Edge Thin erode / Edge Blur | AE-host exact against normalized 8bpc refs / AE-free CLI residual | AE exact for all 9 covered 16bpc ColorKey cases | untested | 2026-06-19 AE pixel return has Edge Thin erode `case_0005/0006` exact and Edge Blur `case_0008` exact. `case_0009` reports `max=47 mean=0.069921` only against the older 20260604 reference; 2026-06-21 and 2026-06-22 provenance audits show the returned candidate is exact against the 20260618 normalized ref and CLI reference, so this is a reference-generation split rather than a clean algorithm witness. Latest audit: `refs/reports/olmcolorkey_edge_reference_provenance_20260622_024907/audit.md`; it now emits the machine-readable classification `reference-generation-split` and the action “do not tune Edge Blur from the 20260604 residual.” Cross-feature canonicalization reports ColorKey 9/9 `normalized-software-exact` in `refs/reports/software_reference_canonicalization_8bpc.md`. 2026-06-26 16bpc reverify still leaves only `case_0009` failing (`12597px` in the `candidate kept / Windows removed` direction). 2026-06-27/28 runtime tracing proves that the live current-AEX 16bpc path uses `Force Lower Precision=3`, `amount=25`, `distance_type=2`, and `dist <= amount` inside a current `OLMColorKey+0x9000` positive Edge Thin orchestrator. Follow-up raw CDB proves primary residual `(1110,149)` consumes `dist=2.0`, takes the copy path, and writes matte word0 `0x0000 -> 0x8000`. 2026-06-28 PE/capstone audit of the Lab76 per-component comparator at `0x1800043a0` shows separate threshold/epsilon multipliers; applying that binary-grounded formula makes `Lab76 hit + taxicab Edge Thin <=25` exact against the Windows 16bpc reference (`diff=0`). 2026-06-28 Mac AE full-batch rerun completed all 9 `ae_pixel_bitdepth16_olmcolorkey_exact_20260625` cases, and `scripts/verify_ae_pixel_validation_result.py` reported `ok=9 fail=0 missing=0 total=9`, all `max=0 mean=0.0000`; report: `/tmp/olm_colorkey_16bpc_full_rerun_20260628/reports/ae_pixel_16bpc_all_exact.json`. 2026-06-28 adds a preview-only 32bpc float-output probe at `refs/reports/bit_depth_32bpc_probe_plan_20260628/request_preview.json`; it is not active and not completion evidence. | Preserve passing 8/16bpc behavior. Next ColorKey work is an intentionally scheduled 32bpc float-preserving reference/probe, not more 8/16bpc tuning. |
| OLMToonDilate cases `1..3` | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0003` with `max_diff=0`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmtoondilate_exact_20260619/reports/ae_pixel_all_exact.json`. AEX-style two-pass chamfer propagation plus semi-alpha RGB premultiply also makes the normalized Windows AE Software refs exact in Python and C++ CLI. Current IR: `notes/IR_OLMToonDilate.md`. | Add 16/32bpc references and keep the IR tied to the two-pass/premultiply evidence. |
| OLMDistanceGradation basic/extended/blur | AE exact for packaged 8bpc slices | not AE exact; extended Constant-binary batch is `1/16` exact | untested | 2026-06-19 AE pixel return is exact for all packaged basic/extended/blur cases (`12 + 16 + 1` cases, `max_diff=0`); local reports live under `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_*`. 2026-06-22 provenance audit shows those AE-host candidates are exact against all 29 20260618 normalized Software refs; latest report: `refs/reports/olmdistancegradation_reference_provenance_20260622_025045/audit.md`, classified as `normalized-software-exact-with-legacy-drift`. Cross-feature canonicalization reports all three groups `normalized-software-exact` in `refs/reports/software_reference_canonicalization_8bpc.md`. 2026-06-26 endian-fix reverify keeps the exact count at `9/29` but corrects residual amplitudes; current batch lives under `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/`. Ghidra confirms 8bpc compose is an AE iterate callback over a prebuilt field world and reads the field green byte. A 2026-06-27 Windows bg-on/bg-off return for `case_0020..0023` removes one false narrowing: these residuals are not just `Use Background Color=1` compose drift, because Windows `bg_off` for `case_0020..0022` still stays grad-color opaque at the witness and `case_0023 bg_off` still differs from the prior Mac `no_bg` probe over the full frame. 2026-06-29 Windows runtime trace answers the `case_0026` branch question: field green already ramps before `FUN_181170480`. Mac AE automation was recovered by avoiding AE 26.3 `JSON.parse` on the large manifest. A gated Mac plug-in dump then proved the field itself ramps but `Power` was collapsed by an erroneous `FIX_2_FLOAT` conversion. The Power fix recovers the row0 ramp within `0..4`, but the 16bpc extended batch remains `1/16` exact. The remaining failures were split into families, and the representative `case_0020` point dump proved the Constant/background mismatch was pre-writeback. Implementing the Constant-specific `THRESH_BINARY` path from `FUN_181174760` moves `case_0020 1001->1`, `case_0021 1002->1`, `case_0022 9347->192`, and `case_0023 1388->73` changed pixels; report: `refs/conformance/olmdistancegradation_16bpc_constant_binary_fix_20260629.md`. The remaining Constant changed pixels are all within 1px of the active threshold; report: `refs/conformance/olmdistancegradation_16bpc_constant_remaining_boundary_20260629.md`. A direct Layer/no-bg unpremultiply probe was rejected because it broadened `case_0012` from `25421` to `285406` changed pixels and required an AE restart to verify the revert; report: `refs/conformance/olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.md`. A new machine-generated current-baseline audit then froze the post-fix witness values and revealed that the earlier quick PNG-space `case_0012 max=65` note was optimistic: the authoritative RGBA16 compare still sees a broad residual (`max=16476`, `mean=332.8368`, `nonzero_px=285406`) even though the main witness points improve to small RGB deltas (`-266/-354`) at `(462,7)`, `(72,8)`, and `(106,19)`; report: `refs/conformance/olmdistancegradation_16bpc_layer_source_current_baseline_20260629.md`. The 2026-06-30 Constant boundary return plus the new targeted diagnostic now narrow the unresolved Constant lane further: only `Both + Outside Threshold=0` (`case_0023`) responds to outside-side helper staging variants, while `case_0022` stays flat. See `refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_boundary_witness_20260630.md` and `refs/conformance/olmdistancegradation_16bpc_constant_both_outside0_variants_20260630.md`. A live Mac AE outside-side equality probe was then rejected: the broad `dist >= t` variant breaks the whole frame, while the narrower `threshold floor 1 + equality` retry leaves `case_0023` at the existing `73px` residual and `case_0022` at `192px`; report: `refs/conformance/olmdistancegradation_16bpc_rejected_outside_threshold_eq_probe_20260630.md`. | Preserve passing 8bpc AE behavior and keep the Power plus Constant binary-threshold fixes. The next bounded move is no longer an outside-side equality tweak; it needs a stricter upstream helper-staging / threshold-ownership proof for the Constant `Both + Outside Threshold=0` lane. |
| OLMSmoother v1 via Smoother2 compatibility | AE exact for packaged 8bpc v1 slices | untested | untested | 2026-06-20 AE pixel rerun corrected the v1 comp to `960x540`; `case_0001..0003` are exact with `max_diff=0`. Local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother_v1_20260619/reports/ae_pixel_exact.json`. | Decide whether v1 remains an independent compatibility path or is formally mapped to Smoother2; add 16/32bpc refs if v1 remains supported. |
| OLMSmoother2 no-key grid | AE exact for packaged 8bpc grid | untested | untested | 2026-06-19 and 2026-06-20 AE pixel returns are exact for all 12 no-key grid cases with `max_diff=0`; latest local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother2_no_key_grid_20260619/reports/ae_pixel_no_key_grid_exact.json`. This supersedes the earlier AE-free near-exact residual as an AE-host conformance fact. Current IR: `notes/IR_OLMSmoother2.md`. | Optional runtime trace only for binary-grounding if it returns; do not spend the next Windows trip on no-key tuning. |
| OLMSmoother2 legacy current-AEX recapture | guarded / writer-confirmed internal unresolved | untested | untested | 2026-06-21 full current-AEX Software recapture covers all 12 requested legacy cases. With AE-saved premultiplied before frames, `legacy_case_0002` and `legacy_case_0003` are exact. CDB captures final writer values: `0004 (501,1055)` emits `[159,95,95,255]`; `0012 (500,877)` emits `[9,9,9,255]`, ruling out PNG export / byte packing. Mac audit reclassifies the preserved `+0x350b` pre-call `[rsp+0x48]` floats as stale output-buffer content. Promoting Smooth Range threshold for key-enabled class-plane generation moves `0004` to `idx=208` and `cce0_after_b120=[0.34566417,0.11387399,0.11387399,1.0]`, matching the Windows final writer floats within print precision. The 11 before-frame measured cases improve from mean-sum `1.3008` to `0.0589`; remaining residuals are localized (`0004 max=113 mean=0.0045`, `0012 max=91 mean=0.0151`). Mac-side 2026-06-21 audit isolates `0012 (91,841)` to `cardinal6 key=50 -> f270/e170/e3a0`, while automated residual audit shows `0004 (1903,519)` is the opposite failure shape: transparent center, `idx=208`, polygon count `0`, Mac `[0,0,0,0]` vs Windows `[103,103,103,113]`. Decision matrix `refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.md` rejects global cplane/idx0 toggles, rejects `bb10/curve_idx` as inert, and rejects global `f270` suppression as worse (`mean_sum 0.058945 -> 0.083017`, max `113 -> 169`). Witness contract `refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.md` freezes the two active local paths and the exact proof boundary. Neighborhood report `refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.md` further classifies the opposite 5x5 shapes: Windows adds semitransparent output where local passthrough is transparent for `0004`, while local adds semitransparent output where Windows stays transparent for `0012`; next proof should stay at center-pixel `c280/cce0` and strongest-neighbor state, not broad PNGs. Tracked decision `refs/conformance/olmsmoother2_current_aex_8bpc_decision.md` records the earlier 2026-06-25 return, and the new writer-frame bundle analysis upgrades the conclusion: the latest writer-frame floats already explain the Windows reference pixels for both active witnesses, so the remaining blocker is upstream producer selection rather than final writer packing; report: `refs/reports/runtime_trace_bundle/olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows/smoother2_writer_frame_followup_analysis_20260629.md`. Current IR: `notes/IR_OLMSmoother2.md`. | Keep the Smooth Range threshold fix. Next proof: exact `d3b0/da50/e170/f270/e3a0` state for `0012 (91,841)` and a 0004 polygon/no-polygon proof if Windows runtime tracing resumes; otherwise avoid global alpha/index/curve-index/f270-suppression toggles. |
| OLMDirectionalBlur | blocked | untested | untested | Official manual describes a non-generic anisotropic blur: front/back strengths are asymmetric, transparent pixels are ignored, and Size Variation / Edge Fade / Sharp Tail depend on opaque pixel groups. Current C++ probes remain expected-red after the 2026-06-21 recheck: `rotated-aex-full-choreo case_0001 max=164 mean=4.9570`, `case_0005 max=251 mean=2.2971`; exact rowdriver/scatter variants stay in the same band, and rowdriver-prepass is worse. The 2026-06-22 candidate matrix confirms this split across `case_0001..0005`: measurement scaffolds `rotated-front-strength/direct` have the best total means (`18.197798` / `18.310725`) but are not AEX-structured, while AEX choreography variants cluster around `22.12` and only clearly beat direct on the diagonal `case_0005`; reports: `refs/reports/olmdirectionalblur_candidate_matrix_20260622_010324/candidate_matrix.md` and `refs/reports/olmdirectionalblur_candidate_matrix_20260622_010433/candidate_matrix.md`. The 2026-06-22 residual cluster audit isolates two concrete witnesses for the next runtime proof: angle-0 `case_0001 (494,169)` is `angle0-rgb-only-rowdriver-or-valid-alpha`, Windows `[164,0,0,255]` vs local `[0,0,0,255]`, alpha diff exactly zero; diagonal `case_0005 (507,367)` is `diagonal-rgb-alpha-rotate-validity`, Windows `[1,0,0,255]` vs local `[252,0,0,255]`, with RGB inversion and smaller alpha residuals; report: `refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/residual_clusters.md`; packaged focused request: `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_residual_witness_20260622_022500.zip`. The 2026-06-24 focused return is only `answered_partial`: it includes exact Software reference renders and a prior live-attempt log, but no successful per-pixel rowdriver/rotate-path values because the module did not resolve before the attempt failed. Current comparison: `refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness_20260624.md`. Decision matrix `refs/conformance/olmdirectionalblur_8bpc_decision.md` classifies this as `blocked-await-runtime-or-asm-proof`: no exact candidate, best overall is a non-AEX measurement scaffold, best AEX-shaped candidate still has `max=251`, and the runtime return is not actionable. Witness contract `refs/reports/olmdirectionalblur_witness_contract_20260624/witness_contract.md` freezes the proof boundary: angle-0 rowdriver/valid-alpha and diagonal rotate/sampler/validity must be proven separately; `direct`/`rotated-front-strength` remain measurement baselines only. 2026-06-21 reference audit shows the 20260619 bulk `OLMDirectionalBlur` folder is mixed: 76 PNGs total, only 16 DirectionalBlur; 60 belong to KiraKira/ColorKey/RadialBlur/Smoother2. Current IR: `notes/IR_OLMDirectionalBlur.md`. | Do not tune from broad PNGs or parent folder names. Need a successful focused runtime/asm proof for angle-0 rowdriver accumulation / validity-alpha side channel separately from the diagonal rotate path, plus final normalization and group-size behavior on non-opaque alpha cases. |
| OLMRadialBlur Zoom / tiny Rotation | guarded / blocked | untested | untested | 2026-06-22 Mac-side recheck: Zoom `case_0009 max=1 mean=0.0046`; tiny Rotation `case_0010 max=255 mean=0.0104` under a mean guard. 2026-06-22 residual cluster audits classify Zoom as `rgba-off-by-one` and tiny Rotation as `high-rgb-border-sampler-or-validity`. The 2026-06-24 focused runtime return narrows this: Zoom final Windows bytes `[20,3,3,254]` are explained by pre-writeback floats, so the mismatch is not a final byte-writer issue but upstream alpha-normalization / sampler-side state. Mac-side witness audit `refs/reports/olmradialblur_zoom_witness_20260624/audit.md` reproduces the local witness: RGB floats match Windows within about `1.3e-7`, local alpha clips to `1.0`, Windows alpha is `0.9999999403953552`, and the only byte delta is alpha `+1`. Tiny Rotation final bytes were captured, but the closest traced inverse-sampler value does not explain the final white pixel, so it remains sampler/validity unresolved rather than rounding. Decision matrix `refs/conformance/olmradialblur_8bpc_decision.md` classifies Zoom as `guarded-alpha-normalization` and tiny Rotation as `blocked-sampler-validity`. Witness contract `refs/reports/olmradialblur_witness_contract_20260624/witness_contract.md` freezes the narrow proof boundary and explicitly rejects final-byte tuning for Zoom plus treating the closest tiny-Rotation sampler return as pre-writeback truth. 2026-06-30 bounded caller-collapse probes reject both `binary-validity` and `zero-rgb-on-invalid`, and a new local witness dump shows `case_0009 (6,0)` remains exactly `[20,3,3,255]` locally even with `--rgba-sampler-alpha-mode repeat-raw`, so the surviving Zoom delta is still caller-side polar alpha/sample collapse rather than the narrow repeat-border alpha rule. A same-day richer witness dump sharpens both lanes further: Zoom's `(6,0)` near-match already uses two `valid=0` contributing cells with nonzero RGBA, so the live issue is not a naive per-cell zero-on-invalid rule; tiny Rotation's `(1614,6)` max witness has all four contributing cells `valid=1` but two negative and two zero RGB contributors, so the black result is upstream in polar RGB population / coordinate choice rather than a last-stage validity gate. A final local clamp probe then shows that clamping negative polar RGB only at the last inverse-sampling stage leaves Zoom unchanged and improves tiny Rotation only marginally (`mean 0.01032034 -> 0.01030189`, `max` still `255`), so that cleanup is not the missing AEX rule either. A nearby patch audit strengthens the remaining call: the Windows output keeps a small bright cluster across `(1612..1614,4..6)` while the candidate preserves surrounding dark/low-gray support pixels but drops that bright lobe entirely, which looks more like a missing bright contribution family than a simple one-pixel output shift. A wider bright-lobe search now makes that even stronger: within a `25x25` window centered on the witness, the reference still has `17` bright pixels (`R>=200`) while the candidate has `0`, so this is not a small local displacement. See `refs/conformance/olmradialblur_local_witness_dumps_20260630.md`, `refs/conformance/olmradialblur_final_polar_rgb_clamp_probe_20260630.md`, `refs/conformance/olmradialblur_tiny_rotation_patch_audit_20260630.md`, and `refs/conformance/olmradialblur_tiny_rotation_bright_lobe_search_20260630.md`. Full Rotation remains expected-red: `case_0001 max=255 mean=1.9034`, `case_0002 max=255 mean=1.3071`. 2026-06-21 reference audit shows same-numbered `case_0001..0013` files conflict between the 20260604 legacy set and the 20260605 extra/img2 set, so do not compare RadialBlur by case number alone. Current IR: `notes/IR_OLMRadialBlur.md`. | AE exact check for Zoom slices and binary-ground the tiny/full Rotation high-max residual before claiming compatibility. Zoom next proof is caller-side polar alpha/sample formation, not final byte packing or naive validity masking; tiny Rotation next proof is the upstream polar RGB / contribution path at the localized high-max witness, not simple final validity gating or a one-pixel output shift. |
| OLMRadialBlur Inner | binary-grounded / guarded / blocked | untested | untested | Runtime trace confirmed `rb_inner_only_strength_small` helper effective span resolves to `31`; C++ CLI default mirrors the span-31 population and the span-stat guard passes. 2026-06-21 recheck still leaves old Inner expected-red: `case_0011 max=255 mean=23.0495`, `case_0012 max=255 mean=16.0039`, `case_0013 max=238 mean=18.0193`. A Mac-side source-scatter/prepass force does not move those old-Inner means, and the `param10` probe rejects the simple alpha-plane hypothesis: `one/factor` are equivalent while `polar-alpha/prepass-alpha` worsen old Inner and Edge Fade. The 2026-06-22 static scatter audit (`refs/reports/olmradialblur_scatter_static_facts.md`) rejects promoting `loop-minus-one`, `table-span-minus-one`, or `circular-wrap` as global rules: asm shows `R14D = trunc(resolved_distance * span_gate)`, table step `30000/R14D`, inner tail `offset < R14D`, and next-row underflow. Decision matrix `refs/conformance/olmradialblur_8bpc_decision.md` classifies Inner as `blocked-no-global-toggle`: `loop-minus-one` has the best total mean in the wide matrix but no candidate is exact and top candidates still keep `max=255`. The dense RadialBlur comparator separates placeholder-only dense returns from the useful-but-narrow span-31 live fact: dense-all is `trace-structure-present-values-missing`, live-followup is `inner-span-31-registers-only`. 2026-06-21 reference audit also shows 18 RadialBlur bulk files are misplaced under an `OLMDirectionalBlur` folder; key by request filename/manifest, not parent folder. Current IR: `notes/IR_OLMRadialBlur.md`. | Binary-ground the remaining wrong plane/value with typed sampler/scatter/writeback witness values; then Mac AE exact check. Prefer the full 20260617 Inner return for coverage. |
| OLMKiraKira strength0 / single-ray slices | binary-grounded / guarded / blocked | untested | untested | Runtime trace confirmed first `boxFilter` FilterEngine branch is OpenCV 4.5.5 AVX2 `FUN_1812e39d0`. IR now lives at `notes/IR_OLMKiraKira.md`. 2026-06-21 focused forward-warp / box-input trace answered the prior follow-up: forward `warpAffine` matrix, temp geometry, source ROI, `boxFilter` args, and pass-1 input witnesses match the local baseline at the traced points. 2026-06-24 boxFilter microprobe ruled out first-pass contributing-window selection, `BORDER_REFLECT_101`, AVX2 accumulator/store, and wrong Mat stage. The apparent upstream source-buffer delta is now explained: Windows plateau `0.79773343` for RGB `[230,210,60]` matches BT.709 luma, while the old local seed used BT.601 and produced `0.77992159`. `refs/scripts/olmkirakira_cli.py` now uses BT.709 for AEX Channel 2 seed; new baseline is `refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json`, and the new witness plan is `refs/reports/olmkirakira_boxfilter_window_plan_20260624_bt709/witness_plan.md`. The 2026-06-24 BT.709 remeasure keeps the single-ray Software set guarded but not exact: vertical/horizontal `max=14/11`, diagonal/diagonal2 `max=23`, rotation13 `max=66`, while strength-0 remains exact/near-match (`max=0..3`). Report: `refs/reports/olmkirakira_remeasure_20260624_bt709_software/reports/diff.json`. The BT.709 local trace also matches the 2026-06-21 deep Windows ray-helper stages within `1e-5` through box pass 1/2/3, rotate-back, and final center-copy; comparison: `refs/reports/runtime_trace_comparisons/olmkirakira_deep_stage_values_20260624_bt709.md`. Focused follow-up return imported: `refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md`. Windows directly grounds `FUN_18114fd90` at center/up/right (`center ray=0.71891218 -> glow [1,1,1,0.71891218]`, PNG-facing `[124,124,124,255]`), but did not isolate the internal merge-mode-1 compose float/writeback site or the residual hotspot. Decision matrix `refs/conformance/olmkirakira_8bpc_decision.md` classifies the current blocker as `blocked-compose-or-final-quantization`: ray-helper and fd90 are grounded, but compose/writeback is not. A Mac gain probe rejected changing the default compose scale from `0.62` to `0.60` because total Software mean worsened (`8.2150 -> 8.7974` over the 9 Software single-ray rows), and `scale=1.0` breaks strength-0 anchors. 2026-06-25 compose model audit preserves current gain `0.62` and rejects `0.60`, inverse-trace-inspired `0.5811/0.5436`, direct scale override, and premultiplied compose as global fixes. 2026-07-01 hotspot-local compose diagnostics now sharpen the remaining lane further: at hotspot `(934,118)` the Mac compose-boundary alpha is `0.507505655`, while the Windows-match interval is only `0.446666666667..0.451111111111`; even applying the already-grounded grayscale control attenuation still projects byte `138`, not Windows `131`, so the remaining gap is a hotspot-local attenuation/branch before writeback rather than a broad compose/gain issue. Old three-case legacy two-temp remains expected-red and is not an exact gate. | Do not send broad KiraKira PNGs and do not tune luma, first-pass boxFilter, ray-helper choreography, fd90, or the default compose scale from this return alone. Next useful proof is a narrower merge-mode-1 compose/writeback or final quantization witness at the residual hotspot, not a global retune. |

## Host Usability Gate

Use this table before spending time inside Mac AE by hand. The point is to
separate "does this behave as an AE plug-in yet?" from "is this exact against
Windows Software?".

| Plug-in | Host status | Why this is the current host status | Meaningful AE hands-on use right now |
| --- | --- | --- | --- |
| ColorKeep | `host-smoke` | Support/helper status only; real Windows compatibility slice is thin. | Only load/add/render sanity. |
| OLMBlur | `host-visual-tuning-ready` | Packaged 8bpc AE exact exists and remaining work is narrow 16bpc rounding/writeback. | Yes, but only for narrow residual confirmation. |
| OLMColorKey | `host-stable` | 16bpc full batch now applies all parameters and verifies 9/9 `max=0` for the covered slice. | Regression confirmation and future 32bpc expansion only; no freeform look tuning. |
| OLMToonDilate | `host-stable` | Packaged 8bpc AE exact exists and no current host integration blocker is known. | Yes, mainly regression confirmation. |
| OLMDistanceGradation | `host-debuggable` | Mac AE automation is recovered. Single-case probes complete after the `eval` manifest parser fix, and the plug-in can emit gated field dumps for 16bpc witnesses. | Yes, but only for witness-focused 16bpc debugging and regression confirmation. |
| OLMSmoother v1 | `host-stable` | Packaged 8bpc v1 slices are AE exact after comp correction. | Yes, for supported v1 slice checks. |
| OLMSmoother2 no-key | `host-debuggable` | No-key grid is AE exact, but legacy/key/gamma path is still unresolved. | Only no-key confirmation and bounded legacy probes. |
| OLMSmoother2 legacy/key/gamma | `host-debuggable` | Manual use can help reproduce witnesses, but internal branch evidence still leads and broad eyeballing is unsafe. | Only witness-focused debugging. |
| OLMDirectionalBlur | `host-debuggable` | Windows-visible controls now exist in the Mac UI, but static/runtime evidence says PNG-only tuning is unsafe and broad output is not yet trusted. | Witness-level host checks only; no visual matching. |
| OLMRadialBlur | `host-debuggable` | Windows-visible controls now exist in the Mac UI, but Zoom/Rotation/Inner still need sampler/prepass/writeback proof before output can be trusted. | Witness-level host checks only; no visual tuning. |
| OLMKiraKira | `host-smoke` | Deep binary facts exist, but compose/writeback remains unresolved and manual output is not yet trustworthy. | Only load/UI/render smoke, not look-matching. |

Practical rule:

- `host-blocked` / `host-smoke`: AE manual testing is only for host integration
  and crash diagnosis.
- `host-debuggable`: AE manual testing is useful only when tied to a specific
  witness or branch question.
- `host-visual-tuning-ready` / `host-stable`: AE manual testing can help close
  narrow residuals or confirm supported slices.

## Recent Mac-Side Audits

- 2026-06-29 UI schema drift audit:
  `refs/reports/param_schema_windows_ref_audit_20260629.md`.
  This separates "same visible parameter set?" from "same algorithm?" using the
  source-backed Mac schema in `refs/reports/mac_plugin_param_schema_20260629.*`.
  Current high-signal findings:
  - `OLMColorKey`: current Mac source-visible schema covers the real numbered
    per-color controls; remaining Windows-only names are mostly section/group
    labels (`Edge Thin`, `Edge Blur`, generic `Amount`) rather than missing
    numbered controls.
  - `OLMKiraKira`: Windows manifests still expose ramp/highlight controls not
    present in the current Mac source-visible UI (`Use Ramp`, `Ramp`, color
    ramps, `Highlight Color`). Do not assume Mac AE hand-tuning is apples to
    apples with the Windows manifest yet.
  - `OLMRadialBlur`: 2026-06-29 host-fix pass added grouped `Outer/Inner Blur`
    labels, per-section `Edge Fade`, separate inner offset controls,
    `Noise Type`, `Noise Layer`, `Seed`, and `Thickness` with Windows-stable
    disk IDs. Visible parameter-set parity is now mostly closed; remaining
    blockers are binary-proof, not missing visible controls.
  - `OLMDirectionalBlur`: 2026-06-29 host-fix pass added grouped Front/Back
    labels plus `Noise Type`, `Noise Layer`, `Seed`, `Offset`, and
    `Thickness` to the Mac source-visible schema. Remaining manifest oddity is
    a duplicated `NO_VALUE` `Sharp Tail` presentation entry, not a missing
    actionable control.
  - `OLMSmoother` v1 still carries a legacy name drift (`Do Smooth Range` vs
    current `Smooth Length Tolerance`), so v1 compatibility policy should stay
    explicit.
  This audit does not prove algorithm exactness, but it explains why manual AE
  validation on the hard plugins can still be non-equivalent even before
  runtime-trace questions are resolved.
- 2026-06-29 hard-plugin control mapping:
  `refs/reports/hard_plugin_ui_control_mapping_20260629.md`.
  This promotes the previous drift warning into a plugin-by-plugin host-fix
  checklist:
  - `OLMRadialBlur`: current Mac source-visible UI now covers the Windows
    visible parameter set closely enough for host-side manifest application.
    Keep the remaining blocker in `binary-proof`, not `host-fix`.
  - `OLMDirectionalBlur`: current Mac source-visible UI now covers the Windows
    visible parameter set closely enough for host-side witness debugging.
    Keep the remaining blocker in `binary-proof`, not `host-fix`.
  - `OLMKiraKira`: the 2026-06-29 host-fix pass added `Highlight Color` and
    the five `Use Ramp` toggles with Windows-stable disk IDs, and the
    2026-06-30 schema pass aligned `Channel` choices, `Blur Mode` choices/range,
    `Strength Multiplier`, `Glow Opacity`, and `Fade Out` with the Windows
    fresh capture. Remaining host drift is now narrower: custom/no-value ramp
    controls (`Ramp`, color-ramp labels) are still absent, and `Brightness Gain`
    plus `Highlight Radius` still need semantic/range proof.
  Operationally, `OLMKiraKira` still has a real two-lane blocker
  (`binary-proof` plus residual `host-fix`), but the host lane is no longer a
  broad surface mismatch. `OLMRadialBlur` and `OLMDirectionalBlur` remain
  closer to pure `binary-proof`.
- 2026-06-29 `OLMDistanceGradation` pending Layer/no-bg proof contract:
  `refs/conformance/olmdistancegradation_pending_layer_source_proof_20260629.md`.
  This turns the current Windows wait into a sharper yes/no decision boundary:
  the next actionable return must distinguish straight-source-times-output-alpha
  from premultiplied-source ownership inside the Layer/no-bg compose path for
  `case_0012` / `case_0016`. Final PNGs or final RGBA16 values alone are
  explicitly insufficient; the return is only useful if it includes the
  consumed source-layer RGBA, any premultiply/unpremultiply step, pre-writeback
  floats, and final RGBA16 words at the witness pixels.
- 2026-06-29 `OLMBlur` pending final-word proof contract:
  `refs/conformance/olmblur_pending_final_word_proof_20260629.md`.
  This sharpens the remaining OLMBlur wait into a narrow writer/helper question:
  the next useful Windows evidence must capture pre-store float(s) and any
  helper/clamp output at `case_0006` sign-mixed one-word witnesses plus the
  surviving Legacy half-step witnesses (`case_0007` 16bpc `(345,672)` and old
  8bpc `(488,941)`). Final PNG/word values alone are not enough, and the
  current source-vs-asm mismatch still does not justify a blind global
  `nearbyintf -> floorf(v + 0.5f)` swap.
- 2026-06-30 `OLMBlur` writer-only hypothesis audit:
  `refs/conformance/olmblur_writer_only_hypothesis_20260630.md`.
  This converts the previous prose warning into a witness matrix. A pure
  non-Legacy writer swap would fix `case_0006 (314,14)` but leaves
  `case_0006 (29,71)` unchanged, while the surviving Legacy 16bpc witness
  `(345,672)` actually prefers the current `nearby` result at the exact local
  raw `12544.5`. Old 8bpc Legacy `(488,941)` is below the half-step under both
  local writer rules. Operationally, this means the pending Windows final-word
  request is still mandatory; broad local writer rewrites remain forbidden.
- 2026-06-30 `OLMBlur` Legacy 16bpc blue witness return:
  `refs/conformance/olmblur_case0007_16bpc_windows_b_witness_20260630.md`.
  This directly captures the Windows pre-store blue float for
  `olmblur__case_0007 (345,672)` as `12544.498046875`, followed by
  `cvttss2si -> 12544`. That removes this witness from the generic
  writer-rule-question bucket: for this exact Legacy point, Windows is simply
  landing slightly below the half-step where the current Mac witness is exactly
  `12544.5`. The remaining OLMBlur final-word uncertainty is therefore
  concentrated in non-Legacy `case_0006` and old normalized 8bpc `(488,941)`.
- 2026-06-29 `OLMKiraKira` pending compose proof contract:
  `refs/conformance/olmkirakira_pending_compose_proof_20260629.md`.
  This fixes the remaining blocker to a narrow merge-mode-1 compose /
  pre-writeback / final-quantization split. BT.709 seed correction, first-pass
  boxFilter window selection, ray-helper stages, and `FUN_18114fd90`
  aggregation all stay grounded; a useful next Windows return must capture a
  real residual-hotspot compose-site float or last-float-before-quantization
  witness, not just final PNG-facing bytes or already-near-matching
  center/up/right samples.
- 2026-06-29 priority4 runtime bundle intake:
  `refs/reports/runtime_trace_bundle/olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows/priority4_runtime_return_summary_20260629.md`.
  This consolidates the latest bundle-level reading in one place:
  `OLMBlur` remains a pre-writeback/helper question rather than a blind writer
  swap; `OLMDistanceGradation` Layer/no-bg stays on the
  straight-source-times-output-alpha branch; `OLMKiraKira` is now cleanly
  blocked at compose/writeback rather than ray-helper or `fd90`; and
  `OLMSmoother2` current-AEX is confirmed upstream of final writer packing by
  the new writer-frame analysis.
- 2026-06-29 `OLMRadialBlur` pending narrow-proof contract:
  `refs/conformance/olmradialblur_pending_narrow_proof_20260629.md`.
  This locks RadialBlur into three separate unresolved lanes instead of one
  vague blocker: Zoom needs upstream polar alpha/sample accumulation proof, not
  final-byte tuning; tiny Rotation needs the exact inverse-sampler
  validity/border or substitute late path for the top-border white witness; and
  Inner needs one helper instance traced beyond effective span into real
  destination accumulation/denominator/writeback. Broad loop/wrap toggles and
  freeform AE look-matching stay forbidden until one of those lanes is closed
  with witness values.
- 2026-06-29 `OLMRadialBlur` compact witness contract:
  `refs/conformance/olmradialblur_witness_contract_20260629.md`.
  This condenses the same blocker into an operator-facing contract: keep Zoom
  final byte packing unchanged, do not trust the closest tiny-Rotation sampler
  return as final truth, and do not promote `loop-minus-one`,
  `table-span-minus-one`, `circular-wrap`, or `grid-aex-float` globally. In
  practice this makes the next Windows return easier to classify: it either
  answers one of the three narrow lanes, or it is still non-actionable.
- 2026-06-30 runtime-queue canonicalization:
  `refs/reports/pending_runtime_trace_packages.md`.
  This temporarily reduced the active runtime wait to four witness families in
  a fixed order: `OLMRadialBlur` caller-collapse, `OLMBlur` final-word,
  `OLMDirectionalBlur` helper-coverage, and `OLMKiraKira` compose/writeback.
  Those four packages were later bundled, returned, and reclassified; do not
  treat this older queue snapshot as the current send list.
- 2026-06-30 Windows 4pack runtime return:
  `/Volumes/onmk/olm_pr/old/20260630_160322__olm_runtime_trace_requests_20260630_4pack_windows_return.zip`.
  This return is asymmetrical and should not be summarized as "4 requests
  answered". Only `OLMBlur` produced a directly actionable new witness:
  `refs/conformance/olmblur_case0007_16bpc_windows_b_witness_20260630.md`
  proves that Legacy 16bpc point `(345,672)` reaches
  `12544.498046875 -> cvttss2si 12544` on Windows, so that point is now a
  pre-store float delta rather than a generic writer-rule uncertainty. The
  other three members of the 4pack remain blocked:
  `OLMRadialBlur` did not capture the caller-collapse chain,
  `OLMDirectionalBlur` did not capture helper-local coverage/runtime values,
  and `OLMKiraKira` did not capture compose/pre-writeback hotspot floats.
  Operationally, this means `OLMBlur` can advance locally while the other three
  should not be "tuned from the return".
- 2026-06-30 post-4pack queue collapse:
  `refs/reports/pending_runtime_trace_packages.md`.
  After importing the later DistanceGradation boundary return and reclassifying
  the 4pack, the live Windows runtime queue is now just one package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmblur_case0006_helper_prestore_witness_20260630.zip`
  with the current share copy at
  `/Volumes/onmk/olm_pr/new/olm_runtime_trace_olmblur_case0006_helper_prestore_witness_20260630.zip`.
  Everything else in the old 4pack remains useful as proof contract material,
  but not as an outstanding send target.
- 2026-06-29 `OLMDirectionalBlur` pending witness-proof contract:
  `refs/conformance/olmdirectionalblur_pending_witness_proof_20260629.md`.
  This sharpens DirectionalBlur into two independent unresolved lanes. The
  angle-0 family now demands helper-local source-to-destination coverage on the
  long strip row, especially the right endpoint `(579,169)` plus companion
  witness `(494,169)`, because broad scatter toggles no longer change the
  dominant strip mask. The diagonal family still demands typed
  rotate/sampler/validity values at the high-red witnesses. Direct /
  `rotated-front-strength` remain measurement scaffolds only, and broad PNG
  tuning stays forbidden.
- 2026-06-30 `OLMDirectionalBlur` angle-0 endpoint constraint:
  `refs/conformance/olmdirectionalblur_angle0_endpoint_constraint_20260630.md`.
  This turns the right strip endpoint from a heuristic into a proof boundary:
  the local row ends at `x=579`, but the documented front helper writes only
  to columns strictly left of its source x and emits no center write. So a
  same-row front-helper explanation for endpoint `(579,169)` would require a
  contributing source beyond the visible strip. Operationally, the next useful
  Windows return must include helper-local source range or an alternate-path /
  rotated-buffer explanation, not only another interior strip pixel.
- 2026-06-29 `OLMDirectionalBlur` scatter static facts:
  `refs/reports/olmdirectionalblur_scatter_static_facts.md`.
  This freezes the helper-local one-sided boundary rules directly from asm:
  front span is `trunc(strength * coeff)`, clipped to `x`, and starts at
  destination `x-1`; back span is clipped to `width-x` and starts at `x+1`;
  zero-length / center writes are excluded (`span <= 1` returns), and the
  rowdriver skips scatter entirely when source alpha is zero. Operationally,
  this makes broad scatter toggles even less admissible: the next proof target
  is rowdriver/group-membership or hidden validity-side-channel behavior inside
  those fixed left/right boundaries, not another global ownership toggle.

- 2026-06-25 bit-depth expansion plan:
  `refs/reports/bit_depth_expansion_plan_20260625/bit_depth_plan.md`.
  Decision is `request-16bpc-for-normalized-8bpc-exact-features`: the next
  broad bit-depth request should start with the normalized 8bpc exact groups
  only: OLMBlur 7 cases, OLMColorKey 9 cases, and OLMDistanceGradation 29
  cases. Generated request:
  `refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json`.
  Project-local Windows package:
  `handoffs/windows_batch/olm_windows_reference_request_20260625_16bpc_normalized_exact.zip`.
  Preflight passed with `verify_reference_request_package.py` and
  `smoke_generate_bitdepth_reference_request.py`: the zip contains one request,
  `software_16bpc` / `SOFTWARE`, with 45 unique cases split as OLMBlur 7,
  OLMColorKey 9, and OLMDistanceGradation 29.
  Windows return was imported on 2026-06-25 and verified as 45/45 matching
  rendered cases for `software_16bpc`; tracked receipt:
  `refs/conformance/bitdepth_16bpc_reference_return_20260625.md`.
  The sampled PNG format is `16-bit/color RGBA`. This only upgrades the
  16bpc status to `reference covered / compare pending`; it is not an
  `AE exact` claim until Mac AE 16bpc output is compared.
  32bpc remains excluded until the float comparison policy is fixed.
- 2026-06-25 `OLMSmoother2` current-AEX proof plan:
  `refs/reports/olmsmoother2_current_aex_proof_plan_20260625/proof_plan.md`.
  Decision is `runtime-or-asm-first-divergence-required`: the Smooth Range
  threshold fix stays, but the next implementation change needs a
  writer-anchored runtime trace or equivalent asm proof. `0004 (1903,519)`
  must prove final writer bytes, `cce0` return, `c280` polygon/append state
  through static dispatch `0xd0 -> FUN_180013140`, and neighbor correlation;
  `0012 (91,841)` must prove final transparent writer output, cardinal6
  descriptor/key, `d3b0/da50/e170/f270/e3a0` through static dispatch
  `0x69 -> FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70`, and any
  `cce0/b120` zeroing. Global transparent-center fallback and global `f270`
  suppression remain rejected.
- 2026-06-25 `OLMKiraKira` compose model audit:
  `refs/reports/olmkirakira_compose_model_audit_20260625/compose_model_audit.md`.
  Decision is `preserve-current-compose-model`: current `aex-screen-over`
  gain `0.62` is best by total mean and best by max across the 9 BT.709
  Software rows. Inverse-trace-inspired gains `0.5811` / `0.5436`, gain
  `0.60`, direct `scale_override=1.0`, and premultiplied compose are rejected
  as global fixes. KiraKira remains blocked on internal merge-mode-1
  compose/pre-writeback or final quantization proof.
- 2026-06-25 `OLMRadialBlur` Inner witness plan:
  `refs/reports/olmradialblur_inner_witness_plan_20260625/witness_plan.md`.
  Decision is `typed-inner-cell-witnesses-only`: the matrix split is now
  represented by `rb_inner_only_strength_large` for low-span behavior and
  `rb_inner_quality_1` for Quality/strong behavior, with
  `rb_inner_edgefade_only` reserved for Edge Fade prepass follow-up. This is
  not an implementation change; it prevents promoting `loop-minus-one`,
  `circular-wrap`, or `table-span-minus-one` as global rules without typed
  `FUN_180001c90` per-cell proof.
- 2026-06-25 `OLMDirectionalBlur` witness plan:
  `refs/reports/olmdirectionalblur_witness_plan_20260625/witness_plan.md`.
  Decision is `two-independent-witness-families`: angle-0 proof is anchored on
  `case_0001 (465,169)` plus the `(487..494,169)` RGB-only strip, while
  diagonal proof is anchored on `case_0005 (507,367)` plus opposite-signed
  companion `(423,187)`. This keeps DirectionalBlur blocked until both
  rowdriver/valid-alpha and rotate/validity families have typed runtime/asm
  evidence, and prevents tuning from only one family or from broad PNG means.

## Imported Runtime Proofs

Current runtime/debugger packages are summarized in
`refs/reports/pending_runtime_trace_packages.md`. The live pending queue
changes over time; check that report rather than assuming this historical
section reflects the current queue. Some returns are only partial proofs, so
"answered" does not mean the feature is exact.

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
- Useful classifier outputs from the merged evidence after placeholder-aware
  comparison:
  - `OLMBlur`: `legacy-border-or-all-same`.
  - `OLMColorKey Edge`: `trace-too-sparse`.
  - `OLMDistanceGradation`: `trace-too-sparse`.
  - `OLMRadialBlur`: `trace-structure-present-values-missing`.
  - `OLMDirectionalBlur`: `trace-structure-present-values-missing`.
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
    resolved/loaded for the request; comparator classification is
    `trace-failed-before-module-load`.
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
- Imported `~/Downloads/olm_runtime_trace_smoother2_legacy_current_aex_0004_cce0_stepover_20260621_return_windows.zip`.
- Stored copy:
  `refs/returns/windows/20260621_smoother2_legacy_current_aex_0004_cce0_stepover/olm_runtime_trace_smoother2_legacy_current_aex_0004_cce0_stepover_20260621_return_windows.zip`.
- Result: `answered_partial`. It preserves the prior exact
  `legacy_case_0004_current_aex` `+0x350b` pre-call capture
  (`x=0x1f5`, `y=0x41f`, `r9=[rsp+0x34]`, pre-call floats
  `[0.78198957,0.0015756468,0.0015756468,1.0]`) and confirms the rerun PNG
  still outputs `[159,95,95,255]` at `(501,1055)`, but the focused fresh reruns
  did not reproduce the exact `y=0x41f` call. An `x=0x1f5` sample saw nearby
  y values `0x41d` and `0x41e`, not `0x41f`.
- Interpretation: this is now a debugger scheduling/reproducibility problem,
  not a new polygon proof. A later Mac-side audit also reclassified
  `[rsp+0x48]` as the `FUN_18000cce0` output buffer before the call. Its
  preserved red value matches the Mac `cce0_after_b120` for the neighboring
  previous pixel `(500,1055)`, so it is stale output-buffer content rather than
  target input evidence. Pause repeated exact-CDB trips for this same
  breakpoint unless the Windows helper can freeze scheduling or single-step an
  already-hit call. The next useful work is Mac-side audit against the final
  writer value and actual classifier/polygon inputs.

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
- OLMDistanceGradation Layer/no-bg source ownership package:
  `refs/runtime_trace_packages/olm_runtime_trace_distancegradation_layer_no_bg_source_ownership_20260629.zip`
  (project-local handoff artifact). This asks Windows to trace
  `olmdistancegradation_extended__case_0012` and `case_0016` at
  `FUN_181170480` and decide whether the 16bpc Layer/no-bg branch uses
  straight source times output alpha, already-premultiplied source, or another
  source-ownership rule.

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
  - `OLMColorKey`: Edge Blur `case_0009` remains `max=47 mean=0.069921`
    only against the older 20260604 reference generation; a 2026-06-21
    provenance audit shows exact match against the 20260618 normalized ref.
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
  - `OLMColorKey`: `8/9` against the packaged older reference; later
    provenance audit reclassifies `case_0009` as reference-generation split,
    not yet a clean Edge Blur algorithm witness.
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
  `OLMColorKey case_0009` was initially treated as a real Edge residual but is
  now reclassified as a reference-generation split, `OLMDistanceGradation`
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
