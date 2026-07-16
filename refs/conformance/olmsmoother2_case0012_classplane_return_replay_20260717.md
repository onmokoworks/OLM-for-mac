# OLMSmoother2 case0012 class-plane return replay

## Verdict

`BLOCKED_CASE0012_LIVE_CLASSPLANE_NOT_RECOVERABLE_LOCALLY`

The three Windows return ZIPs do not contain the missing live neighbor class bytes. The corrected and reentrant returns retain only center, previous-row, and left pixels. Their process addresses are not backed by a memory dump in any archive.

## Fail-Closed Intake

- All three ZIP hashes, member paths, required members, JSON schema, and trace token structure were validated.
- The initial return is superseded because its hard-coded sample disagrees with the corrected live-RDX return.
- The reentrant return remains `exact_bind_failure`; its render result is invalid and its c280 event says `index_inputs_proven=false`.
- No archive contains a class-plane binary, raw dump, or structured neighborhood artifact.

## Reconstruction Test

The older 5x5 log conflicts with corrected live bytes at 2 of the three retained coordinates: 92,841, 92,840. It therefore cannot be spliced into the corrected run as host state.

Two local completions preserve the corrected descriptor and all three retained pixels. Extracted `FUN_18000e170` returns `7` for the retained inputs in both cases. Actual AEX and the portable implementation agree per completion, but c280 returns count `0` for the zero completion and count `3` for the one completion. Thus the captured evidence admits different downstream polygons.

## Conclusion

The missing live neighbor bytes cannot be extracted from these ZIPs or uniquely reconstructed from checked-in classplane/descriptor evidence. A same-run neighborhood memory capture is still required.

## Reproduction

```sh
tmp=$(mktemp -d)
clang++ -std=c++17 -O2 -I cli/OLMSmoother2/shim -I mac/OLMSmoother2 \
  tools/emulation/smoother2_case0012_classplane_replay_adapter_20260717.cpp -o "$tmp/adapter"
python3 tools/emulation/test_olmsmoother2_case0012_classplane_return_replay_20260717.py \
  --adapter "$tmp/adapter" \
  --output-json refs/conformance/olmsmoother2_case0012_classplane_return_replay_20260717.json \
  --output-md refs/conformance/olmsmoother2_case0012_classplane_return_replay_20260717.md
test $? -eq 2
```

## Claims Not Made

- No Windows replay or recovered Windows class plane.
- No After Effects host correctness claim.
- No AE exact claim.
- No production change and no ledger change.
