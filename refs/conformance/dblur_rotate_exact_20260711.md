# OLMDirectionalBlur rotate primitive conformance

- Status: `portable_candidate_byte_exact_bounded`
- Primitive: `FUN_180001ec0`
- Candidate: `core/dblur_rotate.cpp` with `-O0 -fno-fast-math -ffp-contract=off`
- Fixture source: actual `plugins_2025/OLMDirectionalBlur.aex` helper replay
- Fixture set: six small float32 RGBA planes covering angle `0`, positive and
  negative angles, odd/even dimensions, thin boundaries, zero alpha, and
  poisoned destinations.

The replay is byte-exact for all six cases, including every untouched
destination byte. The final operation order follows the checked decomp:
alpha sum `top-right -> top-left -> bottom-left -> bottom-right`, and each RGB
sum `top-left -> top-right -> bottom-left -> bottom-right`.

`tools/emulation/smoke_dblur_rotate_exact.py` runs the byte-exact gate. The
generated shared object is compiled in a temporary directory outside the
repository and is not a fixture artifact.

Full-render integration is intentionally pending and was not modified.
