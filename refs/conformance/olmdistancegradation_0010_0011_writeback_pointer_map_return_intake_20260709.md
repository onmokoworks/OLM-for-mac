# OLMDistanceGradation 0010/0011 Writeback Pointer Map Return Intake

Date: 2026-07-09

Return archive:
`refs/returns/windows/20260709_distancegradation_0010_0011_writeback_pointer_map_partial_success/20260709_210810__olmdistancegradation_0010_0011_writeback_pointer_map_witness_partial_success_windows.zip`

Request id:
`olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709`

## Classification

`partial_success_missing_true16_export`.

This is not full acceptance of the request because the same-run true16 TIFF/EXR
export samples were not included. It is still an accepted pointer-map/store
witness: both primary case_0010 target pixels are bound to explicit PF16 output
addresses, and Windows same-run PF16 store words were captured.

Do not resend the same package unchanged.

## Accepted Facts

- Primary case: `olmdistancegradation_extended__case_0010`.
- Output pixel size: `8` bytes (`4 * uint16`).
- Output dimensions: `1920x1080`.
- Rowbytes: `15360` / `0x3c00`.
- Final buffer formula:
  `out = base + y * 0x3c00 + x * 8`.
- Formula verification: `24356` retained hits, `0` bad hits.
- Target offset `(6,40)`: `0x96030`.
- Target offset `(901,394)`: `0x5c7428`.
- Store sites for both targets:
  `DistanceGradation+0x1170814`,
  `DistanceGradation+0x117081c`,
  `DistanceGradation+0x1170824`,
  `DistanceGradation+0x117082b`.

Same-run target watch:

| Pixel | Address | First words | Final words | First word decimal | `xmm2_alpha` |
| --- | --- | --- | --- | --- | --- |
| `(6,40)` | `0000023e8ddb6130` | `733c 8000 733c 733c` | `0cc4 8000 0000 0000` | `3268` | `0.0997314` |
| `(901,394)` | `0000023e8e2e7528` | `596c 8000 596c 596c` | `2694 8000 0000 0000` | `9876` | `0.301392` |

The observed first words match the Windows-implied target store values from the
request:

- `(6,40)`: `0x0cc4 = 3268`.
- `(901,394)`: `0x2694 = 9876`.

## Missing Evidence

- Same-run true16 TIFF/EXR export samples tied to the same watchpoint render.
- An explicit export-value witness proving the export path preserves these exact
  PF16 words.

## Decision

The sparse `case_0010/0011` one-word split is present by Windows PF16 store
time. This moves the lane away from "derive output address" and toward local
Mac-side classification of the pre-store/store rule around
`DistanceGradation+0x1170814..+0x117082b`.

Allowed next local action:

- Compare the Mac 16bpc store path and debug witnesses against the Windows PF16
  words `3268` and `9876` for `(6,40)` and `(901,394)`.
- Classify whether the Mac mismatch is in field value, compose alpha, float to
  PF16 conversion, channel layout, or host export.

Forbidden next action:

- Re-send the same pointer-map package unchanged.
- Make a global store rounding toggle. The sign flips between the two witnesses.
