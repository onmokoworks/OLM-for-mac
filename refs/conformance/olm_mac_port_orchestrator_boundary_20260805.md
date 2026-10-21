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
| OLMBlur | Broad typed/legacy matrices remain internal oracle artifacts. Public Smart retains PF8 12/12 (24/744), PF16 8/8 (16/494), and PF32 20/20 (40/60) same-source exported-owner cells. The three fractional Smoothness cells reproduce the owner's signed integer-part fixed-slider materialization only inside exact admissions. Classic retains its fixed-tuple real-SDK regression. | Source `22eb712a...fdd7` / candidate `ecdf3d93...284d` are hostless and uninstalled; installed `5893faea...` remains the prior batch identity, and the next AE load/render is deferred to a multi-improvement checkpoint. |
| ColorKeep | Current installed binary is dynamically loaded; public `PF_Cmd_RENDER` connects synthetic ColorParam/iterate16 suites, PF16 worker/writer and retained actual output in one call | Adobe suite implementation and AE loaded-module/render identity; exact `ABOUT` text remains separate |
| OLMColorKey | Current source-built hostless real-SDK Classic and Smart public entries are fixed-source raw exact for 63 named cells with atomic commit and lifecycle fail-close; the installed Universal minOS 11 binary `701ae919…` remains the prior 60-cell identity | Native AE numerical mapping/render and installation of the new three-cell family are intentionally deferred to the later batched checkpoint |
| OLMDirectionalBlur | One fail-closed route connects public production `EffectMain(SMART_RENDER)`, actual-exact PF16/PF32 cores/writers and the installed signed Universal bundle | Current AE load/render |
| OLMDistanceGradation | Actual classic branches plus public Smart command `0x18` connect PF8/PF16/PF32 owners to bounded Mac output; fixed 17x11 has 24 admitted non-Power PF32 exact cells and Mode 5 non-Power 6/6 with Universal noncontracting field codegen proof | PF32 Power pending native Windows UCRT `powf`; unlisted PF32 Smart tuple/geometry/layout, project/global arbitrary fast-math, and post-change current AE load/render |
| OLMKiraKira | Production Mode4 connects both warps, recurrence, centered crop and PF8/PF16/PF32 actual-exact writers to installed identity | Live AE natural `EffectMain` owner delivery/load/render |
| OLMRadialBlur | Rotation/Zoom typed paths plus a compositional public SmartRender→RenderWorld→PF32 writer→installed identity route are exact | Dynamic AE callback ABI/load/render and remaining branch cross-product |
| OLMSmoother | Current workspace Classic admission is fixed-source and tuple/geometry bounded, with private staging and atomic commit over the retained PF8/PF16 owner cells; Smart numerical rendering remains fail-closed | The source-bound Universal candidate is installed byte-for-byte in batch4; the one post-batch4 AE attempt stopped before receipt/payload, so current native-AE load/render remains unproved |
| OLMSmoother2 | Current workspace Smart admission is fixed-source and tuple/geometry bounded across retained PF8/PF16/PF32 cells, including aligned staging for odd row strides and decoded ColorSuite-value binding; Classic remains fail-closed at every depth | The source-bound Universal candidate is installed byte-for-byte in batch4; the one post-batch4 AE attempt stopped before receipt/payload, so current native-AE load/render remains unproved |
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
