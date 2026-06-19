# Binary-Grounded IR: OLMToonDilate

## Feature

- Plug-in: OLM Toon Dilate
- Feature/path: 8bpc Search Radius dilation path
- Bit depth: 8bpc documented here; 16/32bpc still need references
- Reference set:
  - `refs/win_references/20260604_olm/OLMToonDilate`
  - normalized Software refs under
    `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMToonDilate`
- Current status: `CLI exact` against normalized Software refs for
  `case_0001..0003`; Mac AE exact still untested.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| The effect dilates non-transparent image regions toward transparent borders. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMToonDilate__OLMToonDilate__doc__OLM Toon Dilate Manual EN.txt`. | manual-backed |
| Only `Search Radius` is exposed. | Official manual and local PiPL/UI. | proved |
| Render core is a two-pass 8-neighbor chamfer propagation. | `refs/scripts/olmtoondilate_cli.py`, `cli/OLMToonDilate/main.cpp`, and decomp note naming `FUN_1801a6150`. | binary-grounded |
| Seed pixels are fully opaque pixels (`alpha == 255`). | Python/C++ CLI implementation and normalized exact result. | binary-grounded / CLI-confirmed |
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

## Numeric Rules

- Radius uses `ceil`.
- Distance is integer and unit-cost.
- Output premultiply uses integer rounding `(v * a + 127) / 255`.

## Conformance Cases

| Case | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| `case_0001` | 8bpc | `CLI exact` against normalized Software ref | exact in Python/C++ normalized checks | Mac AE exact validation |
| `case_0002` | 8bpc | `CLI exact` against normalized Software ref | exact in Python/C++ normalized checks | Mac AE exact validation |
| `case_0003` | 8bpc | `CLI exact` against normalized Software ref | exact in Python/C++ normalized checks | Mac AE exact validation |

## Open Questions

- Mac AE host exactness against normalized/current Windows Software references.
- 16bpc and 32bpc propagation/writeback behavior.
- Whether non-normalized older residuals were stale reference drift or hidden AE
  host/export differences; do not use them as algorithm guidance now.
