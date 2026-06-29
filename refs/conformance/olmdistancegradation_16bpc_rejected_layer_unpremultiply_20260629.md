# OLMDistanceGradation 16bpc rejected Layer/no-bg unpremultiply hypothesis

- Case: `olmdistancegradation_extended__case_0012`
- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Installed SHA after revert: `ab5f48244d33ab0d7a9078442ea25ff20ad218aca649bd36d1456e1e5f77b6a4`
- Conclusion: Rejected: direct Layer/no-bg unpremultiply/premultiply increased changed-pixel coverage. Reverting and restarting AE restores the prior Constant-binary state. Layer/no-bg residual remains and needs binary/runtime proof instead of broad PNG tuning.

| Variant | max | mean | nonzero_px | Max witness |
| --- | ---: | ---: | ---: | --- |
| `rejected_layer_unpremultiply_cached_before_restart` | 16476 | 332.8368 | 285406 | `(427,572) ch0 ref=[32859, 0, 0, 32859] cand=[16383, 0, 0, 32767] delta=[-16476, 0, 0, -92]` |
| `reverted_after_ae_restart` | 16250 | 53.4510 | 25421 | `(462,7) ch0 ref=[32371, 32371, 32371, 64997] cand=[16121, 16121, 16121, 64997] delta=[-16250, -16250, -16250, 0]` |

## Reading

- The attempted Layer/no-bg source unpremultiply is explicitly rejected.
- AE had to be restarted after reinstall; otherwise it kept using the previously loaded plugin image.
- Next evidence should be binary/runtime proof for Layer/no-bg compose ownership, not PNG-only tuning.
