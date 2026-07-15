# OLMColorKey Edge Thin / Blur Actual-AEX Decomp Probe

This report is intentionally limited to the unresolved edge-stage boundary in
the `case_0009` family. It uses the checked-in Windows PE under local Unicorn
emulation on macOS. It does not claim AE-host execution, PNG equivalence, or
an AE-exact implementation.

## Evidence boundary

- `FACT`: `FUN_180008c90` at `0x180008c90` executes on synthetic byte planes.
- `FACT`: `FUN_1800049a0` at `0x1800049a0` executes on independent byte-boundary,
  float-distance, and float-weight planes.
- `FACT`: the full `FUN_1800094b0` orchestration is not invoked; its host
  context, temporary-world allocation, and apply path remain outside this
  probe.
- `INFERENCE`: the first executable semantic isolated here is boundary seed
  construction. Distance calculation follows it, and Edge Blur weighting
  follows the distance field. Apply/composite is later and unresolved.

## Probe artifacts

The machine-readable fixture results are in
`olmcolorkey_edge_thin_blur_actual_aex_decomp_probe_20260716.json`.

Fixtures discriminate an isolated center pixel, a frame corner, a diagonal
pair, and a horizontal run. The weight fixture holds boundary classification
and distance values independent: boundary columns are `x=0,3,6`, distance is
`x`, and amount is `4.0`.

The executable boundary result is concrete: an isolated center is cleared,
the corner remains seeded, a diagonal pair clears both pixels, and a horizontal
run clears all three pixels. The probe completed in `7395` instructions. The
boundary leaf imported no host or allocator routine. The weight leaf produced
the first-row values `[-0.285398, 0, 0, 0.892699, 0, 0, 1]`; the zero entries
at `x=1,2` are the deliberately zero boundary columns, while the nonzero
columns show the below-amount ramp and the `x=6 >= amount` full-weight branch.
The raw values are retained as emulator observations, not AE-exact byte
behavior.

## Static decomp cross-check

- `FUN_180008c90` writes the bit-depth maximum to the output for nonzero input,
  then clears it when an in-frame 8-neighbor is zero. Its out-of-frame branch
  supplies no zero neighbor, so frame edges are treated as inside for this
  boundary test.
- `FUN_1800049a0` returns zero for a zero boundary byte. For a nonzero boundary
  and distance below amount it evaluates the sine ramp; at or above amount it
  returns the full-scale weight. This is a weight semantic, not a seed or
  distance semantic.
- The decomp confirms `FUN_1800094b0` calls the boundary builder, selects a
  distance helper from the context distance-type field, then calls the blur
  apply helper. The probe stops before the host-dependent orchestration.

## Limits

No PNG tuning was performed. The probe does not determine which distance
helper is responsible for any remaining `case_0009` residual, nor how
`FUN_1800085b0` applies weights to source RGBA. Those require either a direct
leaf harness for the distance helper with its allocator/context contract or a
host-owned typed-world capture.
