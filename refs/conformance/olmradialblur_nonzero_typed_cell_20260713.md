# OLMRadialBlur actual-AEX nonzero typed cell (2026-07-13)

## FACT

- The bounded Zoom probe previously parsed `--source-x/--source-y` but passed
  the full image back into `prepare_direct_zoom_context`, which silently
  reselected the top-left crop. The probe now passes the already cropped image.
- Existing top-left regression smoke still passes.
- Source crop `(416,288,32,32)` contains nonzero RGB and reaches the actual AEX
  normalization boundary `0x180005d99`.
- `FUN_18000b150` receives typed source RGBA `[1,0,0,1]` for the captured rows.
- All 196 polar cells have nonzero accum/denom/valid fields.
- The first four cells are:
  - accum `[1,0,0,1]`
  - denom `1.0`
  - valid `1.0`
  - final `[1,0,0,1]`
- Machine-readable evidence:
  `olmradialblur_nonzero_typed_cell_20260713.json`, SHA-256
  `16e3a79bb278619e795f4d341caef79357d5f80dde486edf287766923d7df8db`.

## CLASSIFICATION

`local actual-AEX typed producer/plane liveness`. This closes the prior local
gate requiring a bounded nonzero RGB cell. It does not prove full-frame
case_0009 semantics or AE exactness. Next compare the same cropped geometry and
polar cells against the portable/Mac implementation; only then request a
Windows full-frame confirmation if the local binary/port delta remains.

## Portable-prefill differential

The same crop was rerun with `--python-prefill`. Its intermediate accumulator
scale diverges at cell 1 (`AEX=[1,0,0,1]`, Python-prefill path approximately
`[1.99999845,0,0,1.99999845]`), but denominator normalization produces the
same final `[1,0,0,1]`. The complete `bounded_output_samples` records,
including `(7,0)`, `(8,0)`, and `(24,0)`, are identical for this uniform-red
witness. This closes the final sampler/normalization lane only for this
controlled crop; it does not validate nonuniform case_0009 prefill semantics.

Python-prefill evidence:
`olmradialblur_nonzero_typed_cell_python_prefill_20260713.json`, SHA-256
`7cde43b4cfc4ee93b3142236491074687afd845c71f91084f43db76b395a98f4`.

## Full-plane nonuniform differential

A higher-variation crop `(1504,864,32,32)` was then compared over all 196
polar cells using raw plane SHA-256 values. Actual AEX and Python-prefill runs
have identical:

- final RGBA plane: `6fc114c6e7b87419dea99d64c705ab08ff77be310e7c97785e09c405a8e6ff4c`
- denom plane: `fff91e873df93b4fe0f83d2e7a763bf00af8fe4a51f4e5662a433611336db00a`
- valid plane: `fff91e873df93b4fe0f83d2e7a763bf00af8fe4a51f4e5662a433611336db00a`

Only pre-normalization accum differs (`6fc114...` actual versus `9166b6...`
Python), and normalization removes that scale difference exactly. This closes
the bounded portable prefill -> normalized final-plane lane for this
nonuniform witness. Remaining case_0009 work is downstream sampling/full-frame
coordinate formation or host context, not this normalized polar plane.

Evidence JSON SHA-256:

- actual AEX: `0c2c022a80f2881d0b684b94386002e2b8b07d693c3d7f9b72f954d906494e88`
- Python prefill: `e25c728a2354e5b5e83124b14a5bc1a16ac377cb890f124685c3ff82dc83ccbc`
