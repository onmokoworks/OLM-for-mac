# OLMRadialBlur border sampler semantic proof

- Status: `pass`
- Classification: `actual-aex-border-validity-alpha-split-proven`
- Evidence class: `bounded_actual_aex_helper_probe`
- AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`

## FACT

- The actual AEX non-repeat helper accepts the loose -2 < int(coord) border window and samples the in-bounds neighbor at -1.x.
- The actual AEX repeat-border helper accepts the same loose-window coordinates but clamps border taps, producing different RGBA float32 words.
- Both helpers agree on the interior control, so the split is boundary behavior rather than a general ABI mismatch.

| point | non-repeat return / RGBA words | repeat-border return / RGBA words |
| --- | --- | --- |
| `left_loose_window` `[-1.25, 0.5]` | `1` / `['0x3e6147ae', '0x3ea3d70b', '0x3ed70a3e', '0x3f000000']` | `1` / `['0x3e6147b0', '0x3ea3d70c', '0x3ed70a40', '0x3effffff']` |
| `top_loose_window` `[0.25, -1.25]` | `1` / `['0x3e124925', '0x3e78af8a', '0x3eaf8af8', '0x3f333334']` | `1` / `['0x3e124924', '0x3e78af8a', '0x3eaf8af8', '0x3f333334']` |
| `interior_control` `[0.25, 0.5]` | `1` / `['0x3eb5c290', '0x3ed9999a', '0x3efd70a4', '0x3f000000']` | `1` / `['0x3eb5c290', '0x3ed9999a', '0x3efd70a4', '0x3f000000']` |

## INFERENCE

- A single final alpha plane cannot represent both the repeat-border raw accumulated alpha and the non-repeat validity return. The caller must preserve validity separately until its documented collapse point.

## LIMITS

- Synthetic 2x2 helper input only.
- No prepass/scatter invocation and no AE host execution.
- Does not claim Mac/Windows or AE exactness and does not authorize production changes.

- Issues: `[]`
