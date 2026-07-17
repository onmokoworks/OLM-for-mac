# OLMDistanceGradation 16bpc Layer residual discriminator

Status: `probe_required`. No production source was edited.

The current Mac AE artifact is a narrow residual: case `0012` has 39 changed
pixels and case `0014` has 35; every changed sample is RGB `-1`, with alpha
exact. The bounded PF16 AEX/source fixture already proves the current
truncating PF16 store shape on a non-degenerate input, so a global rounding
patch is not justified.

## Smallest probe

Run the existing Mac AE debug hooks on two failing pixels and one adjacent
exact control per case:

| Case | failing pixel | exact control |
| --- | --- | --- |
| `0012` | `(165,10)` | `(164,10)` |
| `0014` | `(1035,1)` | `(1034,1)` |

The generated commands are in the companion JSON. They capture `field_debug`
and `shade_debug`; the exported frame must be joined to the same run.

Required chain at all four points: input PF16 words, normalized source,
`field_x`/`d_alpha`, compose float, PF16 words immediately after store, and
same-run exported true16.

## Decision

Do not patch production yet. A source/field patch is warranted only if the
failing point diverges before store while its control remains aligned. If the
Mac PF16 store already equals the Windows target, this is an AE export boundary
and no Mac source patch is supported. If only the store differs, isolate the
typed store path; do not change global rounding without both case families.
