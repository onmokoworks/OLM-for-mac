# OLMKiraKira Mode 3 live Gaussian acceptance audit

Date: 2026-07-15

## Scope

This note covers only the Mode 3 live-Gaussian package generator, Windows
PowerShell runner, classifier, and fixture smoke tests. `notes/CONFORMANCE_LEDGER.md`
was not edited.

## FACT

- The v5 runner launches both the minimal preflight and full JSX with one
  explicitly quoted `Start-Process -ArgumentList` string:
  `-m -r "<absolute-no-space-jsx-path>"`.
- The runner relays through Windows PowerShell 5.1 unless explicitly bypassed,
  verifies the pinned OLMKiraKira AEX SHA-256 and size, and binds breakpoints
  from the live module base plus fixed RVAs.
- The runner now fails closed if `[BitConverter]::IsLittleEndian` is false.
- A successful return requires exactly 84 bytes, decodes 21 words with
  `BitConverter`, and records `float32`, `little`, the raw encoding declaration,
  and a SHA-256 of the captured coefficient bytes.
- The classifier recomputes that SHA-256 from the reported words using an
  explicit little-endian 21-`uint32` packing and rejects metadata, byte-order,
  or byte-hash mismatches before model classification.
- The classifier now requires every required trace marker line to carry the
  returned `run_id`, and requires `KK_RUN_START` to carry the expected case ID;
  a marker name alone cannot satisfy same-run provenance.
- `python3 refs/scripts/smoke_package_olmkirakira_mode3_live_gaussian_20260713.py`
  passed.
- `python3 refs/scripts/smoke_classify_olmkirakira_mode3_live_gaussian_return.py`
  passed, including rejection fixtures for wrong byte order, wrong
  coefficient-byte hash, missing marker run identity, and wrong run-start case.
- No Windows AE coefficient return was accepted by this audit.

## INFERENCE

- The package is structurally ready to accept a hash-pinned, same-run,
  little-endian 21-word live return, but this audit does not prove that the
  Windows desktop capture succeeds.
- CLI/emulation or Unicorn output remains intermediate evidence and is not a
  production Gaussian/luma/gain tuning basis.
- Windows AE Software versus Mac AE `max_diff=0` remains unestablished; this
  package audit cannot promote compatibility to that final criterion.

## Artifact

The regenerated sendable artifact is
`refs/runtime_trace_packages/olm_runtime_trace_olmkirakira_mode3_live_gaussian_20260713.zip`.
