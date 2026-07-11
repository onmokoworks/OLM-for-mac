# 32bpc Compare Policy (2026-07-03)

`32bpc` の Windows reference は、`PNG-only` では `AE exact` 判定に使いません。
`EXR` などの float-preserving return があるときだけ、`refs/scripts/verify_manifest.py`
で float のまま比較します。

## Current rule

- reference / candidate 両方に同 stem の `.exr` companion があれば、manifest 上の
  `frame` が `.png` でも `.exr` を優先する
- `EXR/TIFF/HDR` の比較では画素を `int` に落とさず、`float64` へ上げて差分を測る
- `32bpc` で `AE exact` を名乗るには、declared case set が `max_diff=0`,
  `mean_diff=0`, `nonzero_px=0` を満たすこと
- `PNG-only` 32bpc return は probe / smoke 扱いで、completion evidence にしない

## Why this note exists

以前の `verify_manifest.py` は EXR companion 自体は読めていましたが、比較時に
float を `int64` へ落としていたため、`0 < delta < 1` の 32bpc 差分を潰す可能性が
ありました。2026-07-03 時点でこの比較器は修正済みです。

## Regression guard

- smoke: [refs/scripts/smoke_verify_manifest_float_exr_delta.py](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/scripts/smoke_verify_manifest_float_exr_delta.py)
- companion selection smoke:
  [refs/scripts/smoke_verify_manifest_exr_companion.py](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/scripts/smoke_verify_manifest_exr_companion.py)

このポリシーは、現在 share に置いてある
`olm_reference_request_32bpc_full_probe_20260703.zip` の返却判定にも適用します。
