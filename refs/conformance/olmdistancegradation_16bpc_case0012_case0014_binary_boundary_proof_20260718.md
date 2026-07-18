# OLMDistanceGradation 16bpc target binary-boundary proof

- Date: `2026-07-18`
- Status: `PASS`
- Scope: Mac-only actual-AEX/PF16 boundary evidence for `case_0012` and `case_0014`
- AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`

## Proof

- The six-case actual-AEX PF16 threshold/half-step matrix passed with exact field raw words and exact compose/store raw bytes.
- The non-degenerate 8x5 staging differential passed with zero field-word differences, zero output differences, 40 compose calls, and preserved row padding.
- Disassembly confirms `CVTPS2DQ` float-to-int conversion and packed 16-bit store operations at the relevant binary path.

## Target Residual

The retained Mac AE layer run is `max_diff=1` for both targets: `case_0012` has 39 nonzero pixels / 95 samples, and `case_0014` has 35 nonzero pixels / 104 samples.

This proof does **not** attribute those residuals. The target evidence still lacks Windows same-run pre-store float, PF16 store word, and true16 export word. Therefore host conversion, final store, and upstream field/pre-store causes remain separable only with the requested Windows boundary capture.

## Reproduction

```sh
python3 refs/scripts/audit_olmdistancegradation_16bpc_binary_boundary_proof_20260718.py
```

The script only runs existing Mac-local emulation/differential fixtures and writes the two dated conformance artifacts. It does not build or install the plug-in, edit production source, or tune PNGs.
