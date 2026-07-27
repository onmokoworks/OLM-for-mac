# OLMBlur 32bpc case_0004 AE exact

`OLMBlur/case_0004` is AE exact for the declared 32bpc Non-Legacy profile.

- Host: Adobe After Effects `26.3x87`
- Project: `32bpc`, Software renderer raw `1816`, working-space raw `None`,
  linear blending off
- Effect: Blur Amount requested `125.6` (AE readback
  `125.599998474121`), Blur Smoothness `100`, Number of Repeat `4`,
  Bias Direction `1`, Legacy `0`
- Output: `OLM EXR 32 Float`, uncompressed `A/B/G/R` FLOAT, `1920x1080`
- Input SHA-256:
  `cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4`

Windows rendered the hash-bound AEPX whose path-normalized SHA-256 is
`6e93b35f408cce21d4bd41f373ea774232a24163e727a0874205328328db1cdc`.
The accepted Mac run used a fresh project, new composition/effect identities,
and a new output root, then read back the same declared contract.

Windows Kernel Process ETW binds `aerender` PID `11068` to child
`AfterFX.com` PID `24992` and records load/unload events for:

`C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMBlur.aex`

The loaded AEX SHA-256 is
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
The initial 10 ms `Process.Modules` poll missed this short-lived child and
therefore remained fail-closed. Promotion uses the retained ETW process-start
event and the same-PID Image Load/Unload chain, not that missed poll.

During the final fresh Mac render, `vmmap` binds After Effects PID `23341` to
the exact installed Mach-O path and SHA-256
`c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e`.

Semantic FLOAT32 word comparison gives:

| gate | mismatched values | max raw u32 delta |
| --- | ---: | ---: |
| Windows no-effect vs Mac no-effect | 0 / 8,294,400 | 0 |
| Windows effect-on vs Mac effect-on | 0 / 8,294,400 | 0 |

The effect is active rather than a pass-through: effect-on differs from the
no-effect control at exactly `287,612` values on both hosts, with the same
maximum raw u32 delta `1,054,037,931`.

## Root cause

The old Mac AE effect output differed from the ETW-bound Windows effect at
`5,439/8,294,400` FLOAT32 words with maximum raw delta `4`; the no-effect
control was already exact. This excludes project color management as the
source of the residual.

The Non-Legacy coefficient audit had already localized the first old-path
split to iteration 1, weight index 57: AEX-derived `0x3ecaa909` versus macOS
`expf` output `0x3ecaa908`. The binary-grounded candidate preserves the
float32 exponent and the existing `powf`/`pow`, radius, sigma, and denominator
order, but evaluates binary64 `exp` before casting to float32. It matches all
`177/177` declared coefficient words over radii `[125,36,10,2]`.

Applying only that weight-generation change in
`core/olmblur_worker32_nonlegacy.cpp` makes the final fresh Mac AE output
raw-exact against Windows. All seven complete actual-AEX 32bpc Non-Legacy
worker fixtures remain byte-exact. The machine-readable evidence is
`refs/conformance/olmblur_32bpc_case0004_ae_exact_20260727.json`.
