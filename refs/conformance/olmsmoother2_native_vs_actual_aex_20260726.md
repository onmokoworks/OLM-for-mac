# OLMSmoother2 Native vs Actual-AEX Checkpoint (2026-07-26)

## Status

This is a local native-port differential against the 12/12-exact AEXCompat
oracle. It is not Mac AE `AE exact`.

The Mac port previously forced the internal writer premultiply flag on.
Windows runtime evidence reads `param_8+0x19 == 0`: the AEX writer emits
straight RGB and AE premultiplies the later PNG export. Disabling the duplicate
writer premultiply removes the broad residual and makes cases 0002 and 0003
exact against both preserved actual-AEX raw output and AE-normalized output.

## Result After Binary-Grounded Leaf and Gamma Fixes

Four long-leaf scale initializers now match the AEX's `1.0f` default before
their optional half-scale chase:

- `win_leaf_ec40`
- `win_leaf_e640`
- `win_leaf_ef20`
- `win_leaf_e950`

The v2 gamma-color comparison now uses the internal setup flag encoded by
`FUN_180004e10` (`v1=1`, `v2=0`) instead of treating the UI version number as
that flag. The CLI also selects the five exact `"Gamma Color"` parameter
records instead of counting unrelated textual occurrences.

| Case | raw max | raw differing px | normalized max | normalized differing px |
| --- | ---: | ---: | ---: | ---: |
| 0001 | 1 | 83 | 1 | 83 |
| 0002 | 0 | 0 | 0 | 0 |
| 0003 | 0 | 0 | 0 | 0 |
| 0004 | 1 | 108 | 1 | 108 |
| 0005 | 1 | 7 | 1 | 7 |
| 0006 | 1 | 113 | 1 | 113 |
| 0007 | 1 | 34 | 1 | 34 |
| 0008 | 1 | 1 | 0 | 0 |
| 0009 v1 mode | 1 | 42 | 1 | 42 |
| 0010 gamma 3 | 1 | 41 | 1 | 41 |
| 0011 gamma 5 blue | 1 | 46 | 1 | 45 |
| 0012 gamma 5 red/blue | 1 | 18 | 1 | 18 |

Before the fix, every case had a broad raw residual with `max_diff=255`; the
AE-normalized case 0002 residual alone covered 3,247 pixels. The fixed case
0002 is `max_diff=0`. Current native status is raw exact `2/12`, normalized
exact `3/12`, and all remaining cases have `max_diff=1`. This is not
Mac AE `AE exact`.

## Current PF8 Boundary

Case 0001 witness `(1699,8)` was reduced to a 9x9 input without changing the
target residual. The native writer probe and AEXCompat execution dossier show:

- native raw RGBA: `[204,204,204,163]`
- actual-AEX raw RGBA: `[204,204,204,164]`
- native cce0 alpha bits: `0x3f242423`
- actual-AEX cce0/ab00 alpha bits: `0x3f242424`
- native cce0-to-PF8 writer replay matches its produced bytes exactly
- actual-AEX `ab00` center alpha bits: `0x3f41c1c3`
- native `ab00` center alpha bits: `0x3f41c1c2`

The first observed difference is therefore upstream of the final writer and
already present at the `ab00` center input. For byte value 193,
`float32(193 / 255)` gives `0x3f41c1c2`, while
`float32(193 * float32(1/255))` gives `0x3f41c1c3`.

Applying reciprocal multiplication to the entire PF8 input was rejected:
classification topology changed broadly. Applying a global positive one-ULP
output adjustment was also rejected: it improved the representative witness
but increased residual counts in cases 0004 and 0006. The next proof must
identify the exact Windows host conversion/arithmetic boundary per operation;
neither global input nor writer retuning is allowed.

## Reproduction

The native CLI was rebuilt from the current source:

```sh
refs/scripts/build_olmsmoother2_cli.sh \
  /tmp/olmsmoother2_cli_keep_premul0_20260725
```

Inputs and parameters came from the same manifest and SHA-pinned original
source used by:

`refs/conformance/olmsmoother2_aexcompat_host_io_exact_20260725.md`
