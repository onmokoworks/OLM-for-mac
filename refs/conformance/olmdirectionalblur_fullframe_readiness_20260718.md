# OLMDirectionalBlur Full-Frame Readiness Audit

Date: 2026-07-18
Scope: `OLMDirectionalBlur` front-only bounded lane only.
Policy: fail closed. This audit is allowed to prove readiness barriers, not to promote `AE exact`.

## Decision

- Overall: `blocked`.
- Bounded front-only host/world readiness: `True`.
- Full-frame local readiness: `False`.
- Mac AE validation readiness: `False`.

## Verified Facts

| Invariant | Status | Fact |
| --- | --- | --- |
| bounded angle pair actual-AEX equality | `pass` | Angle 0 and 45 both match the actual AEX exactly on the bounded typed-rowdriver differential. |
| bounded PF world / row mapping | `pass` | The bounded Iterate8 area and padded rowbytes mapping stay identical between actual AEX and typed detour. |
| rowdriver/helper ABI binding | `pass` | One real row enters the actual rowdriver and yields `16` helper calls with the expected buffer ownership. |
| Mac exact-path host adapter | `ok` | Live source-included probe still passes full/partial ROI checks and rejects eight non-exact gates. |
| natural actual populate callback | `pass` | The real populate callback is reached on the natural path and writes the expected source plane. |
| natural continuation after populate | `blocked` | The current natural-path checkpoint still stops before any downstream write, so the real full chain is not yet proven. |
| bounded natural writer oracle | `pass` | The bounded natural follow-up chain still matches the temporary production oracle exactly, but that is not a natural full render. |

## Remaining Invariants

- `natural_iterate8_continuation`: The natural path is still blocked before any downstream write after the actual populate callback. No artifact proves that a real render continues through rowdriver, normalization, rotate-back, and the output callback. Evidence: `refs/conformance/olmdirectionalblur_iterate8_continuation_transform_20260717.json`.
- `same-run_full_render_binding`: The bounded rowdriver/writer proofs are isolated and executable, but they are not yet shown to be the exact chain used by a natural full render on the residual lane. Evidence: `bounded proofs pass; natural continuation remains blocked`.

## FACT / INFERENCE

- FACT: the bounded rowdriver proof, row mapping proof, rowdriver/helper ABI proof, and live Mac exact-path adapter proof all passed again on this machine.
- FACT: the natural-path artifact is still blocked at `pre-render-return`; no downstream write was observed after the actual populate callback.
- INFERENCE: the missing boundary is no longer the typed rowdriver itself for the bounded lane. It is the natural full-render scheduling/continuation that must feed that proven chain in a real render.
- INFERENCE: a broad full-frame or Mac AE validation would still be ambiguous today, because a mismatch could come from the unproven natural host/world continuation rather than from the proven bounded rowdriver path.

## Reproduction

`python3 tools/emulation/audit_olmdirectionalblur_fullframe_readiness_20260718.py`
