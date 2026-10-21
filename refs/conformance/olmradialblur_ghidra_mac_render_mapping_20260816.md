# OLMRadialBlur Windows → Mac public-render mapping (r01–r08)

Scope is the numerically relevant or public-render-reachable functions identified in `r01.md` through `r08.md`. Generic PF-handle allocation/lock/free wrappers, suite RAII, parameter-registration/UI helpers, STL/exception machinery, custom UI, no-ops, and data-table-only unused RNG overloads are excluded.

Status means:

- **exact** — the Mac production path contains the same leaf contract/order, or delegates to a deliberately AEX-matching helper.
- **partial** — the behavior is folded into a larger routine, uses a semantically equivalent algorithm with known boundary differences, or is admitted only for bounded tuples/geometries.
- **missing** — no production implementation of the Windows numerical/public-render behavior was found.

The current port is deliberately bounded at owner level, so an exact leaf does not imply arbitrary public-parameter closure.

## Sampling, geometry, scatter, and component analysis

| Windows function | Mac production mapping (exact function/lines) | Status | Mapping note |
|---|---|---|---|
| `0x180001000` `RadialBlur_sample_polar_rgba_wrap_angle` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:2908–2936` inverse-polar tap loop in `RenderZoomTyped`; rotation reconstruction at `:4450–4500` | partial | Four alpha-weighted taps and angular wrap are present, but are inlined and coupled to bounded owner branches rather than a universal standalone sampler. |
| `0x180001270` `RadialBlur_sample_rgba_nonrepeat_loose` | `SampleRGBAAEXAlpha`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:993–1048`, `repeat=false` | exact | Preserves loose `-2 < trunc(coord) < extent`, surviving-tap normalization, alpha-weighted RGB and eligibility. |
| `0x180001520` `RadialBlur_sample_rgba_repeat_loose` | `SampleRGBAAEXAlpha`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:993–1048`, `repeat=true` | exact | Same clamped taps, raw accumulated alpha and pre-clamp eligibility contract. |
| `0x180001800` `RadialBlur_sample_scalar_nonrepeat_loose` | `SampleScalarAEXNoRepeat`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1084–1113` | exact | Same surviving-tap renormalization and float operation ordering. |
| `0x180001950` `RadialBlur_sample_scalar_repeat_clamped` | `SampleScalarAEXRepeat`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1050–1082` | exact | Same clamped bilinear scalar contract, including the guarded right-neighbor read. |
| `0x180001a90` rotation-angle defaults | Grid initialization inside `RenderRotationTyped`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:3925–3954` | partial | Constants/derived step are represented, but not as the Windows helper object and only inside admitted render owners. |
| `0x180001ac0` rotation-angle-step setter | Step/angle-count setup in `RenderRotationTyped`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:3925–3938` | partial | Defaulting and derived angular grid are folded into owner logic. |
| `0x180001b10` `RadialBlur_xy_to_polar` | `ComputeRadialBlurAEXCoordinateCandidate`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:233–280` | exact | Center subtraction, rotated/elliptical basis, sqrt, `atan2`, nonnegative angle and index conversion are explicitly preserved. |
| `0x180001bb0` radius bounds | Zoom bounds in `RenderZoomTyped`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2609–2630`; rotation bounds at `:3938–3950` | partial | Equivalent min/max radius construction is owner-local and guarded by tuple/geometry admission. |
| `0x180001c90` `RadialBlur_scatter_tail_by_direction` | `olm::radialblur::scatter_tail`, `core/radialblur_scatter_tail.cpp:58–110` | exact | Dedicated AEX-order implementation covers mode resolution, table indexing, wrap/underflow, accumulation and max-alpha update. |
| `0x1800024c0` `RadialBlur_scatter_valid_polar_cells` | `olm::radialblur::scatter_valid_polar_cells`, `core/radialblur_scatter_caller.cpp:44–100` | exact | Dedicated helper preserves three-way gate, radius-dependent offsets and outer-then-inner scatter order. |
| `0x180002780` rotation edge-fade/alpha prepass | Edge-fade and seed phases in `RenderRotationTyped`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4104–4185` | partial | Weighted alpha prepass exists, but is integrated with bounded rotation variants rather than a single general worker. |
| `0x180002d30` component-run constructor | `BuildRadialSizeFactorPlaneAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1271–1346` | partial | Mac uses pixel flood-fill vectors instead of Windows run descriptors/neighbor handles; output-area semantics are represented, Windows edge quirks are explicitly bounded out. |
| `0x180002ff0` append component-run neighbor | Adjacency enqueue inside `BuildRadialSizeFactorPlaneAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1310–1324` | partial | Same connectivity purpose, different representation (pixel neighbor stack, not run adjacency). |
| `0x180003010` run-interval overlap | Connectivity loop in `BuildRadialSizeFactorPlaneAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1305–1325` | partial | No run-interval primitive; four-neighbor flood fill is semantically substituted. |
| `0x180003040` try-mark-run-visited | `visited` admission in `BuildRadialSizeFactorPlaneAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1299–1323` | partial | Visit semantics match; record layout and traversal unit differ. |
| `0x180003060` get-run-neighbors | `pending`/neighbor array in `BuildRadialSizeFactorPlaneAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1300–1324` | partial | Adjacency is materialized transiently rather than stored per run. |
| `0x180008930` `RadialBlur_BuildComponentAreaPlane` | `BuildRadialSizeFactorPlaneAEX<PixelT>`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1271–1346` | partial | Component areas/max and normalized factor plane are present; implementation is flood-fill and rejects NaN/right-edge/final-row quirks outside bounded admission. |
| `0x180009120` recursive component collection | DFS stack/member collection in `BuildRadialSizeFactorPlaneAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1305–1330` | partial | Equivalent component accumulation is iterative and pixel-based. |

## RNG and procedural noise

| Windows function | Mac production mapping (exact function/lines) | Status | Mapping note |
|---|---|---|---|
| `0x180003090` `RadialBlur_MT19937_Seed` | `std::mt19937 random(seed)` in `olm::dblur::generate_radial_noise_plane`, `core/dblur_noise.h:129–150` | exact | Standard 624-state MT19937 scalar seeding is used. |
| `0x1800032a0` `RadialBlur_MT19937_U32` | `random()` calls in `olm::dblur::generate_radial_noise_plane`, `core/dblur_noise.h:143–175` | exact | `std::mt19937` supplies the same canonical U32 state transition/temper sequence. |
| `0x180003410` `RadialBlur_MT19937_RealHalfOpen` | `next_unit` in `olm::dblur::generate_radial_noise_plane`, `core/dblur_noise.h:143–151` | exact | Explicit float-rounded `U32 / 2^32` form matches the active AEX consumer. |
| `0x180009380` `RadialBlur_NoisePlane_generate` | `olm::dblur::generate_radial_noise_plane`, `core/dblur_noise.h:129–179` | exact | The comments and operation tree explicitly preserve the AEX 101-entry table, smoothstep, separate half-products, offset wrap and clamp. |
| `0x180009680` `RadialBlur_NoisePlane_sample` | `olm::dblur::sample_radial_noise_plane`, `core/dblur_noise.h:94–127`; local wrappers `SampleRadialNoisePlaneAEX`/`SampleRadialBlockNoisePlaneAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:68–106` | exact | Smooth and block branches preserve float products and the lower/upper accumulation tree. |
| `0x180009a10` MSVC `generate_canonical<float,24>` | `next_unit` lambda, `core/dblur_noise.h:143–151` | exact | One MT draw, float conversion before division, matching the documented Windows rounding point. |

## Core workers and typed owners

| Windows function | Mac production mapping (exact function/lines) | Status | Mapping note |
|---|---|---|---|
| `0x1800040f0` `RadialBlur_RenderDispatcher` | `Render`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5190–5230`; `RenderWorld`, `:4754–4784` | partial | Depth dispatch and owner selection exist, but Mac adds format/alias guards and bounded fail-close admission. |
| `0x180004640` `RadialBlur_rotation_render` | `RenderRotationTyped<PixelT>`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:3101–4665` | partial | All major planes/stages are implemented, with many actual-AEX-exact admitted families; arbitrary unenumerated parameter products remain intentionally fail-closed. |
| `0x1800056f0` `RadialBlur_zoom_render` | `RenderZoomTyped<PixelT>`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2116–3068` | partial | Polar conversion, edge fade, scatter/normalization and inverse reconstruction exist, but public coverage remains tuple/geometry bounded. |
| `0x180006500` `RadialBlur_fill_i32` | `source_factor_with_guard.assign(..., 1.0f)`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2694–2700`, and equivalent vector initialization at `:3953–3955` | exact | Same visible numerical result; compiler-level unrolled fill is intentionally not reproduced. |
| `0x1800065c0` Type-3 PF16 span composer | `ComposeType3LayerSpanAEX<PF_Pixel16>`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4668–4723` | exact | Exact extent alignment, typed decode, premultiplication, luminance and final mix. |
| `0x180006830` Type-3 PF8 span composer | `ComposeType3LayerSpanAEX<PF_Pixel8>`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4668–4723` | exact | Same template specialization and arithmetic contract. |
| `0x180006aa0` Type-3 PF32 span composer | `ComposeType3LayerSpanAEX<PF_PixelFloat>`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4668–4723` | exact | Same template specialization and arithmetic contract. |
| `0x180006d10` PF16 owner pipeline | PF16 arm of `RenderWorld`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4777–4779`; `RenderZoom16`, `:3080–3087`; `RenderRotationTyped<PF_Pixel16>`, `:3101–4665` | partial | Typed I/O and staging are present, but owner admission is bounded and not a leaf-for-leaf handle pipeline. |
| `0x180007520` PF8 owner pipeline | PF8 arm of `RenderWorld`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4773–4775`; `RenderZoom8`, `:3070–3077`; `RenderRotationTyped<PF_Pixel8>`, `:3101–4665` | partial | Same reason as PF16. |
| `0x180007d30` PF32 owner pipeline | PF32 arm of `RenderWorld`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4781–4783`; `RenderZoom32`, `:3090–3097`; `RenderRotationTyped<PF_PixelFloat>`, `:3101–4665` | partial | Same reason as PF16/PF8. |
| `0x180009d80` polar RGBA wrap-angle sampler | Inline final reconstruction in `RenderZoomTyped`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2908–2955`, and `RenderRotationTyped`, `:4450–4528` | partial | The arithmetic is represented inline; no single reusable production helper covers every Windows call shape. |
| `0x180009fc0` RGBA zero-border sampler | `SampleRGBAAEXAlpha(..., false)`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:993–1048` | exact | Direct leaf mapping. |
| `0x18000a270` RGBA clamp-border sampler | `SampleRGBAAEXAlpha(..., true)`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:993–1048` | exact | Direct leaf mapping. |
| `0x18000a550` scalar zero-border sampler | `SampleScalarAEXNoRepeat`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1084–1113` | exact | Direct leaf mapping. |
| `0x18000a6a0` scalar clamp-border sampler | `SampleScalarAEXRepeat`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1050–1082` | exact | Direct leaf mapping. |
| `0x18000a7e0` polar-mapper constructor | Zoom grid initialization in `RenderZoomTyped`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2609–2635`; rotation grid at `:3925–3954` | partial | Default quality/step state is folded into typed owners. |
| `0x18000a810` polar-mapper quality setter | Same owner-local grid setup, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2609–2635` and `:3925–3954` | partial | Default-on-nonpositive and derived step exist, but no standalone helper contract. |
| `0x18000a850` Cartesian-to-polar | `ComputeRadialBlurAEXCoordinateCandidate`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:233–280`; source-polar loops at `:2773–2804` and `:4048–4082` | exact | Dedicated state helper preserves the Windows float sequencing and index conversion. |
| `0x18000a8f0` radial-bounds computation | Owner-local bounds in `RenderZoomTyped`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2609–2630`, and `RenderRotationTyped`, `:3938–3950` | partial | Equivalent geometry but folded into bounded owners. |
| `0x18000a9d0` Zoom scatter worker | Zoom scatter/weight loops in `BuildZoomAEXOuterOnlyPolar`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1603–1657` | partial | The Windows caller is `RadialBlur_zoom_render@0x180005c90`; the Mac Zoom helper carries the two radial directions, span-indexed tables and max-alpha update inside bounded owner admission. |
| `0x18000b150` `RadialBlur_ApplyZoomEdgeFadeRows` | `BuildZoomAEXOuterOnlyPolar`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1512–1666`, especially `:1551–1600` | exact | Source comment explicitly identifies B150; inverse-factor indexing, dual fade gather and seed writes are preserved. |
| `0x18000b630` Type-3 layer luminance | Luminance block in `ComposeType3LayerSpanAEX`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:4683–4717` | exact | Exact embedded binary64 coefficients and MUL/ADD/CVTPD2PS ordering are documented and retained. |
| `0x18000b680` Gaussian-kernel builder | `ZoomGaussianWeights`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:1115–1133`; `RotationGaussianWeights`, `:1135–1155` | exact | Formula, float denominator sequencing, table scaling and Windows `expf` rounding surrogate are explicit. |

## Public render plumbing and parameter materialization

| Windows function | Mac production mapping (exact function/lines) | Status | Mapping note |
|---|---|---|---|
| `0x180004010` `RadialBlur_SmartPreRender` | `SmartPreRender`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5356–5428` | partial | Input checkout/rect propagation match; Mac additionally checks noise selectors/layer and persists `PreRenderData`. |
| `0x180008690` `RadialBlur_CheckoutParamsIntoRenderInfo` | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5098–5126`; legacy call `:5197–5199`; Smart call `:5493` | partial | Every public render field is materialized, but Windows helper checkout/unit conversions are distributed between AE ParamDef values and owner logic. |
| `0x18000d9d0` checkout Noise Layer world | Legacy noise-world selection, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5204–5208`; Smart layer checkout `:5460–5464` | partial | Public layer dependency exists; lifetime/checkin is implemented directly rather than through this generic wrapper. |
| `0x18000de60` checkout scaled center point | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5102–5103` | partial | Center is decoded from fixed 16.16 directly; Windows PointParamSuite/downsample wrapper is not reproduced as a leaf. |
| `0x18000e190` checkout boolean | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5112` | exact | Repeat Border is normalized through the SDK boolean field with the same public value. |
| `0x18000e270` checkout integer sliders | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5104–5111, 5121–5122` | exact | Strength, offsets, fade integers and seed/noise offset are read from their stable ParamDef fields. |
| `0x18000e430` checkout float sliders | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5113, 5115–5118, 5123` | exact | Ratio, quality, gain, size/noise variation and thickness are read from double-valued float sliders. |
| `0x18000e5f0` checkout popup/enums | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5101, 5106, 5110, 5119` | exact | Blur type, offset modes and noise type map directly. |
| `0x18000e6d0` checkout main angle | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5114` | partial | Public angle is present, but Windows fixed/raw checkout and later conversion are collapsed into the SDK float-slider representation. |
| `0x18000e7b0` checkout fixed noise offset | `InfoFromParams`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5122` | partial | Noise offset is materialized, but the Mac code reads the slider union directly rather than preserving this standalone fixed16.16 conversion helper. |
| `0x180010540` exported `entry_point` / EffectMain dispatch | `EffectMain`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:5602–5644` | partial | Public ABOUT/setup/render/UI/smart-render routing is present; Windows global EffectBase construction and unused/custom callbacks are intentionally absent. |
| `0x180010f70` rectangle union | `UnionLRect`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:577–586`; use in `SmartPreRender` at `:5419–5423` | exact | Branches and fieldwise min/max match directly. |

## Coverage summary

| Status | Count | Interpretation |
|---|---:|---|
| exact | 30 | Dedicated or directly equivalent production implementation. |
| partial | 30 | Folded, representation-different, or bounded owner implementation. |
| missing | 0 | No active numerical/public-render Windows function in r01–r08 is wholly absent; the remaining closure gap is predominantly owner-level admission/generalization, not a missing named leaf. |

The most consequential partial mappings are the three typed owner pipelines, `RadialBlur_rotation_render`, `RadialBlur_zoom_render`, component-area construction at Windows boundary quirks, and public render dispatch. These are the places where “all functions have a Mac counterpart” does **not** yet mean arbitrary geometry/parameter parity.
