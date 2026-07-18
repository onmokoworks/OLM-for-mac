# OLMBlur unresolved exactness audit

Date: 2026-07-18

Scope: Mac-only, read-only audit. It does not edit the plugin, ledger, AE
state, or Windows data.

## Finding

The highest-value local action is to rerun the bounded 32bpc source/AEX
adapter and the case 0003/0004 readiness audit, then freeze the source while
loaded-Windows-AEX provenance is missing.

The current source contains the PF8 legacy, PF16 legacy/non-legacy, and PF32
legacy/non-legacy dispatch symbols, and preserves source alpha in the adapter.
The retained 16bpc Mac AE slice is 7/7 exact. The retained 32bpc result is
12/12 byte-exact against checked-in actual-AEX fixtures, but it is not
cross-host AE exact: the Windows EXR set lacks the loaded AEX hash and module
binding. Case 0003/0004 also remain open at the worker/helper pre-store
boundary.

## Commands

```text
python3 tools/emulation/audit_olmblur_unresolved_20260718.py
python3 tools/emulation/test_olmblur_32bpc_source_aex_adapter_20260717.py
python3 tools/emulation/test_olmblur_case0003_0004_readiness_audit_20260717.py
```

Machine-readable output: `olmblur_unresolved_exactness_20260718.json`.

This audit does not request or fabricate the missing Windows loaded-module
artifact and does not promote 32bpc AE exactness.
