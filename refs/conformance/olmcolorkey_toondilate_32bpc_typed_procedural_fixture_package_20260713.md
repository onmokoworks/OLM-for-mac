# OLMColorKey / OLMToonDilate 32bpc Typed Procedural Fixture Package - 2026-07-13

This lane keeps the existing `scripts/ae_generate_32bpc_typed_procedural_fixture.jsx`
and `refs/scripts/smoke_ae_32bpc_typed_procedural_fixture.py` unchanged and
builds a Windows execution package around them.

## Audit outcome

The existing fixture already encodes the source contract we need:

- AE-generated `64x64` source only, with no imported footage
- one black background solid plus four integer-bounded alpha stages
- `32bpc`, working space `None`, linear blending `false`
- one render comp that flips only the enabled state of `no_effect` and
  `effect_on`
- fail-closed refusal on stale outputs, unsupported effects, missing EXRs, and
  project-state drift

One additional operational constraint matters for packaging: the JSX requires an
empty AE project and empty render queue, then saves the generated `.aep`. That
means the Windows runner cannot safely batch both effect cases inside one live
After Effects session.

## Package decision

The new package therefore does three things:

1. refuses to start if `AfterFX.exe` is already running
2. launches one fresh AE process per effect case
3. force-stops the AE process after each case so the next case starts from an
   empty project again

The package is scoped to two effects only:

- `OLM Color Key`
- `OLM Toon Dilate`

It pins the caller-supplied `OLMColorKey.aex` and `OLMToonDilate.aex` by
SHA-256, copies the audited fixture JSX into the package, and records a generic
render record with:

- platform
- AE version
- output template
- bundled fixture JSX SHA-256
- exact fixture contract
- output SHA-256 for `effect_no_effect_00000.exr` and
  `effect_effect_on_00000.exr`

## Compare path

The package also includes a standalone comparator. It is intentionally
fail-closed: two render records are accepted only when both hosts declare the
same fixture JSX hash and contract, and when both `no_effect` and `effect_on`
OpenEXR outputs are uncompressed FLOAT RGBA `64x64` files whose raw float bits
match exactly.

That gives us the bounded artifact we need for the next step: a Windows return
zip that can be compared against a Mac record generated from the same AE-only
source recipe without reopening the imported-EXR ambiguity that blocked the
earlier lane.
