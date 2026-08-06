# OLMKiraKira Ramp arbitrary callback entrypoint witness

The checked-in 2025 Windows AEX was executed through exported `entry_point`
with `PF_Cmd_ARBITRARY_CALLBACK` (`22`). All numeric selectors `0..10` reached
the recovered `RampDataHandler` slots: NEW `+0x18`, DISPOSE `+0x08`, COPY
`+0x20`, FLAT_SIZE `+0x38`, FLATTEN `+0x28`, UNFLATTEN `+0x30`, INTERPOLATE
`+0x48`, COMPARE `+0x40`, PRINT_SIZE `+0x50`, PRINT `+0x58`, and SCAN `+0x60`.

The lifecycle witness creates a `0x260` handle, serializes `0x145` bytes,
unflattens it, compares equal, copies/interpolates it, and disposes every
result through the same exported entrypoint. See the adjacent JSON for exact
events and hashes.

The raw Windows blob's unused tail is not deterministic, but actual UNFLATTEN
ignores it. Zero-, `0xA5`-, and allocation-pattern tails all compare equal and
produce identical Mode2 output. Mac therefore emits the canonical form: version,
count, active records, then a zero-filled tail. The five rows are enabled for a
41-parameter surface.
