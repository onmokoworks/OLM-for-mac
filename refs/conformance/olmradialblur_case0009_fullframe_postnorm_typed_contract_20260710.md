# OLMRadialBlur case_0009 Full-Frame Post-Normalization Typed Witness

## Purpose

This is the one focused Windows confirmation for the latest bounded nonzero
witness in `tools/emulation/probe_radialblur_final_plane_small.py` and the AEX
fixture boundary recorded in `refs/conformance/aex_cpu_fixture_template_result_20260710.md`.
It targets the real Windows Software AEX full-frame `case_0009`; the bounded
probe and fixture are grounding evidence only, not substitute measurements.

Do not resend any older RadialBlur package, reuse an older return, stage on NAS,
or answer with a package-local recomputation or PNG-only comparison.

## One Run

Run the package-local `case_0009` request once at `1920x1080` under the current
Windows AE Software AEX and CDB. The render, AEX load, hook arm, three point
captures, final output, and console/log artifact must share one `run_id`.

At the post-normalization boundary `0x180005d99` (after `0x180005d96`), use the
actual inverse transform for each output point `(7,0)`, `(8,0)`, `(24,0)`.
Do not infer indices from the bounded crop or from a prior run. From the live
inverse coordinates calculate the ordered four sampler cells `00,10,01,11`,
their `(angle_index,radius_index)`, and absolute plane address.

## Typed Capture

For every point, capture all fields in `RETURN_RUNTIME_TRACE_TEMPLATE.json`:

- observed and reference RGBA8;
- actual inverse sample coordinates and the four ordered cell IDs/indices/addresses;
- each cell's `accum` RGBA float, `denom` float, `valid` float, and final `+0xe` RGBA float;
- the four bilinear weights, final alpha sum before byte conversion, and pre-byte alpha;
- exact hook address, `run_id`, and the same-run CDB console/log artifact.

The `valid` field is the live `+0xf252` value. The `accum` and `denom` fields
are the live accumulation and denominator planes. The `final` field is the
post-collapse `+0xe` final-polar plane value. Keep each value paired with its
cell and sampler slot; an alpha-only list is incomplete.

## Hook Liveness and Failure Reasons

The return must state whether `0x180005d99` hit exactly once and identify the
loaded AEX module/base. If the hook is not reached, the render does not finish,
the full-frame geometry is unavailable, a plane pointer is null, inverse
coordinates are out of range, or any typed field cannot be read, return
`answered_partial` or `failed_partial` with the exact reason, CDB command/log
artifact, hit count, and run id. Never fill missing values with bounded-probe
values or nulls while claiming `answered`.

## Acceptance

`answered` requires complete typed rows for all three points, one completed
full-frame run, exactly one post-normalization hook hit (or the documented
single hook invocation for the callsite), and an auditable console/log.

`answered_partial` is allowed only when `(7,0)` is complete and the exact
same-run isolation failure for `(8,0)` or `(24,0)` is recorded. `failed_partial`
covers PNG-only output, mixed runs, wrapper hit counts without the AEX boundary,
inferred cell IDs/addresses, null typed planes, missing liveness evidence, or
failure without an artifact.

No Mac source change is authorized by this package alone. The result is a
Windows evidence package for deciding whether the residual belongs to polar
population, caller collapse, or final byte conversion.
