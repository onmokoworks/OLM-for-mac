# OLMColorKey 16bpc case_0009 analysis

Status: diagnostic.

This report focuses on the remaining 16bpc Mac AE residual after the Force Lower Precision fix.

- Candidate vs Windows reference diff: `12597` px
- Candidate extra-only pixels: `12597` px
- Candidate missing pixels: `0` px
- Candidate extra bbox: `[0, 0, 1919, 1079]`

## Parameters

- Color Space: `3` (Lab76)
- Force Lower Precision: `3`
- Per Color / Per Component: `1` / `1`
- Edge Thin Amount / Distance Type: `25` / `2`
- Edge Blur Amount / Distance Type / Direction: `0` / `1` / `3`

## Naive models

| Denominator | Hit count | Keep count | Diff px | Extra px | Missing px |
| --- | ---: | ---: | ---: | ---: | ---: |
| 65535.0 | 8873 | 569538 | 80592 | 59503 | 21089 |
| 32768.0 | 4595 | 691200 | 189628 | 174852 | 14776 |
| 32767.0 | 4595 | 691200 | 189628 | 174852 | 14776 |

## Seed / Dilate sweep

| Model | Diff px | Extra px | Missing px | Keep px |
| --- | ---: | ---: | ---: | ---: |
| hit-taxicab-<=25 | 80592 | 59503 | 21089 | 569538 |
| hit-taxicab-<26 | 80592 | 59503 | 21089 | 569538 |
| boundary-clamp-taxicab-<=25 | 80592 | 59503 | 21089 | 569538 |
| boundary-clamp-taxicab-<26 | 80592 | 59503 | 21089 | 569538 |
| boundary-outside-taxicab-<=25 | 80592 | 59503 | 21089 | 569538 |
| boundary-outside-taxicab-<26 | 80592 | 59503 | 21089 | 569538 |
| binary-diamond25 | 80592 | 59503 | 21089 | 569538 |
| hit-taxicab-<=26 | 87488 | 41970 | 45518 | 527576 |
| boundary-clamp-taxicab-<=26 | 87488 | 41970 | 45518 | 527576 |
| boundary-outside-taxicab-<=26 | 87488 | 41970 | 45518 | 527576 |
| hit-taxicab-<25 | 114894 | 99447 | 15447 | 615124 |
| boundary-clamp-taxicab-<25 | 114894 | 99447 | 15447 | 615124 |

## Conclusion

- The residual is not an Edge Blur blend issue.
- The current Mac AE candidate is already much closer to Windows than the naive Lab76+dilate reconstruction.
- A `32768` or `32767` normalization denominator is not the missing fix; it makes the naive model dramatically worse.
- Straightforward seed-world variants also fail badly; the best of them still differs by `80592px`.
- The remaining gap is likely a narrower seed-world or local dilate-ownership rule inside the real plug-in path.

## Largest extra components

| Area | x0 | y0 | x1 | y1 |
| ---: | ---: | ---: | ---: | ---: |
| 1176 | 1088 | 124 | 1133 | 174 |
| 696 | 1195 | 761 | 1228 | 811 |
| 633 | 351 | 78 | 388 | 112 |
| 588 | 1488 | 30 | 1519 | 74 |
| 534 | 651 | 929 | 693 | 960 |
| 343 | 1226 | 447 | 1251 | 473 |
| 331 | 1756 | 216 | 1785 | 256 |
| 300 | 159 | 125 | 200 | 152 |
| 290 | 29 | 776 | 52 | 799 |
| 281 | 1378 | 932 | 1402 | 980 |
| 275 | 1371 | 903 | 1393 | 925 |
| 249 | 1012 | 33 | 1057 | 56 |
