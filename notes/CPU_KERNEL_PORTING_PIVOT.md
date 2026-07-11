# CPU Kernel Porting Pivot

## Decision

The primary conformance lane is now a case-bound CPU-kernel fixture, not a
cross-host AE render image.

Windows AE `26.3x87` and Mac AE `26.3x87` produce a 32bpc EXR no-effect RGB
split. See
`refs/conformance/ae26_3_32bpc_noop_cross_platform_control_20260710.md`.
Therefore a Windows EXR versus Mac EXR difference cannot, by itself, be
attributed to an OLM plug-in algorithm.

## Roles

| Owner | Responsibility | Must not own |
| --- | --- | --- |
| Windows execution lane | Real-AEX CDB capture of case-bound buffers and, once proven, a portable C++ kernel validated against them | Mac AE SDK adapter or speculative UI mapping |
| Mac integration lane | Apple Silicon build, AE SDK adapter, UI/ABI, and Unicorn small-case verification | Reconstructing Windows evidence from cross-host AE images |
| Shared repository | Fixture contract, portable core, IR, deterministic tests | Tolerance-based completion claims |

## Fixture Contract

Each fixture is an atomic same-run record of:

1. ARGB input buffer plus dimensions and rowbytes.
2. The world/header fields consumed by the AEX function.
3. Raw, binary-built parameter-block bytes and a decoded manifest for review.
4. Named intermediate planes or cells at evidence-selected boundaries.
5. Output buffer and exact byte hash.

The portable kernel has no AE SDK types. It must match every fixture byte for
byte on Windows and Apple Silicon. The AE adapter is verified independently as
a host-integration layer.

## First Template

`OLMDistanceGradation` is first because its deterministic field path already
has an AEX emulator and OpenCV detours (`tools/emulation/OPENCV_DETOUR_DESIGN.md`).
The initial success condition is a small, repeatable Windows fixture that can
be replayed through:

1. real Windows AEX,
2. the portable C++ kernel, and
3. Mac/Unicorn for a bounded small case.

Only after that three-way agreement may the fixture contract be reused for
`OLMBlur`.

The first function-level loop is now complete. The real AEX fieldgen and
compose callbacks match the new portable C++ core byte-for-byte for the
committed fixtures, and case_0023 full-frame inside/outside field outputs each
match for `8,294,400` bytes. See
`refs/conformance/aex_cpu_fixture_template_result_20260710.md`. Compose
provenance is now a relocatable `binary-built` block: process-local world
pointers are zeroed and declared as relocations, while the scalar callback
range is retained from the binary layout and case manifest. It remains
distinct from a same-run Windows runtime capture.

The Mac plug-in now compiles and links the same portable distance stage used by
the fixture replay. `dt_to_normalized` delegates to
`core/olmdistancegradation_fieldgen.cpp`; depth-specific source-mask ownership,
inside/outside/BOTH dispatch, blur, compose, and AE writeback remain in the Mac
adapter. A brute-force distance oracle covers 280 Constant/Linear values in
addition to the AEX fixture and full-frame checks. This closes the duplicated
EDT implementation seam, but it is not a new `AE exact` claim.

## RadialBlur

The 2026-07-10 final-plane CDB return is `failed_partial`: it stopped during
hook arming and contains no typed sampler or final-write rows. It is archived
as evidence, not a basis for a code change. The bounded Unicorn probe now
executes the real parameter setup, prepass, and scatter on `32x32`, producing
nonzero accum/denom/valid values in all `196` polar cells. It also maps
`(7,0)`, `(8,0)`, and `(24,0)` to concrete four-cell sampler neighborhoods.
The next allowed action is one re-scoped Windows confirmation of those typed
cells; broad PNG tuning remains forbidden.

## Stop Rules

- Do not issue repeated CDB retries with the same hook design.
- Do not use PNG/EXR appearance matching to choose a kernel formula.
- If two bounded CDB fixture captures fail for a lane, demote CDB to
  confirmation-only and use Unicorn as the primary small-case oracle.
- A fixture lane is not complete until all declared bytes match exactly; a
  host-side AE render is a separate integration check.
