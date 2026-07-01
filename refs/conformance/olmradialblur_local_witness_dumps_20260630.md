# OLMRadialBlur Local Witness Dumps

Date: 2026-06-30

Purpose:

- Freeze one more layer of local evidence for the two highest-value 8bpc
  witnesses without waiting for another Windows trip.
- Specifically, capture the four inverse-sampled polar cells and local
  preserved-validity proxy used by the current CLI at the representative
  output pixel.

## Zoom `case_0009` witness `(6,0)`

Local dump:

- `radius_index=1096.23`
- `angle_index=1047.56`
- `sample_x0/x1=1096/1097`
- `sample_y0/y1=1047/1048`
- bilinear weights:
  - `w00=0.341602`
  - `w10=0.100903`
  - `w01=0.430371`
  - `w11=0.127124`
- final local sample:
  - `sample_rgba=[0.0822407,0.0141302,0.0141302,1.0]`
  - `sample_u8=[20,3,3,255]`

Per-cell values:

- `cell00_rgba=[0.0824175,0.0118616,0.0118616,1.0]`, `cell00_valid=1`
- `cell10_rgba=[0.0821793,0.0118454,0.0118454,1.0]`, `cell10_valid=1`
- `cell01_rgba=[0.0821980,0.0159394,0.0159394,1.0]`, `cell01_valid=0`
- `cell11_rgba=[0.0819587,0.0159147,0.0159147,1.0]`, `cell11_valid=0`

Interpretation:

- Two of the four contributing cells are already `valid=0` under the current
  loose repeat-border proxy, yet they still carry nonzero RGBA and contribute
  to the local near-match.
- This is strong local evidence that a naive "invalid contributing cell must be
  zeroed before final inverse sampling" rule is wrong for the surviving Zoom
  witness.
- Re-running the same witness with `--rgba-sampler-alpha-mode repeat-raw`
  produced the same final sample and the same per-cell data for this witness.

## tiny Rotation `case_0010` witness `(1614,6)`

Local dump:

- `radius_index=844.318`
- `angle_index=1603.84`
- `sample_x0/x1=1603/1604`
- `sample_y0/y1=844/845`
- bilinear weights:
  - `w00=0.109556`
  - `w10=0.572939`
  - `w01=0.0509667`
  - `w11=0.266538`
- final local sample:
  - `sample_rgba=[-0.00408606,-0.00408606,-0.00408606,1.0]`
  - `sample_u8=[0,0,0,255]`

Per-cell values:

- `cell00_rgba=[-0.014711,-0.014711,-0.014711,1.0]`, `cell00_valid=1`
- `cell10_rgba=[0,0,0,1.0]`, `cell10_valid=1`
- `cell01_rgba=[-0.048549,-0.048549,-0.048549,1.0]`, `cell01_valid=1`
- `cell11_rgba=[0,0,0,1.0]`, `cell11_valid=1`

Interpretation:

- The tiny Rotation high-max witness is not explained by a final validity gate:
  all four contributing cells are already `valid=1`.
- The remaining local failure at this witness is upstream of final bilinear
  alpha and comes from the polar RGB values themselves: two contributing cells
  are negative, two are zero, and the weighted sum stays slightly negative.
- That narrows the live question further toward the caller-side polar RGB
  population / normalization path, or toward a source-coordinate mismatch that
  chooses the wrong polar cells before final inverse sampling.
