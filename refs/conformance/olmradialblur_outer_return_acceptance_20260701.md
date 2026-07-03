# OLMRadialBlur Outer Return Acceptance - 2026-07-01

This note explains how to judge the currently pending Windows outer-lane
runtime package.

## Current package scope

- package:
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_caller_collapse_followup_20260701.zip`
- request id:
  `olmradialblur_caller_collapse_followup_20260701`

The package asks for two separate witness chains inside one return:

1. Zoom caller-collapse:
   - `case_0009`
   - witness `(6,0)`
2. tiny Rotation upstream RGB/substitute path:
   - `case_0010`
   - witness `(1614,6)`

## Why this needs an acceptance note

The current package is already narrow, but it still spans two distinct
unresolved lanes.

That means a returned zip can be:

- enough for Zoom but not tiny Rotation
- enough for tiny Rotation but not Zoom
- partial for both

Without an explicit rule, it is too easy to over-promote a useful but
incomplete return into a broad RadialBlur code move.

## `answered`

Classify the package as fully `answered` only if it returns actionable typed
chains for **both** lanes:

### Zoom

- sampler return RGBA
- preserved validity at `+0xf252`
- accumulated or normalized `+0xf250`
- final polar `+0xe.alpha`
- pre-writeback RGBA float
- final stored RGBA8
- denominator or equivalent normalization state explaining Windows
  `0.99999994` versus local `1.0`

### tiny Rotation

- inverse-sampler input / source-polar coordinates
- validity / border branch decision
- fallback or substitute-path fact if present
- preserved validity at `+0xf252`
- accumulated `+0xf250` RGBA
- normalized final polar `+0xe` RGBA
- pre-writeback RGBA float
- final stored RGBA8

## `answered_partial`

Classify the package as `answered_partial` if any of these happen:

- Zoom chain is actionable, but tiny Rotation remains sparse / unisolated
- tiny Rotation chain is actionable, but Zoom lacks the denominator /
  caller-collapse explanation
- both lanes gain useful neighborhood structure, but at least one still lacks
  the typed chain needed for implementation

This is the expected conservative result if the debugger can hold one witness
path cleanly but not the other.

## `trace-too-sparse` / `not isolated`

Use these when the return does not isolate the exact requested chain:

- final bytes only
- closest sample only
- neighborhood hit without the requested witness point
- rejected local substitute re-confirmation without new upstream values

For Zoom specifically, final `[20,3,3,254]` without the denominator /
caller-collapse path is still not enough.

For tiny Rotation specifically, a white final byte without the upstream
population chain is still not enough.

## Practical follow-up if only one lane lands

### If Zoom lands but tiny Rotation does not

Keep RadialBlur globally blocked and narrow the next ask to:

- `case_0010 (1614,6)`
- upstream RGB / substitute-path / source-grid population only

### If tiny Rotation lands but Zoom does not

Keep RadialBlur globally blocked and narrow the next ask to:

- `case_0009 (6,0)`
- caller-collapse / denominator only

## Forbidden conclusion

Do not treat a package as "RadialBlur answered" just because one lane is now
understood.

Implementation may move locally on the answered lane, but the overall outer
RadialBlur lane remains partially unresolved until both witness chains are
covered or one is conclusively retired.
