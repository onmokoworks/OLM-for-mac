# OLMBlur 32bpc case_0007 AE exact

`OLMBlur/case_0007` is AE exact for the declared 32bpc Legacy profile.

- Host: Adobe After Effects `26.3x87`
- Project: `32bpc`, Software renderer raw `1816`, working-space raw `None`,
  linear blending off
- Effect: Blur Amount `5`, Blur Smoothness `100`, Number of Repeat `1`,
  Bias Direction `1`, Legacy `1`
- Output: `OLM EXR 32 Float`, uncompressed `A/B/G/R` FLOAT, `1920x1080`
- Input SHA-256:
  `7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4`

Replacing only the platform-specific AEPX `fileReference` elements with one
canonical marker makes the fresh Mac and Windows projects byte-identical at
SHA-256:
`0dcb11e1315ba32f35423829df594f08c4d01352e61bf025861dd6d4166b89b3`.

Windows Kernel Process ETW binds `aerender` PID `49120` to child
`AfterFX.com` PID `5160` and records load/unload events for the hash-pinned
`OLMBlur.aex`:

`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`

The direct `Process.Modules` poll missed the short-lived child and remained
fail-closed. The accepted runtime proof is the ETW process-start plus
same-PID Image Load/Unload chain. On Mac, `vmmap` binds AE PID `29205` to the
installed Mach-O:

`c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e`

Semantic FLOAT32 word comparison gives:

| gate | mismatched values | max raw u32 delta |
| --- | ---: | ---: |
| Windows no-effect vs Mac no-effect | 0 / 8,294,400 | 0 |
| Windows effect-on vs Mac effect-on | 0 / 8,294,400 | 0 |

Effect-on differs from control at exactly `1,176,535` values on each host,
with the same maximum raw u32 delta `1,060,570,798`, so the exact result is
not a pass-through.

No source change was required after the case-0004 coefficient fix. Together
with cases 0001 through 0006, this closes all seven declared OLMBlur 32bpc
cases under the current Software/FLOAT contract. Machine-readable evidence:
`refs/conformance/olmblur_32bpc_case0007_ae_exact_20260727.json`.
