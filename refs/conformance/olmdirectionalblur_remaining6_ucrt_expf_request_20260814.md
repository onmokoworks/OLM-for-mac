# OLMDirectionalBlur remaining-six native UCRT request closure

- Status: `ready_native_windows_ucrt_capture_ae_free`
- Request: `olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_expf_20260814`
- Vectors: 494 exact source-expression rows for counts 8, 50, 96, 100, 240
- Target: 64-bit AMD64 `%WINDIR%\System32\ucrtbase.dll!expf`
- Vector digest: `0b13bec85e6b37e663f50ea36ce08f544b8e7bc6807c708af58b4f9c04aac455`

This is an AE-free request package, not a numerical promotion. The current
x86_64 six-cell route remains fail-closed until a native Windows return is
validated and the six fixed public outputs are rebuilt from those returned
words. AEXCompat results are not accepted, and counts 96 and 240 are recaptured
in the same run rather than mixed from an older UCRT identity.
The index-zero source row is `-0`; after the strict return proves exact `+1`,
downstream replay normalizes only that value to production's materialized `+0`.
