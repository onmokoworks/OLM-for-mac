# ColorKey / ToonDilate Global OutFlags2 repair (2026-07-12)

## FACT

- Mac AE reported ColorKey code flags `0x00801400` and PiPL flags
  `0x08001400` during effect add.
- `Headers/AE_Effect.h` defines the three flags used by current code as
  `1 << 10`, `1 << 12`, and `1 << 23`, totaling `0x00801400`.
- Both ColorKey and ToonDilate used that code expression while their PiPL files
  still declared `0x08001400`.
- Both PiPL declarations now use `0x00801400`.
- Both Debug builds succeeded as x86_64 + arm64 universal bundles.
- Installed binary SHA-256 values:
  - ColorKey: `c3026c5facbdf227bec55c24e7257f0f94db5ddf94ce26cfb5b593681b5ed0ae`
  - ToonDilate: `d47a81bd8259bd5ca0db31b71a4e0ffd4fef1c037ef31ffd1a922de1775954de`
- A ColorKey case rerun passed effect-add and reached the 32bpc project settings
  dialog without reproducing the OutFlags2 mismatch.

## INFERENCE BOUNDARY

This proves the host declaration mismatch was repaired. It does not prove any
32bpc pixel result or AE exact status. The interrupted paired run produced no
accepted EXR or result JSON and remains fail-closed.
