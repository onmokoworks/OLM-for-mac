# OLMToonDilate Mac Depth Contract Audit - 2026-07-15

## FACT

- The public `PF_Cmd_RENDER` callback is a no-op matching actual AEX owner `FUN_1801a7840`; rendering is exclusively Smart Render.
- The advertised Smart Render callback dispatches the explicit `extra->input->bitdepth`, including `PF_PixelFloat` for 32bpc.
- The Mac 32bpc effect/control pair is classified `blocked-by-host-input-conversion`; it is not `AE exact`.
- The existing 32bpc probe evidence is PNG-only/non-float-preserving and remains probe-only.

## INFERENCE

- Mac 32bpc support is evidenced only when AE invokes the float-aware Smart Render path.
- The legacy no-op cannot promote a 32bpc probe to an exact claim without cross-host Smart Render pixels.

## Gate

`python3 refs/scripts/smoke_audit_olmtoondilate_mac_depth_contract_20260715.py`
