# OLMToonDilate Mac Depth Contract Audit - 2026-07-15

## FACT

- The legacy `PF_Cmd_RENDER` callback selects only 8/16bpc via `PF_WORLD_IS_DEEP(output)`.
- The advertised Smart Render callback dispatches the explicit `extra->input->bitdepth`, including `PF_PixelFloat` for 32bpc.
- The Mac 32bpc effect/control pair is classified `blocked-by-host-input-conversion`; it is not `AE exact`.
- The existing 32bpc probe evidence is PNG-only/non-float-preserving and remains probe-only.

## INFERENCE

- Mac 32bpc support is evidenced only when AE invokes the float-aware Smart Render path.
- The legacy callback boundary cannot promote a 32bpc probe to an exact claim.

## Gate

`python3 refs/scripts/smoke_audit_olmtoondilate_mac_depth_contract_20260715.py`
