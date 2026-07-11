# OLMRadialBlur Zoom Paired-Trig/Float-Inverse Diagnostic Probe

Date: 2026-07-10  
Case: `case_0009`, 8bpc Zoom, Windows Software reference

## Scope

This is a local C++ CLI diagnostic only. The Mac plugin was not modified. The
existing default path remains unchanged; both new behaviors require explicit
flags:

- `--zoom-paired-trig-float`: use a paired scalar-float sine/cosine helper
  boundary, then the AEX order of radius products, rotation products, and
  center adds.
- `--zoom-inverse-float`: use scalar-float `dx/dy`, ordered rotation, division,
  `sqrtf`, `atan2f`, and the binary-style double `2*pi` negative-angle add.

The flags are independent and can be combined.

Important evidence boundary: the paired diagnostic currently calls platform
`sinf` and `cosf`. It preserves the AEX call boundary and downstream scalar
operation order, but it does **not** reproduce the custom SIMD polynomial and
range-reduction body in `FUN_18001d060 -> FUN_18001d040`. Therefore the table
below rejects platform-libm paired trig plus the recovered coordinate order;
it does not yet reject the exact AEX trig helper.

The live Ghidra fact recorded for this probe is `FUN_18000a850` at `0x18000a850`:
`SUBSS` y/x deltas; `MULSS` cosine-y, sine-x, sine-y, cosine-x; `SUBSS` the
radial component; `ADDSS` the angular component; `DIVSS` the radial scale;
`MULSS` both squared terms; `ADDSS`; `SQRTSS`; `atan2f`; then, only for a
negative angle, `CVTSS2SD` + `ADDSD` `2*pi` + `CVTSD2SS`. The diagnostic path
now follows this order. The paired-trig helper fact is `FUN_18001d060`, xref'd
from `0x1800049a0` and `0x180005a0f`; its body uses `MOVSS/PAND/COMISS` and
the `ADDSS/UNPCKLPS` or `MULPS` polynomial return paths.

## Direct AEX Helper Check

After the CLI experiment, the local AEX CPU simulator called
`FUN_18001d060` directly and read the low two `XMM0` float lanes. This proves
that platform `sinf/cosf` is not bit-equivalent to the AEX helper:

| theta | AEX sin | AEX cos | libm f32 sin delta | libm f32 cos delta |
| ---: | ---: | ---: | ---: | ---: |
| `0.001` | `0.000999999931` | `0.999999464` | `+1.16e-10` | `-5.96e-08` |
| `0.1` | `0.0998334214` | `0.995004058` | `+7.45e-09` | `-1.19e-07` |
| `pi` | `-8.74227766e-08` | `-0.99999994` | `-8.74e-08` | `+5.96e-08` |
| `2*pi-0.001` | `-0.00100022939` | `0.999999464` | `-2.30e-07` | `-5.96e-08` |

The helper takes `10` instructions at zero and `88` instructions for the
sampled nonzero angles in the local Unicorn run. This is direct execution of
the Windows AEX code, not a decompiler formula guess.

## Witness Contract

Top-row targets are `(6,0)`, `(7,0)`, and `(12,0)`, each reference alpha
`254`. Controls are `(8,0)` and `(24,0)`, each reference alpha `255`.

| Variant | 6,0 | 7,0 | 12,0 | 8,0 | 24,0 | Target hits | False positives | Full-frame max | Mean | Nonzero pixels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 255 | 255 | 255 | 255 | 255 | 0/3 | 0 | 1 | 0.004613474 | 31,119 |
| paired trig | 255 | 255 | 255 | 255 | 255 | 0/3 | 0 | 1 | 0.004609134 | 31,097 |
| inverse float | 255 | 255 | 255 | 255 | 255 | 0/3 | 0 | 1 | 0.004608652 | 31,095 |
| paired trig + inverse float | 255 | 255 | 255 | 255 | 255 | 0/3 | 0 | 1 | 0.004603106 | 31,062 |

All variants preserve the five-witness RGB values observed in the local run;
only the alpha byte is relevant to this target/control split. No variant emits
a false-positive alpha `254` elsewhere in the top row.

## Result

The requested coordinate-order diagnostic is implemented and exercised, but it
does not explain the Windows Software target boundary with platform libm. The paired-trig-only
variant improves the full-frame residual by 22 pixels relative to baseline; the
exact inverse-only variant improves it by 24 pixels; and the combined variant
improves it by 57 pixels. All still miss the three target alpha-254 witnesses,
so these residual movements do not support a fix claim or promotion to the
default path.

The evidence supports keeping both switches isolated for future typed Windows
final-plane comparison. The next local binary-grounded experiment is to call
the actual `FUN_18001d060` helper across the case angular grid, export that
table, and feed it into the bounded CLI diagnostic together with the recovered
float inverse path. Do not retune offsets or the final quantizer. This result
does not support editing the Mac plugin.

## Commands

```sh
refs/scripts/build_olmradialblur_cli.sh /tmp/olmradialblur_zoom_diag_cli
python3 refs/scripts/run_reference_test.py \
  refs/win_references/20260604_olm/OLMRadialBlur \
  --run-dir /tmp/olmradialblur_case0009_paired_inverse_probe_20260710/<variant> \
  --case-id case_0009 --expected-effect "OLM RadialBlur" \
  --command '"/tmp/olmradialblur_zoom_diag_cli" --input "{input}" --params "{params}" --output "{output}" <flags>'
```

Variants tested were baseline, `--zoom-paired-trig-float`,
`--zoom-inverse-float`, and both flags together. The full-frame comparison used
the copied `case_0009.png` Windows Software reference and the corresponding
`case_0009_before_effects.png` input.
