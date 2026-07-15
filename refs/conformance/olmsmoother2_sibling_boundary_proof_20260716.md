# OLMSmoother2 sibling-scale boundary proof

Date: 2026-07-16

## Verdict

`PASS_LOCAL_AEX_PORTABLE_SIBLING_BOUNDARIES`

This is local execution of the checked-in OLMSmoother2 AEX against the
portable Mac boundary. It is not a Windows execution, host binding, or
After Effects exactness claim.

## Scope

The proof drives actual AEX leaves `FUN_18000e4b0`, `FUN_18000edb0`, and
`FUN_18000e7c0`, and compares each with the production helper for:

- descriptor and predicate result;
- primary scanner result;
- optional chase branch and secondary scanner result;
- emitter `scale_h` and emitted weight.

Each leaf has a predicate-1 no-chase row and a predicate-3 chase row. The
no-chase rows observe the initializer directly at the emitter. The chase rows
confirm that the existing reductions to `0.5` remain unchanged.

The no-chase AEX scale is `1.0` for all three leaves. Before the production
edit, each portable no-chase emitted weight was half the AEX weight. After
changing only the three local initializers from `K_HALF` to `K_ONE`, all six
rows pass at `1e-6`.

## Production change

Changed only `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`:

- `win_leaf_e4b0`: `wsh = K_ONE`;
- `win_leaf_edb0`: `wsh = K_ONE`;
- `win_leaf_e7c0`: `wsh = K_ONE`.

The loop assignments and chase-to-half behavior were preserved.

## Verification

```sh
clang++ -std=c++17 -O2 -Wall -Wextra \
  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \
  tools/emulation/smoother2_sibling_boundary_adapter_20260716.cpp \
  -o /tmp/olmsmoother2_sibling_20260716/adapter
python3 tools/emulation/probe_smoother2_sibling_boundary_20260716.py \
  --adapter /tmp/olmsmoother2_sibling_20260716/adapter \
  --output refs/conformance/olmsmoother2_sibling_boundary_proof_20260716.json
```

Result: exit `0`; six of six AEX/portable rows pass.

```sh
python3 tools/emulation/test_smoother2_producer.py
python3 tools/emulation/test_smoother2_fullchain_diff.py \
  --adapter /tmp/olmsmoother2_fullchain_diff/port_adapter \
  --output /tmp/olmsmoother2_sibling_20260716/fullchain.json
python3 tools/emulation/test_smoother2_typed_witness.py \
  --output-json /tmp/olmsmoother2_sibling_20260716/typed.json \
  --output-md /tmp/olmsmoother2_sibling_20260716/typed.md
```

Results: producer exit `0`, fullchain exit `0`, typed witness exit `0`.

The repository smoke wrapper `refs/scripts/smoke_smoother2_fullchain_diff.py`
still exits `1` because its legacy assertions include the documented
`classifier_one` standalone helper-replay gap; the direct fullchain runner
passes its production-boundary gate.

```sh
xcodebuild -project mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj \
  -scheme OLMSmoother2 -configuration Debug -sdk macosx \
  ARCHS=arm64 ONLY_ACTIVE_ARCH=NO CODE_SIGNING_ALLOWED=NO build
```

Result: `** BUILD SUCCEEDED **` for arm64.

## Claim boundary

No Windows/AE-exact claim is made. Synthetic local fixtures do not establish
live case mapping or final host packing.
