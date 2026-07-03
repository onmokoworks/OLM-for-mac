# OLMRadialBlur Outer Witness Contract - 2026-07-01

This note freezes the two surviving outer-lane proof boundaries so that a
Windows runtime return can be judged quickly and consistently.

## Active package

- request id:
  `olmradialblur_caller_collapse_followup_20260701`
- package:
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_caller_collapse_followup_20260701.zip`

The package is intentionally narrow. It is not asking for broad RadialBlur
behavior; it is asking for the exact typed witness chain on one Zoom pixel and
one tiny Rotation pixel.

## Lane split

Treat these as separate proof lanes even though they share one package.

1. Zoom caller-collapse lane
   - case: `case_0009`
   - witness: `(6,0)`
   - current local status:
     - RGB already matches at the witness
     - final alpha is `255` locally vs `254` on Windows
     - naive validity-side substitutes are already rejected
2. tiny Rotation RGB/substitute-path lane
   - case: `case_0010`
   - witness: `(1614,6)`
   - current local status:
     - final alpha is already fully live locally
     - Windows is white at the witness
     - local candidate is black there
     - the missing bright lobe is upstream of final inverse sampling

## What is already ruled out

### Zoom

- not a final byte-packing issue
- not direct use of the current preserved-validity plane as final alpha
- not a simple "blur the validity bits with the same kernel" fix
- not a broad sampler-geometry mismatch

The strongest local evidence is the same-row probe:

- final alpha stays near-opaque across `x=2..10`
- current preserved-validity proxy collapses much faster
- largest `alpha_u8 - validity_alpha_u8` gap reaches `208`

So the remaining lane is narrower than "sample the validity plane".

### tiny Rotation

- not a validity-only alpha collapse
- not just final inverse-sample masking
- not a one-pixel displacement story
- not fixed by bounded row-coupling probes

The strongest local evidence is:

- `validity_alpha_u8` stays `255` at and around the witness
- contributing `cell_rgb` at `(1614,6)` is already dark/negative
- direct `src_cell_rgba` for the four source polar cells is all black

So the missing bright lobe must come from upstream Rotation contribution
geometry, substitute-path population, or source-grid placement before the final
inverse sample.

## Exact Windows facts that count as actionable

### Zoom answered

An actionable Zoom return must include a typed chain that reaches the final
stored byte through the caller-collapse path:

- sampler return RGBA
- preserved validity at `+0xf252`
- accumulated or normalized `+0xf250`
- final polar `+0xe.alpha`
- pre-writeback RGBA float
- final stored RGBA8
- alpha coverage denominator, equivalent normalization state, or a concrete
  reason why Windows keeps `0.99999994` instead of local `1.0`

### tiny Rotation answered

An actionable tiny Rotation return must include the exact branch that creates
or suppresses the missing bright lobe:

- inverse-sampler input / source-polar coordinates
- validity / border branch decision
- fallback or substitute-path fact if one exists
- preserved validity at `+0xf252`
- accumulated `+0xf250` RGBA
- normalized final polar `+0xe` RGBA
- pre-writeback RGBA float
- final stored RGBA8

## Returns that are not enough

Do not treat any of these as answered:

- final PNG bytes only
- final stored bytes without upstream typed state
- placeholder or schema-only traces
- a trace that hits the neighborhood but does not isolate `(6,0)` or `(1614,6)`
- a retry that only reconfirms rejected local substitutes

Those should be classified as `answered_partial`, `trace-too-sparse`,
`not isolated`, or `non-actionable`.

The currently shared package spans both Zoom and tiny Rotation. See
`refs/conformance/olmradialblur_outer_return_acceptance_20260701.md` for how
to classify a return that fully answers only one of those two lanes.

## Forbidden implementation moves until proof lands

- do not tune final byte conversion for Zoom
- do not promote preserved-validity-plane substitutes as a fix
- do not retune global sampler geometry from PNG symptoms
- do not promote global row-coupling or wrap tweaks for tiny Rotation
- do not treat the tiny Rotation lane as an alpha problem

The next source change should explain one of these two witness chains directly.
