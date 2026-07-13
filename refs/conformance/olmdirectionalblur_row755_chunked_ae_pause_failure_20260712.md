# OLMDirectionalBlur row755 chunked return: AE pause failure (2026-07-12)

## Intake

- Return status: `exact_bind_failure`.
- AEX identity matched SHA-256
  `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`
  and size `56832`.
- Two attempts failed before CDB attach: `ae_ready.marker` was never written.
- No CDB trace or requested row755 buffers exist. This return is not answered
  and cannot promote any DirectionalBlur evidence.

## Runner diagnosis

The package launched AE with `Start-Process -ArgumentList @('-r',$jsx)`.
PowerShell joins `ArgumentList` strings and does not guarantee quoting of an
individual path containing spaces. The observed result (AfterFX remains alive,
but no JSX log/result/marker is created) is consistent with the JSX path being
split before AE receives it.

The retry now explicitly quotes the JSX path and launches with `-m -r` so the
request owns a new AE process. This is a runner correction, not an algorithm
change or an answered runtime witness.
