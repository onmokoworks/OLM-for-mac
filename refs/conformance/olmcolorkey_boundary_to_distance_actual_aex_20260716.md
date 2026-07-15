# OLMColorKey Boundary To Distance Witness 20260716

This is a bounded Mac-local Unicorn execution of the checked-in Windows PE.
It is not AE-host execution and makes no AE-exact claim.

The witness executes `FUN_180008c90` on a 5x3 RGBA8 matte with one nonzero
center pixel, then passes the returned seed world directly to the checked-in
distance leaves `FUN_180006e20` (type 1) and `FUN_180005d60` (type 2). Both
leaves return `RAX=0`, import nothing, and write nonzero float distance output.
The exact grids and instruction counts are retained in the JSON artifact.

## ABI result

- Seed: `RCX=source_world`, `RDX=seed_world`, `R8D=8`.
- Distance: `RCX=context`, `RDX=seed_world`, `R8=distance_world`, `XMM3=255.0`.
- World fields used: `+0x18` payload, `+0x20` row bytes, `+0x24` width,
  `+0x28` height.
- Context fields supplied: `+0x120=255`, `+0x128=255`.

This advances the executable boundary from seed construction to distance
field production for types 1 and 2. The next ABI blocker is type 3,
`FUN_180007ec0`: its decomp allocates an internal squared-distance buffer
through the context's `+0x180` AE handle suite. This witness deliberately does
not invent that host table or claim type 3 execution.
