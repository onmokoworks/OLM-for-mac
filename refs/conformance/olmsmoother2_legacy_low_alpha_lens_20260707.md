# OLMSmoother2 Legacy Low-Alpha Lens - 2026-07-07

## Verdict

FACT: The OLMDistanceGradation-style `alpha > 1.5/255` source-mask ownership rule does not explain the two remaining OLMSmoother2 legacy witnesses.

INFERENCE: The two witnesses are still producer/path divergences around c280/cce0 and the cardinal6 e170-f270-e3a0 chain, but the observed evidence points away from 1-code alpha fringe ownership. The Mac-side 1.5/255 alpha lens leaves both witness pixels unchanged and worsens total residual mean.

## Input 5x5 Alpha

Command:

```sh
python3 - <<'PY'
from pathlib import Path
from PIL import Image
import numpy as np
base=Path('refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference')
cases=[('0004','legacy_case_0004_current_aex',1903,519),('0012','legacy_case_0012_gamma5_red_blue_current_aex',91,841)]
for short,stem,x,y in cases:
    p=next(base.glob(f'*{stem}_before_effects.png'))
    arr=np.asarray(Image.open(p).convert('RGBA'))
    print('CASE', short, 'input_path', p)
    for yy in range(y-2,y+3):
        for xx in range(x-2,x+3):
            rgba=[int(v) for v in arr[yy,xx]]
            print(f'[{xx-x},{yy-y}] [{xx},{yy}] rgba={rgba} alpha={rgba[3]}')
PY
```

Output excerpt:

```text
CASE 0004 input_path refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference/smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0004_current_aex_before_effects.png
[2,-2] [1905,517] rgba=[0, 0, 0, 2] alpha=2
[0,0] [1903,519] rgba=[255, 255, 255, 255] alpha=255

CASE 0012 input_path refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference/smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png
[1,-2] [92,839] rgba=[1, 1, 1, 18] alpha=18
[2,-1] [93,840] rgba=[1, 1, 1, 16] alpha=16
[2,2] [93,843] rgba=[1, 1, 1, 18] alpha=18
[0,0] [91,841] rgba=[255, 255, 255, 255] alpha=255
```

FACT: case 0004 has a low-alpha input fringe at alpha=2 in the 5x5 window. case 0012 has low-alpha input fringes at alpha=16/18. Neither center input pixel is low-alpha; both centers are alpha=255 before key processing.

INFERENCE: A strict `1.5/255` lens can only affect alpha code 0 or 1. It cannot directly remove the observed alpha=2,16,18 input fringe pixels.

## Mac Path Evidence

FACT: Current Mac class-plane generation uses color distance with only exact zero alpha special-casing:

```cpp
// mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp
if (a.a == 0.0f && b.a == 0.0f) return 0.0f;
...
return maxv + std::fabs(a.a - b.a);
```

FACT: Class bytes are produced by `color_dist(...) >= threshold`; the threshold is `smooth_range / 100 + 0.001`.

FACT: Polygon/key predicates consume class bytes, not float alpha thresholds. `win_e170` reads three class bytes and tests `!= 0`; `win_leaf_f270` emits unless `c == 4`, then calls `win_e3a0`.

Trace commands:

```sh
cli/OLMSmoother2/olmsmoother2_cli --input refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference/smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0004_current_aex_before_effects.png --params refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params/smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0004_current_aex.json --output /tmp/olms2_trace_0004.png --trace-pixel 1903,519
cli/OLMSmoother2/olmsmoother2_cli --input refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/reference/smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png --params refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params/smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0012_gamma5_red_blue_current_aex.json --output /tmp/olms2_trace_0012.png --trace-pixel 91,841
```

Output excerpt:

```text
trace class_threshold mode=0 field=2 threshold=0.02100000 enable_key=1 invert_key=0 smooth_range=2 key_pred=1
trace build_polygon x=1903 y=519 idx=208 c=ffffffff eR0=1 bSW=1 bSE=0 uVar7=1 bits=0,0,0,0,0
trace neighborhood sample (1903,519)=1.00000000,1.00000000,1.00000000,0.00000000 class=ffffffff
trace build_polygon_done x=1903 y=519 idx=208 count=0
trace cce0_exit_passthrough out=1.00000000,1.00000000,1.00000000,0.00000000

trace class_threshold mode=0 field=88 threshold=0.88099998 enable_key=1 invert_key=0 smooth_range=88 key_pred=1
trace build_polygon x=91 y=841 idx=105 c=00ff00ff eR0=0 bSW=0 bSE=0 uVar7=0 bits=2,0,0,8,1
trace cardinal6 desc=(91,841,1,91,843,5) key=50 count_before=0
trace e170 p2=(91,841,1,91,843,5) bits Axy-1=1 R x-1y=0 Axy=0 -> c=2
trace f270 c=2 p3=1 extra_n=0.40000001 count_before=0
trace append src=(91,840) dst_center=(91,841) rgba=(0.99106717,0.99106717,0.99106717,0.99607843) w=0.35632184 before_count=0
trace cce0_after_b120 out=0.99106723,0.99106723,0.99106723,0.35492450
```

FACT: case 0004 Mac center is already key-filtered to alpha=0 and c280 returns polygon count 0. case 0012 Mac center is alpha=0, but cardinal6/e170/f270/e3a0 appends source `(91,840)` with alpha about 0.996, not a low-alpha fringe.

## Decomp Backing

FACT: `FUN_18000b2b0 @ 18000b2b0` has only exact-zero alpha exclusion:

```text
6560 fVar2 = 0.0;
6561 if ((param_1[3] != 0.0) || (param_2[3] != 0.0)) {
...
6579 fVar2 = fVar2 + (float)((uint)(param_1[3] - param_2[3]) & DAT_180022710);
```

FACT: `FUN_18000ae10 @ 18000ae10` compares color distance to threshold, not to a low-alpha threshold:

```text
6374 fVar15 = (float)*(int *)(param_5 + 0x1c) / DAT_180022dd0;
6383 fVar15 = fVar15 + _DAT_180022db0;
6391 fVar16 = FUN_18000b2b0(...);
6392 bVar2 = fVar15 <= fVar16;
6402 fVar14 = FUN_18000b2b0(...);
6403 bVar3 = fVar15 <= fVar14;
```

FACT: `FUN_18000c280 @ 18000c280` consumes class bytes by zero/nonzero tests:

```text
7389 local_1b5 = *(char *)(...);
7390 local_1b6 = *(char *)(...);
7391 local_1b7 = *(char *)(...);
7392 local_1b8 = *(char *)(...);
7396 uVar9 = (uint)(*(char *)(...) == '\0');
7405 bVar15 = *(char *)(...) != '\0';
7408 bVar16 = *(char *)(...) != '\0';
7427 switch((iVar3 + uVar9 + ((bVar16 ^ 1) + uVar7 * 2) * 4) * 0x10 + ...)
```

FACT: `FUN_18000cce0 @ 18000cce0` gates only on c280 polygon count:

```text
7908 FUN_18000c280(...);
7909 if (local_58 != 0xffffffffffffffff) {
7917   if (local_58 != 0) {
7922     FUN_18000bb10(...);
7926     FUN_18000c0d0(...);
7929     FUN_18000ab00(...);
7932     FUN_18000b120(...);
```

FACT: `FUN_18000e170 @ 18000e170` and `FUN_18000e3a0 @ 18000e3a0` also show zero/nonzero class or weight tests, not low-alpha ownership:

```text
8769 return (-(*(char *)(...) != '\0') & 2U) + (-(*(char *)(...) != '\0') & 4U) + (*(char *)(...) != '\0');
8856 if (fVar2 != 0.0) {
8859   uVar1 = FUN_1800104d0(param_1,&local_res8,fVar2);
```

INFERENCE: No decomp-backed comparison equivalent to `alpha > 1.5/255` was found in class-plane generation, c280 polygon selection, cce0 fallback, or the e170-f270-e3a0 append chain. The only alpha participation comparison found is exact `!= 0.0` in `FUN_18000b2b0`.

## Trial Measurement

Temporary change tested:

```cpp
const float LOW_ALPHA_LENS = 1.5f / 255.0f;
float aa = (a.a <= LOW_ALPHA_LENS) ? 0.0f : a.a;
float ba = (b.a <= LOW_ALPHA_LENS) ? 0.0f : b.a;
```

Baseline command:

```sh
python3 - <<'PY'
# runs refs/scripts/run_reference_test.py against the 9 current legacy residual cases,
# then sums reports/diff.csv mean_diff and reads the two witness pixels
PY
```

Baseline output:

```text
mean_sum=0.058945
legacy_case_0004_current_aex: max=113 mean=0.004453487 nz%=0.214843750
legacy_case_0012_gamma5_red_blue_current_aex: max=91 mean=0.015055941 nz%=0.186101466
legacy_case_0004_current_aex witness (1903,519) ref=[103, 103, 103, 113] cand=[0, 0, 0, 0]
legacy_case_0012_gamma5_red_blue_current_aex witness (91,841) ref=[0, 0, 0, 0] cand=[90, 90, 90, 91]
```

Temporary low-alpha lens command:

```sh
refs/scripts/build_olmsmoother2_cli.sh
python3 - <<'PY'
# same 9-case run_reference_test.py measurement as baseline
PY
```

Temporary low-alpha lens output:

```text
mean_sum=0.059653
legacy_case_0004_current_aex: max=113 mean=0.004419608 nz%=0.214747299
legacy_case_0012_gamma5_red_blue_current_aex: max=91 mean=0.015058835 nz%=0.186149691
legacy_case_0004_current_aex witness (1903,519) ref=[103, 103, 103, 113] cand=[0, 0, 0, 0]
legacy_case_0012_gamma5_red_blue_current_aex witness (91,841) ref=[0, 0, 0, 0] cand=[90, 90, 90, 91]
```

FACT: The trial did not change either witness pixel. Total mean_sum worsened from `0.058945` to `0.059653` (`+0.000708`).

## Restoration

Commands:

```sh
refs/scripts/build_olmsmoother2_cli.sh
rg -n "LOW_ALPHA_LENS|1\\.5f / 255\\.0f|aa =|ba =" mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp || true
git diff -- mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp | rg -n "LOW_ALPHA_LENS|1\\.5f / 255\\.0f|aa =|ba =|color_dist" || true
```

Output:

```text
7 warnings generated.
/Users/onmk/Documents/Projects/Personal/OLM as/cli/OLMSmoother2/olmsmoother2_cli
# rg output: empty
# git diff rg output: empty
```

FACT: The temporary low-alpha code was removed and the CLI was rebuilt from the restored source. The repository still contains pre-existing unrelated dirty worktree changes; no mac/OLMSmoother2 low-alpha trial diff remains.

