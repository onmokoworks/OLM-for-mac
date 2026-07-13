# Windows 32bpc Typed Procedural Fixture Package Contract

Scope: package a fail-closed Windows runner around the existing
`ae_generate_32bpc_typed_procedural_fixture.jsx` contract without touching the
fixture generator itself.

## Audited facts from the existing fixture

- source pixels are generated entirely inside AE from one black solid plus four
  integer-bounded solids at `64x64`
- the render contract is fixed to `32bpc`, working space `None`, and linear
  blending `false`
- the control/effect comparison is rendered from one comp by toggling only the
  enabled state of two precomp layers
- the JSX refuses stale outputs, unsupported effects, imported footage, and
  project-state drift
- the JSX also requires an empty AE project and empty render queue

## Packaging consequence

Because the JSX saves a project and fails if AE is not empty, the Windows
runner must fail closed when `AfterFX.exe` is already running and must kill the
fresh AE process after each case. Each effect therefore runs in its own clean
AE process.

## Packaged behavior

The package contains:

- the exact audited fixture JSX
- a PowerShell runner for Windows AE 26.3
- a generic render-record template
- a standalone raw-float EXR comparator plus EXR verifier helpers

The runner hashes the caller-supplied `OLMColorKey.aex` and
`OLMToonDilate.aex`, renders both `no_effect` and `effect_on` for each effect,
verifies the returned fixture manifest against the expected `64x64` source
recipe, records SHA-256 values for every output, and emits
`return_manifest.json`.

The packaged comparator accepts two render records, typically one macOS
reference record and one Windows return record, and fails closed unless:

- both records declare the same fixture contract and fixture JSX SHA-256
- both records declare `32bpc`, working space `None`, linear blending `false`,
  and output template `OLM EXR 32 Float`
- both records contain the same effect case set
- each referenced EXR is present, uncompressed, FLOAT, RGBA, and `64x64`
- both `no_effect` and `effect_on` outputs are raw-float-bit exact per case
