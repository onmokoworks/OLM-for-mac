# OLMColorKey PF16 Edge Blur internal plane

Status: **pass**

- actual AEX direction planes: `{'single': [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'line': [0.5, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'all': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]}`
- production direction planes: `{'single': [0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'line': [0.5, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'all': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]}`
- boundary: AEX distance_type=2 generator produces an all-zero seed plane from the inverse PF16 mask; production Boundary8+L1 does not. Final-pixel equality is intentionally not claimed.
