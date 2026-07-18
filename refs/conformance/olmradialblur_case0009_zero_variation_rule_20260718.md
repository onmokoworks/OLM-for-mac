# OLMRadialBlur case0009 zero-variation rule

Status: **pass**, static local conformance only.

The 20260604 RadialBlur manifest identifies `case_0009` as Zoom (`Blur Type=1`),
outer strength `1717`, inner strength `0`, Size Variation `0`, Noise Variation
`0`, and Noise Type `1`.

The decomp proves that Size Variation is scaled by `0.01` and enables the
distance-transform map only when the scaled value exceeds `0.0001`. The disabled
branch fills the size map with `1.0`. The recorded source-space formula is:

```text
size_factor = normalized_size_map * SV + (1 - SV)
span_factor = (NV * noise + (1 - NV)) * size_factor
effective_len = int(base_len * span_factor)
```

Therefore, for case0009, `SV=0` and `NV=0` imply `size_factor=1.0`,
`span_factor=1.0`, and `effective_len=int(base_len)`. Noise generation is not
claimed absent: Noise Type 1 can still enter the generator, but its value is
semantically masked by `NV=0` in this bounded scatter rule.

Evidence: `decomp/OLMRadialBlur.aex.c.txt` lines 4031-4074, 3528-3564,
3594-3620, and `notes/OLMRadialBlur_ASM_FACTS.md` lines 94-118.

This artifact does not compare PNGs, touch PID59481, read or write checkpoint
state, or authorize a production implementation change.
