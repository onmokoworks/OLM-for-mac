# OLMBlur Amount × Repeat × Legacy matrix

- Status: `exact`
- Actual AEX: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- Geometry: one deterministic padded `24×24` typed fixture per bit depth
- Matrix: PF8/PF16/PF32 × Amount `5, 129.4` × Repeat `1, 2, 10` × Legacy `off, on`
- Fixed controls: Smoothness `100`, Bias Direction `1`, render scale `1/1`

All 36 complete buffers execute first through the pinned actual-AEX typed
workers and are retained with SHA-256 identities. The default test then sends
the same source and public parameter tuple through production Mac
`EffectMain(PF_Cmd_SMART_PRE_RENDER)` and
`EffectMain(PF_Cmd_SMART_RENDER)`. Parameter checkout order is `1..5`, active
typed bytes are exact, alpha follows the AEX result, and row padding is intact.

The fixtures contain zero, near-zero, midpoint, and endpoint integer channels;
PF32 additionally contains negative and over-range float values. This closes
the mode-dependent interaction between repeat scheduling and amount without
generalizing to other geometry, Bias Direction, Smoothness, downsample, the
actual Windows public SmartRender callback chain, or native AE rendering.

Reproduce the routine Mac regression without Windows:

```sh
python3 tools/emulation/test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810.py
```

Regenerate the retained oracle directly from the pinned AEX:

```sh
python3 tools/emulation/test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810.py --export
```
