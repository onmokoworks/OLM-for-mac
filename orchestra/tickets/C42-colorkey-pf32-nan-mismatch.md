# C42: ColorKey PF32 Smart mismatches (NaN payload/sign) on seed 46

## Facts (F46 report)
Fresh seed46 shows three ColorKey PF32 Smart mismatches, unchanged across F45/F46:
- case237: 3 words; Mac `00000000` vs ref `4523c17f`, little-endian, i.e. a NaN with a payload
- case246: 5 words; Mac `0000c07f` vs ref `0000c0ff`, i.e. default-NaN sign: x86 `ffc00000` vs arm64 `7fc00000`
- case275

F38 solved the same class for OLMBlur with `core/x86_float.h` (x86 generated-NaN sign). F29 fixed
the oracle's operand-order NaN propagation.

## Do
1. Reproduce the three cases and add them to `tests/fuzz_corpus/olmcolorkey` as witnesses.
2. Find where ColorKey generates or propagates NaNs on the Smart PF32 path: SSE arithmetic,
   min/max, conversions, and copies that may canonicalise. Apply the F38 helpers or equivalent
   general x86 semantics there. For case237, find out why Mac produces 0 where the original
   propagates the NaN payload; for example a comparison/select that drops NaN.
3. If that is not resolved after two refuted hypotheses, narrow the PF32 nonfinite Smart admission
   so those inputs are refused. This fallback is mandatory.
4. Verify with seeds 1, 46 and one fresh seed, n300: 0 Smart mismatches and no exact case lost.
   Replay the corpus.
- Use 1-2 processes. Do not touch the release gate/ledger.
