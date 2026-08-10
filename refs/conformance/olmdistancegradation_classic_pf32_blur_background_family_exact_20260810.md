# OLMDistanceGradation PF32 whole-owner blur family

Status: `exact`, actual-AEX whole-owner execution to production.

Eight cells cross Constant/Linear, Background off/on, and Blur Mode 2/3 for
Inside/RGB, threshold 4, invert on, Blur Size 1, and full resolution. The
fixture is 17x11 PF32 with a short transparent island, input/output rowbytes
280/288, distinct gradation/background colors, and `0xA5` padding.

Every cell naturally completes actual `FUN_181172a10`, including parameter
checkout, both ColorParam calls, `FUN_181174760`, legacy cvSmooth, final owner
matrix, and output checkout. Production matches all 3,168 bytes per cell with
unchanged padding. The source, pre-blur field, post-blur field, and final active
hashes are pinned in the focused test.

The owner establishes four real equivalence classes:

| Interpolation | Blur Mode | Blurred field SHA-256 | Active output SHA-256 |
|---|---:|---|---|
| Constant | 2 box | `f4696ac84b3cd30da637a7d2ebf965cb29e67256be66ada68b7d85ed9be4d21a` | `c71276a654368e18704799e9f19b35f345f3d45f6357814806e2ec929a1b753d` |
| Constant | 3 Gaussian | `f67b7cbcdf3e5380c971f5ea91dd5a23da6c6a57527c468f8dcfe096d3b4989e` | `efe9cfc9932fc0f1f8e6d77e924eb0a9b8d227aad84a491bdd31071e1d736b9d` |
| Linear | 2 box | `a664ac6185774955ed256cddc55a45b5161f07669ff16b5d3b53dc7a4ffab901` | `a79b3e5a478836128944d1c189ceb2a26b8457808e43ccc0ce58c17426b25e5d` |
| Linear | 3 Gaussian | `5666b13a5f368823107fb0af58a23d3f1dccde2b3457dc895c38d150f68236ec` | `b3c5dd901d494c54801438132bd202a31b959cf1c425cacbf2793205d7247f42` |

Background off/on is intentionally identical in each class even though the
owner checks out distinct colors. The PF32 blur owner exports blurred field to
A/R/G and the pre-blur field to B. Arbitrary-float box accumulation and the
Gaussian 3-tap symmetric operation order are independently observable here.

Excluded: other sizes/geometries, Outside/Both, Layer mode, PF8/PF16
extrapolation, host resize, AE import/export, and PF32 SmartRender.
