# OLM RadialBlur PF16 Noise Type 1 pairwise — 2026-08-11

Status: **exact**

All 16 bounded cells are consumed-plane/output exact against actual AEX. Rotation prepass accepts a zero source scalar while scatter retains its zero-scalar skip. The known one-ULP Rotation `source_scalar` differences occur only in inactive, unreferenced allocation-boundary cells and are excluded from semantic exactness.
