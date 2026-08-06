# OLMSmoother v1 PF16 macOS AEXCompat handoff

This handoff requests one missing generic capability: a macOS broker entry for
a hash-bound, one-frame, classic `argb16` render session. The guest worker
already recognizes typed worlds, but broker `image_render` and
`render_request` are currently Windows-gated. Removing the cfg alone is not an
implementation: platform-specific process launch and authenticated transport
must remain explicit.

The machine-readable contract pins the standalone AEX, original run5 request,
source EXR, crash dump, parameters, and the two PF16 words recovered from the
dump. It also requires raw typed-world hashes including row padding. PNG output
is not accepted as typed evidence.

The focused test is intentionally two-stage. It always validates the handoff
and retained run5 identities. When the external task returns its report at the
declared path, it additionally validates format, render path, plugin identity,
parameter readback, input immutability, guards, and session cardinality.

Passing this request proves only a bounded AEXCompat typed session. Exactness
against the source-included production kernel is a later comparison, and AE
host/export exactness remains separate.
