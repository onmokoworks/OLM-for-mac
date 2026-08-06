# OLMSmoother v1 raw setup parity

The pinned Windows AEX was called directly for `GLOBAL_SETUP` and
`PARAMS_SETUP`. A sentinel-filled 404-byte Windows `PF_OutData` window proves
that global setup changes exactly three dwords: version `0x00090800` at `+0`,
`out_flags=0x02000040` at `+0x60`, and `out_flags2=0x08000000` at `+0x190`.
Production returns the same four semantic results, including `PF_Err_NONE`.

All three complete `0xb0` Windows parameter records were captured at the host
`add_param` boundary. Only the relocation-bearing empty-description pointer at
`+0x40` is normalized before hashing. The public records have disk IDs
`1,2,3`, parameter types `4,5,1`, and both `flags=0` and `ui_flags=0` for every
row. Production setup matches these header fields along with the already pinned
defaults, ranges, and color.

The English names `Use Color Key`, `Color Key`, and `Do Smooth Range` remain
grounded by the retained independent-worker fixture. This evidence does not
claim other locales, actual AE panel layout, rendering, PF16, or PF32 behavior.

Executable evidence:

- `tools/emulation/test_olmsmoother_v1_setup_raw_actual_production_20260806.py`
- `refs/conformance/olmsmoother_v1_setup_raw_actual_production_20260806.json`
