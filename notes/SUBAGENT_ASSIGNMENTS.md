# OLM Port Sub-Agent Assignments

This note records the parent/child split for parallel OLM porting work.
Sub-agents are useful for read-only objdump/Ghidra/decomp/PNG-reference audits;
the parent agent owns implementation, verification gates, documentation
integration, and commits.

## Operating Rules

- Parent agent keeps the canonical status in `notes/PORTING_BOARD.md` and
  plugin-specific IR/ASM notes.
- Sub-agents should not edit implementation files unless the parent explicitly
  grants a disjoint write scope.
- Sub-agent findings must cite the files, commands, or reference requests that
  support them.
- Do not deep-tune from PNG residuals alone. If the next discriminating evidence
  is a Windows AE reference request, stop that plugin and ask for that package.
- Returned findings should be folded back into an IR or ASM facts note before
  implementation changes are promoted.

## Active 2026-06-06 Parallel Audit

| Plugin area | Agent | Scope | Expected output |
| --- | --- | --- | --- |
| `OLMDirectionalBlur` | `019e99be-1aad-7392-81a8-7aceed96535b` / Tesla | Read `notes/IR_OLMDirectionalBlur.md`, `notes/OLMDirectionalBlur_ASM_FACTS.md`, current C++/Python probes, decomp/disasm as needed. | IR checkpoints, measured status, stop condition, one non-guesswork next action. |
| `OLMRadialBlur` | `019e99be-41c0-7960-be4f-e9eb65d10a27` / Anscombe | Read `notes/OLMRadialBlur_RE.md`, C++/Python probes, Inner/EdgeFade refs and request JSON, decomp/disasm as needed. | Green vs red slices, Zoom/Rotation/Inner/EdgeFade IR facts, stop condition, one next action. |
| `OLMKiraKira` | `019e99be-59f1-7710-b08d-ed4963911ab1` / Goodall | Read `notes/OLMKiraKira_ASM_FACTS.md`, current C++/Python/OpenCV probes, single-ray request, decomp/disasm as needed. | Two-temp/all-ray facts, measured status, stop condition, one next action. |
| `OLMSmoother` / `OLMSmoother2` | `019e99be-719f-7171-b4a5-2e1cc1082dd9` / Schrodinger | Read `notes/OLMSmoother2_ASM_FACTS.md`, v1/v2 CLI and Mac bridge, no-key-grid request, Smoother refs. | Whether v1 is covered by v2 compatibility, measured status, no-key-grid unblocker, one next action. |

## Current Stop Conditions

- `OLMDirectionalBlur`: wait for
  `refs/reference_requests/directionalblur_context_scale_20260606.json` if
  render-context scale / premul / alpha ownership cannot be separated from the
  current opaque references.
- `OLMRadialBlur`: wait for
  `refs/reference_requests/radialblur_inner_size_variation_20260606.json` if
  Inner `+0x40` span/gate plane and Size Variation coupling remain ambiguous.
- `OLMKiraKira`: wait for
  `refs/reference_requests/kirakira_single_ray_20260606.json` if equal-ray,
  rotation-zero references cannot isolate ray order, angle mapping, helper
  scalar, or crop/placement behavior.
- `OLMSmoother2`: wait for
  `refs/reference_requests/smoother2_no_key_grid_20260606.json` if no-key v2
  residual cannot be assigned to class-plane firing, sample-plane choice,
  color-space handling, or writeback.

## Reusable Prompt Shape

Ask each sub-agent for:

1. Current best-supported algorithm IR checkpoints.
2. Exact measured status and the commands or notes that prove it.
3. Whether the stop condition still holds and which reference request unblocks
   it.
4. One next parent action that is backed by objdump/decomp/IR evidence.

