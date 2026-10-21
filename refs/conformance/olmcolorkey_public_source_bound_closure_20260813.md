# OLMColorKey public source-bound closure (2026-08-13)

Status: `pass_hostless_public_source_bound_raw_exact`

Exactly 63 fixed cells (33 edge-blur, six Lab76 order, and 24 Color Keep / Premultiplied / Replace toggle cells) are raw exact through both public Classic and Smart entries. Production source: `4dbd264501a0d5d990a3726d16223c01c1996677b925f8546157b6a91ce677d1`.

The hostless real-SDK closure covers 567 source/tuple/world negatives, 13 Smart callback errors or throws, 12 suite cases, and every one of 33 parameter checkout plus 33 checkin failure ordinals. Output is not committed on failure. The public-entry output stream is identical on native arm64 and Rosetta x86_64.

This does not claim installed or native-AE execution, arbitrary sources or tuples, or GPU behavior. Install and AE smoke are deferred to a later batched checkpoint.
