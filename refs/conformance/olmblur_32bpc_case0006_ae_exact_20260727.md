# OLMBlur 32bpc case_0006 AE exact

`OLMBlur/case_0006` is AE exact for the declared 32bpc Non-Legacy profile.

- Host: Adobe After Effects `26.3x87`
- Project: `32bpc`, Software renderer raw `1816`, working-space raw `None`,
  linear blending off
- Effect: Blur Amount `5`, Blur Smoothness `100`, Number of Repeat `10`,
  Bias Direction `1`, Legacy `0`
- Output: `OLM EXR 32 Float`, uncompressed `A/B/G/R` FLOAT, `1920x1080`
- Input SHA-256:
  `7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4`

Replacing only the platform-specific AEPX `fileReference` elements with one
canonical marker makes the fresh Mac and Windows projects byte-identical at
SHA-256:
`d29d4c7d01841f74b6b5993d5547d83bce8eb1af9a88dbc0daa28ee7ede9f6c6`.

Windows Kernel Process ETW binds `aerender` PID `10176` to child
`AfterFX.com` PID `46876` and records load/unload events for the hash-pinned
`OLMBlur.aex`:

`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`

The direct `Process.Modules` poll missed the short-lived child and remained
fail-closed. The accepted runtime proof is the ETW process-start plus
same-PID Image Load/Unload chain. On Mac, `vmmap` binds AE PID `26758` to the
installed Mach-O:

`c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e`

Semantic FLOAT32 word comparison gives:

| gate | mismatched values | max raw u32 delta |
| --- | ---: | ---: |
| Windows no-effect vs Mac no-effect | 0 / 8,294,400 | 0 |
| Windows effect-on vs Mac effect-on | 0 / 8,294,400 | 0 |

Effect-on differs from control at exactly `5,911,831` values on each host,
with the same maximum raw u32 delta `1,059,590,190`, so the exact result is
not a pass-through.

No source change was required after the case-0004 Non-Legacy coefficient
fix. This fresh same-contract capture supersedes the old 32bpc unpromoted
status for case_0006; it does not alter the separate historical 16bpc
provenance record. Machine-readable evidence:
`refs/conformance/olmblur_32bpc_case0006_ae_exact_20260727.json`.
