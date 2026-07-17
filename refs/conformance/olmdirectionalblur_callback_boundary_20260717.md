# OLMDirectionalBlur callback boundary witness

- Status: `pass`; Mac-local actual-AEX/Unicorn only.
- The real `0x180006980` callback maps PF `A/R/G/B` bytes to work-plane `R/G/B/A` float32 values for five boundary vectors, including partial byte values.
- The real `0x180006b30` callback packs three float vectors as `A/R/G/B`, proving RGB clamp and the separate un-clamped alpha byte cast at the callback boundary.
- The plane address contract is explicit (`+0x8078`, `+0x8090`, `row0=2`, `col0=3`, `stride=4`); no PNG, render entry, production source, Windows value, or AE-exact claim is involved.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_callback_boundary_20260717.py
```
