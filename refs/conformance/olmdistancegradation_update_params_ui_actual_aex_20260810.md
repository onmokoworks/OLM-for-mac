# OLMDistanceGradation UPDATE_PARAMS_UI actual-AEX parity

- Status: exact
- Cases: 144 (complete public-range Cartesian product)
- Actual AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`
- Observable payload SHA-256: `46957c67f648fd399793338a995f67f14ffc8d0c93182dce1c85d9afe2955b1f`

The exported Windows command-14 entry and Mac production `EffectMain` emit the same six `PF_UpdateParamUI` calls, in order `[10, 4, 3, 7, 8, 12]`, with each copied parameter's `ui_flags` replaced by exactly `0` or `PF_PUI_DISABLED (0x20)`. The JSON report records all cases.

Boundaries: native AE redraw timing, callback-error injection, and values outside popup ranges are not claimed.
