# OLMBlur ROI/tile audit

The retained kernels have finite rectangular support, but the current generic
production lane remains full-frame only.

For Legacy at render scale `s`, one iteration uses
`r = floor(amount * s)`. After `repeat` horizontal/vertical pairs, the maximum
halo on every side is `repeat * r`.

For non-Legacy, let `decay = 1` when `repeat == 1`, otherwise
`pow(3 / amount, 1 / (repeat - 1))`. Iteration `i` uses
`r_i = floor(amount * s * pow(decay, i))`; the maximum halo is `sum(r_i)`.
To reproduce the worker exactly, `decay` must first be rounded to float32 and
the per-iteration power evaluated at the same double boundary as the worker;
a pre-render implementation should conservatively add one pixel if it cannot
preserve those operation boundaries. At Amount 1000 / Repeat 10 / scale 1 the
non-Legacy radii are 1000, 524, 275, 144, 75, 39, 20, 10, 5, and 3 (halo 2095).
Bias changes pass order and Smoothness changes weights, but neither changes the
structural support radius. The UI-wide worst case is Legacy Amount 1000,
Repeat 10: a 10,000-pixel halo per side.

## Blocking counterexample

For Legacy, an exact-radius halo is not sufficient. Its retained helper skips a
sample whose local coordinate is zero. For a full-frame output at global x=8
and radius 3, global x=5 participates. An exact tile checkout begins at global
x=5, maps it to local x=0, and the worker skips it. Full-frame and tiled output
therefore differ. The non-Legacy helper includes coordinate zero, so its
mathematical halo is sufficient.

An interior Legacy tile needs one additional guard pixel beyond the mathematical halo
on each non-frame-clipped side. At a true frame boundary the guard must not be
added, because local zero must continue to represent global zero. Implementing
that distinction requires the pre-render checkout result's global result/max
rect and a proven mapping between those rectangles, `PF_EffectWorld` origin,
extent, dimensions, and data pointer.

The existing adapters also require equal input/output geometry. A tiled path
would need a separate adapter that renders the expanded input into an equally
sized temporary world, then crops the requested output rectangle while
preserving independent output stride and alpha.

Without a native AE observation establishing the world/rectangle coordinate
mapping, enabling this in production would be speculative and risks seams or
out-of-bounds crops. The safe next implementation gate is:

1. Capture one interior and four frame-edge Smart Render tiles, recording
   output request, checkout result, input/output world origin, extent, width,
   height, rowbytes, and pointer offset.
2. Implement asymmetric `support + 1` guards only on non-frame-clipped sides.
3. Compare full-frame versus a tile mosaic for PF8/PF16/PF32, Legacy 0/1,
   both bias choices, transparent barriers, odd strides, and radii crossing
   every tile edge.
4. Preserve the existing exact-fixture lane unchanged.
