# OLMDirectionalBlur Angle 0 / Diagonal Actual-AEX Port Differential

- Status: `pass`.
- Scope: bounded 16x16 world from case_0005, area `[2,1,14,15]`, downsample `1/2`.
- The checked-in Windows AEX runs under Unicorn. The rotate primitive uses the existing byte-exact detour; only the rowdriver is replaced in the typed run.
- This is binary-grounded rowdriver evidence, not Mac AE exactness.

| angle | actual-AEX output | typed output | equal | rotate bits | rowdriver calls |
| ---: | --- | --- | :---: | --- | ---: |
| 0 | `9a3c02edf3ca268adba2ccbbcfb16b98775e1f78b022ed2bea8694cd3d809d65` | `9a3c02edf3ca268adba2ccbbcfb16b98775e1f78b022ed2bea8694cd3d809d65` | `True` | `['0x3fc90fdb', '0xbfc90fdb']` | 26 |
| 45 | `d1e80171e1b25e9153641121347caf93d0ac389d42479ec15d5ec034ce60a322` | `d1e80171e1b25e9153641121347caf93d0ac389d42479ec15d5ec034ce60a322` | `True` | `['0x4016cbe4', '0xc016cbe4']` | 26 |

## FACT / INFERENCE

- FACT: both control angles reached two real AEX rotate calls, two Iterate8 callbacks, normalization, and the complete output callback.
- FACT: for both angle 0 and 45 degrees, actual-AEX and typed-rowdriver output hashes are identical.
- FACT: user angle 0 materializes `pi/2`; user angle 45 materializes `3pi/4`.
- INFERENCE: the bounded typed rowdriver is compatible with the AEX at both geometry controls for this host fixture.
- LIMIT: this does not prove Mac AE parameter/host binding, full-frame output, modes 2/3, or Windows-vs-Mac AE exactness.

Reproduction: `python3 tools/emulation/test_dblur_angle0_diagonal_actual_aex_port_differential_20260718.py`
