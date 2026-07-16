# OLMBlur case0003/0004 readiness audit (2026-07-17)

## Result

- Local cross-check: **PASS** against the pinned actual-AEX evidence.
- Claim boundary: local actual-AEX fixture and portable evidence only; no AE exact claim.
- case0003 schedule: 120 calls, ten exact `H x 6, V x 6` iterations, with H offsets `0..450` by 90 and V offsets `0..800` by 160.
- case0004 schedule: four exact radius stages `[125, 36, 10, 2]`, one H and one V call per stage; retained helper microfixtures are exact.
- Coefficients: case0004 double-exp candidate `177/177`; case0003 Legacy candidate `4970/4970` with zero candidate mismatches.
- Rounding: actual-AEX writer evidence retains the add-0.5/truncate half-tie behavior; no rounding change is justified.

## Open boundary

The locally testable schedule/coefficient/rounding conditions are covered. The remaining blocker is the worker/helper pre-store boundary: case0003 is full-frame dependent and case0004 does not reach the radius-125 helper within the established cap. This report does not promote either case to AE exact.

## Reproduction

`python3 tools/emulation/test_olmblur_case0003_0004_readiness_audit_20260717.py`
