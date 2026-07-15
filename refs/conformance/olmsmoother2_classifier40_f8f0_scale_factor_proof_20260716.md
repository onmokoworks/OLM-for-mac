# OLMSmoother2 classifier `0x40` f8f0 local boundary regression

Date: 2026-07-16

## Verdict

`PASS_LOCAL_CLASSIFIER_0X40_F8F0_BOUNDARY_REGRESSION`

This is a Mac-only local regression against the checked-in AEX binary using a
synthetic fixture. It is not Windows execution, live After Effects binding, or
an AE-exact production claim.

## Binary-grounded correction

- The checked-in 2025 AEX has SHA-256
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
- The AEX c280 classifier `0x40` enters `FUN_18000f8f0` at `0x18000f8f0`
  with descriptor `[5,6,3,5,6,0]`. Its inner key is `1`, selecting
  `FUN_18000ead0` at `0x18000ead0`.
- At `0x18000eb56`, AEX initializes the ead0 scale to `1.0`. The predicate-1
  fixture does not execute the optional secondary `FUN_18000cee0` chase, so the
  scale remains `1.0` through the emitter.
- The portable `win_leaf_ead0` now has the same default. Its existing optional
  chase semantics remain unchanged, including the binary-grounded `0.5`
  reductions when that chase runs.
- The global fallback and unrelated leaf helpers were not changed.

## Exact local regression

The adapter and AEX trace agree for every recorded boundary comparison:
descriptor, inner key, predicate, primary scan, secondary branch state and
values, `scale_m`, `scale_h`, trapezoid `p1`, `p2`, `p3`, and emitted weight.
The probe requires every comparison to be true and returns nonzero otherwise.

Observed local values include `scale_h=1.0`, trapezoid `p3=0.5`, and emitted
weight `0.499997079372406` on both sides within the probe tolerance.

## Commands and results

```sh
mkdir -p /tmp/olmsmoother2_classifier40_f8f0_boundary_20260716
clang++ -std=c++17 -O2 -Wall -Wextra \
  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \
  tools/emulation/smoother2_classifier40_f8f0_boundary_adapter_20260716.cpp \
  -o /tmp/olmsmoother2_classifier40_f8f0_boundary_20260716/port_adapter
```

Result: exit `0`.

```sh
python3 tools/emulation/probe_smoother2_classifier40_f8f0_boundary_20260716.py \
  --adapter /tmp/olmsmoother2_classifier40_f8f0_boundary_20260716/port_adapter \
  --output /tmp/olmsmoother2_classifier40_f8f0_boundary_20260716/result.json
```

Result: exit `0`; verdict
`PASS_LOCAL_CLASSIFIER_0X40_F8F0_BOUNDARY_REGRESSION`; all comparisons true.

```sh
python3 -m py_compile \
  tools/emulation/probe_smoother2_classifier40_f8f0_boundary_20260716.py
```

Result: exit `0`.

```sh
clang++ -std=c++17 -O2 -Wall -Wextra \
  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \
  tools/emulation/smoother2_fullchain_port_adapter.cpp \
  -o /tmp/olmsmoother2_fullchain_diff/port_adapter
python3 tools/emulation/test_smoother2_fullchain_diff.py \
  --adapter /tmp/olmsmoother2_fullchain_diff/port_adapter \
  --output /tmp/olmsmoother2_fullchain_diff/result.json
```

Result: exit `0`; the existing supported fullchain differential passes. Its
current harness still records classifier-one as an expected gap outside the
supported-row pass gate; this focused report makes no broader fullchain claim.

## Claim boundary

No Windows or After Effects process was launched. No live Windows/AE exact
claim is made, no live case mapping is made, and no global fallback change was
made.
