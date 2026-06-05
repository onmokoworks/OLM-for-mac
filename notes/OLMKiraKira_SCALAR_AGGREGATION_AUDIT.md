# OLMKiraKira Scalar Aggregation Audit

Date: 2026-06-06

Scope: fact log for `FUN_18114fd90` / `FUN_18114ffd0`, per-ray scalar arrays, Brightness/Gain argument flow, and source/glow opacity ordering. This note records confirmed vs ambiguous facts only; it does not add image-diff tuning recommendations beyond the already pending single-ray references.

## Confirmed

- `FUN_18114f4a0` builds five ray buffers and a parallel five-entry scalar array before final aggregation.
  - Decomp: `local_290[5]` stores ray buffer data pointers; `local_2a8[6]` is the scalar side array.
  - For normal directional rays, `FUN_181150790(...)` returns a float and the caller stores it with `*pfVar8 = fVar15`.
  - For layer index `4`, the special/highlight branch computes `iVar6 = length * 2 + 1`, stores `length_area = iVar6 * iVar6`, and in Blur Mode 2 squares twice more (`fVar13 = *pfVar8 * *pfVar8; *pfVar8 = fVar13 * fVar13`).

- `FUN_18114f4a0` dispatches merge mode through vtable slots after ray generation:
  - `param_15 == 1` calls `(*vtable + 0x08)`.
  - `param_15 == 2` calls `(*vtable + 0x10)`.
  - The nearby assembly confirms the richer call setup at `18114fc2d..18114fc86`: both branches pass the ray pointer array, color/ramp metadata, output float RGBA buffer, width, height, and the same float loaded from `[rbp+0x608]` for the `+0x08` path. `+0x10` receives the same stack slot in assembly even though the decompiler omits the trailing float in `FUN_18114ffd0`'s prototype.

- `FUN_18114fd90` is the premultiply/alpha-union-style aggregator.
  - It clears the output float RGBA buffer via `FUN_181150250(param_7, width * height * 4, zero)`.
  - It loops five layers per pixel.
  - It reads `ray = *(float *)(*ray_ptr + pixel_index * 4)`.
  - If `ray <= DAT_181489990` it skips contribution and keeps the current output alpha.
  - Otherwise it computes `alpha = clamp(ray * param_10)` with `FUN_181156740`.
  - It selects either the fixed layer color or ramp color (`FUN_181232080`) and adds premultiplied RGB: `rgb += color.rgb * alpha`.
  - It updates alpha as `a = a + alpha - a * alpha`.
  - After the five layers, if alpha is positive it clamps alpha and normalizes RGB by `1 / alpha`.

- `FUN_18114ffd0` is the additive/clamp-style aggregator.
  - It also clears the output float RGBA buffer first.
  - It loops five layers per pixel and skips `ray <= DAT_181489990`.
  - For active layers it selects fixed/ramp color, adds color channels directly (`rgb += color.rgb`), and adds raw ray to alpha (`a += ray`).
  - After the five layers, it clamps each channel independently with `FUN_181156740`.
  - Unlike `FUN_18114fd90`, the decompiled body does not multiply ray by the trailing Brightness/Gain float and does not normalize RGB by alpha.

- Parameter registration confirms UI ids and default units:
  - `Brightness/Gain` is parameter id `2`, registered as a float slider/default around `1.0`.
  - `Glow Opacity` is parameter id `7`, registered as percent default `100`.
  - `Source Opacity` is parameter id `0xc`, registered as percent default `100`.
  - CLI parsing matches these ids: suffix `-0002` -> `brightness_gain`, `-0007` -> `glow_opacity / 100`, `-0012` -> `source_opacity / 100`.

- Current CLI aggregation mirrors the confirmed `FUN_18114fd90` shape in `aggregate_fd90_exact`: five buffers ordered `{vertical, horizontal, diagonal, highlight_zero, diagonal2}`, active-layer skip, `clamp(ray * brightness) * color.a`, alpha union, then RGB normalization by final alpha.

## Ambiguous / Not Confirmed

- The exact semantic use of the per-ray scalar array in final aggregation is still ambiguous.
  - `FUN_18114f4a0` definitely stores one scalar per ray/helper result and passes the scalar array into the vtable aggregator call.
  - `FUN_18114fd90` and `FUN_18114ffd0` bodies, as decompiled, index only the ray pointer array for pixel values. The scalar array may be part of color/ramp metadata, may be consumed by another vtable implementation, or may be obscured by decompiler parameter naming.
  - Existing equal-length all-ray refs cannot isolate whether helper-return scalar / `length^2` materially changes final aggregation.

- Brightness/Gain flow is confirmed into `FUN_18114fd90` but not confirmed as active in `FUN_18114ffd0`.
  - `FUN_18114fd90` uses trailing `param_10` directly as the `ray * brightness` scale before clamping.
  - Assembly shows the same stack slot is prepared for the `+0x10` dispatch, but the visible `FUN_18114ffd0` body does not read/use it.

- Source/glow opacity ordering is not proven by `FUN_18114fd90` / `FUN_18114ffd0` themselves.
  - These functions produce an intermediate float RGBA glow/output buffer; they do not compose source pixels with glow pixels.
  - The CLI currently applies source opacity first to source alpha/color and glow opacity to aggregated glow alpha before merge composition.
  - Existing `OLMKiraKira_ASM_FACTS.md` still lists merge-mode dispatch and source/glow opacity ordering for `+0x08 FUN_18114fd90` / `+0x10 FUN_18114ffd0` as a confirmation target, so treat composition ordering as pending unless a separate compose-site audit confirms it.

## Reference Gap

- The current tracked refs use equal ray lengths and `Glow Rotation=0`, so they cannot separate ray order, angle mapping, helper scalar / `length^2`, or single-ray crop behavior.
- The already pending `refs/reference_requests/kirakira_single_ray_20260606.json` remains the right reference request for isolating these scalar/ray-order questions.
