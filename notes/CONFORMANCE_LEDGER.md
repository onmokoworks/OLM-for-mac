# OLM Conformance Ledger

- 2026-07-17 `OLMRadialBlur natural B150 span matrix` (latest override): no
  correctness status is promoted. The natural reader-owned caller reaches
  actual `FUN_18000B150` for Outer Edge Fade spans 1, 2, and 3 and Inner Edge
  Fade span 1. The AEX-generated Gaussian tables and all 196 RGBA/scalar work
  cells match an independent per-operation float32 oracle by raw words in
  every fixture. This closes the B150 table/population operation for these
  naturally reachable nonzero spans; do not reopen it from broad PNG
  residuals. A fail-closed full-size pre-collapse attempt proves that the
  retained setup checkpoint is only 32x32 and cannot resume the 250M
  case_0009 path, so no four-cell full-size state was fabricated. Windows
  equivalence and AE exact remain open. Next action requires either a new
  resumable full-size checkpoint at `0x180005c9f` or a same-run Windows witness;
  further bounded B150 tuning is forbidden. Evidence:
  `refs/conformance/olmradialblur_natural_b150_replay_oracle_20260717.json`
  and `refs/conformance/olmradialblur_natural_fullsize_precollapse_witness_20260717.json`.

- 2026-07-17 `OLMSmoother2 natural classifier matrix and polygon gate`
  (latest override): no correctness status is promoted. The actual AEX path
  `ada0 -> ac00 -> ae10` matches an independent class-plane oracle byte for
  byte across 30 fixtures spanning threshold raw values 0/1/10/100/200,
  hysteresis 0/1, and multipliers 0/1/2, with 256 classifier calls per case.
  All 30 generated planes execute actual c280/cce0; the 18 default-dispatch
  `0xff` cases match the portable empty-polygon/center-sample oracle exactly.
  All unique classifier families in the 30-case matrix are now independently
  grounded. Index `0x00` uses:
  helper chain `0x134c0 -> 0x13570 -> 0x12ce0 -> 0x12c20`, append owner
  `FUN_1800104d0`, vertex stride `0x14`, weight at `+0x10`, and the 12-vertex
  cap; all eight cases match count/order/RGBA/raw weights. Index `0x42` grounds
  `FUN_180013630` with a bit-precise SSE float32 weight oracle and both cases
  match. Index `0x5a` grounds the `ec40 -> e0e0 -> dbd0 -> d230 -> e430`
  empty path and both cases match; all 18 `0xff` cases also match the empty
  path. This closes the local classifier/c280 family matrix, not the retained
  Windows case0012 host state or AE exact. Evidence:
  `refs/conformance/olmsmoother2_case0012_ada0_matrix_oracle_20260717.json`
  and `refs/conformance/olmsmoother2_case0012_c280_5a_oracle_20260717.json`.

- 2026-07-17 `OLMDirectionalBlur writer buffer provenance` (latest
  override): no correctness status is promoted. The natural angle-0 caller
  proves that output `PF Iterate8` refcon field `params+0x8090` owns the
  writer-entry float RGBA. Static and dynamic write tracing identify
  `FUN_180004A20` as the nearest producer: its final-path store at
  `0x18000562d` writes `R15` to that field immediately before constructing the
  output callback and entering `FUN_180006700`. `R15` is a HandleSuite-backed
  26x26x4 float plane (2704 bytes); target `(0,0)` is cell 135 at byte offset
  2160. Actual callback `0x180006980` now runs with grounded ABI and produces
  source RGBA `[1,0,0,1]` in `params+0x8078`; the separate writer plane at
  `params+0x8090` remains zero before downstream processing. A
  continuation-safe attempt stops at `pre-render-return` before any downstream
  write, so the exact render-branch/PF Iterate8 state remains the next
  boundary. Do not change the proven `0x180006b30` writer. Evidence:
  `refs/conformance/olmdirectionalblur_natural_writer_owner_20260717.json`
  and `refs/conformance/olmdirectionalblur_iterate8_continuation_transform_20260717.json`.

- 2026-07-17 `OLMDistanceGradation PF16 bounded full-chain exact` (latest
  override): no AE correctness status is promoted. The earlier
  `fieldgen_or_staging` result was caused by a harness contract error:
  WIDTH/HEIGHT were written into the PF_InData downsample numerators, staging
  the AEX side as 64x25, and an all-opaque degenerate field was manually forced
  through the non-degenerate compose branch. With 1/1 ratios and an actual
  transparent/opaque boundary, the hash-pinned AEX and production Mac source
  match all 40 field words. Decomp of `FUN_181170480` proves PF16 truncating
  float-to-int stores; removing the Mac-only `+0.5` closes the complete
  40-pixel output at byte_diff=0. Universal Debug build and all focused
  harnesses pass. The new binary is installed at the sole MediaCore path with
  SHA-256 `af328fae...f64232fd`. AE PID 7653 is running but does not currently
  map OLMDistanceGradation, so no stale loaded DG module is present. The proof
  render still requires a disposable/fresh AE project because the safe runner
  resets renderer, color state, and project depth. Next allowed action: rerun
  canonical 16bpc cases 0012/0014 with loaded-module SHA binding after the
  current AE project can be replaced safely. Evidence:
  `refs/conformance/olmdistancegradation_pf16_field_staging_exact_20260717.json`.

- 2026-07-17 `OLMBlur 32bpc source/AEX adapter` (latest override): no AE
  correctness status is promoted. Production `BlurRender(..., 32, ...)`
  matches 12/12 actual-AEX float fixtures across Legacy and Non-Legacy paths,
  including bias directions, radius/repeat boundaries, mixed alpha, exact
  alpha preservation, and padded rowbytes. This is Mac production-source
  versus bounded actual-AEX evidence, not Windows AE/EXR or Mac AE exactness.
  The retained Windows EXR set is not sufficient to bind a cross-host result
  to the AEX actually loaded by AE. Next allowed action: obtain one same-run
  Windows record containing the loaded AEX path/hash, AfterFX PID/module base,
  parameter readbacks, and control/effect EXR hashes, then run the equivalent
  loaded-module-bound Mac AE comparison. Evidence:
  `refs/conformance/olmblur_32bpc_source_aex_adapter_20260717.md` and
  `refs/conformance/olmblur_32bpc_missing_windows_loaded_aex_artifact_20260717.md`.

- 2026-07-17 `OLMRadialBlur natural B150 checkpoint` (latest override): no
  correctness status is promoted. A bounded natural case_0009 caller reaches
  B150 once after 85,967 instructions without Python prefill or a worker
  detour. Four natural prefill rows populate all 196 RGBA and source-alpha
  cells, and caller/work-object pointers agree. `FUN_180008690` owns the two
  spans through host integer-reader indices 5/9 (Outer/Inner Edge Fade); all
  13 retained references set both to zero. Changing only Outer Edge Fade to 1
  naturally propagates through `param_ctx+0x6c`, `work+0x4200`, and
  `FUN_18000B680`, yielding B150 spans `1/0` and nonzero inline-table counts
  `1/0` without direct harness writes. This closes zero-state ownership and a
  minimal natural nonzero table fixture only; larger spans, B150 output,
  Windows equivalence, and AE exact remain open. Next Mac-only action: execute
  the populated B150 output path and compare it with an independent float32
  oracle. Evidence:
  `refs/conformance/olmradialblur_natural_b150_checkpoint_20260717.json`.

- 2026-07-17 `OLMSmoother2 case0012 class-plane intake` (latest override):
  no correctness status is promoted. Fail-closed intake proves the three
  retained return ZIPs contain only center/previous/left class bytes and no
  backing neighborhood dump. The old 5x5 capture conflicts with two corrected
  live coordinates. Two completions preserve every retained fact and the same
  e170 result yet produce actual-AEX c280 polygon counts 0 and 3, proving the
  missing neighborhood is not uniquely reconstructible. A Mac-local natural
  caller now executes `FUN_18000ada0 -> VCOMP140!_vcomp_fork -> FUN_18000ac00
  -> FUN_18000ae10`, makes 256 classifier calls, regenerates the supported 3x4
  class window exactly, and feeds it into actual c280 for polygon count 1.
  Do not splice old captures or tune c280. The remaining fail-closed boundary
  is the `FUN_18000ada0` entry state: source/class planes, rectangle, strides,
  and config bytes `+0x1c/+0x70/+0x74`. Evidence:
  `refs/conformance/olmsmoother2_case0012_classplane_return_replay_20260717.json`
  and
  `refs/conformance/olmsmoother2_case0012_classplane_natural_caller_20260717.json`.

- 2026-07-17 `OLMKiraKira Handle Suite natural boundary` (latest
  override): no correctness status is promoted. The common-owner run now
  completes 25 grounded checkouts/checkins plus five exact
  `PF ColorParamSuite` v1 acquisitions, conversions, and releases while
  preserving both PF32 world canaries. `PF Handle Suite` v2 acquisition,
  16-byte allocation, and lock now also execute with recorded pointers. The
  minimal `GS:[0x58]` TLS epoch contract and bounded
  aligned allocation/free plus one-key FLS set/get lifecycle are crossed.
  Observed aligned requests 16/48/100 bytes are valid and guarded; the former
  OOM was only a null allocator callback. PF depth `0x20` selects PF32, Blur
  Mode disk ID 9/index 8 reads back 2, and the Mode2 branch enters
  `FUN_18114f4a0` then `FUN_181150790`. The latter enters the dispatch loop at
  `FUN_181294950`; the bounded run exhausts its instruction budget at
  `0x181294ad5` without hitting an unimplemented import, returning, or reaching
  the typed writer. Next Mac-only action is a resumable/checkpointed audit of
  that dispatch loop, not a parameter remap, exception suppression, or direct
  writer invocation. Evidence:
  `refs/conformance/olmkirakira_mode2_common_owner_20260717.json`.

- 2026-07-17 `OLMRadialBlur reconstructed B150 population` (latest override):
  no correctness status is promoted. A logical width-1104, rows-1047..1048
  reconstructed fixture executes actual `FUN_18000B150` once and changes all
  six seeded target/control output cells. An independent zero-span spec oracle,
  with explicit per-operation float32 rounding, matches every RGBA and scalar
  raw word. This closes only bounded zero-span B150 population math; natural
  prefill, nonzero Gaussian spans/tables, Windows equivalence, and `AE exact`
  remain open. Evidence:
  `refs/conformance/olmradialblur_reconstructed_b150_oracle_20260717.json`.

- 2026-07-17 `OLMKiraKira parameter-surface contract` (latest override): no
  correctness status is promoted. Manifest-backed comparison proves that five
  Windows custom Color Ramp rows are absent from the Mac schema and that the
  top-level parameter order differs. The checked-in validator now requires
  match-name identity, rejects index-only KiraKira rows, fails closed as
  `unmappable` for the missing ramp rows, and accepts the 25 mapped plugin rows
  plus two shared built-ins. This protects reference application but does not
  implement the missing Mac ramp UI. Evidence:
  `refs/conformance/olmkirakira_parameter_surface_contract_20260717.json`.

- 2026-07-17 `OLMColorKey PF32 Mac SmartRender adapter` (latest override): no
  correctness status is promoted. A source-included arm64 harness executes the
  actual `EffectMain` SmartRender dispatch for a core case and an Edge Blur
  case, verifies parameter checkout order and callback lifecycle, preserves
  padded rowbytes, exercises the current zero-alpha/premultiply behavior, and
  performs no `PF_Cmd_RENDER` fallback. This is a Mac source-adapter contract
  proof, not a Windows comparison or 32bpc `AE exact`. Evidence:
  `tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py`.

- 2026-07-17 `OLMKiraKira Mode2 typed-writer lineage gate` (latest override):
  no correctness status is promoted. The actual Mode2 target mutates its float
  RGBA output and the actual PF32 leaf records matching XMM inputs and ARGB
  destination mutation in one Unicorn instance, but the value transfer between
  them is Python-mediated. Static and runtime checks confirm the Mode2 target
  returns without a typed-writer call edge, so synthetic lineage is rejected.
  A natural run now enters common owner `FUN_18114c8f0`, executes both PF32
  world callbacks with preserved canaries, grounds the 25-entry disk-ID table,
  and observes six parameter checkouts/five checkins. It still exits `2` before
  Mode2 at the next exact host boundary: `outer_context+0x180` must provide an
  SPBasicSuite that acquires `PF ColorParamSuite1`. The next Mac-only action is
  that suite contract, not another direct leaf invocation. Evidence:
  `refs/conformance/olmkirakira_mode2_common_owner_20260717.json`.

- 2026-07-17 `OLMDirectionalBlur Mac SmartRender adapter` (latest override):
  no correctness status is promoted. A source-included arm64 adapter executes
  the production PF16 and PF32 SmartRender dispatch with padded rowbytes. Both
  paths preserve zero-alpha RGB and input/output padding, invoke each expected
  host callback once, and perform no `PF_Cmd_RENDER` fallback. This closes a
  Mac host-adapter boundary only; it is not Windows equivalence or `AE exact`.
  Evidence:
  `tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py`.

- 2026-07-17 `OLMBlur fixed live 16bpc worker` (latest override): the declared
  normalized 16bpc seven-case slice is now `7/7 AE exact`. Mac AE `26.3x87`
  loaded OLMBlur binary SHA-256 `71df7efc...f4f0d72` in PID `7653` and rendered
  all seven cases under Software, 16bpc, working space `None`, linear blending
  off; every case verified at `max_diff=0`. The old candidate missed the live
  adapter path: the host calls `core/olmblur_worker16_nonlegacy.cpp`, which had
  retained float `exp`. Commit `e053c3dc` applies the binary-grounded
  float-exponent/double-`exp` sequence to the actual worker. This supersedes
  all `5/7` and "candidate not loaded" statements for the declared 16bpc cell,
  but does not promote 32bpc. Evidence:
  `refs/conformance/olmblur_16bpc_fixed_worker_mac_ae_exact_20260717.md`.

- 2026-07-17 `OLMToonDilate Mac SmartRender adapter` (latest override): no
  correctness status is promoted. A source-included arm64 adapter now executes
  the production SmartPreRender/SmartRender dispatch for PF16 and PF32 at
  radius zero. Both paths preserve visible pixels, zero-alpha RGB, input and
  output padding, perform the expected checkout/check-in calls once, and do
  not fall back to `PF_Cmd_RENDER`. This is a Mac host-adapter contract proof,
  not Windows equivalence or `AE exact`. Evidence:
  `tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py`.

- 2026-07-17 `OLMSmoother2 case_0012 post-division c280 boundary` (latest
  override): no correctness status is promoted. Actual AEX c280/cce0 execution
  and the portable adapter agree under the retained center/previous/left class
  bytes, but both produce an empty polygon because the remaining live neighbor
  class bytes were not captured. The self-contained smoke requires the probe
  to exit `2` with
  `BLOCKED_CASE0012_POST_DIVISION_C280_NEIGHBOR_SEAM`; the next useful witness
  is the missing class-plane neighborhood, not another global fallback change.
  Evidence:
  `tools/emulation/test_olmsmoother2_case0012_c280_post_division_boundary_smoke_20260717.py`.

- 2026-07-17 `DistanceGradation PF16 wrapper/iterate boundary` (latest
  override): no correctness status is promoted. The actual AEX wrapper
  `FUN_181170ff0` returns after reaching fieldgen twice and dispatching the
  live `FUN_181170480` pointer through a continuation-safe host PF Iterate16
  callback for all `8 * 5 = 40` pixels. Every nested compose returns to its
  private sentinel, the outer context is restored, and the observable 12-byte
  row padding canary is preserved. A production-source oracle with matched
  compose parameters and source world then localizes the first divergence
  before compose: the actual wrapper field is `X=0` at all 40 pixels, while
  production `RenderBits<PF_Pixel16>` supplies `X=1` (`32768`) at all 40.
  Compose semantics match and both paddings remain intact. Therefore the live
  Mac-only lane is now `fieldgen_or_staging`; do not tune compose/writeback.
  This is still not Windows equivalence or `AE exact`.
  Evidence:
  `refs/conformance/olmdistancegradation_pf16_source_oracle_20260717.json`.

- 2026-07-17 `RadialBlur reconstructed Zoom actual collapse` (latest
  override): no correctness status is promoted. A hash-pinned Mac Unicorn
  run now enters the real `FUN_1800056F0+0x5c9f` collapse block and reaches
  its exact post-loop boundary at `0x180005d96`. On the reconstructed `32x1`
  case_0009 row, actual `+0xe` writes match an independent float32 oracle at
  x=`7,8,24`, and the real `FUN_180009D80` output matches the collapsed x=7
  cell. The x=7 and x=8 alpha remain exactly `1.0`; therefore this bounded
  fixture excludes the collapse and sampler as the source of the x=7
  sub-one Windows result and keeps the next live uncertainty upstream in
  worker/population state. This is reconstructed direct-entry evidence, not
  a natural full-size caller, Windows equivalence, production patch, or
  `AE exact`. Evidence:
  `refs/conformance/olmradialblur_reconstructed_zoom_collapse_20260717.md`.

- 2026-07-17 `DistanceGradation embedded OpenCV GATE C` (latest override): no
  correctness status is promoted. An opt-in single-thread TLS/FLS/aligned-
  allocation scaffold now lets the hash-pinned AEX execute its embedded
  `cvThreshold`, `cvDistTransform`, and complete `FUN_181174760` field-generator
  paths without OpenCV detours. Threshold is bit-exact with the independent
  OpenCV 4.5.5 sidecar. Ten distance geometries expose six exact relations,
  two pinned x86-SIMD one-ULP families, and the no-source `0x5f7fffff` sentinel.
  Three complete field-generator fixtures are byte-exact against the validated
  detour pipeline. This closes the former `RIP=0x181187e41` static-init blocker
  for these bounded paths, but optional Windows/CRT imports remain explicit
  zero-return stubs, so the result is not a full Windows runtime or `AE exact`.
  Next expand the embedded field-generator matrix around final-pixel-sensitive
  thresholds before changing the production EDT. Evidence:
  `refs/conformance/olmdistancegradation_embedded_opencv_gate_c_20260717.md`.

- 2026-07-16 `classic PF_Cmd_RENDER bit-depth dispatch` (latest override):
  no correctness status is promoted. All eight classic render entry points now
  query `PF_WorldSuite2::PF_GetPixelFormat` and map ARGB32/ARGB64/ARGB128 to
  8/16/32 bpc, failing closed on unknown formats. This removes the prior
  `PF_WORLD_IS_DEEP` ambiguity that treated every deep world as 16bpc. The four
  discoverable source-contract tests and all eight Debug builds pass;
  SmartRender behavior is unchanged. This is source/build evidence only, with
  no AE host render or AE-exact claim. Evidence:
  `refs/conformance/olm_classic_render_bitdepth_dispatch_20260716.md`.

- 2026-07-16 `OLMBlur case_0004 double-exp production candidate` (latest
  override): no correctness status is promoted. Keeping the current float32
  exponent input and all powf/pow/radius/sigma/denom order, replacing only
  `expf(x_f32)` with `(float)exp((double)x_f32)` matches all `177/177` declared
  callback-backed coefficient words. The portable cones remain exact halves
  and predict Windows reference words `22038/26374`. The production Non-Legacy
  coefficient line now uses this candidate; the source-contract gate, eight
  actual-AEX helper fixtures, staged/sensitivity gates, and Universal
  arm64/x86_64 Debug build pass. AE 2026 is currently open with the previously
  loaded plug-in, so no install/restart/render was attempted. Keep correctness
  at `5/7 AE exact` until a fresh loaded-module-bound 16bpc revalidation proves
  `case_0004`; `case_0003` is unaffected and remains open. Evidence:
  `refs/conformance/olmblur_case0004_exp_double_candidate_20260716.md`.

- 2026-07-16 `OLMBlur case_0004 coefficient sensitivity` (latest override):
  no correctness status is promoted. With identical staged RGB/flags, radii,
  pass order, crop geometry, and portable helper, the host-callback and current
  Mac coefficient sets differ only at iteration 1 indices `57` and `70`, each
  by one float32 ULP. That set change moves both retained pre-store values from
  `22037.498046875/26373.498046875` to exact halves `22037.5/26373.5`, and the
  grounded standard-writer prediction from the two observed Mac red words
  `22037/26373` to the Windows reference words `22038/26374`. Neither
  coefficient set is independently Windows CRT truth, so this is a complete
  residual explanation and implementation discriminator, not AE exact. Next
  test a double-`exp` to float candidate against every captured coefficient,
  then apply it only if the full coefficient gate and existing regressions
  pass. Evidence:
  `refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.md`.

- 2026-07-16 `OLMBlur case_0004 caller schedule and two-layer helper witness`
  (latest override): no correctness status is promoted. After adding the
  missing Windows-x64 `powf(float,float)` XMM callback, the hash-pinned actual
  caller reaches all `48` helper calls and independently records H/V-agreed
  radii `[125,36,10,2]`, dimensions, pass ranges, and coefficient bytes from
  declared host-backed math callbacks. Those coefficients are not Windows CRT
  truth.
  Eight one-output actual-AEX helper strips (four radii by two directions)
  match the portable C++ helper byte-for-byte. A portable-only composition of
  the two complete `347x347` dependency cones, driven exclusively by those
  callback-produced coefficients, ends at exact float32 values `22037.5` and
  `26373.5`; with the already-grounded standard writer these are the expected
  output words under that backend. This is not an actual-AEX full-chain,
  Windows CRT coefficient proof, or AE-exact result. The Mac production formula
  differs by one coefficient ULP at iteration 1/index 57 and index 70, while
  radii and all other iterations agree.
  Treat that as a libm-backend sensitivity candidate, not a production fix.
  Evidence:
  `refs/conformance/olmblur_case0004_staged_helper_replay_20260716.md`.

- 2026-07-16 `RadialBlur unprefilled full-size Zoom cap` (latest override): no
  correctness status is promoted. A hash-pinned natural full-size
  `FUN_1800056F0` run reaches the core but hits the `250,000,000` instruction
  cap at the emulator return sentinel before `FUN_18000B150` or
  `FUN_18000A9D0`; the required alpha discriminator therefore fails closed.
  Four isolated `FUN_180009D80` samples still match the portable float32 and
  trunc-u8 replay exactly. Do not rerun this unprefilled full-size path with the
  same cap. Further Mac-local work must checkpoint after setup or reconstruct
  the caller state at the worker; the existing prefilled same-run witness
  remains the semantic local baseline. Evidence:
  `refs/conformance/olmradialblur_zoom_caller_collapse_consistency_20260716.md`.

- 2026-07-16 `DistanceGradation raw-threshold caller correction` (latest
  override): no correctness status is promoted. All nine hash-pinned AEX
  callsites pass config `+0xb8/+0xbc` directly in `R9D` to `FUN_181174760`;
  staged dimensions are separate arguments. The Mac port now passes the raw
  UI threshold to the already-matching helper and retains downsample scale only
  for blur geometry. A focused regression proves helper output invariant under
  caller labels `ds_scale=1/0.5`, detects a reintroduced multiplied threshold,
  the 286-value core test passes, and the arm64 plug-in build succeeds. AE-host
  render validation is still required; this is not `AE exact`. Evidence:
  `refs/conformance/olmdistancegradation_raw_threshold_contract_20260716.md`.

- 2026-07-16 `Smoother2 case0012 second-leaf payload` (latest override): no
  correctness status is promoted. Starting from the accepted descriptor
  `92,841,1,92,842,2`, `e170 c=7`, and first polygon count `1`, hash-pinned
  actual-AEX execution and the portable implementation agree through
  `df30 -> f130 -> e290`. A distinctive nonzero source at `(92,843)` emits
  RGBA `(0.125,0.25,0.75,0.625)`, matching weight within `1e-6` and polygon
  count `1 -> 2`; the full dispatcher remains key `0x14` and total count `2`.
  This closes the checked-in AEX/portable second-leaf payload, not the live
  Windows post-leaf polygon or AE output. Evidence:
  `refs/conformance/olmsmoother2_case0012_second_leaf_20260716.md`.

- 2026-07-16 `DistanceGradation fieldgen actual-AEX differential` (latest
  override): no correctness status is promoted. A hash-pinned direct execution
  of `FUN_181174760` and the current portable core match all `187/187` float32
  samples for the bounded `param8=0`, raw-threshold `4`, `ds_scale=1` ramp.
  The strict `param8=1`, threshold-zero anchors are exactly `(0,1,1)`, and all
  detour, callback, import, and sample-count guards pass. At an explicit
  `ds_scale=0.5`, the direct AEX helper and current Mac caller contract differ
  (`55/187` float32 matches), which moves the unresolved ownership to caller
  threshold scaling and staged mask/resize integration rather than the EDT,
  threshold, or normalization helper itself. This is helper parity, not full
  AE field-generation parity or `AE exact`. Evidence:
  `refs/conformance/olmdistancegradation_fieldgen_actual_aex_differential_20260716.md`.

- 2026-07-16 `Mac 32bpc loaded-module gates` (latest override): no correctness
  status is promoted. ColorKey and ToonDilate validation runners now bind the
  claimed Mach-O path and SHA-256 to the single live After Effects process via
  exact-path `vmmap`, and reject a binary modified after AE startup. ColorKey's
  first nine-case attempt stopped fail-closed at an existing unsaved-project
  modal and produced no candidate evidence. ToonDilate's unavailable old
  `c05db8...c32b3` pin is superseded by an explicit current-candidate revision:
  installed and Debug-build Mach-O both hash to `d47a81...954de`, and the
  request records source/project hashes plus universal architectures. It has
  not yet been rendered. Evidence:
  `refs/conformance/mac_32bpc_loaded_module_gates_20260716.md`.

- 2026-07-16 `KiraKira Merge Mode plumbing` (latest override): no correctness
  status is promoted. The Mac UI already exposed Merge Mode, but normal and
  Smart Render both discarded its value. `OLMKiraKiraInfo`, `ReadRenderInfo`,
  and `CheckoutSmartInfo` now preserve it, with an `8/8` source-contract gate.
  `RenderTyped` remains unchanged because Mode 2's later host compose/writer
  binding is still unresolved. Evidence:
  `refs/conformance/olmkirakira_merge_mode_plumbing_20260716.md`.

- 2026-07-16 `DistanceGradation PF8 coordinate witness` (latest override): no
  correctness status is promoted. A Mac AE `26.3x87` Software run proved one
  PF8 field record and one PF8 shade record for each bounded live coordinate:
  `case_0001 (17,0)`, `case_0015 (780,495)`, and `case_0029 (987,496)`.
  Their field values are `0.0078125`, `0.037291009`, and `0.250339508`;
  stored ARGB is respectively `57,255,0,0`, `10,10,0,0`, and `64,28,0,238`.
  With current-source bundle SHA `f60fecc...d596`, two fresh runs reproduced
  the same output hashes and all three clamped ARGB tuples equaled immediate
  destination-world readback, closing the local PF8 assignment boundary.
  Earlier hashes from a stale installed bundle are superseded.
  These replace the prior zero-hit `(397,281)` probe as the local PF8
  field/compose/store witness lane. Evidence:
  `refs/conformance/olmdistancegradation_8bpc_coordinate_witness_runner_20260716.md`.

- 2026-07-16 `DistanceGradation PF8 compose/store actual-AEX differential`
  (latest override): no correctness status is promoted. A hash-pinned local
  execution of `FUN_181170870` injects the same PF8 field/source bytes used by
  the current Mac model at `(17,0)`, `(780,495)`, and `(987,496)`. Correct
  `1024x512`, rowbytes `4096`, nonzero fixture readback is gated before
  execution. All three points match through field/source reads, canonicalized
  pre-U8 floats, truncating conversion, and stored ARGB bytes. This closes the
  bounded compose/store interpretation for those injected values only; it does
  not compare `FUN_181174760` field generation or establish AE exactness.
  Evidence:
  `refs/conformance/olmdistancegradation_pf8_compose_store_differential_20260716.md`.

- 2026-07-16 `ColorKey Euclidean distance type 3 actual-AEX lane` (latest
  override): no correctness status is promoted. Hash-pinned
  `FUN_180007ec0` returns normally through the bounded PF Handle Suite shim,
  allocates the required `width*height*4` buffer exactly once, completes
  lock/unlock/dispose/release, and leaves no unresolved imports. Its four
  float32 output channels match an independent nearest-zero Euclidean model
  at `max_abs_error=0`. This closes the bounded type-3 distance primitive,
  not the full Replace+Edge orchestrator or AE-host output. Evidence:
  `refs/conformance/olmcolorkey_boundary_to_distance_type3_actual_aex_20260716.md`.

- 2026-07-16 `OLMBlur 16bpc case_0003/0004 bounded pre-store audit` (latest
  override): no correctness status is promoted. Hash-pinned actual-AEX staging
  matches retained-PNG-to-PF16 source conversion at all 20 Legacy
  `case_0003` residual coordinates and both Non-Legacy `case_0004` points.
  For `case_0004`, isolated actual-AEX writer micro-runs also store the current
  portable pre-store inputs exactly. The attempted dependency-cone worker run
  hit its one-billion-instruction cap before the writer, so the first unresolved
  boundary remains worker/helper pre-store; the source decode and conditional
  writer rule are no longer the first suspects. `case_0003` has a full-frame
  dependency cone at radius 248 x repeat 10 and stays fail-closed after staging.
  Evidence:
  `refs/conformance/olmblur_case0003_0004_actual_aex_prestore_differential_20260716.md`.

- 2026-07-16 `Smoother2 case0012 frame-setup gate correction` (latest
  override): no correctness status is promoted. Windows 8bpc
  `FUN_180003eb0 -> FUN_180002e90` gates unpremultiply on render byte `+0x18`,
  which maps through `FUN_180005180(base+8)` to setter byte `+0x20`.
  `FUN_180004e10` leaves that byte zero; it is not `Enable Color Key`. Removing
  the Mac shortcut reproduces the accepted Windows class bytes, cardinal6
  descriptor `92,841,1,92,842,2`, `e170 c=7`, and first appended RGBA/weight
  within float print precision. A same-context bundle A/B shows the old false
  gate at `max=115`, mean `0.1616552`, `19486` differing pixels and the
  grounded gate at `max=151`, mean `0.2171072`, `19891` differing pixels.
  The old path was accidental downstream compensation, not a reason to
  restore a binary-disproved gate, and no `AE exact` claim is made. The broad
  legacy CLI before-frame aggregate is not an override because those AE-saved PNGs are premultiplied exports rather
  than host-input truth. Keep downstream `d3b0/da50/e170/f270/e3a0` unchanged
  for this witness; next local work is the remaining producer/composite lane
  and separate `0004` path. Evidence:
  `refs/conformance/olmsmoother2_case0012_unpremul_gate_20260716.md`.

- 2026-07-16 `DirectionalBlur isolated PF8 writer proof` (latest override):
  no correctness status is promoted. The actual AEX callback at
  `0x180006b30` is now isolated and replayed directly: it indexes float RGBA
  through params `+0x8090/+0x8098/+0x809c/+0x80a0`, applies Brightness Gain
  from `+0x28` to RGB, upper-clamps RGB only, truncates with `CVTTSS2SI`,
  leaves alpha ungained/unclamped, and stores all four ARGB8 bytes. Three
  actual-AEX cases ground half-tie truncation, upper-clamp/alpha wrap, biased
  indexing, and complete overwrite in 35 instructions each. The remaining
  external fact is the same-run float RGBA entering this callback on the real
  row-755 residual lane; no production change follows from the isolated
  writer. Evidence:
  `refs/conformance/olmdirectionalblur_direct_writer_actual_aex_20260716.md`.

- 2026-07-16 `KiraKira PF16 scale correction and typed local boundary`
  (latest override): no correctness status is promoted. The checked-in AEX
  constants used by the separate byte/word writer helpers are `255.0` at
  `0x1814d65a8` and `32768.0` at `0x1814d65ac`; every other Mac OLM deep-color
  path also uses the AE `PF_MAX_CHAN16` scale. `OLMKiraKira.cpp` alone used
  `65535.0` for PF16 read/write, so it now uses `PF_MAX_CHAN16`. A bounded
  Mode-2 Mac-source fixture grounds screen-over ordering and PF8/PF16/PF32
  conversion for one checked-in float witness, and the universal Debug build
  succeeds. Direct actual-AEX execution now separately proves that the leaf
  PF8/PF16 helpers truncate toward zero without clamping, PF32 copies raw
  float bits, and all three store ARGB order. The Mode-2 output-to-host-writer
  call chain remains unbound, so these helper-local facts do not justify a
  Mac rounding change or infer host compose, Windows output, or AE exactness.
  Evidence: `refs/conformance/olmkirakira_mode2_mac_boundary_20260716.md` and
  `refs/conformance/olmkirakira_typed_writers_actual_aex_20260716.md`.

- 2026-07-16 `Smoother2 live producer witness accepted` (latest override):
  no correctness status is promoted. The accepted in-process Windows return for
  `legacy_case_0012_gamma5_red_blue_current_aex` now binds the live producer
  lane through writer hook `+0x350b` and records exact same-run call order
  `f270 entry -> e170 entry/return -> e3a0 entry/return -> f270 return`. The
  valid Windows return is `e170_c=7`, not the earlier local `c=2`
  predecessor, and `e3a0` / `f270` both return one vertex from
  `0x908f6ff8a0` with raw words
  `3e3ce706,3e3ce706,3e3ce706,3f2eaeaf` and weight `3e91a7b9`. The corrected
  descriptor rerun now proves live `RDX p2[0..5]=92,841,1,92,842,2`, sample
  `x/y=92,841`, center bytes `255,255,0,255`, previous bytes `255,0,0,0`,
  left bytes `0,255,0,255`, and predicate bits `center_b0=255`,
  `prev_b0=255`, `left_b1=255`, which match `e170_c=7`. The predicate is now
  proven. A local diagnostic at the Windows origin `(92,841)` still produces
  `cardinal6 desc=92,840,1,92,843,2`, so the difference is not coordinate-only.
  The remaining live lane is the `d3b0/da50` stop-predicate class bytes around
  `x=91..93`, `y=840..844`; keep `0004` separate.
  Evidence:
  `refs/conformance/olmsmoother2_legacy_key_producer_actual_aex_20260716.md`
  and
  `refs/conformance/olmsmoother2_legacy_upstream_descriptor_local_probe_20260716.md`.

- 2026-07-16 `Smoother2 common-runner producer successor` (latest override):
  no correctness status is promoted. The rejected launcher-only case0012
  request is superseded by
  `olmsmoother2_legacy_key_producer_common_core_20260716`, which carries the
  real AE input/manifest/renderer, binds the writer anchor, and captures the
  `e170`, `f270`, and `e3a0` entries and callsite-bound returns. The contract
  distinguishes function `hook_rva` from `return_site`, records raw float32
  vertex/weight words, rejects mixed identity, and avoids the unsupported CDB
  MASM `&&` form. Package generation and local fail-closed validation pass;
  this is not a Windows observation. Current host feedback says AE2025 exits
  even for attach-only CDB with `g`, while the no-CDB control succeeds, so a
  missing typed event remains `exact_bind_failure` and no final-writer or
  export evidence may substitute. The validated request is staged on the NAS
  as
  `REQUEST__OLMSMOOTHER2_LEGACY_KEY_PRODUCER_COMMON_CORE__20260716_092547.zip`.

- 2026-07-16 `writer/export boundaries and next live witnesses` (latest
  override): no `AE exact` status is promoted. `OLMBlur case_0004` retains
  pre-store values `22037.498046875/26373.498046875`; the actual standard
  writer stores `22037/26373`, so the remaining residual is upstream of that
  writer. `OLMDirectionalBlur` Front Alpha Fade differs from the Windows PF
  slice at `226` packed words (`468` channel values across `226` pixels), while
  that Windows PF slice and its returned PNG are identical; export is ruled
  out. `OLMDistanceGradation` PF16 alpha samples remain Windows
  `3268/9876/28359` versus Mac `3267/9877/28360`, which rejects one global
  final-writer rounding rule but does not separate field, compose, and store.
  `OLMKiraKira` Mode 2 `FUN_18114ffd0` ends after four clamps and float stores;
  no call to the separate PF8/PF16/PF32 writer candidates is statically bound.
  `OLMSmoother2` now has valid same-run call-order and return facts for `0012`:
  writer hook `+0x350b`, `e170_c=7`, and one-vertex `e3a0/f270` raw words
  `3e3ce706,3e3ce706,3e3ce706,3f2eaeaf` / `3e91a7b9`. The corrected rerun now
  proves live descriptor `92,841,1,92,842,2`, sample `92,841`, class bytes
  `255,255,0,255` / `255,0,0,0` / `0,255,0,255`, and predicate bits
  `center_b0=255`, `prev_b0=255`, `left_b1=255`, matching `e170_c=7`. The
  old local `c=2` row is still predecessor context only; the next move is a
  Mac-side descriptor/dispatch comparison/patch against the Windows live lane.
  The fail-closed
  DirectionalBlur writer-entry and
  KiraKira Mode 2 compose/writeback requests are queued. The first generated
  Smoother2 producer runner was rejected before dispatch because it did not
  inject the requested AE case; its contract is retained for a common-runner
  successor. Evidence:
  `refs/conformance/olmblur_writer_export_boundary_20260716.md`,
  `refs/conformance/olmdirectionalblur_writer_boundary_localization_20260716.md`,
  `refs/conformance/olmdistancegradation_alpha_store_residual_20260716.md`,
  `refs/conformance/olmkirakira_mode2_host_compose_writeback_boundary_20260716.md`,
  and
  `refs/conformance/olmsmoother2_legacy_key_setup_producer_witness_20260716.md`.

- 2026-07-16 `span-complete Radial differential and parallel boundary audits`
  (latest override): no `AE exact` status is promoted. `OLMRadialBlur` now
  captures the complete AEX `1x4` polar/scalar/validity span rather than the
  old two-cell display limit. After binding the same-run `ctx+0x3a9e8` outer
  base span and removing the portable prepass's premature validity rejection,
  Repeat Border 0 and 1 are bit-exact at all five compared stages: injected
  polar RGBA, filtered source alpha, accumulated RGBA, max alpha, and collapsed
  RGBA. The full-frame case_0009 downstream witness remains open.
  `OLMSmoother2` locally grounds c=2/c=3 classifier rows and cce0 gamma mode 0
  (`apply=0`) versus Gamma Colors mode 3 (`gamma=2.1695473`, `apply=1`), and
  the accepted Windows in-process witness now separately preserves valid live
  `0012` call-order/return facts (`e170_c=7`, one returned vertex), and the
  corrected rerun now proves matching live predicate bytes under descriptor
  `92,841,1,92,842,2`. The Smoother2 next action therefore moves upstream to
  local Mac descriptor/dispatch comparison/patch versus Windows, not another
  predicate-byte rerun. `OLMDirectionalBlur` Front Alpha
  Fade is exact through its bounded actual-AEX rowdriver, denominator, alpha,
  and normalization boundary; its PF writer still differs from the Windows
  reference at 226 values. `OLMKiraKira` Mode 2 statically grounds its five-ray
  raw RGB/raw-alpha accumulation, the pinned float64 `0.001` threshold, and
  four independent clamps; the later host compose remains unresolved. Evidence:
  `refs/conformance/radialblur_prepass_local_20260716.md`,
  `refs/conformance/olmsmoother2_legacy_key_gamma_classifier_config_witness_20260716.md`,
  `refs/conformance/olmdirectionalblur_front_alpha_boundary_audit_20260716.md`,
  and `refs/conformance/olmkirakira_mode2_compose_witness_20260716.md`.

- 2026-07-16 `latest override: bounded differential and fixture-state corrections`:
  no `AE exact` status is promoted and broader priorities are unchanged.
  `OLMColorKey` Edge Blur directions 1/2/3 are `9/9` binary-grounded in the
  actual-AEX differential, but there is no AE-exact result. The Replace flag is
  absent from the AEX Edge orchestrator, whose static order is keyer -> Thin ->
  Blur; the two Mac-only Replace guards are removed, while the full Unicorn
  orchestration scaffold remains blocked before its first stage hook.
  `OLMDirectionalBlur`
  angle 0 and angle 45 are typed-differential exact; the Mac host adapter is
  locally `2/2` exact with eight gate rejects, and this adds no AE-exact result.
  `OLMDistanceGradation` retains the PF8 truncation fact, while the PF16 writer
  leaves `inactive_for_fixture`; neither changes the pending live residual
  assignment. `OLMToonDilate` now has a bounded PF16 worker chain from the
  five-argument copy callback through the exact-opaque (`32768`) seed boundary
  to an in-output exact four-word helper copy. A corrected true-`2x2` PF16
  fixture crosses the former `0x1801adc8f` stop and matches source selection,
  copied words, and final output against `RenderTyped<PF_Pixel16>` for seven
  alpha values. Host `PF_COPY` behavior remains
  an inference, and the global seed/premultiply candidate stays rejected because
  it broke two of three normalized regression gates. `OLMRadialBlur` remains blocked: the live scatter
  validity span is 4, not the previously assumed 2. Evidence:
  `refs/conformance/olmcolorkey_edge_blur_apply_differential_20260716.md`,
  `refs/conformance/olmcolorkey_replace_edge_orchestration_20260716.md`,
  `refs/conformance/olmdirectionalblur_actual_aex_port_differential_20260716_followup.md`,
  `refs/conformance/olmdirectionalblur_mac_host_adapter_20260716.md`,
  `refs/conformance/dg_u8_rounding_boundary_20260716.md`,
  `refs/conformance/olmtoondilate_pf16_pf32_copy_boundary_20260716.md`,
  `refs/conformance/olmtoondilate_pf16_actual_aex_cli_differential_20260716.md`,
  `refs/conformance/olmtoondilate_pf16_2d_propagation_followup_20260716.md`, and
  `refs/conformance/radialblur_prepass_local_20260716.md`.

- 2026-07-16 `post-boundary local proofs and PF8 correction` (latest
  override): no `AE exact` status is promoted. `OLMDistanceGradation` now has
  an actual-2025-AEX U8 conversion witness: a steered `12.51` code is stored as
  `12`, rejecting round-nearest and matching truncation. The Mac PF8-only
  `clamp8` writer now follows that rule; PF16 is unchanged, the focused AEX/CPU
  fixtures pass, and an isolated arm64 Debug build succeeds. The pending
  three-case Windows return is still required to assign the live residuals.
  `OLMBlur` build provenance is closed locally: the MediaCore binary SHA
  `c6de66da...badf206` predates the current PF16 writer correction, while a
  fresh no-install HEAD build contains the new writer and hashes to
  `23b358e8...f350520d`. Do not judge the new writer using the stale installed
  binary. `OLMDirectionalBlur` now matches the actual AEX typed rowdriver on a
  padded `rowbytes=76`, non-full-area host-world fixture and the complete
  bounded host fixture reaches final ARGB8 output; neither is an AE-host exact
  claim. `OLMRadialBlur` retains valid actual-AEX prepass/scatter plane
  snapshots, but its first attempted portable comparison was rejected as
  self-referential. The corrected harness is fail-closed because the CLI has
  no callable typed-plane seam; sampler execution alone is insufficient.
  `OLMColorKey` corrected its Edge Blur apply fixture contract: direction 1 is
  locally byte-exact, while directions 2/3 remain real alpha-only semantic
  mismatches under a fixture-scoped mapping audit. Evidence:
  `refs/conformance/dg_u8_rounding_boundary_20260716.md`,
  `refs/conformance/olmblur_pf16_current_head_build_provenance_20260716.md`,
  `refs/conformance/olmdirectionalblur_actual_aex_port_differential_20260716_followup.md`,
  `refs/conformance/radialblur_prepass_local_20260716.md`, and
  `refs/conformance/olmcolorkey_edge_blur_apply_differential_20260716.md`.

- 2026-07-16 `production binary-boundary corrections and deeper host stops`
  (latest override): no `AE exact` status is promoted. `OLMBlur` PF16 final
  storage now follows the actual AEX `ADDSS 0.5f -> floorf -> CVTTSS2SI ->
  store AX` sequence without nominal `0..32768` saturation; actual-AEX
  microfixtures, the bounded worker fixture, the Mac-lane differential, and an
  arm64 Debug build pass. `OLMSmoother2` corrects the `FUN_18000ead0`,
  `FUN_18000e4b0`, `FUN_18000edb0`, and `FUN_18000e7c0` horizontal-scale
  initializers from `0.5` to the AEX-proven `1.0`; all four synthetic
  classifier rows now agree at every production c280/cce0 boundary and all
  six sibling no-chase/chase boundaries pass. The remaining classifier-`0x40`
  difference is confined to an incomplete standalone helper replay and is
  not a production dispatch gap. `OLMColorKey` now executes the actual-AEX
  boundary seed through the type-1/2 distance fields and drives
  `FUN_1800085b0` Edge Blur apply through directions 1/2/3 to normal `RAX=0`
  return with PF Handle Suite cleanup. The later bounded type-3 probe closes
  its separate allocator/host ABI and Euclidean float output; only the full
  combined orchestration remains blocked.
  `OLMToonDilate` advances beyond the former `0xc3` callback alias to
  `0x1801adc8f`, which is the next synthetic host/exception boundary.
  `OLMRadialBlur` now drives the bounded `FUN_180004640` caller through
  sampler dispatch, prepass/scatter, scalar collapse, inverse sampling, and a
  synthetic-loader return for Repeat Border 0/1. This proves dispatch and
  plane ownership, not general border semantics or native AE caller behavior.
  The unresolved work remains live AE/Windows binding and downstream host
  ABI, not broad PNG tuning. Evidence:
  `refs/conformance/olmblur_pf16_unclamped_pack_boundary_20260716_followup.md`,
  `refs/conformance/olmsmoother2_classifier40_f8f0_scale_factor_proof_20260716.md`,
  `refs/conformance/olmsmoother2_sibling_boundary_proof_20260716.md`,
  `refs/conformance/olmsmoother2_current_aex_c280_cce0_branch_proof_20260716.md`,
  `refs/conformance/olmcolorkey_boundary_to_distance_actual_aex_20260716.md`,
  `refs/conformance/olmcolorkey_edge_blur_apply_aex_20260716.md`,
  `tools/emulation/OLMRADIALBLUR_CALLER_WITNESS_20260716_followup.md`,
  and
  `tools/emulation/OLMTOONDILATE_ACTUAL_AEX_DIFFERENTIAL_20260716_followup.md`.

- 2026-07-16 `Mac-only second-wave binary proofs`: no correctness status is
  promoted, but five unresolved lanes now have narrower binary-grounded stop
  points. `OLMSmoother2` classifier `0x40` first diverges in the portable
  `f8f0`/cardinal-9 contribution: the actual AEX first weight is
  `0.4999970794`, while the port emits `0.24999854`; the following `fef0`
  contribution agrees. `OLMRadialBlur` actual-AEX helpers `FUN_180001270` and
  `FUN_180001520` are proven to differ on loose border coordinates while
  agreeing on an interior control. `OLMDirectionalBlur` angle `0` is proven to
  enter the shared rotation schedule as `pi/2` rather than bypassing it, and
  angle `45` enters as `3pi/4`; normalization and output remain outside that
  probe. `OLMKiraKira` Merge Mode 2 is statically grounded at
  `FUN_18114ffd0` as five-layer additive RGB/raw-alpha accumulation followed
  by independent clamping, but still lacks a live compose/writeback witness.
  `OLMColorKey` now has a bounded runnable CLI-binary fixture plus a successful
  plug-in build; the built plug-in exposes only AE host entry points, so this
  is not execution of Smart Render and does not close the 32bpc host boundary.
  Evidence:
  `refs/conformance/olmsmoother2_classifier40_f8f0_first_divergence_20260716.md`,
  `refs/conformance/olmradialblur_border_sampler_semantics_actual_aex_20260716.md`,
  `refs/conformance/olmdirectionalblur_angle0_diagonal_schedule_20260716.md`,
  `refs/conformance/olmkirakira_merge2_address_contract_20260716.md`, and
  `refs/conformance/olmcolorkey_mac_binary_harness_20260716.md`.

- 2026-07-16 `Mac-only binary differentials`: five bounded lanes advanced
  without Windows execution or production image tuning.
  `OLMBlur` now matches the actual AEX PF16 writer and complete 16/32bpc
  worker fixtures, rejecting a global nearest-even writer fix.
  `OLMColorKey` has a static source/evidence audit for native PF_PixelFloat
  Smart Render dispatch; it does not execute that host path, and keeps the
  32bpc pair blocked on host-input conversion. `OLMDirectionalBlur` proves PF Iterate8 area plus padded-row mapping
  while leaving production integration gated on live host binding.
  `OLMRadialBlur` proves B150 changes propagate through normalization,
  sampling, and byte writeback in the bounded actual-AEX scaffold.
  `OLMSmoother2` closes c=2/c=4/zero classifier rows and localizes classifier
  `0x40` to a portable c280 contribution/weight dispatch gap. Evidence:
  `refs/conformance/olmblur_mac_lane_differential_20260716.md`,
  `refs/conformance/olmcolorkey_32bpc_host_path_proof_20260716.md`,
  `refs/conformance/olmdirectionalblur_world_row_mapping_differential_20260716.md`,
  `refs/conformance/olmradialblur_b150_downstream_replay_20260716.md`, and
  `refs/conformance/olmsmoother2_current_aex_c280_cce0_branch_proof_20260716.md`.

- 2026-07-16 `additional Mac-only depth/residual proofs`:
  `OLMToonDilate` now has a 4/4 portable typed-core model covering 16/32bpc
  storage, alpha thresholds, boundaries, propagation, and quantization; the
  current 32bpc comparison remains host-input-conversion blocked, not exact.
  `OLMDistanceGradation` actual-AEX PF8 callback emulation matches the local
  model across eight field-byte boundaries and the portable field core still
  passes 286 values. This makes case `0001 (17,0)` locally compatible with a
  pre-store boundary but does not explain the direct live residuals in cases
  `0015/0029`; no production tuning is allowed before their typed chain.
  The model duplicates production formulas and is not an independent binary
  oracle. Evidence: `refs/conformance/olmtoondilate_typed_core_differential_20260716.md`
  and `refs/conformance/olmdistancegradation_8bpc_residual_semantics_20260716.md`.

- 2026-07-16 `last-priority local guards`: `OLMKiraKira` now has an
  8-check binary-grounded rejection matrix that forbids promotion of Mode 3
  live Gaussian, Mode 4, merge-mode-2 compose, or broad final quantization
  without stronger evidence. `OLMSmoother v1` now has a static source contract
  for 8/16/32bpc branches and `--force-version 1`; it does not execute dispatch,
  and 16bpc remains exact-eligible
  only after cross-host evidence and 32bpc remains probe-only. Neither result
  claims AE exactness or v1-v2 equivalence. Evidence:
  `refs/conformance/olmkirakira_rejection_matrix_20260716.md` and
  `refs/scripts/smoke_olmsmoother_v1_depth_dispatch.py`.

- 2026-07-15 `OLMDistanceGradation 8bpc coordinate-liveness census`: accepted
  as `answered / observation-only`. All three fresh AE 25.2 Software 8bpc
  cases are bound to AEX SHA-256
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
  PF8 is live (`24714/9310/3439` hits) and PF32 is zero, while `(397,281)` and
  its radius-2 neighborhood have zero PF8 hits in every case. The return has a
  parser-fixture kind drift but satisfies the material census contract. Next
  use the Mac-residual/census intersection for a strict typed witness:
  `case_0001 (17,0)` derived from live anchor `(0,0)`, direct live
  `case_0015 (780,495)`, and direct live `case_0029 (987,496)`. Do not retry
  `(397,281)` or infer an image-math change from liveness alone. Evidence:
  `refs/conformance/olmdistancegradation_8bpc_coordinate_liveness_census_return_20260715.md`.

- 2026-07-15 `OLMDirectionalBlur mode-0 local adapter boundary`: the
  actual-AEX full rowdriver gate remains `3/3` byte-exact and a local typed
  harness closes the portable source/comp-map/prepass/scatter/denominator/
  alpha-max/normalization/final-RGBA chain. No production dispatch changed.
  A compile-gated Mac adapter was explicitly rejected because the AE
  host/world mapping is not independently proven. Keep the row755 Windows
  typed witness as the production-integration gate. Evidence:
  `refs/conformance/olmdirectionalblur_mode0_local_adapter_boundary_20260715.md`.

- 2026-07-15 `OLMDistanceGradation 8bpc exact-coordinate return`: accepted as
  `exact_bind_failure`, not algorithm evidence. AE 25.2 completed all three
  8bpc Software cases (`0001/0015/0029`) and CDB armed the absolute PF8/PF32
  callback breakpoints, but the PF8 entry condition `EDX=397/R8D=281`
  produced zero target records. The archive also omits the AEX SHA-256 and a
  complete typed field/compose/store chain, so the original request remains
  unsatisfied. Static ABI evidence still identifies `EDX/R8D` as callback
  x/y; the unresolved host question is whether AE's iterate ROI invokes that
  coordinate. Do not repeat the exact-coordinate condition. Next collect a
  hash-pinned coordinate-liveness census (total/min/max/first hits,
  target-neighborhood hits, output pointers, PF32 count) for the same cases.
  Evidence:
  `refs/conformance/olmdistancegradation_8bpc_exact_fixed_failure_20260715.md`.

- 2026-07-15 `OLMRadialBlur B150 worker differential`: a bounded local
  actual-AEX run reaches and returns from `FUN_18000B150`; a paired no-op
  detour keeps identical typed inputs/spans. The live worker changes only its
  owned RGBA/scalar row slice (`9 -> 245` nonzero cells), while the detour
  leaves it unchanged, and all retained float32 words pass raw-bit checks.
  This grounds B150 output ownership in the local scaffold, not full-frame
  case_0009 or Windows AE truth. Evidence:
  `refs/conformance/olmradialblur_b150_live_noop_detour_differential_20260715.md`.

- 2026-07-15 `OLMSmoother2 local c280-to-cce0 matrix`: local actual-AEX and
  portable replay agree through classifier/producer/c280/cce0 boundaries for
  the `c=2` append witness, `c=4` suppression control, and all-zero classifier
  `0xff`. An all-one neighborhood reaching classifier `0x40` remains an
  explicit portable-dispatch gap and is excluded from the pass gate. This is
  local binary-semantic evidence only; the live case_0012 class/config bytes
  and Windows AE result remain unbound. Evidence:
  `refs/conformance/olmsmoother2_fullchain_matrix_20260715.md`.

- 2026-07-15 `OLMKiraKira Mode 3 local Gaussian dispatch audit`: the pinned
  AEX body executes once in the local Unicorn scaffold and returns 63 words.
  Its allocated 21-word coefficient buffer is uniformly `0x3d430c31`; the
  portable uniform replay is `63/63` word-exact, while OpenCV 4.5.5 differs at
  all 63 words. This confirms the local emulation scaffold's behavior only.
  No runtime indirect target executed, and no live Windows coefficient return
  is bound, so production Gaussian changes remain forbidden. Evidence:
  `refs/conformance/olmkirakira_mode3_gaussian_actual_aex_dispatch_audit_20260715.md`.

- 2026-07-14 `OLMKiraKira Mode 3 forward warp`: the Mac helper now mirrors
  the observed OpenCV 4.5.5 `INTER_LINEAR` fixed-point coordinate and weight
  quantization for the grounded forward-warp call. A source-extracted C++
  fixture matches the captured AEX/OpenCV output at `63/63` float32 words;
  the arm64 Debug plug-in build succeeds. This closes only the forward-warp
  primitive boundary. Inverse warp, Gaussian live coefficients, ray
  aggregation, and AE-host output remain unproven and are not `AE exact`.
  Evidence: `refs/scripts/smoke_olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.py`.

- 2026-07-14 `common Windows CDB launcher gate`: the previous four-plugin
  batch was fail-closed at `cdb_launch` for every plugin: AfterFX was observed
  by process enumeration, but no CDB detach or queue binding marker was
  produced. The common runner was changed to launch `AfterFX.exe -r <queue>`
  directly under CDB, keep the initial breakpoint enabled, write an explicit
  initial-break marker, and detach with `qd`; the `cmd.exe` child wrapper and
  `ld:AfterFX.exe` filter are removed. Local common tests are 19/19 and all six
  current witness-package smokes pass. A DG case0026 launch-only package was
  sent for real-Windows validation; it is a launcher gate only and must not
  change any plugin correctness status until `cdb_bootstrap_exit`, the initial
  break marker, and `queue_bootstrap.log` are all returned. Evidence:
  `refs/conformance/windows_witness_return_batch_20260714.md`.

- 2026-07-13 `Windows one-click witness batch`: the reusable
  `tools/windows_witness` compiler, six current common-core witness specs,
  outer serial dispatcher, and fail-closed batch intake are ready. The batch
  covers OLMBlur case0006, DistanceGradation 8bpc typed boundary,
  Smoother2 case0012, DistanceGradation case0026 16bpc, DirectionalBlur
  row755, and KiraKira Mode 3. Every inner contract is pinned to AE 25.2,
  Software render, the audited MediaCore AEX path/hash, a unique request ID,
  authoritative return names, and actual exported bytes. Windows PowerShell
  5.1 parsed the outer launcher and all six inner launchers; `-PreflightOnly`
  verified all six host paths and AEX hashes before any AE launch. A separate
  Windows PowerShell 5.1 integration run proved that native stderr does not
  abort a successful job, a timed-out job is killed and classified with exit
  124, the following job still runs, and the Mac intake accepts the resulting
  backslash-named Windows ZIP only after binding its inner exports and identity
  to the exact request batch. Each job's
  `satisfies_request_ids` binds the new common-core request to the legacy queue;
  the batch covered seven of the eight requests pending when that batch was
  generated. This is historical cardinality, not the current queue count. The
  separate DirectionalBlur angle-0 single-shot request is intentionally not
  claimed. Two live six-lane attempts and the first one-lane launch gate
  returned no ready marker. The one-lane return proved that AfterFX started,
  but the generated queue contained an unescaped literal newline inside the
  bootstrap string and therefore failed JSX parsing before it could write
  `queue_bootstrap.log`. The compiler now emits `\\n`; 16 unit tests, the
  synthetic witness smoke, an independent review, and a generated-JSX syntax
  check pass. The corrected queue still did not bootstrap when AE was launched
  once with `-m -r`; this matches the observed surviving AE command line and
  Adobe's documented behavior that `-r` dispatches to an existing instance.
  A live two-phase retry then started fresh AE with `-m` as PID `12792` and
  dispatched `-r <queue.jsx>` as PID `51764`, but AE 25 still produced no
  bootstrap. The returned diagnostics bind both invocations and prove that
  neither one-shot nor existing-instance `-r` dispatch is reliable in this
  environment. The next runner must use the repository's previously successful
  CDB-launched AfterFX-plus-JSX path and retain fail-closed bootstrap/process
  diagnostics. The replacement one-lane DG 8bpc CDB launch gate is staged at
  `$OLM_EXCHANGE_ROOT/new/olm_windows_witness_launch_gate_dg8_cdb_sameprocess_ae25_20260713_205007.zip`,
  SHA-256
  `c6f326c8407745cf7f737b29068f0147de39cc8b2a47292a528fdf22843df8ff`.
  Windows PowerShell 5.1 parses every included PS1. This is request readiness,
  not algorithm evidence or AE exact. Do not send the full six-lane batch or
  superseded variants until this gate writes its bootstrap and ready markers.

- 2026-07-13 `OLMSmoother2 case0012 live config request`: a focused,
  fail-closed Windows package now binds one fresh current-AEX run at `(91,841)`
  and requests the c280 `+0x20/+0x24` scale words, cce0 gamma bytes through
  mode `+0x06`, pointer arithmetic, and final-writer corroboration under one
  run id. This is request readiness, not live evidence; its register/pointer
  hypotheses must be accepted only if the returned raw bytes and same-run
  identity pass the strict parser. Package SHA-256:
  `374e774bf7bfc95b06be11298144a682d11089db429e5da937fd00cd670e53e3`.

- 2026-07-13 `OLMRadialBlur A850 -> D80 downstream`: local actual-AEX replay
  now matches the portable mirror raw-float exactly at all four focused Zoom
  points after enforcing float32 argument quantization and the AEX
  `SUBSS/MULSS/ADDSS` order. The former `(6,0)` alpha one-ULP gap was caused by
  double arithmetic in the mirror. Mac production used the same double
  accumulation and is now changed to explicit per-operation float32; universal
  Debug build passes. Mac AE case0009 A/B with the grounded float32 order and
  pure truncate improves `31,119 -> 21,429` differing pixels (`max=1`) but is
  not exact. A same-point Mac Debug capture proves the AEX-order float32
  candidate's raw A850 radius/angle bits exact at all 32 top-row points. That
  operation order is now promoted to production and a fresh Mac AE run proves
  production raw A850 exact at 32/32. The PNG residual improves again to
  `12876` nonzero pixels with `max=1`, so this is binary-grounded progress but
  not `AE exact`. The older actual-AEX probe used `32x32` geometry and a forced `90`
  degree quality step, so its downstream indices, selected cells, and D80
  values are non-semantic for the 1920x1080 AE render. The comparator permits
  the raw-A850 candidate proof while its exactness gate fails closed if that
  artifact is used to claim full index/cell exactness. A follow-up attempt to
  make negative-angle `+2pi` a float32 add was rejected: raw A850 fell from
  `32/32` to `0/32` and the PNG residual rose to `20868`; retain the observed
  double-add-then-float behavior. Evidence:
  `refs/conformance/olmradialblur_a850_downstream_actual_aex_20260713.md` and
  `refs/conformance/olmradialblur_a850_d80_f32_mac_ae_ab_20260713.md` and
  `refs/conformance/olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_20260713.md` and
  `refs/conformance/olmradialblur_case0009_mac_a850_coordinate_comparison_20260713.md` and
  `refs/conformance/olmradialblur_case0009_production_a850_f32_mac_ae_20260713.md`.

- 2026-07-13 `OLMDirectionalBlur row755 nested-CDB retry`: the latest return is
  still `exact_bind_failure`, but closes AE launch/pause, exact AEX hash,
  absolute-base lookup, CDB attach, and breakpoint arming. Capture failed only
  because 63 writes were expanded into one overlong breakpoint command and
  the row predicate used unsupported `&&`. The replacement invokes a separate
  line-oriented `capture_at_5554.cdb` via `$><` and uses nested `.if`; do not
  reopen algorithm code from this tooling failure. Evidence:
  `refs/conformance/olmdirectionalblur_row755_nested_cdb_retry_20260713.md`.

- 2026-07-13 `Windows SSH retry intake`: fail-closed execution returned
  `exact_bind_failure` for both focused requests. DirectionalBlur failed before
  AE launch because a PowerShell default parameter evaluated `$PSScriptRoot`
  before it was populated. Smoother2 launched AE25/CDB but attempted resolved
  `bp` commands before `OLMSmoother2.aex` loaded, then timed out with no module
  or typed markers. Neither return is proof. The replacement initializes the
  DirectionalBlur work root from `$PSCommandPath`, uses deferred `bu` hooks for
  Smoother2, and pins the current AE25 AEX to size `192000`, SHA-256
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
  A later runner audit found the PowerShell 5.1 `Start-Process` argument-array
  boundary could drop the JSX path; the current packages use one explicitly
  quoted argument string. Current replacement ZIP SHA-256 values are
  `5e9b14dba8ac4a6075d17ca2c91f712da2cef143ba2dd58f6398cbea346881e2`
  and `f3234ae45e8627d4f39b533804e31533cf34ef679f95a2c10980411804202edb`.

- 2026-07-13 `Windows SSH / AE launch boundary`: Windows Codex orchestration,
  transfer, hash checks, and return packaging work, but OpenSSH launches
  AE/CDB in session 0 while the logged-in desktop is session 1. A bounded
  Interactive Token probe reached session 1, yet a one-line JSX marker failed
  with an `AfterFX.com` GPU3 prior-sanity warning and a contemporaneous
  Explorer/dcomp Application-log crash. AE-dependent requests therefore stay
  on the logged-in desktop launch path; SSH remains valid for non-GUI binary
  work. This is host tooling evidence only and does not change plug-in
  correctness. Evidence:
  `refs/conformance/windows_ssh_ae_interactive_broker_20260713.md`.

- 2026-07-13 `OLMDistanceGradation 8bpc depth-control desktop retry`: the
  diagnostic v4 is accepted. One hash-pinned 8bpc AE run recorded PF8
  `+0x1170870 = 24377` hits and PF32 `+0x1170c90 = 0` hits under one
  run/PID/base/hash. This closes callback-depth dispatch only, not any pixel or
  algorithm rule. The next allowed request is the typed field/compose/store
  boundary at `(397,281)` for cases `0001/0015/0029`. Evidence:
  `refs/conformance/olmdistancegradation_8bpc_depth_control_runner_fix_20260713.md`.

- 2026-07-13 `OLMDistanceGradation PF16 max-2 sensitivity`: twelve bounded
  actual-AEX `FUN_181170480` calls cover representative field words at
  `n-1/n/n+1` for cases `0024..0027`. The compose outputs change by at most one
  PF16 word per channel at those steps, while case `0027` stays flat. This is
  binary compose sensitivity, not live Windows field or AE-exact evidence. The
  retained store/export audit remains classified for three of four case-0026
  points; only `(907,222)` still needs direct same-run Windows PF16 store and
  export values. Evidence:
  `refs/conformance/olmdistancegradation_16bpc_max2_compose_sweep_20260713.md`.

- 2026-07-13 `OLMKiraKira Mode 3 actual-AEX probe`: the direct helper harness
  executes the AEX's MSVC TLS/OpenCV initialization, supplies the binary-bound
  `_aligned_malloc/_aligned_free` and CPU-dispatch backing stores, and now
  reaches `FUN_181272ec0` exactly once. The captured four-argument boundary is
  InputArray CV_32FC1 `9x7` (step 36), OutputArray CV_32FC1 `9x7`, `Size(0,1)`,
  and `sigmaX=2.5` for helper length 5. R9 and caller shadow words are explicitly
  not promoted to parameters. OpenCV 4.5.5 accepts the same primitive contract.
  The synthetic helper setup reaches the boundary with an all-zero input ray,
  so this closes Mode3 dispatch/primitive arguments but not the preceding ray
  population or full effect output. Evidence:
  `refs/conformance/olmkirakira_mode3_actual_aex_20260713.md`.

- 2026-07-13 `OLMKiraKira Mode 3 live desktop entry`: a hash-pinned
  AE 2026 desktop run reached the wrapper, create call, and first Gaussian
  kernel entry in one run with `ecx=21`, `xmm1=2.5`, and `r8=5`. Its return
  address fixes this pinned callsite at module RVA `0x126685c`. The returned
  archive remains `exact_bind_failure` because no return marker or 21-word
  payload was captured. A later v4 retry failed even earlier because the
  PowerShell 5.1 split argument form launched AfterFX with only `-m`; v5 uses
  one explicitly quoted `-m -r <jsx>` string for preflight and full render.
  Only an accepted v5 payload may classify the live Gaussian coefficients.
  Evidence:
  `refs/conformance/olmkirakira_mode3_live_gaussian_entry_and_runner_fix_20260713.md`.

- 2026-07-13 `OLMKiraKira Mode 3 sigma/ray witnesses`: four independent
  actual-AEX runs at lengths `1/2/5/9` keep the raw Size words `[0,1]` and
  capture sigmaX `0.5/1.0/2.5/4.5`. The callsite multiply and `.rdata` bytes
  independently fix `DAT_18148d670` to `double 0.5`. A separate producer
  witness captures 59 nonzero CV_32FC1 values immediately after the ROI copy
  and 63 nonzero values after the forward warp/Gaussian input. The first zero
  result was a probe defect: libm imports were not registered, so both AEX
  `cos` and `sin` calls retained the input angle in XMM0. With real libm, the
  captured 5-degree affine matrix is valid; OpenCV 4.5.5 reproduces all 63
  post-warp float32 words exactly. Mode 3's forward warp and Gaussian call
  contract are now grounded; the portable Gaussian primitive is the live
  implementation boundary. Evidence:
  `refs/conformance/olmkirakira_mode3_sigma_sweep_actual_aex_20260713.md` and
  `refs/conformance/olmkirakira_mode3_ray_population_actual_aex_20260713.md`
  plus
  `refs/conformance/olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.md`.

- 2026-07-13 `Windows runtime return intake`: the latest DirectionalBlur,
  Smoother2, and DistanceGradation returns are all explicit
  `exact_bind_failure`. DirectionalBlur never received the AE ready marker;
  Smoother2 resolved no module/base or requested hooks; DistanceGradation
  returned zero typed records and no same-run identity. Retain the archives,
  but promote none of them to proof and do not repeat the SSH/session-0 launch
  path. Evidence:
  `refs/conformance/windows_runtime_returns_fail_closed_20260713.md`.

- 2026-07-13 `OLMKiraKira Mode 3 actual-AEX Gaussian output`: after repairing
  the probe's libm imports, a derived harness executes the embedded
  `FUN_181272ec0` Gaussian body instead of stopping at entry and reaches caller
  return `0x181151105`. The returned CV_32FC1 output contains 63/63 nonzero raw
  float words. However, the portable/OpenCV-4.5.5 primitive differs at all 63
  words by much more than ULP noise. The Unicorn run uses synthetic TLS and a
  zero-initialized CPU-dispatch backing table, so its internal OpenCV path is
  not yet proven equivalent to a live Windows process. Retain these words as
  an emulation-path witness, not the primary algorithm oracle, until the
  dispatch path is validated or Windows captures the same bounded output.
  This is not AE exact. Evidence:
  `refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.md`.

- 2026-07-13 `OLMKiraKira Mode 3 Gaussian dispatch audit`: the embedded AEX
  initializes the probe-owned OpenCV dispatch backing to 4034 nonzero qwords
  before Gaussian entry. Sigma propagation is intact: `2.5` reaches
  `FUN_181266730`, the first `FUN_1812754a0`, and `FUN_181274e10`; ksize is
  `21`, type is `CV_32F`, and the locally generated 21-word coefficient buffer
  is uniformly `0x3d430c31` (`1/21`). The resulting output is exactly
  reproducible by a uniform 21-tap scalar filter, but this contradicts pinned
  OpenCV 4.5.5 Gaussian output at all 63 words. Treat the uniform kernel as a
  Unicorn/emulation-path fact only until the same five targets and coefficient
  buffer are captured in a live Windows process. Evidence:
  `refs/conformance/olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.md`.

- 2026-07-13 `OLMDistanceGradation 16bpc live field/source audit`: strict
  return-only extraction finds four coordinate-bound `case_0026` source worlds
  and converts their semantic RGBA16 values to exact A,G,R,B raw words. No
  retained return contains the corresponding live field raw word read at
  `[RCX+2]`, so exact `FUN_181170480` replay is possible for `0/4` points.
  Cases 0024/0025/0027 have no source+field-bound trace point at all. Do not
  derive the missing field word from PNG or rounded X values; the next Windows
  witness must capture source raw words, field raw words, coordinate, and case
  tuple in one run. Evidence:
  `refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.md`.

- 2026-07-13 `OLMDistanceGradation case0026 live field/source request`: a
  fail-closed Windows package now requests all four retained points in one
  AE/CDB run, including exact case tuple, source and field A,G,R,B words,
  `[RCX+2]`, and pre/post `FUN_181170480` output words. Post-state is bound at
  the exact caller return address captured from `[RSP]`, not an assumed shared
  exit offset. AEX identity and AE Software/16bpc are mandatory; all four must
  be complete for `answered`. Package SHA-256:
  `2d9ae24b59afea176fba8423a5cf943cd0c024fc089548fcae053b9a38451948`.

- 2026-07-13 `ColorKey / ToonDilate 32bpc second-generation parity`: accepted
  AE26.3 Software/linear-off/FLOAT return proves Windows effect-on equals its
  same-run no-effect control at raw sample level for ColorKey `case_0002` and
  ToonDilate `case_0001`; Mac effect/control pairs are also raw-sample exact.
  Cross-host controls still differ in every RGB sample (`6,220,800`, alpha
  excluded), so this is plugin-delta exact, not `AE exact`. Freeze both pixel
  implementations. Next replace imported-EXR conformance input with a
  cross-host-identical typed AE world or explicitly grounded import
  interpretation. Evidence:
  `refs/conformance/olm_windows_32bpc_second_generation_parity_20260713.md`.

- 2026-07-13 `OLMBlur PF16 writer half ties`: actual 2025 AEX execution at
  `0x1800030e2..0x180003123` distinguishes the writer from nearest-even:
  controlled raw float `1100.5` stores `1101` (add-half/truncate), while
  nearest-even would store `1100`. PF16 writer semantics are closed. This is a
  binary microtest, not AE conformance; remaining `case_0006` differences must
  be assigned to the pre-store float or host/reference provenance before any
  production change. Evidence:
  `refs/conformance/olmblur_writer16_half_ties_actual_aex_20260713.md`.

- 2026-07-13 `OLMDistanceGradation PF16 max-2 compose sweep`: bounded
  actual-AEX calls into `FUN_181170480` completed for representative
  `0024..0027` branch shapes (`4/4`, 653 instructions total). This proves the
  local harness can drive the PF16 compose branches and records their raw
  AGRB stores, but the injected field words are not Windows-live field values.
  Therefore this is binary-grounded branch evidence only: it does not close
  the max-2 residual family or justify an `AE exact` promotion. Evidence:
  `refs/conformance/olmdistancegradation_16bpc_max2_compose_sweep_20260713.md`.

This ledger replaces percentage-style progress tracking. The only completion
status is `AE exact`; all other states are evidence or work states.

See `notes/AE_EXACT_CONFORMANCE.md` for definitions and
`notes/PORTING_ROADMAP.md` for the current release scope and critical path.
`refs/conformance/olm_release_scope.json` is the machine-readable whole-release
gate. A passing row or packaged subset must not be promoted to plug-in complete
unless `scripts/check_olm_release_scope.py --require-complete` passes.

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

## Latest Overrides

- 2026-07-17 `OLMSmoother2 c280/cce0 direct-division boundary`: use
  `refs/conformance/olmsmoother2_case0012_post_leaf_cce0_20260717.md` /
  `.json`. A hash-pinned local AEX run and the current portable path now use
  an exactly matched `16x16` synthetic class/source fixture and caller config
  words `65536/65536` (normalized `655.36/655.36`, gamma mode `0`). The c280
  vertex RGBA and weight were already bit-exact. The former first cce0 red
  difference was one float32 ULP and came from the Mac computing one reciprocal
  then multiplying RGB, while `FUN_18000b120` performs three scalar `DIVSS`
  instructions at `0x18000b17c/181/18f`. Using direct per-channel division
  makes all nine compared c280/cce0 float32 words bit-exact. This closes only
  the bounded local synthetic arithmetic boundary; it is not live Windows,
  AE exact, a case_0012 continuation, or proof that the live polygon/dispatch
  selection is correct. Preserve the direct-division rule and continue the
  live post-f130/polygon-state lane separately.

- 2026-07-17 `OLMKiraKira Mode 2 aggregation/caller output`: use
  `refs/conformance/olmkirakira_mode2_actual_aex_merge_boundary_20260717.md`
  and `refs/conformance/olmkirakira_mode2_caller_output_boundary_20260717.md`.
  Three direct actual-AEX fixtures ground five-ray raw accumulation, the
  conditional color-helper path, four clamps, and float RGBA output. Static
  caller flow then proves Mode 2 selection through vtable `+0x10` and forwards
  the result into a caller-owned float buffer; the immediate caller performs
  no compose or PF8/PF16/PF32 writer selection afterward. The first unavailable
  ABI is `FUN_18114f4a0`'s host-owned vtable/channel object. Do not reopen the
  grounded aggregation, gain, clamps, or typed writers; the next proof must
  bind that host object/next consumer without claiming AE exactness.

- 2026-07-17 `OLMColorKey Edge Thin erode leaf`: use
  `refs/conformance/olmcolorkey_edge_thin_erode_aex_20260717.md` / `.json`.
  The hash-pinned actual-AEX `FUN_180008320` completes `2,176` exhaustive
  calls and disproves both prior threshold predicates as leaf semantics. Six
  terminal-loop fixtures ground the raw word load, float32 `MULSS`,
  `CVTTSS2SI` truncation, and low-word store. Static and connected-stage
  evidence separates the direct `8AD0 -> 58A0 -> 8320` family, whose immediate
  caller is `FUN_180009000`, from the independent 8-bit `8C90 -> 5D60` plus
  inline-erode path in `FUN_1800094B0`; the latter never calls `8320`. The
  pinned constant at `0x18001f754` is `4000.0f`, not `0.5f`. A bounded direct
  pipeline preserves the generated distance world and matches the portable
  terminal oracle. A bounded hash-pinned `FUN_180009000` run now reaches the
  native type-2 ERODE seam with paired amounts `-1/-3`, records the native
  stack/register ABI, and preserves the distance world. Because volatile
  `RDX` is explicitly rebound at the callsite and selected worlds are repaired
  after the raw seam snapshot, this is not untouched full caller-to-leaf
  execution. Host orchestration and the full amount-normalization boundary
  therefore remain open; do not patch the production threshold from the leaf
  or repaired seam alone. Evidence:
  `refs/conformance/olmcolorkey_edge_thin_actual_caller_20260717.md` / `.json`.

- 2026-07-17 `OLMRadialBlur scatter caller and tail core`: use
  `refs/conformance/olmradialblur_scatter_caller_20260717.md` /
  `.json` and
  `refs/conformance/olmradialblur_scatter_tail_equivalence_20260717.md` /
  `.json`. The bounded actual-AEX `FUN_1800024c0` caller and portable caller
  agree on absolute-radius source-plane indexing for nonzero start radii,
  zero/NaN skip versus negative-finite activation, and outer-before-inner
  call order. Mode-1 integer accumulation is pinned to x86 two's-complement
  wrap, including `INT_MAX + 1 -> INT_MIN`. The portable `FUN_180001c90` tail
  also matches ten actual-AEX fixtures byte-for-byte, including mode 2, the
  3000 clamp, table origin, inner row-tail underflow, persistent max-alpha,
  source NaN payload, and `CVTTSS2SI` exceptional sentinels. UBSan is clean.
  This is bounded function-level evidence only; production wiring and
  full-frame host/output binding remain open, and the portable bounds bailout
  is an explicit safety divergence outside the fixture domain.

- 2026-07-17 `OLMToonDilate raw semi-alpha candidate`: use
  `refs/conformance/olmtoondilate_pf32_raw_copy_witness_20260717.md` and
  `refs/conformance/olmtoondilate_rgb_alpha_postpass_ab_20260717.md`, plus
  `refs/conformance/olmtoondilate_pf8_seed_predicate_20260717.md` / `.json`.
  A seeded
  actual-AEX PF32 worker hits the live copy helper while an out-of-radius
  semi-alpha pixel survives with raw RGB, disproving the Mac-only final
  `RGB*=alpha` postpass for the bounded path. Removing it makes 8bpc
  `case_0002` exact, improves but does not close `case_0003`, and preserves
  all three covered 16bpc exact cases. A paired hash-pinned native PF8 worker
  fixture further proves that alpha `254` is not a propagation seed while
  alpha `255` is; both runs reach the live copy helper and preserve padded
  rowbytes. A paired `3x1` actual-worker fixture also proves equal-distance
  forward propagation keeps the first winner (`x=0`) under both endpoint
  permutations while reaching the native tie branch, copy helper, and resume
  address. Do not revisit the PF8 opaque-seed threshold or this bounded
  equal-distance forward tie rule for `case_0003`; narrow the residual at
  radius scaling, host staging, propagation order outside this fixture, or
  transparent-cell candidate selection. Keep the status candidate /
  binary-grounded until Mac AE regression and 32bpc cross-host validation.

- 2026-07-17 `OLMDistanceGradation RenderBits staging boundary`: use
  `refs/conformance/olmdistancegradation_renderbits_host_resize_staging_audit_20260717.md`
  / `.json`. Four typed same-shape staging cases and six existing production
  harness cases pass with padded rowbytes. Non-identity resize, origin, and
  host allocation order remain unresolved; this does not reopen EDT,
  compose, or store and does not promote 8bpc status.

- 2026-07-17 `OLMDirectionalBlur writer caller contract`: use
  `refs/conformance/olmdirectionalblur_caller_contract_20260717.md` / `.json`.
  A real `FUN_180006700` wrapper call binds the Iterate8 callback ABI and the
  `0x180006b30` writer's params/x/y/stack-output contract, including the
  float-cell index formula and one actual packed ARGB8 result. The pending
  Windows same-run writer-entry floats are still required; do not change the
  already-grounded writer from this synthetic caller fixture.

- 2026-07-17 `OLMBlur case_0003/0004 readiness`: use
  `refs/conformance/olmblur_case0003_0004_readiness_audit_20260717.md` /
  `.json`. The audit now fail-closes all 120 Legacy schedule calls, ten H/V
  partitions, four Non-Legacy radius stages, coefficient sets `4970/4970` and
  `177/177`, and the retained writer rounding control. No additional local
  schedule/coefficient/rounding condition remains; the worker/helper
  pre-store boundary and fresh Mac AE validation remain open.

- 2026-07-16 `OLMBlur Legacy case_0003 schedule/full-frame candidate`: use
  `refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.md` /
  `.json`. The hash-pinned Legacy caller, with helper bodies detoured, emits
  exactly `120` calls as ten `H x 6, V x 6` iterations at radius `248`.
  Actual-AEX one-output helper fixtures match portable C++, and a native
  `960x540` replay using the captured schedule predicts the pinned Windows
  writer words at all `20/20` residual coordinates. Current float-exp
  generation differs from the captured coefficient input at `16/4970` words;
  the 16bpc-only double-exp-to-float candidate matches `4970/4970` and changes
  `0/110` coefficient words for already-exact Legacy `case_0007`. The
  Universal build succeeds. The coefficients were produced through
  host-backed Python math callbacks, not Windows CRT, and the full-frame replay
  is native portable C++, not actual full-frame x86 or AE. Keep current-plugin
  16bpc status at `5/7 AE exact` until one fresh identity-bound Mac AE run
  validates both `case_0003` and `case_0004` with `max_diff=0`.

- 2026-07-16 `OLMSmoother2 case_0012 post-leaf boundary`: use
  `refs/conformance/olmsmoother2_case0012_post_leaf_20260716.md` / `.json`.
  For the accepted descriptor `92,841,1,92,842,2`, actual-AEX direct calls and
  the current portable path agree at `e170 c=7`, after `f270` count `1`, and
  after unconditional `f130` count `2`, including both RGBA/weight payloads
  within `1e-6`. Neither side enters `cce0`. This closes the bounded synthetic
  two-leaf polygon state, not the live Windows continuation: accepted live
  evidence still stops after the first vertex. The next proof is a live or
  equivalently bound post-`f130` polygon/cce0 context, not another descriptor,
  leaf-math, or broad PNG adjustment.

- 2026-07-16 `OLMDistanceGradation PF8 mask/stride/field boundary`: use
  `refs/conformance/olmdistancegradation_pf8_mask_stride_field_actual_aex_20260716.md`
  / `.json`. A `17x11` PF8 source-linked mirror with padded input, mask, and
  output rows matches the hash-pinned actual-AEX `FUN_181174760` helper and an
  independent OpenCV 4.5.5 oracle at all `187/187` float32 field words. The
  visible alpha mask is exact, padding is untouched, undersized layouts are
  rejected, and all callback/import/detour gates pass. This closes only the
  PF8 alpha-to-mask, row-stride, and field-helper boundary. It does not enter
  the full `RenderBits` host path, compose, pixel store, SmartRender, or AE,
  and therefore does not promote the current 8bpc `known-red` status. The
  remaining Mac-local integration question is the actual `RenderBits`
  host-world/resize staging between this boundary and the already bounded
  compose/store path.

- 2026-07-16 `OLMRadialBlur reconstructed caller-state witness`: use
  `refs/conformance/olmradialblur_reconstructed_caller_state_witness_20260716.md`
  / `.json`. A bounded `32x1` Mac-local run starts from byte-identical live and
  no-op caller state, enters and returns from the checked-in B150 worker,
  A9D0 scatter, and D80 inverse sampler exactly once, and finishes in `3147`
  live instructions (`768` no-op). Both sampled RGBA float32 word vectors
  match the independent portable sampler exactly. This closes the proposed
  reconstructed-state propagation boundary and supersedes another full-size
  natural-run attempt. It remains bounded binary evidence, not AE exact; the
  missing obligation is Windows-equivalent full-frame host/output binding.

- 2026-07-16 `OLMColorKey Replace + Edge bounded orchestration`: use
  `refs/conformance/olmcolorkey_replace_edge_orchestration_callback_20260716.md`
  / `.json`. A hash-pinned actual-AEX callback run in a synthetic `5x5` host
  world invokes Iterate8 exactly 25 times and observes the unique stage order
  `replacement_write -> thin_boundary -> blur_boundary -> blur_apply`, followed
  by successful suite cleanup. This closes the bounded callback/stage-order
  wiring only. It is not numerical Replace/Thin/Blur evidence and does not
  promote `CLI exact` or `AE exact`; the live next action remains numerical
  output closure and the fail-closed Mac 32bpc cross-host comparison.

- 2026-07-16 `OLMColorKey bounded numerical stages`: use
  `refs/conformance/olmcolorkey_combined_numerical_stage_witness_20260716.md`
  / `.json`. Four separately staged calls into the hash-pinned checked-in AEX
  match independent portable expectations for replacement bytes, the Thin
  boundary seed, all 25 type-3 distance float32 words, and Blur Apply output;
  all eight acceptance gates pass in `10715` guest instructions. The calls use
  deterministic synthetic stage inputs, so this is not a natural same-run
  numerical orchestration witness and not AE exact. Preserve the now-grounded
  stage functions and continue only with same-run output closure or 32bpc
  cross-host validation.

- 2026-07-15 `OLMBlur case_0001 32bpc hash-bound retry`: use
  `refs/conformance/olmblur_32bpc_case0001_hash_bound_recapture_retry_20260715.md`
  / `.json`. The first hash-bound return is `failed_observation_gate`, not
  render evidence: it contains only status JSON and says the loaded AEX was not
  observed by the launcher-PID-only gate. It has no EXR, AE log/result, module
  inventory, or process diagnostics, so it neither proves a wrong AEX nor an
  algorithm mismatch. The retry pauses after live effect/parameter setup,
  binds a nonce-bearing marker PID to the fresh AfterFX launch, and verifies
  the exact loaded AEX path/hash before render continuation. Retry ZIP SHA-256
  is `d178ff2a56eea84cb2b87261f28cd9a285d7936246a16423f45fbf3a3dcb7c53`.
  Keep 32bpc correctness unchanged until the returned pair passes EXR header,
  environment, control, parameter, and raw FLOAT gates.

- 2026-07-15 `OLMBlur case_0001 32bpc Mac/Windows FLOAT comparison`: use
  `refs/conformance/olmblur_32bpc_case0001_mac_ae_comparison_20260715.md` /
  `.json`. Mac AE `26.3x87` Software with installed plug-in SHA-256
  `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`
  has an exact FLOAT control/no-effect comparison (`0/8294400`). Effect-on is
  not comparable: the request and Mac readback use `Number of Repeat=2`, but
  the Windows manifest read back `1`. Its raw outputs differ at `207108`
  `R` values, but that delta is `invalid`, not `known-red` algorithm evidence.
  The Windows return also has no loaded AEX SHA-256, records its color/linear
  fields as unknown `null`, and lacks actual Output Module readback, so the
  verdict is `AE exact refused`. The Mac binary is independently bound to the
  live AE process by exact-path `vmmap` proof. Next action is the hash-pinned
  current-AEX one-process Windows recapture of the same effect/control pair;
  it asserts all five parameter readbacks, removes the effect before the
  control, binds the launched PID and AEX hash, and returns the executed
  contract hashes. The request root is fixed in
  `refs/conformance/olmblur_32bpc_case0001_hash_bound_recapture_request_20260715.md`
  (ZIP SHA-256 `f0dd409e2455ade7a853386ccaafaadb977af162b839cba88a4a3cb43e76fde4`).
  PNG/EXR-derived tuning is forbidden.

- 2026-07-15 `OLMBlur current-plugin 16bpc revalidation`: the installed
  current plug-in SHA-256 is
  `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`.
  Current-plugin 16bpc revalidation is `5/7 AE exact` for
  `case_0001`, `case_0002`, `case_0005`, `case_0006`, and `case_0007`.
  `case_0006` is `AE exact` with output PNG SHA-256
  `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`.
  `case_0003` is Legacy, `max_diff=2` across 20 sign-mixed red samples.
  `case_0004` is Non-Legacy,
  `max_diff=2` across 2 red samples at `(411,258)` and `(458,314)`.
  Both remain unlocalized before the final exported word; current evidence
  does not justify a writer/global-rounding change. Next action is a same-run
  typed pre-store arithmetic/writer/export proof for `case_0003`/`case_0004`.
  Global rounding, writer, and kernel changes are forbidden; do not revive
  old installed-bundle conclusions. Keep `AE exact` limited to the declared
  exact cases above. The unanswered
  `olmblur_case0006_same_run_internal_20260713` request is now `superseded`,
  not `answered`: retain its failed evidence, but do not resend it after the
  current-plugin AE-exact closeout.

- 2026-07-15 `Mac depth-validation execution lanes`: use
  `refs/reports/plugin_orchestration_20260715.md` under "Prepared Mac
  validation lanes". Windows 32bpc FLOAT references now have fail-closed Mac
  execution contracts for OLMBlur, OLMColorKey, OLMDistanceGradation,
  OLMSmoother2 no-key, OLMDirectionalBlur, OLMRadialBlur, OLMKiraKira Mode 2,
  and the isolated OLMToonDilate typed-procedural case. These are prepared
  runners, not completed comparisons, except for the OLMBlur `case_0001`
  comparison scoped in the override above. Exactness remains unchanged until a
  fresh Mac AE effect/control pair binds the installed plug-in binary,
  AE/project/color/output identity, and raw FLOAT32 samples.

- 2026-07-15 `OLMBlur case_0006 current-plugin promotion`: the installed
  current plug-in is SHA-256
  `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`.
  The current-plugin 16bpc revalidation promotes `case_0006` to `AE exact`
  with output SHA-256
  `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`.
  The remaining 16bpc red cases are `case_0003` Legacy (`max_diff=2` across
  20 sign-mixed red samples) and `case_0004` Non-Legacy
  (`max_diff=2` across 2 red samples at `(411,258)` and `(458,314)`).
  Both remain unlocalized before the final exported word; the next proof is a
  same-run typed pre-store arithmetic/writer/export chain for those two cases.
  Do not change global
  rounding, the writer, or the kernel, and do not use old installed-bundle
  conclusions.

- 2026-07-15 `parallel witness hardening`: use
  `refs/reports/plugin_orchestration_20260715.md` for the ordered queue and
  the individual `refs/conformance/*20260715.md` notes for acceptance facts.
  The first DistanceGradation 8bpc typed-boundary attempt returned
  `exact_bind_failure` with no `ae_result_case_0001.json`; the canonical package
  therefore remains the next resend, not answered evidence. Corrected
  fail-closed packages are locally ready for DirectionalBlur row755,
  RadialBlur case_0009 full-frame cells, Smoother2 case_0012 live config,
  KiraKira Mode 3 live Gaussian coefficients, and a low-priority Smoother v1
  16/32bpc expansion probe. ColorKey has nine Windows Software FLOAT EXR
  effect/control pairs; ToonDilate has a separate typed-procedural 32bpc
  contract. Their remaining gate is a bound Mac FLOAT EXR pair and cross-host
  raw-float comparison. Package readiness is not `AE exact` and changes no
  correctness status.

- 2026-07-15 `DistanceGradation local fieldgen boundary`: use
  `refs/conformance/olmdistancegradation_fieldgen_opencv_detour_audit_20260715.md`.
  Existing P1/P1C/P2 detours already execute the current-AEX fieldgen path.
  The full-frame case_0023 inside and outside fields each match the portable
  replay for all `8294400` bytes, and the bound compose triplet is
  `0,32768,32768`. This is hash-pinned local AEX/emulation evidence only; it
  does not replace the pending Windows AE Software typed-boundary return.

- 2026-07-15 `OLMBlur residual-locus split`: use
  `refs/conformance/olmblur_residual_locus_analysis_20260715.md` / `.json`.
  The current Windows export and Mac single-case output differ only at
  `(601,598)`, while the typed actual-AEX witnesses remain `(314,14)` and
  `(29,71)`. No artifact proves a transform between those coordinates, so the
  export residual and historical internal witnesses remain separate lanes.
  Do not infer helper, kernel, or writer changes from the image-only locus.

- 2026-07-15 `OLMBlur case_0006 worker probe return`: use
  `refs/conformance/olmblur_case0006_worker_probe_return_20260715.md`.
  The direct UI Windows AE2025/16bpc/Software export returned `status=ok` and
  produced PNG SHA-256
  `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`,
  byte-identical to both the canonical 2026-06-25 16bpc Software reference and
  the 2026-07-09 current-AEX export. This re-closes Windows export provenance
  for `case_0006`. The worker monitor did not observe an `OLMBlur.aex` worker
  process, and prior CDB attach-only control killed the render, so this is not
  internal worker proof. Do not request another plain Windows export for this
  case; any reopened proof must bind OLMBlur internals without CDB attach side
  effects.

- 2026-07-13 `Windows witness dispatch`: for the six covered lanes, use the
  unified `windows_witness_batch_20260713.zip` generated by
  `scripts/package_windows_witness_batch_20260713.py`. The outer runner
  preflights all jobs before launching AE, requires fresh AE/CDB lifecycle per
  job, applies a bounded per-job timeout, binds only the named return JSON/ZIP
  and required export bytes to the exact request ID, and preserves partial
  evidence without accepting it as complete. Intake must
  include `--request-batch`; partial evidence is rejected unless explicitly
  salvaged with `--allow-partial-evidence` for a narrowed retry.

- 2026-07-13 `OLMBlur case_0006 actual-AEX full-worker`: use
  `refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.md` /
  `refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.json`.
  The hash-pinned 2025 AEX full worker and the portable worker match exactly
  through all observed helper stages, final pre-store floats, and stored
  ARGB16 words at both witnesses `(314,14)` and `(29,71)`; each run observes
  the expected 120 helper calls. Windows PNG matches the AEX/portable RGB at
  `(314,14)` but is `[725,725,725,65535]` against the shared stored `[727,727,727,65535]`
  at `(29,71)`. This is actual-AEX/portable typed worker evidence, not a
  same-run Windows internal trace: the first Windows internal difference is
  not localized. Freeze kernel, source-staging, helper, and store rewrites.
  The next proof is Windows same-run internal/live-context capture plus export
  provenance for `(29,71)`; do not tune from the PNG.

- 2026-07-12 `OLMDistanceGradation 8bpc Mac typed boundary`: use
  `refs/conformance/olmdistancegradation_8bpc_mac_typed_boundary_20260712.md`.
  Mac AE26.3 captured field, compose, PF8 store, and final PNG at the pending
  Windows request coordinate `(397,281)` for `case_0001/0015/0029` under an
  explicitly 8bpc project. All have `field_x=0` and `d_alpha=0`; `case_0001`
  stores hidden RGB `(255,0,0)` and `case_0029` stores `(28,0,238)` under zero
  alpha, while both final PNG pixels are transparent zero. This confirms why
  the pending same-run Windows stage records are necessary: PNG cannot assign
  ownership between compose and AE host alpha handling. No production rule is
  changed from the Mac-only capture.

- 2026-07-12 `OLMDirectionalBlur row755 supplied-runner return`: still
  `exact_bind_failure`, with no algorithm evidence. The supplied
  launch-under-CDB runner reached process termination without ever loading
  `OLMDirectionalBlur.aex`; `lmvm OLMDirectionalBlur` was empty. Its CDB script
  also used nonexistent pseudo-registers `$tA/$tB`. Formal intake correctly
  rejects the return. The replacement no longer depends on CDB module-name
  resolution: JSX pauses after adding the effect, PowerShell binds the
  hash-pinned loaded module and obtains its absolute base, CDB attaches to that
  PID, arms absolute `base+0x38d0/+0x5554` breakpoints using only `$t0..$t9`,
  and only then releases the render. The failed return and superseded request
  are archived; this absolute-base package is the sole NAS active exchange.

- 2026-07-12 `OLMDirectionalBlur row755 first return`: classify the return as
  `exact_bind_failure`, not runtime evidence. AE25 completed the same-run
  Software render, but the Windows execution replaced the supplied
  launch-under-CDB runner with an attach runner. It attached before
  `OLMDirectionalBlur.aex` loaded and attempted unresolved
  `bu OLMDirectionalBlur+0x38d0/+0x5554`, so no stage/provenance records or
  typed row planes exist. The request contract now requires
  `run_alpha_fade_row755.ps1` exactly as supplied and forbids attach-mode
  replacement. The failed return and superseded request are archived; the
  corrected package is the sole NAS active exchange. Intake now resolves a
  unique root-or-nested runtime package manifest and recognizes its top-level
  `request_id`, preventing this failure from being matched against an
  unrelated default package.

- 2026-07-12 `OLMRadialBlur case_0009 live sampler / alpha A/B`: use
  `refs/conformance/olmradialblur_case0009_alpha_ab_20260712.md`. The corrected
  CDB runner hit `OLMRadialBlur+0x5e5b/+0x5e6d` in both
  AE25 and AE26, so module and Zoom sampler liveness are closed. The package
  never armed its requested `+0x5d99` breakpoint and the obsolete
  `+0x7404/+0x7409` predicates did not hit; its typed-plane request remains
  `failed_partial`. The live `(7,0)` sampler cell is RGBA float words
  `3da8cc33 3c706e30 3c706e30 3f7fffff`; Windows truncation explains alpha
  254, but changing only Mac `RenderZoom8` alpha quantization from epsilon to
  truncation was rejected by Mac AE A/B: `(7,0)` stayed 255 and total alpha
  residual expanded to 536,668 pixels. Float-order, simple denominator,
  weighted-alpha, and repeat-raw variants were also inert or worse. The source
  and installed plug-in were restored. Mac debug shows all four target cell
  alpha/valid values as `1.0`; the missing Windows fact is the corresponding
  full-frame final-polar plane at `+0x5d99`. The package template now arms that
  breakpoint. Do not retry a writer-only/global-alpha toggle.

- 2026-07-12 `OLMRadialBlur case_0009 producer narrowing`: static ownership
  now places final-polar alpha in the `context+0x4218` plane written by
  `FUN_18000b150`, before `+0x5d99`; the final normalization loop copies that
  float unchanged and `FUN_180009d80` only bilinearly consumes it. Two Mac AE
  A/Bs reconstructed the AEX forward sampler's float32 accumulation, first
  with the existing epsilon writer and then with truncation. The first was
  bit-for-bit inert (`31119` differing pixels); the second regressed to
  `536668` pixels, and `(7,0)` remained 255 in both. Both were reverted and the
  installed baseline hash restored. The narrow local target is now a one-cell
  replay of `FUN_18000b150`'s center/left/right float accumulation versus the
  current double/FFT alpha convolution; do not revisit forward sampling or
  final quantization.

- 2026-07-12 `OLMRadialBlur target-cell Gaussian A/B`: Mac AE replays replaced
  FFT alpha only for rows `1047..1050`, radii `1075..1100`, covering every
  final-polar cell sampled by `(6,0)/(7,0)/(8,0)/(24,0)`. A fixed-span
  one-sided float32 replay was bit-for-bit inert. Combining it with the AEX
  repeat-border float32 forward sampler was also inert: all four `(7,0)` cells
  stayed exactly `1.0` and the case remained `31119` differing pixels. Both
  changes were removed and the baseline binary restored. This rejects generic
  FFT precision and fixed-span accumulation; the remaining live input is
  `FUN_18000b150`'s per-cell `fVar28` scale/span plane and its derived left/right
  table indices.

- 2026-07-12 `OLMRadialBlur bounded cell-set closeout`: an exhaustive
  angle/radius offset sweep over `-3..+3` found no exact top-row classifier.
  Candidates that hit all Windows-254 targets `[6,7,12]` introduce at least
  eight false positives, so coordinate bias remains forbidden. The local
  RadialBlur package now adds a same-run `+0xb150` producer hook for rows
  `1047/1048`, radii `1095..1097`, capturing the scale plane, source alpha,
  row partition, spans, and plane pointers before the existing final-plane
  hooks. It passes package smoke but remains unstaged until the active
  DirectionalBlur exchange finishes.

- 2026-07-12 `OLMRadialBlur case_0009 CDB module-wait retry`: the first
  full-frame post-normalization return is `failed_partial`, not algorithm
  evidence. AE rendered the expected case and loaded `OLMRadialBlur.aex`, but
  the runner waited for `RadialBlur.aex`; CDB therefore reached process exit
  before arming hooks and reported `No runnable debuggees`. The runner now
  waits for and lists `OLMRadialBlur`, package smoke rejects the old spelling,
  and the corrected package is the sole NAS active exchange. Do not interpret
  the zero hook count as proof that `+0x5d99` is outside the render path.

### Emulator versus Windows boundary

- Local AEX/Unicorn/emulation evidence may close deterministic leaf semantics:
  constants, branches, loop bounds, address arithmetic, typed intermediate
  buffers, and portable-core equivalence to an actual AEX function.
- It may not by itself close AE host state, worker scheduling in the real
  Windows process, loaded-binary identity, color-management/export behavior,
  or Windows-versus-Mac final effect output. Those require a hash-pinned
  Windows AE Software capture (and, for final conformance, the matching Mac AE
  capture).
- Ask Windows only for the first unresolved in-situ boundary after local
  emulation has exhausted deterministic evidence. Do not request broad PNG/EXR
  sets when one typed witness can decide the branch.

- 2026-07-12 `32bpc AE26.3 FLOAT EXR acceptance`: use
  `refs/conformance/ae26_3_float_exr_acceptance_20260712.md`. Incoming
  OLMBlur/ColorKey/ToonDilate evidence must bind AE 26.3, 32bpc, linear-light
  off, uncompressed FLOAT RGBA EXRs, Windows/reference input, Mac no-effect,
  Windows effect-on, and Mac effect-on artifacts, dimensions, hashes, loaded
  Windows AEX hash, and loaded Mac plug-in hash. Host-input conversion, Mac
  effect delta, and Windows-versus-Mac effect output are compared separately;
  missing controls or either effect output fail closed.

- 2026-07-12 `RadialBlur case_0009 typed return readiness`: use
  `scripts/compare_olmradialblur_case0009_fullframe_postnorm_typed.py`. The
  comparator rejects incomplete returns and identifies the first difference
  in inverse sampler, cell selection, bilinear weights, accum, denom, valid,
  or final order at `(7,0)/(8,0)/(24,0)`. It is readiness tooling, not new
  RadialBlur evidence.

- 2026-07-12 `Smoother2 0012 typed return readiness`: use
  `refs/scripts/analyze_olmsmoother2_0012_typed_bind_read.py`. Acceptance now
  requires same-run module/hook identity, live fifth-argument/config binding,
  gamma/key context, and complete typed producer/class/polygon/cce0/writer
  stages. The existing request/failed-partial state is rejected and cannot be
  promoted from local c280->cce0 replay alone.

- 2026-07-12 `Smoother2 Mac AE host trace`: use
  `refs/conformance/olmsmoother2_ae_host_trace_0012_20260712.md`. The target
  `(91,841)` now has a direct Mac AE trace through input/setup/class, polygon,
  and orchestrator. The local host produces alpha `0.3549245` and final
  `[32,32,32,91]`; this does not explain the Windows `[0,0,0,0]` alpha. Keep
  the Windows same-run class/config witness as the only promotion path and do
  not change global append or writeback rules from this trace.

- 2026-07-12 `Smoother2 input/alpha provenance A/B`: use
  `refs/conformance/olmsmoother2_input_alpha_provenance_20260712.md`. Changing
  the input artifact or AE alpha mode can make the target pixel match while
  worsening the full frame (`max_diff` up to 254). No alpha mode is promoted;
  future evidence must bind the exact input artifact, alpha mode, parameters,
  and complete output in one case.

- 2026-07-12 `OLMDirectionalBlur UCRT Gaussian fix`: use
  `refs/conformance/dblur_ucrt_gaussian_fix_20260712.md`. The accepted x64
  Windows return proves that double-exp-then-float reproduces all `336/336`
  UCRT Gaussian words, while macOS expf misses two by one ULP. The shared core,
  CLI, and Mac fallback now use that model. A depth/alpha-correct Mac AE rerun
  improves Alpha Fade from 563 to 226 differing pixels; the remaining max-3
  family is confined to `x=1308` and is still known-red. Continue at the first
  divergent prepass/scatter/rotate-back boundary, not with PNG tuning.

- 2026-07-12 `OLMDirectionalBlur Alpha Fade row-755 return`: use
  `refs/conformance/olmdirectionalblur_row755_return_20260712_exact_bind_failure.md`.
  The latest Windows run reached the exact pre-normalization stage and emitted
  valid same-run origin provenance, but all three large writemem artifacts were
  absent. The next retry is chunked capture with exact-size combination; do not
  promote the partial return.

- 2026-07-12 `OLMDirectionalBlur Alpha Fade stage audit`: use
  `refs/conformance/dblur_alpha_fade_stage_residual_20260712.md`. Bounded AEX
  leaf/rowdriver fixtures still pass and the current raw PF worlds are valid,
  but a full 2206x2206 AEX run exhausted its instruction budget before
  yielding a live intermediate. This does not prove full-frame stage equality.
  The next proof is one affected `(1308,184)` prepass/scatter call with before
  and after destination, denominator, and alpha buffers; do not request broad
  PNGs or change production math from the column shape.

- 2026-07-12 `OLMDirectionalBlur Alpha Fade bounded row`: use
  `refs/conformance/dblur_alpha_fade_witness_row_20260712.md`. Host residual
  `(1308,184..517)` maps exactly to internal row `(747..1080,755)`. A bounded
  actual-AEX `FUN_1800038d0` run using the accepted UCRT tables matches the
  portable destination, denominator, and alpha buffers byte-for-byte over the
  full 2206-pixel row. Prepass and scatter are closed for this witness. The
  remaining boundary is normalization, zero-fraction rotate-back, or PF8
  quantization; production remains frozen until one differs exactly.

- 2026-07-12 `OLMDirectionalBlur Alpha Fade in-situ row request`: local direct
  AEX normalization, zero-fraction rotate-back, and PF8 packing also reproduce
  the portable result, while the captured Windows full render retains the same
  226-pixel difference. Scheduler coverage matches the port and row 755 is a
  normal `[748,816)` chunk member. The only missing fact is the in-situ row 755
  destination/denominator/alpha state after the real Windows worker schedule
  and before normalization. The fail-closed request is
  `refs/runtime_trace_packages/olmdirectionalblur_alpha_fade_fullrender_row755_chunked_capture_20260712.zip`;
  keep it behind the currently active RadialBlur exchange.

- 2026-07-12 `OLMBlur 32bpc Mac adapter audit`: use
  `refs/conformance/olmblur_32bpc_mac_adapter_conformance_audit_20260712.md`.
  The existing Mac adapters route Non-Legacy and Legacy float worlds to their
  exact portable workers with the correct PF_PixelFloat channel order,
  rowbytes, alpha ownership, and failure handling. Complete actual-AEX worker
  fixtures remain exact at `7/7` Non-Legacy and `5/5` Legacy. This is
  binary-grounded adapter evidence, not cross-host `AE exact`; the remaining
  lane is hash-pinned AE host/reference validation.

- 2026-07-12 `OLMColorKey / OLMToonDilate 32bpc host paths`: use
  `refs/conformance/olmcolorkey_toondilate_32bpc_mac_audit_20260712.md`. Their
  existing `out_flags2` value is now expressed with the equivalent SDK names
  for Smart Render, float-color awareness, and flattened sequence data. The
  32bpc production path is `PF_Cmd_SMART_RENDER` with explicit `bitdepth=32`;
  classic `PF_Cmd_RENDER` remains an 8/16bpc path, matching the AE SDK sample
  contract. Do not add a guessed classic-render float detector. No pixel math
  changed and no cross-host `AE exact` claim is made.

- 2026-07-12 `Mac 32bpc effect/control collection`: use
  `refs/conformance/mac_32bpc_effect_control_batch_20260712.md`. The focused
  ColorKey/ToonDilate Mac batch now records validated FLOAT EXR effect-on and
  no-effect artifacts as an inseparable pair per case. This removes the local
  candidate/control collection gap, but does not replace the pending AE 26.3
  Windows FLOAT EXR, no-effect control, or loaded-AEX hash requirements.

- 2026-07-12 `OLMDirectionalBlur row755 chunked return`: use
  `refs/conformance/olmdirectionalblur_row755_chunked_ae_pause_failure_20260712.md`.
  The return is `exact_bind_failure` before JSX pause/CDB attach and contains
  no row evidence. The retry runner now explicitly quotes the JSX path and
  uses `AfterFX -m -r`; do not count the failed return as answered.

- 2026-07-12 `OLMSmoother2 c280 -> cce0 replay`: use
  `refs/conformance/olmsmoother2_c280_cce0_replay_20260712.md`. Two local
  actual-AEX fixtures agree with the current port through descriptor,
  producer, normalization, and independent cce0 accumulation boundaries. The
  live five-argument c280 binding plus gamma/key/config and final host packing
  remain outside this proof; production fallback changes remain forbidden.

- 2026-07-12 `OLMKiraKira Mode 3/4 narrowing`: use
  `refs/conformance/olmkirakira_mode34_narrowing_20260712.md`. Static evidence
  identifies Mode 3 as a GaussianBlur branch and Mode 4 as an inline
  recursive/separable branch, but does not recover their complete parameter or
  recurrence contracts. Both stay explicitly on the existing Mode 2 scaffold
  until those facts land; this is a guarded placeholder, not compatibility.
  The first 2026-07-13 live-Gaussian returns stopped at AE readiness. A later
  desktop run reached the live first kernel entry with the requested arguments,
  but a timestamped CDB log path and nested dynamic return breakpoint prevented
  the return capture. The fixed v4 package pre-arms the pinned callsite return;
  it still must return all 21 words before classifying the implementation.

- 2026-07-12 `OLMKiraKira hotspot transform provenance`: use
  `refs/conformance/olmkirakira_hotspot_transform_provenance_20260712.md`.
  The traced/current compose value 144 cannot become canonical 131 through
  premultiply at alpha 1 or standard linear-light color management (which
  predicts 190). Keep math frozen. The live lane is reference generation,
  witness placement, or an unobserved endgame/host path; no host transform is
  presently proven.

- 2026-07-12 `OLMKiraKira Channel 2 seed luma`: use
  `refs/conformance/olmkirakira_channel2_bt709_cpp_fix_20260712.md`. Windows
  runtime already fixed Channel 2 at BT.709, but the C++ CLI and Mac plug-in
  had retained BT.601 after only the Python witness path was corrected. Both
  C++ paths now use `0.2126/0.7152/0.0722`; the focused constant/runtime smoke
  passes and the universal arm64/x86_64 plug-in builds. This closes only seed
  luma. Merge compose, final quantization, and remaining modes are not
  promoted and stay in their existing evidence lanes.

- 2026-07-12 `OLMDistanceGradation 8bpc current binary`: use
  `refs/conformance/olmdistancegradation_8bpc_current_binary_reconstruction_20260712.md`.
  The depth-correct current Mac binary remains `0/29 AE exact`; no defensible
  source-only fix was found and the historical `29/29` artifact remains
  excluded. A narrow hash-pinned same-run field/compose/store witness request
  is prepared at
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip`.
  Its 2026-07-13 Windows return is fail-closed: CDB emitted none of the three
  required `(397,281)` typed markers and supplied no shared run/AEX identity.
  The subsequent liveness probe returned five zero counts, but its AE result
  proves the nominal 8bpc request actually rendered at 32bpc because the
  packaged runner ignored `comp.bpc`. Use
  `refs/conformance/olmdistancegradation_8bpc_hook_liveness_depth_mismatch_20260713.md`.
  A replacement request now requires AE-reported 8bpc and compares only the
  PF8 callback against a PF32 negative control. Do not tune the 8bpc port
  until that depth gate is positive.

- 2026-07-12 `OLMDistanceGradation 16bpc residual families`: use
  `refs/conformance/olmdistancegradation_16bpc_residual_family_classifier_20260712.md`.
  Preserve the seven exact controls. Treat Layer/no-bg `0012/0013/0014/0016`,
  broad max-2 `0024..0027`, and outlier `0028` as three independent witness
  families. In particular, `0028` is a max-3080 source/field/premultiply lane
  and must not be folded into the max-2 store/export family.

- 2026-07-11 `OLMDistanceGradation OpenCV/PF16 boundary`: use
  `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`.
  Actual-AEX field values plus the real OpenCV 4.5.5 sidecar ground a single
  float32 reciprocal-multiply normalization followed by PF16
  round-to-nearest-even field-world conversion. The current Mac AE 16bpc
  extended batch is now `7/16 AE exact`; `case_0010/0011` are newly exact and
  the prior five exact cases remain exact. The same audit corrects the 8bpc
  current state: after teaching both JSX runners to fall back to `comp.bpc`, a
  depth-correct current-binary batch is `0/29` exact. The historical `29/29`
  candidates have no loaded Mac plug-in hash and two retained June 18 binaries
  fail fresh reruns. Treat 8bpc as current-binary known-red; do not cite the
  unbound historical artifact as current `AE exact`.

- 2026-07-11 `OLMSmoother2 local full-chain differential`: use
  `refs/conformance/olmsmoother2_fullchain_local_diff_20260711.md`. Actual AEX
  and current-port helpers agree for the identical-memory c=2 witness and c=4
  suppressing control through direct descriptor, append, vertex/weight,
  cardinal descriptor, and normalization boundaries. This narrows the active
  unknown to the live five-argument `c280` host/config binding and the
  gamma/key/config context needed by `cce0`; it is not Windows AE truth and
  authorizes no production fallback change.

- 2026-07-11 `OLMKiraKira Blur Mode 1 dispatch`: use
  `refs/conformance/olmkirakira_blur_mode1_dispatch_20260711.md`. Static AEX
  control flow is now reflected in CLI and Mac adapters: Mode 1 uses one box
  pass, Mode 2 uses three, and an explicit CLI falloff remains a diagnostic
  override. Modes 3/4 retain the old three-pass placeholder and are still
  unimplemented; no AE-exact, hotspot, gain, or quantization claim is made.

- 2026-07-11 `OLMDirectionalBlur Alpha Fade host boundary`: use
  `refs/conformance/dblur_alpha_host_boundary_20260711.md`. The requested
  same-run capture accepted the exact 2025 AEX hash and complete 1920x1080 PF
  input/output worlds. It proves half-up host unpremultiplication into the AEX
  and half-up premultiplication on export, both byte-exact. The old June 19 PNG
  differs from the current hash-pinned Windows render at 234845 values and is
  no longer a current-AEX oracle. Against the corrected reference, current Mac
  AE is still known-red at `max=3`, 980 values / 563 pixels. A double-exp probe
  removes all 562 arm64-versus-macOS-x86_64 raw differences, proving a platform
  `expf` split, but x86_64 still differs from Windows at 468 values / 226 pixels
  confined to `x=1308`. Next capture the UCRT `expf` table words for `n=96/240`
  and replay them; do not promote double-exp or tune pixels from the PNG.

- 2026-07-11 `OLMDirectionalBlur front-only 8bpc exact`: the portable shared
  core now reproduces the actual-AEX full-entry raw ARGB8 SHA-256 for
  `db_angle0_strength_sweep_small`. The former 523-pixel max-1 residual was a
  stage mismatch: raw plug-in `[RGB=247,A=254]` versus AE-rendered PNG
  `[RGB=246,A=254]`; a host premultiply model closes all 1,569 channel bytes,
  and no darkening was added to the plug-in. Actual Mac AE 26.3 Software
  renders are `max_diff=0` for both `db_angle0_strength_sweep_small` and
  `db_angle0_no_tail_no_size`. Use
  `refs/conformance/dblur_frontonly_mac_ae_exact_20260711.md`. This promotes
  only the declared front-only/no-variation/no-fade/no-tail/no-back/no-noise
  8bpc slice; Alpha Fade, Size Variation, Sharp Tail, Back, Noise, and 16/32bpc
  remain open.

- 2026-07-11 `OLMBlur 32bpc Mac candidate`: the latest Mac plug-in renders all
  seven focused cases as uncompressed FLOAT32 RGBA EXR. Cross-host no-effect
  controls are byte-exact for cases `0001..0004`; cases `0005..0007` retain a
  small PNG-input conversion difference. Effect-on outputs differ for all
  seven, but both 32bpc complete workers replay actual AEX fixtures byte-exact
  at every declared parameter tuple. The retained Windows return omits the
  loaded AEX hash, so version split remains unresolved. Use
  `refs/conformance/olmblur_32bpc_mac_ae_candidate_20260711.md`; next action is
  hash-pinned current-AEX 8/32bpc recapture, not PNG/EXR tuning.

- 2026-07-11 `OLMBlur Legacy center-copy closeout`: decomp proves the
  `FUN_1800014f0/FUN_180001ea0` `all_same` branch copies the current center
  source RGB; carry RGB is comparison state only. Correcting the portable
  helper preserves all prior helper/8bpc/16bpc fixtures and makes all three
  32bpc Legacy complete-worker fixtures exact. Formal Mac AE now has 16bpc
  `case_0001..0007` all `max_diff=0`, so the declared OLMBlur 16bpc cell is
  `AE exact`. 8bpc case 0007 is also exact against both retained families;
  case 0003 and canonical-family provenance remain open. Use
  `refs/conformance/olmblur_legacy_center_copy_fix_20260711.md`.

- 2026-07-11 `OLMBlur complete-worker Mac AE update`: 8bpc Legacy
  `FUN_180007300` and 16bpc Legacy `FUN_180005f20` portable cores now replay
  actual-AEX complete-buffer fixtures byte-exact and are wired through narrow
  Mac adapters. Formal 16bpc Mac AE is exact for cases `0001..0006`; case
  `0007` remains `max=16` at 18 pixels. Formal 8bpc against the retained
  AE25.2 family is exact for `0001/0002/0004/0005/0006`; Legacy `0003` is
  `max=1` and `0007` is `max=16` at 18 pixels. Use
  `refs/conformance/olmblur_8bpc_worker_mac_ae_20260711.md` and
  `refs/conformance/olmblur_16bpc_worker_mac_ae_20260711.md`. Because the
  complete worker cores are exact, the next allowed action for these residuals
  is host-boundary/reference-provenance proof, not kernel tuning.

- 2026-07-10 `ToonDilate Mac 32bpc candidates`: live Mac AE `26.3x87`
  rendered all three declared cases as uncompressed FLOAT `A,B,G,R` EXRs;
  the fail-closed candidate-index validator accepts `3/3`. Use
  `refs/conformance/olmtoondilate_32bpc_mac_candidates_20260710.md`. The
  current registered template is `OLM EXR 32 Float`; the name ending in `2`
  is invalid. This completes the Mac candidate side only. Cross-host no-op RGB
  drift still prevents a 32bpc `AE exact` verdict.
- 2026-07-10 `OLMBlur portable helper exact`: actual AEX
  `FUN_180001000/FUN_180001980` and `core/olmblur_helper.cpp` are byte exact
  across six typed fixtures covering basic traversal, inactive-center copy,
  directional flag break, edge/radius clamp, zero denominator, and nonzero
  offset. The AEX includes the active center with `weights[0]`; an earlier
  prose audit saying “center excluded” was rejected by decomp plus fixture
  output. Helper status is `portable-core-ready`; full worker
  `FUN_180005f20` PF Handle/layout remains blocked, so this is not case_0006
  full-entry or `AE exact`.
- 2026-07-10 `OLMBlur shared-core broad integration rejected`: the portable
  `FUN_180001000/FUN_180001980` core remains byte-exact for its six typed
  function fixtures, but substituting it for all Mac non-Legacy horizontal /
  vertical calls is not grounded by `FUN_180005f20`, whose audited branch uses
  the differently labelled `FUN_1800014f0/FUN_180001ea0` family. Formal 8bpc
  comparison with depth explicitly fixed to 8 produced red-channel maxima
  `59/59/14/58` in case_0001..0004 against normalized references, but these
  outputs are identical before/after the integration and match the old
  20260604 drift family; only case_0006 moved by one red value. The wiring was
  removed because the callsite mapping is unproven and the 16bpc run gained an
  extra residual, not because of the pre-existing 8bpc family. Use
  `refs/conformance/olmblur_shared_core_mac_ae_case0006_20260710.md`. Preserve
  the standalone core evidence, but do not integrate it again until the exact
  full-worker callsite/ABI/branch alias is proven. Current-AEX 8bpc Windows
  references must pin the AEX SHA-256 before selecting the canonical family.
- 2026-07-11 `OLMBlur 8bpc reference/AEX provenance`: use
  `refs/conformance/olmblur_8bpc_reference_aex_provenance_audit_20260711.md`.
  The current Mac maxima `59/59/14/58/0/0/1` reproduce the old Windows AE
  25.2 reference-family shape, while the retained Windows AE 26.2 normalized
  family and its historical Mac candidate are 7/7 byte-identical. Both
  manifests omit the loaded AEX hash. The local helper fixtures are pinned to
  official 2025 AEX SHA-256 `f0611785...e96e5b`, but no existing reference
  proves it used that binary. Treat canonical 8bpc selection as blocked on a
  hash-pinned current-AEX Software recapture; do not tune either family into
  the implementation by assumption.
- 2026-07-11 `OLMBlur hash-pinned 8bpc recapture ready`: project-local package
  `refs/reference_requests/olmblur_windows_software_8bpc_aex_canonical_recapture_20260711.zip`
  gates rendering on installed `OLMBlur.aex` SHA-256
  `f0611785...e96e5b`, records path/size/time/hash, forces Software and 8bpc,
  renders all seven normalized cases plus an effect-disabled control, and
  fails closed on hash or render mismatch. Package SHA-256 is
  `2e5473ace6edb38e644141bdab04f5abc5f4c66200dcb6fd2e068cd5706cee84`.
  It is prepared but not staged;
  do not overwrite the active RadialBlur NAS request.
- 2026-07-11 `OLMBlur full-worker helper fixtures`: actual 2025 AEX functions
  `FUN_1800014f0/FUN_180001ea0` now replay byte-exact against six portable C++
  fixtures covering offsets, partial passes, flag breaks, asymmetric inactive
  behavior, and large radii. Use
  `refs/conformance/olmblur_fullworker_helper_20260711.md` and
  `refs/scripts/smoke_olmblur_fullworker_helper.py`. This grounds the helper
  pair only. Keep Mac source unchanged until `FUN_180005f20` callsites map the
  `1000/1980` and `14f0/1ea0` pairs to exact Legacy/Bias parameter branches;
  do not infer the mapping from function names.
- 2026-07-11 `OLMBlur full-worker branch map`: use
  `refs/conformance/olmblur_fullworker_branch_map_20260711.md`. Dispatch
  `FUN_18000a380` proves `1000/1980` are Non-Legacy and `14f0/1ea0` are Legacy
  for 8/16/32bpc; Bias `1` is horizontal-then-vertical and Bias `2` reverses
  it. Mac direction order matches, but its full-plane helper signature does
  not represent the AEX's six subpass offsets and plane swaps. The next local
  implementation boundary is full-worker orchestration against an actual-AEX
  full-entry fixture, not another direct helper substitution.
- 2026-07-11 `OLMBlur 8bpc Non-Legacy worker exact`: portable orchestration for
  `FUN_180003710` now includes A/R/G/B staging, six row/column chunks,
  plane swaps, direction order, repeat decay, weights/radius, and 8bpc
  writeback. Two complete-buffer fixtures (basic and large-radius/reverse
  direction) replay byte-exact against the actual 2025 AEX. Use
  `refs/conformance/olmblur_worker_orchestration_20260711.md` and
  `refs/scripts/smoke_olmblur_worker_orchestration.py`. This grounds only the
  8bpc Non-Legacy worker; Mac integration must remain depth/mode-limited and
  pass AE host regression before any `AE exact` claim.
- 2026-07-11 `OLMBlur 8bpc worker Mac AE`: the depth/mode-limited adapter is
  installed and the formal Mac AE batch was rerun with depth explicitly fixed
  to 8. All five Non-Legacy cases `0001/0002/0004/0005/0006` are byte-exact
  against the retained Windows AE25.2 family; normalized AE26.2 remains split
  at `59/59/58` for 0001/0002/0004 while 0005/0006 are exact. Legacy cases are
  outside the adapter and remain red. Use
  `refs/conformance/olmblur_8bpc_worker_mac_ae_20260711.md`. Do not select the
  canonical family until the prepared current-AEX hash-pinned Windows recapture
  returns.
- 2026-07-11 `OLMBlur 32bpc Non-Legacy worker exact`: portable
  `FUN_180004b80` orchestration now covers raw float A/R/G/B staging, active
  alpha semantics, six subpasses/plane swaps, repeat decay/weights, and
  float-preserving RGB writeback. Basic and large-radius reverse-direction
  complete buffers replay byte-exact against the actual 2025 AEX; no EXR was
  used as oracle. Use `refs/conformance/olmblur_worker32_nonlegacy_20260711.md`
  and `refs/scripts/smoke_olmblur_worker32_nonlegacy.py`. This is binary core
  proof, not cross-host `AE exact` until the float host/no-effect policy is
  satisfied.
- 2026-07-11 `OLMBlur 32bpc Non-Legacy Mac integration`: the Mac adapter now
  packs/unpacks PF_PixelFloat A/R/G/B with rowbytes awareness, preserves alpha,
  calls the exact 32bpc worker only for Non-Legacy, and catches allocation
  failure at the host boundary. 8bpc and 32bpc fixture smokes plus universal
  Debug build (`x86_64 arm64`) pass. The installed MediaCore bundle contains
  this adapter. No cross-host exact claim is made before a float-preserving
  Mac candidate/no-effect comparison under the declared 32bpc policy.
- 2026-07-11 `OLMBlur 16bpc Non-Legacy worker exact`: corrected entry
  `FUN_180002280` stages PF_Pixel16 A/R/G/B, executes the exact Non-Legacy
  helper pair in six subpasses with decay/weights, and applies the AEX
  `+0.5` truncating/clamped writer. Basic and large-radius reverse-direction
  complete buffers replay byte-exact against actual AEX. Use
  `refs/conformance/olmblur_worker16_nonlegacy_complete_worker_20260711.md`
  and `refs/scripts/smoke_olmblur_worker16_nonlegacy.py`. Earlier use of
  `FUN_180005f20` for this lane was rejected because that entry is Legacy.
- 2026-07-11 `OLMBlur 8bpc Legacy worker exact`: portable `FUN_180007300`
  uses the exact `14f0/1ea0` helper pair, centered weights, six subpasses /
  plane swaps, Legacy repeat/smoothness rules, and 8bpc writer. Three complete
  buffers replay byte-exact against actual AEX, including a reverse-direction
  mixed-alpha fixture with 69 zero-alpha pixels and partial alpha
  `32/96/160/224`. Use `refs/conformance/olmblur_worker8_legacy_20260711.md`
  and `refs/scripts/smoke_olmblur_worker8_legacy.py`.
- 2026-07-10 `DirectionalBlur angle-0 rowdriver classifier`: local actual-AEX
  `FUN_1800038d0` execution on case_0001 source row 169 classifies strip
  `x=487..494` and control `(579,169)` as reachable. All records have valid
  source, positive component, `param_11=0.629629612`, and span `1064`; neither
  source-range exclusion nor `span<=1` explains the zero-RGB Mac result. Use
  `refs/conformance/olmdirectionalblur_case0001_row169_typed_classifier_20260710.md`.
  Keep Mac source frozen; the next local boundary is post-scatter accumulation
  and writeback, not coefficient or PNG tuning.
- 2026-07-10 `DirectionalBlur row169 scatter boundary`: actual-AEX capture at
  source `(959,169)` shows both target `(494,169)` and control `(579,169)` are
  written by `FUN_1800013e0` with RGB zero and valid/denominator `1`; the same
  values remain when `FUN_1800038d0` returns. This rules out non-reachability,
  alternate buffer ownership, and a later rowdriver erase for this boundary.
  Use
  `refs/conformance/olmdirectionalblur_case0001_row169_boundary_capture_20260710.md`.
  Keep coefficient/PNG tuning frozen. The next proof boundary is why the
  Windows reference's nonzero red differs at source/staging or final source
  modelling; final stored bytes remain outside this rowdriver-only probe.
- 2026-07-10 `DirectionalBlur source/staging witness`: the packaged
  before-effects input and actual-AEX rowdriver both show source `(959,169)` as
  zero RGB, and the observed staging records for `(494,169)` / `(579,169)`
  remain zero through rowdriver return. Therefore the Windows reference reds
  `164` / `25` cannot be attributed to that single source under the current
  staging model. Use
  `refs/conformance/dblur_source_staging_witness_20260710.md`. The exact next
  boundary is the real helper call that writes either target, with contributing
  source coordinate, B pre/post floats, and final host-store bytes in one run;
  coefficient tuning remains forbidden.
- 2026-07-11 `DirectionalBlur target-writer capture`: actual AEX rowdriver
  records all helper contributors that overlap the two targets. `(494,169)`
  receives 465 calls from source x `495..959`; `(579,169)` receives 380 from
  `580..959`. All 845 observed contributors and target B states remain zero
  RGB with denominator/valid `1`, direction `1`, span `1064`. Use
  `refs/conformance/dblur_target_writer_capture_20260711.md`. This closes the
  local contributor/scatter explanation for the Windows red values. The next
  exact boundary is host output storage after rowdriver normalization /
  rotate-back; do not modify coefficients or source selection from this local
  witness alone.
- 2026-07-11 `DirectionalBlur rotate-back ownership`: use
  `refs/conformance/dblur_rotateback_output_20260711.md`. At `0x180005628`,
  `FUN_180001ec0` receives source buffer B in `RCX`, destination buffer A in
  `RDX`, width/height in `R8D/R9D`, and stack angle; afterward A is published
  at `param_6+0x8090`. This is still an internal float buffer, not the host
  world. The next local fixture must implement the grounded PF Iterate8
  populate/output callbacks and param fields through `+0x80a4`; do not invent
  an external host-writer breakpoint.
- 2026-07-11 `DirectionalBlur 8bpc host callbacks`: use
  `refs/conformance/dblur_fullrender_host_fixture_20260711.md`. Actual AEX
  populate `0x180006980` and output `0x180006b30` callbacks match the local
  model, including final byte A/R/G/B stores; authoritative objdump shows
  `movb` where the checked-in disassembly is stale. The exact 960x540 source,
  `PF_Cmd_RENDER=0x18`, depth dispatch, checkout callbacks, and descriptor now
  reach `FUN_180004a20` and the real PF Iterate8 suite. The next local blocker
  is the wrapper stack ABI at `0x1800067c5` for callback/refcon/source/dest
  worlds; SmartRender selection and callback byte semantics are no longer the
  blocker.
- 2026-07-10 `Smoother2 local producer leaf witness`: actual AEX execution of
  `FUN_18000e170`, `FUN_18000f270`, and `FUN_18000e3a0` now fixes the local
  branch shape at legacy `(91,841)`. Producer bytes `0,1,0` yield `c=2`,
  `f270=1`, `e3a0=1`, and one chain append; control `0,0,1` yields `c=4` and
  suppresses the wrapper append. Use
  `refs/conformance/olmsmoother2_typed_witness_20260710.md`. This is local AEX
  binary evidence, not Windows truth, Mac AE exactness, or permission to alter
  the global class plane.
- 2026-07-10 `Smoother2 0012 strict typed request ready`: project-local package
  `refs/runtime_trace_packages/olm_smoother2_current_aex_0012_typed_bind_read_20260710.zip`
  contains the exact case fixture, AE runner, CDB hooks/parser, complete-trace
  and missing-field parser tests, and a runtime package manifest. `answered`
  is reachable only when idx105, descriptor, class bytes, e170/f270/e3a0,
  polygon, cce0, and final writer share one run; all missing fields fail closed
  as `exact_bind_failure`. Package SHA-256 is
  `a1e78fc99941717e31a96ff23c345274663a909efc72901758ca749bf12315d5`.
  It is pending behind the already staged RadialBlur
  request and must not overwrite `$OLM_EXCHANGE_ROOT/new`.
- 2026-07-10 `RadialBlur full-frame confirmation staged`: the one-shot package
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_case0009_fullframe_postnorm_typed_20260710.zip`
  is the sole item in `$OLM_EXCHANGE_ROOT/new` with matching SHA-256
  `a4bc1b52fa78130f5dc2a2c1b214a674a7315c761956b4d6b2439887f8e60191`.
  It recalculates actual inverse indices in the live full-frame run and captures
  paired accum/denom/valid/final cells for `(7,0)`, `(8,0)`, and `(24,0)`.
  Do not run or resend older RadialBlur final-plane packages.
- 2026-07-10 `OLMBlur CPU fixture readiness`: real AEX helpers
  `FUN_180001000` and `FUN_180001980` execute import-free and retain typed
  output hashes in `core/olmblur_cpu_fixture_readiness.json`. Portable replay
  remains explicitly blocked on the disassembly-backed traversal/boundary
  contract and full-entry PF Handle layout. This is useful binary readiness,
  not an exact fixture and not permission to encode observed outputs.
- 2026-07-10 `DistanceGradation shared-core Mac AE validation`: use
  `refs/conformance/olmdistancegradation_shared_core_mac_ae_case0023_20260710.md`.
  After installing the shared-core build and restarting AE `26.3x87`, 16bpc
  case_0023 is `AE exact` for both Use Background Color on and off
  (`max_diff=0`, `nonzero_px=0`). This promotes only that declared case/variant
  slice; the complete OLMDistanceGradation depth cell and release gate remain
  open.
- 2026-07-10 `DistanceGradation compose exact-address local witness`: actual
  `DistanceGradation.aex` compose executed under Unicorn for `(6,40)` and
  `(901,394)` and produced PF16 alpha words `3268` / `9876`, matching accepted
  Windows stores in 272 total instructions. Use
  `refs/conformance/olmdg_compose_exact_address_witness_20260710.md`. This
  grounds compose/address arithmetic for supplied field words, not Windows
  field production. The remaining blocker is the Windows field-world base,
  layout, and exact `RCX` words; do not infer a global pack/rounding change.
- 2026-07-11 `DistanceGradation strict same-run request ready`: package
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_current_aex_same_run_exact_address_20260711.zip`
  fingerprints the live worker block at `RBX+0xB8/+0xBC` as case0010
  `(63,82)` or case0011 `(348,0)`, tags every stage in CDB, rebinds output base
  at each entry, derives XY from output address, and reads all field/source /
  compose/writer values from live state. Unknown fingerprints use a DEAD tag
  and fail closed; ordering, JSX stdout, external run-specific addresses, and
  hardcoded writer words are rejected by smoke. It is pending but not staged
  over the active RadialBlur NAS request. Package SHA-256 is
  `19c0d4c4974eb68c30302635803dd20c6dd985a1e92837a463ebe83d15905f6f`.
- 2026-07-10 `DistanceGradation fixture provenance`: the compose refcon is now
  a relocatable `binary-built` block rather than a dump containing emulator
  heap addresses. Source/field world pointers are zeroed and represented as
  explicit `+0x00/+0x08` relocations; scalar range `+0x90:+0xd4` remains tied
  to the AEX callback layout and case manifest. The verifier requires
  relocations for binary-built blocks. This is stronger deterministic
  provenance, not a claim of Windows runtime capture or `AE exact`.
- 2026-07-10 `Mac 32bpc candidate fail-close`: the candidate batch now records
  case ID, canonical parameter SHA-256, artifact SHA-256, and depth, and the
  validator rejects non-FLOAT, non-RGBA, compressed, malformed-scanline,
  hash-mismatched, or implicit-exact candidates. Dry/non-Mac runs emit a
  readiness artifact instead of a render claim. This improves ColorKey and
  ToonDilate 32bpc host evidence only; the cross-host no-op split still blocks
  algorithm attribution and neither plug-in is `AE exact` at 32bpc.
- 2026-07-10 `RadialBlur bounded nonzero witness`: the prior zero-plane result
  was a harness setup omission, not an AEX semantic fact. Calling real AEX
  `FUN_180008690` before the direct Zoom core yields `196/196` informative
  accum/denom/valid cells on `32x32`; actual prepass and scatter each execute
  once. Actual inverse mapping now selects the four-cell neighborhoods for
  `(7,0)`, `(8,0)`, and `(24,0)`. This remains bounded `binary-grounded`
  evidence, not full-frame case_0009 or `AE exact`; permit one narrow Windows
  typed-cell confirmation and keep Mac source frozen until it returns.
- 2026-07-10 `DistanceGradation shared core integration`: the Mac plug-in now
  compiles and invokes the same AE-free EDT/threshold/normalize implementation
  used by the exact AEX CPU fixtures. Synthetic fieldgen (`748` bytes),
  case_0023 inside/outside (`8,294,400` bytes each), compose (`24` bytes), and
  an independent `280`-value brute-force distance test pass; the Universal
  Debug plug-in build also succeeds. Keep the lane `binary-grounded` until a
  Mac AE render proves the declared slice `AE exact`. Blur, compose, bit-depth
  mask ownership, and writeback remain adapter-side and are not covered by this
  integration claim.
- 2026-07-10 `AEX CPU fixture pivot first closure`: use
  `refs/conformance/aex_cpu_fixture_template_result_20260710.md` and
  `notes/CPU_KERNEL_PORTING_PIVOT.md`. The real DistanceGradation AEX
  `FUN_181174760` fieldgen now matches a portable AE-free C++ core exactly for
  the committed `17x11` fixture and for both full-frame case_0023 inside and
  outside passes (`8,294,400` bytes each). Real AEX `FUN_181170480` compose and
  portable compose also match for the case_0023 triplet (`24` bytes), with the
  fieldgen `0,1,1` values bound to compose words `0,32768,32768`. This is
  function-level `binary-grounded` evidence with harness-constructed parameter
  provenance, not `AE exact`. RadialBlur now reaches `0x180005d99` locally and
  grounds all four plane pointers at `4x1`, but its bounded accum/denom/valid
  planes are zero; keep it plane-layout-only and do not change Mac source.
- 2026-07-10 `AE26.3 32bpc EXR recap accepted`: imported
  `refs/win_references/20260710_190500__ae26_3_32bpc_recap/` from the portable
  return. The six contracted requests reconcile as `98/98` requested cases and
  `196/196` paired effect/before-effect FLOAT32 RGBA EXRs, all uncompressed,
  rendered by Windows AE `26.3x87` with `SOFTWARE` (`raw=1816`) at `32bpc`.
  This removes the AE25.2-vs-26.3 version mismatch for the covered 32bpc lane.
  The return manifest leaves `working_space`, `linearize_working_space`, and
  `blend_colors_using_1_0_gamma` unreported; retain the user's recorded
  template settings as supporting evidence and require these fields in future
  return manifests. The matching Mac AE26.3 no-effect control is now recorded
  in `refs/conformance/ae26_3_32bpc_noop_cross_platform_control_20260710.md`:
  it still differs in every RGB float sample with ColorKey disabled, including
  the explicit project-color-management-disable variant. Thus this lane is a
  Windows/Mac `host-platform split`, not a plug-in verdict.
- 2026-07-10 `32bpc no-op EXR host-version split`: the accepted Windows
  FLOAT EXR existing-48 return was generated by AE `25.2x131`; current Mac
  candidate renders use AE `26.3x87`. A no-effect ColorKey case-0001 control
  rendered through the Mac EXR path changes `0.9725490808` to
  `0.9884691238` (`pow(x, 1/2.4)`), with all RGB float samples differing.
  Mac project working space `None` and linear blending `false` did not change
  that result. This is `host-version split`, not a ColorKey or ToonDilate
  algorithm residual. Keep the accepted AE25.2 reference as valid provenance,
  but do not use it for Mac AE26.3 32bpc `AE exact` attribution. The active
  replacement is the AE26.3/SOFTWARE/98-case FLOAT-EXR recapture request at
  `refs/reference_requests/AE_26_3_32BPC_RECAPTURE_20260710.md`.
- 2026-07-10 `32bpc float acceptance / Mac host path`: use
  `refs/conformance/bitdepth_32bpc_colorkey_toondilate_acceptance_audit_20260710.md`
  and
  `refs/conformance/mac_ae_32bpc_float_candidate_path_design_20260710.md`.
  The focused 9+3 request is contract-ready, and
  `scripts/verify_32bpc_float_return.py` now fail-closes PNG, HALF, bad hashes,
  non-SOFTWARE metadata, case/parameter mismatches, false channel-order
  declarations, and unsupported compressed EXR. It does not make either lane
  exact: the current Mac AE runners remain PNG-only. The selected host-final
  path is Render Queue/OpenEXR. Cold `-r`/`-noui -r` startup crashes even with
  all OLM/ColorKeep plug-ins removed, while ordinary GUI startup is stable;
  enumerate the Output Module template from a stable GUI session before
  implementing the separate 32bpc runner. Do not use plug-in raw dumps as AE
  exact evidence.
- 2026-07-10 `OLMDistanceGradation break-ignore return`: use
  `refs/conformance/olmdistancegradation_0010_compose_break_ignore_return_intake_20260710.md`.
  The source run proves software `bp` still reached the live entry under
  `sxi 80000003`, but its first callback was `(0,90)` and target `(6,40)` never
  reached `+0x11705f1`; AE then closed with `PNG was not written`. No typed
  compose values were returned. The active successor is source-only target
  `(901,394)` in
  `refs/runtime_trace_packages/olmdistancegradation_0010_compose_source_901_394_tile_retry_windows_20260710.zip`.
  Do not stage the hardware-breakpoint fallback unless a later live log proves
  the software stop itself is suppressed.
- 2026-07-10 `OLMDistanceGradation exact-address return`: use
  `refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_return_intake_20260710.md`.
  The return is `answered_partial`: same-run 16bpc source/output bases,
  rowbytes, pixel size, and exact addresses for `(6,40)` / `(901,394)` are
  grounded. Field addresses/words, exact RCX/RDX values, transform scalars,
  and final PF16 stores are all missing. Do not change Mac source; retry as one
  target and one downstream site per run.
- 2026-07-10 `OLMDistanceGradation single-site retry`: the direct successor is
  `refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md`.
  The first single-site package returned `answered_partial`, so the active
  standard runtime package is now
  `refs/runtime_trace_packages/olmdistancegradation_0010_compose_single_site_break_ignore_retry_windows_20260710.zip`.
  It is staged in `$OLM_EXCHANGE_ROOT/new` with matching SHA-256 and adds only
  `sxi 80000003`. It still runs field and source as separate debugger processes
  for case_0010 `(6,40)`; do not replace it with either earlier script while
  awaiting return.
- 2026-07-10 `OLMDistanceGradation single-site first return`: use
  `refs/conformance/olmdistancegradation_0010_compose_single_site_return_intake_20260710.md`.
  Field/source runs reached entry but ended on first-chance `0x80000003` before
  either downstream breakpoint. The replacement package adds
  `sxi 80000003`; this is a debugger-control retry, not a new math hypothesis.
- 2026-07-10 `parallel proof materialization`: the focused 32bpc
  float-preserving Windows reference requests for ColorKey (`9` cases) and
  ToonDilate (`3` cases) are ready under `refs/reference_requests/`; they are
  requests, not exact evidence, and are not staged while the active DG exchange
  occupies `$OLM_EXCHANGE_ROOT/new`. The DirectionalBlur angle-0 single-shot
  runtime package is also materialized project-locally at
  `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_angle0_single_shot_20260710.zip`.
- 2026-07-10 `OLMRadialBlur Zoom remaining boundary`: use
  `refs/conformance/olmradialblur_zoom_remaining_polar_sampler_audit_20260710.md`.
  Exact AEX paired trig plus the recovered float inverse order still leaves the
  alpha-254 targets unresolved. Static sampler ownership rules out a new global
  late-alpha policy; the strongest remaining boundary is final polar cell
  population/collapse from `+0xf252` into `+0xe.alpha`. Do not tune a global
  quantizer or fixed cell offset. When this lane becomes active, request one
  typed final-plane witness for `(7,0)` with controls `(8,0)` and `(24,0)`.
  That focused package is now materialized at
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_zoom_case0009_final_plane_typed_20260710.zip`
  under
  `refs/conformance/olmradialblur_zoom_case0009_final_plane_typed_contract_20260710.md`;
  it is pending locally and is not staged while the DG exchange is active.
- 2026-07-10 `OLMDirectionalBlur angle-0 static audit`: use
  `refs/conformance/olmdirectionalblur_angle0_static_helper_writeback_audit_20260710.md`.
  Helper validity input, effective-span/denominator accumulation, A/B buffer
  ownership, and writeback order are binary-grounded. The actual source range,
  validity, and denominator for `(494,169)` / `(579,169)` remain runtime facts;
  no current Mac-only probe distinguishes them. Keep the existing angle-0
  single-shot package as the minimal next Windows proof and do not tune PNGs.
- 2026-07-10 `OLMBlur local AEX CPU witness`: use
  `refs/conformance/olmblur_case0006_aex_cpu_emulation_20260710.md` and
  `refs/conformance/olmblur_fullentry_host_layout_probe_20260710.md`. The bounded
  harness now executes the actual non-Legacy helpers `FUN_180001000` and
  `FUN_180001980` and produces nontrivial weighted outputs. A second harness
  now drives full worker `FUN_180005f20` through a complete PF Handle lifecycle
  to a changed synthetic 16bpc output buffer. This grounds local helper ABI and
  host-layout reachability, but it does not close `case_0006`: synthetic worlds
  are not the canonical case input, and final values still need typed Windows
  or equivalent case-bound evidence.
- 2026-07-10 `OLMBlur case_0006 full-frame AEX probe`: use
  `refs/conformance/olmblur_case0006_fullentry_probe_20260710.md`. Canonical
  1920x1080 RGBA16 input/parameter loading and guest ARGB word layout are
  materialized, but the full worker completes `0` frames in the 30-second
  practical cap. The probe now enforces that cap with a subprocess hard kill.
  A cropped result is not admissible until binary evidence grounds crop origin
  and halo semantics at the absolute witness coordinates.
- 2026-07-10 `OLMKiraKira mode dispatch`: use
  `refs/conformance/olmkirakira_mode_dispatch_static_audit_20260710.md`. Blur
  Modes `1/2/3/4` are now statically mapped: one-pass boxFilter, three-pass
  boxFilter, GaussianBlur wrapper, and an inline recursive accumulation body,
  respectively. Merge Mode `1/2` is grounded as the
  `FUN_18114fd90` / `FUN_18114ffd0` dispatch, while Approximated Input, Fade
  Out, and highlight consumers remain open. Do not infer popup semantics from
  ordering.
- 2026-07-10 `OLMRadialBlur Zoom local float probe`: use
  `refs/conformance/olmradialblur_zoom_aex_float_mode_local_probe_20260710.md`
  and
  `refs/conformance/olmradialblur_zoom_paired_trig_float_inverse_probe_20260710.md`.
  The existing forward AEX-float mode improves only `22` full-frame pixels and
  the recovered float-inverse order plus platform-libm paired trig improves
  `57`, but every variant still misses all three top-row alpha targets; sampler
  alpha and caller-collapse toggles are inert there. The next bounded local
  experiment must feed a table generated by directly invoking the actual
  `FUN_18001d060` SIMD polynomial into the CLI. Direct local AEX execution now
  proves platform libm differs by up to about `2.3e-7` on sampled angles; do
  not treat `sinf/cosf` as helper-exact or change the final quantizer.
- 2026-07-10 `OLMRadialBlur Zoom exact AEX trig table`: use
  `refs/conformance/olmradialblur_zoom_exact_aex_trig_table_probe_20260710.md`.
  All `1800` real case-grid trig pairs were executed from the Windows AEX and
  consumed by the CLI with the recovered float inverse sequence. The result
  improves the full-frame nonzero count to `31,025` but still misses all three
  alpha-254 targets while preserving both controls. Trig and inverse coordinate
  order are not sufficient; keep source changes frozen and return to typed
  polar-plane/sampler-collapse/alpha-ownership evidence.

- 2026-07-10 `release scope`: use `notes/PORTING_ROADMAP.md` for target-set and
  critical-path decisions, and `refs/conformance/olm_release_scope.json` for
  whole-release completion. The current machine gate is intentionally red:
  only fully declared depth cells with `AE exact` count; partial covered slices
  and PNG-only 32bpc returns do not. The independent evidence audit
  `refs/conformance/olm_release_scope_evidence_audit_20260710.md` confirms that
  no whole-feature depth cell is complete yet; packaged exact slices remain
  valid evidence but are `partial-ae-exact` at release scope. `ColorKeep`
  remains support-only.
- 2026-07-10 `OLMDistanceGradation case_0012/0014`: use
  `refs/conformance/olmdistancegradation_0012_0014_store_export_local_audit_20260710.md`.
  Existing local evidence closes neither family. `0012` is compatible with an
  export-only explanation but lacks a same-run Windows chain; `0014` still
  requires a pre-store/store discriminator. Do not implement either inference.
- 2026-07-10 `OLMDirectionalBlur angle-0`: use
  `refs/conformance/olmdirectionalblur_angle0_local_readiness_audit_20260710.md`.
  The single-shot contract/profile is self-consistent and comparator smoke
  passes, but no focused package or live return exists. The missing proof is two
  independent typed records for `(494,169)` and `(579,169)`.
- 2026-07-10 `OLMSmoother2 legacy`: use
  `refs/conformance/olmsmoother2_legacy_local_readiness_audit_20260710.md`.
  The shortest next witness is `0012 (91,841)`: bind the live Windows class
  base/stride, then read `center_b0`, `prev_b0`, `left_b1`, and `e170 c` in the
  same run. Local Unicorn facts are not Windows truth.
- 2026-07-10 `32bpc`: use
  `refs/conformance/bitdepth_32bpc_completion_matrix_20260710.md`. No 32bpc
  slice is complete. Existing ColorKey/ToonDilate and broad returns are
  PNG-only probe evidence; the next references must preserve float samples and
  metadata, preferably in EXR.
- 2026-07-10 `32bpc all-plugin reference bundle`: the separate Windows request
  `handoffs/windows_batch/olm_windows_reference_request_32bpc_all_plugins_exr_20260710.zip`
  covers 98 deduplicated cases across all release plugins. It combines the
  existing 48-case Blur/ColorKey/ToonDilate/DistanceGradation batch with
  random10 cases for RadialBlur, DirectionalBlur, KiraKira, Smoother2, and
  Smoother v1. It is a reference request, not completion evidence; require
  EXR-first float-preserving returns and do not stage it over the active DG
  runtime-trace request.
- 2026-07-10 `OLMBlur Mac provenance`: use
  `refs/conformance/olmblur_mac_export_provenance_readiness_20260710.md`.
  `case_0006` needs no further Windows export: current-AEX and canonical hashes
  already match. A fresh Mac single/batch rerun can classify deterministic
  export-path provenance, but cannot authorize source or writer changes.
- 2026-07-10 `OLMBlur Mac provenance result`: use
  `refs/conformance/olmblur_mac_export_provenance_result_20260710.md`. Two
  single-case and two batch runs converge to the same stable Mac hash per case;
  the historical single/batch split is not live. Canonical verification remains
  `0/7` exact with `max_diff=2`, so the next proof is typed helper/pre-store or
  equivalent binary-grounded AEX evidence, not another export-provenance pass.
- 2026-07-10 `OLMBlur Windows value correction`: use
  `refs/conformance/olmblur_case0006_unverified_windows_value_audit_20260710.md`.
  The old `answered` helper/pre-store result is invalid: CDB never captured the
  target, the later ZIP adds no debug-dump artifact, and its `windows_*` values
  duplicate the Mac values despite the missed bind. Retract all claims that
  Windows pre-store/store matched Mac at `(314,14)` / `(29,71)`; the request is
  now `invalid_unverified_values`.
- 2026-07-10 `OLMRadialBlur Zoom`: use
  `refs/conformance/olmradialblur_zoom_polar_cell_sequence_audit_20260710.md`.
  The narrow binary-grounded divergence is scalar-float paired-trig and
  coordinate/index generation, not a uniform cell offset or late quantizer.
  Do not change source until a full-size typed final-plane witness exists.
- 2026-07-10 `OLMKiraKira controls`: use
  `refs/conformance/olmkirakira_endgame_control_coverage_audit_20260710.md`.
  Keep the hotspot compose lane frozen. Non-2 Blur modes and Merge mode 2 are
  P0 uncovered paths; Approximated Input, ramps/toggles, highlight behavior,
  and Fade Out are visible P1 gaps. UI/default parity is not render parity.
- 2026-07-10 `AEX CPU simulation performance`: use
  `refs/conformance/aex_cpu_sim_detour_performance_audit_20260710.md`. The
  detoured full-frame DG fieldgen is repeatable at about 7.22s and 6,921 AEX
  instructions locally, but speedup is not proven because no comparable
  non-detoured baseline completes. GATE C remains blocked at OpenCV static init.

- 2026-07-08 `OpenCV detour / AEX CPU simu`: P1 is no longer a pending
  implementation task. `refs/conformance/opencv_detour_current_gate_20260708.md`
  records that `python3 refs/scripts/smoke_emulation_opencv_detours.py` passes
  in the current workspace: `cvDistTransform(DIST_L2, DIST_MASK_PRECISE)`,
  `cvThreshold`, same-shape `cvResize`, and limited `cvNormalize` all pass
  GATE A+B. Do not spend orchestration time "implementing P1" unless this gate
  regresses; the next DG proof is the queued store/export rounding witness.
- 2026-07-08 `OLMRadialBlur Zoom emulator`: use
  `refs/conformance/olmradialblur_zoom_emulator_dispatch_bottleneck_20260708.md`
  as the current local emulator classification. Zoom `case_0009` reaches
  `blur_type=1` but not the Zoom core functions within the instruction cap; the
  active local work is staging-loop/entrypoint shortening around `0x180007811`,
  not Mac source tuning. The follow-up staging probe
  `refs/conformance/olmradialblur_zoom_staging_loop_probe_20260708.md` shows
  that this loop is a full-frame `1920x1080` pass with 16-byte pixel strides,
  explaining why the current emulator path burns budget before dispatch.
- 2026-07-08 `OLMDistanceGradation`: use
  `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md` as the
  source-mask-rule evidence. The installed Mac build uses a depth-gated
  source-mask rule: 8bpc keeps the HEAD behavior (`alpha > 0`), while 16bpc and
  deeper exclude the one-code 8bpc alpha fringe (`alpha > 1.5/255.0`). This
  closes 16bpc `case_0023`. The earlier `7/16` extended-batch exact count in
  that report is superseded for true16 conformance by
  `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md`:
  re-verifying the same `/tmp/olmdg_16ext_depthgate2` artifacts with the
  canonical verifier gives `5/16`, matching the current non-Layer true16
  residual shape. 8bpc is structurally HEAD-identical, but the canonical 8bpc
  batch reconfirmation remains an explicit follow-up because
  `scripts/run_ae_single_case.py` is not a valid 8bpc verdict runner.
- 2026-07-08 `OLMDistanceGradation case_0024..0027`: the `max=1` family is now
  classified in
  `refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md`.
  Mac AE debug witnesses in
  `refs/conformance/olmdistancegradation_depthgate_nearmiss_witness_20260708.md`
  point at compose/interpolation/store/export quantization, not distance-field
  topology. The Windows return
  `refs/conformance/olmdistancegradation_depthgate_quantization_return_intake_20260708.md`
  classifies three of four `case_0026` representatives as export-quantization;
  only `(907,222)` remains unresolved and needs a direct PF16 store/export stop
  if this family is pursued further.
- 2026-07-08 `OLMRadialBlur`: use
  `refs/conformance/olmradialblur_case0010_final_writeback_return_intake_20260708.md`
  as the current return classification for tiny Rotation `case_0010 (1614,6)`.
  The final-writeback package returned `answered_partial`: it proves the
  package-bundled current Windows SOFTWARE recapture is still bright at the
  witness (`[237,237,237,255]`) while the direct collapsed `+0xe` path remains
  black, and it also proves the legacy `[255,255,255,255]` reference should not
  be treated as the only current target. It does not contain a fresh same-run
  Windows debugger stop, so do not change Mac code from this return. If this
  lane is retried, the missing proof is one same-run debugger stop tying
  `+0xf250`, `+0xf252`, collapsed `+0xe`, direct `+0xe` sampling,
  output-buffer writeback, and exported byte together.
- 2026-07-08 `OLMDirectionalBlur` / `OLMDistanceGradation` follow-up queue:
  the next-but-not-active runtime packages are now prepared as focused,
  single-request packages and have smoke coverage. DirectionalBlur uses
  `refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md`
  to capture angle-0 `(494,169)` / `(579,169)` typed rowdriver/valid/writeback
  facts without the prior hit storm. DistanceGradation uses
  `refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md`
  for the broad 16bpc Layer-source family, choosing `case_0014` because the
  primary witness already has matching alpha and isolates RGB/source ownership.
  The RadialBlur final-writeback request has returned `answered_partial`, so the
  active shared-folder send target is now
  `$OLM_EXCHANGE_ROOT/new/20260708_runtime_trace__olm_runtime_trace_distancegradation_case0014_layer_source_witness_20260708.zip`.
  DirectionalBlur remains prepared but not active until this DG package returns
  or is explicitly superseded.
- 2026-07-08 `OLMDistanceGradation case_0014`: the Layer-source witness return is
  `failed_partial`, not implementation proof. Use
  `refs/conformance/olmdistancegradation_case0014_layer_source_return_intake_20260708.md`
  and
  `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0014_layer_source_witness_20260708.md`
  as the current classification. The return confirms the alpha-preserving RGB
  deficit shape at `(1652,2)` and `(461,6)`, but it did not capture a fresh live
  Windows callback witness, consumed source RGBA16, compose inputs, pre-store
  float, or final stored RGBA16. Do not change Mac code from this return; a
  retry must bind the witness pixels inside a same-run live callback stop.
- 2026-07-09 `OLMDistanceGradation case_0014 resend2`: the resend return is
  `failed`, not implementation proof. Use
  `refs/conformance/olmdistancegradation_case0014_layer_source_return_resend2_intake_20260709.md`
  as the current classification. It contains neither a fresh Windows live
  callback witness nor an exact hook/watchpoint failure artifact. Do not resend
  the same package unchanged; this lane needs a different Windows debug tactic
  or local evidence before another runtime trip.
- 2026-07-09 `OLMDistanceGradation 16bpc export/rounding residual audit`:
  use
  `refs/conformance/olmdistancegradation_16bpc_export_rounding_residual_audit_20260709.md`
  as the current local classification for the focused Layer/no-bg residual.
  Across `case_0012/0013/0014/0016`, every nonzero true16 delta is even-valued;
  `case_0014` is the only focused case with RGB abs delta `4`. This supports a
  store/export-boundary lane, not broad source-ownership retuning, but it is not
  an implementation proof and does not justify changing Mac code by itself.
- 2026-07-09 `OLMDistanceGradation dominant-channel all-modes probe`:
  deferred / not adopted.
  `refs/conformance/olmdistancegradation_dominant_channel_all_modes_probe_rejected_20260709.md`
  shows that generalizing the 16bpc+ low-alpha dominant-channel promotion from
  `IN_OUT_BOTH` to all in/out modes reduces `case_0014` from max `4` to max `2`,
  but still does not reach exact and is not binary-grounded. A reverted
  BOTH-only spot-check also reports `case_0010` and `case_0011` at max `2`
  under `scripts/run_ae_single_case.py`, so the full single-case run is not an
  exact-count authority for this 16bpc batch. The source and installed plug-in
  were rebuilt back to the BOTH-only rule. Do not adopt this broadening without
  a new binary-grounded discriminator or a canonical batch validation.
- 2026-07-09 `OLMDistanceGradation PF16 store/export samples`: use
  `refs/conformance/olmdistancegradation_pf16_store_export_sample_analysis_20260709.md`
  as the current local arithmetic split. `case_0012` retained samples are
  explainable by export rounding from the same Mac PF16 store words; `case_0014`
  is not, and needs a pre-store/store discriminator because the deferred
  all-modes probe moves the representative store RGB word from `18117` to
  `18119`, matching the Windows PNG direction. Treat `case_0012` and
  `case_0014` as related but not identical subfamilies.
- 2026-07-09 `OLMDistanceGradation current integrated 16bpc batch`: use
  `refs/conformance/olmdistancegradation_current_integrated_16bpc_batch_20260709.md`
  as the current canonical-batch measurement for the installed/worktree build.
  It verifies at `5/16` exact. The later true16 reverify
  `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md`
  shows that the old depthgate `/tmp` artifacts also verify at `5/16` under
  the canonical 16bpc verifier; the suspected current-vs-depthgate provenance
  delta is therefore not a live lane. The next DG task is to classify and close
  the actual true16 residual families: sparse `0010/0011`, Layer/no-bg
  `0012/0013/0014/0016`, and `0024..0028`.
- 2026-07-09 `OLMDistanceGradation Layer/no-bg disabled A/B`: use
  `refs/conformance/olmdistancegradation_layer_changes_disabled_ab_20260709.md`
  as a negative control from before the true16 reverify. It remains useful
  evidence that Layer/no-bg color handling is not the source of
  `case_0010/0011/0024..0028`, but it no longer implies a current-vs-depthgate
  split.
- 2026-07-09 `OLMDistanceGradation source-mask old-rule A/B`: rejected.
  `refs/conformance/olmdistancegradation_source_mask_old_rule_ab_rejected_20260709.md`
  shows that reverting 16bpc `source_mask_owns_alpha()` to global `alpha > 0`
  makes the canonical 16bpc batch far worse (`1/16` exact) and reopens
  `case_0023` (`73px`, max `61165`). The depth-gated source mask is necessary;
  the remaining true16 residuals are not solved by returning to the old
  inclusive mask.
- 2026-07-09 `OLMDistanceGradation depthgate true16 reverify`: use
  `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md`
  as the correction for depthgate exact counts. It proves that the old `7/16`
  number was not a true16 verifier result; the same `/tmp/olmdg_16ext_depthgate2`
  output verifies at `5/16` with `scripts/verify_ae_pixel_validation_result.py`.
  Do not chase a provenance delta between depthgate and current integrated
  builds unless a new canonical verifier result contradicts this correction.
- 2026-07-09 `OLMDistanceGradation true16 residual family audit`: use
  `refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.md`
  as the current family split. The active 16bpc residuals are now:
  sparse R/A-only quantization `case_0010/0011` (`max=2`, `852px` total),
  Layer/no-bg rounding `case_0012/0013/0014/0016` (`max=4`, `26957px` total,
  with `case_0014` the only abs-4 subfamily), and field/export true16
  `case_0024..0028` (`max=3080`, `3721420px` total, `case_0028` outlier).
  The next local DG work should start with `case_0010/0011` because it is the
  smallest true16 family and only moves R/A.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 R/A probe`: use
  `refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md`
  as the current closeout boundary for the smallest 16bpc family. Mac AE debug
  shows these visible R/A `±2` deltas are one-word `PF_Pixel16` alpha-store
  differences exposed through AE export (`2 * store_a - 1`). The sign flips by
  witness, so a global store rounding toggle is forbidden. Next local proof is
  to compare the exact distance-field normalization/field packing for those raw
  distances against the OpenCV/AEX rule, or ask Windows for one positive and one
  negative same-run field/store witness if local proof cannot decide it.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 local field-normalization`:
  use
  `refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md`
  as the current closeout boundary. Local Mac EDT and the repository OpenCV
  detour EDT agree bit-for-bit at the representative witnesses; simple
  field-pack/store simulations are not safe as a broad fix; the sign-flipped
  half-boundary stores require a narrow Windows same-run witness before code
  changes. The next action is to package `case_0010 (6,40)` and `(901,394)`
  with raw distance, consumed field value/word, compose `out_a`, PF16 store,
  and export sample.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 pointer-map return`: use
  `refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md`
  as the current closeout boundary for the sparse 16bpc R/A family. The return
  is `partial_success_missing_true16_export`, not full request acceptance, but
  it answers the output-address and same-run PF16 store questions: output
  rowbytes are `0x3c00`, pixel size is `8`, and the formula
  `out = base + y * 0x3c00 + x * 8` verified for `24356` hits with zero bad
  hits. Windows same-run final PF16 words are `0cc4 8000 0000 0000` at
  `(6,40)` and `2694 8000 0000 0000` at `(901,394)`, with writer sites
  `DistanceGradation+0x1170814/+0x117081c/+0x1170824/+0x117082b`.
  Do not resend the same pointer-map package unchanged. The next action is
  local Mac-side classification of field/compose/float-to-PF16/store/export
  against those words; only request a same-run true16 TIFF/EXR export if export
  binding remains mandatory after local classification.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 PF16 store classification`:
  use
  `refs/conformance/olmdistancegradation_0010_0011_pf16_store_classification_20260709.md`
  as the current local interpretation. Windows `xmm2_alpha` is already close to
  the final PF16 word grid (`3268` and `9876`) before the observed writer
  stores, while Mac `out_a` sits on opposite half-boundary sides. A global final
  `clamp16()` truncation/rounding swap is still forbidden: it would help
  `(901,394)` but not `(6,40)`. The next local proof is the 16bpc field-world
  pack/read path consumed by `FUN_181170480`.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 field-pack/read audit`: use
  `refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md`
  as the current local arithmetic boundary. It confirms that Windows
  `FUN_181170480` consuming a PF16 field-world word is the right source shape to
  inspect, but simple `floor`/`ceil`/`round` packing of the current Mac float
  field does not explain all sign-flipped witnesses at once. The next proof is
  therefore the raw-distance / normalization-denominator / OpenCV field-pack
  boundary, not final `clamp16()` and not a single field-pack toggle.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 normalization denominator`:
  use
  `refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md`
  as the current local denominator split. The sparse witnesses are
  `mixed-actual-max-and-threshold-half-boundary`: `(6,40)` is normalized by the
  outside field's actual max (`~45.54119`), while `(901,394)` and `(915,392)`
  are threshold-limited inside-field witnesses. This rejects a single global
  denominator constant or a final output rounding fix. The next proof is the
  AEX/OpenCV field-prep detail that measures/clamps max and packs the field
  world before `FUN_181170480`.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 OpenCV field-prep audit`:
  use
  `refs/conformance/olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709.md`
  as the current source-shape classifier. It confirms this lane is no longer a
  broad final writer issue: the Windows pointer-map return binds the PF16 output
  writes, the sign-flipped witnesses reject a global `clamp16()` swap, and the
  remaining open boundary is the AEX/OpenCV field-prep chain that clamps,
  normalizes, and feeds/stores the field world before `FUN_181170480`. The next
  allowed action is a local AEX CPU fieldgen probe for `case_0010/0011` at
  `(6,40)`, `(901,394)`, and `(915,392)` with the existing
  `threshold`/`dist_transform`/`resize_same_shape`/`normalize_minmax` detours
  registered. Only if that reproduces the current Mac field rather than the
  Windows-required words should we ask Windows for a narrower primitive trace or
  true16 TIFF/EXR same-run export.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 AEX fieldgen probe`: use
  `refs/conformance/olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.md`
  as the current local AEX CPU witness. The full-frame real-AEX helper, with
  validated OpenCV detours, completes for `case_0010` inside/outside and
  `case_0011` inside. It reproduces the current Mac float fields, while the
  Windows-required field-word relation sign-flips: outside `(6,40)` matches
  `floor`, inside `(901,394)` and `(915,392)` require `ceil`. This rules out
  both a generic helper rewrite and a single field-pack/final-writer toggle.
  The next Windows ask should be narrower than the old pointer-map package:
  bind the real Windows run's field-world pack/read boundary for those exact
  pixels, plus true16 TIFF/EXR only as export confirmation.
- 2026-07-09 `OLMDistanceGradation case_0010/0011 field-world pack/read return`:
  use
  `refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_return_intake_20260709.md`
  as the current Windows boundary. The return is
  `partial_success_fieldread_boundary_not_pack`, not implementation proof, but
  it captures the final-writer read-side `rdx` candidate in the same run:
  `(6,40)` reads all-zero `rdx_src_words`, `(901,394)` reads alternating
  `8000 8000 0000 0000`, and the retained run has `rdx = rdi - 0xfe0000` at
  `DistanceGradation+0x1170814`. Static asm then corrects the interpretation:
  late `rdx` is the source/shade pointer from `param_1[0]`, while the
  field-world pointer is `RCX` from `param_1[1]` at
  `DistanceGradation+0x117057d`. The corrected next ask is
  `refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md`,
  which binds both `RCX` field-world and `RDX` source/shade reads. Do not resend
  the field-world pack/read or misclassified `rdx producer` package unchanged,
  and do not retune Mac final rounding from this return.
- 2026-07-10 `OLMDistanceGradation case_0010/0011 rdx producer return`:
  use
  `refs/conformance/olmdistancegradation_0010_0011_rdx_producer_return_intake_20260710.md`
  as negative evidence for the superseded `rdx producer` ask. The return is
  `partial_watch_miss_prepopulated_rdx`: both derived `rdx` addresses were
  already populated before the first captured `DistanceGradation+0x1170480`
  callback, so a callback-level data watch cannot catch that producer. Combined
  with static asm, this reinforces the corrected next action: bind `RCX`
  field-world and `RDX` source/shade compose inputs, not late final-writer
  `rdx` alone.
- 2026-07-10 `OLMDistanceGradation case_0010/0011 compose input pointer return`:
  use
  `refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_return_intake_20260710.md`
  as the current partial Windows evidence. It confirms `RCX` is the
  field-world read at `DistanceGradation+0x117057d` and `RDX` is the
  source/shade read at `DistanceGradation+0x11705f1`, but it did not bind
  exact `(6,40)` or `(901,394)`: the attempted `r9=x && rbp=y` gate produced no
  exact hits. The live next action is now
  `refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_contract_20260710.md`:
  derive field/source/output base pointers, rowbytes, pixel size, and sub-rect
  offsets, then gate compose input reads and final writer by exact address.
  Do not repeat broad `x=6` logging or `rbp=y`.
- 2026-07-09 `OLMBlur case_0006 current-AEX export`: the one-case Windows
  current-AEX export return is imported and closes the reference-provenance
  question as Outcome A. Use
  `refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.md`
  as the machine audit: the Windows current-AEX export for 16bpc
  `olmblur__case_0006` is byte-identical to the canonical 2026-06-25 Windows
  Software reference
  (`27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`).
  Do not resend `olmblur_case0006_current_aex_export_20260709` unchanged. If
  this lane is reopened, the next proof is Mac export / AE-host run provenance,
  not Windows reference equivalence or helper/writer surgery.
- 2026-07-08 `OLMDistanceGradation depthgate endgame`: the depthgate quantization
  return is `answered` and classifies three of four `case_0026` representatives
  as export-quantization. The remaining open pixel is `(907,222)`. The next
  prepared package is
  `olmdistancegradation_depthgate_907_store_export_witness_20260708`, which must
  capture the target PF_Pixel16 store words and same-run export byte. Do not
  repeat the broad four-pixel depthgate batch.
- 2026-07-08 `OLMDistanceGradation depthgate 907`: the one-pixel store/export
  return is `answered_partial`, not closeout proof. Use
  `refs/conformance/olmdistancegradation_depthgate_907_store_export_return_intake_20260708.md`
  and
  `refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_907_store_export_witness_20260708.md`
  as the current classification. It preserves the carried source/field/float
  values for `(907,222)`, but does not freshly bind the Windows output-world
  address, directly observed PF_Pixel16 store words, or a same-run export. The
  family remains `depthgate-907-store-export-still-open`.
- 2026-07-08 `OLMDistanceGradation Layer/no-bg`: the Mac port now keeps 8bpc
  Layer/no-bg RGB on the old path but uses straight source RGB without final
  alpha scaling for 16bpc and deeper. The current focused Mac AE family is
  `refs/conformance/olmdistancegradation_layer_both_lowalpha_20260708.md`:
  `case_0013 max=2`, `case_0014 max=4`, `case_0016 max=2`, and `case_0012
  max=28` true16 after the Both-only low-alpha channel-mask rule. This is still
  not `AE exact`; next DG work should isolate the remaining low-alpha
  source-word/rounding rule, not revisit the old straight-vs-premultiplied
  broad rewrite.
- 2026-07-08 `OLMDistanceGradation case0012/case0014 store/export rounding`:
  the return
  `20260708_return__olm_runtime_trace_olmdistancegradation_case0012_case0014_store_export_rounding_20260708_windows.zip`
  is `failed_partial`, not a proof. Use
  `refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_return_intake_20260708.md`
  as the current intake classification. It preserves package-local PNG bytes
  and carried notes, but does not contain fresh same-run pre-store float,
  PF16 store word, or TIFF/EXR true16 export for either requested family. Do not
  change Mac code from this return.
- 2026-07-08 `OLMSmoother2 current-AEX producer bytes`: the return
  `20260708_return__olm_runtime_trace_smoother2_current_aex_producer_bytes_20260708_windows.zip`
  is `failed_partial`, not a proof. Use
  `refs/conformance/olmsmoother2_current_aex_producer_bytes_return_intake_20260708.md`
  as the current intake classification. It preserves the local Mac/Unicorn
  producer sweeps for `0012` and `0004`, but contains no fresh same-run Windows
  stop for the requested producer bytes/class-plane values. Do not change
  `mac/OLMSmoother2` from this return; the next Windows ask must first bind the
  actual Windows producer/class buffer address, then read one lane's typed bytes
  in the same run.
- 2026-07-08 `OLMSmoother2 current-AEX 0012 bind-then-read`: the return
  `20260708_return__olm_runtime_trace_smoother2_current_aex_0012_bind_then_read_20260708_windows.zip`
  is also `failed_partial`, not a proof. Use
  `refs/conformance/olmsmoother2_current_aex_0012_bind_then_read_return_intake_20260708.md`
  as the current classification. It kept the request narrowed to
  `legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`, but still
  did not include a fresh same-run Windows Stage A bind or Stage B typed byte
  read. Do not change `mac/OLMSmoother2` from this return; the next retry must
  first prove the live Windows witness-local stop and pointer recovery route.
- 2026-07-08 `OLMRadialBlur Zoom direct core`: use
  `refs/conformance/olmradialblur_zoom_direct_core_prefill_probe_20260708.md`
  as the current local emulator state. The direct-core harness now reaches
  `FUN_1800056f0` and computes the full Zoom geometry (`1800 * 1104` polar
  grid). A reduced non-semantic debug run (`32x32`, quality step `90.0`)
  reaches `FUN_18000b150` and `FUN_18000a9d0` once each, proving hookability.
  A full-size synthetic prefill + no-op heavy-worker run reaches the final-plane
  branch at `0x180005c9f`. The newer `--direct-python-prefill` run replaces the
  hot prefill loop with a decomp-grounded repeat-border sampler and produces
  Zoom `(6,0)` alpha `0.9999999924232991 -> trunc 254`, matching the shape of
  the Windows alpha byte split. Reduced `32x32/q90` validation against the
  original AEX prefill now reports `max_abs_diff=0.0` in
  `refs/conformance/olmradialblur_zoom_python_prefill_validation_20260708.md`.
  This is stronger than synthetic reachability but still a candidate only:
  the one-worker detour matrix in
  `refs/conformance/olmradialblur_zoom_python_prefill_worker_detour_matrix_20260708.md`
  keeps the same target alpha/truncation when either heavy worker is live in
  isolation, but full AE exact still requires translating the rule into the
  C++ port and validating against Windows/Mac AE output or capturing Windows
  final-plane cell evidence. The first direct CLI translation candidate
  (`refs/conformance/olmradialblur_zoom_cli_polar_alpha_candidate_20260708.md`)
  is near-inert, and the global-truncate extension
  (`refs/conformance/olmradialblur_zoom_cli_truncate_candidate_20260708.md`)
  is overbroad. Do not promote `polar-alpha` / `repeat-raw-f32` /
  `zoom-grid-mode=aex-float` / global alpha truncation as the fix yet.
- 2026-07-09 `OLMRadialBlur Zoom final-plane index variants`: use
  `refs/conformance/olmradialblur_zoom_case0009_final_plane_index_variants_20260709.md`
  as the current Mac-only closeout for bounded final-plane index/bias
  variants. The best tested variant (`cpp-double`, double-before-floor,
  angle bias `-0.5`, radius bias `0.5`, truncate) hits only `x=[6,7]`, misses
  `x=12`, and still emits false positives `[14,15,16,29,30]`. This reinforces
  that `case_0009` is not ready for a Mac source change from local index
  arithmetic alone; the next proof remains either exact C++ polar
  coordinate/float-sequence grounding or a Windows same-run final-plane
  four-cell witness.

## Current Decision Matrix

Use this table to choose the next action. It is intentionally stricter than a
progress summary: if a row says a class of work is forbidden, do not spend time
there unless new evidence changes the row.

The 2026-07-10 `AEX CPU fixture pivot first closure` override supersedes the
older DistanceGradation sentence that names another broad CDB exact-address
attempt as the live next action. Its current next action is fixture provenance:
replace the harness-constructed compose/fieldgen parameter block with a
runtime-captured or binary-built block, then replay the same portable core.

| Plug-in / feature | correctness_status | host_status | work_lane | next allowed action | forbidden action |
| --- | --- | --- | --- | --- | --- |
| ColorKeep | `guarded` | `host-smoke` | `parked` | Keep as support/helper unless a real Windows Software reference is requested. | Treat synthetic helper output as OLM compatibility. |
| OLMColorKey | 8bpc and 16bpc covered slices retain their prior status; Edge Blur directions 1/2/3 are `9/9` binary-grounded at the typed apply boundary but have no new AE-exact result; the actual-AEX type-3 primitive completes its HandleSuite lifecycle and matches four-channel float32 Euclidean output exactly. Combined Replace+Edge has exact bounded callback order with cleanup, and separately staged actual-AEX replacement, Thin boundary, type-3 distance, and Blur Apply calls match independent portable outputs with no divergence. A natural same-run numerical orchestration output remains unresolved; 32bpc has nine bound Windows Software FLOAT EXR effect/control pairs but no Mac cross-host comparison. | `host-debuggable` | `bitdepth-expand` | Preserve the passing slices, grounded stage functions, Replace+Edge dispatch and callback order, and repaired OutFlags2 declaration. Close only the natural same-run runtime/AE-host Replace+Edge output lane without changing the established order. Run the fail-closed Mac 32bpc nine-case pair with identical inputs, parameters, color state, output-module settings, and plug-in identity; compare raw FLOAT EXR samples against the audited Windows pairs before classifying any residual. | Reopen the now-grounded distance primitives, staged numerical functions, or callback order; visual/look tuning; reintroducing the Mac-only Replace guard; claiming full RGBA/host equivalence from separately staged calls; PNG-only 32bpc exact claims; compensating for host conversion in plug-in code; or promoting a cross-host effect delta when the no-effect control is not exact. |
| OLMBlur | Packaged 8bpc slice `AE exact`; the declared normalized 16bpc seven-case slice is `7/7 AE exact` on Mac AE `26.3x87` with loaded binary SHA-256 `71df7efc...f4f0d72`. The live non-Legacy worker now uses the binary-grounded float-exponent/double-`exp` sequence, and all seven cases were rerun at `max_diff=0`. The 32bpc `case_0001` raw control samples match, but its old effect comparison remains `invalid`. | `host-stable` for covered 8/16bpc slices; `host-debuggable` for 32bpc | `bitdepth-expand` | Freeze the exact 8/16bpc behavior and evidence in `refs/conformance/olmblur_16bpc_fixed_worker_mac_ae_exact_20260717.md`. Resume only the identity-bound, FLOAT EXR 32bpc effect/control comparison when its contract is valid. | Reopen 8/16bpc coefficient, writer, staging, or rounding rules from CLI/PNG speculation; broaden the seven-case coverage claim; alter Legacy/32bpc workers from the 16bpc proof; or promote 32bpc without same-contract no-effect control and raw FLOAT comparison. |
| OLMToonDilate | 8bpc `AE exact`; covered 16bpc slice is `AE exact`; the bounded PF16 AEX worker uses a five-argument copy callback and exact-opaque `32768` seeding. A true-`2x2` seven-alpha actual-AEX differential crosses the former callback boundary and exactly matches current PF16 source selection, four-word copies, and final typed output; host `PF_COPY` behavior is still an inference; the global seed/premultiply candidate is rejected because it broke two of three normalized regression gates; 32bpc has a fail-closed typed-procedural FLOAT EXR contract but no accepted cross-host compare | `host-debuggable` | `bitdepth-expand` | Keep the exact 8/16bpc slice, bounded PF16 2D kernel, and repaired OutFlags2 stable. Run the isolated Mac 32bpc same-comp effect/control package, capture localized output-module settings, and compare its raw FLOAT EXR samples with the matching Windows typed-procedural pair. | Reopen the 8bpc/PF16 two-pass dilation algorithm, promote PNG-only 32bpc evidence, treat the bounded PF_COPY model as a universal AE-host contract, apply the rejected global seed/premultiply candidate, attribute a control-world host split to ToonDilate, or claim PiPL repair/Mac no-op as cross-host conformance. |
| OLMDistanceGradation | current 8bpc canonical batch is `known-red` (`0/29`); current 16bpc extended is `7/16 AE exact`; PF8 truncation and the source-linked alpha-mask/stride/field boundary are binary-grounded, while the PF16 writer remains `inactive_for_fixture` | `host-debuggable` | `cli-port` | Preserve reciprocal-multiply normalization, raw-threshold helper calls, the PF16 nearest-even field-world roundtrip, Power/Constant fixes, depth-gated source mask, and the existing exact set `0008/0010/0011/0020/0021/0022/0023`. The PF8 source-linked mirror matches the actual-AEX helper and OpenCV 4.5.5 at all `187/187` field words with padded rowbytes and fail-closed layout guards; bounded actual-AEX differentials also match current Mac compose/store for injected live-coordinate bytes. Next isolate the actual `RenderBits` host-world/resize staging between those closed boundaries without treating the mirror as the full host path. When the active AE session can be restarted safely, run the canonical Mac AE 8bpc cases with loaded-module identity; if residuals remain, assign them to that integration boundary rather than broad compose/store or EDT retuning. PF16 alpha-store samples remain Windows `3268/9876/28359` versus Mac `3267/9877/28360`; one global writer rule is rejected. Keep Layer/no-bg `0012/0013/0014/0016`, max-2, and outlier `0028` separate. | Treat the source-linked mirror as full `RenderBits` or `AE exact`; interrupt the active AE session; reintroduce threshold downsample scaling; repeat the closed depth-control request or zero-hit `(397,281)` condition; tune PF8 compose/store or the EDT/helper from broad residuals; revert the grounded PF16 boundary; call historical unbound 8bpc candidates current `AE exact`; use a runner without explicit depth or loaded-module identity; reopen `0010/0011`; apply global output rounding toggles; merge `0028` into the max-2 family; broad PNG tuning; or use CLI output as Windows-reference truth. |
| OLMSmoother v1 | 8bpc `AE exact`; 16/32bpc request is sendable but unreturned | `host-stable` | `parked` | Keep v1 behind the hard lanes. When reopened, run the regenerated fail-closed package whose canonical readback contains only the three v1 parameters; 16bpc is exact-eligible after comparison and 32bpc remains FLOAT EXR probe-only. | Mix v1/v2 behavior without an explicit policy, accept AE compositing controls as v1 parameters, or promote an unreturned 32bpc pass-through branch. |
| OLMSmoother2 no-key | 8bpc `AE exact` | `host-debuggable` | `ae-validate` | Preserve no-key exact behavior; use only bounded regression checks. | Spend Windows/runtime trips on no-key tuning. |
| OLMSmoother2 legacy/key/gamma | `guarded`; exercised c280/helper/cce0 entries and Gamma Colors mode are locally binary-grounded; actual-AEX c=2/c=3 rows ground gamma mode 0 `apply=0` and mode 3 `gamma=2.1695473/apply=1`; case `0012` now matches Windows class bytes, descriptor `92,841,1,92,842,2`, `e170 c=7`, and first appended RGBA/weight after removing a binary-disproved key/unpremultiply coupling. The accepted descriptor selects current-AEX dispatcher key `0x14`; bounded actual-AEX and portable calls agree after `f270` count `1` and unconditional `f130` count `2`, including both RGBA/weight payloads within `1e-6`. Accepted live Windows evidence still ends at the first count `1`, so the live post-`f130`/cce0 context remains unobserved. | `host-debuggable` | `binary-proof` | Preserve the Smooth Range, a9c0 version-gate, direct PF float-slider fetch, parameter-surface, deployment-target fixes, corrected frame-setup gate, dispatcher, and two bounded leaf payloads. The same-context bundle A/B remains known-red: old accidental-compensation path `max=115`, mean `0.1616552`, `19486px`; grounded path `max=151`, mean `0.2171072`, `19891px`. At `(92,841)`, Windows is `[233,233,233,237]`, grounded Mac `[210,210,210,239]`, old Mac `[246,246,246,252]`. Use the post-leaf report as the local baseline. The next proof boundary is live or equivalently bound polygon state after `f130` entering `cce0`, not local descriptor/leaf math. Keep `0004` separate. | Restore the false `Enable Color Key -> unpremultiply` gate because its aggregate happened to be closer; global fallback, alpha, index, curve-index, or `f270` changes; change grounded dispatcher/leaf math from PNG residuals; claim live post-leaf equality from the synthetic direct-call fixture; claim typed producer equality or a single-case render as AE exact; use premultiplied AE-saved PNGs as host-input truth; use an installed bundle without identity checks. |
| OLMDirectionalBlur | front-only/no-variation/no-fade/no-tail/no-back/no-noise 8bpc slice remains `AE exact` for 2/2 declared cases; angle 0 and angle 45 typed differentials are exact; the Mac host adapter is locally `2/2` exact with eight gate rejects; Front Alpha Fade is exact through bounded rowdriver/denominator/alpha/normalization, and the isolated actual-AEX PF8 writer is now grounded for indexing, RGB gain/clamp, alpha handling, truncation, and ARGB stores, but the full PF output remains different from Windows at `226` packed words / `468` channel values / `226` pixels; the same Windows PF slice and returned PNG are identical, ruling out export; other feature families remain `blocked` | `host-debuggable` | `binary-proof` | Preserve the declared 2/2 AE-exact slice, typed differential, host-adapter evidence, exact host transforms, accepted double-exp-then-float Gaussian model (`336/336` UCRT words), and direct `0x180006b30` writer contract. Execute the queued same-run writer-entry witness at `(494,169)` to capture the float RGBA entering the proven writer without reopening exact upstream stages. Re-run the bounded Mac AE regression after the current build is installed; keep Size Variation, Sharp Tail, Back, and Noise independent behind their own witnesses. | Re-request UCRT tables; use the superseded June 19 PNG or old row755 package; reopen the exact Front Alpha Fade rowdriver/normalization stages; change the proven writer before obtaining its live entry values; promote the typed differential or Mac adapter into a new AE-exact claim; bake host conversion, a channel bias, or a case-specific lookup into the plug-in; broad PNG tuning; or apply the front-only shortcut to variation/tail modes. |
| OLMRadialBlur | `guarded` / `blocked`; bounded producer/final-plane semantics, B150 output ownership, and production raw A850 coordinates are binary-grounded; the complete `1x4` actual-AEX prepass/scatter/collapse differential is exact for Repeat Border 0/1 at all five stages. A reconstructed `32x1` caller-state witness now enters and returns from actual B150/A9D0/D80 exactly once, starts from byte-identical live/no-op state, and matches the portable float32 sampler words exactly in `3147` live instructions. A natural unprefilled full-size run remains nonviable at 250M instructions before worker/scatter. Windows-equivalent full-frame host/output binding remains open. | `host-debuggable` | `binary-proof` | Preserve the crop fix, promoted per-operation float32 A850 order, span-4 validity contract, prepass-before-validity-gated-scatter rule, and the bounded reconstructed-state propagation witness. A fresh Mac AE capture matches actual-AEX raw A850 bits at 32/32; the remaining Windows PNG residual is `12876` pixels, `max=1`, so it is not AE exact. Use `refs/conformance/olmradialblur_case0009_fullframe_same_run_points_20260716.json` and `refs/conformance/olmradialblur_reconstructed_caller_state_witness_20260716.json` as local semantic baselines. The next allowed action is only the missing Windows-equivalent full-frame host/output binding when Windows becomes available. | AE visual matching, blind alpha tuning, using bounded reconstructed cells as full-frame truth, rerunning the unchanged unprefilled full-size 250M path, restoring the premature prepass validity rejection, assuming a span of 2, reopening raw A850 or the exact bounded chain, or changing downstream sampling before a semantic witness. |
| OLMKiraKira | `binary-grounded` Mode 1/2 control slices, Mode 2 five-ray raw RGB/raw-alpha accumulation with pinned float64 threshold `0.001` and four independent clamps, Mode 3 warp/Gaussian call contract, and isolated actual-AEX typed writers: PF8/PF16 truncate after scales `255/32768` without local clamp, PF32 stores raw float, all in ARGB order; Mac normal/Smart paths now preserve the Merge Mode UI value, while Mode 2 execution and the later host compose/writer selection remain guarded | `host-smoke` | `binary-proof` | Preserve the hotspot compose witness, distinct Mode 1/2 dispatch, resolved `DAT_181489990`, bounded Mode 2 operation order, corrected Mac PF16 scale, and new Merge Mode parameter plumbing. Bind the preserved value to a Mode 2 production aggregation only after the later host compose/writer contract is grounded. Mode 3 has actual-AEX `CV_32FC1`, raw Size `[0,1]`, `sigmaX=length*0.5`, a corrected 5-degree affine, and OpenCV 4.5.5 post-warp `63/63` word proof. Keep Mode 4 and other controls independent. | Discard the Merge Mode value again; route Mode 2 through the Mode 1 normalized-union path; invent the unresolved host compose/writer; replace the pinned threshold; revert PF16 to `65535`; tune from broad PNGs; call Mode 3/4 placeholders compatible; or infer AE exactness from helper probes. |

Current priority order:

RadialBlur release accounting is split even though the decision matrix keeps a
single operational row:

| RadialBlur feature obligation | Current state | Required proof |
| --- | --- | --- |
| Zoom | `guarded` / `blocked` | Exact polar-cell coordinate and float sequence, or Windows final-plane cell witness. |
| Tiny Rotation | `blocked` | Same-run sampler, output-buffer, and export writeback binding. |
| Inner | `blocked` | Sampler/prepass/scatter normalization proof. |
| Size Variation / Noise Variation / edge behavior | `blocked` | Explicit nonzero-control case sets and binary/runtime witnesses at 8/16/32bpc. |

1. `OLMDistanceGradation` 16bpc `case_0010/0011` exact-address compose witness.
   The R/A probe shows these are sign-flipping one-word PF16 alpha-store
   differences, not color bugs, and the local EDT/field-normalization probe
   could not decide the rule. The latest writeback-follow return reached
   `DistanceGradation+0x117051c` and PF interleave, but did not bind the target
   pixels. The pointer-map return then bound `(6,40)` and `(901,394)` to the
   PF16 output formula and same-run Windows store words, but did not include
   true16 export samples. The active work is now Mac-side classification
   against Windows words `3268` and `9876`, not resending the same debugger
   package. Do not use
   `scripts/run_ae_single_case.py` for 8bpc verdicts or PIL/8-bit comparisons
   for 16bpc verdicts.
2. `OLMDirectionalBlur` angle-0 helper-gate proof. The 2026-07-07 return for
   `olmdirectionalblur_angle0_helper_gate_retry_20260702` is `answered_partial`:
   module load and the broad helper/normalize/writeback breakpoints are proven,
   but the per-pixel typed witness for `(494,169)` and `(579,169)` is still
   missing because the front-scatter helper hit-storm overwhelmed the trace.
   The prepared `olmdirectionalblur_angle0_single_shot_witness_20260708`
   request is conditional/single-shot and must return rowdriver/group,
   helper-local destination range, denominator, `alpha_or_valid`,
   pre-writeback, and final-byte values in the same run.
3. `OLMRadialBlur` same-run final-writeback retry, only if we decide this lane
   should consume another Windows trip. The 2026-07-08 return is useful
   provenance evidence but missing the same-run debugger stop. Do not requeue
   it ahead of DG/DirectionalBlur unless the explicit decision is to resolve
   RadialBlur tiny Rotation first.
4. `OLMBlur` 16bpc typed pre-store arithmetic/operation-order proof. The
   installed current-plugin SHA-256 is
   `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206` and
   revalidation is `5/7 AE exact` for `0001`, `0002`, `0005`, `0006`, and
   `0007`; `case_0006` output SHA-256 is
   `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`.
   Prove only `case_0003` Legacy (`max_diff=2` across 20 sign-mixed red
   samples) and `case_0004` Non-Legacy (`max_diff=2` at `(411,258)` and
   `(458,314)`). Both remain unlocalized before the final exported word, so
   pre-store arithmetic, writer input/store, and export ownership remain in
   the narrow proof chain.
   Do not repeat export provenance or request a new Windows reference image;
   global rounding, writer, kernel, and old installed-bundle changes are
   forbidden.
5. `OLMSmoother2 legacy` descriptor/dispatch comparison first. The final writer,
   live `e170_c=7`, corrected live descriptor `92,841,1,92,842,2`, and
   matching predicate bytes are already grounded. Next useful work is a narrow
   Mac descriptor/dispatch comparison/patch against that Windows lane, not
   broad PNG or final-writeback toggles.
6. Bit-depth expansion on already-strong plug-ins:
   `OLMColorKey`, `OLMToonDilate`, and then other slices that are already
   `AE exact` or close enough to validate safely.
7. `OLMKiraKira` remains parked behind the above, but for a different reason
   than before: the 2026-07-01 hotspot witness now argues against compose-side
   code movement, so the next meaningful work is provenance / witness-placement
   or endgame control coverage rather than more hotspot tuning.
8. `OLMSmoother v1` true endgame work only; do not spend early bit-depth budget
   here while broader plug-ins still need 16/32bpc coverage.

2026-07-02 external review note:

- An `oracle` browser review over the current hard-lane evidence agreed with
  the then-current hard-lane ordering: keep `OLMRadialBlur tiny Rotation
  case_0010` ahead of `OLMDistanceGradation case_0023`.
- It also agreed that Mac-side source edits should pause on both lanes until a
  Windows return retains the requested anchor-context or
  refcon/stack/output-word mapping itself. Local diagnostics and intake logic
  remain allowed; source-side algorithm tuning does not.

2026-07-07 queue sync note:

- The queue source of truth has moved since the 2026-07-02 review. In
  the then-current `refs/reports/pending_runtime_trace_packages.md`, the RadialBlur
  anchor-context request is now `superseded`, `OLMBlur case_0006` is already
  `answered`, `OLMDistanceGradation case_0023 refcon/stack` is now
  `superseded` by the local AEX CPU simu probe, and the 2026-07-07 Send First
  item was `olmdistancegradation_case0023_final_source_ownership_20260707`.
- This remains historical context only. Use the current priority list above and
  the freshly generated `refs/reports/pending_runtime_trace_packages.md` for
  the live send order.

2026-07-07 AEX CPU simu probe note:

- `tools/emulation/test_dg_fieldgen_p1b.py` now accepts a real RGBA PNG,
  derives a binary mask from alpha, applies an optional crop, and samples
  witness points after directly calling Windows `DistanceGradation.aex`
  `FUN_181174760` through the local AEX CPU emulation harness.
- The case_0023 threshold-family crop over the current Windows Software
  recapture before-effects PNG completes and reproduces the known field pattern:
  `(414,393)=0`, `(415,393)=1`, `(416,393)=1`, `(415,392)=0`, `(415,394)=1`.
  Report: `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_probe_20260707.md`.
- After adding the limited `cv::normalize_minmax` detour, the same harness also
  completes full-frame inside/outside `FUN_181174760` passes for case_0023. At
  the live edge witness `(1699,7)`, inside field is `0.0`, outside field is
  `0.0`, and Both add-saturate field is `0.0`. Report JSON:
  `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json`.
- This strengthens the reference-path split classification for the 65px
  edge-family: the Windows CPU AEX helper itself produces the Mac-side field
  value at `(1699,7)`. It still does not prove whole-plugin Mac AE exact, so
  keep Software/EXR recapture or typed final-output witness as the closeout
  evidence before changing completion state.
- A follow-up local overlap audit found that the binary-grounded BOTH
  `cv::add` fact is not a current full-resolution implementation lever for the
  existing 16bpc cases: all 11 BOTH cases in
  `olm_bitdepth_16bpc_normalized_exact_20260625` have `0` pixels where
  `max(inside,outside)` differs from `min(inside+outside,1)`. Report:
  `refs/conformance/olmdistancegradation_both_add_overlap_audit_20260707.md`.
  Keep `cv::add` in the IR, but only reopen it for a resize/downsample witness
  that proves overlapping support.

Current pending Windows runtime queue:

- No current `OLMDistanceGradation case_0023` runtime request is pending. The
  2026-07-07 final/source ownership return has been consumed, and the
  2026-07-08 depth-gated source-mask result is now the live DG evidence.
- Use `refs/reports/pending_runtime_trace_packages.md` as the queue authority
  for non-DG hard lanes such as DirectionalBlur/RadialBlur/KiraKira when those
  packages are regenerated or returned.

Answered/superseded context:

1. Answered partial: `olmdirectionalblur_angle0_helper_gate_retry_20260702`
   - package:
     `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_angle0_helper_gate_retry_20260702.zip`
   - latest return:
     `refs/reports/runtime_trace_comparisons/olmdirectionalblur_dense_sampler.md`
     records the 2026-07-07 result as `answered_partial`.
   - why it still matters:
     the angle-0 residual is reduced to typed helper-local proof, not broad
     PNG tuning. The broad breakpoint reachability is now proven, but the
     useful follow-up must isolate both `(494,169)` and endpoint `(579,169)`
     and retain helper-local source/destination range, rowdriver group,
     denominator, `alpha_or_valid`, pre-writeback, and final byte values.
2. Superseded context only: `olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702`
   - package:
     `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.zip`
   - current status:
     `superseded` in `refs/reports/pending_runtime_trace_packages.md`.
   - why it is no longer first:
     the 2026-07-07 local AEX CPU simu shows the Windows CPU helper produces
     the Mac-side field value at the live edge witness. The live question moved
     from stack/refcon isolation to reference-path split vs final
     output/export evidence.
3. Superseded context only: `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`
   - package:
     `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip`
   - current status:
     `superseded` in `refs/reports/pending_runtime_trace_packages.md`.
   - why it is no longer first:
     the 2026-07-05 local CPU AEX emulation changes the live question from
     "which upstream branch was retained?" to "is the remaining difference a
     reference-path split or CPU final writeback/export issue?" Do not resend
     this anchor-context package as-is.

Queue acceptance rule:

- A runtime-trace request is only actionable if it returns the exact requested
  witness family: target case, target XY, target breakpoint/callsite, and the
  specific registers / floats / words named in the request contract.
- If those are missing, classify the return explicitly as
  `answered_partial`, `failed_breakpoint_watchpoint`, `trace-too-sparse`,
  `not isolated`, or `non-actionable`; do not silently promote it into a live
  proof lane.
- For current hard lanes, “final PNG rendered correctly” is not enough:
  `OLMDirectionalBlur`, `OLMRadialBlur`, `OLMSmoother2 legacy`, and
  `OLMKiraKira` each require producer-side, helper-side, or compose-side
  witness values before implementation changes.
- For current `OLMDirectionalBlur`, the next prepared request is the angle-0
  single-shot witness, not the old broad helper-gate retry. A usable answer
  must include typed helper-local coverage and staged values for both
  `(494,169)` and `(579,169)`.
- For current `OLMRadialBlur`, the broad outer package should no longer be
  treated as live just because it once spanned Zoom and tiny Rotation. The
  anchor-context package is superseded; the active useful proof is now the
  tiny Rotation `case_0010` final-writeback/export evidence.
- For current `OLMDistanceGradation case_0023`, the old edge-family package
  should no longer be treated as the active send target either. Local AEX CPU
  simu has moved that lane into reference-path split vs final output/export
  closeout evidence.

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
  membership before compose-writeback; later local AEX CPU simu then superseded
  the stack/refcon follow-up and shifted the lane to Software/EXR recapture or
  typed final-output evidence.

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

This long table is a historical evidence snapshot. When a row conflicts with
`Latest Overrides` or `Current Decision Matrix`, the newer sections are
authoritative. In particular, its old `OLMDirectionalBlur | blocked` row
predates the 2026-07-11 front-only 8bpc AE-exact closeout.

| Plug-in / feature | 8bpc Software status | 16bpc status | 32bpc status | Evidence | Next required proof |
| --- | --- | --- | --- | --- | --- |
| ColorKeep synthetic helper | guarded | untested | untested | Synthetic CLI smoke only. | Real Windows Software reference or keep as support utility. |
| OLMBlur current-plugin cases `case_0001..0007` | AE exact for packaged 8bpc slices | current-plugin: `7/7 AE exact` (`0001..0007`) | `case_0001`: raw control samples match; old effect comparison `invalid`; `AE exact refused` | Mac AE `26.3x87` loaded binary SHA-256 `71df7efc027b463327fefa23575fff5f80d4b38ff529ae97418d79297f4f0d72`; all seven 16bpc outputs are byte-identical to the pinned Software references. Evidence: `refs/conformance/olmblur_16bpc_fixed_worker_mac_ae_exact_20260717.md`. The 32bpc control contract remains incomplete. | Freeze 8/16bpc behavior. Run only the identity-bound FLOAT EXR 32bpc effect/control comparison when its contract is valid. |
| OLMBlur residual slices `case_0006..0007` | AE exact for packaged 8bpc slices | current-plugin 16bpc: `case_0006` and `case_0007` are `AE exact` | untested | `case_0006` output SHA-256 is `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`; the current-plugin revalidation is `5/7 AE exact`. `case_0003`/`case_0004` are the only remaining red 16bpc cases and are covered by the narrow typed pre-store arithmetic/operation-order proof. | Do not reopen `case_0006` export provenance or change rounding, writer, or kernel globally. Do not use old installed-bundle conclusions. |
| OLMColorKey core RGB/color-space/Replace | AE exact for core packaged 8bpc slices | reference covered / compare pending | untested | 2026-06-19 AE pixel return is exact for `case_0001..0008`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmcolorkey_exact_20260619/reports/ae_pixel_all_exact.json`. Normalized CLI is exact for core `case_0001..0004` and `case_0007`. | Add 16/32bpc references for the core path after Edge Blur reference generation is fixed. |
| OLMColorKey Edge Thin erode / Edge Blur | AE-host exact against normalized 8bpc refs / AE-free CLI residual | AE exact for all 9 covered 16bpc ColorKey cases | untested | 2026-06-19 AE pixel return has Edge Thin erode `case_0005/0006` exact and Edge Blur `case_0008` exact. `case_0009` reports `max=47 mean=0.069921` only against the older 20260604 reference; 2026-06-21 and 2026-06-22 provenance audits show the returned candidate is exact against the 20260618 normalized ref and CLI reference, so this is a reference-generation split rather than a clean algorithm witness. Latest audit: `refs/reports/olmcolorkey_edge_reference_provenance_20260622_024907/audit.md`; it now emits the machine-readable classification `reference-generation-split` and the action “do not tune Edge Blur from the 20260604 residual.” Cross-feature canonicalization reports ColorKey 9/9 `normalized-software-exact` in `refs/reports/software_reference_canonicalization_8bpc.md`. 2026-06-26 16bpc reverify still leaves only `case_0009` failing (`12597px` in the `candidate kept / Windows removed` direction). 2026-06-27/28 runtime tracing proves that the live current-AEX 16bpc path uses `Force Lower Precision=3`, `amount=25`, `distance_type=2`, and `dist <= amount` inside a current `OLMColorKey+0x9000` positive Edge Thin orchestrator. Follow-up raw CDB proves primary residual `(1110,149)` consumes `dist=2.0`, takes the copy path, and writes matte word0 `0x0000 -> 0x8000`. 2026-06-28 PE/capstone audit of the Lab76 per-component comparator at `0x1800043a0` shows separate threshold/epsilon multipliers; applying that binary-grounded formula makes `Lab76 hit + taxicab Edge Thin <=25` exact against the Windows 16bpc reference (`diff=0`). 2026-06-28 Mac AE full-batch rerun completed all 9 `ae_pixel_bitdepth16_olmcolorkey_exact_20260625` cases, and `scripts/verify_ae_pixel_validation_result.py` reported `ok=9 fail=0 missing=0 total=9`, all `max=0 mean=0.0000`; report: `/tmp/olm_colorkey_16bpc_full_rerun_20260628/reports/ae_pixel_16bpc_all_exact.json`. 2026-06-28 adds a preview-only 32bpc float-output probe at `refs/reports/bit_depth_32bpc_probe_plan_20260628/request_preview.json`; it is not active and not completion evidence. | Preserve passing 8/16bpc behavior. Next ColorKey work is an intentionally scheduled 32bpc float-preserving reference/probe, not more 8/16bpc tuning. |
| OLMToonDilate cases `1..3` | AE exact for packaged 8bpc slices | AE exact for the focused 16bpc slice `case_0001..0003`; 32bpc untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0003` with `max_diff=0`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmtoondilate_exact_20260619/reports/ae_pixel_all_exact.json`. AEX-style two-pass chamfer propagation plus semi-alpha RGB premultiply also makes the normalized Windows AE Software refs exact in Python and C++ CLI. 2026-07-03 imported the focused Windows 16bpc batch and confirmed live Mac AE exactness for `case_0001..0003` in both isolated single-case reruns and a fresh batch rerun; note: `refs/conformance/olmtoondilate_16bpc_single_case_host_probe_20260703.md`. The temporary batch verifier output was not retained as a repository artifact. Current IR: `notes/IR_OLMToonDilate.md`. | Keep the IR tied to the two-pass/premultiply evidence; next ToonDilate work is broader bit-depth expansion or holdout use, not reopening the 8/16bpc kernel. |
- 2026-07-03 covered 16bpc exact manifest:
  `refs/conformance/bitdepth_16bpc_exact_manifest_20260703.md`.
  This re-verifies the currently covered 16bpc exact slices directly from the
  live request/result directories and freezes them into committed artifacts:
  - `OLMColorKey`: `9/9` exact
  - `OLMToonDilate`: `3/3` exact
  Treat this as a narrow bit-depth conformance slice, not whole-plugin 16bpc completion.
| OLMDistanceGradation basic/extended/blur | current-binary 8bpc `known-red` (`0/29`); historical exact candidates have unbound plug-in provenance | current 16bpc extended is `7/16 AE exact`; 32bpc untested | untested | The 2026-07-11 depth-correct canonical rerun supersedes the historical `29/29` artifact as current-binary status. The OpenCV/PF16 boundary closes 16bpc `case_0010/0011` while preserving `0008/0020/0021/0022/0023`; see `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`. | Preserve the grounded 16bpc boundary. Reconstruct current 8bpc field/compose behavior from binary evidence; do not use unbound historical outputs, single-case depth carryover, PIL/8-bit true16 comparisons, or CLI output as conformance truth. |
| OLMSmoother v1 via Smoother2 compatibility | AE exact for packaged 8bpc v1 slices | untested | untested | 2026-06-20 AE pixel rerun corrected the v1 comp to `960x540`; `case_0001..0003` are exact with `max_diff=0`. Local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother_v1_20260619/reports/ae_pixel_exact.json`. | Decide whether v1 remains an independent compatibility path or is formally mapped to Smoother2; add 16/32bpc refs if v1 remains supported. |
| OLMSmoother2 no-key grid | AE exact for packaged 8bpc grid | untested | untested | 2026-06-19 and 2026-06-20 AE pixel returns are exact for all 12 no-key grid cases with `max_diff=0`; latest local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother2_no_key_grid_20260619/reports/ae_pixel_no_key_grid_exact.json`. This supersedes the earlier AE-free near-exact residual as an AE-host conformance fact. Current IR: `notes/IR_OLMSmoother2.md`. | Optional runtime trace only for binary-grounding if it returns; do not spend the next Windows trip on no-key tuning. |
| OLMSmoother2 legacy current-AEX recapture | guarded / writer-confirmed internal unresolved | untested | untested | 2026-06-21 full current-AEX Software recapture covers all 12 requested legacy cases. With AE-saved premultiplied before frames, `legacy_case_0002` and `legacy_case_0003` are exact. CDB captures final writer values: `0004 (501,1055)` emits `[159,95,95,255]`; `0012 (500,877)` emits `[9,9,9,255]`, ruling out PNG export / byte packing. Mac audit reclassifies the preserved `+0x350b` pre-call `[rsp+0x48]` floats as stale output-buffer content. Promoting Smooth Range threshold for key-enabled class-plane generation moves `0004` to `idx=208` and `cce0_after_b120=[0.34566417,0.11387399,0.11387399,1.0]`, matching the Windows final writer floats within print precision. The 11 before-frame measured cases improve from mean-sum `1.3008` to `0.0589`; remaining residuals are localized (`0004 max=113 mean=0.0045`, `0012 max=91 mean=0.0151`). Mac-side 2026-06-21 audit isolates `0012 (91,841)` to `cardinal6 key=50 -> f270/e170/e3a0`, while automated residual audit shows `0004 (1903,519)` is the opposite failure shape: transparent center, `idx=208`, polygon count `0`, Mac `[0,0,0,0]` vs Windows `[103,103,103,113]`. Decision matrix `refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.md` rejects global cplane/idx0 toggles, rejects `bb10/curve_idx` as inert, and rejects global `f270` suppression as worse (`mean_sum 0.058945 -> 0.083017`, max `113 -> 169`). Witness contract `refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.md` freezes the two active local paths and the exact proof boundary. Neighborhood report `refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.md` further classifies the opposite 5x5 shapes: Windows adds semitransparent output where local passthrough is transparent for `0004`, while local adds semitransparent output where Windows stays transparent for `0012`; next proof should stay at center-pixel producer/class-plane state, not broad PNGs. Tracked decision `refs/conformance/olmsmoother2_current_aex_8bpc_decision.md` records the earlier 2026-06-25 return, and the writer-frame bundle analysis upgrades the conclusion: the latest writer-frame floats already explain the Windows reference pixels for both active witnesses, so the remaining blocker is upstream producer selection rather than final writer packing; report: `refs/reports/runtime_trace_bundle/olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows/smoother2_writer_frame_followup_analysis_20260629.md`. The accepted 2026-07-16 in-process producer run adds valid same-run call order `f270 -> e170 -> e3a0`, valid `e170_c=7`, and one-vertex raw return words `3e3ce706,3e3ce706,3e3ce706,3f2eaeaf` / `3e91a7b9`; the corrected descriptor rerun now proves live `RDX p2[0..5]=92,841,1,92,842,2`, sample `92,841`, class bytes `255,255,0,255` / `255,0,0,0` / `0,255,0,255`, and predicate bits `center_b0=255`, `prev_b0=255`, `left_b1=255`, matching `e170_c=7`. The remaining blocker is upstream descriptor/dispatch selection versus Mac local descriptor `91,841,1,91,843,5`. Current IR: `notes/IR_OLMSmoother2.md`. | Keep the Smooth Range threshold fix. Next proof: compare the corrected Windows live descriptor/dispatch lane `92,841,1,92,842,2` against the current Mac local lane `91,841,1,91,843,5`, then patch the first upstream selector mismatch. Keep `0004 (1903,519)` separate, do not request final writer bytes again, and avoid global alpha/index/curve-index/f270-suppression toggles. |
| OLMDirectionalBlur | blocked | untested | untested | Official manual describes a non-generic anisotropic blur: front/back strengths are asymmetric, transparent pixels are ignored, and Size Variation / Edge Fade / Sharp Tail depend on opaque pixel groups. Current C++ probes remain expected-red after the 2026-06-21 recheck: `rotated-aex-full-choreo case_0001 max=164 mean=4.9570`, `case_0005 max=251 mean=2.2971`; exact rowdriver/scatter variants stay in the same band, and rowdriver-prepass is worse. The 2026-06-22 candidate matrix confirms this split across `case_0001..0005`: measurement scaffolds `rotated-front-strength/direct` have the best total means (`18.197798` / `18.310725`) but are not AEX-structured, while AEX choreography variants cluster around `22.12` and only clearly beat direct on the diagonal `case_0005`; reports: `refs/reports/olmdirectionalblur_candidate_matrix_20260622_010324/candidate_matrix.md` and `refs/reports/olmdirectionalblur_candidate_matrix_20260622_010433/candidate_matrix.md`. The 2026-06-22 residual cluster audit isolates two concrete witnesses for the next runtime proof: angle-0 `case_0001 (494,169)` is `angle0-rgb-only-rowdriver-or-valid-alpha`, Windows `[164,0,0,255]` vs local `[0,0,0,255]`, alpha diff exactly zero; diagonal `case_0005 (507,367)` is `diagonal-rgb-alpha-rotate-validity`, Windows `[1,0,0,255]` vs local `[252,0,0,255]`, with RGB inversion and smaller alpha residuals; report: `refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/residual_clusters.md`; packaged focused request: `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_residual_witness_20260622_022500.zip`. The 2026-06-24 focused return is only `answered_partial`: it includes exact Software reference renders and a prior live-attempt log, but no successful per-pixel rowdriver/rotate-path values because the module did not resolve before the attempt failed. Current comparison: `refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness_20260624.md`. Decision matrix `refs/conformance/olmdirectionalblur_8bpc_decision.md` classifies this as `blocked-await-runtime-or-asm-proof`: no exact candidate, best overall is a non-AEX measurement scaffold, best AEX-shaped candidate still has `max=251`, and the runtime return is not actionable. Witness contract `refs/reports/olmdirectionalblur_witness_contract_20260624/witness_contract.md` freezes the proof boundary: angle-0 rowdriver/valid-alpha and diagonal rotate/sampler/validity must be proven separately; `direct`/`rotated-front-strength` remain measurement baselines only. 2026-06-21 reference audit shows the 20260619 bulk `OLMDirectionalBlur` folder is mixed: 76 PNGs total, only 16 DirectionalBlur; 60 belong to KiraKira/ColorKey/RadialBlur/Smoother2. Current IR: `notes/IR_OLMDirectionalBlur.md`. | Do not tune from broad PNGs or parent folder names. Need a successful focused runtime/asm proof for angle-0 rowdriver accumulation / validity-alpha side channel separately from the diagonal rotate path, plus final normalization and group-size behavior on non-opaque alpha cases. |
| OLMRadialBlur Zoom / tiny Rotation | guarded / blocked | untested | untested | 2026-06-22 Mac-side recheck: Zoom `case_0009 max=1 mean=0.0046`; tiny Rotation `case_0010 max=255 mean=0.0104` under a mean guard. 2026-06-22 residual cluster audits classify Zoom as `rgba-off-by-one` and tiny Rotation as `high-rgb-border-sampler-or-validity`. The 2026-06-24 focused runtime return narrows this: Zoom final Windows bytes `[20,3,3,254]` are explained by pre-writeback floats, so the mismatch is not a final byte-writer issue but upstream alpha-normalization / sampler-side state. Mac-side witness audit `refs/reports/olmradialblur_zoom_witness_20260624/audit.md` reproduces the local witness: RGB floats match Windows within about `1.3e-7`, local alpha clips to `1.0`, Windows alpha is `0.9999999403953552`, and the only byte delta is alpha `+1`. Tiny Rotation final bytes were captured, but the closest traced inverse-sampler value does not explain the final white pixel, so it remains sampler/validity unresolved rather than rounding. Decision matrix `refs/conformance/olmradialblur_8bpc_decision.md` classifies Zoom as `guarded-alpha-normalization` and tiny Rotation as `blocked-sampler-validity`. Witness contract `refs/reports/olmradialblur_witness_contract_20260624/witness_contract.md` freezes the narrow proof boundary and explicitly rejects final-byte tuning for Zoom plus treating the closest tiny-Rotation sampler return as pre-writeback truth. 2026-06-30 bounded caller-collapse probes reject both `binary-validity` and `zero-rgb-on-invalid`, and a new local witness dump shows `case_0009 (6,0)` remains exactly `[20,3,3,255]` locally even with `--rgba-sampler-alpha-mode repeat-raw`, so the surviving Zoom delta is still caller-side polar alpha/sample collapse rather than the narrow repeat-border alpha rule. A same-day richer witness dump sharpens both lanes further: Zoom's `(6,0)` near-match already uses two `valid=0` contributing cells with nonzero RGBA, so the live issue is not a naive per-cell zero-on-invalid rule; tiny Rotation's `(1614,6)` max witness has all four contributing cells `valid=1` but two negative and two zero RGB contributors, so the black result is upstream in polar RGB population / coordinate choice rather than a last-stage validity gate. A final local clamp probe then shows that clamping negative polar RGB only at the last inverse-sampling stage leaves Zoom unchanged and improves tiny Rotation only marginally (`mean 0.01032034 -> 0.01030189`, `max` still `255`), so that cleanup is not the missing AEX rule either. A nearby patch audit strengthens the remaining call: the Windows output keeps a small bright cluster across `(1612..1614,4..6)` while the candidate preserves surrounding dark/low-gray support pixels but drops that bright lobe entirely, which looks more like a missing bright contribution family than a simple one-pixel output shift. A wider bright-lobe search now makes that even stronger: within a `25x25` window centered on the witness, the reference still has `17` bright pixels (`R>=200`) while the candidate has `0`, so this is not a small local displacement. See `refs/conformance/olmradialblur_local_witness_dumps_20260630.md`, `refs/conformance/olmradialblur_final_polar_rgb_clamp_probe_20260630.md`, `refs/conformance/olmradialblur_tiny_rotation_patch_audit_20260630.md`, and `refs/conformance/olmradialblur_tiny_rotation_bright_lobe_search_20260630.md`. Full Rotation remains expected-red: `case_0001 max=255 mean=1.9034`, `case_0002 max=255 mean=1.3071`. 2026-06-21 reference audit shows same-numbered `case_0001..0013` files conflict between the 20260604 legacy set and the 20260605 extra/img2 set, so do not compare RadialBlur by case number alone. Current IR: `notes/IR_OLMRadialBlur.md`. | AE exact check for Zoom slices and binary-ground the tiny/full Rotation high-max residual before claiming compatibility. Zoom next proof is caller-side polar alpha/sample formation, not final byte packing or naive validity masking; tiny Rotation next proof is the upstream polar RGB / contribution path at the localized high-max witness, not simple final validity gating or a one-pixel output shift. |
| OLMRadialBlur Inner | binary-grounded / guarded / blocked | untested | untested | Runtime trace confirmed `rb_inner_only_strength_small` helper effective span resolves to `31`; C++ CLI default mirrors the span-31 population and the span-stat guard passes. 2026-06-21 recheck still leaves old Inner expected-red: `case_0011 max=255 mean=23.0495`, `case_0012 max=255 mean=16.0039`, `case_0013 max=238 mean=18.0193`. A Mac-side source-scatter/prepass force does not move those old-Inner means, and the `param10` probe rejects the simple alpha-plane hypothesis: `one/factor` are equivalent while `polar-alpha/prepass-alpha` worsen old Inner and Edge Fade. The 2026-06-22 static scatter audit (`refs/reports/olmradialblur_scatter_static_facts.md`) rejects promoting `loop-minus-one`, `table-span-minus-one`, or `circular-wrap` as global rules: asm shows `R14D = trunc(resolved_distance * span_gate)`, table step `30000/R14D`, inner tail `offset < R14D`, and next-row underflow. Decision matrix `refs/conformance/olmradialblur_8bpc_decision.md` classifies Inner as `blocked-no-global-toggle`: `loop-minus-one` has the best total mean in the wide matrix but no candidate is exact and top candidates still keep `max=255`. The dense RadialBlur comparator separates placeholder-only dense returns from the useful-but-narrow span-31 live fact: dense-all is `trace-structure-present-values-missing`, live-followup is `inner-span-31-registers-only`. 2026-06-21 reference audit also shows 18 RadialBlur bulk files are misplaced under an `OLMDirectionalBlur` folder; key by request filename/manifest, not parent folder. Current IR: `notes/IR_OLMRadialBlur.md`. | Binary-ground the remaining wrong plane/value with typed sampler/scatter/writeback witness values; then Mac AE exact check. Prefer the full 20260617 Inner return for coverage. |
| OLMKiraKira strength0 / single-ray slices | binary-grounded / guarded provenance lane | untested | untested | Runtime trace confirmed first `boxFilter` FilterEngine branch is OpenCV 4.5.5 AVX2 `FUN_1812e39d0`. IR now lives at `notes/IR_OLMKiraKira.md`. 2026-06-21 focused forward-warp / box-input trace answered the prior follow-up: forward `warpAffine` matrix, temp geometry, source ROI, `boxFilter` args, and pass-1 input witnesses match the local baseline at the traced points. 2026-06-24 boxFilter microprobe ruled out first-pass contributing-window selection, `BORDER_REFLECT_101`, AVX2 accumulator/store, and wrong Mat stage. The apparent upstream source-buffer delta is now explained: Windows plateau `0.79773343` for RGB `[230,210,60]` matches BT.709 luma, while the old local seed used BT.601 and produced `0.77992159`. `refs/scripts/olmkirakira_cli.py` now uses BT.709 for AEX Channel 2 seed; new baseline is `refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json`, and the new witness plan is `refs/reports/olmkirakira_boxfilter_window_plan_20260624_bt709/witness_plan.md`. The 2026-06-24 BT.709 remeasure keeps the single-ray Software set guarded but not exact: vertical/horizontal `max=14/11`, diagonal/diagonal2 `max=23`, rotation13 `max=66`, while strength-0 remains exact/near-match (`max=0..3`). Report: `refs/reports/olmkirakira_remeasure_20260624_bt709_software/reports/diff.json`. The BT.709 local trace also matches the 2026-06-21 deep Windows ray-helper stages within `1e-5` through box pass 1/2/3, rotate-back, and final center-copy; comparison: `refs/reports/runtime_trace_comparisons/olmkirakira_deep_stage_values_20260624_bt709.md`. Focused follow-up return imported: `refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md`. Windows directly grounds `FUN_18114fd90` at center/up/right (`center ray=0.71891218 -> glow [1,1,1,0.71891218]`, PNG-facing `[124,124,124,255]`). The answered 2026-07-01 hotspot witness then goes further: `refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.md` and `refs/conformance/olmkirakira_hotspot_lane_audit_20260701.md` show that at hotspot `(934,118)` the traced Windows glow-after-opacity, composed float, pre-writeback float, and sampled RGBA8 all match the current Mac compose-boundary witness at `144`, while the canonical Windows reference PNG still says `131`. That shifts the live lane away from compose/gain/quantization tuning and into reference/export provenance or witness-placement drift. Old three-case legacy two-temp remains expected-red and is not an exact gate. | Do not send broad KiraKira PNGs and do not tune luma, first-pass boxFilter, ray-helper choreography, fd90, compose gain, or final quantization from this witness alone. Next useful work is provenance / witness-placement validation or endgame control coverage, not another global retune. |

## Host Usability Gate

Use this table before spending time inside Mac AE by hand. The point is to
separate "does this behave as an AE plug-in yet?" from "is this exact against
Windows Software?".

| Plug-in | Host status | この状態である理由 | AEで今やってよいこと |
| --- | --- | --- | --- |
| ColorKeep | `host-smoke` | Support/helper status only; real Windows compatibility slice is thin. | 読み込み・追加・最小レンダーだけを確認する。 |
| OLMBlur | `host-stable` for covered 8/16bpc slices | Packaged 8bpc AE exact exists; the current-plugin declared 16bpc slice is now `7/7 AE exact` with loaded-module identity. | 8/16bpcは回帰確認だけを行い、次は同一契約の32bpc FLOAT EXR比較へ進む。 |
| OLMColorKey | `host-stable` | 16bpc full batch now applies all parameters and verifies 9/9 `max=0` for the covered slice. | 回帰確認と32bpc展開を行う。自由な見た目合わせはしない。 |
| OLMToonDilate | `host-stable` | Packaged 8bpc AE exact exists and no current host integration blocker is known. | 主に回帰確認を行う。 |
| OLMDistanceGradation | `host-debuggable` | Mac AE automation is recovered. Single-case probes complete after the `eval` manifest parser fix, and the plug-in can emit gated field dumps for 16bpc witnesses. | 16bpcの指定witnessと回帰だけを確認する。 |
| OLMSmoother v1 | `host-stable` | Packaged 8bpc v1 slices are AE exact after comp correction. | 対応済みv1 sliceの回帰確認を行う。 |
| OLMSmoother2 no-key | `host-debuggable` | No-key grid is AE exact, but legacy/key/gamma path is still unresolved. | no-key確認と限定的なlegacy probeだけを行う。 |
| OLMSmoother2 legacy/key/gamma | `host-debuggable` | Manual use can help reproduce witnesses, but internal branch evidence still leads and broad eyeballing is unsafe. | 指定witnessの再現だけを行う。 |
| OLMDirectionalBlur | `host-debuggable` | Windows-visible controls now exist in the Mac UI, but static/runtime evidence says PNG-only tuning is unsafe and broad output is not yet trusted. | witness単位のhost確認だけを行う。見た目合わせはしない。 |
| OLMRadialBlur | `host-debuggable` | Windows-visible controls now exist in the Mac UI, but Zoom/Rotation/Inner still need sampler/prepass/writeback proof before output can be trusted. | witness単位のhost確認だけを行う。見た目合わせはしない。 |
| OLMKiraKira | `host-smoke` | Deep binary facts exist, but compose/writeback remains unresolved and manual output is not yet trustworthy. | 読み込み・UI・最小レンダーだけを確認する。見た目合わせはしない。 |

実用上の判断:

- `host-blocked` / `host-smoke`: AEを開く目的は、host統合とクラッシュ診断だけ。
- `host-debuggable`: 指定したwitnessや分岐に結びつく確認だけをする。
- `host-visual-tuning-ready` / `host-stable`: 狭い残差の確認、または対応済みsliceの
  回帰確認に使える。

## Recent Mac-Side Audits

- 2026-07-03 Windows UI surface parity refresh:
  `refs/conformance/windows_ui_surface_parity_20260703.md`.
  This uses the new Windows Effect Controls surface capture return
  `refs/win_references/olm_reference_return_windows_20260703_combined/OLMmulti-effectUIsurfacecapture/reference_manifest.json`
  plus machine audits
  `refs/reports/windows_ui_surface_defaults_audit_20260703.md`,
  `refs/reports/windows_ui_surface_ranges_audit_20260703.md`, and
  `refs/reports/windows_ui_surface_param_parity_summary_20260703.md`.
  Current operational read:
  - `OLMColorKey` moved materially toward `mostly-fixed` on 2026-07-03:
    the Mac source now mirrors the Windows `Threshold Parameters` /
    `Edge Thin` / `Edge Blur` topic layout, uses visible child `Amount`
    labels, matches the Windows per-color block order, and exposes the
    Windows-scale `Amount` ranges. Remaining drift is narrow
    (symbolic `Use Color N` defaults plus group-end placeholder modeling).
  - `OLMKiraKira` is now the clearest remaining host/UI follow-up candidate,
    but still not a broad panel-breakage lane; the high-signal drift is
    drift is narrower host metadata, especially `Brightness Gain` range
    semantics and ramp-related UI metadata.
  - `OLMRadialBlur` remains mostly past host-fix: the new UI-surface return
    mainly reconfirms grouped/no-value rows and missing Windows range metadata,
    not missing actionable controls. Keep it on witness-led `binary-proof`.
- 2026-07-03 Windows fresh defaults/ranges parity snapshot:
  `refs/conformance/windows_fresh_param_parity_20260703.md`.
  This freezes the cold-start defaults/range lane into committed artifacts
  instead of relying only on ignored `refs/reports/*` summaries. Current
  operational read:
  - `OLMToonDilate` is the only plug-in that is fully `fixed` in this narrow
    cold-start parity lane.
  - `OLMColorKey`, `OLMKiraKira`, `OLMRadialBlur`, and `OLMSmoother2` are
    `mostly-fixed`: remaining drift is narrow schema/default metadata, not
    broad missing controls.
  - none of these rows are algorithm claims; they are host/UI-source-of-truth
    bookkeeping only.
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
  Keep this as a historical contract, not a live queue item. It records the
  point where the remaining OLMBlur wait was first narrowed into a
  writer/helper question, but the lane has since split further. Use
  `refs/conformance/olmblur_closeout_gate_audit_20260701.md` for the current
  reopen rule: `case_0006` is provenance/export-first, normalized 16bpc
  Legacy `case_0007` is closed as a Windows pre-store float delta, and only
  old normalized 8bpc `(488,941)` remains reopenable.
- 2026-06-30 `OLMBlur` writer-only hypothesis audit:
  `refs/conformance/olmblur_writer_only_hypothesis_20260630.md`.
  This converts the previous prose warning into a witness matrix. A pure
  non-Legacy writer swap would fix `case_0006 (314,14)` but leaves
  `case_0006 (29,71)` unchanged, while the surviving Legacy 16bpc witness
  `(345,672)` actually prefers the current `nearby` result at the exact local
  raw `12544.5`. Old 8bpc Legacy `(488,941)` is below the half-step under both
  local writer rules. Operationally, broad local writer rewrites remain
  forbidden, but the live lane is no longer "pending final-word request"; it
  is the 2026-07-01 closeout-gate split.
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
  `$OLM_EXCHANGE_ROOT/old/20260630_160322__olm_runtime_trace_requests_20260630_4pack_windows_return.zip`.
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
  the 4pack, that older one-package statement is no longer current. Treat
  `refs/reports/pending_runtime_trace_packages.md` as the only live queue
  authority for runtime requests; share-folder contents may instead be occupied
  by bit-depth reference bundles such as the 2026-07-03 broad 32bpc EXR-first
  probe.
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
- 2026-07-01 `OLMDirectionalBlur` source-candidates audit:
  `refs/conformance/olmdirectionalblur_source_candidates_audit_20260701.md`.
  This freezes which local preset families are no longer acceptable global
  fixes. `rotated-aex-full-choreo` remains the structural base because it
  preserves the confirmed A/B choreography; `rowdriver_prepass`, broad
  `source_driven_scatter`, the combined `exact-rowdriver` bundle, and
  measurement scaffolds `direct` / `rotated-front-strength` all stay
  diagnostic-only. So the live binary-proof lane is now even narrower: patch
  only after typed witness values land for one of the two surviving families,
  `angle0-rowdriver-valid-alpha` or `diagonal-rotate-validity`.
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
- 2026-07-07 `OLMDirectionalBlur` angle-0 local static review:
  `refs/conformance/olmdirectionalblur_angle0_local_static_review_20260707.md`.
  This re-audits the current Windows send package and confirms that it already
  targets both `(494,169)` and endpoint `(579,169)` with the necessary
  denominator / `alpha_or_valid` / pre-writeback / helper-local destination
  range fields. The lane remains `blocked` until that typed return lands; a
  module-load-only, final-byte-only, or broad `+0x2000` hit-storm answer stays
  `answered_partial` / `failed_partial`, not proof.

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
  as global fixes.
- 2026-07-01 `OLMKiraKira` hotspot lane audit:
  `refs/conformance/olmkirakira_hotspot_lane_audit_20260701.md`.
  The answered Windows hotspot witness now reports the same
  `glow_after_opacity`, `composed_rgba_float`, `pre_writeback_rgba_float`, and
  sampled RGBA8 (`144`) as the current Mac compose-boundary witness at
  `(934,118)`, while the canonical Windows reference PNG still says `131`.
  This freezes KiraKira away from broad compose / quantization tuning and
  reclassifies the live lane as reference/export provenance or witness-
  placement drift plus still-missing endgame controls.
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
