# OLMBlur Amount × Repeat × Legacy matrix

- Status: `exact`
- Actual AEX: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- Geometry: one deterministic padded `24×24` typed fixture per bit depth
- Matrix: PF8/PF16/PF32 × Amount `5, 129.4` × Repeat `1, 2, 10` × Legacy `off, on`
- Fixed controls: Smoothness `100`, Bias Direction `1`, render scale `1/1`

All 36 complete buffers were produced through the pinned actual-AEX typed
workers and remain retained with SHA-256 identities. The default command only
checks those retained oracle artifacts; it does not execute current production
and is not a current numerical PASS. The former reduced-fake-ABI Mac public
replay is superseded: the
current production public owner intentionally admits only Amount `5`, Repeat
`1`, both Legacy values, and the exact source/layout in
`olmblur_smart_public_admission_20260813.{json,md}` (six numerical cells).

The fixtures contain zero, near-zero, midpoint, and endpoint integer channels;
PF32 additionally contains negative and over-range float values. This closes
the mode-dependent interaction between repeat scheduling and amount without
generalizing to other geometry, Bias Direction, Smoothness, downsample, the
actual Windows public SmartRender callback chain, or native AE rendering.

Regenerate the retained typed-worker matrix through the pinned AEX worker
probe (an explicit oracle export, not a current-public replay):

```sh
python3 tools/emulation/test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810.py --export
```

Validate the bounded current public owner instead:

```sh
python3 tools/emulation/test_olmblur_smart_public_admission_20260813.py --validate-only
```
