# OLMBlur PF16 writer half-tie microfixture

Date: 2026-07-13

## Result

`PASS`: the actual 2025 `OLMBlur.aex` writer interval
`0x1800030e2..0x180003123` executed on three controlled float32 values.

| raw float | actual stored word | add-half/truncate | nearest-even |
| ---: | ---: | ---: | ---: |
| 1100.5 | 1101 | 1101 | 1100 |
| 1101.5 | 1102 | 1102 | 1102 |
| 32767.5 | 32768 | 32768 | 32768 |

The first value discriminates the rules. The actual writer uses
`float32 + 0.5`, its clamp/helper, and `CVTTSS2SI`; it is not a nearest-even
writer. The run executed 22 actual-AEX instructions and preserved alpha word
`32768`.

Binary SHA-256:
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.

Runner:
`tools/emulation/test_olmblur_writer16_half_ties_20260713.py`.

## Scope

This closes PF16 writer semantics only. It is a controlled binary microtest,
not Windows/Mac AE case conformance. It does not prove that a live case reaches
the writer with the same pre-store float. In particular, it does not justify
classifying `case_0006` as `AE exact`; its remaining lane is upstream float or
host/reference provenance.
