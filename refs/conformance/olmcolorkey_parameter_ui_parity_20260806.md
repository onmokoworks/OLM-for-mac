# OLMColorKey parameter UI parity

Status: **source-fixed, built, installed, and AE-load verified**

The Windows 2025 AEX parameter setup and the fresh Windows AE property manifest
agree that `Number of Colors` is an integer slider with valid range `0..25`, UI
range `0..30`, and default `1`. The Mac port had narrowed both minima to `1` and
its UI maximum to `25`. The AEX raw record also proves Edge Thin has valid range
`-4000..4000` but UI range `-100..100`; Mac previously exposed the full valid
range as its UI range. Both UI ranges now match the AEX while preserving disk
IDs, parameter order, types, defaults, and therefore saved-project ABI.

The full raw comparator subsequently closed all 223 owned `add_param` rows. It
also found and corrected Edge Blur UI range `0..100`, the AEX parameter flags
(`0x20` collapsed fields and `0x40` supervised controls), `Use Color 1` default
off, and the Edge Blur end-topic structural ID `16`. Leaf disk IDs remain
unchanged; changing the structural end-topic ID does not alter saved leaf values.

The audited fixed surface retains the Windows group nesting, names, popup choice
strings/defaults, Edge Thin integer range, Edge Blur float range and precision,
and all existing leaf disk IDs. This change does not alter rendering semantics.

The plugin was rebuilt Universal (`arm64 x86_64`), ad-hoc signed, installed, and
After Effects 26.3 restarted without a plugin-load or duplicate-plugin modal.
Installed executable SHA-256: `020d2c0634137f94c37991c7c93afa832eba4abc9ba4e6ce7c370ec9a268bc46`.
Computer Use confirmed the restarted host, but did not obtain a reliable
accessibility-tree readout of the slider minimum; therefore native visual range
inspection is not promoted beyond the exact setup-source/build evidence.
