# OLMKiraKira Witness Path Split

- Focus: `(934, 118)`
- Status: `historical-8bpc-and-live-16bpc-lanes-must-not-be-mixed`

## Reference

- RGBA8: `[131, 131, 131, 255]`

## Historical 8bpc lane

- bitsPerChannel: `8`
- Output PNG: `[144, 144, 144, 255]`
- Debug out_u8: `[144, 144, 144, 255]`
- Debug source: `[0.117647059, 0.117647059, 0.117647059, 1.0]`

## Live 16bpc lane

- bitsPerChannel metadata: `None`
- Output PNG: `[91, 91, 91, 255]`
- Debug out_u8: `[45, 45, 45, 128]`
- Debug out_u8 * 2 RGB: `[90, 90, 90, 128]`

## Reading

- The old 144-valued KiraKira hotspot witness belongs to an explicit 8bpc request lane, while the 2026-07-03 live probe was run through a request with no project bits_per_channel metadata and executed as a 16bpc host path. Those are different host contexts.
- At the same hotspot `(934,118)`, the historical 8bpc rerun reproduces `[144,144,144,255]`, while the live 16bpc lane exports `[91,91,91,255]` and logs plugin-local `out_u8=[45,45,45,128]`. So the current KiraKira discrepancy is not permission to collapse the lane into a single provenance statement.
- Next: Keep 8bpc witness reasoning and 16bpc/live-host reasoning separate. Reopen provenance/export claims only after matching bit-depth and host context.
