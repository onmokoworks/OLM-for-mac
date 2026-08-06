# OLMRadialBlur case0009 PF32 captured host boundary

The hash-attested diagnostic bundle captured the checked-out input and output
worlds around production `RenderWorld`. Compact hashes and exact comparison
counts are recorded in
`olmradialblur_case0009_pf32_world_capture_result_20260806.json`; no full world
or EXR artifact and no ephemeral path is retained.

The checked-out input equals both the disabled-control EXR and compact PNG-byte
mapping at all `8,294,400` words. Captured output equals a hostless local
`RenderWorld` replay at all words. Raw captured output differs from effect EXR
in `80,625` RGB words by at most `3` ULP, with alpha exact. Applying float32
`RGB *= alpha` while retaining alpha reproduces all effect EXR words exactly.

Therefore the first divergent boundary is not AE checkout and not RadialBlur:
it is the Output Module `Color: Premultiplied (Matted)` transformation. This
explains the current Mac artifact but is not a Windows-AE exact claim.
