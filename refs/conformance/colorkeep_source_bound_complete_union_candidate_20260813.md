# ColorKeep source-bound complete-union candidate — 2026-08-13

Status: `PASS_COLORKEEP_SOURCE_BOUND_COMPLETE_UNION_CANDIDATE`

The frozen Universal candidate reproduces all ten legacy count5/100 public paths and all five count9 public paths on both arm64 and Rosetta x86_64. The legacy source predicate accepts six exact typed sources and rejects first/middle/last active-byte mutations (18 controls). Count9 retains 136 precommit-atomic rejects per slice. Both slices require macOS 11.0 and export EffectMain/PluginDataEntryFunction2; the bundle has a strict-valid ad-hoc signature.

Boundary: AE-free current-workspace evidence for the exact source-bound ColorKeep public union only: legacy 11x7 count5/100 and count9 4x3. No arbitrary source, palette, geometry, native AE, installation, Developer ID, or notarization claim.
