Facts:
- F30's committed `mac-call-sites.txt` and `aex-float-imports.json` identify the requested original float import set. `call-sites.txt` records the resulting production calls, each explicitly using `UCRT_FMA`.
- Additional DirectionalBlur boundaries: original `OLMDirectionalBlur.aex.asm.txt` calls thunk `0x18000a67c` (`powf`) at `0x1800037cf`, `0x1800039b6`, and `0x180003a5b`. The first passes the fractional noise-table position in XMM0 and XMM11 in XMM1. XMM11 is loaded at `0x180003733` from `0x18000b218`; reading the original PE RVA `0xb218` gives bytes `00000040` (float 2). The other two pass FLOAT32 `comp_map / scale` and exponent. Accordingly `core/dblur_noise.h` and `core/dblur_rowdriver.cpp` now call `ucrt_powf`, replacing double-pow casts.
- KiraKira's finite-seed admission guard now evaluates the same UCRT float power as its recovered constructor.

Unchanged / excluded:
- Blur's double repeat-index `std::pow(double(decay), double(repeat))`; the original contains a separate double `pow` thunk (`0x18000ccba`) as well as `powf` (`0x18000ccc0`).
- `core/kirakira_gaussian.h` and DistanceGradation's double Gaussian exp paths.
- RadialBlur's genuine double geometric atan2 and double sin/cos operations.
- KiraKira's unrecovered legacy fallback double overloads. Their conversion to a float boundary is not established by this ticket; only the recovered FLOAT32 constructor/fade operations were changed.
- Smoother2's float pow grep hits in both source copies: F30's original import inventory contains none of these three float imports for Smoother2, so they remain unchanged.

Inference:
The additional DirectionalBlur scalar operands and imported thunk identify the float boundaries independently of the old C++ overloads. This is not a claim that other double/UCRT imports or native AE behavior have been qualified.
