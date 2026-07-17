# OLMKiraKira packed-size argument lineage

Date: 2026-07-17

## Result

- Status: **PASS_CLASSIFIED_FAIL_CLOSED_STOP**
- Classification: **B**
- Basis: The caller constructs the packed R9 value in checked-in AEX arithmetic and the callee ABI spill/load preserves it.
- Reader: `0x181280e92 MOV R9,qword ptr [RSP + 0x1f8]`.
- The caller constructs `R9 = RSI | 0x100000000` at `0x18115110a..0x18115116f`.
- The callee prologue at `0x181280bc0` spills that ABI argument; this is continuity evidence and is not labeled the semantic first writer.
- The paired JSON retains the spill RIP, raw bytes, register context, later stack load, and unchanged FilterEngine stop.

## Fail-Closed Boundary

- A: observed packed argument arrives from outside the pinned AEX image.
- B: checked-in AEX arithmetic constructs the packed argument and callee spill/load preserves it.
- C: observed construction occurs inside the pinned OpenCV/FilterEngine ranges.
- Any missing, contradictory, or non-sentinel evidence is `ambiguous` and exits non-zero.

## Limits

- No value patch, assertion suppression, Windows execution, After Effects host claim, final-pixel claim, or AE-exactness claim.
