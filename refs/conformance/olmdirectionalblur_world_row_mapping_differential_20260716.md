# OLMDirectionalBlur PF world/row mapping differential

Date: 2026-07-16

## Result

`pass`, local actual-AEX/portable differential. No production Mac dispatch was
changed and no Windows package was created or sent.

## FACT

- The actual AEX entered both PF Iterate8 callbacks with the supplied world
  rectangle `[2, 1, 14, 15]`; the detoured run observed the same two callback
  rectangles.
- The host worlds were `16x16`, PF8 `A/R/G/B`, with `rowbytes=76` (`64`
  packed bytes plus `12` padding bytes). All callback reads and writes returned
  without an ABI or bounds error.
- Actual-AEX and the rowdriver-detoured run produced the identical complete
  output hash:
  `942a45b3a8eeb5da50f7badbfd6d68a4594b6af486b58be44d1d950cbf7e5ca5`.
- The existing focused gates still pass: mode-0 typed adapter, full rowdriver
  `3/3` byte equality, rowdriver contract, and the origin-zero full-render
  smoke.

## INFERENCE

- For this bounded lane, PF Iterate8 area coordinates are host-world pixel
  coordinates, while the callback's padded work-buffer offset remains
  callback-local. Row addressing uses `data + y * rowbytes + x * 4`; padding is
  not treated as image width.
- The local rowdriver candidate can be placed behind the existing actual-AEX
  detour harness without changing host-world results for this mapping case.
- This does not prove Mac AE callback/world semantics, nonzero AE layer origins,
  smart-render ROI conversion, or production integration safety. The Mac
  production bridge remains stopped pending an independent Mac host/world
  binding and the typed Windows row-755 witness.

## Reproduction

```sh
python3 tools/emulation/test_dblur_world_row_mapping_20260716.py
python3 tools/emulation/test_dblur_mode0_adapter_20260715.py
python3 tools/emulation/test_dblur_rowdriver_full_exact_20260711.py
python3 tools/emulation/test_dblur_rowdriver_contract_20260715.py
python3 tools/emulation/smoke_dblur_fullrender_detour_equivalence_20260711.py
```

Harness change: `tools/emulation/dblur_fullrender_host_fixture_20260711.py`
now accepts `--world-area` and `--row-padding`; the new differential is
`tools/emulation/test_dblur_world_row_mapping_20260716.py`.
