# OLMRadialBlur case_0009 Alpha A/B

Date: 2026-07-12

## Accepted facts

- The corrected CDB runner hit `OLMRadialBlur+0x5e5b/+0x5e6d` in both AE25
  and AE26.
- Windows `(7,0)` returned sampler words
  `3da8cc33 3c706e30 3c706e30 3f7fffff`; truncation maps alpha to `254`.
- Baseline Mac AE26.3 case_0009 remains `max=1`, `31119/2073600` differing
  pixels. Mac debug points `(6,0)/(7,0)/(8,0)/(24,0)` have four final-polar
  cell alphas and validities equal to `1.0`.
- The returned request did not arm its contracted `+0x5d99` breakpoint. It is
  not evidence that the boundary is dead.

## Rejected A/B candidates

| Candidate | Mac AE result | Decision |
| --- | --- | --- |
| writer truncation only | `max=1`, `536668` pixels; `(7,0)` stayed 255 | reject |
| float32 final-bilinear order with epsilon | `max=1`, `31119` pixels | inert |
| float32 final-bilinear order plus truncation | `max=1`, `40584` pixels; `(7,0)` stayed 255 | reject |
| simple weight denominator or weighted-alpha propagation plus truncation | `max=1`, `536668` pixels; `(7,0)` stayed 255 | reject |
| repeat raw-alpha sampler plus float accumulation and truncation | `max=1`, `536668` pixels; `(7,0)` stayed 255 | reject |
| AEX-order float32 forward sampler, existing writer epsilon | `max=1`, `31119` pixels; identical to baseline and `(7,0)` stayed 255 | inert / reject |
| AEX-order float32 forward sampler plus writer truncation | `max=1`, `536668` pixels; `(7,0)` stayed 255 | reject |
| target-cell one-sided float32 Gaussian replay, existing sampler | `max=1`, `31119` pixels; target cells and output unchanged | inert / reject |
| AEX-order repeat sampler plus target-cell one-sided float32 Gaussian replay | `max=1`, `31119` pixels; target cells remained exactly `1.0` | inert / reject |

Every candidate was built, installed, rendered through Mac AE26.3, compared
against the same case_0009 expected PNG, then removed. Production source and
the installed plug-in were restored to the pre-A/B state.

## Remaining boundary

The unresolved value is the full-frame AEX final-polar alpha/validity cell
state before `FUN_180009d80`. The next RadialBlur request must actually arm
`OLMRadialBlur+0x5d99`, bind the `+0x38/+0x50/+0x4210/+0x4218` plane pointers,
and retain target call coordinates for `(7,0)/(8,0)/(24,0)`. Do not retry a
writer-only or global alpha formula.

Static ownership is now narrower. At `0x180005ce0..0x180005d80`, the final
polar RGB is normalized from `context+0x4210`, while alpha is copied directly
from `context+0x4218`; `0x180005d99` starts the output-coordinate loop and
`0x180005e68` calls `FUN_180009d80`. The `+0x4218` plane is written by
`FUN_18000b150`: its alpha is a float32 Gaussian weighted value
`fVar30 / fVar31`, accumulated in the binary's explicit center/left/right
order. The Mac large-radius path instead obtains alpha through a double/FFT
convolution. The next local lane is therefore a one-cell replay of
`FUN_18000b150` using captured source alpha, scale, and table values; the next
Windows witness must bind those inputs as well as the final plane. Production
source and the installed plug-in were restored after both A/B runs.

The target-cell replays covered final-polar rows `1047..1050` and radii
`1075..1100`, including all four cells consumed by output `(7,0)`:
`(1095/1096,1047/1048)`. Replacing FFT alpha there with fixed-span one-sided
float32 accumulation was inert with both the current forward sampler and the
reconstructed repeat-border sampler. The remaining producer fact is therefore
the per-cell scale/span input `fVar28` consumed by `FUN_18000b150`, which
changes left/right limits and Gaussian table indices. The next Windows witness
should capture that scalar plane and the selected indices for the four cells.

The bounded cell-set sweep over angle/radius offsets `-3..+3` also found no
exact candidate. Every candidate that emitted 254 at all three Windows target
positions `[6,7,12]` produced at least eight false-positive 254 positions.
Coordinate bias is therefore not an implementation candidate. The prepared
full-frame package now captures the target-row `FUN_18000b150` ABI and scale/
source-alpha words together with the final-plane witness; it is intentionally
not staged while DirectionalBlur owns the NAS queue.
