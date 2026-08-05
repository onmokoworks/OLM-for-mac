# OLMColorKey Edge Blur direction 1

Status: **pass**

Scope: 4x3 single black key, Edge Blur amount 2.0 and public direction 1, PF8/PF16/PF32 actual full worker through production SmartRender; exact internal distance/direction planes, final alpha, padding, and AEX hash. No other direction/amount or AE-host claim.

Direction 1 exposes a negative boundary plane and an unbounded final multiplier. PF8 wraps after integer cast, PF16 exceeds its nominal 32768 channel maximum, and PF32 remains above one.
