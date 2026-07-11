# OLMDistanceGradation case_0012 Dominant-channel Closeout

- Accepted patch: Both channel-mask branch uses src_a for dominant source channels only, limited to src_a <= 150/255; non-dominant channels keep straight-source ratio.

## Results

| Case | max true16 | mean true16 | nonzero px | channel max RGBA |
| --- | ---: | ---: | ---: | --- |
| `case_0012` | 2 | 0.001990500 | 2948 | `[2, 2, 2, 2]` |
| `case_0013` | 2 | 0.005261622 | 9006 | `[2, 2, 2, 2]` |
| `case_0014` | 4 | 0.005750386 | 9630 | `[4, 4, 4, 2]` |
| `case_0016` | 2 | 0.003700569 | 5373 | `[2, 2, 2, 0]` |

## Rejected Probes

- `both_channel_mask src_a for all source alpha`: rejected: full-alpha small-color channels exploded to max 64744 (refs/conformance/olmdistancegradation_case0012_both_srca_all_patch_20260708.md)
- `dominant-channel src_a up to 180/255`: rejected: high-alpha low-luma uniform point exploded to max 42676 (refs/conformance/olmdistancegradation_case0012_both_dominant180_patch_20260708.md)

## Reading

- The accepted rule is not AE exact for case_0012, but it narrows the broad Layer/no-bg Both residual from true16 max 28 to max 2 without moving neighboring Inside cases beyond their prior 2/4/2 residuals.
- The remaining max 2/4/2 family is now a common 16bpc export/rounding residual candidate rather than a broad Layer-source ownership problem.
- Do not broaden the rule past 150/255 without an additional dominance/low-luma guard or Windows store/export proof.

## Remaining Rounding Residual

- After the dominant-channel rule, case_0012/0013/0014/0016 are max 2/2/4/2 true16.
- Residual tuples are mostly even +/-2 true16 words, with case_0014 containing a small -4 RGB subset.
- Output-space what-if corrections show simple +2 on negative RGB would reduce means, but the condition depends on knowing the Windows reference and is not an implementation proof.
- Next evidence: Windows or Mac same-run PF16 store/export witness for representative +/-2 and case_0014 -4 pixels before changing global clamp/export rounding.
