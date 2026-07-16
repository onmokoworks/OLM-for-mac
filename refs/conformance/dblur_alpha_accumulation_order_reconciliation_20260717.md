# DirectionalBlur alpha accumulation-order reconciliation

## FACT

- `core/dblur_rotate.cpp` is unchanged from its original alpha sequence:
  `top-right -> top-left -> bottom-left -> bottom-right`.
- The original six actual-AEX fixtures pass byte-for-byte. No fixture expected
  file was changed.
- The deterministic `6x6`, angle `0.37` stress vector places alpha values
  `TL=0.1`, `BL=0.2`, `TR=0.3`, and `BR=0.4` at source coordinates
  `(3,1)`, `(3,2)`, `(4,1)`, and `(4,2)`.
- At output `(3,1)`, the rotate address calculation gives `ix=3`, `iy=1`.
  Therefore the four reads are `top+3`, `bottom+3`, `top+7`, and `bottom+7`
  in TL/BL/TR/BR semantic order.
- Float32 accumulation gives `0x3e843044` for
  `TR+TL+BL+BR`, and `0x3e843043` for `BL+TL+TR+BR`.
- The actual AEX returns `0x3e843044`; the restored portable candidate returns
  the same bit. The diagnostic is now part of
  `tools/emulation/test_dblur_rotate_exact.py` and does not materialize a
  fixture.
- Applying `BL+TL+TR+BR` made the existing AEX fixture fail at
  `alpha_boundary`, byte `256`: got `0x4b`, expected `0x4e`.

## INFERENCE

The requested `BL+TL+TR+BR` sequence is not established as the accumulation
order of the checked-in actual AEX helper. The corner/address mapping is
consistent with both the source layout and the observed AEX result. The root
cause of the failed correction is therefore an incorrect attribution of the
proposed order to this AEX path, not a corner-address mapping error.

## Verification

```text
python3 tools/emulation/test_dblur_rotate_exact.py
[OK] 6 actual-AEX rotate fixtures match byte-for-byte

python3 tools/emulation/smoke_dblur_rotate_exact.py
[OK] dblur rotate exact replay is byte-exact
```

No production change is accepted pending independent evidence that a different
AEX order is active for this helper and can pass the unchanged fixtures.
