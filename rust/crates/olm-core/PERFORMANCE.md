# Row access and scheduling

`View::row(y)` and `ViewMut::row_mut(y)` expose only active bytes. They support
odd strides, unaligned channel storage, nonzero origins, and a final row without
padding. Coordinates are local; callers translate global coordinates once and
validate source coverage before mapping a crop. `View::pixels(y)` decodes a row
without repeated geometry checks. `read_pixel` and `write_pixel` require at least
`depth.pixel_bytes()` bytes and retain native float payload bits.

`ViewMut::for_each_row` splits mutable destination storage into disjoint row
chunks. Callbacks receive absolute local row indices and active bytes; padding
is untouched. Input captures must be read-only. `parallel_rows_auto` provides
the corresponding driver for packed scratch planes (stride in elements).

Workers are capped by available parallelism and row count, with a conservative
65,536-byte/element grain. Small buffers execute inline. `parallel_rows` also
accepts an explicit worker cap; one worker executes inline. Every scoped worker
is joined before return, with no persistent pool or global mutable state.
Callbacks must be independent of invocation order; ordered neighborhood scans
and floating-point reductions must retain their original order.

Tests compare one versus multiple workers and check active bytes, padding,
short final rows, negative origins, and float payloads. Native AE Multi-Frame
Rendering performance remains unmeasured; these are per-call bounds, not a
process-wide thread reservation.
