# OLMDistanceGradation 16bpc case0012/case0014 proof-render preflight

- Status: `blocked_refused_missing_disposable_project_flag`
- Claim boundary: `non-destructive local preflight only; no AE launch, no AE quit, no render execution, and no AE exact claim`
- Canonical request: `ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Canonical cases: `olmdistancegradation_extended__case_0012, olmdistancegradation_extended__case_0014`
- Canonical request manifest SHA-256: `7c4761b3b4de904c2a8baa8883c964f234943604414d2cd34bab107ccc43cf29`
- Canonical reference manifest SHA-256: `c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e`
- Request dir: `$REPO/handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- MediaCore bundle count: `1`
- Installed bundle: `$HOME/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin`
- Installed binary SHA-256: `af328faed0fcfbdefac7618d1218c2e5e5c9c0420c3bc58cdde7a7b6f64232fd`
- Running AE PIDs: `[7653]`
- DG mapped in any running AE: `False`
- Disposable-project flag supplied: `False`

## Structural checks

- Request check status: `ok`
- Request manifest hash matches canonical: `True`
- Reference manifest hash matches canonical: `True`
- Installed plug-in check status: `ok`
- Running AE check status: `running`

## Guard

- Existing runner API is reused through `scripts/run_ae_single_case.py`.
- The preflight does not launch AE, quit AE, or execute a render.
- Guard failures: `["proof_render:explicit_disposable_project_flag_required"]`

## Preview commands

- `olmdistancegradation_extended__case_0012`: `/opt/homebrew/opt/python@3.14/bin/python3.14 '$REPO/scripts/run_ae_single_case.py' --request-dir '$REPO/handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625' --case-id olmdistancegradation_extended__case_0012 --output-dir $TMP/olmdg_16bpc_case0012_case0014_proof_render_20260716/olmdistancegradation_extended__case_0012 --app-name 'Adobe After Effects 2026' --timeout 1200 --ae-env OLM_AE_FORCE_NEW_PROJECT=1 --ae-env OLM_AE_FORCE_SOFTWARE=1 --ae-env OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1`
- `olmdistancegradation_extended__case_0014`: `/opt/homebrew/opt/python@3.14/bin/python3.14 '$REPO/scripts/run_ae_single_case.py' --request-dir '$REPO/handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625' --case-id olmdistancegradation_extended__case_0014 --output-dir $TMP/olmdg_16bpc_case0012_case0014_proof_render_20260716/olmdistancegradation_extended__case_0014 --app-name 'Adobe After Effects 2026' --timeout 1200 --ae-env OLM_AE_FORCE_NEW_PROJECT=1 --ae-env OLM_AE_FORCE_SOFTWARE=1 --ae-env OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1`
