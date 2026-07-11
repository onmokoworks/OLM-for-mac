# OLMBlur 32bpc Legacy Complete Worker

Date: 2026-07-11

## Scope

This report covers the portable `FUN_1800086d0` worker and its actual-AEX
complete-buffer fixtures. The fixture oracle is the current AEX execution,
not PNG or EXR output.

## Root Cause

The shared Legacy helper's unchanged branch must copy the current center
source pixel. Carry RGB is only the comparison state used to detect the
decompiled `all_same` path. Passing carry RGB to the unchanged writer was a
staging/helper-boundary mismatch with `FUN_1800014f0` and `FUN_180001ea0`.

The fix is confined to the existing helper change. No alpha-threshold rule,
Mac adapter, project file, ledger, or unrelated worker semantics were changed
for this closeout.

## Fixtures

| Case | Shape | Radius | Repeat | Bias | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `32bpc_legacy_basic` | 12x12 | 3 | 2 | 1 | exact |
| `32bpc_legacy_large_radius_reverse` | 18x18 | 11 | 3 | 2 | exact |
| `32bpc_legacy_mixed_alpha_reverse` | 18x12 | 3 | 2 | 2 | exact |
| `32bpc_legacy_declared_248_6_red_boundary` | 7x5 | 248.6 | 10 | 1 | exact |
| `32bpc_legacy_declared_5_mixed_alpha` | 9x7 | 5 | 10 | 1 | exact |

The two added cases use the declared 32bpc Legacy parameter tuples from the
focused request: `(248.6, 100, 10, 1, Legacy=1)` and
`(5, 100, 10, 1, Legacy=1)`. The first is a red-only interior with an
inactive boundary; the second uses the small mixed-alpha float pattern.

The replay compares every byte of each complete little-endian float32
A/R/G/B buffer and retains the existing first-mismatch diagnostics.

## Verification

Command 1:

```text
c++ -std=c++17 -O2 -ffp-contract=off -Icore core/olmblur_fullworker_helper.cpp core/olmblur_worker32_legacy.cpp tools/emulation/replay_olmblur_worker32_legacy.cpp -o /tmp/olmblur_worker32_legacy_replay_independent
```

Command 2:

```text
/tmp/olmblur_worker32_legacy_replay_independent tools/emulation/fixtures/olmblur_worker32_legacy
```

Output:

```text
PASS 32bpc_legacy_basic bytes=2304
PASS 32bpc_legacy_large_radius_reverse bytes=5184
PASS 32bpc_legacy_mixed_alpha_reverse bytes=3456
PASS 32bpc_legacy_declared_248_6_red_boundary bytes=560
PASS 32bpc_legacy_declared_5_mixed_alpha bytes=1008
```

Smoke wrapper:

```text
python3 refs/scripts/smoke_olmblur_worker32_legacy.py
```

Expected output:

```text
PASS 32bpc_legacy_basic bytes=2304
PASS 32bpc_legacy_large_radius_reverse bytes=5184
PASS 32bpc_legacy_mixed_alpha_reverse bytes=3456
[OK] OLMBlur 32bpc Legacy worker matches 5 complete AEX fixtures
```
