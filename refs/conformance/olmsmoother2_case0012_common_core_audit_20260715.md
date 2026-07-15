# OLMSmoother2 case_0012 Common-Core Audit

Date: 2026-07-15

Scope: `OLMSmoother2` case_0012 common-core witness, its dedicated package smoke, and the independent audit test. Shared ledger and queue files were not changed.

## FACT

- The CCE0 `.printf` has 9 conversions and 9 arguments: one pointer, seven byte reads at `+0x00` through `+0x06`, and one mode-byte read at `+0x06`.
- The C280 `.printf` has 12 conversions and 12 arguments: two pointers, eight byte reads at `+0x20` through `+0x27`, and two DWORD scale reads.
- The C280 breakpoint condition requires `poi(@rsp+0x28)==@$t6`, where `@$t6` is captured from CCE0's `poi(@rsp+0x28)`.
- The validator accepts the complete fixture with the seven-byte CCE0 payload and rejects a drifted C280 current pointer.
- When the required export is absent, `bundle_return` writes a ZIP containing only `RETURN_OLMSMOOTHER2_CASE0012.json`; that manifest reports `exact_bind_failure` at `artifact_collection` and has no artifacts.

## INFERENCE

- The requested CDB arity, seven-byte configuration capture, CCE0-to-C280 pointer provenance, and generated-ZIP fail-closed semantics are covered by executable checks in this audit.
- These checks establish local witness/package behavior only. They do not establish Windows render equivalence or AE exactness.

## Verification

```text
python3 tools/emulation/test_smoother2_case0012_common_core_audit.py -q
python3 refs/scripts/smoke_windows_witness_olmsmoother2_case0012_20260713.py
```
