# OLMDirectionalBlur UI setup parity — 2026-08-06

The actual 2025 Windows AEX public entry point and the Mac production
`EffectMain` now register the same bounded host contract.

- `GLOBAL_SETUP`: version `0x00088800`, flags `0x06000040`, flags2 `0x08001408`.
- `PARAMS_SETUP`: 21 added rows, 22 parameters including input.
- Every row matches in order, disk ID, parameter type, name, flags, UI flags,
  width/height, ranges, defaults, precision and display flags.
- The parameter-type sequence is
  `3,10,2,13,1,1,2,14,13,1,1,2,14,13,2,7,0,1,3,10,14`.
- Group-end rows intentionally inherit the preceding names: `Sharp Tail`,
  `Sharp Tail`, and `Thickness`, matching the AEX raw structures.

The correction replaces approximate Mac UI declarations with the AEX forms:
angle/fixed sliders, true group start/end rows, brightness slider maximum 2,
percentage display flags, two declared popup choices with the original
three-item string, a no-layer default, angle-form Offset, and hundredths
precision for Thickness. Render parameter decoding was updated for the fixed
and angle representations.

The actual-AEX fixture does not emulate imported `strncpy`; names are therefore
bound to the exact string-table indices visible in the decompiled setup owner,
while every other field is captured directly at the AEX `add_param` callback.
Native AE visual layout and localization remain outside this hostless proof.

Reproduce:

```sh
python3 tools/emulation/test_olmdirectionalblur_ui_setup_actual_aex_20260806.py
```
