# OLM native UCRT math batch request

- Status: `ready_native_windows_ucrt_batch_ae_free`
- DirectionalBlur: 494 exact `expf` source-expression rows
- DirectionalBlur: 787 exact actual-call `powf` keys
- DistanceGradation: 63 exact `powf` pairs
- Total: 1,344 rows in one 64-bit AMD64 process
- After Effects required: no

The batch requires both child results to report the same exact System32
`ucrtbase.dll` identity. It changes no production admission: DirectionalBlur's
six x86_64 cells and DistanceGradation's eight PF32 Power cells remain
fail-closed until their respective downstream public-output evidence is also
complete.
