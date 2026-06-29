# OLMBlur 16bpc Mac AE Rerun - 2026-06-28

## Summary

- Current Mac AE rerun reproduces the existing 16bpc residual family: 0/7 exact with `max_diff=2` for `case_0001..0006` and `max_diff=383` for `case_0007`.
- `case_0003` did not complete cleanly in the full batch progress log, so it was re-rendered as a single-case request. AppleEvent timed out after PNG creation, but `verify_manifest.py` comparison gives the same `max_diff=2` / `nz=414` result.
- Signed deltas are mixed (`reference - candidate` has both `-2` and `+2`) in the near-1LSB family. A one-line global round/truncate swap is not justified.
- `case_0007` keeps a separate localized Legacy border/seed anomaly at `(0,0)` where candidate is `[383,383,383,65535]` and reference is `[0,0,0,65535]`.

## Case Table

| Case | Classification | Max | Nonzero px | Signed delta counts | Key params |
| --- | --- | ---: | ---: | --- | --- |
| `olmblur__case_0001` | `sign-mixed-near-1lsb` | 2 | 66/518400 | `{'-2': 14, '2': 52}` | Blur Amount=129.399993896484, Blur Smoothness=100, Number of Repeat=2, Bias Direction=1, Legacy=0 |
| `olmblur__case_0002` | `sign-mixed-near-1lsb` | 2 | 67/518400 | `{'-2': 14, '2': 53}` | Blur Amount=129.399993896484, Blur Smoothness=100, Number of Repeat=2, Bias Direction=2, Legacy=0 |
| `olmblur__case_0003` | `legacy-sign-mixed-near-1lsb` | 2 | 414/518400 | `{'-2': 189, '2': 225}` | Blur Amount=248.600006103516, Blur Smoothness=100, Number of Repeat=10, Bias Direction=1, Legacy=1 |
| `olmblur__case_0004` | `sign-mixed-near-1lsb` | 2 | 55/518400 | `{'-2': 9, '2': 46}` | Blur Amount=125.599998474121, Blur Smoothness=100, Number of Repeat=4, Bias Direction=1, Legacy=0 |
| `olmblur__case_0005` | `sign-mixed-near-1lsb` | 2 | 106/2073600 | `{'-2': 54, '2': 112}` | Blur Amount=5, Blur Smoothness=100, Number of Repeat=2, Bias Direction=1, Legacy=0 |
| `olmblur__case_0006` | `sign-mixed-near-1lsb` | 2 | 283/2073600 | `{'-2': 113, '2': 233}` | Blur Amount=5, Blur Smoothness=100, Number of Repeat=10, Bias Direction=1, Legacy=0 |
| `olmblur__case_0007` | `legacy-border-plus-near-1lsb` | 383 | 304/2073600 | `{'-383': 3, '-2': 268, '2': 101}` | Blur Amount=5, Blur Smoothness=100, Number of Repeat=10, Bias Direction=1, Legacy=1 |

## Next Evidence

- For `case_0001..0006`: narrow proof belongs in accumulation/helper/final 16bpc writer order, not broad kernel tuning.
- For `case_0007`: isolate Legacy border/seed/all-same state and the alternate writer family before changing code.
- Preserve existing 8bpc AE exact behavior; do not apply a global rounding change from this 16bpc evidence alone.
