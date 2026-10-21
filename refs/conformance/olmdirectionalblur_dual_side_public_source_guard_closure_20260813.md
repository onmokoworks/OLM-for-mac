# OLMDirectionalBlur fixed dual-side Type-2 exact-source closure

Status: **exact_bounded_public_owner_source_guard**

The public Smart route is restricted to fifteen exact cells: 32x18 tuple 1 at
PF8/PF16/PF32, plus 64x36 tuples 0, 1, 2 and 3 at PF8/PF16/PF32. They use the exact case_0001 input
bytes, depth-specific input/output rowbytes, zero extents, and disjoint payloads.
The current Mac public output is raw exact against the exported AEX Smart route.

Two hundred forty source/layout counterfactuals return
`PF_Err_BAD_CALLBACK_PARAM` before destination mutation while completing the
recorded public checkout/checkin lifecycle. This does not generalize to other
source bytes, 16x16 or other tuple/geometry, rowbytes, extent, overlap, renderer,
or native After Effects output.

Production SHA-256: `b39732e285688f1f8ae2fc5f64efcfba3d7ac52a1451a2685dd7b606bb18fb12`

Reproduce without AE:

```sh
python3 tools/emulation/test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.py
```
