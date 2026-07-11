# OLMDistanceGradation 0010/0011 Field-World Pack/Read Contract

Date: 2026-07-09

Request id:
`olmdistancegradation_0010_0011_field_world_pack_read_witness_20260709`

## Purpose

This is the narrowed successor to
`olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709`.

The previous pointer-map return is useful but incomplete:

- it binds the final PF16 output address formula
  `out = base + y * 0x3c00 + x * 8`;
- it binds Windows final PF16 output words for `case_0010` `(6,40)` and
  `(901,394)`;
- it does not include a same-run true16 TIFF/EXR export sample;
- it does not explain the field-world pack/read boundary that feeds
  `FUN_181170480`.

The local AEX CPU fieldgen probe then showed that the real AEX helper, with
validated OpenCV detours, reproduces the current Mac float fields:

| Probe | XY | field X | field * 32768 | Windows-required field word |
| --- | --- | ---: | ---: | ---: |
| case0010 inside | `(901,394)` | `0.698593139648` | `22891.5` | `22892` |
| case0010 outside | `(6,40)` | `0.900283813477` | `29500.5` | `29500` |
| case0011 inside | `(915,392)` | `0.134536772966` | `4408.50097656` | `4409` |

So this request is not asking for broad output stepping, a fieldgen topology
hunt, or final writer tuning. It asks for the exact field-world pack/read path
in the live Windows AE run.

## Required Case Path

Use the exact 16bpc Software request:

`handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/`

Primary case:

- `olmdistancegradation_extended__case_0010`

Target pixels:

- `(6,40)` outside witness: Windows needs floor of the local AEX field float.
- `(901,394)` inside witness: Windows needs ceil of the local AEX field float.

Optional control:

- `olmdistancegradation_extended__case_0011` at `(915,392)`, another inside
  witness requiring ceil.

## Required Facts

For each target pixel, capture direct same-run facts where possible:

- the source alpha ownership/mask value;
- the raw distance after `cvDistTransform`;
- the value after threshold clamp;
- the min/max or normalization denominator used by the live Windows run;
- the float field value before any PF16/field-world storage;
- the field-world pointer, rowbytes, pixel size, and channel layout;
- the field-world stored word(s) if a PF16/16-bit/byte field world exists;
- the value read by `FUN_181170480` before invert;
- the composed `out_a` / RGBA float immediately before PF16 output store;
- the final PF16 output words;
- same-run true16 TIFF/EXR exported sample if available.

## Acceptance Rule

Satisfactory:

- both primary `case_0010` pixels bind field float, field-world stored/read
  value, compose/pre-store float, and final PF16 output word; and
- the answer explains why one witness follows floor and the other follows ceil,
  or proves the split occurs before field-world packing.

Partial:

- one primary pixel is fully typed; or
- field-world pointer/layout is explicit but the target watchpoint fails with
  exact address/register reason.

Failed:

- broad PF interleave hits without field-world pack/read binding;
- final PNG/display bytes only;
- package-local recomputation;
- Windows-implied store words without a direct live stop;
- resending the old pointer-map result unchanged.
