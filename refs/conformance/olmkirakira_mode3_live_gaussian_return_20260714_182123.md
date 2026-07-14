# OLMKiraKira Mode 3 live Gaussian return

Date: 2026-07-14

## Verdict

`exact_bind_failure` at `ae_jsx_preflight`. The preflight `-r` invocation did
not emit its ready marker, so no Gaussian coefficient payload was captured.

## Facts

- Request: `olmkirakira_mode3_live_gaussian_20260713`
- Archive: `refs/windows_returns/20260714/20260714_182123__RETURN__OLMKIRAKIRA_MODE3_LIVE_GAUSSIAN.zip`
- SHA-256: `18bdbc6c54f753da33d3b23551f45daacc4d5e17775e7795a8283edeb03de08f`
- AfterFX was observed in session 1 with `AfterFX.exe -r`.
- The required preflight ready marker was absent.
- No `gaussian_kernel_21_f32_le.bin` or typed Gaussian return was present.

## Decision

Retain as host-launch failure. Do not infer coefficients or modify the
KiraKira Mode 3 implementation.
