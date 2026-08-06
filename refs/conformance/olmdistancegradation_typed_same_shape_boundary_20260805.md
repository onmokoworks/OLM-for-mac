# OLMDistanceGradation typed same-shape boundary

- Status: `pass`
- Scope: Mac production `RenderBits<P>` entry boundary for PF8, PF16, and PF32 worlds; not AE exact and not a Windows pixel-equivalence claim.
- Selected unfinished bounded case: host-world/resize staging immediately before the already typed Mac kernel.

## Implementation

`RenderBits<P>` now rejects null worlds/data, negative dimensions, input/output dimension mismatches, and row strides shorter than `width * sizeof(P)`. This makes the portable typed kernel's ownership explicit: non-identity host resize or depth conversion must happen before entry and cannot be silently approximated by the kernel.

## Focused fixture

`tools/emulation/dg_renderbits_real_harness_20260716.cpp` executes eight production-source fixtures:

- tight and padded PF8, PF16, and PF32 same-shape worlds (six cases);
- PF8 shape mismatch with destination canary unchanged;
- PF8 short input row with destination canary unchanged.

`tools/emulation/test_olmdistancegradation_renderbits_host_resize_staging_20260717.py` also retains its independent three-depth row-layout model and rejects non-identity resize.

## Verification

```text
PASS staging-contract cases=4
PASS production-renderbits harness cases=8
PASS scope=Mac-local-layout-only no-AEX-exact-claim
```

The static Windows typed-dispatch contract and the existing 16bpc fail-closed boundary test also pass. No AEXCompat change was required.

## Boundary

This closes only safe entry into the portable same-shape typed kernel. The actual Windows `RenderBits` host-world allocation/resize sequence, non-identity resize kernel, AE checkout behavior, and whole-frame equality remain separate work.
