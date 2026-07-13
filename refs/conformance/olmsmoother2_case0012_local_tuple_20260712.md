# OLMSmoother2 case_0012 local tuple replay

Date: 2026-07-12

## Verdict

`PASS_LOCAL_ACTUAL_AEX_TUPLE_REPLAY`

This is bounded local AEX binary-semantic evidence only. It is not Windows or
After Effects truth.

## Command

```sh
python3 tools/emulation/test_smoother2_case0012_local_tuple.py \
  --output refs/conformance/olmsmoother2_case0012_local_tuple_20260712.json
```

## Exact run output

- Input: exact 25-record 5x5 class/setup neighborhood from
  `olmsmoother2_case0012_class_neighborhood_20260712.log`.
- Host target: `(91,841)`; local translated origin: `(8,8)`.
- AEX: `aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex`.
- Actual entries executed: `0x18000c280`, `0x18000cce0`.
- `c280`: `count=1`; vertex RGBA
  `[0.9910671710968018, 0.9910671710968018, 0.9910671710968018, 0.9960784316062927]`;
  weight `0.49999961256980896`.
- `cce0` no-gamma entry: RGBA
  `[0.9910671710968018, 0.9910671710968018, 0.9910671710968018, 0.4980388283729553]`.
- Both calls used the reused descriptor/config ABI scaffold with fixed scale
  `[65536,65536]`.

## Explicit limits

- The coordinate translation preserves only the logged offsets; it does not
  establish host-image addresses or live Windows binding.
- Logged gamma metadata is retained as input evidence, but the executed cce0
  call uses the grounded no-gamma mode-0 ABI path. No gamma or host writeback
  truth is claimed.
- No production Mac comparison, Windows render, After Effects render, or final
  byte-packing claim is made.

## Comparison with the live Mac AE trace

The checked-in live Mac AE neighborhood trace reports one vertex with weight
`0.356321841` and orchestrated RGBA
`[0.991067231,0.991067231,0.991067231,0.3549245]`. This local AEX replay uses
the older scaffold's fixed scale `[65536,65536]` and mode 0, producing weight
`0.49999961256980896` and alpha `0.4980388283729553` instead. The identical
5x5 class/setup data therefore does **not** bind the live producer tuple by
itself. The next discriminating evidence is the typed config block and mode at
the live `c280`/`cce0` callsite; no polygon or gamma fallback should change
before that capture.

Machine-readable output: `olmsmoother2_case0012_local_tuple_20260712.json`.
