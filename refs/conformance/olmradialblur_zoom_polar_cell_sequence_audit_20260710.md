# OLMRadialBlur Zoom Polar Cell/Float Sequence Audit

Date: 2026-07-10
Case: `case_0009`, 8bpc Zoom, Windows Software reference

## Verdict

The smallest binary-grounded live mismatch is the **coordinate/float sequence**, not
the final byte writer or a uniform cell offset:

1. The current C++ Zoom default computes polar prefill coordinates with `double`
   (`theta`, `sin/cos`, radius products, rotation products, and center adds), then
   stores `sx/sy` as `float`.
2. The AEX Zoom core at `FUN_1800056f0+0x3a00` computes the same geometric formula
   as scalar `float`: `float(ai) * float(step)`, paired trig through
   `FUN_18001d060`, radius/trig products with `MULSS`, then ordered rotation
   `MULSS`/`SUBSS`/`ADDSS` operations and float center adds. See
   `disasm/OLMRadialBlur.aex.asm.txt:4410-4447` and
   `decomp/OLMRadialBlur.aex.c.txt:2490-2515`.
3. The current C++ inverse coordinate path also computes `dx/dy`, rotated `ex/ey`,
   `sqrt`, and `atan2` in `double`, then casts only `radius_index` and
   `angle_index` to `float` (`cli/OLMRadialBlur/main.cpp:1341-1354`). The AEX
   inverse geometry is documented as float `sqrt`/`atan2f` and feeds the final
   sampler `FUN_180009d80` (`notes/OLMRadialBlur_ASM_FACTS.md:533-541`,
   `decomp/OLMRadialBlur.aex.c.txt:4918-4987`).

This identifies a **candidate local parity change**, but does not authorize editing
the CLI in this audit: no full-size typed Windows final-plane witness exists, and
the reduced AEX run proves only prefill parity for `32x32/q90`.

## FACT

- The AEX prefill loop is angle-major and radius-minor. It computes the angle as
  `CVTDQ2PS -> MULSS [step]`, calls `FUN_18001d060`, uses the returned paired
  trig values, converts the integer radius with `CVTDQ2PS`, and performs the
  rotation in ordered scalar float instructions. The source coordinates are
  therefore, in operation order:

  `theta_f = f32(ai) * f32(step)`

  `sin_f, cos_f = FUN_18001d060(theta_f)`

  `x0 = f32(f32(radius) * cos_f)`

  `y0 = f32(f32(f32(radius) * sin_f) * ratio_f)`

  `sx = f32(f32(f32(cos_a_f * x0) - f32(sin_a_f * y0)) + cx_f)`

  `sy = f32(f32(f32(sin_a_f * x0) + f32(cos_a_f * y0)) + cy_f)`.

- `FUN_18001d060` is not evidence for an arbitrary coordinate offset. It is the
  AEX scalar paired-trig helper (`disasm/OLMRadialBlur.aex.asm.txt:26917-26932`);
  the helper dispatches to the plugin's float math implementation.

- The current CLI has an opt-in `--zoom-grid-mode aex-float` branch, but its
  default is `double` (`cli/OLMRadialBlur/main.cpp:76-80`). Even that diagnostic
  branch calls `std::cos` and `std::sin` separately and does not reproduce the
  binary's paired helper call exactly (`cli/OLMRadialBlur/main.cpp:1204-1230`).

- The AEX final bilinear sampler is scalar float arithmetic: integer conversion
  uses `CVTTSS2SI`, fractions use `SUBSS`, weights/products use `MULSS`, and
  accumulation is ordered `ADDSS`; RGB normalization uses `DIVSS`
  (`disasm/OLMRadialBlur.aex.asm.txt:19-30,51-133`).

- Local final-sample sequence testing rejects arithmetic order as the missing
  rule. `f32_products_sum_double` hits `[6,7,12]` but adds eleven false
  positives; sequential/grouped variants miss targets
  (`refs/conformance/olmradialblur_zoom_case0009_final_sample_float_sequence_20260709.md:8-35`).

- Local cell-set testing rejects a uniform final-plane offset. The best tested
  candidate, `cpp-double`, angle `+1`, radius `-2`, truncate, hits all three
  targets but also emits `[3,4,8,10,11,13,24,25,26,27,28]`
  (`refs/conformance/olmradialblur_zoom_case0009_cellset_candidate_20260709.md:9-17,32-41`).

- The local current cells for `(7,0)` are all alpha `1.0`, while Windows writes
  alpha `254`; this rejects a pure late quantizer explanation
  (`refs/conformance/olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.md:9-19`).

- The local AEX CPU reduced-geometry run matched original prefill cells exactly
  (`max_abs_diff=0.0`) at the pre-worker boundary, but this is only `32x32/q90`
  evidence (`refs/conformance/olmradialblur_zoom_python_prefill_validation_20260708.md:5-12,21-49`).

- The latest Windows final-plane request is `failed_partial`: it contains no
  same-run cell IDs, per-cell floats, bilinear weights, or retained hook failure
  artifact (`refs/reports/runtime_trace_comparisons/olmradialblur_zoom_case0009_final_plane_cells_20260709.md:3-14`).

## INFERENCE

- The live C++ divergence is most narrowly described as **which polar cells are
  reached after scalar-float coordinate generation**, including the paired-trig
  result and ordered rounding. The final index candidates in the 20260709 probes
  are useful diagnostics, but none is binary-grounded enough to promote to a
  source change.

- If a local parity patch is later approved, the smallest defensible change is to
  make the Zoom path use a dedicated scalar-float paired-trig helper and float
  temporaries for the exact prefill sequence above, then separately make the
  inverse `dx/dy -> sqrtf/atan2f -> index` path float. Do not add a fixed angle or
  radius bias. This is a parity experiment, not an accepted implementation change.

- Current recommendation: **no source edit** until a full-size Windows witness
  captures `(6,0)`, `(7,0)`, `(12,0)` plus controls `(8,0)` and `(24,0)` with the
  actual final-plane cells and pre-byte alpha. The emulator's staging bottleneck
  remains upstream of the useful full-size Zoom worker
  (`refs/conformance/olmradialblur_zoom_emulator_dispatch_bottleneck_20260708.md:3-21`).

## Commands Run

```bash
rg -n "polar|zoom|cell|prefill|final|sample|float|mulss|addss|subss|divss|sqrt|round|trunc|floor|ceil" decomp/OLMRadialBlur.aex.c.txt disasm/OLMRadialBlur.aex.asm.txt cli/OLMRadialBlur/main.cpp
nl -ba disasm/OLMRadialBlur.aex.asm.txt | sed -n '4410,4447p;26917,26932p'
nl -ba decomp/OLMRadialBlur.aex.c.txt | sed -n '2490,2515p;4918,4987p'
nl -ba cli/OLMRadialBlur/main.cpp | sed -n '1159,1238p;1341,1394p'
nl -ba refs/conformance/olmradialblur_zoom_case0009_final_sample_float_sequence_20260709.md | sed -n '1,35p'
nl -ba refs/conformance/olmradialblur_zoom_case0009_cellset_candidate_20260709.md | sed -n '1,41p'
nl -ba refs/conformance/olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.md | sed -n '1,79p'
nl -ba refs/conformance/olmradialblur_zoom_python_prefill_validation_20260708.md | sed -n '1,49p'
nl -ba refs/reports/runtime_trace_comparisons/olmradialblur_zoom_case0009_final_plane_cells_20260709.md | sed -n '1,24p'
```

No source file, Windows package, or staging artifact was edited.
