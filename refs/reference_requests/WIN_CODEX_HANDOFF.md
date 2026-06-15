# Windows reference re-capture — 2026-06-14

Render these 4 requests in After Effects on Windows and return a zip.

## What to render (JSON specs are in this package)

| request | cases | why it's needed |
|---|---|---|
| radialblur_inner_20260605 | 10 | previous return wrote the manifest but only exported 5/40 PNGs |
| radialblur_inner_size_variation_20260606 | 8 | previous return exported 0 PNGs |
| smoother2_no_key_grid_20260606 | 12 | previous return exported 0 PNGs |
| kirakira_strength0_brightness_20260614 | 4 | NEW: 1 Strength=0 sample is underdetermined; need a brightness sweep to pin the gain constant |

## CRITICAL — what went wrong last time

The 2026-06-14 render produced a combined `reference_manifest.json` listing 112
cases but only exported PNG files for ~2.5 of the 5 requests (manifest claimed
cases whose PNGs were never written). Before returning:

- **Verify the number of exported PNGs equals the number of manifest cases.**
  Each case needs BOTH its effect-output PNG and its `before_effects_frame` PNG.
- If any case fails to render, fix it or drop it from the manifest — do not ship
  a manifest entry without its PNG.

## Recording requirements (every case)

- Record `project_gpu_accel_type.current_name` and raw value per render set
  (CUDA and SOFTWARE). The `software` render set is REQUIRED; `cuda` optional.
- Keep `ADBE Force CPU GPU` / `GPU Rendering` as reference-only metadata — it is
  NOT the execution-path label; `project_gpu_accel_type` is.
- Record all OLM property names, match_names, property_index, values, and
  enabled/active state.
- Prefer the same comp size and source artwork used by the prior returns so
  residuals are directly comparable.

## Return

Zip the PNGs + manifest and hand back. Mac side imports with
`scripts/intake_olm_return.py <zip>` (it splits a multi-request manifest per
request).

## NOTE: not requested

OLMDirectionalBlur does NOT need a re-capture. Its software references already
exist; its remaining max~254 residual is a real CPU-side algorithm gap (max-alpha
/ rotate-back edge), not a GPU-vs-CPU or missing-reference problem.
