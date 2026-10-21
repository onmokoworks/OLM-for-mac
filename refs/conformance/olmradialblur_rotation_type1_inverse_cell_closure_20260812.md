# OLM RadialBlur Rotation Type-1 inverse-cell closure — 2026-08-12

Status: **98/98 bounded cells exact after inverse-cell integration**.

The fixed 32×18 Rotation Type-1 source-scalar seam is closed for exactly five
existing admission flags: pairwise (8 cells), dual strength (18), edge/noise
(24), size+edge+noise (12), and size+noise/brightness (36).  The common sampler
uses a float inverse-cell multiply, matching the pinned Windows AEX arithmetic.
Fresh read-only direct-owner integration runs pin every required available plane
across all 98 cells.  Pairwise, dual-strength, and size/noise do not make a
98-wide prepass claim; edge families additionally captured exact prepass alpha.
The size/noise family alone compared 55,214,784 bytes with zero differences.
PF8 source span was captured explicitly at owner work `+0x90`.
Older reports remain contextual evidence; source-scalar exactness is not inferred
from their stale inactive-only classification.

The Windows evidence is direct internal-owner execution under the repository's
x86_64 emulation fixture, not a natural exported public AEX call.  The Mac
numerical evidence likewise reuses direct typed-owner fixtures; the natural
classic `EffectMain` public admission is bounded by the same five flags, but this
document does not relabel all 98 rows as fresh natural-owner executions.

Type 2 stays on its prior block sampler and Type 3 Rotation remains fail-closed.
Fresh Type2 actual controls are exact and all nine Type3 Rotation controls reject
before iteration.  Strength 290 is excluded: its post-fix direct-owner replay is
zero-diff on all named planes, while public `EffectMain` still rejects it.  No
install, native AE render, arbitrary geometry, or general-strength claim is made.

An isolated Debug `xcodebuild` also completed for `arm64` and `x86_64`; the
Universal binary and both slices are hash-bound in the JSON, and `EffectMain`
and `PluginData` were exported.  The durable bundle is strict/deep-valid ad-hoc
signed.  It is not Developer ID/notarized, installed, or AE-load evidence.

This closure supersedes the older “inactive/unreferenced source-scalar only”
wording in the listed 2026-08-11 reports.  Some differing cells were consumable;
they happened not to cross the fixed small-strength integer-span boundary.
