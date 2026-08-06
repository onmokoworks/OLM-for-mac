# OLM Mac port orchestrator boundary — 2026-08-05

This is a current routing document, not a replacement for plugin-specific
conformance evidence.  Completion is judged by a connected path from the public
entrypoint through the real worker and writer to the installed Universal bundle,
then by a hash-bound AE host load/render.  Adding isolated fixtures is not itself
completion.

## Evidence precedence

1. Retained actual-AEX execution with binary identity pinned.
2. The same input through the current Mac production entry/dispatch/worker/writer.
3. Byte- or bit-exact active pixels, required internal planes, row padding, and
   callback/parameter contracts within the stated boundary.
4. The exact current Universal binary installed as the sole MediaCore bundle,
   with `arm64 x86_64` and strict codesign verification.
5. A hash-bound load/render in the target AE host.

Old PNG comparisons remain supporting evidence only.  They cannot replace a
missing entrypoint, typed dispatch, internal-plane, writer, installed-identity,
or current-host edge in this chain.

## Current integrated state

The standard Mac fixed-fixture suite passes all ten plugin lanes.  The aggregate
install preflight proves all ten currently expected executable hashes, both
architectures, and strict signatures.  After Effects was not running during the
latest preflight, so there is no current hash-bound AE load/render claim.

| Plugin | Strongest connected production evidence | Current completion edge |
|---|---|---|
| OLMBlur | All typed/legacy dispatch cells plus production public SmartPre→SmartRender→parameter checkout→PF8 writer are executed and installed-identity-bound | Actual exported AEX entry and current AE load/render |
| ColorKeep | Current installed binary is dynamically loaded; public `PF_Cmd_RENDER` connects synthetic ColorParam/iterate16 suites, PF16 worker/writer and retained actual output in one call | Adobe suite implementation and AE loaded-module/render identity; exact `ABOUT` text remains separate |
| OLMColorKey | Actual all-depth entry/worker/writer, production Smart path and all-depth public `PF_Cmd_RENDER` fallback connect to reproducible installed `__text`/`__const` identity | Remaining parameter cross-product and current AE mapping/render |
| OLMDirectionalBlur | One fail-closed route connects public production `EffectMain(SMART_RENDER)`, actual-exact PF16/PF32 cores/writers and the installed signed Universal bundle | Current AE load/render |
| OLMDistanceGradation | Actual classic PF8/PF16/PF32 owner-to-output branches now include Constant+blur entry/cvSmooth/PF32 writer exactness and installed identity | PF32 Smart remains actual-AEX unsupported; current AE load/render |
| OLMKiraKira | Production Mode4 connects both warps, recurrence, centered crop and PF8/PF16/PF32 actual-exact writers to installed identity | Live AE natural `EffectMain` owner delivery/load/render |
| OLMRadialBlur | Rotation/Zoom typed paths plus a compositional public SmartRender→RenderWorld→PF32 writer→installed identity route are exact | Dynamic AE callback ABI/load/render and remaining branch cross-product |
| OLMSmoother | PF8 canonical no-key and retained Color Key enabled full frames are pixel/byte exact in the installed Universal build | PF16 typed session remains AEXCompat-bounded; current AE load/render |
| OLMSmoother2 | Production classic PF16 and SmartRender PF32 public chains connect ordered host callbacks, actual classifier/worker-writer exact output and installed Universal identity | Actual exported entry invocation and current AE load/render |
| OLMToonDilate | Installed bundle is dynamically loaded and its exported SmartPre/SmartRender executes exact PF8 output; the wider route connects actual all-depth workers/writers and installed identity | Real AE load/render; composition metadata and legacy Render remain bounded/unproven |

## Integration gates

- `scripts/run_olm_mac_fixed_fixture_regression_20260805.py` is the standard
  Mac-only regression entrypoint.  It consumes retained Windows evidence and
  does not require a Windows host.
- `scripts/preflight_olm_all_universal_installs_20260805.py` is the fail-closed
  installed-identity gate.  Exit 2 with `ae_not_running` proves bundle identity,
  not host loading or rendering.
- Any production rebuild must update its plugin install evidence and the
  aggregate expected hash before host testing.
- AE host testing must identify the exact loaded executable hashes.  A render
  from an older process or older bundle does not close the host edge.

## Routing rule

Run at most one active agent per plugin.  That agent chooses the shortest
remaining connection in the path above; it need not follow matrix row order.
Generic AEXCompat work is split out only after a concrete reusable deficiency is
demonstrated, and must avoid the parallel Apple Silicon work.
