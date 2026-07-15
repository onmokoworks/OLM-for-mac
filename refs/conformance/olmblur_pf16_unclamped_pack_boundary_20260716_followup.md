# OLMBlur PF16 unclamped packing boundary follow-up

This is a new Mac-only local actual-AEX/portable proof. It makes no AE exact claim and does not alter earlier differentials or the ledger.

## Result

- The opaque 7x5 worker output is byte-exact after removing only the portable nominal `32768` clamp and storing the low 16 bits.
- The clamped candidate differs only at pixel 33 `(5,4)` and pixel 34 `(6,4)`, where the actual G-like words are `32787` and `32807`.
- The matching pre-store G-like floats are `32786.66015625` and `32806.6875`; `floorf(value + 0.5f)` produces those exact words.
- Therefore the prior two-word `border_radius4_opaque` mismatch begins at the portable final-writer range clamp, not at border sampling or coefficient accumulation.

## Binary rule

The PF16 writer at `0x1800030e2..0x18000311f` performs `ADDSS 0.5f`, calls `floorf`, executes `CVTTSS2SI EAX,XMM0`, and stores `AX`. There is no comparison, branch, or saturation in the three-channel writer interval. Controlled actual-AEX probes, using a host-backed `floorf` import callback, also confirm values above `65535` and below zero are packed by their low 16 bits after conversion.

## Scope

This excludes border sampling as the explanation for the two observed synthetic-fixture words only. It does not establish the cause of the live `case_0006` export residual and does not establish AE exactness.

## Command

`python3 tools/emulation/test_olmblur_pf16_unclamped_pack_boundary_20260716_followup.py`
