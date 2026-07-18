# OLMBlur PF32 local provenance/package audit

Date: 2026-07-18

## Verdict

No remaining **local-only** flaw was found in either:

- the narrow `case_0001` repeat=`1` 32bpc provenance request/package, or
- the checked-in Mac-side PF32 implementation proof boundary.

The source must stay frozen. The only live blocker is still external:
Windows loaded-AEX provenance and returned same-run evidence are not yet
closed.

## Request/package result

- Request: `refs/reference_requests/olmblur_32bpc_case0001_repeat1_provenance_20260718.json`
  SHA-256 `955007d248052b1dc2dfa809c998932a44797808f382da0a4c6efc35dde488ae`
- Package: `refs/reference_requests/olmblur_32bpc_case0001_repeat1_provenance_request_20260718.zip`
  SHA-256 `bcffe8ae5c77c061fd31a614f877135abd247fb45cd0d1214d30fd140602a446`
- The package smoke remained deterministic, required one same-AE-process
  effect/control pair, required loaded AEX path plus SHA-256, rejected partial
  answers, and contained no leaked workspace-absolute paths.

## PF32 local proof result

- `python3 tools/emulation/test_olmblur_32bpc_source_aex_adapter_20260717.py`
  passed `12/12` checked-in actual-AEX float fixtures with zero byte, alpha, or
  padding mismatches.
- `python3 tools/emulation/test_olmblur_case0003_0004_readiness_audit_20260717.py`
  passed its local schedule/coefficient/rounding cross-check and preserved the
  open worker/helper pre-store boundary classification.
- `python3 tools/emulation/audit_olmblur_unresolved_20260718.py` still classifies
  the 32bpc lane as **not AE exact** while Windows loaded-module provenance is
  missing.

## Reproduction

```text
python3 refs/scripts/smoke_package_olmblur_32bpc_case0001_repeat1_provenance_request_20260718.py
python3 tools/emulation/audit_olmblur_unresolved_20260718.py
python3 tools/emulation/test_olmblur_32bpc_source_aex_adapter_20260717.py
python3 tools/emulation/test_olmblur_case0003_0004_readiness_audit_20260717.py
python3 refs/scripts/smoke_audit_olmblur_pf32_local_provenance_package_20260718.py
```

## Conclusion

There is no binary-local basis for a production PF32 algorithm change on
2026-07-18. Keep the implementation frozen until a Windows same-run return
binds the retained EXR evidence to the loaded `OLMBlur.aex` module and the
declared AE/output environment.
