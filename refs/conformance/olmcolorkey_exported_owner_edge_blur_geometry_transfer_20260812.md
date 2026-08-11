# OLMColorKey exported-owner geometry transfer

Status: **exact**

Actual exported SmartPreRender/SmartRender and Mac production EffectMain match 12/12 declared cells. Production verifies callback counts, 33 parameter checkout/checkins, input immutability, and eight-byte input/output padding.

PF32 checkpoint capture localizes the former Type-3 residual to the direction-plane construction order in `0x8840 -> 0x56f0`: float distance multiplication, double `sin`, cast after `+1`, then float half-scale. Production now follows that general instruction order.

Boundary: Exact only for the declared padded 64x36 semitransparent multi-island fixture, four Direction 0/4 covering tuples, and PF8/PF16/PF32. The 32x18 public-owner matrix remains the control. Unlisted values, arbitrary geometry, native Windows, and AE-host execution are unclaimed.
