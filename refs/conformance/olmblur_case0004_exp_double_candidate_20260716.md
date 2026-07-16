# OLMBlur case_0004 double-exp candidate gate

## FACT

- Classification: `coefficient_exact`.
- Platform: `Darwin arm64`; compiler `Apple clang version 17.0.0 (clang-1700.6.4.2)`.
- Raw coefficient words exact: `True` (`177/177` compared).
- First mismatch: `None`.
- Radius sequence: `[125, 36, 10, 2]`.
- Candidate keeps current powf/pow/radius/sigma/denom order and replaces only expf(x_f32) with `static_cast<float>(std::exp(static_cast<double>(x_f32)))`.

## Full Cone

- `(411,258)`: pre-store `['0x46ac2b00', '0x00000000', '0x00000000']`; predicted RGB words `[22038, 0, 0]`.
- `(458,314)`: pre-store `['0x46ce0b00', '0x00000000', '0x00000000']`; predicted RGB words `[26374, 0, 0]`.

## INFERENCE

- Production source `mac/OLMBlur/OLMBlur.cpp` is pinned to `55def455a29f72c04748a784bcd598ddeecb84ec25d475376ea93b6e838e3b02` and contains the candidate exactly once.
- The production source is integrated and builds for arm64/x86_64; Mac AE output remains unvalidated.
- The cone replay is portable-only, and neither coefficients nor outputs are labeled Windows truth.

## Test

```text
python3 tools/emulation/test_olmblur_case0004_exp_double_candidate_20260716.py
```

## Changed files

- `tools/emulation/probe_olmblur_case0004_exp_double_candidate.cpp` (new)
- `tools/emulation/test_olmblur_case0004_exp_double_candidate_20260716.py` (new)
- `refs/conformance/olmblur_case0004_exp_double_candidate_20260716.json` (new)
- `refs/conformance/olmblur_case0004_exp_double_candidate_20260716.md` (new)
