# OLMDirectionalBlur writer boundary localization

- Status: `pass`
- Scope: Front Alpha Fade, same-run Windows PF output and accepted PNG pair.

## FACT

- The actual-AEX rowdriver destination, denominator, alpha, and normalization remain exact against the portable bounded replay.
- The actual-AEX output-writer slice differs from the same-run Windows PF output at 226 packed 32-bit words (468 channel values) across 226 pixels.
- The accepted same-run Windows PF output converts to the returned PNG with zero differing values under the recorded host formula.
- The Windows return contains no typed pre-writer float buffer or writer-entry capture for this case.

## INFERENCE

- PNG/export is not the source of the 226-value writer_vs_windows boundary residual.
- The residual is localized to the plug-in output side at or before PF byte storage, but cannot be assigned uniquely to writer input versus the store without a Windows typed writer-entry witness.
- No production change is justified and no AE-exact status is promoted.

## Boundary result

- Writer-vs-Windows PF slice: `226 packed words / 468 channel values / 226 pixels`.
- Windows PF-to-PNG export: `0 values / 0 pixels`.
- Localized conclusion: export is ruled out; writer input versus store remains unresolved.

Reproduction: `python3 tools/emulation/test_dblur_writer_boundary_localization_20260716.py`
