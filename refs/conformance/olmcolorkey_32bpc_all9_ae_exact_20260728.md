# OLMColorKey declared 32bpc set — Windows/Mac AE exact

All nine declared OLMColorKey 32bpc cases are exact on Windows and Mac After
Effects `26.3x87`.

## Contract

- Software renderer (`gpuAccelType` raw `1816`)
- 32 bits per channel
- working-space raw value `None`
- linear blending off
- `OLM EXR 32 Float`, RGB+Alpha, uncompressed FLOAT, Preserve RGB
- semantic-channel raw FLOAT32 comparison
- independent no-effect and effect-on gates

Each of the 18 gates compares `8,294,400` FLOAT32 words. Every gate has zero
mismatches and max raw-u32 delta `0`.

## Newly promoted non-default cases

| Case | Parameters | Windows preparation / aerender / child PID | No-effect | Effect-on |
| --- | ---: | --- | ---: | ---: |
| `0001` | 219 exact readbacks | `19476 / 48820 / 43780` | `0 / 8,294,400` | `0 / 8,294,400` |
| `0003` | 219 exact readbacks | `10592 / 29548 / 10192` | `0 / 8,294,400` | `0 / 8,294,400` |
| `0004` | 219 exact readbacks | `43452 / 40644 / 39252` | `0 / 8,294,400` | `0 / 8,294,400` |
| `0005` | 219 exact readbacks | `49500 / 46168 / 53092` | `0 / 8,294,400` | `0 / 8,294,400` |
| `0006` | 219 exact readbacks | `53236 / 26224 / 47132` | `0 / 8,294,400` | `0 / 8,294,400` |
| `0007` | 219 exact readbacks | `41924 / 12904 / 36172` | `0 / 8,294,400` | `0 / 8,294,400` |
| `0008` | 219 exact readbacks | `6108 / 43492 / 14180` | `0 / 8,294,400` | `0 / 8,294,400` |

For every row, Kernel Process ETW records the `aerender.exe` process, its
`AfterFX.com` child, and that child's load/unload of
`OLMColorKey.aex` SHA-256
`9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
The Mac side is the same fresh all-nine run already bound by
`vmmap_exact_path` to AE PID `60412` and Mach-O SHA-256
`410d6cd6b568f7d2ae5bb426451eb3d628998a716a83f0cdbe3c5c0bc028ed7f`.

Windows construction is two-stage and fail-closed. Fresh AfterFX first adds a
native `OLM Color Key` effect, writes all 219 requested parameters, verifies
all readbacks, and saves the project. Fresh `aerender` then executes the
AEPX-embedded Preserve-RGB queues. This avoids both Mac-AEPX effect-control
conversion and the Windows-local output-template color transform that was
detected by the no-effect gate.

Cases `0002` and `0009` retain their independent earlier closeouts:

- `refs/conformance/olmcolorkey_32bpc_case0002_ae_exact_20260727.md`
- `refs/conformance/olmcolorkey_32bpc_case0009_ae_exact_20260728.md`

The older bulk Windows pair remains rejected. Its no-effect mismatch is a
source/output-contract failure and is not used for any promotion.

Machine-readable evidence:
`refs/conformance/olmcolorkey_32bpc_all9_ae_exact_20260728.json`.
