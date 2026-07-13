# OLMDirectionalBlur front-only 8bpc exact closeout

## Verdict

The declared 8bpc front-only slice is `AE exact` for these Windows Software
references:

| Case | Front strength | Mac AE vs Windows AE |
| --- | ---: | --- |
| `db_angle0_strength_sweep_small` | 48 | `max_diff=0`, `differing_pixels=0` |
| `db_angle0_no_tail_no_size` | 240 | `max_diff=0`, `differing_pixels=0` |

Both Mac output PNG file hashes equal their Windows reference PNG hashes. The
actual run evidence is
`refs/reports/ae_single_case_dblur_frontonly_current_20260711/comparison.json`.

## Binary proof

The portable core executes the AEX choreography rather than the previous
direct-blur approximation:

1. AEX diagonal-derived square padding and centered RGBA8-to-float staging.
2. Alpha-weighted `FUN_180001ec0` rotate-in.
3. Copy-back plus `FUN_1800038d0` front-only rowdriver.
4. AEX worker-row truncation and RGB denominator normalization.
5. Zeroed destination plus `FUN_180001ec0` rotate-back.
6. Raw AEX truncating 8bpc writer semantics.

For `db_angle0_strength_sweep_small`, the complete portable raw ARGB8 output
and the actual-AEX full-entry capture share SHA-256
`ebfda2207558a335d35a3928fe623b6d6d5cc44a7e0befe89dc06cdf1c4d9544`.
The complete-core gate is
`tools/emulation/test_dblur_frontonly_current_exact_20260711.py`.

Independent actual-AEX gates also pass:

- rotate primitive: 6/6 fixtures byte-exact
- full rowdriver: 3/3 fixtures byte-exact
- current residual/control rows: 5/5 destination, denominator, and alpha
  buffers byte-exact
- rotate-back boundary/control targets: 7/7 float32 RGBA values byte-exact

## Host-stage correction

The former residual was 523 pixels on the top row: raw plug-in output
`[RGB=247,A=254]` versus rendered PNG `[RGB=246,A=254]`. All 1,569 differing
channel bytes become exact after a standard 8bpc premultiply model. This is an
AE/output-stage distinction, not permission to darken or premultiply inside
the plug-in. Both floor and nearest models give the same values for this
witness, so this case does not determine the host rounding subrule.

Evidence:

- `refs/conformance/dblur_ae_render_premultiply_closeout_20260711.json`
- `refs/conformance/dblur_rotateback_current_targets_20260711.json`
- `refs/conformance/dblur_rowdriver_current_rows_20260711.json`

## Integration scope

`mac/OLMDirectionalBlur` uses the exact shared core only when all of the
following are true:

- 8bpc, full-resolution render scale
- front-only blur
- Size Variation, front/back Sharp Tail, Back Strength, Back Alpha Fade, and
  Noise Variation are zero
- input and output worlds have identical dimensions

Front Alpha Fade now reaches the same complete shared core, and its current
2025-AEX PF input/output boundary is hash-pinned. It is still not promoted by
this closeout: the corrected Windows reference leaves the current Mac render
at `max_diff=3`, `980` differing values / `563` pixels. The broad Mac
architecture split is proven to come from platform `expf`; exact UCRT table
words are the next proof. See
`refs/conformance/dblur_alpha_host_boundary_20260711.md`. Size Variation, Sharp
Tail, Back, Noise, 16bpc, and 32bpc remain separate proof lanes.

## Verification commands

```text
python3 tools/emulation/test_dblur_rotate_exact.py
python3 tools/emulation/test_dblur_rowdriver_full_exact_20260711.py
python3 tools/emulation/test_dblur_rowdriver_current_rows_20260711.py
python3 tools/emulation/test_dblur_rotateback_current_targets_20260711.py
python3 tools/emulation/test_dblur_frontonly_current_exact_20260711.py
xcodebuild -project mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj -configuration Debug ONLY_ACTIVE_ARCH=NO ARCHS='arm64 x86_64' build
```
