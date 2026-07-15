# OLMDirectionalBlur 16/32bpc Evidence Audit - 2026-07-15

## Verdict

`windows-software-float-reference-only; no AE exact claim`

The imported Windows return contains 10 effect/control pairs. Every pair is an uncompressed FLOAT RGBA EXR at 1920x1080 from the SOFTWARE render set.

## Family Separation

- The established front-only exact family is the separate 8bpc slice `db_angle0_strength_sweep_small` and `db_angle0_no_tail_no_size`.
- All 10 imported 32bpc cases have nonzero Size Variation, front/back Alpha Fade, front/back Sharp Tail, back Blur Strength, and Noise Variation. They are mixed variation/fade/tail/back/noise stress cases.
- No DirectionalBlur row exists in the covered 16bpc exact manifest. Its 12 rows are OLMColorKey and OLMToonDilate only.

## Windows 32bpc Return

| Cases | Effect/control pairs | Format | Renderer | Exactness |
| ---: | ---: | --- | --- | --- |
| 10 | 10 | FLOAT RGBA, uncompressed EXR | SOFTWARE | Windows reference only |

The audit records per-artifact SHA-256 and EXR header facts. It does not infer algorithm equality from the files and does not retune production source.

## Mac Gate

The narrowest pinned request is one case, `final_random10_olm_directionalblur_01`, with its input identity, complete effect parameter values, 1920x1080/24fps comp, 32bpc SOFTWARE project, no-effect control, effect-on output, and OpenEXR FLOAT/no-compression contract. See `refs/mac_validation_requests/olmdirectionalblur_32bpc_mac_validation_20260715.json`.

Pass requires raw FLOAT32 word equality after the Windows/Mac no-effect control gate. Any missing hash, changed input/parameter, output drift, non-FLOAT/compressed EXR, or PNG-only return fails closed. No `AE exact` claim is permitted by this request.
