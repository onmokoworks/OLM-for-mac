# OLMDirectionalBlur Actual-AEX vs Typed-Port Differential Follow-Up

- Status: `pass`.
- Scope: angle 0, padded PF_EffectWorld (`rowbytes=76`), non-full area `[2, 1, 14, 15]`.
- Actual AEX and typed port output SHA-256: `942a45b3a8eeb5da50f7badbfd6d68a4594b6af486b58be44d1d950cbf7e5ca5`.
- Typed ownership: `{'source': '0x2002ac88', 'destination': '0x2002d6c8', 'denominator': '0x20030108', 'alpha_max': '0x20030b98', 'comp_map': '0x20031628'}`; source and destination are distinct.
- Fail-closed schedule proof: stopped at `0x180005554`; rowdriver returns to `0x18000553b` after `26` typed calls.
- Production integration was not callable in this environment; no AE-exact claim is made.

Reproduction: `python3 tools/emulation/test_dblur_actual_aex_port_differential_20260716_followup.py`
