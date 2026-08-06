# OLMSmoother2 UI setup parity — 2026-08-06

Status: **exact**.

The current Windows AEX exported entry was executed directly for `PF_Cmd_GLOBAL_SETUP` and `PF_Cmd_PARAMS_SETUP`. All 15 owned parameter rows were captured from the host callback and compared with the Mac production entry after ABI-normalizing float-slider storage.

The comparison fixed four concrete differences:

- `Smooth Range` valid and slider maxima: 255 → 100.
- `Gamma Correction`: add `PF_ParamFlag_SUPERVISE`.
- `Number of Gamma Colors`: add `PF_ParamFlag_SUPERVISE`.
- `Gamma Value`: preserve the AEX zero `curve_tolerance` instead of the SDK helper's audio-oriented 0.05 default.

The final comparison covers version, output flags, disk IDs, parameter order/types/names, flags, ranges/defaults, popup choices, colors, and float-slider metadata. It does not claim native AE layout/render parity.
