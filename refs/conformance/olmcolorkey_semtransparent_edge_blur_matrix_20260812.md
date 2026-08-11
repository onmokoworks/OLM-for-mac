# OLMColorKey semitransparent Edge Blur matrix

Status: **exact**

A 32x18 two-key multi-island fixture varies alpha on matched and unmatched pixels. The actual Windows AEX worker and the Mac production RenderWorld path match for all 39 PF8/PF16/PF32 cells: the retained 27-cell public Amount-2 matrix plus the 12-cell Direction 0/4, Amount 1/4 endpoint matrix at Distance Type 2. Comparison includes every typed ARGB byte and row-padding byte.

Boundary: Exact only for the declared semitransparent 32x18 two-key fixture: the retained Amount-2 public Direction 1/2/3 x Distance Type 1/2/3 matrix plus Amount 1/4 endpoints at internal Directions 0/4 and Distance Type 2, all at PF8/PF16/PF32. Native actual-AEX temporary planes and final raw output are captured. No AE-host, arbitrary-input, other combination, or geometry claim.
