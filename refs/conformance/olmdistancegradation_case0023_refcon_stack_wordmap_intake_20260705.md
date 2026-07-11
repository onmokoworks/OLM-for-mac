# OLMDistanceGradation case_0023 refcon/stack/wordmap follow-up — 2026-07-05 intake

Return: `olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702_return_windows_20260705.zip`
(imported from `/Volumes/onmk/olm_pr/new` on 2026-07-05)

## Classification

`failed_partial` (verify: `[MISS] count=3 statuses=diagnostic,failed_partial`).
This is the **third consecutive `failed_partial`** on this witness family with the
**same root blocker**: the hook cannot be bound back to the authoritative triplet.

## What the return DID retain (useful context, not proof)

- `DistanceGradation.aex` loaded; breakpoints armed at `FUN_181170280` / `FUN_181170480`.
- `FUN_181170480` retained **130 hook hits** with live `r8`, `r9`, `[rsp+0x28]`, and
  stack/refcon qword+dword dumps (e.g. hit 0: `r8=0x2d`, refcon qwords `0x80008000`
  repeated; hit 23: `rdx=0x391`, `r8=0x169`, `out_pixel16_pre = 8000 8000 0000 0000 …`).
- Authoritative triplet final stored RGBA16 (README-authoritative):
  - `(414,393)`: inside `35.014`, outside `0.0`, final `[7195,0,61165,65535]` (blue-low endpoint)
  - `(415,393)`: inside `36.014`, outside `0.0`, final `[65535,0,0,65535]` (red)
  - `(416,393)`: inside `37.014`, outside `0.0`, final `[65535,0,0,65535]` (red)
  - Case params: `in_out=3 (Both)`, `inside_threshold=36`, `outside_threshold=0`,
    `render_mode=1`, `use_background_color=1`, `interpolation_mode=1`.

## What is still missing for `answered`

- No witness-bound proof that any retained `FUN_181170480` hit is exactly
  `(414/415/416, 393)`.
- No width/stride→xy mapping recovered from retained `r9` / `[rsp+0x28]`.
- No typed helper-stage / compose RGBA at the same hook for the triplet.
- No output-word watchpoint stop immediately before the triplet store.
- `xy_recovered_from_stack_refcon_wordmap: false`,
  `trace_status: final_stage_known_hook_binding_missing` for all three pixels.

## Orchestration read

The Windows debugger route has now failed the **same xy-binding step three times**.
This is the identical failure class that the local `.aex` emulation lane bypassed for
OLMRadialBlur tiny Rotation (M1–M4, 2026-07-05): emulation makes xy-binding trivial
because the harness controls which pixel is rendered and can read the output world at
the exact witness coordinate. `DistanceGradation.aex` (64/2025) is a standard PE64 and
loads in the same generic `tools/emulation/aex_loader.py`, so the recommended next move
is to drive `FUN_181170480` (compose/word-store) locally for case_0023 rather than
re-ask the same Windows hook-binding a fourth time.

Note: this return is threshold-family. Per the ledger split, the threshold triplet is
provenance/export-first against the Mac build; emulation here is for binary-grounding the
threshold decision / compose value at the boundary, not for retuning from PNG means.

The return remains in `share/new` (verify failed → not auto-archived).
