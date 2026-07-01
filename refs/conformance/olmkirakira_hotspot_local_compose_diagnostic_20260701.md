# OLMKiraKira Hotspot-Local Compose Diagnostic - 2026-07-01

Bounded Mac-side diagnostic using only existing witness/audit evidence to sharpen the remaining compose question at `(934,118)`.

## Primary hotspot

- case: `kk_vertical_len50_brightness1_strength100`
- point: `(934, 118)`
- Mac compose-boundary alpha: `0.507505655`
- Mac compose-boundary byte: `144`
- Windows reference byte: `131`
- Windows-match implied alpha interval: `[0.446666666667, 0.451111111111]`
- Windows-match implied alpha midpoint: `0.448888888889`
- Additional alpha drop from Mac boundary midpoint: `0.058616766111`
- Hotspot attenuation ratio midpoint: `0.884500270`

## Grayscale controls

- Center `(960,540)`: Mac alpha `0.440345466`, Windows-implied alpha midpoint `0.417777777778`, attenuation ratio `0.948750038`
- Right `(1010,540)`: Mac alpha `0.438375115`, Windows-implied alpha midpoint `0.413333333333`, attenuation ratio `0.942875905`

## Hotspot-local readout

- Average grayscale control attenuation ratio: `0.945812972`
- If that same ratio is applied at the hotspot, projected hotspot alpha is `0.480005431739` and projected byte is `138`
- Windows still needs hotspot alpha midpoint `0.448888888889`, which is `0.031116542850` below the control-ratio projection
- That leaves an extra hotspot-only byte drop of `7` beyond the already-grounded grayscale control behavior

## Decision fit

- Compose audit status: `preserve-current-compose-model`
- Compose audit reason: No audited candidate improves total mean and max while preserving strength0 anchors.

## Bottom line

- The hotspot already mismatches at the Mac compose boundary, and the exact Windows-match alpha interval at that point is 0.446666666667..0.451111111111.
- Applying the average grayscale control attenuation to the hotspot still predicts byte 138, not the Windows byte 131.
- So the remaining KiraKira gap at (934,118) is narrower than a broad grayscale/global compose retune; it needs an additional hotspot-local attenuation or branch before writeback.
