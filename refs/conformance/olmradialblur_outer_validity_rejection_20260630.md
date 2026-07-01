# OLMRadialBlur Outer Validity Rejection - 2026-06-30

Bounded rejection of the simplest outer caller-collapse interpretation using current local witness dumps plus imported Windows trace facts.

## Zoom `case_0009`

- Current local witness alpha: `1.0`
- Windows traced pre-writeback alpha: `0.9999999403953552`
- Bilinear alpha from current local binary valid bits: `0.44250500000000004`
- Windows final alpha byte: `254`
- Bilinear binary-validity alpha byte floor: `112`

Interpretation:

- The current local witness has two contributing cells with `valid=1` and two with `valid=0`.
- If AEX caller-collapse for this witness were just bilinear sampling of that current binary valid plane, the resulting alpha would be about `0.44250488` (`112/255`), not the Windows traced `0.99999994` (`254/255`).
- Therefore the surviving Zoom lane cannot be explained by direct bilinear sampling of the current local `0/1` preserved-validity proxy.

## tiny Rotation `case_0010`

- Current local bilinear validity alpha: `0.9999997`
- Current local sample RGBA: `[-0.00408606, -0.00408606, -0.00408606, 1]`
- Windows traced closest inverse-sampler RGBA: `[-0.004081939347088337, -0.004081939347088337, -0.004081939347088337, 1.0]`
- Windows final RGBA8: `[255, 255, 255, 255]`

Interpretation:

- All four current local contributing cells are already `valid=1`, so a validity-only collapse would keep alpha fully live.
- Even with that, both the current local sample and the closest traced Windows inverse-sampler return remain near-black while the final Windows pixel is exact white.
- Therefore the tiny Rotation residual is not solved by validity-only substitution either; it still points to upstream polar RGB / caller-collapse / substitute-path behavior.

## Bottom line

- `binary-validity -> final alpha` was already rejected at whole-frame level.
- This report strengthens the same point at witness level: the current local binary validity plane is not numerically compatible with the Windows Zoom alpha witness, and it is not sufficient to explain tiny Rotation either.
