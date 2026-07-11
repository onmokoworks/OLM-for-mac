# OLMDistanceGradation regression check after case_0023 alpha fix

Date: 2026-07-08 JST

## FACT: commands run

```sh
python3 refs/scripts/run_reference_test.py refs/win_references/20260605_extra/OLMDistanceGradation --run-dir /tmp/olmdg_regression_8bpc_all_20260708_1 --expected-effect "OLM Distance Gradation" --command 'python3 "refs/scripts/olmdistancegradation_cli.py" --input "{input}" --params "{params}" --output "{output}"' --max-diff 255 --mean-diff 999 --nonzero-px-percent 100
```

```sh
python3 refs/scripts/run_reference_test.py refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch --run-dir /tmp/olmdg_regression_16bpc_extended_20260708_1 --expected-effect "OLM Distance Gradation" --command 'python3 "refs/scripts/olmdistancegradation_cli.py" --input "{input}" --params "{params}" --output "{output}"' --case-id olmdistancegradation_extended__case_0008 --case-id olmdistancegradation_extended__case_0010 --case-id olmdistancegradation_extended__case_0011 --case-id olmdistancegradation_extended__case_0012 --case-id olmdistancegradation_extended__case_0013 --case-id olmdistancegradation_extended__case_0014 --case-id olmdistancegradation_extended__case_0016 --case-id olmdistancegradation_extended__case_0020 --case-id olmdistancegradation_extended__case_0021 --case-id olmdistancegradation_extended__case_0022 --case-id olmdistancegradation_extended__case_0023 --case-id olmdistancegradation_extended__case_0024 --case-id olmdistancegradation_extended__case_0025 --case-id olmdistancegradation_extended__case_0026 --case-id olmdistancegradation_extended__case_0027 --case-id olmdistancegradation_extended__case_0028 --max-diff 255 --mean-diff 999 --nonzero-px-percent 100
```

```sh
python3 - <<'PY'
import csv
paths=[('8bpc','/private/tmp/olmdg_regression_8bpc_all_20260708_1/reports/diff.csv'),('16bpc','/private/tmp/olmdg_regression_16bpc_extended_20260708_1/reports/diff.csv')]
for bpc,p in paths:
    with open(p,newline='') as f:
        for row in csv.DictReader(f):
            print(bpc, row['id'], row['nonzero_px'], row['max_diff'], row['mean_diff'])
PY
```

```sh
git status --short -- mac/OLMDistanceGradation/OLMDistanceGradation.cpp refs/conformance/olmdistancegradation_regression_after_case0023_fix_20260707.md
git diff --stat -- mac/OLMDistanceGradation/OLMDistanceGradation.cpp refs/conformance/olmdistancegradation_regression_after_case0023_fix_20260707.md
git diff -- mac/OLMDistanceGradation/OLMDistanceGradation.cpp | shasum -a 256
```

## FACT: command output excerpts

8bpc run:

```text
=== verify reference_manifest.json ===
[OK]      case_0001            max=2 mean=0.0473
[OK]      case_0002            max=1 mean=0.0015
[OK]      case_0003            max=0 mean=0.0000
[OK]      case_0004            max=2 mean=0.1051
[OK]      case_0005            max=1 mean=0.0187
[OK]      case_0006            max=1 mean=0.1001
[OK]      case_0007            max=1 mean=0.0866
[OK]      case_0008            max=1 mean=0.0022
[OK]      case_0009            max=1 mean=0.0866
[OK]      case_0010            max=1 mean=0.1205
[OK]      case_0011            max=2 mean=0.0960
[OK]      case_0012            max=251 mean=0.7059
[OK]      case_0013            max=62 mean=0.2269
[OK]      case_0014            max=63 mean=0.2664
[OK]      case_0015            max=1 mean=0.0016
[OK]      case_0016            max=64 mean=0.2074
[OK]      case_0017            max=2 mean=0.0025
[OK]      case_0018            max=1 mean=0.0347
[OK]      case_0019            max=1 mean=0.0350
[OK]      case_0020            max=238 mean=0.0561
[OK]      case_0021            max=238 mean=0.0561
[OK]      case_0022            max=238 mean=0.5180
[OK]      case_0023            max=238 mean=0.0737
[OK]      case_0024            max=15 mean=0.1706
[OK]      case_0025            max=4 mean=0.1682
[OK]      case_0026            max=2 mean=0.1446
[OK]      case_0027            max=6 mean=0.0600
[OK]      case_0028            max=142 mean=0.1508
[OK]      case_0029            max=23 mean=0.2827
[SKIP] case_0030            missing effect OLM Distance Gradation
---
ok=29 fail=0 missing=0 total=29
report_json=/private/tmp/olmdg_regression_8bpc_all_20260708_1/reports/diff.json
report_csv=/private/tmp/olmdg_regression_8bpc_all_20260708_1/reports/diff.csv
run_dir=/private/tmp/olmdg_regression_8bpc_all_20260708_1
```

16bpc extended run:

```text
=== verify reference_manifest.json ===
[OK]      olmdistancegradation_extended__case_0008 max=0.0 mean=0.0000
[OK]      olmdistancegradation_extended__case_0010 max=0.5058365758754917 mean=0.0822
[OK]      olmdistancegradation_extended__case_0011 max=0.5058365758754917 mean=0.0500
[OK]      olmdistancegradation_extended__case_0012 max=63.96108949416343 mean=0.2609
[OK]      olmdistancegradation_extended__case_0013 max=37.47470817120623 mean=0.1146
[OK]      olmdistancegradation_extended__case_0014 max=38.217898832684824 mean=0.1439
[OK]      olmdistancegradation_extended__case_0016 max=38.36575875486382 mean=0.1038
[OK]      olmdistancegradation_extended__case_0020 max=237.99610894941634 mean=0.0572
[OK]      olmdistancegradation_extended__case_0021 max=237.99610894941634 mean=0.0574
[OK]      olmdistancegradation_extended__case_0022 max=237.99610894941634 mean=0.5187
[OK]      olmdistancegradation_extended__case_0023 max=237.99610894941634 mean=0.0739
[OK]      olmdistancegradation_extended__case_0024 max=0.5214007782101167 mean=0.0813
[OK]      olmdistancegradation_extended__case_0025 max=0.5097276264591528 mean=0.0686
[OK]      olmdistancegradation_extended__case_0026 max=0.5136186770427997 mean=0.0654
[OK]      olmdistancegradation_extended__case_0027 max=0.5136186770427997 mean=0.0270
[OK]      olmdistancegradation_extended__case_0028 max=12.116731517509727 mean=0.0539
---
ok=16 fail=0 missing=0 total=16
report_json=/private/tmp/olmdg_regression_16bpc_extended_20260708_1/reports/diff.json
report_csv=/private/tmp/olmdg_regression_16bpc_extended_20260708_1/reports/diff.csv
run_dir=/private/tmp/olmdg_regression_16bpc_extended_20260708_1
```

16bpc dtype/compare-mode audit:

```text
id,candidate_dtype,reference_dtype,compare_mode
olmdistancegradation_extended__case_0008,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0010,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0011,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0012,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0013,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0014,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0016,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0020,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0021,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0022,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0023,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0024,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0025,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0026,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0027,uint8,>u2,integer-normalized-8bit
olmdistancegradation_extended__case_0028,uint8,>u2,integer-normalized-8bit
```

## FACT: per-case results

| case_id | bpc | nonzero_px | max_diff | mean | 判定 |
|---|---:|---:|---:|---:|---|
| case_0001 | 8bpc | 195176 | 2 | 0.04730709877 | diff |
| case_0002 | 8bpc | 6138 | 1 | 0.001480034722 | diff |
| case_0003 | 8bpc | 0 | 0 | 0 | exact |
| case_0004 | 8bpc | 435914 | 2 | 0.105114294 | diff |
| case_0005 | 8bpc | 77422 | 1 | 0.01866849923 | diff |
| case_0006 | 8bpc | 415032 | 1 | 0.1000752315 | diff |
| case_0007 | 8bpc | 359283 | 1 | 0.08663266782 | diff |
| case_0008 | 8bpc | 9162 | 1 | 0.002209201389 | diff |
| case_0009 | 8bpc | 359283 | 1 | 0.08663266782 | diff |
| case_0010 | 8bpc | 499808 | 1 | 0.1205169753 | diff |
| case_0011 | 8bpc | 397472 | 2 | 0.09603636188 | diff |
| case_0012 | 8bpc | 572489 | 251 | 0.7058755305 | diff |
| case_0013 | 8bpc | 142162 | 62 | 0.226939863 | diff |
| case_0014 | 8bpc | 448566 | 63 | 0.2663711661 | diff |
| case_0015 | 8bpc | 5382 | 1 | 0.001633752894 | diff |
| case_0016 | 8bpc | 14131 | 64 | 0.2074321229 | diff |
| case_0017 | 8bpc | 14204 | 2 | 0.002452739198 | diff |
| case_0018 | 8bpc | 212535 | 1 | 0.03466760706 | diff |
| case_0019 | 8bpc | 243856 | 1 | 0.03500012056 | diff |
| case_0020 | 8bpc | 1000 | 238 | 0.0560619213 | diff |
| case_0021 | 8bpc | 1001 | 238 | 0.05611798322 | diff |
| case_0022 | 8bpc | 9240 | 238 | 0.5180121528 | diff |
| case_0023 | 8bpc | 1315 | 238 | 0.0737214265 | diff |
| case_0024 | 8bpc | 1051193 | 15 | 0.1705913628 | diff |
| case_0025 | 8bpc | 959197 | 4 | 0.1682092737 | diff |
| case_0026 | 8bpc | 986145 | 2 | 0.1446295091 | diff |
| case_0027 | 8bpc | 463235 | 6 | 0.06001157407 | diff |
| case_0028 | 8bpc | 444586 | 142 | 0.1507729311 | diff |
| case_0029 | 8bpc | 229595 | 23 | 0.2827018229 | diff |
| case_0008 | 16bpc | 0 | 0.0 | 0 | exact |
| case_0010 | 16bpc | 1338683 | 0.5058365758754917 | 0.08217224054 | diff |
| case_0011 | 16bpc | 824665 | 0.5058365758754917 | 0.04995910325 | diff |
| case_0012 | 16bpc | 1488573 | 63.96108949416343 | 0.2608540102 | diff |
| case_0013 | 16bpc | 235284 | 37.47470817120623 | 0.1145642149 | diff |
| case_0014 | 16bpc | 924242 | 38.217898832684824 | 0.1438753469 | diff |
| case_0016 | 16bpc | 48194 | 38.36575875486382 | 0.1037661086 | diff |
| case_0020 | 16bpc | 304210 | 237.99610894941634 | 0.05723249027 | diff |
| case_0021 | 16bpc | 1406979 | 237.99610894941634 | 0.0574371218 | diff |
| case_0022 | 16bpc | 702536 | 237.99610894941634 | 0.5186626278 | diff |
| case_0023 | 16bpc | 182728 | 237.99610894941634 | 0.07389163464 | diff |
| case_0024 | 16bpc | 1320574 | 0.5214007782101167 | 0.08128165982 | diff |
| case_0025 | 16bpc | 2073540 | 0.5097276264591528 | 0.06864413513 | diff |
| case_0026 | 16bpc | 2073600 | 0.5136186770427997 | 0.06539478795 | diff |
| case_0027 | 16bpc | 858071 | 0.5136186770427997 | 0.0269950449 | diff |
| case_0028 | 16bpc | 867625 | 12.116731517509727 | 0.05385528973 | diff |

## FACT: existing CLI green guard check

The 8bpc values were checked against the existing smoke guard thresholds in `refs/scripts/smoke_olmdistancegradation_cli.py`, `refs/scripts/smoke_olmdistancegradation_extended_cli.py`, and `refs/scripts/smoke_olmdistancegradation_blur_cli.py`: basic `max<=7 mean<=0.11 nonzero<=22%`, extended `max<=255 mean<=0.72 nonzero<=51%`, blur `max<=23 mean<=0.29 nonzero<=12%`.

```text
case_id,max_diff,mean,nonzero_pct,guard_result
case_0001,2.0,0.04730709877,9.41242284,PASS
case_0002,1.0,0.001480034722,0.2960069444,PASS
case_0003,0.0,0,0,PASS
case_0004,2.0,0.105114294,21.02208719,PASS
case_0005,1.0,0.01866849923,3.733699846,PASS
case_0006,1.0,0.1000752315,20.0150463,PASS
case_0007,1.0,0.08663266782,17.32653356,PASS
case_0008,1.0,0.002209201389,0.4418402778,PASS
case_0009,1.0,0.08663266782,17.32653356,PASS
case_0010,1.0,0.1205169753,24.10339506,PASS
case_0011,2.0,0.09603636188,19.16820988,PASS
case_0012,251.0,0.7058755305,27.60845872,PASS
case_0013,62.0,0.226939863,6.855806327,PASS
case_0014,63.0,0.2663711661,21.6322338,PASS
case_0015,1.0,0.001633752894,0.2595486111,PASS
case_0016,64.0,0.2074321229,0.6814718364,PASS
case_0017,2.0,0.002452739198,0.684992284,PASS
case_0018,1.0,0.03466760706,10.24956597,PASS
case_0019,1.0,0.03500012056,11.76003086,PASS
case_0020,238.0,0.0560619213,0.04822530864,PASS
case_0021,238.0,0.05611798322,0.04827353395,PASS
case_0022,238.0,0.5180121528,0.4456018519,PASS
case_0023,238.0,0.0737214265,0.06341628086,PASS
case_0024,15.0,0.1705913628,50.69410687,PASS
case_0025,4.0,0.1682092737,46.25757137,PASS
case_0026,2.0,0.1446295091,47.55714699,PASS
case_0027,6.0,0.06001157407,22.33965085,PASS
case_0028,142.0,0.1507729311,21.44029707,PASS
case_0029,23.0,0.2827018229,11.07228974,PASS
```

## INFERENCE: regression and bisection result

No 8bpc case regressed relative to the existing AE-free CLI green guard thresholds. Therefore no temporary individual revert build was run, and no source bisection was needed.

The per-pixel table is not an AE exact claim for 8bpc because the Python CLI itself is a compact AE-free algorithm target and historically has nonzero residuals for many cases. It is a regression measurement against the existing CLI guard surface.

## INFERENCE: CLI cannot decide these AE cases

The 16bpc extended batch is CLI-measurable but not AEX-16bpc-equivalent: `verify_manifest` reports `reference_dtype=>u2`, `candidate_dtype=uint8`, and `compare_mode=integer-normalized-8bit` for all 16 extended cases. These cases require AE 16bpc revalidation before accepting or rejecting AEX regression:

`case_0008`, `case_0010`, `case_0011`, `case_0012`, `case_0013`, `case_0014`, `case_0016`, `case_0020`, `case_0021`, `case_0022`, `case_0023`, `case_0024`, `case_0025`, `case_0026`, `case_0027`, `case_0028`.

## FACT: final git state check

No temporary source revert was performed. Before adding this report, scoped status/stat/hash were:

```text
 M mac/OLMDistanceGradation/OLMDistanceGradation.cpp
 mac/OLMDistanceGradation/OLMDistanceGradation.cpp | 107 ++++++++++++++++++----
 1 file changed, 90 insertions(+), 17 deletions(-)
648df3c56881bb55a79b2003c80ed372d8c16457bc3a1b665f0471f938157b79  -
```

The only intended new file from this task is:

```text
refs/conformance/olmdistancegradation_regression_after_case0023_fix_20260707.md
```
