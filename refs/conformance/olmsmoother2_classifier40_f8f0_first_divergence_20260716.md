# OLMSmoother2 classifier `0x40` production-boundary probe

Date: 2026-07-16

## Verdict

`PASS_LOCAL_CLASSIFIER_0X40_PRODUCTION_BOUNDARY_CLOSED`

This is Mac-only evidence from local emulation of the checked-in 2025 AEX
against the existing fullchain adapter. It is binary-grounded for the local
fixture only. It is not Windows AE truth, host binding, or an AE-exact claim.

## Evidence

- The synthetic `classifier_one` neighborhood reaches classifier `0x40` in
  both paths and both c280 builders produce two vertices.
- The actual AEX c280 trace enters dispatch `FUN_18000f8f0` first, appends one
  vertex at source `(5,5)` with float32 weight `0.499997079372406`, then enters
  dispatch `FUN_18000fef0` and appends a second vertex at `(5,5)` with weight
  `0.4999988377094269`.
- The fullchain adapter's production builder emits the same two append weights
  within `1e-6`. The prior `0.24999854` observation was stale pre-`ead0` output;
  the classifier `0x40` production boundary is now closed.
- The probe has a fail-closed comparison gate: it requires classifier `0x40`,
  equal append cardinality, and every AEX append weight to compare equal to the
  production-builder weight. Missing builder data, count mismatch, or any
  unequal weight returns nonzero and cannot produce a passing verdict.
- The checked-in disassembly documents the four cardinal entry families and
  identifies `f8f0` as the beta family and `fef0` as the gamma family; the
  current port's classifier `0x40` case calls its corresponding cardinal-9
  then cardinal-6 paths.

## Scope boundary

The standalone helper replay incompleteness is tracked by the existing
fullchain differential evidence and is not reclassified by this focused
production-boundary probe. No live case mapping is established.

## Commands and results

```sh
mkdir -p /tmp/olmsmoother2_classifier40_probe_20260716
clang++ -std=c++17 -O2 -Wall -Wextra \
  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \
  tools/emulation/smoother2_fullchain_port_adapter.cpp \
  -o /tmp/olmsmoother2_classifier40_probe_20260716/port_adapter
```

Result: exit `0`; clang emitted 12 pre-existing warnings (deprecated
`sprintf`, unused variables/parameters/functions).

```sh
python3 tools/emulation/probe_smoother2_classifier40_first_divergence_20260716.py \
  --adapter /tmp/olmsmoother2_classifier40_probe_20260716/port_adapter \
  --output /tmp/olmsmoother2_classifier40_probe_20260716/result.json
```

Result: exit `0`; verdict
`PASS_LOCAL_CLASSIFIER_0X40_PRODUCTION_BOUNDARY_CLOSED`. The fail-closed
comparison gate reports classifier equality, append-count equality, and
append-weight equality at `1e-6`.

The machine-readable trace is in the temporary output path above and records
the two dispatch/append pairs and both portable c280 vertices.

```sh
python3 tools/emulation/test_smoother2_fullchain_diff.py \
  --adapter /tmp/olmsmoother2_classifier40_probe_20260716/port_adapter \
  --output /tmp/olmsmoother2_classifier40_probe_20260716/fullchain_result.json
```

Result: exit `0`; the existing fullchain adapter reports
`pass_all_production_boundaries_with_expected_helper_replay_gap`. The
standalone helper replay incompleteness remains tracked there.

## Claim boundary

No Windows execution, Windows package, NAS archive, production source change,
ledger change, or AE-exact claim is made.
