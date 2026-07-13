# OLMSmoother2 case0012 live config capture contract

Date: 2026-07-12

## Scope

This contract is for one fresh Windows current-AEX run of
`legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`, scanner `idx=105`,
descriptor `[91,841,1,91,843,5]`.

## Required same-run evidence

The return must emit all of these from the same run and witness stop:

- `observations.c280.config_raw_bytes`
- `observations.c280.config_pointer` and `config_pointer_arithmetic`
- `observations.c280.scale_fixed`
- `observations.cce0.config_raw_bytes`
- `observations.cce0.config_pointer` and `config_pointer_arithmetic`
- `observations.cce0.mode_byte` and `mode_name`

The byte spans are exact: c280 must include the 8 bytes for its two 32-bit
scale fields at render-config offsets `+0x20` and `+0x24`, with decoded
`scale_fixed`; cce0 must include the gamma-context bytes from `+0x00` through
the mode byte at `+0x06`, with decoded `mode_byte` and `mode_name`. The return
must preserve the raw bytes and pointer arithmetic, not only decoded numbers.

These raw byte fields are the discriminators. A polygon, c280 index, cce0
float, or final writer value without the bound config bytes is insufficient,
because the local replay currently supplies its own config scaffold.

## Current instrumentation audit

The Mac host trace currently emits input/setup bytes, class-neighborhood bytes,
parameter values, polygon vertices, and the orchestrator float. It does not
emit c280 raw config bytes, c280 pointer arithmetic, cce0 raw config bytes, or
the cce0 mode byte. The smoke therefore fails closed until a live return carries
those fields.

The local replay metadata is `c280 scale_fixed=[65536,65536]` and cce0 no-gamma
`mode_byte=0`. Those values are not Windows expectations.

## Smoke

```sh
python3 refs/scripts/smoke_olmsmoother2_case0012_live_config_contract.py
```

The default smoke passes only when the host/package audit is valid and reports
`BLOCKED_MISSING_LIVE_CONFIG_BINDING` without a live return. Use
`--strict-live --return <same-run-return.json>` for the promotion gate.
