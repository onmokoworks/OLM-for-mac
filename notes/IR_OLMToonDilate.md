# Binary-Grounded IR: OLMToonDilate

## Feature

- Plug-in: OLM Toon Dilate
- Feature/path: 8bpc Search Radius dilation path
- Bit depth: 8bpc documented here; covered 16bpc slice is AE exact; the
  declared 32bpc `64x64` typed-procedural Search Radius `13` profile is AE
  exact
- Reference set:
  - `refs/win_references/20260604_olm/OLMToonDilate`
  - normalized Software refs under
    `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMToonDilate`
- Current status: packaged 8bpc `AE exact` for `case_0001..0003`.
  Python/C++ CLI are also exact against normalized Software refs for the same
  cases. The covered 16bpc Mac AE slice is also `AE exact` for the same three
  cases (`refs/conformance/bitdepth_16bpc_exact_manifest_20260703.md`).
  The narrow 32bpc typed-procedural profile is Windows/Mac AE exact at both
  raw FLOAT32 gates (`0/16,384` mismatches for no-effect and effect-on);
  evidence:
  `refs/conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728.md`.
  The older broad PNG-only return remains probe-only and is not part of this
  promotion. The Mac source-included SmartRender adapter also now executes a
  positive-radius typed fixture through `EffectMain` for PF8, PF16, and PF32.
  All three outputs are byte-exact against the behavior bounded by the cited
  actual-AEX worker fixtures; this is an adapter regression gate, not a new AE
  host-exact slice. PF8, PF16, and PF32 `5x3`, radius `2` shape fixtures also pass
  raw four-word equality. Their source reports and the originating AEX are
  pinned by SHA-256 before the production source is compiled or executed.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| The effect dilates non-transparent image regions toward transparent borders. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMToonDilate__OLMToonDilate__doc__OLM Toon Dilate Manual EN.txt`. | manual-backed |
| Only `Search Radius` is exposed. | Official manual and local PiPL/UI. | proved |
| Render core is a two-pass 8-neighbor chamfer propagation. A checked-in PF16 AEX worker executed under local Unicorn matches the current typed model on a true `2x2` fixture across seven alpha values. | `refs/scripts/olmtoondilate_cli.py`, `cli/OLMToonDilate/main.cpp`, decomp note naming `FUN_1801a6150`, and `refs/conformance/olmtoondilate_pf16_2d_propagation_followup_20260716.json`. | binary-grounded / bounded 2D differential |
| Seed pixels are fully opaque pixels (`alpha == 255` for PF8; `alpha == 32768` for PF16). The PF16 actual-AEX alpha sweep distinguishes `32767`, `32768`, and `32769`. | Python/C++ CLI implementation, normalized exact result, and the bounded PF16 2D differential. | binary-grounded / typed differential |
| Effective radius is `ceil(SearchRadius * image_width / comp_width)`. | Python/C++ CLI implementation and half/full-res reference behavior. | binary-grounded / CLI-confirmed |
| Relaxed pixels copy the current winner neighbor's RGBA immediately. | Python/C++ CLI implementation; `case_0003` distinguishes this from a global nearest-source lookup. | CLI-confirmed |
| Remaining semi-alpha pixels are premultiplied on output with `(rgb * alpha + 127) / 255`. | Python/C++/Mac implementation and normalized exact result. | CLI-confirmed |
| The declared PF32 host path matches Windows and Mac AE for a transparent-background `64x64` fixture at Search Radius `13`. Both no-effect and effect-on pairs are raw FLOAT32 exact, effect-on is non-no-op at `6,448` words, and the loaded AEX/Mach-O identities are recorded. | `refs/conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728.json` and retained EXRs. | AE exact / runtime-bound narrow profile |
| The Mac SmartRender entrypoint dispatches a positive-radius fixture through the production `EffectMain` path for PF8/PF16/PF32, preserves padded rowbytes, and matches the bounded actual-AEX typed worker behavior. | `tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py`, grounded by the PF8 tie-break, PF16 2D propagation, and PF32 seed-propagation reports. | source-included adapter exact / bounded typed fixtures |
| The PF32 SmartRender entrypoint propagates a center seed across the exact radius-2 Chebyshev footprint in a `5x3` padded world, preserving all four float words. The harness refuses to run if either the PF32 seed-matrix report (`8fcd021...52f`) or AEX (`c05db8c...32b3`) identity drifts. | `tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py` and `refs/conformance/olmtoondilate_pf32_seed_propagation_matrix_20260717.json`. | hash-bound fixture-driven adapter exact; no Mac AE claim |
| The PF16 actual-AEX worker and production SmartRender entrypoint both propagate a center seed across the full radius-2 footprint of a padded `5x3` world. The Unicorn worker returns after 4,447 instructions with 14 copy-helper hits; visible output is four-word exact and padding is unchanged. | `tools/emulation/test_olmtoondilate_pf16_radius2_shape_20260805.py`, `refs/conformance/olmtoondilate_pf16_radius2_shape_20260805.json`, and the production adapter gate. | actual-AEX worker exact plus source-included adapter exact; no AE-host claim |
| The independently executed PF8 actual-AEX worker and production SmartRender entrypoint both propagate a center seed across the full radius-2 footprint of a padded `5x3` PF8 world. The Unicorn worker returns after 4,432 instructions with 14 PF8 copy-helper hits; visible ARGB is exact and padding is unchanged. This witness does not reuse the PF16 result. | `tools/emulation/test_olmtoondilate_pf8_radius2_shape_20260805.py`, `refs/conformance/olmtoondilate_pf8_radius2_shape_20260805.json`, and the production adapter gate. | independent actual-AEX PF8 worker exact plus source-included adapter exact; no AE-host claim |
| A distinct PF8 radius-3 fixture places differently colored opaque seeds on the left and right boundaries of a padded `7x3` world. It captures the scan-order-asymmetric equal-distance frontier: the top-row `x=3` pixel chooses the right seed, while middle/bottom `x=3` choose the left. Actual AEX and production SmartRender agree on every ARGB byte and all padding. | `tools/emulation/test_olmtoondilate_pf8_radius3_boundary_tie_20260805.py`, `refs/conformance/olmtoondilate_pf8_radius3_boundary_tie_20260805.json`, and the production adapter gate. | actual-AEX boundary/tie exact plus source-included adapter exact; no AE-host claim |
| Independent PF16 and PF32 actual-AEX radius-3 fixtures reproduce the same scan-order-asymmetric boundary frontier without consuming PF8 evidence. Both also run through production SmartRender with full raw four-word/padding equality; PF32 comparison is bitwise FLOAT32 rather than numeric tolerance. | `tools/emulation/test_olmtoondilate_pf16_radius3_boundary_tie_20260805.py`, `tools/emulation/test_olmtoondilate_pf32_radius3_boundary_tie_20260805.py`, their `refs/conformance/*radius3_boundary_tie_20260805.json` reports, and the production adapter gate. | independent actual-AEX PF16/PF32 exact plus typed production adapter exact; no AE-host claim |
| A separate `5x5`, radius-4 corner-seed geometry executes PF8, PF16, and PF32 workers independently. All three produce the same diagonal scan frontier with depth-specific raw four-word equality and preserved padding. Each typed form is also independently connected through production `EffectMain` to SmartRender; PF8/PF16 do not reuse the PF32 adapter case. | `tools/emulation/test_olmtoondilate_corner_seed_all_depths_20260805.py`, `refs/conformance/olmtoondilate_corner_seed_all_depths_20260805.json`, and the production adapter gate. | independent all-depth actual-AEX exact plus all-depth dynamic adapter exact; no AE-host claim |
| A radius-4 eligibility fixture places an alpha-zero pixel with deliberately nonzero RGB opposite one exact-opaque seed. PF8, PF16, and PF32 workers run independently and reject the alpha-zero candidate as a seed; the opaque pixel fills every output word and padding remains intact. The PF32 form also passes production SmartRender bitwise. | `tools/emulation/test_olmtoondilate_alpha0_rgb_eligibility_all_depths_20260805.py`, `refs/conformance/olmtoondilate_alpha0_rgb_eligibility_all_depths_20260805.json`, and the production adapter gate. | independent all-depth eligibility exact; PF32 adapter exact; no AE-host claim |
| Zero and negative Search Radius are exact copy branches for PF8, PF16, and PF32. Six independent actual-AEX worker runs preserve mixed-alpha visible typed bytes, zero-alpha nonzero RGB, and padding; six independent production `EffectMain`/SmartRender runs match. | `tools/emulation/test_olmtoondilate_nonpositive_radius_all_depths_20260805.py`, `refs/conformance/olmtoondilate_nonpositive_radius_all_depths_20260805.json`, and the production adapter gate. | independent all-depth actual-AEX and dynamic adapter exact; no AE-host claim |

## Parameters

| UI / manifest name | Internal meaning | Normalization | Evidence |
| --- | --- | --- | --- |
| `Search Radius` | Maximum propagation distance. | `ceil(radius * image_width / comp_width)`; default comp width fallback in CLI is `1920`. | CLI exact + comp-width scaling behavior |

## Kernel / Loop Shape

The current exact CLI kernel is:

1. Copy input RGBA to output.
2. Initialize `dist = UINT32_MAX`.
3. For every pixel, set `dist = 0` only when source alpha is `255`.
4. Forward raster pass:
   - order: `y = 0..h-1`, `x = 0..w-1`
   - candidate neighbors:
     - left
     - upper-left
     - up
     - upper-right
5. Backward raster pass:
   - order: `y = h-1..0`, `x = w-1..0`
   - candidate neighbors:
     - right
     - lower-right
     - down
     - lower-left
6. For each pass, if `best_neighbor_dist + 1 < current_dist`, update distance.
7. If updated distance is within `r_eff`, immediately copy the winner neighbor's
   current output RGBA into the current pixel.
8. After propagation, premultiply RGB for semi-alpha pixels only.

## Sampling / Boundary

- Boundary mode: skip out-of-bounds neighbors.
- Metric: two-pass chamfer with unit cost for all eight listed neighbors.
- Tie rule: first neighbor in the listed scan order wins because only
  `d < best` updates the candidate.
- Fill source: current output buffer, not immutable original source.

## Channel Rules

- Fully opaque source pixels are seeds.
- Fully transparent pixels may be filled when reachable within `r_eff`.
- Semi-alpha source pixels are not seeds.
- Semi-alpha pixels that remain semi-alpha after propagation get premultiplied
  RGB on output.
- Copied pixels preserve all RGBA bytes from the winner neighbor at copy time.

The bounded PF16 `2x2` actual-AEX fixture crosses the prior
`context+0x180`/`0x1801adc8f` boundary. For alpha values
`0,1,16384,32767,32768,32769,65535`, it records each selected source and
destination coordinate plus all four PF16 words, and its final output equals
the current `RenderTyped<PF_Pixel16>` model. The suite/PF_COPY host ABI remains
synthetic, so this is binary-grounded kernel evidence rather than AE exact.

## Numeric Rules

- Radius uses `ceil`.
- Distance is integer and unit-cost.
- Output premultiply uses integer rounding `(v * a + 127) / 255`.

## Conformance Cases

| Case | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| `case_0001` | 8bpc | `AE exact` for packaged Software ref | `max_diff=0` in 2026-06-19 AE pixel return; exact in Python/C++ normalized checks | Preserve exact behavior; next open depth is float-preserving 32bpc |
| `case_0002` | 8bpc | `AE exact` for packaged Software ref | `max_diff=0` in 2026-06-19 AE pixel return; exact in Python/C++ normalized checks | Preserve exact behavior; next open depth is float-preserving 32bpc |
| `case_0003` | 8bpc | `AE exact` for packaged Software ref | `max_diff=0` in 2026-06-19 AE pixel return; exact in Python/C++ normalized checks | Preserve exact behavior; next open depth is float-preserving 32bpc |
| `case_0001..0003` | 16bpc | `AE exact` for covered Software slice | Live Mac AE verification against imported Windows Software 16bpc refs passes `3/3` with `max_diff=0` | Preserve exact behavior; broaden only with declared references |
| `olmtoondilate_typed_procedural_64x64`, Search Radius `13` | 32bpc | `AE exact` for this declared profile | Windows/Mac no-effect and effect-on are each `0/16,384` mismatched raw FLOAT32 words; effect-on differs from control at `6,448` words | Freeze this profile; broaden only through independent raw control/effect pairs |

## Open Questions

- 32bpc behavior beyond the one declared typed-procedural Search Radius `13`
  profile. Do not generalize this exact result to arbitrary sources or radii.
- Broader 16bpc behavior beyond the declared covered slice, if new ToonDilate
  parameters or inputs are introduced.
- Mac AE host execution for typed fixtures outside the already declared exact
  slices. The source-included positive-radius adapter gate must not be promoted
  to AE exact without hash-bound host evidence.
- SmartRender extent/result-rect clipping with partial worlds remains unproved;
  the nonpositive-radius fixtures cover full visible worlds only.
- The actual AEX SmartRender command boundary is identified: export
  `entry_point` is `0x1801abc00`, command `0x17` reaches `MyEffect` vtable
  `+0x10` (`0x1801a5940`), and command `0x18` reaches `+0x20`
  (`0x1801a5970`). A probe-local PF Handle v2 / AEGP Utility v13 shim now
  completes sequence setup, retains the initialized 0x90-byte handle at
  `out_data+0x28`, invokes SmartPre checkout, and reads back distinct result
  and max rectangles exactly. Command `0x18` now locks the retained sequence
  handle, invokes `checkout_layer_pixels` and `checkout_output`, and produces
  independent exact padded `2x1` PF8/PF16/PF32 outputs with depth-specific
  rowbytes and both backing guards intact. These AEX paths do not invoke the
  optional checkin callback. A PF8 probe with input extent
  `[100,200,102,201]`, output extent `[300,400,302,401]`, and SmartPre result
  `[10,20,13,22]` remains pixel exact with guards intact. Independent PF16 and
  PF32 worlds use different nonzero extents, rowbytes, callbacks, and guards
  and are likewise typed-byte exact with their headers unchanged. This proves
  the actual workers use buffer-local coordinates and read only data/rowbytes/
  width/height. Production `EffectMain` matches this rule at all depths. The exact
  metadata layout supplied by real AE and AE-host execution remain open.
- A larger partial-world slice uses independent `3x2` PF8/PF16/PF32 worlds,
  depth-specific nonpacked rowbytes (`20/32/56`), mixed-alpha non-seeds, one
  exact-opaque seed, distinct nonzero extents, padding, and backing guards.
  Radius 1 visibly propagates the seed across all six pixels through actual
  command `0x18`; production `EffectMain` matches every typed byte and padding.
  Evidence: `refs/conformance/olmtoondilate_actual_aex_smartrender_entrypoint_20260805.json`
  and `refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json`.
- A distinct radius-2 boundary slice uses independent `4x2` PF8/PF16/PF32
  worlds with mixed-alpha non-seeds, nonzero input/output extents, backing
  guards, and 12 padding bytes per row (`rowbytes 28/44/76`). From the opaque
  seed at `(0,0)`, actual command `0x18` replaces the complete distance-2
  frontier (`x=0..2`) while preserving the distance-3 column's raw typed RGBA;
  production `EffectMain` matches those bytes and all padding at every depth.
  The actual outputs are hash-fixed in the sequence/SmartRender report. This
  remains a probe-local metadata result, not a claim about general AE-host
  extent layout or AE-host execution.
- The typed-core radius-3 boundary is promoted through actual command `0x18`
  and production `EffectMain` for an independent PF32 `5x1` partial world.
  Its opaque seed reaches exactly the distance-3 pixel; the distance-4
  mixed-alpha pixel retains its raw FLOAT32 words. Nonzero input/output extents,
  `rowbytes=88`, eight padding bytes, backing guards, and the actual output hash
  are fixed. This focused one-depth result does not generalize AE-host metadata.
- The same `5x1`, radius-3 boundary is independently executed for PF16 rather
  than inferred from PF32. Its distance-3 frontier and distance-4 mixed-alpha
  `uint16` pixel are exact through actual command `0x18` and production
  `EffectMain`; `rowbytes=48`, eight padding bytes, distinct nonzero extents,
  backing guards, and the actual output hash are fixed. AE-host metadata remains
  outside this bounded claim.
- PF8 independently completes the same `5x1`, radius-3 SmartRender boundary:
  actual command `0x18` and production `EffectMain` agree that distance 3 is
  replaced by the opaque seed and distance 4 retains raw `uint8` RGBA.
  `rowbytes=28`, eight padding bytes, distinct nonzero extents, guards, and the
  actual output hash are fixed. Together these are three independent typed
  entrypoint cases, without extending the claim to real AE metadata layout.
- Radius 4 is separately exercised through the actual SmartRender entrypoint,
  not inferred from the existing core-only corner fixture. A PF8 `6x1` partial
  world propagates its opaque seed exactly through distance 4 while preserving
  the distance-5 mixed-alpha pixel. Distinct nonzero extents, `rowbytes=32`,
  eight padding bytes, guards, and the actual output hash are fixed, and the
  production `EffectMain` adapter is byte-exact. AE-host metadata remains open.
- PF16 independently matches that radius-4 entrypoint boundary: a `6x1` world
  replaces the complete distance-4 frontier and preserves the distance-5 raw
  `uint16` RGBA pixel. The actual and production paths agree byte-for-byte with
  distinct nonzero extents, `rowbytes=56`, eight padding bytes, intact guards,
  and a fixed output hash. This remains a probe-local host-seam result.
- PF32 completes the independent radius-4 entrypoint set. Actual command
  `0x18` and production `EffectMain` agree bitwise that distance 4 takes the
  opaque seed while distance 5 preserves raw FLOAT32 RGBA. Its nonzero extents,
  `rowbytes=104`, eight padding bytes, guards, and output hash are fixed. This
  closes the bounded PF8/PF16/PF32 radius-4 partial slice, not AE-host metadata.
- After integer radii 0 through 4, the next public parameter boundary is a
  non-integer Search Radius. A PF8 `5x1` actual command `0x18` case requests
  `2.01` and proves the effective radius is `ceil(2.01)=3`: distance 3 takes
  the opaque seed while distance 4 retains raw `uint8` RGBA. Production
  `EffectMain` is byte-exact with nonzero extents, `rowbytes=28`, eight padding
  bytes, guards, and a fixed output hash. This does not claim AE-host parameter
  checkout or metadata beyond the focused probe seam.
- PF32 independently verifies fractional rounding without reusing the PF8
  `2.01` quantization: a `5x1` command-`0x18` world requests radius `2.5`,
  propagates the opaque FLOAT32 seed through distance 3, and preserves the raw
  distance-4 FLOAT32 pixel. Production `EffectMain` is bitwise exact with
  distinct nonzero extents, `rowbytes=88`, padding, guards, and fixed output
  hash. Real AE parameter checkout and host execution remain unclaimed.
- PF16 supplies a third independent fractional quantization: radius `3.25` on
  a `6x1` command-`0x18` world yields effective radius 4, propagating through
  distance 4 while retaining the distance-5 raw `uint16` pixel. Production is
  byte-exact with nonzero extents, `rowbytes=56`, padding, guards, and fixed
  output hash. This does not widen the probe-local host-seam claim.
- The completion matrix is recorded in
  `refs/conformance/olmtoondilate_completion_matrix_20260805.json`. This round
  closes PF8 empty-width geometry through actual command `0x18` and production
  `EffectMain`: a `0x1` world with radius 4, `rowbytes=8`, nonzero-origin
  zero-width extents, padding, and guards returns exactly without touching the
  output bytes. Composition-width scaling remains explicitly unproved because
  the exact actual-AEX host metadata field/layout has not been established.
- The next matrix geometry gap, empty height, is independently closed with a
  PF16 `1x0` world through actual command `0x18` and production `EffectMain`.
  Radius 4 returns without touching its 16-byte output backing store; nonzero-
  origin zero-height extents, guards, and the output hash are fixed. No
  composition-width field, other plugin, AEXCompat, or AE host is involved.
- PF32 closes the both-axes-empty geometry with an independent `0x0` SmartRender
  world. Actual command `0x18` and production preserve its 24-byte backing
  sentinel, nonzero-origin zero-size extents, and guards exactly. A legacy
  `PF_Cmd_RENDER` feasibility probe returned without World Suite acquisition or
  expected output under the current ABI; legacy Render therefore remains
  explicitly unproved rather than inferred.
- The shortest AE-free completion route is now fail-closed in
  `tools/emulation/test_olmtoondilate_installed_completion_route_20260805.py`:
  actual AEX entrypoint `0x17/0x18` evidence, typed workers/writers, the
  source-included production adapter, current source SHA, and current installed
  signed Universal bundle SHA are checked in one run. This is a transitive
  identity connection; real AE loading and rendering remain unclaimed.
- The remaining installed edge is now directly exercised rather than only
  transitively identified: an AE-free harness `dlopen`s the installed arm64
  binary, resolves `EffectMain`, and executes SmartPreRender then SmartRender
  independently for PF8, PF16, and PF32 `3x2` radius-1 fixtures. Callback
  lifecycle, visible typed words, and row padding are exact at every depth;
  PF32 comparison is bitwise. This proves focused installed dynamic execution,
  but still does not claim loading or rendering inside real AE.
- The real-AE Software phase package is prepared without launching AE. Its
  runner/fixture manifest is pinned to installed SHA `8ac60d57...0ffc`, 32bpc
  FLOAT, Software renderer, SmartPreRender/SmartRender, Search Radius 13
  property readback, exact loaded-module path/SHA, and prior canonical
  no-effect/effect-on EXR hashes. The generated project path is fixed as
  `mac_run/fixture.aep`; legacy Render is explicitly not an accepted substitute.
  Evidence: `refs/conformance/olmtoondilate_mac_ae_software_phase_preflight_20260805.json`.
- The current source was built as a Universal `arm64` + `x86_64` plugin,
  ad-hoc signed, deep/strict verified, and safely installed to the user
  MediaCore directory without stopping After Effects. Binary identity, host
  identity, prior-bundle backup, and installation procedure are recorded in
  `refs/conformance/olmtoondilate_macos_universal_install_20260805.json`.
  The observed AE process predates installation, so restart is required and
  loading of this new binary is not yet claimed.
- Whether non-normalized older residuals were stale reference drift or hidden AE
  host/export differences; do not use them as algorithm guidance now.
