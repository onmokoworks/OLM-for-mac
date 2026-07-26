# Binary-Grounded IR: OLMSmoother2

## Feature

- Plug-in: OLM Smoother v2
- Feature/path: 8bpc cel-line smoother, color-key, gamma/color-space, v1/v2
  compatibility
- Bit depth: 8bpc exact for the covered lanes; 16bpc still needs expansion.
  A bound 32bpc no-key case-07 run exists but is blocked by the cross-host
  no-effect raw FLOAT32 control.
- Current reference target: current Windows AEX Software recaptures.
- Retired reference set: `refs/win_references/20260605_extra/OLMSmoother2`
  is reference-only for legacy cases because `case_0001` does not match the
  current AEX/runtime-traced CPU behavior.
- Current status: no-key grid has packaged 8bpc `AE exact` evidence from the
  2026-06-19/2026-06-20 AE pixel returns. Standalone OLMSmoother v1
  `case_0001..0003` is also 8bpc `AE exact` after the corrected 960x540 rerun.
  The current Smoother2 legacy/key/gamma implementation is byte-exact with the
  unchanged AEXCompat AEX plane for all 12 cases, and the optimized Mac AE
  plug-in is `AE exact 12/12` against the Windows AE Software references.
  The Xcode conformance build must use optimization level 2; its former `-O0`
  build left 104 max-1 pixels through compiler float sequencing. The first
  32bpc case is not promoted: Windows before-effects vs Mac no-effect differs
  at `6,106,918` raw words, before the effect can be attributed.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Smoother is specialized in smoothing cel animation drawings. | Official v1/v2 manuals under `refs/upstream_official/20260619_olm_official_zips/pdf_text/`. | manual-backed |
| v2 adds color space conversion, Smoothness, Extra Smooth, Gamma Correction, 32-bit support, and improved diagonal smoothing. | Official v2 manual. | manual-backed |
| `Smoother Version` v1/v2 mainly affects Gamma Correction / linearization. | Official v2 manual says v1 does not linearize prior to processing. | manual-backed |
| Parameter setter initializes mode/key/palette/gamma fields and routes invert-key through the active palette. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180004e10`. | binary-grounded |
| Frame setup order is setup, optional unpremultiply, active-palette filter, non-invert scalar-key filter, then optional sRGB decode. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180002e90`. | binary-grounded |
| PF8 source loading performs integer-to-float conversion followed by multiplication with `DAT_180022690` (`float32(1/255)`), not floating-point division by 255. | `FUN_1800024c0` disassembly and the 12-case actual-AEX differential. | binary-grounded / exact-suite-confirmed |
| The sRGB decode linear branch multiplies by `DAT_1800226c0 = 0.07739938080495357 = 1/12.92`. The previous `1/12.9216` interpretation was incorrect. | AEX `.rdata` bytes `80b5492172d0b33f`, `FUN_180002ba0`, and the focused case-0011 c0d0/ab00/b120 witness. | binary-grounded / runtime-confirmed |
| The covered 8bpc conformance build uses optimization level 2. The former Xcode `-O0` build placed case-0001 ab00/cce0 alpha one ULP above AEX (`0x3f3b3b3b` vs `0x3f3b3b3a`) and left 104 max-1 AE pixels; `-O2` is Mac AE exact for all 12 cases. | AEXCompat occurrence watches at c0d0/ab00/b120/cce0, exact no-effect control, and Mac AE request `ae_pixel_olmsmoother2_current_aex_20260726_r3`. | binary-grounded / AE exact |
| Active-palette filter compares RGB against palette entries using threshold `0.001960922` and zeroes alpha for non-matches. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180002930`. | binary-grounded |
| Non-invert scalar-key filter compares RGB against scalar key with threshold `0.001960922` and zeroes alpha for matches. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180002a70`. | binary-grounded |
| Class-plane generation uses Smooth Range in the no-key path as `SmoothRange / 100.0 + 0.001`. | `notes/OLMSmoother2_ASM_FACTS.md`, no-key grid finding. | binary-grounded / reference-confirmed |
| Class-plane bytes record self-vs-left, self-vs-top, self-vs-top-left, self-vs-top-right local comparisons. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_18000ae10`. | binary-grounded |
| Smoothing geometry is not an 8-neighbor blur. It is a 2x2-cell classifier that builds an 8-bit switch index and dispatches into a large helper table. | `disasm/OLMSmoother2_port_gap_analysis.md`, `FUN_18000c280`, `disasm/OLMSmoother2_case_map.txt`. | binary-grounded |
| Polygon vertices sample integer grid pixels, not bilinear positions. | `disasm/OLMSmoother2_port_gap_analysis.md`, `FUN_1800104d0`. | binary-grounded |
| Small corner helper family uses `0.125` base step and `0.4/0.2/0.4` weights. | `disasm/OLMSmoother2_port_gap_analysis.md`, `FUN_1800134c0`, `FUN_180013570`, `FUN_180012c20`, `FUN_180012ce0`. | binary-grounded |
| `FUN_18000cc70` normalizes emitted vertex weights by vertex count. | `disasm/OLMSmoother2_port_gap_analysis.md`. | binary-grounded |
| Final writeback premultiplies RGB by output alpha in the output writer path. 8bpc uses `FUN_180003370` via `FUN_180003d00`; `FUN_1800036e0` is the float writer and did not execute in the 8bpc legacy AE trace. | `decomp/OLMSmoother2.aex.c.txt`, 2026-06-20 writeback-extract failure return. | binary-grounded / guarded |
| Legacy `case_0001` target pixel `(712,406)` receives low alpha before final packing: `FUN_18000cce0` returns floats `[0.57797289, 0.57797289, 0.57797289, 0.52794117]`, then the 8bpc writer packs `EAX=c8c8c887` / A/R/G/B `[135,200,200,200]`. | `refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_cce0_pixel_trace_20260621_0145.md`. | runtime-trace |
| Mac CLI now reproduces the runtime-traced Windows CPU AEX `cce0` value for legacy `case_0001` witness `(712,406)`: Mac `cce0_after_b120 = [0.57797277,0.57797277,0.57797277,0.52794117]`, matching Windows `[0.57797289,0.57797289,0.57797289,0.52794117]` within float print precision. The Mac output pixel `[106,106,106,135]` follows from the same final store, while the old Windows reference PNG has `[207,207,207,207]` identical to input. | Local scratch trace, `refs/returns/windows/20260621_132250_smoother2_cce0_internals_replay_from_writer/`. | binary-grounded / provenance-blocked |
| Current Windows AE 2026 Software recapture confirms the runtime-traced CPU behavior: source input pixel `(712,406)` is `[207,207,207,207]`, current AEX output is `[106,106,106,135]`, and Mac CLI with the same source input also outputs `[106,106,106,135]`. AE `saveFrameToPng` before/control frames are premultiplied to `[168,168,168,207]`, so CLI tests must not use the AE-saved before frame for this recapture when proving source-equivalence. | `refs/win_references/olm_reference_return_windows_smoother2_legacy_current_aex_recapture_20260621/OLMSmootherv2/`, local direct-source rerun. | current-AEX witness exact / old-ref stale |
| Full current-AEX recapture covers all 12 legacy cases. Using the returned source input gives a close `legacy_case_0001` measurement (`max=43 mean=0.0020`), but key/gamma cases are more consistent when the CLI uses AE-saved premultiplied before frames: `legacy_case_0002` and `legacy_case_0003` become exact, and the remaining residuals are localized (`max=94..224`, `mean=0.0183..0.3266`). | `refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2/`, local CLI probes. | current-reference measured / residual-classified |
| Current-AEX residual writer trace proves the remaining `0004`/`0012` residual is not PNG export or 8bpc packing. Windows writer receives final values for `0004 (501,1055)` as `[159,95,95,255]` with reconstructed result-area floats `[0.34566423,0.11387402,0.11387402,1.0]`; before the Smooth Range threshold fix Mac cce0 for the same witness produced neutral `[65,65,65,255]` from one gray sample. Windows writer receives `0012 (500,877)` as `[9,9,9,255]` with floats `[0.002731743,0.002731743,0.002731743,1.0]`, while Mac currently leaves a smaller localized residual. | `refs/returns/windows/20260621_smoother2_legacy_current_aex_residuals_trace/`, local `--trace-pixel` probes. | writer-grounded / polygon-classifier blocked |
| The preserved `0004 +0x350b` pre-call `[rsp+0x48]` floats are not target input evidence. Decomp shows `rcx=[rsp+0x48]` is the `FUN_18000cce0` output buffer, and the saved red-heavy value `[0.78198957,0.0015756468,0.0015756468,1.0]` matches Mac `cce0_after_b120` for the neighboring previous pixel `(500,1055)`. Treat it as stale output-buffer content. The remaining hard witness for `(501,1055)` is the Windows final writer value `[0.34566423,0.11387402,0.11387402,1.0]` / `[159,95,95,255]`. | `refs/returns/windows/20260621_smoother2_legacy_current_aex_0004_cce0_stepover/`, local Mac `--trace-pixel` probes for `(500,1055)` and `(501,1055)`. | false-lead retired / writer-grounded |
| Key-enabled current-AEX class-plane generation follows Smooth Range, not the earlier key-predicate threshold. With Smooth Range promoted to the default, `0004 (501,1055)` changes from `idx=192` / one gray sample / `[0.05220960,0.05220960,0.05220960,1.0]` to `idx=208` / three samples / `cce0_after_b120=[0.34566417,0.11387399,0.11387399,1.0]`, matching the Windows final writer floats within print precision. The 11 before-frame measured legacy cases improve from mean-sum `1.3008` to `0.0589`; `0002` and `0003` remain exact. | Local `--class-threshold-mode` sweep and `refs/scripts/smoke_olmsmoother2_legacy_current_aex_cli.py`. | implementation-improved / residual-classified |
| Local producer-path diff groundwork now assembles the active `0004`/`0012` witness lanes as a writer-anchored stage matrix, so the next harness only needs the first unresolved producer proof. `0004` is reduced to `idx=0xd0` polygon-or-fallback evidence; `0012` is reduced to the first divergence inside `cardinal6/e170/f270/e3a0`. | `scripts/analyze_smoother2_producer_path_diff.py`, `refs/scripts/smoke_analyze_smoother2_producer_path_diff.py`. | harness-grounded |
| Accepted Windows actual-AEX producer witness for `legacy_case_0012_gamma5_red_blue_current_aex` binds the live lane at writer hook `+0x350b`, captures exact call order `f270 entry -> e170 entry/return -> e3a0 entry/return -> f270 return`, returns valid `e170_c=7`, and preserves one-vertex raw words `3e3ce706,3e3ce706,3e3ce706,3f2eaeaf` / `3e91a7b9`. The corrected rerun proves live `RDX p2[0..5]=92,841,1,92,842,2`, sample `x/y=92,841`, center bytes `255,255,0,255`, previous bytes `255,0,0,0`, left bytes `0,255,0,255`, and predicate bits `center_b0=255`, `prev_b0=255`, `left_b1=255`, which match `e170_c=7`. The then-current `91,841,...` Mac descriptor difference was superseded by the frame-setup correction in the next row. | `refs/conformance/olmsmoother2_legacy_key_producer_actual_aex_20260716.md`, `refs/reports/runtime_trace_summary_windows_witness_olmsmoother2_legacy_key_producer_common_core_20260716_20260716_150855.json`, `refs/windows_returns/20260716/20260716_150500__RETURN__OLMSMOOTHER2_RDX_DESCRIPTOR_CORRECTED/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip`. | current-AEX witness exact / predicate matched / descriptor superseded |
| The case_0012 upstream descriptor divergence was the Mac frame-setup unpremultiply gate. Windows `FUN_180002e90` tests render byte `+0x18`, which is setter byte `+0x20` after `FUN_180005180` returns `base+8`; `FUN_180004e10` leaves that byte zero and does not bind it to Enable Color Key. Removing the Mac `enable_key -> unpremultiply` shortcut reproduces Windows class bytes, descriptor `92,841,1,92,842,2`, `e170 c=7`, and the first appended RGBA/weight within float print precision. | `refs/conformance/olmsmoother2_case0012_unpremul_gate_20260716.md`, `FUN_180002e90`, `FUN_180004e10`, `FUN_180005180`. | binary-grounded / typed-witness matched / AE validation pending |
| The accepted descriptor `92,841,1,92,842,2` selects `FUN_18000fef0` key `0x14`. The checked-in actual AEX and portable dispatcher both call `f270` followed unconditionally by `f130` and grow the polygon `0 -> 2`. Direct `df30 -> f130 -> e290` probes read a distinctive nonzero source at `(92,843)` and agree on emitted RGBA, weight within `1e-6`, append decision, and count `1 -> 2`. The accepted live Windows witness ends at the first count `1`, so the unresolved boundary is the live post-leaf polygon state before `cce0`, not local dispatch or second-leaf payload math. | `refs/conformance/olmsmoother2_case0012_second_leaf_20260716.json`, `tools/emulation/test_smoother2_case0012_second_leaf_20260716.py`. | Actual-AEX/portable second-leaf payload exact / live post-leaf state unobserved |
| A bounded direct-call fixture now captures both sides immediately after `f270` and after unconditional `f130`. Actual AEX and the current portable path agree on descriptor/key, `e170 c=7`, return bytes, counts `1 -> 2`, and both RGBA/weight payloads within `1e-6`; neither side enters `cce0`. This closes the synthetic two-leaf polygon state only. The accepted live Windows trace still stops after the first vertex, so live post-`f130` state entering `cce0` remains the next context-bound proof. | `refs/conformance/olmsmoother2_case0012_post_leaf_20260716.md` / `.json`. | bounded actual-AEX/portable post-leaf exact / live context unresolved |
| The Mac AE boundary probe exposed a separate PF8 host-input contract before frame setup. At `(92,840)`, the retained raw PNG is `[174,174,174,174]` while the Windows before-effects frame is `[119,119,119,174]`. Native-code nearest premultiplication `(rgb*alpha+127)//255` gives `119`; loading that byte and applying the grounded sRGB decode reproduces the accepted Windows first append (`Mac 0.18447499`, Windows 0.18447503), class bytes, descriptor, `e170 c=7`, and first weight. This diagnostic closes the first causal chain but is not yet a permanent plug-in policy: the full candidate remains known-red and the live Windows post-`f130` polygon is still missing. | `refs/conformance/olmsmoother2_pf8_host_adapter_chain_20260718.md`, `refs/scripts/smoke_olmsmoother2_pf8_host_adapter_chain_20260718.py`. | host-boundary binary-grounded / first append matched / live post-leaf unresolved |
| A bounded 16x16 Unicorn run now executes the checked-in current Windows AEX naturally from the audited PF8 adapter through key removal, sRGB decode, class-plane generation, `cce0 -> c280 -> fef0 -> f270 -> f130`, and the compact two-vertex cce0 input. The post-boost builder polygon is float32-word identical to the compact polygon consumed by cce0; the AEX returns `[0.85751957,0.85751957,0.85751957,0.93870682]`. The runner still manually constructs the crop and render config and lacks a full worker-to-writer bridge, so this proves bounded AEX ownership/reachability rather than equality with the full live Windows host context. The retained 3-ULP source difference is not attributable to UCRT `pow`: Darwin libm and a high-precision oracle agree, and forcing the retained word does not change this witness downstream. | `refs/conformance/olmsmoother2_case0012_natural_post_f130_20260718.md`, `refs/conformance/olmsmoother2_case0012_bounded_assumption_audit_20260718.md`, `refs/conformance/olmsmoother2_imported_pow_boundary_20260718.md`. | bounded actual-AEX natural chain / config-host-writer audit pending |
| The corrected PF8 load, `1/12.92` decode constant, and optimized conformance build close the full current-AEX legacy/key/gamma 8bpc set: native raw output is `12/12` byte-exact with the actual AEX plane and Mac AE is `12/12`, `max_diff=0` against Windows AE Software. | `refs/conformance/olmsmoother2_native_vs_actual_aex_20260726.md`. | AE exact / actual-AEX exact |
| The identity-bound 32bpc no-key case-07 Mac run reaches AE `26.3x87` with the expected `SOFTWARE`, FLOAT EXR, working-space, parameter, and Mach-O contracts. Its no-effect control differs from Windows at `6,106,918` raw FLOAT32 words, so the `6,108,445`-word effect delta is not attributable. Two Mac renders are raw-sample exact with each other. | `refs/conformance/olmsmoother2_no_key_32bpc_case07_mac_ae_20260726.md`. | host-control blocked / AE exact refused |

## Parameters

| UI / manifest name | Internal meaning | Evidence |
| --- | --- | --- |
| `Use Color Key` / `Enable Color Key` | Enables key filtering before smoothing. | asm setter |
| `Invert Color Key` | Routes key color through active-palette keep filter when enabled; non-invert uses scalar-key remove filter. | asm setter/frame setup |
| `Color Key` | Scalar key color or one-entry active palette, depending on invert. | asm setter |
| `Smoothness` | Strength of smoother interpolation. | manual + port |
| `Extra Smooth` | Additional smoothing strength/path. | manual + port |
| `Smooth Range` | Class-plane threshold for no-key and current-AEX key-enabled paths; nearby colors can be treated as same-color. | asm/grid/current-AEX |
| `Smoother Version` | v1/v2 gamma/linearization behavior. | official manual + asm |
| `Gamma Correction`, `Gamma Value`, `Gamma Colors` | Post-linearization gamma handling; gamma colors list is separate from active palette. | asm setter |

## Frame Setup

Current binary-grounded order:

1. `FUN_1800024c0`: frame scratch setup.
2. If byte `[SMParams + 0x18] != 0`: unpremultiply.
3. If qword `[SMParams + 0x60] != 0`: active-palette filter
   `FUN_180002930`.
4. If byte `[SMParams + 0x14] != 0`: non-invert scalar-key filter
   `FUN_180002a70`.
5. If dword `[SMParams + 0x0] != 1`: sRGB decode.

Important caution: the scalar-key filter gate is not the UI invert checkbox.
It corresponds to the non-invert scalar-key branch populated by the setter.

## Class Plane

- Built after frame setup.
- Effective threshold for no-key path:
  `SmoothRange / 100.0 + 0.001`.
- Byte layout:
  - byte 0: self vs left, when `x >= 1`
  - byte 1: self vs top, when `y >= 1`
  - byte 2: self vs top-left, when `x >= 1 && y >= 1`
  - byte 3: self vs top-right, when `y >= 1 && x + 1 < width - 1`
- ASM writes `0` or `1` via `SETNC`. Current port uses zero/nonzero semantics;
  storing `0xff` is equivalent only if downstream never compares numeric byte
  values.
- Optional pruning guarded by `[SMParams + 0x70]` should not run for no-key
  `case_0001` unless stronger evidence appears.

## Polygon Builder / Dispatch

`FUN_18000c280` builds the anti-aliased smoothing polygon. The important
structural rule is that this is a cell classifier, not a free 8-neighbor
filter.

- The switch value is:
  `switch_val = (iVar3 + uVar9 + ((!bVar16 + uVar7 * 2) * 4)) * 0x10 + iVar4 + (local_1b7 == 0) + iVar11 + iVar10`.
- The low nibble comes from four class-plane bytes for the current 2x2-ish
  cell; the high nibble comes from neighboring context probes.
- `disasm/OLMSmoother2_case_map.txt` currently maps 222 used cases and 34
  fallthrough/default cases.
- The polygon struct uses a vertex array at Win offset `+0x40` and a count at
  `+0x130`. Each vertex is sampled by integer grid coordinate through
  `FUN_1800104d0` as `{R,G,B,A,w}`.
- Corner helpers are small and already high-confidence:
  - NW `FUN_1800134c0`: `(-1,0)`, `(-1,-1)`, `(0,-1)` with `0.4/0.2/0.4`.
  - NE `FUN_180013570`: `(0,-1)`, `(+1,-1)`, `(+1,0)` with `0.4/0.2/0.4`.
  - SW `FUN_180012c20`: `(-1,0)`, `(-1,+1)`, `(0,+1)` with `0.4/0.2/0.4`.
  - SE `FUN_180012ce0`: `(0,+1)`, `(+1,+1)`, `(+1,0)` with `0.4/0.2/0.4`.
- The current Mac port has many literal helper/dispatcher pieces already, but
  it still contains diagnostic controls such as `--idx18-mode` and
  `--skip-index`. Those are probes only; they must not be used as acceptance
  fixes.

## Distance Metric

`FUN_18000b2b0`:

- returns zero when both alphas are zero;
- otherwise returns `max(abs(dR), abs(dG), abs(dB), abs(dY709)) + abs(dA)`;
- luma coefficients are `0.2126`, `0.7152`, `0.0722`.

## Current Residual Interpretation

- 2026-06-19 AE pixel return update:
  `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmsmoother2_no_key_grid_20260619/reports/ae_pixel_no_key_grid_exact.json`
  is exact for all 12 no-key grid cases. This means the current Mac AE plug-in
  path matches the packaged Windows Software reference for that grid. The older
  AE-free residual remains useful as a harness/IR discrepancy, not as a reason
  to PNG-tune the no-key Mac AE path.
- The same return leaves the legacy key/gamma request red:
  `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json`
  fails all 7 cases with max diff up to `254`. The next Smoother blocker is
  legacy setup/key/gamma/writeback evidence, plus optional runtime trace to
  explain why the no-key AE path is exact while the CLI harness previously was
  only near-exact.
- 2026-06-20 AE pixel rerun:
  `refs/reports/ae_host_validation_20260620_1425/`.
  This confirms the v1 reference-shape issue was a packaging/render setup
  problem, not an algorithm result: `OLMSmoother v1 case_0001..0003` are exact
  at `960x540`. The same rerun keeps Smoother2 legacy key/gamma red at `0/7`
  exact, with the same `max=101/254` range.
- 2026-06-20 Smoother2 legacy follow-up addendum:
  `refs/reports/ae_host_validation_20260620_smoother2_legacy_followup/`.
  This is AE pixel validation evidence, not runtime trace. It keeps the legacy
  adjustment-layer rerun at `0/7` exact (`case_0001 max=101`, remaining cases
  up to `254`). For `case_0001`, the sweep variants did not improve the
  original output: `Gamma Correction=0` and `GPU Rendering=2` were metric-
  identical to original, while `Smoother Version=1`, `Gamma Correction=2`,
  `Smooth Range=1`, and `Smoother Version=1 + Gamma Correction=0` were worse.
  This rules out the tested gross AE runner/setup causes, and points back to a
  real legacy key/gamma/class-plane/writeback mismatch.
- 2026-06-20 dense runtime trace return:
  `refs/reports/dense_runtime_trace_20260620/runtime_trace_summary_dense_all_20260620_184543.md`.
  This return was valid and machine-readable, but the dense return audit says
  no new live debugger trace was captured for the legacy key/gamma request.
  The template was filled with explicit `not traced / not isolated` strings, so
  it does not settle parameter struct, key polarity, class-plane, gamma, or
  writeback values. Treat its formal `answered` status as an intake fact only,
  not as Smoother2 proof. The current follow-up package is
  `refs/runtime_trace_packages/olm_runtime_trace_dense_live_followup_20260620_184655.zip`.
- 2026-06-20 dense live follow-up all-attempts return:
  `refs/reports/dense_live_followup_20260620/runtime_trace_summary_dense_live_followup_20260620_213031.md`.
  This return did run Windows AE/CDB for all 9 live-followup request IDs.
  For Smoother2 legacy it proves the candidate functions are reachable:
  `OLMSmoother2+0x36e0` hit 2 times, `+0x10550` hit 6440 times, and
  `+0xc280` hit 44451 times during the legacy AE pixel validation run.
  However, the included `cdb_hits_excerpt.txt` preserves mostly hit markers and
  counts; the actual register/stack dumps around the two `+0x36e0`
  writeback-candidate hits are not present in the zip. Therefore this is
  reachability/control-flow proof, not yet parameter/key/class-plane/writeback
  proof.
- The next Smoother trace should not be another broad all-plugin run. It should
  extract the complete windows around the two `HIT_FUN_1800036e0_writeback_candidate`
  hits from the existing Windows full log, whose path was recorded as
  `C:\Users\optim\Documents\Codex\2026-06-11\files-mentioned-by-the-user-olm\work\live_attempt_smoother2_legacy_20260620\cdb_console.txt`.
  The generated package profile is `smoother2-legacy-writeback-extract`.
- 2026-06-20 Smoother2 legacy writeback extraction return:
  `refs/reports/smoother2_legacy_writeback_extract_20260620/runtime_trace_summary_smoother2_legacy_writeback_extract_20260620_231855.md`.
  This return corrects the previous interpretation. The existing full log was
  available, but the only `HIT_FUN_1800036e0_writeback_candidate` lines were
  breakpoint setup/listing lines. A scoped rerun completed all requested legacy
  cases, but `OLMSmoother2+0x36e0` did not fire. Therefore `+0x36e0` should no
  longer be treated as the active 8bpc writeback path for these references.
  Decomp shows the 8bpc writer is `FUN_180003370`, invoked by
  `FUN_180003d00`, while `FUN_1800036e0` is the float writer invoked by
  `FUN_180003d90`. The next trace target is `OLMSmoother2+0x3370` and wrapper
  `OLMSmoother2+0x3d00`.
- 2026-06-20 Smoother2 legacy u8 writer trace return:
  `refs/reports/smoother2_legacy_u8_writer_trace_20260620/runtime_trace_summary_smoother2_legacy_u8_writer_trace_20260620_233427.md`.
  This directly confirms the active 8bpc writer path: `OLMSmoother2+0x3370`
  / `FUN_180003370` hit 26 times for `case_0001`, and `OLMSmoother2+0x3d00`
  / `FUN_180003d00` hit once. The returned first 20 hits include entry
  registers, call stacks, and p5-p9 pointer memory dumps. Because the
  breakpoint was at function entry, it does not yet decode per-pixel loop
  coordinates, `FUN_18000cce0` output floats, gamma/premultiply branch state,
  or packed store bytes.
- Disassembly pins the next per-pixel breakpoint sites inside
  `FUN_180003370`:
  - `+0x350b`: `CALL 0x18000cce0`.
  - `+0x3510`: immediately after orchestrator return; local x/y are
    `[RSP+0x34]` / `[RSP+0x38]`, and output floats are staged at
    `[RSP+0x48]..[RSP+0x54]`.
  - `+0x35ad`: before scale/add/pack.
  - `+0x360e`: immediately before `MOV dword ptr [RSI],EAX` final 8bpc store.
  The selected high-diff witness is `case_0001 (712,406)`, expected RGBA
  `[207,207,207,207]` vs candidate RGBA `[106,106,106,135]`.
- 2026-06-21 Smoother2 legacy u8 per-pixel trace return:
  `refs/reports/smoother2_legacy_u8_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_u8_pixel_trace_20260621_0040.md`.
  The trace did not capture the requested `+0x3510` stack-float snapshot, but
  it did capture the final packed writer value at `OLMSmoother2+0x3610`, right
  after the `+0x360e` store for the target output address. The observed packed
  value is `EAX=c8c8c887`, little-endian bytes `87 c8 c8 c8`, interpreted as
  A/R/G/B `[135,200,200,200]`.
  This explains the AE PNG candidate `[106,106,106,135]` because
  `round(200 * 135 / 255) == 106`. Therefore the `case_0001 (712,406)` max
  residual is upstream of the final 8bpc store: the writer receives alpha/RGB
  values that already encode the failing output. Do not spend the next step on
  store rounding. Move upstream to `FUN_18000cce0` output, polygon composition,
  class-plane inputs, or key/gamma setup for this pixel.
- 2026-06-21 Smoother2 legacy cce0 target-pixel trace return:
  `refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_cce0_pixel_trace_20260621_0145.md`.
  This answered the immediate upstream question. At the same witness pixel,
  the `FUN_18000cce0` returned floats are
  `[0.57797289, 0.57797289, 0.57797289, 0.52794117]`; the writer then packs
  the RGB through the gamma/OETF path to `200` and alpha directly to `135`
  (`EAX=c8c8c887`). The writer flag byte `[RBP+0x19]` is `00`, so a hidden
  writer-side premultiply branch is not the explanation. The observed PNG
  value still follows from premultiplication during AE/export. Therefore the
  remaining bug for this witness is inside `FUN_18000cce0` or before it:
  polygon construction (`FUN_18000c280`), class-plane/key inputs, or the
  `bb10`/`c0d0`/`ab00`/`b120` composite chain.
- Therefore the current Smoother priority is not the no-key grid. It is the
  legacy key/gamma setup and cce0 composite path. The project-local priority
  trace package is:
  `refs/runtime_trace_packages/olm_runtime_trace_smoother2_legacy_cce0_internals_trace_*.zip`.
  It targets the already isolated `case_0001 (712,406)` witness and asks for
  `FUN_18000cce0` stage internals. The older broad key/gamma package remains
  useful if this focused trace cannot isolate the source.
- 2026-06-21 Smoother2 legacy cce0 internals trace return:
  `refs/returns/windows/20260621_011845_smoother2_cce0_internals/olm_runtime_trace_smoother2_legacy_cce0_internals_trace_20260621_011845_return_windows.zip`.
  This is a `failed_partial` result, not an answered internals trace. It did
  not capture the target-pixel `FUN_18000cce0` composite chain for
  `case_0001 (712,406)`. The useful evidence is negative/scoping evidence:
  `OLMSmoother2+0xcd5f` is reachable, an unconditional probe hit 64 times, and
  `RSI` at that site points to x/y dwords, but the target qword
  `00000196\`000002c8` was not observed by the attempted conditions. At
  `+0xcd5f`, `mov r14,[rbp+0x90]` has not executed yet, so any next polygon
  count probe must read `[rbp+0x90]` or break after stepping that instruction.
  Do not treat this return as stage-value proof; it only says the next trace
  must be driven from the already successful writer/data-watch target or from
  an output-address watchpoint, not from a broad `+0xcd5f` coordinate filter.
  The next packaged request is therefore the R9-callsite variant:
  `olmsmoother2_legacy_cce0_internals_r9_callsite_trace_20260621`. Its primary
  breakpoint is `OLMSmoother2+0x350b` with `dwo(@r9)==0x2c8` and
  `dwo(@r9+4)==0x196`, then one-shot stage breakpoints inside the same
  `FUN_18000cce0` call.
- 2026-06-21 Smoother2 legacy cce0 R9-callsite return:
  `refs/returns/windows/20260621_022708_smoother2_cce0_internals_r9_callsite/olm_runtime_trace_smoother2_legacy_cce0_internals_r9_callsite_20260621_022708_return_windows.zip`.
  This also returned `failed_partial`: the `OLMSmoother2+0x350b` breakpoint
  with `dwo(@r9)==0x2c8 && dwo(@r9+4)==0x196` was installed, AE Software render
  completed, and the target callsite condition did not hit. Static disassembly
  still confirms `+0x350b` is the `CALL FUN_18000cce0` and `R9 = RSP+0x34`
  immediately before the call, so the next request should stop relying on
  coordinate-only filtering. Reuse the older successful data-watch anchor:
  compute `$t3` at writer entry `+0x3370`, catch the current pixel loop at
  `+0x34b0` when `@rsi == @$t3`, then collect the same `FUN_18000cce0` stage
  breakpoints before the final `+0x3610` store.
- 2026-06-21 Smoother2 legacy cce0 target-address return:
  `refs/returns/windows/20260621_025613_smoother2_cce0_internals_targetaddr/olm_runtime_trace_smoother2_legacy_cce0_internals_targetaddr_20260621_025613_return_windows.zip`.
  This also returned `failed_partial`. Writer entry `+0x3370` did execute and
  computed latest run candidate output addresses `$t1=000001cd\`22545c20`,
  `$t2=000001cd\`23c1a020`, `$t3=000001cd\`2145a020`, but the requested
  `+0x34b0 @rsi == @$t3` loop condition did not hit. The next request must not
  assume `$t3` ownership. It should arm write watchpoints for all `$t1/$t2/$t3`
  and compare `+0x34b0` against all three candidates, returning either the
  internal cce0 stages or the actual T address that receives the target write.
- 2026-06-21 Smoother2 legacy cce0 multi-address return:
  `refs/returns/windows/20260621_031230_smoother2_cce0_internals_multiaddr_probe/olm_runtime_trace_smoother2_legacy_cce0_internals_multiaddr_probe_20260621_031230_return_windows.zip`.
  This returned `failed_partial`, but it answered the ownership question:
  `$t3=00000272\`2244a020` receives the target pixel write at
  `OLMSmoother2+0x3610`, with `EAX=00000000c8c8c887` and stack xy
  `(712,406)`. The `+0x34b0` candidate-loop condition still did not hit for
  `$t1/$t2/$t3`, so the next trace must anchor at the actual pre-cce0 callsite:
  compute `$t3` at `+0x3370`, then break at `+0x350b` when `@rsi == @$t3` and
  arm the one-shot `FUN_18000cce0` stage probes from there.
- 2026-06-21 Smoother2 legacy cce0 T3-RSI callsite return:
  `refs/returns/windows/20260621_032645_smoother2_cce0_internals_t3_rsi_callsite/olm_runtime_trace_smoother2_legacy_cce0_internals_t3_rsi_callsite_20260621_032645_return_windows.zip`.
  This also returned `failed_partial`. It confirms the pre-call plan is not a
  stable target anchor in retained Windows runs: `+0x350b @rsi == @$t3` did
  not hit, and the cross-check `+0x350b @rdi==0x2c8 && @r14==0x196` also did
  not hit, while the previous `+0x3610` writer fact remains valid. The next
  request should start from the reliable writer stop, dump the full writer
  frame, and either replay `FUN_18000cce0` from reconstructed arguments or
  return a complete argument block for local replay.
- 2026-06-21 Smoother2 legacy cce0 replay-from-writer return:
  `refs/returns/windows/20260621_132250_smoother2_cce0_internals_replay_from_writer/olm_runtime_trace_smoother2_legacy_cce0_internals_replay_from_writer_20260621_132250_return_windows.zip`.
  This returned `failed_partial` because live replay was correctly skipped as
  unsafe, but it captured the reconstructed `FUN_18000cce0` argument block and
  the same output floats `[0.57797289,0.57797289,0.57797289,0.52794117]`.
  After adding Mac-side `cce0` stage trace, the current Mac CLI reports
  `cce0_after_b120 = [0.57797277,0.57797277,0.57797277,0.52794117]` for the
  same `case_0001 (712,406)` witness. The CPU AEX algorithm is therefore not
  the likely source of the old PNG residual at this pixel. The active next
  proof is reference provenance: `refs/reference_requests/smoother2_legacy_current_aex_recapture_20260621.json`.
- 2026-06-21 Smoother2 legacy current-AEX recapture return:
  `refs/returns/windows/20260621_smoother2_legacy_current_aex_recapture/olm_reference_return_windows_smoother2_legacy_current_aex_recapture_20260621.zip`.
  Imported to
  `refs/win_references/olm_reference_return_windows_smoother2_legacy_current_aex_recapture_20260621/OLMSmootherv2/`.
  It resolves the old-reference ambiguity. The source input pixel `(712,406)`
  is `[207,207,207,207]`; current Windows AE 2026 Software output for
  `legacy_case_0001_current_aex` is `[106,106,106,135]`; Mac CLI with the
  included source input and same params also outputs `[106,106,106,135]`.
  The old `refs/win_references/20260605_extra/OLMSmoother2/case_0001.png`
  value `[207,207,207,207]` is stale/non-current for this CPU Software witness.
  Caveat: AE-saved `before_effects_frame` and the smoothness0 control are
  `[168,168,168,207]` at the witness due PNG/premultiply behavior, so use
  `input/current_olm_cells.png` for source-equivalence CLI checks.
- 2026-06-21 Smoother2 legacy full current-AEX recapture return:
  `smoother2_legacy_full_current_aex_recapture_20260621` imported cleanly with
  12/12 requested Software cases covered. Two local CLI probes were run:
  - returned source input for all cases:
    `legacy_case_0001 max=43 mean=0.0020`; remaining key/gamma cases have
    `max=254` and `mean=0.5235..0.7264`, with nonzero pixels under 1.43%.
  - AE-saved premultiplied before frames:
    `legacy_case_0002` and `legacy_case_0003` are exact; the remaining
    residuals are localized (`0004 max=94 mean=0.0183`,
    `0005 max=224 mean=0.3266`, `0006 max=130 mean=0.0289`,
    `0007 max=176 mean=0.1610`, `0008 max=99 mean=0.0543`,
    `0009 max=128 mean=0.1727`, `0010/0011 max=167 mean=0.1415/0.1453`,
    `0012 max=167 mean=0.2522`).
  Representative max-diff witnesses from the AE-saved before-frame probe:
  - `0004`: `(501,1055)`, Windows `[159,95,95,255]`, Mac CLI
    `[65,65,65,255]`, diff `[94,30,30,0]`.
  - `0005`: `(679,674)`, Windows `[0,0,255,255]`, Mac CLI
    `[0,0,31,255]`, diff `[0,0,224,0]`.
  - `0006`: `(501,1056)`, Windows `[130,2,2,255]`, Mac CLI
    `[0,0,0,255]`, diff `[130,2,2,0]`.
  - `0007`: `(500,880)`, Windows `[0,0,0,255]`, Mac CLI
    `[176,103,103,255]`, diff `[176,103,103,0]`.
  - `0008`: `(500,880)`, Windows `[0,0,0,255]`, Mac CLI
    `[99,56,56,255]`, diff `[99,56,56,0]`.
  - `0009`: `(908,734)`, Windows `[0,0,0,0]`, Mac CLI
    `[125,48,48,128]`, diff `[125,48,48,128]`.
  - `0010`, `0011`, `0012`: `(500,877)`, Windows `[9,9,9,255]`,
    Mac CLI `[176,112,112,255]`, diff `[167,103,103,0]`.
  Interpretation: no more broad Windows PNG capture is needed for this slice.
  The next Smoother2 work is narrow binary/runtime classification of input
  premultiply semantics and the remaining key/gamma/writeback residuals.
- 2026-06-21 Smoother2 legacy current-AEX residual writer trace return:
  status is `answered_partial`, but the stable final writer evidence is useful.
  - `0002 (500,877)` control: source/before `[9,9,9,255]`, Windows writer
    raw `EAX=0000000009090900`, exported `[0,0,0,0]`. This matches the
    Mac exact-control behavior and confirms alpha-zero output is intentional.
  - `0004 (501,1055)`: source/before `[12,12,12,255]`, Windows writer
    raw `EAX=000000005f5f9fff`, exported `[159,95,95,255]`. Reconstructed
    result-area floats are `[0.34566423,0.11387402,0.11387402,1.0]`.
    Mac trace for the same pixel currently has `idx=192`, one neutral sample
    `(501,1054)` with weight `0.0875`, `cce0_after_b120=[0.05220960]*3,1`,
    then output `[65,65,65,255]` after the final sRGB writer.
  - `0012 (500,877)`: source/before `[9,9,9,255]`, Windows writer
    raw `EAX=00000000090909ff`, exported `[9,9,9,255]`. Reconstructed
    result-area floats are `[0.002731743,0.002731743,0.002731743,1.0]`.
    Mac trace currently has `idx=22` and three samples, including red
    neighbors; `cce0_after_b120=[0.43280423,0.16133800,0.16133800,1]`,
    which becomes `[176,112,112,255]`.
  Interpretation: final writer and input ownership are no longer the likely
  source. The remaining mismatch is in class-plane / switch-index / polygon
  emitter semantics. `0004` needs stronger/redder Windows polygon evidence;
  `0012` needs proof that Windows polygon is empty or gated before composite.
- 2026-06-21 Smoother2 legacy current-AEX polygon trace return:
  `refs/returns/windows/20260621_smoother2_legacy_current_aex_polygon_trace/olm_runtime_trace_smoother2_legacy_current_aex_polygon_20260621_return_windows.zip`.
  This returned `answered_partial`. It recaptured the final writer stores and
  proved the `+0x350b` cce0 argument layout, but it did not isolate c280/polygon
  facts for the exact residual witnesses.
  - `+0x350b` probe: for cce0 calls, `@r9[0]` is x and `@r9[1]` is y. Example
    hit in case `0012`: `rdi_x=500`, `r14_y=1004`, `@r9` dwords
    `[0x1f4,0x3ec,0,0x3ec]`.
  - For `0004 (501,1055)`, the final writer still hits `+0x3610` with
    `EAX=0x5f5f9fff`; stack dwords near the writer are
    `[0x418,0x1f5,0x41f,0,0x41f,0]`; result floats are
    `[0.34566423,0.11387402,0.11387402,1.0]`.
  - For `0012 (500,877)`, the final writer still hits `+0x3610` with
    `EAX=0x090909ff`; stack dwords near the writer are
    `[0x368,0x1f4,0x36d,0,0x36d,0]`; result floats are
    `[0.002731743,0.002731743,0.002731743,1.0]`.
  - The validated target-XY conditions at `+0x350b` did not hit for either
    exact witness, so there are no `ENTER_C280_XY_TARGET`,
    `APPEND_104D0_XY_TARGET`, or after-stage records for these pixels.
  Interpretation: do not repeat a final-output-XY-only `+0x350b` filter. The
  next trace must backtrack from the successful writer store/output address and
  recover the actual upstream callsite/coordinate convention, or prove that
  these witness pixels bypass the normal `+0x350b -> cce0/c280` path.
- 2026-06-21 Smoother2 legacy current-AEX writer-backtrack return:
  `refs/returns/windows/20260621_smoother2_legacy_current_aex_writer_backtrack/olm_runtime_trace_smoother2_legacy_current_aex_writer_backtrack_20260621_return_windows.zip`.
  The machine-readable summary is conservative and says the upstream call was
  not recovered, but direct CDB log inspection adds an important correction:
  `legacy_case_0004_current_aex` did hit `OLMSmoother2+0x350b` with the exact
  target coordinates.
  - Writer-loop disassembly confirms the normal 8bpc path:
    `+0x34b5` sets `r9=[rsp+0x34]`, `+0x34e0` writes x,
    `+0x34f8` writes y, `+0x350b` calls `FUN_18000cce0`,
    `+0x3510..+0x3530` reads result floats, and `+0x360e` stores the final
    packed dword.
  - For `0004 (501,1055)`, the `@rsp+0x34/@rsp+0x38` condition hit
    `+0x350b`. The callsite dump has `x=0x1f5`, `y=0x41f`,
    `rcx=[rsp+0x48]`, `rdx=[rsp+0x80]`, `r8=[rsp+0x60]`,
    `r9=[rsp+0x34]`. The pre-call result buffer at `rcx` contained
    `[0x3f483078,0x3ace85ef,0x3ace85ef,0x3f800000]`
    = `[0.78198957,0.0015756468,0.0015756468,1.0]`.
  - The script armed internal breakpoints at `+0xc280`, `+0xc50a`,
    `+0x104d0`, `+0xc7dd`, and `+0x3510`, but the log did not capture the
    post-call `+0x3510` state or c280 internals. The next request should step
    over/into the already-observed `+0x350b` hit rather than trying to
    rediscover the writer coordinates.
  - For `0012 (500,877)`, the target condition did not hit before AE reported
    an access violation at `OLMSmoother2+0x98f2`; keep it secondary until the
    0004 call can be stepped through.
  Interpretation: 0004 is now the best live witness. The immediate missing
  fact is the `FUN_18000cce0` return at `+0x3510` and, if reachable, the
  c280 switch/polygon records from that same call.
- 2026-06-21 Smoother2 legacy current-AEX 0004 cce0 step-over return:
  `refs/returns/windows/20260621_smoother2_legacy_current_aex_0004_cce0_stepover/olm_runtime_trace_smoother2_legacy_current_aex_0004_cce0_stepover_20260621_return_windows.zip`.
  This also returned `answered_partial`. It preserves the prior exact
  `+0x350b` pre-call hit but could not reproduce/step it in fresh reruns.
  - Preserved exact hit: `0004 (501,1055)` stopped at `+0x350b` with
    `x=0x1f5`, `y=0x41f`, `r9=[rsp+0x34]`, and pre-call `[rsp+0x48]`
    values `[0x3f483078,0x3ace85ef,0x3ace85ef,0x3f800000]`
    = `[0.78198957,0.0015756468,0.0015756468,1.0]`.
  - Three focused reruns (`continue`, `p` step-over, and old-package retry)
    rendered the same correct output PNG pixel `[159,95,95,255]`, but did not
    reproduce the exact `x=0x1f5,y=0x41f` `+0x350b` hit before shutdown.
  - An `x=0x1f5` sampling run observed 12 cce0 calls with y values
    `0x329,0x383,0x3d2,0x39d,0x425,0x425,0x42d,0x41d,0x415,0x427,0x41e,0x417`;
    target `0x41f` was absent. Near hits show pre-call buffers:
    `y=0x41d -> [0.88968968,0.0068502375,0.0068502375,1.0]` and
    `y=0x41e -> [0.80821502,0.06012414,0.06012414,0.97499996]`.
  - The requested post-call `+0x3510` result, c280 switch index, polygon count,
    vertices, weights, and append sequence remain not isolated.
  Interpretation: the target cce0 call is not reproducible enough under the
  current AE/OpenMP/CDB workflow. Do not keep burning Windows trips on the same
  exact breakpoint unless the helper can freeze thread scheduling or single-step
  immediately within the already-hit session. A later Mac audit retired the
  preserved pre-call value as a target-input clue: `rcx=[rsp+0x48]` is the
  cce0 output buffer, and the red-heavy value matches the Mac result for the
  neighboring previous pixel `(500,1055)`. The useful Mac-side next move is to
  audit the local cce0/classifier/polygon path against the final writer floats
  `[0.34566423,0.11387402,0.11387402,1.0]`, while ignoring stale pre-call
  output-buffer content.
- 2026-06-21 Smoother2 Mac-side classifier diagnostics:
  - Before the Smooth Range threshold promotion, `0004 (501,1055)` built
    `idx=192` from one gray sample `(501,1054)` and reported
    `cce0_after_b120=[0.05220960,0.05220960,0.05220960,1.0]`, producing
    `[65,65,65,255]` after the final sRGB writer.
  - Promoting the key-enabled class-plane threshold to Smooth Range changes
    the same target to `idx=208`, `count=3`,
    `cce0_after_b120=[0.34566417,0.11387399,0.11387399,1.0]`. This matches
    the Windows final writer floats
    `[0.34566423,0.11387402,0.11387402,1.0]` within trace print precision,
    though the whole `0004` frame still has localized residual
    (`max=113 mean=0.0045`).
  - Neighbor probes show `(500,1055)` produces
    `cce0_after_b120=[0.78198946,0.00157565,0.00157565,1.0]`, which explains
    the preserved Windows pre-call buffer as stale previous-pixel output.
  - Diagnostic class-plane timing / byte-read variants can force this target
    into `idx=0` with a red/gray 12-vertex polygon. `--cplane-read-mode
    south2-se1 --idx0-mode double` reaches local floats
    `[0.37729287,0.14958720,0.14958720,1.0]`, closer to the Windows final
    writer `[0.34566423,0.11387402,0.11387402,1.0]` at this single point.
  - After the Smooth Range threshold promotion, the active `0012` max witness is
    no longer `(500,877)`. The frame max is `(91,841)`: Windows reference
    `[0,0,0,0]`, Mac `[90,90,90,91]`. Mac trace builds `idx=105`, center
    `rgba=(1,1,1,0)`, and one north sample `(91,840)` through
    `cardinal6 desc=(91,841,1,91,843,5) key=50`, which dispatches to
    `win_leaf_f270 -> e170/e3a0`. `win_FUN_1800125c0` is not the emitter for
    this witness (`span=1`, early false). Broad probes are rejected:
    transparent-center passthrough fixes this pixel but worsens `0012`
    (`max=155` at `(1197,449)`), `skip-index 105` worsens to `max=122`, and
    suppressing only cardinal6 key=50 worsens to `max=108`. The next useful
    proof is therefore the exact Windows `d3b0/da50/e170/f270/e3a0` state for
    this post-threshold witness, not another global alpha guard.
    However, the full 12-case legacy run worsens (`0004 max=188 mean=0.2888`
    versus normal `max=94 mean=0.0183`, and other cases regress), so these are
    diagnostic branches only, not production fixes.
- 2026-06-21 automated current-AEX residual audit:
  `scripts/analyze_smoother2_current_aex_residuals.py` runs the current-AEX
  recapture, finds the max-diff witness, and reruns the CLI with
  `--trace-pixel` for that coordinate. On the current tree it reports:
  - `0004`: max witness `(1903,519)`, Windows `[103,103,103,113]`, Mac
    `[0,0,0,0]`. Local trace builds `idx=208`, center alpha `0`, polygon
    count `0`, then transparent passthrough. This is the opposite side of the
    0012 problem: Windows appears to write a small neighbor-derived output
    where Mac has no polygon contribution.
  - `0012`: max witness `(91,841)`, Windows `[0,0,0,0]`, Mac `[90,90,90,91]`.
    Local trace builds `idx=105`, transparent center, one north sample through
    `cardinal6 desc=(91,841,1,91,843,5) key=50`, and
    `cce0_after_b120=[0.99106723,0.99106723,0.99106723,0.35492450]`.
  A full residual-case diagnostic sweep keeps `normal` as the best current
  candidate: `mean_sum=0.058945, maxmax=113`. Existing global toggles are
  rejected (`south2-se1 mean_sum=0.933151`, `south0-se1 mean_sum=1.273705`,
  `idx0-double mean_sum=1.051111`, `south2-se1+idx0-double
  mean_sum=1.443685`). Therefore the remaining mismatch is not a simple
  class-plane byte read or idx0 weight mode. Treat the exact Windows
  `d3b0/da50/e170/f270/e3a0` state for the 0012 witness, and a corresponding
  0004 polygon/no-polygon proof, as the next high-value evidence if Windows
  runtime tracing resumes.
- 2026-06-21 curve-index sweep:
  `scripts/sweep_smoother2_current_aex_curve_idx.py` reruns the nine localized
  current-AEX residual cases with CLI-only `--curve-idx-override 0..8`.
  Every curve gives the same metrics (`maxmax=113`,
  `mean_sum=0.058945`, `nonzero_sum=1.773003`, `exact_count=0`), so the
  remaining legacy residual is not explained by the unverified `bb10`
  curve-index source. Keep the override as a diagnostic only; do not promote
  it into production behavior.
- 2026-06-21 `f270/e170/e3a0` trace refinement:
  This is now a historical pre-fix local predecessor only. The then-current `0012 (91,841)` max
  witness enters `cardinal6` with `desc=(91,841,1,91,843,5)` and `key=50`.
  Local `e170` reads `A(x,y-1)=1`, `R(x-1,y)=0`, `A(x,y)=0`, producing `c=2`;
  `f270` then emits source `(91,840)` with `weight=0.35632184`,
  `rgba=(0.99106717,0.99106717,0.99106717,0.99607843)`, leading to
  `cce0_after_b120=[0.99106723,0.99106723,0.99106723,0.35492450]`.
  Suppressing all `f270` emits is rejected: the nine residual cases worsen
  from normal `mean_sum=0.058945` to `mean_sum=0.0831`-class behavior, and
  `0012` worsens from `max=91 mean=0.0151` to `max=122 mean=0.0184`. The
  accepted 2026-07-16 Windows actual-AEX producer witness returns valid
  `e170_c=7` with a one-vertex `e3a0/f270` result, so `c=2` is no longer the
  live target truth for this lane. The corrected frame-setup gate now makes
  the current Mac trace reproduce descriptor `92,841,1,92,842,2`, predicate
  bytes, `e170 c=7`, and the first append; see
  `refs/conformance/olmsmoother2_case0012_unpremul_gate_20260716.md`.
  The next live boundary is downstream: the accepted descriptor selects AEX
  dispatcher key `0x14`, which calls `f130 -> e290` unconditionally after
  `f270`; local actual-AEX execution grows the polygon from one vertex to two.
  The accepted live Windows producer witness remains at one vertex because
  it ends before this continuation, so the missing fact is the live
  second-leaf input/return and post-leaf polygon state before `cce0`.
  The earlier corrected-origin probe is retained as historical diagnosis,
  not current descriptor truth.
- 2026-06-24 Ghidra MCP static recheck:
  - `FUN_18000e170` reads exactly `A(x,y-1)`, `R(x-1,y)`, and `A(x,y)` and
    returns the `2/4/1` bit sum. The current Mac `win_e170` matches this
    decompile for the `0012 (91,841)` witness.
  - `FUN_18000f270` only suppresses when `e170` returns `4`; otherwise it calls
    `FUN_18000e3a0` with `scale_m = extra_n * DAT_180022dd8 + 0.5` and the
    supplied scale parameter. The current Mac `win_leaf_f270` matches this
    shape.
  - `FUN_18000fef0` dispatches key `50` to `FUN_18000f270(..., 1.0)` and then
    returns, matching the local `cardinal6 key=50 -> f270` trace.
  - `FUN_180010760` still has the expected `d3b0` then `da50` then
    `FUN_18000fef0` shape. Ghidra's stack-variable rendering is ambiguous for
    the packed six-int descriptor, so keep the earlier full-cardinal reference
    as the descriptor truth table.
  Interpretation: do not promote a Mac-side `f270` or `e170` change from the
  current evidence. The remaining `0012` proof still needs either exact Windows
  live state for this witness or a lower-level descriptor/scan asm audit that
  contradicts the current full-cardinal mapping.
- 2026-06-24 Mac-side decision matrix:
  `refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.md`
  consolidates the latest current-AEX residual audit, curve-index sweep, and
  `f270` suppression probe. It classifies global `bb10/curve_idx` tuning as
  `rejected-inert` because overrides `0..8` all report identical metrics
  (`mean_sum=0.058945071373`, `max=113`), and global `f270` suppression as
  `rejected-worse` because it worsens the nine-case mean sum to
  `0.083016854745` and max to `169`. The two active residual witnesses are now
  explicitly tracked as opposite shapes: `0004 (1903,519)` needs a
  transparent-center neighbor/polygon proof, while `0012 (91,841)` needs exact
  `d3b0/da50/e170/f270/e3a0` state or equivalent asm proof.
- 2026-06-24 witness contract:
  `refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.md`
  parses the local trace logs into a compact contract for the next narrow
  proof. It keeps the Smooth Range threshold promotion, `e170` bit mapping,
  `f270` suppress-only-`c==4` shape, `fef0 key=50 -> f270(...,1.0)`, and the
  final 8bpc writer ruling. It also records why broad toggles stay rejected:
  `curve_idx` is inert and global `f270` suppression is worse. Active local
  paths:
  - `0004 (1903,519)`: `idx=208`, transparent center, polygon count `0`,
    passthrough `[1,1,1,0]`, but Windows writes `[103,103,103,113]`. The next
    proof is whether Windows also has zero vertices or whether a helper appends
    neighbor-derived samples before cce0.
  - `0012 (91,841)`: local predecessor path is `idx=105`,
    `cardinal6 desc=(91,841,1,91,843,5)`, `key=50`, `e170 c=2`,
    `f270 -> e3a0`, appending source `(91,840)` with weight `0.35632184`,
    then `cce0_after_b120=[0.99106723,0.99106723,0.99106723,0.35492450]`,
    while Windows is transparent. The accepted 2026-07-16 live witness now
    preserves valid call order `f270 -> e170 -> e3a0`, live `e170_c=7`, and
    one-vertex raw words
    `3e3ce706,3e3ce706,3e3ce706,3f2eaeaf` / `3e91a7b9`. The corrected rerun
    proves live `RDX p2[0..5]=92,841,1,92,842,2` with sample `92,841` and
    predicate bytes `center_b0=255`, `prev_b0=255`, `left_b1=255`, matching
    the Windows `c=7` return. The next proof is therefore the first upstream
    descriptor/dispatch divergence versus the current Mac local descriptor
    `91,841,1,91,843,5`.
- 2026-06-24 witness neighborhood report:
  `refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.md`
  records the 5x5 Windows-reference-vs-Mac-candidate neighborhood around the
  two active max-diff witnesses. This is a narrowing report, not an
  implementation tuner.
  - `0004 (1903,519)` is now classified as
    `windows-adds-semitransparent-output-where-local-passthrough-is-transparent`:
    center Windows `[103,103,103,113]`, Mac `[0,0,0,0]`, with 13 nonzero
    cells in the 5x5 window. The useful next trace is only whether Windows
    `c280` emits a polygon sample for this transparent-center cell, or whether
    `cce0` receives a nonzero fallback before passthrough.
  - `0012 (91,841)` is the opposite shape,
    `local-adds-semitransparent-output-where-windows-stays-transparent`:
    center Windows `[0,0,0,0]`, Mac `[90,90,90,91]`, with 4 nonzero cells in
    the 5x5 window. The useful next trace is only whether Windows suppresses
    the local `cardinal6/f270/e3a0` append, changes class bits, or zeroes the
    sample before `cce0`.
  This report makes another broad Smoother2 PNG request low-value. If Windows
  tracing resumes, ask for center-pixel `c280/cce0` state and the listed
  strongest neighboring deltas, not a full-image sweep.
- 2026-06-25 proof plan:
  `refs/reports/olmsmoother2_current_aex_proof_plan_20260625/proof_plan.md`
  turns the contract/neighborhood pair into an ordered proof checklist. The
  decision is `runtime-or-asm-first-divergence-required`: keep the Smooth Range
  threshold fix, and require a writer-anchored runtime trace or equivalent asm
  proof before changing implementation again. For `0004 (1903,519)`, prove
  final writer bytes, `cce0` return, and `c280` polygon/append state through
  static dispatch `0xd0 -> FUN_180013140`; also check whether the missing
  center value correlates with the strongest neighbors. For `0012 (91,841)`,
  prove final transparent writer output, cardinal6 descriptor/key, the
  `d3b0/da50/e170/f270/e3a0` emit chain, and whether `cce0/b120` zeroes a
  same-sample append through static dispatch
  `0x69 -> FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70`. Stop lines: do
  not add a global transparent-center fallback, and do not globally suppress
  `f270`.
- No-key `case_0001` residual is dominated by pixels where candidate smoothed
  but reference looks like input. This points to class-plane / dispatch firing
  too often, not final PNG premultiply alone.
- Diagnostics that skip cardinal branches are not valid promotions because the
  Windows binary calls those branches.
- 2026-06-19 diagnostic run:
  `refs/reports/olmsmoother2_forecast_20260619_021900/`.
  The no-key grid still has 3 exact zero-smoothness cases and 9 residual
  cases with `max=4/8/9`. The hottest classifier indices are `0xff`, `0x1f`,
  `0xf8`, `0x18`, `0x00`, `0xd6`, `0x6b`, and `0x42`.
- In the same run, `idx=0x18` leaf histograms are concentrated at:
  - cardinal 12: keys `0x29`, `0x55`, plus tiny counts at `0x2a`, `0x01`,
    `0x28`.
  - cardinal 3: keys `0x21`, `0x4d`, plus tiny counts at `0x14`, `0x1e`,
    `0x13`, `0x2b`.
- Negative probes saved beside that diagnostic run show that suppressing all
  `idx=0x18`, or suppressing either of its cardinal sides, worsens the grid.
  Therefore `idx=0x18` is a hot fidelity target, not a branch to delete.
- 2026-06-19 follow-up with `--trace-pixel` found that the current max-diff
  pixels in `sm2_no_key_s100_r3` are mostly `idx=0x10` and `idx=0x08`.
  These pixels emit two duplicate samples:
  - `idx=0x10`: weights `0.4` and `0.2`.
  - `idx=0x08`: weights `0.32` and `0.2`.
  Candidate pixels are weaker than the Windows reference. However, globally
  changing `W_IN_W` from `0.2` to `0.4` worsens the grid and does not move
  those sampled pixels, so the hot `0.2` is not the global corner-helper
  constant. Suppressing `idx=0x08` or `idx=0x10` also worsens the grid.
- Static recheck of those hot paths confirms the top-level dispatch:
  `idx=0x08/0x10` both call `FUN_180010820` and then `FUN_1800105f0`.
  The observed `cardinal3` keys (`0x14` / `0x1e`) and `cardinal12` key
  (`0x29`) map to the same leaf sequences in Mac as in the Windows decomp.
  `FUN_1800104d0`, `FUN_18000c0d0`, `FUN_18000ab00`, `FUN_18000b120`, and
  `FUN_1800036e0` also match structurally.
- 2026-06-19 Ghidra follow-up rechecked the hot span leaves
  `FUN_18000ec40` and `FUN_18000e640`. Their weights are built from scanned
  run endpoints using `(span + 1) * (extra * 0.2 + 0.5) / total`, then emitted
  through `FUN_18000e430` / `FUN_18000e320` and `FUN_180013630`. The Mac
  formulas still match at the decomp level, so the next trace request now asks
  for the scan helper returns as well as append/writeback values.
- 2026-06-19 Ghidra MCP recheck of `FUN_18000d520`, `FUN_18000dbd0`,
  `FUN_18000d230`, and `FUN_18000d800`: the call sites set `RCX`, `RDX`, `R8`,
  `R9`, and `[RSP+0x20]` immediately before `FUN_180010550`. The classifier
  first uses only `CL`, `DL`, and `R8B` to choose the jump target:
  `index = p1 + (p3 + p2 * 2) * 2`, table base `DAT_1800105d0`. Existing
  disasm notes resolve `idx=0..6` as fixed classes, while `idx=7` jumps to a
  variable target that reads the extra context (`R9B` and the stack argument)
  to return classes `6..9`. Therefore the live model is "3-input index,
  optional 2-input refinement for idx=7", not a plain 3-input table.
- 2026-06-19 second Ghidra MCP assembly check pinned the concrete scanner
  argument mapping. This matters because the decompiler often presents
  `FUN_180010550` as 3-argument, but the call ABI clearly carries two extra
  context bits:
  - `FUN_18000d520` at `0x18000d640..0x18000d64d`: `CL=R@(x-1,y)`,
    `DL=A@(x,y-1)`, `R8B=A@(x,y)`, `R9B=G@(x,y)`,
    `[RSP+0x20]=B@(x-1,y)`.
  - `FUN_18000d230` at `0x18000d367..0x18000d377`: `CL=R@(x-1,y+1)`,
    `DL=A@(x,y)`, `R8B=A@(x,y+1)`, `R9B=G@(x,y+1)`,
    `[RSP+0x20]=B@(x-1,y+1)`.
  - `FUN_18000dbd0` at `0x18000ddaa..0x18000ddc0`: `CL=R@(x,y)`,
    `DL=A@(x,y)`, `R8B=A@(x,y-1)`, `R9B=G@(x,y)`,
    `[RSP+0x20]=B@(x-1,y)`.
  - `FUN_18000d800` at `0x18000d9e7..0x18000d9fd`: `CL=R@(x,y+1)`,
    `DL=A@(x,y+1)`, `R8B=A@(x,y)`, `R9B=G@(x,y+1)`,
    `[RSP+0x20]=B@(x-1,y+1)`.
  The current Mac port's p4/p5-aware classifier model matches this assembly
  shape; the remaining no-key residual should be traced at the scanner return
  and append stages rather than by removing the idx=7 refinement.
- 2026-06-19 rejection probe: forcing `win_FUN_180010550` back to the resolved
  fixed 3-input table worsened the no-key grid from the guarded `max=4/8/9`
  band to `max=14/24/41` with about `1.0%..2.5%` nonzero pixels. Keep the
  current scanner-sensitive idx=7 refinement until Windows runtime trace proves
  the exact scan helper return behavior and context bytes.
- A Mac-side baseline trace for witness pixel `(211,139)` was saved at
  `refs/reports/olmsmoother2_trace_baseline_20260619_024716/mac_trace_211_139.log`.
  A fuller four-pixel baseline was later saved at
  `refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/`.
  The no-key binary-grounding request package is
  `refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_no_key_grid_scan_append_p1p5_with_mac_baseline_20260619_030034.zip`.
- This no-key trace is now optional/historical because the AE-host no-key grid
  is exact. If it returns, use it to tighten the binary-grounded IR, not as the
  next active Smoother blocker.

2026-06-19 Ghidra MCP recheck:

- `FUN_1800104d0` appends exactly one integer-grid source sample, copying two
  qwords of float RGBA from the source world and storing the caller-supplied
  float weight at `vertex + 0x10`.
- `FUN_18000c280` still dispatches `idx=0x08/0x10` through
  `FUN_180010820` and `FUN_1800105f0`, then copies the local 12-vertex polygon
  to the caller.
- `FUN_1800036e0` composites through `FUN_18000cce0`, optionally applies
  sRGB/gamma conversion, optionally premultiplies by alpha, and writes float
  RGBA in output order `{A,R,G,B}`.
- The legacy key/gamma trace request now takes priority over this no-key scan
  trace because the no-key AE-host path is exact while legacy key/gamma remains
  `0/7`.

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| no-key grid | 8bpc | AE exact for packaged grid | 12/12 exact in 2026-06-19 and 2026-06-20 AE pixel returns | Optional runtime trace for binary-grounding; do not PNG-tune |
| key/gamma paths | 8bpc | guarded / writer-grounded residual | Full current-AEX recapture imported. With AE-saved premultiplied before frames, `legacy_case_0002` and `0003` are exact. Smooth Range threshold promotion makes the `0004 (501,1055)` target cce0 value match the Windows final writer floats, and reduces the 11-case mean-sum from `1.3008` to `0.0589`. Remaining localized residuals include `0004 max=113 mean=0.0045` and `0012 max=91 mean=0.0151`; the `0012` max witness is now `(91,841)` and is isolated to `cardinal6 key=50 -> f270/e170/e3a0`. Decision matrix `refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.md` rejects `bb10/curve_idx` as inert and global `f270` suppression as worse. | Keep the Smooth Range threshold fix. Next proof should be binary/runtime evidence for `d3b0/da50/e170/f270/e3a0` on `(91,841)` and a polygon/no-polygon proof for `0004 (1903,519)`; broad alpha/index/curve-index/f270-suppression probes were worse or inert |
| standalone v1 | 8bpc | AE exact for packaged v1 slices | 3/3 exact in corrected 960x540 2026-06-20 AE pixel rerun | Decide whether v1 stays independent or maps to v2 compatibility |
| no-key case-07 | 32bpc | raw FLOAT32 control must be exact before effect attribution | Windows/Mac no-effect differs at 6,106,918 words; effect-on comparison is non-attributable; no AE-exact claim | Align and attest the no-effect host/export path; keep 8bpc frozen |

## Open Questions

- Remaining scanner/leaf behavior around `idx=0x18`.
- Whether class-plane byte value `1` vs `0xff` matters in any downstream path.
- Exact AE-host Mac output against current Windows Software refs for legacy
  key/gamma after the full current-AEX recapture returns.
- 16bpc smoothing/writeback behavior, and the 32bpc cross-host no-effect
  source/export interpretation that currently fails before algorithm
  attribution.
