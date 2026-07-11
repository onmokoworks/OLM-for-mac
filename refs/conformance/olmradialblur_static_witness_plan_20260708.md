# OLMRadialBlur Static Witness Plan - 2026-07-08

This note records the current narrow proof boundary while
`OLMDistanceGradation` waits on the depth-gate quantization witness.

## FACT

- Rotation keeps separate polar planes for sampled RGBA, span/gate, prepass
  alpha, prepass factor, and a preserved sampler-return side channel at
  `+0xf252`. The caller later collapses `+0xf252` into `+0xe.alpha` before the
  final inverse sample. The final inverse sampler does not read `+0xf252`
  directly.
- Repeat-border and non-repeat RGBA samplers do not treat alpha identically:
  the repeat-border sampler keeps raw accumulated alpha and returns a separate
  loose-window validity flag, while the non-repeat sampler rewrites alpha as
  `alpha_sum / weight_sum`.
- Zoom `(6,0)` has already been narrowed away from final byte packing. Windows
  pre-writeback floats truncate to the stored Windows byte; remaining evidence
  points upstream at caller-side alpha/sample formation.
- Tiny Rotation `case_0010 (1614,6)` is no longer explained by a simple
  validity-alpha collapse. Local CPU AEX emulation returns black from the
  normalized-polar final sampler path while the legacy PNG reference remains
  white.
- Low-alpha fringe has already been rejected for RadialBlur tiny Rotation and
  must not be reopened as the active hypothesis.

## Missing Typed Facts

1. Zoom: the live value domain of `+0xf252` on the top-row witness, plus its
   relation to `+0xf250.a` and final `+0xe.a`.
2. Inner: the exact update operator for the `+0x3c948` scalar plane inside or
   around `FUN_180001c90`, especially before prepass, after prepass, and after
   the first scatter hit.
3. Tiny Rotation: the typed relation between contributing cells'
   `+0xf250.rgba`, `+0xf252`, collapsed `+0xe.rgba`, and the actual final
   output buffer for `case_0010 (1614,6)` in one same-run witness.

## INFERENCE

- The highest-value local lane is still Zoom caller-collapse if we can get a
  CPU/AEX-side dump of `+0xf252 -> +0xe.alpha` without Windows. It could explain
  the guarded off-by-one family without PNG tuning.
- The highest-value Windows lane is Tiny Rotation final writeback/provenance:
  capture `+0xf250.rgba`, `+0xf252`, collapsed `+0xe.rgba`, and final output
  buffer RGBA for `case_0010 (1614,6)` in the same run. That separates a real
  CPU-side rule gap from a reference/export/path split.
- Inner should not be approached with span-minus-one or wrap toggles; the next
  useful proof is the scalar-plane writeback/update semantics.

## Next Action

Do not place a new RadialBlur zip into the shared `new` folder while the
DistanceGradation depth-gate package is active. If the shared queue is clear and
Windows runtime capacity is available, package a focused RadialBlur request for
`case_0010 (1614,6)` final-writeback/provenance with the typed values listed
above.
