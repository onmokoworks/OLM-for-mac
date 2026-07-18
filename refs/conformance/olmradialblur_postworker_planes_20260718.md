# OLMRadialBlur post-worker planes (2026-07-18)

- Status: `pass_bounded_internal_evidence`
- No AE-exact claim is made.

## FACT

- Checkpoint, AEX, and case input identities matched pinned SHA256 values.
- Checkpoint RIP is exactly 0x180005c9f, the start of FUN_1800056f0 normalization.
- zoom_param1 was loaded from checkpoint metadata as the work/state pointer.
- All requested planes were extracted at exact geometry sizes from readable checkpoint ranges.
- The extracted +0x38 RGBA plane is pre-normalization at this checkpoint.

## INFERENCE

- The established continuation normalized_polar_plane.f32rgba is the appropriate comparison oracle because the checkpoint stops before normalization.
- Exact reconstructed/oracle equality supports the caller normalization model for this bounded state; it does not establish AE equivalence.

- Geometry: `1104x1800` (`1987200` cells).
- Work: `0xf0c25c0`; RIP: `0x180005c9f`.
- Reconstructed normalization equals established oracle: `True`.

## Plane Evidence

- `output_rgba_plus_0x38`: pointer `0x28ecba00`, bytes `31795200`, SHA256 `fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef`.
- `source_scalar_plus_0x40`: pointer `0x2ad1e200`, bytes `7948800`, SHA256 `2af5c86165c5b96b4c686e05f9e4587b0b1b464efbd389803a9d623e69da9a1f`.
- `b150_scalar_gate_plus_0x48`: pointer `0x2b4b2c00`, bytes `7948800`, SHA256 `9d8cbc91c0628af17310bb8521fe5814203612b3586f01bd536c3048a0fa0136`.
- `source_scalar_plus_0x50`: pointer `0x2bc47600`, bytes `7948800`, SHA256 `13a5c887cd8c8c9a6a5380bf65ed8aacebc820d0751a0be81321053a596412ce`.
- `accumulation_rgba_plus_0x4210`: pointer `0x268e4800`, bytes `31795200`, SHA256 `6cd62652dd838e1e42f64a2fce829d27b3da54256adf16084730f12bc03420d0`.
- `max_alpha_plus_0x4218`: pointer `0x28737000`, bytes `7948800`, SHA256 `d729eba1fad810705618e2d5bb580558bbdbde6a6d5aa3df0c142cd9e9c99e96`.
- `eligibility_mask_rbp_minus_0x60`: pointer `0x2c3dc000`, bytes `1987200`, SHA256 `861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7`.
