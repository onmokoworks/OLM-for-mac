# OLMRadialBlur small-plane scatter boundary witness

Date: 2026-07-14

## Result

The bounded actual-AEX probe was run twice on the same 32x32 case geometry:

```text
python3 tools/emulation/probe_radialblur_final_plane_small.py \
  --output-json /tmp/radial_default_20260714.json
python3 tools/emulation/probe_radialblur_final_plane_small.py \
  --detour-scatter \
  --output-json /tmp/radial_scatter_detour_20260714.json
```

Both runs completed with `status=ok`, 196 informative cells, and no fault.
The actual-AEX prepass was used in both runs. The second run replaced the
scatter entry with a diagnostic no-op.

| Plane | normal run SHA-256 | scatter-detour SHA-256 |
| --- | --- | --- |
| `accum_rgba_f32` | `6fc114c6e7b87419dea99d64c705ab08ff77be310e7c97785e09c405a8e6ff4c` | `6fc114c6e7b87419dea99d64c705ab08ff77be310e7c97785e09c405a8e6ff4c` |
| `denom_f32` | `fff91e873df93b4fe0f83d2e7a763bf00af8fe4a51f4e5662a433611336db00a` | `fff91e873df93b4fe0f83d2e7a763bf00af8fe4a51f4e5662a433611336db00a` |
| `final_rgba_f32` | `6fc114c6e7b87419dea99d64c705ab08ff77be310e7c97785e09c405a8e6ff4c` | `6fc114c6e7b87419dea99d64c705ab08ff77be310e7c97785e09c405a8e6ff4c` |
| `valid_f32` | `fff91e873df93b4fe0f83d2e7a763bf00af8fe4a51f4e5662a433611336db00a` | `fff91e873df93b4fe0f83d2e7a763bf00af8fe4a51f4e5662a433611336db00a` |

## Interpretation

This is a local AEX/emulator boundary fact, not AE exact evidence and not a
mapping to the full-frame case_0009 output coordinates. It rules out the
scatter call as the owner of the pre-normalization plane difference for this
bounded geometry. The next local boundary, if pursued, is the producer
`FUN_18000b150` input/output and the `+0x843` scalar/denom generation. Do not
change the Mac writer or tune PNG values from this probe.
