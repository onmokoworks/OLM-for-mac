# OLMSmoother2 case-07 32bpc Mac AE exact (2026-07-27)

The declared no-key `final_random10_olm_smoother_v2_07` slice is `AE exact`.
Windows and Mac AE `26.3x87` use the same hash-bound Preserve RGB source,
Software renderer, 32bpc project, working space `None`, disabled linear
blending, and uncompressed FLOAT RGBA EXR output contract.

The final Mac plug-in binary is
`63c1b84f7df409f8789da962b40b737fe76e470a8684b4b79f35a3d446cb2377`
and is built with the sole Xcode configuration at `-O2`.

| Gate | Compared words | Mismatches | Max raw u32 delta |
| --- | ---: | ---: | ---: |
| Windows PF32 effect entry vs bound source | 8,294,400 | 0 | 0 |
| Windows vs Mac no-effect control | 8,294,400 | 0 | 0 |
| Windows vs Mac effect-on | 8,294,400 | 0 | 0 |

The first algorithmic divergence was established at polygon antialias weight
generation. Windows uses separate SSE scalar multiply and add/subtract
instructions, while the ARM64 `-O2` build contracted matching source
expressions into FMA. At output pixel `(738,287)`, the direct Windows runtime
weight is `0x3c83df6f`; the pre-fix Mac weight was `0x3c83df70`.

The PF32-only implementation now preserves the Windows scalar rounding points
for antialias weights and final accumulation. Its sRGB decode/inverse tables
are byte-for-byte runtime captures from the loaded Windows AEX:

- decode: 40,000 bytes,
  `11056c2feda87964204a53471e172ae6fb6039a0c3120f6277c7ff115fe88cba`
- inverse: 40,000 bytes,
  `b7014467dcae06109111302b8c930494950d27b817d1390d6434605795772fbc`

The PF32 accumulator is a separate function. A first runtime-conditional
implementation perturbed ARM64 contraction in the frozen 8bpc accumulator and
produced nine max-1 regressions. After source-level separation, the same final
binary passed the complete 8bpc Mac AE request
`ae_pixel_olmsmoother2_current_aex_20260726_r3`: `12/12`, `max_diff=0`.

The machine-readable attestation is
`refs/conformance/olmsmoother2_case07_32bpc_mac_ae_exact_20260727.json`.
This promotes only the declared 32bpc case-07 slice. It does not promote
16bpc or untested 32bpc cases.
