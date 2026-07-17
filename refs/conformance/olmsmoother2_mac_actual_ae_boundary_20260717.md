# OLMSmoother2 Mac actual-AE boundary probe - 2026-07-17

- Verdict: `BLOCKED_MAC_AE_BOUNDARY_RENDER_EMPTY`
- Case: `legacy_case_0012_gamma5_red_blue_current_aex`; target `(x=92, y=841)`.
- Installed Mac plug-in binary SHA-256: `a7b9747dec20e97c019de8ffd402c6476eb39dcab14a6b8648772e0af1539c69`.

## Result

- The Mac AE host was reached, but the render output remained empty and the harness timed out waiting for a stable PNG: `FAIL_CLOSED: 0
[OK] AE single case status: error
[INFO] output_dir: /private/var/folders/75/9dt3mly976q79gzrd3sg8qxm0000gn/T/olmsmoother2_mac_boundary_20260717_bin3mhiv/render
[INFO] result_json: /private/var/folders/75/9dt3mly976q79gzrd3sg8qxm0000gn/T/olmsmoother2_mac_boundary_20260717_bin3mhiv/render/AE_SINGLE_CASE_RESULT.json
[INFO] output_png: /private/var/folders/75/9dt3mly976q79gzrd3sg8qxm0000gn/T/olmsmoother2_mac_boundary_20260717_bin3mhiv/render/legacy_case_0012_gamma5_red_blue_current_aex.png
[INFO] png_observation: empty waited_ms=120114 size_bytes=0
[FAIL] AE single case error: Error: PNG was not stably written (empty): /private/var/folders/75/9dt3mly976q79gzrd3sg8qxm0000gn/T/olmsmoother2_mac_boundary_20260717_bin3mhiv/render/legacy_case_0012_gamma5_red_blue_current_aex.png
`.
- No Mac pixel or AE-exactness claim is made.

## Reproduction

```sh
python3 tools/emulation/probe_olmsmoother2_mac_actual_ae_boundary_20260717.py
```
