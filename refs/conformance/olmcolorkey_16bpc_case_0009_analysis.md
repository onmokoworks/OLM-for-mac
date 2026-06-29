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
| 65535.0 | 10582 | 531124 | 0 | 0 | 0 |
| 32768.0 | 5269 | 628713 | 111065 | 104327 | 6738 |
| 32767.0 | 5269 | 628713 | 111065 | 104327 | 6738 |

## Candidate-model epsilon sweep

| Key epsilon | Hit count | Candidate-model diff px | Candidate extra px | Candidate missing px |
| ---: | ---: | ---: | ---: | ---: |
| 0.0 | 8872 | 0 | 0 | 0 |
| 1.52587890625e-05 | 8886 | 54 | 0 | 54 |
| 0.00196078431372549 | 10582 | 12597 | 0 | 12597 |
| 0.00392156862745098 | 12362 | 26458 | 0 | 26458 |
| 0.00784313725490196 | 29770 | 65487 | 0 | 65487 |

## Seed / Dilate sweep

| Model | Diff px | Extra px | Missing px | Keep px |
| --- | ---: | ---: | ---: | ---: |
| hit-taxicab-<=25 | 0 | 0 | 0 | 531124 |
| hit-taxicab-<26 | 0 | 0 | 0 | 531124 |
| boundary-clamp-taxicab-<=25 | 0 | 0 | 0 | 531124 |
| boundary-clamp-taxicab-<26 | 0 | 0 | 0 | 531124 |
| boundary-outside-taxicab-<=25 | 0 | 0 | 0 | 531124 |
| boundary-outside-taxicab-<26 | 0 | 0 | 0 | 531124 |
| binary-diamond25 | 0 | 0 | 0 | 531124 |
| hit-taxicab-<=26 | 39737 | 0 | 39737 | 491387 |
| boundary-clamp-taxicab-<=26 | 39737 | 0 | 39737 | 491387 |
| boundary-outside-taxicab-<=26 | 39737 | 0 | 39737 | 491387 |
| hit-taxicab-<25 | 43617 | 43617 | 0 | 574741 |
| boundary-clamp-taxicab-<25 | 43617 | 43617 | 0 | 574741 |

## Source-seed sweep

| Model | Diff px | Extra px | Missing px | Keep px |
| --- | ---: | ---: | ---: | ---: |
| source-nonblack-taxicab-<=25 | 259652 | 0 | 259652 | 271472 |
| source-nonblack-taxicab-<26 | 259652 | 0 | 259652 | 271472 |
| source-nonblack-taxicab-<25 | 278372 | 28932 | 249440 | 310616 |
| source-nonblack-taxicab-<=26 | 294797 | 0 | 294797 | 236327 |
| source-black-opaque-taxicab-<25 | 399970 | 86 | 399884 | 131326 |
| source-black-opaque-taxicab-<=25 | 402979 | 29 | 402950 | 128203 |
| source-black-opaque-taxicab-<26 | 402979 | 29 | 402950 | 128203 |
| source-black-opaque-euclidean-<25 | 403732 | 8 | 403724 | 127408 |
| source-nonblack-euclidean-<25 | 403961 | 832 | 403129 | 128827 |
| source-black-opaque-euclidean-<=25 | 405308 | 7 | 405301 | 125830 |
| source-black-opaque-taxicab-<=26 | 405992 | 6 | 405986 | 125144 |
| source-nonblack-euclidean-<=25 | 406498 | 0 | 406498 | 124626 |
| source-black-opaque-euclidean-<26 | 407136 | 0 | 407136 | 123988 |
| source-black-opaque-euclidean-<=26 | 408404 | 0 | 408404 | 122720 |
| source-black-opaque-chessboard-<25 | 411855 | 4 | 411851 | 119277 |
| source-black-opaque-chessboard-<=25 | 415165 | 0 | 415165 | 115959 |
| source-black-opaque-chessboard-<26 | 415165 | 0 | 415165 | 115959 |
| source-black-opaque-chessboard-<=26 | 418370 | 0 | 418370 | 112754 |
| source-nonblack-euclidean-<26 | 426193 | 0 | 426193 | 104931 |
| source-nonblack-euclidean-<=26 | 428682 | 0 | 428682 | 102442 |
| source-nonblack-chessboard-<25 | 455775 | 495 | 455280 | 76339 |
| source-nonblack-chessboard-<=25 | 470658 | 0 | 470658 | 60466 |
| source-nonblack-chessboard-<26 | 470658 | 0 | 470658 | 60466 |
| source-nonblack-chessboard-<=26 | 483152 | 0 | 483152 | 47972 |
| source-opaque-taxicab-<25 | 531124 | 0 | 531124 | 0 |
| source-opaque-taxicab-<=25 | 531124 | 0 | 531124 | 0 |
| source-opaque-taxicab-<26 | 531124 | 0 | 531124 | 0 |
| source-opaque-taxicab-<=26 | 531124 | 0 | 531124 | 0 |
| source-opaque-chessboard-<25 | 531124 | 0 | 531124 | 0 |
| source-opaque-chessboard-<=25 | 531124 | 0 | 531124 | 0 |
| source-opaque-chessboard-<26 | 531124 | 0 | 531124 | 0 |
| source-opaque-chessboard-<=26 | 531124 | 0 | 531124 | 0 |
| source-opaque-euclidean-<25 | 531124 | 0 | 531124 | 0 |
| source-opaque-euclidean-<=25 | 531124 | 0 | 531124 | 0 |
| source-opaque-euclidean-<26 | 531124 | 0 | 531124 | 0 |
| source-opaque-euclidean-<=26 | 531124 | 0 | 531124 | 0 |

## Conclusion

- The residual is not an Edge Blur blend issue.
- The binary-grounded `Lab76 hit + taxicab <=25` reconstruction is exact against the Windows reference.
- A `32768` or `32767` normalization denominator is not the missing fix; it makes the naive model dramatically worse.
- The current Mac AE candidate matches the old threshold mapping; the current-AEX Lab76 per-component mapping expands the seed enough to remove the `12597px` candidate-kept / Windows-removed residual.
- CDB now confirms the live current-AEX path really has `Force Lower Precision=3`, `amount=25`, `distance_type=2`, and `dist <= amount` in the `+0x9000` positive Edge Thin path.
- The 2026-06-28 raw CDB log proves `(1110,149)` uses Windows `dist=2.0` and is copied to matte word `0x8000`; with the binary-grounded Lab76 mapping, the local exported-PNG model also puts that witness at distance `2`.
- No further Windows trace is needed for this case unless the Mac AE re-render after the comparator fix still differs.

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

## Representative witness pixels

| Area | x | y | Before A | Candidate A | Reference A | Hit65535 | Hit32768 | Dist->hit | Dist->boundary(clamp) |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| 1176 | 1110 | 149 | 65535 | 65535 | 0 | False | False | 2 | 2 |
| 696 | 1213 | 785 | 65535 | 65535 | 0 | False | False | 8 | 8 |
| 633 | 369 | 95 | 65535 | 65535 | 0 | False | False | 11 | 11 |
| 588 | 1503 | 57 | 65535 | 65535 | 0 | False | False | 8 | 8 |
| 534 | 668 | 945 | 65535 | 65535 | 0 | False | False | 9 | 9 |
| 343 | 1238 | 460 | 65535 | 65535 | 0 | False | False | 8 | 8 |
| 331 | 1770 | 236 | 65535 | 65535 | 0 | False | False | 11 | 11 |
| 300 | 181 | 138 | 65535 | 65535 | 0 | False | False | 12 | 12 |

## Extra-pixel proximity summary

| Seed family | Min dist | Max dist | Mean dist | Extra px within dist<=25 |
| --- | ---: | ---: | ---: | ---: |
| nonblack | 0 | 25 | 18.7095 | 12597 |
| opaque | 0 | 0 | 0.0000 | 12597 |
| black_opaque | 0 | 26 | 0.1554 | 12596 |
| lab76_hit_65535 | 0 | 25 | 19.8347 | 12597 |
| red_dominant | 0 | 1205 | 385.5941 | 217 |
