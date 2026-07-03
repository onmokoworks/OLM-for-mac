# OLMKiraKira Source-Candidates Audit

- Case: `kk_vertical_len50_brightness1_strength100`
- Witness: `(934, 118)`
- Source: `mac/OLMKiraKira/OLMKiraKira.cpp`
- Hotspot decision: `hotspot-proof-shifted-to-reference-or-witness-placement`
- Provenance decision: `reference-export-or-witness-placement-pending`

## Lane Summary

- canonical reference hotspot: `[131, 131, 131, 255]`
- windows traced hotspot: `[144, 144, 144, 255]`
- current Mac witness hotspot: `[144, 144, 144, 255]`
- archived BT.709 candidate hotspot: `[145, 145, 145, 255]`

## Non-Source Gate

- Required before source patch: Same-run export or witness-placement evidence that contradicts the current traced hotspot agreement.
- Why: The current in-tree facts already split into reference/export provenance or witness-placement: Windows traced hotspot == current Mac witness == 144, while canonical reference is 131.

## Source Candidates

| Rank | Site | Function | Line | Why live | Allowed change shape |
| --- | --- | --- | ---: | --- | --- |
| 1 | `render_typed_merge_mode_1_screen_compose` | `RenderTyped` | `456` | This is the first in-source place to reopen only if a future same-run export/reference witness explicitly contradicts the current traced hotspot agreement through compose and sampled writeback. | single-witness merge-mode-1 compose or writeback boundary only |
| 2 | `add_colored_union_glow_aggregation` | `AddColoredUnion` | `366` | Aggregation remains second-order only. Reopen it only if a later witness proves the same-run export disagrees before final compose, not because the canonical reference PNG differs from the traced hotspot. | typed per-ray aggregation contradiction only; no broad brightness/gain retune |
| 3 | `params_setup_highlight_ramp_control_surface` | `ParamsSetup` | `615` | The remaining KiraKira work may still need control-surface coverage because Windows manifests expose ramp/highlight controls. But that is a schema/endgame-coverage lane, not a hotspot compose fix. | parameter/control-surface coverage only; not a hotspot pixel-math patch |

## Decision Ladder

1. If no new same-run export/reference contradiction exists -> Do not patch OLMKiraKira source for the hotspot lane; keep work in provenance/export or witness-placement validation.
2. If a future witness says compose/writeback diverges on the same run and same hotspot -> Reopen RenderTyped merge-mode-1 screen compose at the hotspot before touching upstream aggregation.
3. If the future witness proves the mismatch already exists before final compose -> Only then reopen AddColoredUnion or upstream per-ray aggregation.
4. If remaining work is about missing Windows-visible controls rather than the hotspot pixel -> Treat highlight/ramp parameters as a separate schema/endgame-coverage lane.

## Forbidden Actions

- Do not retune BT.709, boxFilter, ray-helper choreography, or global brightness gain from the current hotspot evidence.
- Do not promote a broad final-quantization tweak from the canonical-reference mismatch alone.
- Do not treat highlight/ramp control coverage as proof that the hotspot compose math is wrong.

