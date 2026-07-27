# OLMBlur 32bpc case_0002 AE exact

`OLMBlur/case_0002` is AE exact for the declared 32bpc profile.

- Host: Adobe After Effects `26.3x87`
- Project: `32bpc`, Software renderer raw `1816`, working-space raw `None`,
  linear blending off
- Effect: Blur Amount requested `129.4` (AE readback
  `129.399993896484`), Blur Smoothness `100`, Number of Repeat `2`,
  Bias Direction `2`, Legacy `0`
- Output: `OLM EXR 32 Float`, uncompressed `A/B/G/R` FLOAT, `1920x1080`
- Input SHA-256:
  `cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4`

The Mac and Windows projects came from the same Mac AE-generated AEPX. Only
the three source/output `fileReference` elements differ. Replacing those
elements with role tokens gives the same normalized SHA-256 on both hosts:
`2ed3afe9d2b82c7e4dab2c5e3ae821d6d9e71497a1865e08f9d8f75d1e70a97a`.

Windows used one `aerender` process for the two embedded render-queue items.
Kernel Process ETW binds its child `AfterFX.com` PID `45732` to parent
`aerender` PID `42172`, then records load and unload events for:

`C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMBlur.aex`

The loaded AEX SHA-256 is
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
The Mac plug-in Mach-O SHA-256 is
`71df7efc027b463327fefa23575fff5f80d4b38ff529ae97418d79297f4f0d72`.

Both EXR pairs pass the fail-closed header gate: four FLOAT channels, no
compression, `1920x1080`, and no NaN or infinity. Semantic FLOAT32 word
comparison gives:

| gate | mismatched values | max raw u32 delta |
| --- | ---: | ---: |
| Windows no-effect vs Mac no-effect | 0 / 8,294,400 | 0 |
| Windows effect-on vs Mac effect-on | 0 / 8,294,400 | 0 |

The effect is active rather than a pass-through: effect-on differs from the
no-effect control at exactly `207,108` values on both hosts, with the same
maximum raw u32 delta `1,054,075,639`.

Container SHA-256 values differ across hosts because EXR metadata differs;
the acceptance comparator operates on semantic channel FLOAT32 words.
The machine-readable evidence is
`refs/conformance/olmblur_32bpc_case0002_ae_exact_20260727.json`.
