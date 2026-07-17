# OLMToonDilate Mac Depth Contract Audit - 2026-07-15

## FACT

- The classic `PF_Cmd_RENDER` callback queries `PF_WorldSuite2::PF_GetPixelFormat` and explicitly dispatches ARGB32/64/128.
- The advertised Smart Render callback dispatches the explicit `extra->input->bitdepth`, including `PF_PixelFloat` for 32bpc.
- The Mac 32bpc effect/control pair is classified `blocked-by-host-input-conversion`; it is not `AE exact`.
- The existing 32bpc probe evidence is PNG-only/non-float-preserving and remains probe-only.

## INFERENCE

- Mac 32bpc support is evidenced only when AE invokes the float-aware Smart Render path.
- A correct classic callback boundary cannot promote a 32bpc probe to an exact claim without cross-host pixels.

## Gate

`python3 refs/scripts/smoke_audit_olmtoondilate_mac_depth_contract_20260715.py`
