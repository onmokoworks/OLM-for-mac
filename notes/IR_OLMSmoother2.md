# Binary-Grounded IR: OLMSmoother2

## Feature

- Plug-in: OLM Smoother v2
- Feature/path: 8bpc cel-line smoother, color-key, gamma/color-space, v1/v2
  compatibility
- Bit depth: 8bpc documented here; 16/32bpc still need references
- Current reference target: current Windows AEX Software recaptures.
- Retired reference set: `refs/win_references/20260605_extra/OLMSmoother2`
  is reference-only for legacy cases because `case_0001` does not match the
  current AEX/runtime-traced CPU behavior.
- Current status: no-key grid has packaged 8bpc `AE exact` evidence from the
  2026-06-19/2026-06-20 AE pixel returns. Standalone OLMSmoother v1
  `case_0001..0003` is also 8bpc `AE exact` after the corrected 960x540 rerun.
  Smoother2 legacy key/gamma slices remain guarded residuals, so Smoother2 as
  a whole is not complete.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Smoother is specialized in smoothing cel animation drawings. | Official v1/v2 manuals under `refs/upstream_official/20260619_olm_official_zips/pdf_text/`. | manual-backed |
| v2 adds color space conversion, Smoothness, Extra Smooth, Gamma Correction, 32-bit support, and improved diagonal smoothing. | Official v2 manual. | manual-backed |
| `Smoother Version` v1/v2 mainly affects Gamma Correction / linearization. | Official v2 manual says v1 does not linearize prior to processing. | manual-backed |
| Parameter setter initializes mode/key/palette/gamma fields and routes invert-key through the active palette. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180004e10`. | binary-grounded |
| Frame setup order is setup, optional unpremultiply, active-palette filter, non-invert scalar-key filter, then optional sRGB decode. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180002e90`. | binary-grounded |
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

## Parameters

| UI / manifest name | Internal meaning | Evidence |
| --- | --- | --- |
| `Use Color Key` / `Enable Color Key` | Enables key filtering before smoothing. | asm setter |
| `Invert Color Key` | Routes key color through active-palette keep filter when enabled; non-invert uses scalar-key remove filter. | asm setter/frame setup |
| `Color Key` | Scalar key color or one-entry active palette, depending on invert. | asm setter |
| `Smoothness` | Strength of smoother interpolation. | manual + port |
| `Extra Smooth` | Additional smoothing strength/path. | manual + port |
| `Smooth Range` | No-key class-plane threshold; nearby colors can be treated as same-color. | asm/grid |
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
| key/gamma paths | 8bpc | current-reference pending | Old legacy PNGs are retired as correctness targets; runtime-traced Windows CPU AEX and Mac CLI agree for high-diff witness `(712,406)` | Import `smoother2_legacy_full_current_aex_recapture_20260621`, then classify exact/residual against current-AEX Software output |
| standalone v1 | 8bpc | AE exact for packaged v1 slices | 3/3 exact in corrected 960x540 2026-06-20 AE pixel rerun | Decide whether v1 stays independent or maps to v2 compatibility |

## Open Questions

- Remaining scanner/leaf behavior around `idx=0x18`.
- Whether class-plane byte value `1` vs `0xff` matters in any downstream path.
- Exact AE-host Mac output against current Windows Software refs for legacy
  key/gamma after the full current-AEX recapture returns.
- 16bpc and 32bpc smoothing/writeback behavior.
