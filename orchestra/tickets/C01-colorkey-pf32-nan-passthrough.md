# C01: ColorKey PF32 with a NaN source pixel: Mac passes the NaN through, the original computes a value

## Witness (N01 smoke, `orchestra/reports/N01-nightly-fuzz-runner.md`)
- `orchestra/reports/N01-evidence/witnesses/c2d799e6b17314d055e78508.json`: default sampler, seed 812324792801853187, index 2081, reduced to 1x8 PF32. At word 25, the original gives `b7b6b63e` (≈0.357) and Mac gives `4523c17f`, which is the input's qNaN payload 0x7fc12345 passed through. 3 words differ. Two more default-sampler mismatches in that run share the signature.

## Do
- Replay the witness. From disassembly (`decomp/OLMColorKey.aex.c.txt` and P03b's notes on NaN comparison and CVTTSS2SI semantics), find what the original does with a NaN channel on this path: which comparison or min/max lets a finite value out, and where Mac keeps the NaN. Implement exactly that in the general path. Keep the R10 reference/fast split.
- Acceptance:
  - the witness and its two siblings are exact;
  - a PF32-nonfinite-heavy campaign (default + realistic-v1, 3 seeds, n100) has 0 mismatches;
  - default fuzz seed 1 n300 has no exact→non-exact;
  - all ColorKey corpora replay true;
  - `tools/perf/ref_vs_fast.py --plugin olmcolorkey` is clean.
- Add the witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Change only ColorKey sources. Do not touch the release gate or ledger. The stop rule applies.
