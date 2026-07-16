# Binary-Grounded IR: OLMToonDilate

## Feature

- Plug-in: OLM Toon Dilate
- Feature/path: 8bpc Search Radius dilation path
- Bit depth: 8bpc documented here; covered 16bpc slice is AE exact;
  32bpc has returned only as PNG/non-float-preserving probe evidence
- Reference set:
  - `refs/win_references/20260604_olm/OLMToonDilate`
  - normalized Software refs under
    `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMToonDilate`
- Current status: packaged 8bpc `AE exact` for `case_0001..0003`.
  Python/C++ CLI are also exact against normalized Software refs for the same
  cases. The covered 16bpc Mac AE slice is also `AE exact` for the same three
  cases (`refs/conformance/bitdepth_16bpc_exact_manifest_20260703.md`).
  32bpc is not exact evidence yet: the broad EXR-first rerun came back
  PNG-only/non-float-preserving and is frozen as `probe-only-png-return` in
  `refs/conformance/bitdepth_32bpc_probe_status_20260703.md`.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| The effect dilates non-transparent image regions toward transparent borders. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMToonDilate__OLMToonDilate__doc__OLM Toon Dilate Manual EN.txt`. | manual-backed |
| Only `Search Radius` is exposed. | Official manual and local PiPL/UI. | proved |
| Render core is a two-pass 8-neighbor chamfer propagation. A checked-in PF16 AEX worker executed under local Unicorn matches the current typed model on a true `2x2` fixture across seven alpha values. | `refs/scripts/olmtoondilate_cli.py`, `cli/OLMToonDilate/main.cpp`, decomp note naming `FUN_1801a6150`, and `refs/conformance/olmtoondilate_pf16_2d_propagation_followup_20260716.json`. | binary-grounded / bounded 2D differential |
| Seed pixels are fully opaque pixels (`alpha == 255` for PF8; `alpha == 32768` for PF16). The PF16 actual-AEX alpha sweep distinguishes `32767`, `32768`, and `32769`. | Python/C++ CLI implementation, normalized exact result, and the bounded PF16 2D differential. | binary-grounded / typed differential |
| Effective radius is `ceil(SearchRadius * image_width / comp_width)`. | Python/C++ CLI implementation and half/full-res reference behavior. | binary-grounded / CLI-confirmed |
| Relaxed pixels copy the current winner neighbor's RGBA immediately. | Python/C++ CLI implementation; `case_0003` distinguishes this from a global nearest-source lookup. | CLI-confirmed |
| Remaining semi-alpha pixels are premultiplied on output with `(rgb * alpha + 127) / 255`. | Python/C++/Mac implementation and normalized exact result. | CLI-confirmed |

## Parameters

| UI / manifest name | Internal meaning | Normalization | Evidence |
| --- | --- | --- | --- |
| `Search Radius` | Maximum propagation distance. | `ceil(radius * image_width / comp_width)`; default comp width fallback in CLI is `1920`. | CLI exact + comp-width scaling behavior |

## Kernel / Loop Shape

The current exact CLI kernel is:

1. Copy input RGBA to output.
2. Initialize `dist = UINT32_MAX`.
3. For every pixel, set `dist = 0` only when source alpha is `255`.
4. Forward raster pass:
   - order: `y = 0..h-1`, `x = 0..w-1`
   - candidate neighbors:
     - left
     - upper-left
     - up
     - upper-right
5. Backward raster pass:
   - order: `y = h-1..0`, `x = w-1..0`
   - candidate neighbors:
     - right
     - lower-right
     - down
     - lower-left
6. For each pass, if `best_neighbor_dist + 1 < current_dist`, update distance.
7. If updated distance is within `r_eff`, immediately copy the winner neighbor's
   current output RGBA into the current pixel.
8. After propagation, premultiply RGB for semi-alpha pixels only.

## Sampling / Boundary

- Boundary mode: skip out-of-bounds neighbors.
- Metric: two-pass chamfer with unit cost for all eight listed neighbors.
- Tie rule: first neighbor in the listed scan order wins because only
  `d < best` updates the candidate.
- Fill source: current output buffer, not immutable original source.

## Channel Rules

- Fully opaque source pixels are seeds.
- Fully transparent pixels may be filled when reachable within `r_eff`.
- Semi-alpha source pixels are not seeds.
- Semi-alpha pixels that remain semi-alpha after propagation get premultiplied
  RGB on output.
- Copied pixels preserve all RGBA bytes from the winner neighbor at copy time.

The bounded PF16 `2x2` actual-AEX fixture crosses the prior
`context+0x180`/`0x1801adc8f` boundary. For alpha values
`0,1,16384,32767,32768,32769,65535`, it records each selected source and
destination coordinate plus all four PF16 words, and its final output equals
the current `RenderTyped<PF_Pixel16>` model. The suite/PF_COPY host ABI remains
synthetic, so this is binary-grounded kernel evidence rather than AE exact.

## Numeric Rules

- Radius uses `ceil`.
- Distance is integer and unit-cost.
- Output premultiply uses integer rounding `(v * a + 127) / 255`.

## Conformance Cases

| Case | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| `case_0001` | 8bpc | `AE exact` for packaged Software ref | `max_diff=0` in 2026-06-19 AE pixel return; exact in Python/C++ normalized checks | Preserve exact behavior; next open depth is float-preserving 32bpc |
| `case_0002` | 8bpc | `AE exact` for packaged Software ref | `max_diff=0` in 2026-06-19 AE pixel return; exact in Python/C++ normalized checks | Preserve exact behavior; next open depth is float-preserving 32bpc |
| `case_0003` | 8bpc | `AE exact` for packaged Software ref | `max_diff=0` in 2026-06-19 AE pixel return; exact in Python/C++ normalized checks | Preserve exact behavior; next open depth is float-preserving 32bpc |
| `case_0001..0003` | 16bpc | `AE exact` for covered Software slice | Live Mac AE verification against imported Windows Software 16bpc refs passes `3/3` with `max_diff=0` | Preserve exact behavior; broaden only with declared references |

## Open Questions

- 32bpc propagation/writeback behavior under a float-preserving EXR/TIFF/HDR
  return.
- Broader 16bpc behavior beyond the declared covered slice, if new ToonDilate
  parameters or inputs are introduced.
- Whether non-normalized older residuals were stale reference drift or hidden AE
  host/export differences; do not use them as algorithm guidance now.
