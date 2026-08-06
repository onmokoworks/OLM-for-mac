# OLMKiraKira Ramp flat relocation boundary

Two actual-AEX entrypoint runs used identical ramp semantics but shifted host
allocations by `0x3000`. Both FLATTEN→UNFLATTEN roundtrips compared equal, yet
their `0x145`-byte flat SHA-256 values differed. The Windows flatten routine
copies stack-backed unused regions, so the complete blob is not presently
proven deterministic or pointer-free.

All observed differences fall in the tail ignored by actual UNFLATTEN. Tainting
that tail with zero, `0xA5`, or allocation-derived bytes preserves COMPARE and
bit-exact Mode2 output. The Mac serializer therefore canonicalizes the tail to
zero and enables the five arbitrary rows, yielding 41 parameters.
