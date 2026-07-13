# OLMDirectionalBlur row755 no-space return and nested-CDB retry

Date: 2026-07-13

## Return classification

The no-space JSX return is `exact_bind_failure`, not algorithm evidence.
Return SHA-256:
`f0fc8ba6593a9610aafea626af941755b447f7bb5c46571f4f005dfb6107a3e1`.

Unlike the preceding attempts, it proves all of these host/debugger gates:

- AE pause marker written;
- exact AEX hash matched;
- CDB attached to the held AE process;
- absolute AEX base emitted;
- breakpoints reached the armed state.

It produced no typed row planes. The generated `+0x5554` breakpoint command
placed 63 `.writemem` operations in one quoted CDB line and exceeded the CDB
command/string limit. The rowdriver predicate also used unsupported `&&`
syntax and emitted `Numeric expression missing`.

## Corrected request

The corrected package keeps the no-space JSX launch, but:

- writes chunk commands as separate lines in `capture_at_5554.cdb`;
- arms `+0x5554` with the short command
  `$><...\capture_at_5554.cdb`;
- expresses row coverage as nested `.if` commands without `&&`;
- keeps exact-size chunk combination and all previous fail-closed gates.

Package:
`refs/runtime_trace_packages/olmdirectionalblur_alpha_fade_fullrender_row755_nospace_jsx_retry_20260713.zip`

SHA-256:
`f267c2f73612eda775642cbe9697bcd242dc4ffd40d856149c9fa513aa8bd896`.

Smoke:
`python3 refs/scripts/smoke_dblur_row755_nospace_jsx_retry_20260713.py`.
