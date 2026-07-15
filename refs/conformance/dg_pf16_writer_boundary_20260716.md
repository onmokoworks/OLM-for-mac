# DistanceGradation PF16 Writer Boundary

- Run date: 2026-07-16.
- Scope: direct bounded calls into the checked-in 2025 `DistanceGradation.aex`; Mac-local Unicorn only, not AE-host execution.
- AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- ABI: `RCX=float32*`, `RDX=uint16*`, `R8D=count` under Windows x64.
- `FUN_18144b820` was not called: both writer leaves completed without a host callback/import.

## Model

The corrected Mac comparison is code-domain `clamp16(x / 32768.0)`: `saturate(floor(float32(float32(x / 32768.0) * 32768.0) + 0.5), 0, 32768)`. This is a domain mapping for comparison only. Any upstream scale feeding the AEX writer remains unproven.

## Results

| Case | Raw code-domain float32 inputs | `FUN_181458030` words | `FUN_1814581a0` words | Fourth preserved | Mac code-domain model |
|---|---|---|---|---|---|
| `sub_1` | `0x1.fef9dc0000000p-2, 0x1.0000000000000p-1, 0x1.0083120000000p-1` | `0000, 0000, 0001` | `0000, 0000, 0001` | `True` (`a55a`) | `0, 1, 1` |
| `code_ties` | `0x1.0000000000000p-1, 0x1.fffa000000000p+14, 0x1.fffe000000000p+14` | `0000, 7ffe, 8000` | `0000, 7ffe, 8000` | `True` (`a55a`) | `1, 32767, 32768` |
| `near_32768` | `0x1.fffdf60000000p+14, 0x1.fffe000000000p+14, 0x1.0000000000000p+15` | `7fff, 8000, 8000` | `7fff, 8000, 8000` | `True` (`a55a`) | `32767, 32768, 32768` |
| `above_32768` | `0x1.fffcfa0000000p+15, 0x1.fffe000000000p+15, 0x1.0000000000000p+16` | `fffe, ffff, ffff` | `fffe, ffff, ffff` | `True` (`a55a`) | `32768, 32768, 32768` |

## Evidence

- The raw float32 hex words, output words, exact destination write events, instruction counts, import list, and callback list are retained in the JSON fixture.
- The fourth destination word was initialized to `a55a`; the RGBA-shaped writer restored/preserved it for every triplet.
- The AEX clamp domain observed at these leaves is `[0, 65535]`. The AEX conversion instruction is MXCSR-dependent; this run used MXCSR `0x00000000` (round-to-nearest-even), via `CVTSS2SI`/`CVTPS2DQ`. The Mac model is half-up and is not substituted for the AEX rule.
- Tie discriminators: code-domain `0.5` is AEX `0` versus Mac-model `1`; `32766.5` is AEX `32766` versus Mac-model `32767`; `32767.5` is AEX `32768` versus Mac-model `32768`.
- Xref/callsite audit found no direct executable `CALL`/`JMP` xref to either leaf. The leaf input is therefore proven only as raw code-domain `float32`; upstream normalization or scaling is open.

## Limits

This is a function-level AEX witness with a harness-constructed buffer. It does not establish full AE execution, Windows hardware behavior, or production/ledger changes.
