# OLM RadialBlur PF32 Zoom Noise 32×18

Status: **exact**

Actual AEX and production match for pre/post polar planes and padded final output at Noise 0/25/100. The apparent final mismatch had two probe-only causes: the retained 9×7 center literal `(4,3)` affected active pixels, then the retained `0xA0+y` padding seed affected only row padding. Materializing public center `(16,9)` and the fixture padding contract closes the general centered same-shape rule without a geometry-specific output mapping.
