# OLMDirectionalBlur Diagonal Actual-AEX vs Typed-Rowdriver Differential

- Status: `pass`.
- Scope: case_0005 crop around primary witness `(507,367)`, angle `45`, 16x16 world, rowbytes `76`, area `[2,1,14,15]`.
- The actual run leaves AEX rowdriver `0x1800038d0` in place; the typed run detours only that rowdriver. Both runs use the byte-exact rotate detour.
- Actual output SHA-256: `d1e80171e1b25e9153641121347caf93d0ac389d42479ec15d5ec034ce60a322`; typed output SHA-256: `d1e80171e1b25e9153641121347caf93d0ac389d42479ec15d5ec034ce60a322`; equal: `True`.
- Typed state: `{'mode': 1, 'dimensions': [26, 26], 'buffers': {'source': '0x2002ac88', 'destination': '0x2002d6c8', 'denominator': '0x20030108', 'alpha': '0x20030b98', 'comp_map': '0x20031628'}, 'rowdriver_calls': 26, 'last_rows': [25, 26]}`.
- Schedule probe: `{'status': 'blocked', 'rowdriver_calls': 26, 'return_address': '0x18000553b', 'normalization_stop': '0x180005554', 'last_rows': [25, 26]}`.
- No AE-exact claim is made; production integration is explicitly unclaimed.

Reproduction: `python3 tools/emulation/test_dblur_diagonal_actual_aex_port_differential_20260716.py`
