# OLMKiraKira Reference Provenance Audit

- Case: `kk_vertical_len50_brightness1_strength100`
- Hotspot: `(934, 118)`
- Decision: `reference-export-or-witness-placement-pending`
- Reason: The primary hotspot now has three distinct in-tree facts: the canonical Windows Software reference PNG is 131, the current Mac compose-boundary witness and answered Windows traced writeback both say 144, and the archived BT.709 candidate PNG says 145. That means the remaining KiraKira hotspot is not a single compose-math disagreement; it is at least partly a provenance/export/witness-placement lane.
- Forbidden action: Do not retune BT.709, boxFilter, ray-helper, FUN_18114fd90 aggregation, merge-mode-1 screen compose, or final quantization from these hotspot artifacts alone.
- Next allowed action: Treat the traced hotspot algorithm lane as matched through current writeback, and only spend further effort here on canonical reference provenance, same-run export comparison, witness placement validation, or endgame control coverage.

## Artifact Hotspot Values

- canonical Windows reference PNG: `[131, 131, 131, 255]`
- archived BT.709 candidate PNG: `[145, 145, 145, 255]`
- current Mac compose-boundary witness: `[144, 144, 144, 255]`
- answered Windows traced hotspot: `[144, 144, 144, 255]`

## Pairwise Deltas

- archived candidate minus canonical reference: `[14, 14, 14, 0]`
- windows traced minus canonical reference: `[13, 13, 13, 0]`
- current Mac witness minus canonical reference: `[13, 13, 13, 0]`
- archived candidate minus windows traced: `[1, 1, 1, 0]`

## Role Matrix

- canonical reference == windows traced: `False`
- canonical reference == current Mac witness: `False`
- canonical reference == archived candidate: `False`
- windows traced == current Mac witness: `True`
- windows traced == archived candidate: `False`
- current Mac witness == archived candidate: `False`

## Reading

- The canonical reference PNG is not the same artifact as the current traced/writeback-aligned hotspot.
- The archived BT.709 candidate PNG is also not the same artifact as the current traced/writeback-aligned hotspot; it is one count brighter at the witness pixel.
- So this lane should stay parked away from compose retuning. The current evidence supports provenance/export or witness-placement investigation first.

