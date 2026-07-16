# OLMBlur case_0004 coefficient sensitivity A/B

## FACT

- Captured radius sequence: `[125, 36, 10, 2]`.
- Complete-set coefficient discriminators: `[{'iteration': 1, 'index': 57, 'index_base': 0, 'a_word': '0x3ecaa909', 'b_word': '0x3ecaa908', 'unsigned_word_delta': -1}, {'iteration': 1, 'index': 70, 'index_base': 0, 'a_word': '0x3e7d158f', 'b_word': '0x3e7d158e', 'unsigned_word_delta': -1}]`.
- Set A: declared host-callback coefficient set; not Windows truth.
- Set B: current Mac production-generated coefficient set; not Windows truth.
- Both use identical staged RGB/flags, radii, pass order, crop geometry, and portable helper implementation across `16` stages.

## Witnesses

- `(411,258)`: pre-store A `['0x46ac2b00', '0x00000000', '0x00000000']`, B `['0x46ac2aff', '0x00000000', '0x00000000']`, exact `False`; predicted RGB words A `[22038, 0, 0]`, B `[22037, 0, 0]`, exact `False`.
- `(458,314)`: pre-store A `['0x46ce0b00', '0x00000000', '0x00000000']`, B `['0x46ce0aff', '0x00000000', '0x00000000']`, exact `False`; predicted RGB words A `[26374, 0, 0]`, B `[26373, 0, 0]`, exact `False`.

## Conclusion

- The complete coefficient-set change alters either final pre-store result: `True`.
- The complete coefficient-set change alters either standard-writer predicted word: `True`.
- Supplemental index-57-only isolation changes either pre-store result: `True`.
- Supplemental index-57-only isolation changes either predicted word: `True`.
- The index-57 isolation is portable synthetic sensitivity evidence only; authentic set B also differs at iteration 1/index 70.
- Writer values are arithmetic predictions only, not actual-AEX writer observations.
- Neither coefficient set is Windows truth; no Windows, NAS, or SSH execution was used.

## Test

```text
python3 tools/emulation/test_olmblur_case0004_coefficient_sensitivity_20260716.py
```

## Changed files

- `tools/emulation/probe_olmblur_case0004_coefficient_sensitivity.py` (new)
- `tools/emulation/test_olmblur_case0004_coefficient_sensitivity_20260716.py` (new)
- `refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.json` (new)
- `refs/conformance/olmblur_case0004_coefficient_sensitivity_20260716.md` (new)
