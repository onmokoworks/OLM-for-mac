# OLMRadialBlur Mac AE Single-Case Probe

Date: 2026-07-01

This note records the first live Mac-AE rerun of the new single-case
`OLMRadialBlur` probe requests plus the local debug hook.

## Important host finding

The first probe attempt ran without explicit bit depth in the copied
single-case `reference_manifest.json`. In that state, AE host output matched
the input frame exactly for both `case_0009` and `case_0010`, which is
consistent with the current plug-in's unsupported 16/32bpc fallback copy path.

The single-case probe generator now injects:

- `reference_manifest.project.bits_per_channel = 8`

After regenerating the request dirs and rerunning, AE host entered the 8bpc
effect path as intended.

## Request dirs

- `handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701`
- `handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701`

## Live Mac AE runs

### Zoom `case_0009`

- output dir:
  `/tmp/case_0009_radialblur_probe_20260701_bpc8`
- AE log confirms:
  - `bitsPerChannel=8`
- comparison vs Windows software reference:
  - `max=1`
  - `mean=0.004613474151234568`
  - `nonzero_pct=1.5007233796296295`

This matches the known guarded Zoom near-exact lane rather than the earlier
copy-input fallback.

### tiny Rotation `case_0010`

- output dir:
  `/tmp/case_0010_radialblur_probe_20260701_bpc8`
- AE log confirms:
  - `bitsPerChannel=8`
- comparison vs Windows software reference:
  - `max=255`
  - `mean=0.01032033661265432`
  - `nonzero_pct=1.6271219135802468`

This matches the known guarded tiny Rotation residual lane rather than the
earlier copy-input fallback.

## Debug hook result

The new host debug hook did produce useful witness data in live AE:

- `handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701/radialblur_debug_points.json`
- `handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701/radialblur_debug_points.md`

Observed parsed content:

- `zoom` points: `10`
- `rotation` points: `11`

Representative live host facts from that parsed witness:

- Zoom top-row `(6,0)` still reports:
  - `sample_u8=(20,3,3,255)`
  - `alpha=1`
  - `validity_alpha=1`
  - `cell_valid=(1,1,1,1)`
- tiny Rotation `(1614,6)` reports:
  - `sample_rgba≈(-0.00408606,-0.00408606,-0.00408606,1)`
  - `sample_u8=(0,0,0,255)`
  - `validity_alpha=1`
  - `cell_valid=(1,1,1,1)`

After rebuilding the host plug-in with `cell_rgb` dump support and rerunning
`case_0010` in isolation (`/tmp/case_0010_radialblur_probe_20260701_cellrgb`),
the same tiny-Rotation witness sharpened further:

- `(1612,6)`:
  - `sample_u8=(5,5,5,255)`
  - `cell_rgb=((0,0,0),(0,0,0),(0.04418,0.04418,0.04418),(0.00694,0.00694,0.00694))`
- `(1613,6)`:
  - `sample_u8=(1,1,1,255)`
  - `cell_rgb=((0.04418,0.04418,0.04418),(0.00694,0.00694,0.00694),(-0.01471,-0.01471,-0.01471),(0,0,0))`
- `(1614,6)`:
  - `sample_u8=(0,0,0,255)`
  - `cell_rgb=((-0.01471,-0.01471,-0.01471),(0,0,0),(-0.04855,-0.04855,-0.04855),(0,0,0))`

This is stronger than the earlier "validity is live" statement alone. The
bright family is not merely being masked off at the final sample. At the max
witness itself, all four contributing cells are already dark or negative.
That pushes the remaining blocker upstream into polar RGB population before the
final inverse sample.

A second isolated host rerun then added `src_cell_rgba` for those same four
contributing polar cells:

- `(1612,6)`, `(1613,6)`, `(1614,6)`, `(1614,5)`, `(1614,7)` all report
  `src_cell_rgba=((0,0,0,1),...)` for every contributing source polar cell
  even though the blurred `cell_rgb` neighborhood already contains small
  positive and negative values.

That narrows the branch again:

- the witness is not explained by "bright source cells exist here but final
  validity kills them";
- the local bright family at the witness is not coming from the direct source
  polar cells themselves;
- the remaining split is now between upstream Rotation contribution geometry
  (which neighboring polar cells feed the lobe, with what span/row structure)
  and a source-grid placement difference that shifts where the bright source
  family enters the polar buffer.

These host-side witnesses are consistent with the current CLI-side reading:

- Zoom remains a caller-collapse / alpha-side one-step issue, not a broad host
  mismatch.
- tiny Rotation remains an upstream RGB / substitute-path issue with fully live
  validity alpha.
- The host cell dump now makes the likely branch narrower still: the current
  no-inner Rotation path is probably missing AEX-style outer prepass/scatter
  population, not just mis-handling final inverse-sample validity.
- The added `src_cell_rgba` dump shows the four direct source polar cells at
  the witness are all black. So the active question is no longer "why did
  those exact source cells get suppressed?" but "which nearby Rotation
  contributions or source-grid positions should have populated this lobe on the
  AEX side?"

## Host automation finding

The original paired rerun of `case_0009` and `case_0010` used two parallel
`run_ae_single_case.py` invocations against one live After Effects process.
That produced mixed or missing `radialblur_debug.log` files because the wrapper
uses shared `$.setenv(...)` state inside the AE process.

This is now fixed in tooling:

- `scripts/run_ae_single_case.py` takes an exclusive lock on
  `/tmp/olm_ae_single_case.lock`
- parallel callers now serialize their AE `DoScriptFile` execution instead of
  racing on shared ExtendScript environment variables

After the lock change:

- `case_0009` produced a clean dedicated log:
  `/tmp/case_0009_radialblur_probe_20260701_bpc8_locktest/radialblur_debug.log`
- `case_0010` produced a clean dedicated log:
  `/tmp/case_0010_radialblur_probe_20260701_bpc8_locktest_retry/radialblur_debug.log`

The parsed request artifacts were updated from those isolated reruns:

- `handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/radialblur_debug_points.json`
- `handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701/radialblur_debug_points.json`

So the earlier missing/mixed dump should now be treated as an automation race,
not as a RadialBlur algorithmic symptom.
