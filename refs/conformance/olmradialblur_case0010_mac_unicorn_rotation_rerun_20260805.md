# OLMRadialBlur case0010 Mac-Unicorn Rotation rerun (2026-08-05)

Status: `actual_aex_internal_exact_reference_path_split`

The retained full case0010 M4 harness executed the pinned 2025 AEX entirely
on Mac through Unicorn:

`FUN_180008690 -> FUN_180007520 -> FUN_180004640`

- Input geometry: `1920x1080`
- Angular columns: `1800`
- Wall time: `922.85s`
- Reader calls: `21`
- Four retained Windows typed polar witnesses: two bit-exact, two one RGB ULP;
  alpha exact for all four
- AEX direct inverse sample at output `(1614,6)`: approximately
  `(-0.004081939, -0.004081939, -0.004081939, 1.0)`, quantized RGB black
- AEX-emulated output witness: ARGB `(0,0,0,0)`
- The legacy 20260604 Windows PNG witness is white

This independently reproduces the AEX internal Rotation cells on Mac, but it
also proves that the legacy white PNG witness cannot be used to authorize a
Mac production change. Its rendering path, AEX identity, GPU/CPU selection,
or manifest provenance differs from the pinned actual-AEX Software model.

No production code was changed. The next admissible Rotation gate is a fresh
same-run Windows CPU/AEX-bound output or equivalent writeback witness. The
complete rerun output is retained in `tools/emulation/M4_REPORT.md`.

Verification:

```sh
python3 tools/emulation/test_m4_case0010.py
```
