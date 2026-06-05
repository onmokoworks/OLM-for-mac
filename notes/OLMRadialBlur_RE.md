# OLMRadialBlur Reverse-Engineering Notes

Status: initial decomp pass only. No CLI output is claimed correct yet.

## Reference Cases

Use `python3 refs/scripts/audit_olmradialblur_manifest.py` to print the Windows
reference manifest with Outer Blur and Inner Blur separated.

Best first target:

- `case_0010`: Blur Type=2 (Rotation), Outer Strength=4, Inner Strength=0,
  Repeat Border=1, Ratio=1, Angle=0, Quality=5, Size Variation=0,
  Noise Variation=0. This is the smallest Rotation slice.

Useful next targets:

- `case_0001`: Rotation, stronger outer blur, no inner/noise.
- `case_0002`: Rotation, outer offset enabled.
- `case_0009`: Zoom, strong outer blur, no inner/noise.
- `case_0008`: full hard case with inner+outer, ratio/angle, size/noise
  variation. Do not start here.

## Parameter Reader

`FUN_180008690` reads AE params into the render struct:

- `+0x20`: Blur Type, param 1. `1=Zoom`, `2=Rotation`.
- `+0x28/+0x30`: Center, param 2.
- `+0x64`: Outer Strength, param 4.
- `+0x54`: Outer Offset Mode, param 28.
- `+0x58`: Outer Offset, param 29.
- `+0x6c`: Outer Edge Fade, param 5.
- `+0x68`: Inner Strength, param 8.
- `+0x5c`: Inner Offset Mode, param 30.
- `+0x60`: Inner Offset, param 31.
- `+0x70`: Inner Edge Fade, param 9.
- `+0x74`: Repeat Border, param 26.
- `+0x78`: Ratio, param 12.
- `+0x7c`: Angle radians, param 13 degrees multiplied by pi/180.
- `+0x80`: Quality step. Stored as `1.0 / Quality` if Quality > 0, otherwise
  `0.2`.
- `+0x38`: Brightness Gain, param 16.
- `+0x40`: Size Variation, param 17, multiplied by 0.01.
- `+0x44`: Size variation enabled if scaled value > 0.0001.
- `+0x3c`: Noise Variation, param 19, multiplied by 0.01.
- `+0x50`: Noise Type, param 20. If value is 3, param 21 Noise Layer is read.
- `+0xfc`: Seed, param 22.
- `+0x100`: Noise Offset, param 23.
- `+0x104`: Thickness, param 24.

Constants confirmed from `plugins_2025/OLMRadialBlur.aex`:

- `DAT_1800212d0 = 0.2f`
- `DAT_1800212d4 = 1.0f`
- `_DAT_1800212d8 = pi / 180`
- `_DAT_1800212e0 = 2*pi`
- `_DAT_1800215f8 = 0.01f`
- `_DAT_180021600 = 0.0001`
- `DAT_180021608 = 0.2`
- `_DAT_180021624 = 360.0f`
- `DAT_1800216c8 = 0.5f`
- `DAT_1800216cc = 3.0f`

## Render Path

`FUN_1800040f0` dispatches by pixel depth after `FUN_180008690`.

8-bit path `FUN_180007520`:

1. Converts source pixels into float RGBA buffers.
2. Builds noise/size maps when Noise Type / Noise Variation require it.
3. Calls `FUN_180006830` to apply noise or noise layer into the per-pixel
   variation buffer.
4. Branches:
   - Blur Type 1: `FUN_18000a7e0`, `FUN_18000a810`, then `FUN_1800056f0`
     (Zoom).
   - Blur Type 2: `FUN_180001a90`, `FUN_180001ac0`, then `FUN_180004640`
     (Rotation).
5. Converts float output buffer back to 8-bit with Brightness Gain.

## Rotation Body

`FUN_180004640` implements Rotation:

- Initializes angle basis from Ratio/Angle and Center.
- Computes min/max radial span with `FUN_180001bb0`.
- Allocates polar-grid buffers. Angular resolution is derived from `360.0 /
  quality_step`; since quality_step is `1 / Quality`, case Quality=5 produces
  roughly 1800 angular samples before integer truncation.
- Source sampling:
  - Repeat Border off: `FUN_180001270` / `FUN_180001800`.
  - Repeat Border on: `FUN_180001520` / `FUN_180001950`.
- Coordinate conversion:
  - `FUN_180001b10`: XY -> radius/angle for the final inverse lookup.
  - `FUN_180001bb0`: computes radius bounds around the center.
- Blur passes:
  - `FUN_180002780`: one accumulation pass.
  - `FUN_1800024c0`: second accumulation pass using segment/validity data.
  - `FUN_180001c90`: inner/outer strength and offset-mode helper.
- Final inverse sampling uses `FUN_180001000` over the polar-grid buffer.

### Rotation Inner/Outer Scatter Facts

2026-06-06 decomp recheck:

- `FUN_180001c90(param_2=0)` is the outer-direction angular scatter:
  - blur mode/offset mode comes from `param_1 + 0x24`
  - base strength/offset comes from `param_1 + 0x3a9e8`
  - Gaussian table base is `param_1 + 0x68`
  - offsets advance angular index forward in the same radius row, wrapping to
    angular index `0`
- `FUN_180001c90(param_2=1)` is the inner-direction angular scatter:
  - blur mode/offset mode comes from `param_1 + 0x2c`
  - base strength/offset comes from `param_1 + 0x3a9ec`
  - Gaussian table base is `param_1 + 0x1d528`
  - offsets decrement angular index; on negative wrap the pointer moves to
    `(radius + 1) * angular_count`, matching the previously measured
    `aex-next-row` diagnostic shape
- For both directions, mode handling is:
  - mode `1`: add dynamic offset `param_3` to base length
  - mode `2`: max(base length, dynamic offset)
  - mode `3`: use dynamic offset directly
  - length is clamped to `3000`
  - effective length is `int(length * param_10)`
  - table stride is `30000 / effective_length`
- `FUN_1800024c0` calls `FUN_180001c90` outer first and inner second for each
  valid source cell. The dynamic offset passed as `param_3` is
  `int((param_7 / 2) * strength_or_offset_mode_value / radius_row)`, where
  `param_7` is radial grid height and `radius_row` is the current row index.
- `FUN_180002780` prepass writes the source RGBA consumed by
  `FUN_1800024c0`: when source alpha and the sampled base/validity buffer are
  nonzero, it gathers alpha in both angular directions and writes
  `out.rgb = gathered_alpha * input.rgb`, `out.a = gathered_alpha`.
  The backward/outer-side prepass table is `param_1 + 0x3a9f0`; the
  forward/inner-side prepass table is `param_1 + 0x3b990`. The gathered alpha
  is normalized by the total prepass weight sum.

Current implication: the existing C++ diagnostics already model many isolated
pieces of this, and the rejected probes show no global switch is enough. The
next useful implementation probe should combine exact prepass table selection,
the `param_1+0x10` sampled base/validity buffer, and `FUN_180001c90`'s
direction-specific row/angle pointer movement rather than tuning final alpha
or replacing one table/seed mode globally.

## Zoom Body

`FUN_1800056f0` mirrors the Rotation structure for Zoom:

- Coordinate helpers are `FUN_18000a850` and `FUN_18000a8f0`.
- Source samplers are `FUN_180009fc0`/`FUN_18000a550` when Repeat Border is off,
  and `FUN_18000a270`/`FUN_18000a6a0` when on.
- Blur passes are `FUN_18000b150` and `FUN_18000a9d0`.
- Final inverse sampling uses `FUN_180009d80`.

Current Zoom CLI:

- `refs/scripts/olmradialblur_cli.py --algorithm zoom-direct` remains as the
  original simple inward center-ray sampler for Blur Type=1.
- `refs/scripts/olmradialblur_cli.py --algorithm zoom-polar` implements the
  AEX-shaped Zoom no-noise slice: build an angle-major radius grid with
  `FUN_18000a850`/`FUN_18000a8f0` coordinate semantics, scatter along the
  radius axis with Zoom's direct `FUN_18000b680` Gaussian table, then
  inverse-sample with `FUN_180009d80`'s alpha-weighted bilinear sampler.
- `refs/scripts/smoke_olmradialblur_zoom_cli.py` runs `case_0009`
  (Zoom, Outer Strength=1717, no inner/no noise/no size variation) as a
  near-match regression guard.
- `case_0009` identity baseline: `max=255`, `mean=23.0118`,
  `nz=1982738/2073600`.
- `case_0009` zoom-direct scaffold: `max=233`, `mean=21.1533`,
  `nz=1982569/2073600`.
- `case_0009` first zoom-polar scaffold, incorrectly scaling Strength by
  `1 / Quality`: `max=150`, `mean=14.3105`, `nz=2051221/2073600`.
- `case_0009` current zoom-polar, using Strength itself as the radius-table
  length: `max=1`, `mean=0.0058`, `nz=40768/2073600` (passes the smoke gate:
  max<=1, mean<=0.01, nz<=2.1%).
- `refs/scripts/smoke_olmradialblur_zoom_offset_cli.py` runs `case_0003..0005`
  (Zoom, Outer Strength=212, Offset Mode=1, Offset=153, Quality=1,
  Size Variation=50, no noise) with `--ignore-size-variation`. This is a
  guard for the current Zoom/Offset baseline, not a Size Variation claim:
  all three cases pass at `max=8`, `mean=0.0145`.
- Probe result: scaling `Strength * (1 / Quality)` by 5.0, i.e. using the UI
  Strength directly, improved `mean=14.3415` to `mean=0.0058`. So Blur Type=1
  should not inherit Rotation's angular Strength scaling; Quality controls the
  angle-grid count, while Zoom's radial blur table follows the Strength value.
- Probe result: applying Offset Mode=1 as `Strength + Offset` worsened
  `case_0003` to `mean=4.0360`; keeping the radius-table length at Strength
  gives `mean=0.0145`. So Zoom Offset Mode=1 currently must not extend the
  radius blur table length. The offset probably feeds another pass detail that
  is not needed for these near-matching cases.
- Rejected probe: reversing the outer radial scatter worsens to
  `max=254`, `mean=22.3328`, `nz=2073275/2073600`, so the outer direction is
  currently kept as increasing radius/outward.
- Rejected/diagnostic probes: angle index offsets `-1..+1` are worse than zero;
  radius offset `-1` is slightly better (`mean=14.2848` before the Strength
  fix) but much smaller than the Strength-scale correction, so radius offset is
  treated as a remaining boundary/indexing detail rather than the main model.

This slice is now close enough to guard automatically. The remaining max=1
residual appears to be 8-bit rounding / alpha-floor level: input alpha is fully
255, the Windows reference has some 254-alpha pixels, and the candidate remains
255-alpha. Size Variation is still explicitly ignored in the offset smoke, and
Noise is still not implemented.

C++ Zoom slice:

- `cli/OLMRadialBlur/main.cpp` ports the Zoom polar no-inner/no-noise kernel for
  the offset cases. It reads grouped Outer/Inner params from the AE manifest,
  builds the angle-major radius grid, scatters outward along radius using the
  Zoom Gaussian table, then inverse-samples with alpha-normalized bilinear
  sampling.
- This first C++ version intentionally supports only Blur Type=1 (Zoom),
  Inner Strength=0, Noise Variation=0. `Size Variation` must be ignored with
  `--ignore-size-variation`, matching the Python guard for `case_0003..0005`.
- `refs/scripts/build_olmradialblur_cli.sh` builds it, and
  `refs/scripts/smoke_olmradialblur_cpp_cli.py` verifies cases
  `0003..0005`: `max=8`, `mean=0.0059`, ok=3.
- Large-strength `case_0009` (Strength=1717) now uses a C++ FFT forward
  convolution path for the radius scatter. `refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py`
  verifies it at `max=1`, `mean=0.0046`, ok=1.
- Quantization note: the small direct path keeps a tiny RGB/alpha floor epsilon
  to match `case_0003..0005`; the FFT path keeps that epsilon for alpha but not
  RGB, which removes the one-pixel `max=2` overshoot observed in `case_0009`.

Mac AE integration:

- `mac/OLMRadialBlur/` now builds as `OLM RadialBlur` with match name
  `OLM RadialBlur`.
- The current plug-in ports the C++ Zoom/no-inner/no-noise kernel into 8bpc
  SmartRender/classic Render. It includes the same large-Strength FFT forward
  convolution path as the C++ CLI, so `case_0009`-style Zoom does not fall back
  to the slow direct radius loop. Size Variation is intentionally ignored for
  this slice, matching the `case_0003..0005` CLI guard; the actual modulation
  is not implemented yet.
- The plug-in also ports the C++ Rotation/no-inner/no-noise/no-size-variation
  slice into `RenderRotation8`, including the radius-dependent Offset Mode=1
  branch used by broad Rotation `case_0002`. This matches the current C++ CLI
  measurement scaffold, not an exact final port.
- Unsupported paths (nonzero Inner Strength, Noise Variation, unsupported Size
  Variation for Rotation, and 16/32bpc) currently copy the input rather than
  claiming correctness.
- `scripts/build_all_mac_plugins.sh` includes this project and verifies the
  Debug bundle as universal (`arm64` + `x86_64`) with `codesign --verify`.
- AE-host validation is still pending; the local environment can only prove
  build/universal/codesign and AE-free CLI behavior.

## Noise

`FUN_180009380` creates a Mersenne-Twister-like noise map using Seed, Thickness,
and Offset. `FUN_180009680` samples it with optional smooth interpolation.

Defer this until the no-noise cases above have a matching baseline.

## Experimental CLI Baseline

`refs/scripts/olmradialblur_cli.py` contains a deliberately incomplete direct
Rotation sampler. It is only a measurement scaffold for the first slice, not
the final algorithm.

Smoke:

```sh
python3 refs/scripts/smoke_olmradialblur_rotation_cli.py
```

Current `case_0010` results:

- identity baseline (`identity_image_cli.py`): `max=255`, `mean=1.1796`,
  `nz=148816/2073600`.
- direct Rotation, wrongly treating Strength=4 as 4 degrees:
  `mean=3.5529`.
- direct Rotation after AEX grid scaling (`Strength * 0.2deg` at Quality=5),
  default direction: `mean=2.0812`.
- direct Rotation with reversed outer direction: `max=255`, `mean=1.3977`,
  `nz=188768/2073600` (best direct probe so far).
- polar-grid scatter experiment with corrected 30000-sample Gaussian table and
  AEX-style final alpha-normalized sampler: `max=255`, `mean=0.2907`,
  `nz=161439/2073600`.
- same path with floor-like 8-bit quantization: `max=255`, `mean=0.2864`,
  `nz=155419/2073600`.
- polar-grid with AEX-style Strength-1 blur tail: `max=255`, `mean=0.0104`,
  `nz=33794/2073600` (current default). The alpha max residual is only 1; the
  remaining `max=255` comes from sparse boundary/transparent-RGB differences.
- rejected probes:
  - polar scatter reverse direction: `mean=1.2781`.
  - center offset `-0.5` / `+0.5`: `mean=0.4154` / `0.4178`; exact scaled
    center is best for `case_0010`.

Current `case_0001` results (same outer-only/no-noise class, Strength=540):

- identity baseline: `max=255`, `mean=7.5294`, `nz=1498380/2073600`.
- polar-grid FFT scatter experiment with Strength-1 tail: `max=255`,
  `mean=1.9039`, `nz=711827/2073600`.
- rejected probe, angular grid half-step offsets: integer shifts preserve the
  current result (`mean=1.9038..1.9039`), but half/quarter-step offsets worsen
  to `mean=1.9338..1.9507`. The zero-based angular table from
  `FUN_180004640` is therefore still the best interpretation.
- rejected probe, final sampler/intermediate normalization variants:
  `FUN_180001000`-style alpha-normalized final sampling remains best.
  Raw straight bilinear and premultiply-then-unpremultiply both worsen slightly
  (`mean=1.9045`), while normalizing the scatter by max alpha or skipping the
  scatter normalization explodes to `mean=142.2530`.

The FFT scatter path is used for large kernels (`Strength >= 64`) so this case
can be measured without hundreds of full-grid `np.roll` passes.

Current `case_0002` results (outer-only/no-noise, Strength=212, Offset Mode=1,
Offset=153):

- identity baseline: `max=255`, `mean=6.9395`, `nz=1408841/2073600`.
- polar-grid FFT scatter with AEX-inspired `effective_strength = Strength +
  Offset - 1`: `max=255`, `mean=1.9582`, `nz=990115/2073600`.
- polar-grid with `FUN_1800024c0`'s radius-dependent Offset Mode=1 span
  (`int((radius_count/2 * Offset) / (radius_index+1))` before
  `FUN_180001c90` combines it with Strength): `max=255`, `mean=1.3077`,
  `nz=520250/2073600` (current default).
- rejected probe, ignoring Offset: `mean=2.6050`.

So Offset Mode=1 is usefully approximated as additive for the current
outer-only slice, but the AEX radius-dependent span is substantially closer
than a constant additive length.

2026-06-05 probe notes for the remaining Rotation residual:

- Channel diff audit shows alpha is only a sparse one-step residual:
  `case_0001/0002/0010` all have `31204` alpha pixels off by `+1` in the
  candidate. RGB, especially the red channel on strong blur cases, dominates
  the mean difference.
- Using the scatter max-alpha buffer as the RGB normalization denominator is
  wrong: it worsens `case_0001` to `mean=142.2530`, `case_0002` to
  `mean=119.8239`, and `case_0010` to `mean=0.9553`. Keep RGB normalized by
  the weighted alpha sum.
- Quantization remains best as floor. `--quantize round` worsens to
  `case_0001 mean=2.0859`, `case_0002 mean=1.5241`, `case_0010 mean=0.0316`;
  `--quantize ceil` worsens further to `2.3800 / 1.8827 / 0.0595`.
- A naive alpha-only negative bias is not valid; after clipping it still
  worsens to `2.1463 / 1.5502 / 0.2529`. The alpha residual is likely upstream
  validity/sampling rather than a final quantization offset.
- Changing only the outer radius margin from `max_r + 2` to `max_r + 1`
  slightly improves the offset case (`case_0002 mean=1.3041`) while leaving
  `case_0001` and `case_0010` unchanged. `max_r + 3` matches the current
  result. This is too small to adopt but supports that case_0002's remaining
  gap sits near radius-span/validity handling.
- Scaling the `FUN_1800024c0` radius-dependent Offset Mode=1 term away from
  `1.0` is worse. Probes for `0.75 / 0.9 / 1.1 / 1.25 / 1.5` produced
  `case_0002 mean=1.5012 / 1.3600 / 1.4794 / 1.7292 / 2.1130`, so the current
  raw coefficient remains the best found.

Current `case_0011` results (Rotation, Outer Strength=62, Inner Strength=478,
no noise):

- identity baseline: `max=255`, `mean=96.0015`, `nz=1912481/2073600`.
- polar outer-only with `--ignore-inner`: `max=255`, `mean=73.9185`,
  `nz=1937371/2073600`.
- polar with the first reverse-scatter inner probe (`--experimental-inner`):
  `max=255`, `mean=63.4216`, `nz=1939117/2073600`.
- `case_0012` with `--experimental-inner`: `max=255`, `mean=15.4809`,
  `nz=828038/2073600`. Ignoring Offset improves only to `mean=14.0969`, so
  outer offset handling is not the main blocker.
- `case_0013` with `--experimental-inner`: `max=255`, `mean=20.0627`,
  `nz=934411/2073600`. Ignoring inner is worse (`mean=23.0514`), and ignoring
  Offset is also worse (`mean=21.9761`), so the current inner probe is
  directionally useful but structurally incomplete.
- `refs/scripts/smoke_olmradialblur_inner_cli.py` tracks cases
  `0011..0013` as an aggregate red measurement scaffold.

2026-06-05 inner alpha accumulator probe: `olmradialblur_cli.py` now exposes
`--inner-alpha-mode max|sum|outer|inner|input` for measurement only. The
default remains `max`, matching the current probe above. Results:

| mode | case_0011 mean | case_0012 mean | case_0013 mean |
|---|---:|---:|---:|
| max | 63.4216 | 15.4809 | 20.0627 |
| sum | 54.8108 | 17.8476 | 20.3022 |
| outer | 63.4216 | 14.4723 | 20.8289 |
| inner | 92.1468 | 14.2521 | 21.4477 |
| input | 92.1468 | 13.1667 | 22.2504 |

This rules out a single alpha-accumulator swap as the inner-blur fix. `sum`
helps the no-offset `case_0011`, while `input` helps the Offset Mode=3
`case_0012`, and the original `max` remains best for high-Quality
`case_0013`. The next useful RE target is the exact inner/offset/edge-fade
branching around `FUN_180001c90` and its caller rather than C++/Mac porting of
this experimental inner path.

Subagent/local decomp audit: `FUN_180001c90` itself does use a shared
accumulator for outer then inner, with RGB/denominator summed and the alpha
output tracked as max contribution. That supports the default
`--inner-alpha-mode max`; `sum` corresponds to the RGB denominator, not final
alpha. The bigger missing pieces are caller-side validity/weighting and
geometry, not a final alpha swap.

Rejected 2026-06-05 probes:

- A binned approximation of `FUN_180001c90`'s `length *= source alpha/validity`
  rule only nudged `case_0011` (`mean=63.0417`) and badly worsened
  `case_0012` (`mean=31.8404`) and `case_0013` (`mean=36.3246`). Do not adopt
  this approximation.
- AEX scales Rotation Strength/Offset/EdgeFade by `Quality / 5` before the
  angular-grid helper. The CLI exposes this as measurement-only
  `--rotation-quality-scale aex`, but applying it to the current incomplete
  inner model worsens `case_0013` from `mean=20.0627` to `mean=21.7408`.
  Keep the default as `none` until the surrounding validity/row-driver model is
  closer.

The inner probe is directionally better than ignoring inner, but still far too
wrong to treat as a supported slice. The CLI therefore refuses nonzero inner
blur in polar mode unless `--ignore-inner` or `--experimental-inner` is passed.
Use this as a measurement hook only; exact inner handling still needs the
remaining `FUN_180001c90`/validity/edge paths.

Additional decomp note: `FUN_180002780` prefilters the polar alpha/validity
before `FUN_1800024c0` calls the outer/inner scatter helper. The smoothing
lengths come from `param_1 + 0x3c930` and `param_1 + 0x3c934`, initialized in
`FUN_180004640` from Outer/Inner Edge Fade (`+0x6c` / `+0x70`) scaled by
`1 / Quality`. The prepass uses separate tables at `0x3a9f0` and `0x3b990`
and normalizes the gathered alpha before premultiplying source RGB. For the
current outer-only target cases the Edge Fade params are zero, so this path is
not expected to explain the remaining `case_0001` / `case_0002` / `case_0010`
residual by itself.

The polar-grid path is now clearly better than identity but still red, so do
not tolerance-green the broad smoke. `case_0010` is separately guarded by
`refs/scripts/smoke_olmradialblur_tiny_rotation_cli.py` with a near-match gate.
The useful findings are: AEX Strength is in angular-grid samples, not degrees;
the source sample is handled separately so the blur tail is effectively
`Strength - 1`; the outer scatter direction is increasing angular index; the
Gaussian table is always 30000 samples and then re-indexed by blur length;
Offset Mode=1 is radius-dependent via `FUN_1800024c0`, not a constant
`Strength + Offset`; the final inverse sampler is alpha-normalized as in
`FUN_180001000`; and the remaining gap is now in the detailed
`FUN_180002780`/`FUN_1800024c0` validity/weighting rules rather than the
high-level polar coordinate structure.

2026-06-05 C++ Rotation update:

- `cli/OLMRadialBlur/main.cpp` now includes a native Rotation polar-grid slice
  for Blur Type=2, outer-only/no-noise/no-size-variation cases. It ports the
  Python polar scaffold into C++: radius-major polar sampling, Rotation's
  30000-entry Gaussian-table mapping, circular angular scatter, alpha-normalized
  inverse sampling, and floor quantization with the same small alpha epsilon
  used by the Zoom C++ path.
- New guard: `refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py`.
  It builds the C++ CLI and verifies `case_0010` with the same near-match gate
  as the Python tiny Rotation guard. Latest result: `max=255`, `mean=0.0104`,
  ok=1.
- Existing C++ Zoom gates still pass after adding the Rotation dispatch:
  `smoke_olmradialblur_cpp_zoom_cli.py` remains `case_0009 max=1 mean=0.0046`;
  `smoke_olmradialblur_cpp_cli.py` remains cases `0003..0005 max=8
  mean=0.0059`.
- Broad C++ Rotation measurement after porting the radius-dependent Offset
  Mode=1 path gives `case_0001 max=255 mean=1.9034`, `case_0002 max=255
  mean=1.3071`, `case_0010 max=255 mean=0.0104`. This brings C++ `case_0002`
  down from the previous `mean=2.6174` to the Python scaffold level
  (`mean=1.3077`) by matching Python's `variable_scatter_accumulate()` /
  `FUN_1800024c0` radius-dependent dynamic offset.
- 2026-06-05 follow-up: the C++ Rotation CLI now also accepts nonzero Inner
  Strength as a measurement-only path. It mirrors the Python experimental
  model: outer scatters forward, inner scatters backward, the source sample is
  counted once, and final alpha uses the max-contribution buffer. New red
  measurement guard: `refs/scripts/smoke_olmradialblur_cpp_inner_cli.py`.
  Latest C++ Inner results are `case_0011 max=255 mean=63.4207`,
  `case_0012 max=255 mean=15.4790`, `case_0013 max=255 mean=20.0603`, tracking
  the Python probe closely. This is not a supported Mac plug-in slice yet.
- Subagent audit points the next likely fixes at `FUN_180001c90` and friends:
  keep RGB normalization by weighted-alpha sum, but model the separate
  max-contribution alpha/validity buffer more literally; split repeat-border
  RGBA sampling from validity sampling (`FUN_180001520`/`FUN_180001950`); then
  port `FUN_1800024c0` offset/inner handling instead of treating inner as a
  simple reverse blur.
- 2026-06-06 probe: `cli/OLMRadialBlur/main.cpp` now has a diagnostic
  `--polar-valid-mode strict|aex-repeat`, and
  `refs/scripts/smoke_olmradialblur_cpp_inner_polar_valid_probe_cli.py`
  measures whether Repeat Border should loosen the polar-grid validity buffer
  like `FUN_180001520` (`-2 < int(x) < width`, `-2 < int(y) < height`) instead
  of the previous strict image bounds. Result: mostly neutral. Strict gives
  `case_0011 mean=25.2972`, `case_0012 mean=10.6222`,
  `case_0013 mean=21.2910`; `aex-repeat` gives `case_0011 mean=25.1925`,
  `case_0012 mean=10.6245`, `case_0013 mean=21.2894`. Keep this as a
  measurement hook only; it does not explain the Inner residual.
- `mac/OLMRadialBlur/OLMRadialBlur.cpp` now carries the same 8bpc
  outer-only/no-noise/no-size-variation Rotation slice, including the
  radius-dependent Offset Mode=1 path. Unsupported Rotation cases (Inner,
  Noise, Size Variation, 16/32bpc) still copy input. `xcodebuild -project
  mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj -configuration Debug build
  CODE_SIGNING_ALLOWED=NO` succeeds after the update.
