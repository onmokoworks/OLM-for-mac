# OLMSmoother2 case0012 live-config package audit

Date: 2026-07-15

## Scope

One current-AEX Windows Software witness at `(91,841)`, descriptor
`[91,841,1,91,843,5]`, case
`legacy_case_0012_gamma5_red_blue_current_aex`. No Mac Smoother source was
changed. `notes/CONFORMANCE_LEDGER.md` was not changed.

## FACT

- The sendable witness spec now requires the three four-byte class-plane
  samples, `e170.c`, and the two append observations from the same run.
- The c280 event now requires its bound pointer identity, raw eight-byte
  scale span at `+0x20/+0x24`, and decoded `scale_fixed` values.
- The cce0 event now requires its bound pointer identity, raw seven-byte gamma
  context from `+0x00` through mode byte `+0x06`, and decoded `mode_byte`.
- The final writer remains required as corroboration, but its pixel values are
  shape-validated rather than hard-coded to a guessed result.
- Fixture-based smoke cases reject missing class bytes, c280 scale data, cce0
  gamma data/mode, pointer identity, append, writer corroboration, duplicate
  events, and witness identity drift.
- The regenerated package is deterministic and the local fixture classifier
  passes fail-closed verification.

## INFERENCE

- A complete returned trace with these fields would be sufficient to bind one
  live config/class-plane witness for the requested audit, subject to normal
  Windows capture provenance and the package's AEX hash pin.
- The repository does not contain a fresh complete Windows return proving
  `Windows AE vs Mac AE max_diff=0`; the local classifier and emulation remain
  intermediate evidence only.

## Promotion boundary

Do not promote local replay values such as `scale_fixed=[65536,65536]` or
`mode_byte=0` into Windows expectations. The package requests raw live bytes
and decoded fields from one run, plus append and writer corroboration; it does
not request only final writer bytes.

## Verification

```text
python3 refs/scripts/smoke_windows_witness_olmsmoother2_case0012_20260713.py
```

Result: `PASS`.
