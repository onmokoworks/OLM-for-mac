# OLMSmoother2 Current-AEX c280/cce0 Branch Proof

Date: 2026-07-16

## Verdict

`LOCAL_PRODUCTION_BOUNDARY_PROOF_WITH_HELPER_REPLAY_GAP`

This is Mac-only actual-AEX/portable-emulation evidence. It is not Windows AE
truth, live case binding, or production exactness evidence.

## FACT

- `tools/emulation/test_smoother2_fullchain_diff.py` now executes four bounded
  synthetic rows through the actual AEX c280 and cce0 entries: c=2 append,
  c=4 suppression, all-one classifier, and all-zero classifier.
- The existing producer bytes and branch conditions remain connected to the
  output-selection calls. The rows use source/class descriptors and raw scale
  words `65536/65536`; the cce0 no-gamma and Gamma Colors paths are both run.
- The c=2, c=4, and all-zero rows pass the existing actual-AEX versus portable
  boundary checks, including c280 vertices, normalization, cce0 output, and
  Gamma Colors output at the harness tolerance.
- Binary inspection of `FUN_18000ead0` showed that AEX address `0x18000eb56`
  initializes the horizontal scale to `1.0`; the port had initialized it to
  `0.5`. The production port and its boundary adapter now use `1.0`, while the
  optional cce0 chase remains the only path that reduces the scale to `0.5`.
- After that correction, all four rows match at every production boundary:
  classifier/branch selection, actual c280 entry versus production builder,
  cce0 no-gamma output, Gamma Colors output, and accumulation.
- The all-one standalone helper replay still emits one contribution while the
  actual c280 entry and production builder emit two. Only
  `c280_equiv_helpers_vs_production_builder_equal_1e-6` and the aggregate
  helper-inclusive flag remain false for this row.
- The existing producer and typed-witness tests were not changed. No Windows
  package was created and `notes/CONFORMANCE_LEDGER.md` was not edited.

## INFERENCE

- The former classifier `0x40` production mismatch was the `ead0` scale-factor
  initialization, not classifier dispatch or a global fallback.
- The remaining helper-only gap belongs to the synthetic replay harness and
  must not be used to tune production behavior.
- This local result still cannot map the synthetic row to legacy case 0004 or
  0012. Live Windows class/config bytes and a writer-bound witness remain the
  external boundary.

## Reproduction

```sh
clang++ -std=c++17 -O2 -Wall -Wextra \
  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \
  tools/emulation/smoother2_fullchain_port_adapter.cpp \
  -o /tmp/olmsmoother2_fullchain_diff_next/port_adapter
python3 tools/emulation/test_smoother2_fullchain_diff.py \
  --adapter /tmp/olmsmoother2_fullchain_diff_next/port_adapter \
  --output /tmp/olmsmoother2_fullchain_diff_next/result.json
```

The harness exits zero only when all four production boundary comparisons pass.
The classifier `0x40` row retains a separately named helper-replay gap. Its
machine-readable status is
`pass_all_production_boundaries_with_expected_helper_replay_gap`; exit zero
must not be read as Windows AE or full helper-chain equivalence.
