# OLMDirectionalBlur fixed Type-3 Layer exact-source closure

Status: **exact_bounded_public_owner_source_guard**

The public Smart tuple is restricted to the exact 16x16 case_0001 input and
independent Layer active bytes, exact PF8/PF16/PF32 rowbytes, zero extents, and
disjoint payloads. The current Mac public output is raw exact against the
Windows AEX exported Smart entry under the pinned repository AEXCompat/Unicorn
worker at all three depths; input, Layer, headers, and output padding remain
unchanged as applicable.

Fifty-four source/layout counterfactuals (18 per depth) return
`PF_Err_BAD_CALLBACK_PARAM` before destination mutation while completing the
recorded public checkout/checkin lifecycle. This does not generalize to other
source bytes, Layer bytes, tuple, geometry, rowbytes, extent, overlap, renderer,
or native After Effects output. This is not a native-Windows execution claim.

Production SHA-256: `f213902b4e606b1f35f548d801a66dd83213c254c6fa5cbfca7dae71daa9634f`

Reproduce without AE:

```sh
python3 tools/emulation/test_olmdirectionalblur_type3_layer_source_guard_closure_20260813.py
```
