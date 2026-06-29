# DistanceGradation 16bpc bg-compose return audit - 2026-06-27

Windows returned explicit `Use Background Color=1` and `=0` variants for
`case_0020..0023`. This audit compares those variants at the focused witness
pixels and against the earlier Mac `no_bg` probe.

| Case | Witness | Windows bg_on | Windows bg_off | Mac no_bg probe | Reading |
| --- | --- | --- | --- | --- | --- |
| `case_0020` | `(951,417)` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | Windows bg_off witness stays grad-color opaque; does not match prior Mac no_bg probe |
| `case_0021` | `(951,417)` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | Windows bg_off witness stays grad-color opaque; does not match prior Mac no_bg probe |
| `case_0022` | `(4,0)` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | Windows bg_off witness stays grad-color opaque; does not match prior Mac no_bg probe |
| `case_0023` | `(1699,7)` | `[65535, 0, 0, 65535]` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | Windows bg_off witness flips transparent, but still differs from prior Mac no_bg probe |

## Whole-frame diffs

| Case | Windows bg_on vs bg_off nonzero px | Windows bg_off vs Mac no_bg probe nonzero px |
| --- | ---: | ---: |
| `case_0020` | 666621 | 1001 |
| `case_0021` | 666621 | 1002 |
| `case_0022` | 1371064 | 9347 |
| `case_0023` | 1890872 | 1388 |

## Conclusion

- The Windows `bg_off` variants invalidate the earlier simplification that `case_0020..0023` only disagree once `Use Background Color=1` participates.
- `case_0020..0022` keep the gradation-color opaque witness even with `Use Background Color=0` on Windows.
- `case_0023` does change meaningfully between bg_on and bg_off, but the returned bg_off still does not match the prior Mac no_bg probe over the whole frame.
- So the active 16bpc DistanceGradation question is again upstream of just the bg-on compose branch.
