# OLMBlur 32bpc Mac AE candidate audit

## Contract

- Mac AE: `26.3x87`
- project: `32bpc`, working space `None`, linear blending `false`
- output template: `OLM EXR 32 Float`
- output: uncompressed FLOAT32 RGBA OpenEXR
- Mac plug-in binary SHA-256:
  `3f47a0d3da033c6092f1997c406c9feb0644afcaeaf63bdeb7b7900064d02ff2`
- focused spec:
  `refs/reference_requests/olmblur_32bpc_mac_windows_float_focus_20260711.json`

## No-effect control

Using normalized PNG inputs, Windows before-effects EXR versus Mac effect-off
EXR gives:

| case | mismatched float values | max raw-u32 delta |
| --- | ---: | ---: |
| 0001 | 0 | 0 |
| 0002 | 0 | 0 |
| 0003 | 0 | 0 |
| 0004 | 0 | 0 |
| 0005 | 63,644 | 32,639 |
| 0006 | 63,644 | 32,639 |
| 0007 | 63,644 | 32,639 |

This proves the current template and host path can be cross-host exact for the
first four inputs. Cases 0005 through 0007 still carry a small PNG-import/input
conversion difference and cannot yet support a direct effect verdict.

## Effect-on direct comparison

All seven current Windows effect EXRs differ from the Mac candidates. Alpha is
exact in every case. Cases 0001 through 0004 differ only in red; cases 0005
through 0007 differ in RGB. Direct mismatch counts are:

| case | mismatched float values |
| --- | ---: |
| 0001 | 207,098 |
| 0002 | 207,098 |
| 0003 | 518,400 |
| 0004 | 287,612 |
| 0005 | 2,165,806 |
| 0006 | 5,911,831 |
| 0007 | 5,899,212 |

## Binary evidence and verdict

The portable 32bpc complete workers replay actual 2025 AEX fixtures byte-exact
at every declared parameter tuple:

- Non-Legacy `FUN_180004b80`: seven fixtures, including amounts `129.4`,
  `125.6`, and `5`, repeats `2/4/10`, and both bias orders.
- Legacy `FUN_1800086d0`: five fixtures, including `248.6/100/10/bias1` and
  `5/100/10/bias1`.

The retained Windows 32bpc EXR return records AE/renderer/depth and artifact
hashes, but not the loaded OLMBlur AEX hash. Therefore the effect-on mismatch
cannot yet be assigned to the current Mac worker: a Windows plug-in version
split remains a live explanation, as already observed in the retained 8bpc
families.

Classification: `binary-grounded`, Mac candidate rendered, `AE exact` not
proven. Next allowed action is a hash-pinned current-AEX 8/32bpc recapture with
effect-disabled controls. Do not tune the exact worker from the unpinned EXRs.
