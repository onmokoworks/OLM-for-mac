# OLMRadialBlur reconstructed caller-state witness

- Status: `pass`
- Classification: `bounded-reconstructed-caller-state-proven`
- Scope: bounded Mac Unicorn execution of the checked-in AEX; no AE-exact claim.
- Geometry: `32x1`, row slice `[0, 1)`.

## Actual-binary facts

- `live`: worker/scatter/sampler entries `1/1/1`, instructions `3147`, actual words `['0x00000000', '0x00000000', '0x00000000', '0x3f800000']`, portable exact `True`.
- `noop`: worker/scatter/sampler entries `1/1/1`, instructions `768`, actual words `['0x00000000', '0x00000000', '0x00000000', '0x00000000']`, portable exact `True`.

## Gates

- Issues: `[]`
- Live and no-op data state hashes are byte-identical before entry.
- The no-op side replaces only B150; A9D0 and D80 remain actual checked-in code.

## Boundary

The final-plane collapse is the documented bounded caller operation over the actual worker/scatter planes. This witness does not execute the full-size path, compare Windows, or establish AE exactness.
