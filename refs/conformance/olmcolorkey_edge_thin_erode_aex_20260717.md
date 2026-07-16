# OLMColorKey Edge Thin Erode AEX Witness 20260717

This is a Mac-local Unicorn execution of the hash-pinned Windows PE leaf
`FUN_180008320` at `0x180008320`. It does not execute AE, Windows, NAS, PNG,
or production code. The harness now exhaustively searches all binary 5x1 and
3x3 mattes at four negative amounts.

## FACT

- AEX SHA-256 and the exact function-byte SHA-256 are recorded in the JSON.
- The harness reuses the proven 5x3 boundary seed and `distance_type=2`
  distance leaf (`FUN_180005D60`) fixtures.
- All 2,176 exhaustive calls return `RAX=0`; the PF Handle Suite shim observes
  allocation, lock, unlock, disposal, and suite release.
- The output matte is read directly from the destination payload.
- The search contains 274 cases where `dist > abs(amount)` and
  `dist > abs(amount)+1` disagree.

## INFERENCE

The exhaustive search finds zero matches for either oracle on all 274
discriminating cases. The first boundary disagreement and raw AEX result are
retained in JSON. The exact semantic reason is visible in the target leaf:
bytes `0x180008494..0x1800084A8` load a source word, multiply it by a
generated `float32`, truncate with `CVTTSS2SI`, and store the low 16 bits.
There is no distance comparison against `abs(amount)` in
`FUN_180008320`; the amount is forwarded into the distance-helper call.

The independent terminal-loop oracle models the observed raw contract: source word loads at
the leaf's `x*2` address, `MULSS` float32 rounding, `CVTTSS2SI` truncation
toward zero, low-word storage at the destination `x*4` address, and the
4-byte first-channel sampling used by the harness. Six constant-word fixtures
(`1`, `3`, `5`, `127`, `255`, `32767`) all match when the oracle is supplied
with the generated float values captured from the AEX, and discriminate
truncation from nearest rounding. This does not independently prove the
float-generation stage for all 2,176 calls. The two threshold predicates
remain caller-level erode oracles, not alternatives implemented by this leaf.

Run:

```sh
python3 tools/emulation/probe_olmcolorkey_edge_thin_erode_aex_20260717.py \
  --json refs/conformance/olmcolorkey_edge_thin_erode_aex_20260717.json
python3 tools/emulation/test_olmcolorkey_edge_thin_erode_aex_20260717.py
```
