# OLMBlur case_0006 actual-AEX dependency-cone worker probe

## FACT

- AEX SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- Entry/helper: `0x180002280`, `0x180001000`, `0x180001980`
- Worker status: `return`; elapsed `542.632` s
- Helper calls observed per witness run: `[120, 120]` (expected 120 each)
- Portable trace self-check against current worker: `True`
- Source staging, helper call ABI/planes/origins/offsets, stage outputs, final pre-store float bits, and stored words are retained in the JSON report.
- `pow`, `powf`, and `expf` execute through the loader's host-backed libm callbacks; they are not native Windows CRT calls.

## Witnesses

- `(314,14)`: actual pre-store `['0x45098f32', '0x45098f32', '0x45098f32']`, portable `['0x45098f32', '0x45098f32', '0x45098f32']`; actual stored RGB `[2201, 2201, 2201]`, portable `[2201, 2201, 2201]`, Windows PNG RGBA `[2201, 2201, 2201, 65535]`.
- `(29,71)`: actual pre-store `['0x4435beb4', '0x4435beb4', '0x4435beb4']`, portable `['0x4435beb4', '0x4435beb4', '0x4435beb4']`; actual stored RGB `[727, 727, 727]`, portable `[727, 727, 727]`, Windows PNG RGBA `[725, 725, 725, 65535]`.

## INFERENCE

- The dependency-cone restriction is exact for the two witnesses if each helper is local to its recorded radius and the six chunks are disjoint, as established by the helper ABI fixtures and disassembly. Pixels outside the cone are not full-frame output evidence.
- First current-portable difference: `None`.
- Windows PNG difference points: `['(29,71)']`. The first Windows internal difference is not localized because no same-run Windows typed helper/pre-store trace is available.
- This is a typed worker/helper/store comparison. No PNG-derived tuning or production-source change was made.
