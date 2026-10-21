# ColorKeep source-bound complete-union install — 2026-08-13

Status: `PASS_COLORKEEP_SOURCE_BOUND_COMPLETE_UNION_INSTALLED_AE_FREE`

The candidate and installed bundle inventories are exact at binary `dae59a6…`; three durable old-bundle copies retain `fcd501…`. The retained install-time manifests prove that only the ColorKeep row and two top-level timestamps changed in that transaction. The current accepted manifest still retains that exact ColorKeep row while allowing later transactions for other plug-ins. The installed arm64 and Rosetta x86_64 slices replay all 10 legacy and all 5 count9 paths; count9 retains 136 atomic rejects per slice. Two all-ten preflights report the expected `ae_not_running` state with all identities, Universal slices, and signatures exact.

Boundary: ColorKeep-only hostless historical install transition, current accepted ColorKeep-row identity, and complete bounded public replay. Later changes to other accepted identity rows are outside this transaction. No AE launch/load/render, Developer ID, notarization, or arbitrary source/tuple claim.
