# OLMDirectionalBlur Mode-0 Local Adapter Boundary

## Fact

- The checked-in actual-AEX rowdriver gate remains byte-exact for all three
  fixtures (`3/3`, no tolerance).
- A new local typed harness executes source-plane staging, rotation,
  component-map setup, prepass/scatter, denominator and alpha-max accumulation,
  RGB normalization, inverse rotation, and final RGBA quantization through the
  portable core.
- The focused rowdriver contract still confirms exclusive row-end semantics,
  width stride, denominator addition, and max-alpha accumulation.
- No Mac plug-in production dispatch or source path changed.

## Boundary

This is local binary/portable plane evidence. It does not prove the Mac AE
host/world adapter, full-frame angle mapping, Alpha Fade, Size Variation,
Sharp Tail, Back, Noise, diagonal behavior, or AE exactness. A proposed
compile-gated production adapter was rejected because host/world semantics are
not yet independently bound.

## Verification

- `python3 tools/emulation/test_dblur_mode0_adapter_20260715.py`
- `python3 tools/emulation/test_dblur_rowdriver_full_exact_20260711.py`
- `python3 tools/emulation/test_dblur_rowdriver_contract_20260715.py`

All three commands pass. Production integration remains behind the Windows
row755 typed witness and a Mac host/world binding proof.
