# OLMColorKey Color Keep × Premultiplied × Replace

Status: **exact**

The 11x7 asymmetric two-key fixture covers accepted/rejected colors, fractional alpha, alpha-zero hidden RGB, and padded rows. All 24 public-toggle/depth cells compare the actual Windows AEX full worker against production output byte-for-byte.

Toggle ownership: Premultiplied changes classifier input interpretation and rejected-pixel writeback; Color Keep inverts mask writeback and admits Replace; Replace changes accepted-key RGB without changing classification.

Boundary: Exact only for the declared 11x7 two-key padded fixture, Color Keep off/on, Premultiplied off/on, Replace off/on, and PF8/PF16/PF32 through the actual AEX full worker. Threshold, Edge, other key colors/counts, geometry, and native AE-host parameter materialization are not claimed.
