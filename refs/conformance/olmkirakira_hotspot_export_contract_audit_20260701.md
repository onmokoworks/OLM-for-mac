# OLMKiraKira Hotspot Export Contract Audit

- Plug-in: `OLMKiraKira`
- Case: `kk_vertical_len50_brightness1_strength100`
- Hotspot: `(934, 118)`
- Decision: `awaiting-same-run-export-or-witness-placement-proof`
- Reason: The traced hotspot already agrees with the current Mac compose-boundary witness at 144, while the canonical reference PNG is 131. Without a same-run Windows export or explicit witness-placement/endgame-control proof, this remains a provenance lane.
- Next step: Import a same-run Windows current-AEX export for the hotspot case, or a proof artifact that shows the traced hotspot is not the final export class.

## Artifact Hotspot Values

- canonical Windows reference PNG: `[131, 131, 131, 255]`
- archived BT.709 candidate PNG: `[145, 145, 145, 255]`
- current Mac compose-boundary witness: `[144, 144, 144, 255]`
- answered Windows traced hotspot: `[144, 144, 144, 255]`
- same-run Windows current export: `-`

## Required Windows Payload

- same-run exported PNG file for the hotspot case
- AE version
- project renderer metadata
- parameter/property snapshot for the same case
- statement whether the export comes from the same current-AEX build/path as the trace run
- if export and trace differ, any witness-placement or endgame-control note explaining the split

## Forbidden Moves

- retune BT.709 seed
- retune boxFilter or ray-helper choreography from hotspot PNGs
- promote a broad compose or final-quantization rewrite from the canonical 131 mismatch alone
- treat missing endgame controls as proof that hotspot compose math is wrong
