# OLMDirectionalBlur row755 return

Date: 2026-07-14

## Verdict

`exact_bind_failure` at `jsx_launch`. This is Windows AE queue-dispatch
evidence only; no DirectionalBlur algorithm or pixel evidence was returned.

## Facts

- Request: `olmdirectionalblur_row755_20260713`
- Archive: `refs/windows_returns/20260714/20260714_182123__RETURN__OLMDIRECTIONALBLUR_ROW755.zip`
- SHA-256: `a7f0a0115906fabd672e09405ab6aba664ed5bebb71cc61e32de6160de1a6832`
- AfterFX process observed in session 1 with command line `AfterFX.exe -m`.
- The process did not execute the dispatched queue JSX.
- Missing: `queue_bootstrap.log`, typed row witness, and render artifact.

## Decision

Retain as host-launch failure. Do not change DirectionalBlur source or status.
