# OLMColorKey parameter UI parity

Status: **source-fixed, built, installed, and AE-load verified**

The Windows 2025 AEX parameter setup and the fresh Windows AE property manifest
agree that `Number of Colors` is an integer slider with valid/UI range `0..25`
and default `1`. The Mac port had narrowed both minima to `1`. The Mac setup now
uses `0..25`, preserving `NUMBER_OF_COLORS_DISK_ID == 0x15`, parameter order,
type, and default, so saved-project ABI is unchanged.

The audited fixed surface retains the Windows group nesting, names, popup choice
strings/defaults, Edge Thin integer range, Edge Blur float range and precision,
and all existing leaf disk IDs. This change does not alter rendering semantics.

The plugin was rebuilt Universal (`arm64 x86_64`), ad-hoc signed, installed, and
After Effects 26.3 restarted without a plugin-load or duplicate-plugin modal.
Installed executable SHA-256: `23d551389131bcb28a2505b68f5c5726b3177af0ec100577adae4369dad48678`.
Computer Use confirmed the restarted host, but did not obtain a reliable
accessibility-tree readout of the slider minimum; therefore native visual range
inspection is not promoted beyond the exact setup-source/build evidence.
