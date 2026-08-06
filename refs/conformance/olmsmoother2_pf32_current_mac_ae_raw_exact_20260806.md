# OLMSmoother2 current Mac AE PF32 raw-exact boundary

The bounded `final_random10_olm_smoother_v2_07` case ran in After Effects
`26.3x87`, Software renderer, 32 bpc, working space `None`, Preserve RGB input,
and uncompressed FLOAT RGBA OpenEXR output.  The installed Universal executable
was SHA-256
`fe782f344dcaf8865b778198b0faeb8cecd525062a83f38aca8dc1db74442c34`.

The nonce-bound process attestor observed AE PID `88521` and exactly one vmmap
mapping of that executable before and after both renders.  PID birth identity,
AE executable identity, plug-in inode/stat identity, and module hash remained
unchanged across the interval.

Both raw FLOAT32 comparisons against the pinned Windows AE 26.3 Software /
Preserve RGB artifacts are exact:

| Branch | Values compared | Mismatched values | Maximum raw u32 delta |
|---|---:|---:|---:|
| no-effect control | 8,294,400 | 0 | 0 |
| effect enabled | 8,294,400 | 0 | 0 |

The Windows artifact manifest and same-run PF32 input-entry witness are also
admissible and exact.  This closes the current Mac host/load/render boundary
for this one declared PF32 case and parameter vector.  It does not generalize
to other parameters, cases, depths, renderers, color-management settings, or
AE versions.

The classification remains
`raw_float32_exact_artifact_only_missing_windows_process_proof`: the retained
Windows artifacts are exact and their PF32 entry is same-run-bound, but the
Windows render lacks an equivalent same-run AfterFX process and loaded-AEX
module attestation.  Therefore this record does not make a two-host AE-exact
process-proven claim.

Primary evidence is under
`refs/mac_validation_runs/olmsmoother2_pf32_current_20260806_run1/output/`, in
particular `mac_process_attestation.json`, `mac_validation_return.json`, and
`validation_report.json`.
