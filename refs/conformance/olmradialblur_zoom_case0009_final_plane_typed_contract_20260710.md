# OLMRadialBlur Zoom case_0009 Final-Plane Typed Witness Contract

## Purpose

This is a single-run Windows runtime witness for the remaining `OLMRadialBlur`
Zoom `case_0009` top-row alpha residual. It follows the One Next Proof in
`refs/conformance/olmradialblur_zoom_remaining_polar_sampler_audit_20260710.md`.

Run the current Windows AE Software reference from
`refs/win_references/20260604_olm/OLMRadialBlur`. Do not satisfy this request
with a new PNG batch, package-local recomputation, inferred cell offsets, or
values copied from an earlier return. NAS staging is out of scope.

## Required Single Run

Use one render/debugger run and capture exactly these top-row output points:

| role | output pixel | expected reference alpha |
| --- | --- | ---: |
| primary | `(7,0)` | `254` |
| control | `(8,0)` | `255` |
| control | `(24,0)` | `255` |

The two controls are required in the same run so the primary witness can be
separated from a broad coordinate, cell, or byte-quantization change.

## Required Typed Fields Per Point

For each of the three points, return a structured row containing all of:

- output `x,y`, reference RGBA8, and observed Windows RGBA8;
- final inverse-sampler sample coordinates `(sample_x,sample_y)`;
- the four final-polar cell IDs, preserving their sampler order (`00`, `10`,
  `01`, `11`) and any `(angle,radius)` indices or address used to identify each;
- each of those four cells' `+0xe` RGBA float values, including alpha;
- the corresponding `+0xf252` value for each sampled cell, with raw byte/word
  representation when available;
- the four bilinear weights in the same order as the cell IDs;
- the final alpha sum before byte conversion and the pre-byte alpha value;
- the exact hook/watchpoint address and run identifier that binds the row.

Do not collapse the four cell records into only an alpha list: the cell ID,
`+0xe` RGBA float, `+0xf252`, and weight must remain positionally paired.

## Acceptance

`answered` requires all fields above for `(7,0)`, `(8,0)`, and `(24,0)` from the
same run. The result must make the layer decision possible:

1. different four-cell IDs at `(7,0)` indicate polar population or coordinate
   generation;
2. matching IDs with sub-one `+0xe.alpha` indicate collapse/state ownership;
3. matching IDs and all-one alpha move the residual to the final byte path.

`answered_partial` is acceptable only when at least `(7,0)` has complete typed
fields and the return contains the exact reason the controls or remaining
fields could not be isolated. `failed_partial` covers PNG-only output, wrapper
hit counts, null typed fields, or values inferred outside the Windows run.

## Return

Fill `RETURN_RUNTIME_TRACE_TEMPLATE.json` in the package. Preserve the schema
and field names. Include the debugger console/log artifact that proves the
three rows came from one run.
