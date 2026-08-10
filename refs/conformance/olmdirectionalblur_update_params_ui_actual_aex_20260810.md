# OLMDirectionalBlur dynamic Noise UI contract — 2026-08-10

## Result

The Windows 2025 AEX exported `PF_Cmd_UPDATE_PARAMS_UI` path and the Mac
production implementation now share the same bounded visibility contract:

| Noise Type value | Noise Layer (17) | Seed (18) | Noise Offset (19) | Thickness (20) |
| --- | --- | --- | --- | --- |
| `3` (Layer) | visible | hidden | hidden | hidden |
| every other observed integer (`0, 1, 2, 4`) | hidden | visible | visible | visible |

This is a `Dynamic Stream` `HIDDEN` transition, not a disabled/greyed-out
`PF_ParamDef` update. The AEX updates indices `17..20` in that order with
`AEGP_DynStreamFlag_HIDDEN`, `undoable=false`, disposes every stream reference,
and disposes its effect reference once. The Mac implementation does the same.

## Evidence

- Oracle binary: `aex/OLMDirectionalBlur/Plugins/64/2025/OLMDirectionalBlur.aex`
- SHA-256: `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`
- Exported entry: `0x1800083f0`, command `14`
- Actual implementation: `0x180007eb0`; per-stream helper `0x1800081d0`
- Machine-readable report:
  `refs/conformance/olmdirectionalblur_update_params_ui_actual_aex_20260810.json`
- Harness:
  `tools/emulation/test_olmdirectionalblur_update_params_ui_actual_aex_20260810.py`
- Focused regression:
  `tests/test_olmdirectionalblur_update_params_ui_20260810.py`
- Production source: `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`

The harness executes the unmodified exported AEX command path in Unicorn. Only
the host suite callbacks are modeled. The branch decision, stream lookup order,
flag arguments, and cleanup are executed from the AEX itself.

The production bundle also builds successfully as a signed Universal Mach-O
(`arm64` and `x86_64`).

On 2026-08-10, After Effects 26.3.0.87 on Apple Silicon loaded the installed
bundle and applied it to a solid without an error dialog. With `Noise Type =
Smooth`, `Seed`, `Offset`, and `Thickness` were visible and `Noise Layer` was
hidden. Selecting the third popup item, `Layer`, immediately hid those three
controls and exposed `Noise Layer`, confirming the native host redraw.

## Boundary

This closes the executable callback contract, production build, and native Mac
AE visible-redraw boundary. Host error behavior when an individual suite call
fails and invocation without a valid effect context remain outside this claim.
