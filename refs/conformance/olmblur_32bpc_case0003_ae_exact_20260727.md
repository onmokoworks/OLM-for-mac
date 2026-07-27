# OLMBlur 32bpc case_0003 AE exact

`OLMBlur/case_0003` is AE exact for the declared 32bpc Legacy profile.

- Host: Adobe After Effects `26.3x87`
- Project: `32bpc`, Software renderer raw `1816`, working-space raw `None`,
  linear blending off
- Effect: Blur Amount requested `248.6` (AE readback
  `248.600006103516`), Blur Smoothness `100`, Number of Repeat `10`,
  Bias Direction `1`, Legacy `1`
- Output: `OLM EXR 32 Float`, uncompressed `A/B/G/R` FLOAT, `1920x1080`
- Input SHA-256:
  `cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4`

Windows rendered the hash-bound AEPX whose path-normalized SHA-256 is
`0b19ad80101a90c82e5af56917fae6878285599d60b5ecfcafc8dcf726524c00`.
The accepted Mac run created a fresh project, composition, footage item, and
effect through JSX, then read back the same declared contract. This avoided
AE's read-only disk-cache reuse; the earlier saved-AEPX reruns completed both
frames in zero seconds without entering the instrumented dispatch and are
rejected as stale-cache false negatives.

Windows Kernel Process ETW binds `aerender` PID `50036` to child
`AfterFX.com` PID `47780` and records load/unload events for:

`C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMBlur.aex`

The loaded AEX SHA-256 is
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
During the final fresh Mac render, `vmmap` binds After Effects PID `18283` to
the exact installed Mach-O path and SHA-256
`a0b3a138007dbf0519773f41ba96e00f921f33f3db4d4923293d8f5fa495279d`.

Semantic FLOAT32 word comparison gives:

| gate | mismatched values | max raw u32 delta |
| --- | ---: | ---: |
| Windows no-effect vs Mac no-effect | 0 / 8,294,400 | 0 |
| Windows effect-on vs Mac effect-on | 0 / 8,294,400 | 0 |

The effect is active rather than a pass-through: effect-on differs from the
no-effect control at exactly `518,400` values on both hosts, with the same
maximum raw u32 delta `1,035,178,019`.

## Root cause

The AEX weight generator `FUN_180009e10` forms the exponent in float32 and
calls imported `expf`. With the exact case parameters, Windows
`ucrtbase.dll` and macOS `libSystem` differ at `8/2,490` unique coefficient
words by one ULP, distributed across iterations
`[0,0,0,0,1,1,2,3,1,0]`. Windows UCRT agrees with
binary64 `exp` followed by a float32 cast at `2,490/2,490`.

A native full-frame discriminator using the exact no-effect FLOAT input
reproduces the host-shaped residual: the old Mac float-`exp` path differs
from Windows at `54,235/33,177,600` words with maximum raw delta `4`.
Preserving the float32 exponent but evaluating `exp` in binary64 before the
float32 cast matches Windows at all `33,177,600` words. The production change
is confined to `core/olmblur_worker32_legacy.cpp`.

The candidate passes all five complete actual-AEX 32bpc Legacy worker
fixtures and all twelve production-source/AEX 32bpc adapter fixtures before
the AE promotion. The machine-readable evidence is
`refs/conformance/olmblur_32bpc_case0003_ae_exact_20260727.json`.
