# DistanceGradation case_0027 observed X probe - 2026-06-26

Observed `X` is reconstructed from `layer_no_bg` alpha, because for
`In/Out=Both` and `Use Background Color=0`, the current Mac implementation
writes `out_a = X`.

## Model scores

| Model | MAE | RMSE | Corr |
| --- | ---: | ---: | ---: |
| `current_max_nopow` | 0.266455 | 0.415289 | 0.875063 |
| `current_max_pow` | 0.388227 | 0.564748 | 0.755178 |
| `inside_nopow` | 0.667464 | 0.791711 | 0.299932 |
| `inside_pow` | 0.715173 | 0.829395 | 0.349493 |
| `outside_nopow` | 0.593677 | 0.731535 | 0.365168 |
| `outside_pow` | 0.667739 | 0.787736 | 0.396396 |

## Witnesses

| Point | Observed X | current_max_nopow | current_max_pow | outside_nopow | outside_pow | Reading |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `(3,0)` | 1.000000 | 0.923077 | 0.812285 | 0.923077 | 0.812285 | observed field stays much closer to 1 than the current model |
| `(14,0)` | 0.976562 | 0.076923 | 0.001278 | 0.076923 | 0.001278 | observed field stays much closer to 1 than the current model |
| `(397,281)` | 0.984375 | 0.230769 | 0.022178 | 0.230769 | 0.022178 | observed field stays much closer to 1 than the current model |
| `(438,1)` | 0.945312 | 0.006329 | 0.000002 | 0.000000 | 0.000000 | observed field stays much closer to 1 than the current model |
| `(15,0)` | 0.945312 | 0.006329 | 0.000002 | 0.000000 | 0.000000 | observed field stays much closer to 1 than the current model |
| `(16,0)` | 0.945312 | 0.006329 | 0.000002 | 0.000000 | 0.000000 | observed field stays much closer to 1 than the current model |
| `(17,0)` | 0.945312 | 0.006329 | 0.000002 | 0.000000 | 0.000000 | observed field stays much closer to 1 than the current model |

## Conclusion

- The Mac AE probe does not support the earlier `compose/background-branch is dead` hypothesis.
- `layer_bg` and `layer_no_bg` differ materially when read as true 16-bit PNGs, and `grad_bg` / `grad_no_bg` also differ in alpha and RGB once decoded natively.
- The active mismatch for `case_0027` is upstream: the observed field `X` extracted from `layer_no_bg` alpha stays much closer to `1.0` than the current distance model predicts at key witness pixels.
- So the next correction target is field prep / normalization / threshold ownership, not the final RGB compose branch.
