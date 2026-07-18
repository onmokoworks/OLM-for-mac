# OLMKiraKira signed geometry boundary

Date: 2026-07-18

## Result

- Status: **PASS_SIGNED_GEOMETRY_BOUNDARY_FAIL_CLOSED**
- Classification: **AEX_GENERATED_SIGNED_FILTER_GEOMETRY**
- This is a Mac-only Unicorn actual-AEX proof, not an AE exact result.

## FACT

- `FUN_181281e90` stores `R15D=0x80000000` at source `+0x08` and `R14D=0xc0000000` at source `+0x0c`.
- The same raw words reach FilterEngine's `ksize.width` and `anchor.x` stores.
- The unmodified assertion observes `ksize.width=-2147483648` and `anchor.x=-1073741824`, then stops without mutation.

## INFERENCE

The first proven generation of `0xc0000000` is the `FUN_181281e90` default-anchor branch: when `param_5 < 0`, the AEX computes `param_4 / 2` (`CDQ; SUB; SAR`) and writes the result to `R14D`. The value is then stored at source `+0x0c` and forwarded to FilterEngine as signed `anchor.x`. The values are generated AEX geometry, not a direct host-parameter value. This does not justify a patch yet.

## Verification

```text
python3 tools/emulation/test_olmkirakira_signed_geometry_boundary_20260718.py
```

The JSON report contains the full runtime evidence, static hashes, gates, and limits.
