# OLMDirectionalBlur rowdriver binding audit (2026-07-18)

Status is written by `tools/emulation/audit_olmdirectionalblur_rowdriver_binding_20260718.py`.

This is a bounded Mac-local Unicorn execution of the checked-in Windows
`OLMDirectionalBlur.aex`. It calls one real row of `FUN_1800038D0` and observes
the real `FUN_1800013E0` calls. It verifies the decompilation's buffer and stack
contract: source A, destination B, denominator, alpha/validity plane, front
weight table, direction, strength, and row width.

It is not an AE render comparison and does not promote `AE exact`. The natural
worker fixture still does not enter `FUN_1800038D0`; the next boundary is the
natural worker scheduling/dispatch that supplies these arguments in a real
render. No production source or ledger row is changed by this audit.
