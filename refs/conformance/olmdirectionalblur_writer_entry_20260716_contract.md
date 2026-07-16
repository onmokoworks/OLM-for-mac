# OLMDirectionalBlur Writer Entry Boundary Contract

This request is one hash-pinned Windows AE 2025 Software run for
`db_angle0_alpha_fade_hard_edges` (Front Alpha Fade). The input, expected PNG,
comp, frame, and effect parameters are copied from the existing row755 request:
1920x1080, 8bpc, 24 fps, angle `0`, brightness gain `1`, size variation `0`,
front strength `48`, front alpha fade `0`, sharp tail `0`, back strength `0`,
back alpha fade `0`, and sharp tail `0`.

Required identity is the same `run_id`, AE PID, loaded `OLMDirectionalBlur.aex`
module base, renderer, case id, and pinned 2025 AEX SHA-256
`d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e` on every
record. The target `(494,169)` must produce a writer-entry pre-store float RGBA
record and a store-immediately-after PF ARGB8 byte record sharing
`same_run_key=writer-pf-494-169`. The same run must also bind the existing PF
output hash and returned PNG export.

Missing hook, missing typed field, absent export, or mixed run identity is an
`exact_bind_failure`; no partial result is accepted. The package is local only
and must not be copied to NAS. No production, ledger, or `smoke_all` files are
part of this request.
