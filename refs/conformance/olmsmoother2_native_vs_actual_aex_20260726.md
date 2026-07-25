# OLMSmoother2 Native vs Actual-AEX Checkpoint (2026-07-26)

## Status

This is a local native-port differential against the 12/12-exact AEXCompat
oracle. It is not Mac AE `AE exact`.

The Mac port previously forced the internal writer premultiply flag on.
Windows runtime evidence reads `param_8+0x19 == 0`: the AEX writer emits
straight RGB and AE premultiplies the later PNG export. Disabling the duplicate
writer premultiply removes the broad residual and makes cases 0002 and 0003
exact against both preserved actual-AEX raw output and AE-normalized output.

## Result After the One-Line Writer Fix

| Case | raw max | raw differing px | normalized max | normalized differing px |
| --- | ---: | ---: | ---: | ---: |
| 0001 | 43 | 271 | 43 | 271 |
| 0002 | 0 | 0 | 0 | 0 |
| 0003 | 0 | 0 | 0 | 0 |
| 0004 | 48 | 304 | 48 | 304 |
| 0005 | 49 | 129 | 49 | 129 |
| 0006 | 48 | 139 | 48 | 139 |
| 0007 | 37 | 533 | 37 | 532 |
| 0008 | 11 | 440 | 10 | 439 |
| 0009 v1 mode | 37 | 723 | 37 | 722 |
| 0010 gamma 3 | 37 | 2,148 | 37 | 2,114 |
| 0011 gamma 5 blue | 75 | 2,070 | 75 | 2,038 |
| 0012 gamma 5 red/blue | 70 | 199 | 70 | 177 |

Before the fix, every case had a broad raw residual with `max_diff=255`; the
AE-normalized case 0002 residual alone covered 3,247 pixels. The fixed case
0002 is `max_diff=0`.

## Next Native Boundary

Case 0001 witness `(1612,455)` has:

- actual-AEX raw RGBA: `[255,0,0,170]`
- Mac native raw RGBA: `[255,0,0,127]`
- Mac polygon: two opaque red samples with weights `1/6` and `1/3`
- Mac accumulated/output alpha: `1/2`

Because the actual-AEX output alpha is `170/255 = 2/3`, the next narrow
boundary is the case-`0x10` polygon/cardinal dispatcher. It must explain the
missing `1/6` contribution before any cce0 or writer change.

## Reproduction

The native CLI was rebuilt from the current source:

```sh
refs/scripts/build_olmsmoother2_cli.sh \
  /tmp/olmsmoother2_cli_keep_premul0_20260725
```

Inputs and parameters came from the same manifest and SHA-pinned original
source used by:

`refs/conformance/olmsmoother2_aexcompat_host_io_exact_20260725.md`
