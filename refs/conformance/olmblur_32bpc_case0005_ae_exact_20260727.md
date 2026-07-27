# OLMBlur 32bpc case_0005 AE exact

`OLMBlur/case_0005` is AE exact for the declared 32bpc Non-Legacy profile.

- Host: Adobe After Effects `26.3x87`
- Project: `32bpc`, Software renderer raw `1816`, working-space raw `None`,
  linear blending off
- Effect: Blur Amount `5`, Blur Smoothness `100`, Number of Repeat `2`,
  Bias Direction `1`, Legacy `0`
- Output: `OLM EXR 32 Float`, uncompressed `A/B/G/R` FLOAT, `1920x1080`
- Input SHA-256:
  `7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4`

The Mac-created and Windows path-only AEPX files have the same normalized
SHA-256:
`3f006ba05a79730859f2433ca204f372f1f459a355eb59226ef2f00bf0b05eee`.

Windows Kernel Process ETW binds `aerender` PID `44264` to child
`AfterFX.com` PID `44300` and records load/unload events for the hash-pinned
`OLMBlur.aex`:

`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`

The direct `Process.Modules` poll missed the short-lived child and remained
fail-closed. The accepted runtime proof is the ETW process-start plus
same-PID Image Load/Unload chain. On Mac, `vmmap` binds AE PID `24997` to the
installed Mach-O:

`c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e`

Semantic FLOAT32 word comparison gives:

| gate | mismatched values | max raw u32 delta |
| --- | ---: | ---: |
| Windows no-effect vs Mac no-effect | 0 / 8,294,400 | 0 |
| Windows effect-on vs Mac effect-on | 0 / 8,294,400 | 0 |

Effect-on differs from control at exactly `2,165,806` values on each host,
with the same maximum raw u32 delta `1,059,693,019`, so the exact result is
not a pass-through.

## Older reference pair

The retained 2026-07-03 Windows pair is not used for promotion. Its no-effect
frame already differs from the fresh Mac no-effect frame at `63,644` words
with maximum raw delta `94,225,591`. Because the disagreement exists before
the effect, that pair is a different input/project-generation contract rather
than evidence of an OLMBlur arithmetic residual.

The fresh same-AEPX Windows recapture closes both gates without another core
change after the case-0004 coefficient fix. Machine-readable evidence:
`refs/conformance/olmblur_32bpc_case0005_ae_exact_20260727.json`.
