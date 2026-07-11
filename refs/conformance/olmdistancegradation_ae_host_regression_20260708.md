# OLMDistanceGradation AE Host Regression - 2026-07-08

## Conclusion

- FACT: The currently installed MediaCore `OLMDistanceGradation.plugin` binary matches the current local Debug build binary by SHA-256.
- FACT: The 8bpc packaged regression batch did not render any candidate PNGs in this run because After Effects 26.3 could not be launched/scripted from this environment.
- FACT: No per-case `max_diff` / `mean_diff` / `nonzero_px` could be measured for the 29 packaged 8bpc cases in this run.
- INFERENCE: This run cannot prove either "8bpc 29 cases all exact maintained" or identify AE-rendered regression cases. Treat the final gate as blocked by AE host launch failure, not as a pixel regression pass/fail.
- FACT: 16bpc extended follow-up was not attempted because the required 8bpc gate did not reach render/verify.

## Binary Provenance

Command:

```sh
for p in "$HOME/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation" \
         "$HOME/Library/Developer/Xcode/DerivedData/OLMDistanceGradation-fqjqkjfjqasflpfhuebjyqccpqob/Build/Products/Debug/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation" \
         "mac/OLMDistanceGradation/Mac/build/Debug/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation"; do
  if [ -f "$p" ]; then
    stat -f '%Sm %z %N' -t '%Y-%m-%d %H:%M:%S %z' "$p"
    shasum -a 256 "$p"
  fi
done
```

Log excerpt:

```text
2026-07-07 23:43:05 +0900 294656 /Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation
e0d6652a5f8df0d97fc8c10e29a786d71519b146395143a4d81d6aec46bf3601  /Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation
2026-07-07 23:43:05 +0900 294656 mac/OLMDistanceGradation/Mac/build/Debug/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation
e0d6652a5f8df0d97fc8c10e29a786d71519b146395143a4d81d6aec46bf3601  mac/OLMDistanceGradation/Mac/build/Debug/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation
```

Source check:

```sh
rg -n "source_mask_owns_alpha|1\\.5f|255" mac/OLMDistanceGradation/OLMDistanceGradation.cpp
```

Log excerpt:

```text
mac/OLMDistanceGradation/OLMDistanceGradation.cpp:376:static inline bool source_mask_owns_alpha(float alpha)
mac/OLMDistanceGradation/OLMDistanceGradation.cpp:382:	return alpha > (1.5f / 255.0f);
```

INFERENCE: Because the installed MediaCore binary and local Debug build binary have identical SHA-256 and timestamp, the AE host would have loaded the current alpha-threshold build if AE launched successfully.

## Request Materialization

Command:

```sh
mkdir -p handoff/ae_pixel_validation_20260618/requests
unzip -oq refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_basic_exact_20260619_032933.zip -d handoff/ae_pixel_validation_20260618/requests
unzip -oq refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_extended_exact_20260619_032933.zip -d handoff/ae_pixel_validation_20260618/requests
unzip -oq refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_blur_exact_20260619_032933.zip -d handoff/ae_pixel_validation_20260618/requests
```

Log excerpt:

```text
ae_pixel_olmdistancegradation_basic_exact_20260619
ae_pixel_olmdistancegradation_blur_exact_20260619
ae_pixel_olmdistancegradation_extended_exact_20260619
```

Package manifest counts:

```text
olm_ae_pixel_validation_olmdistancegradation_basic_exact_20260619_032933.zip ae_pixel_olmdistancegradation_basic_exact_20260619 12 basic_exact
olm_ae_pixel_validation_olmdistancegradation_blur_exact_20260619_032933.zip ae_pixel_olmdistancegradation_blur_exact_20260619 1 blur_exact
olm_ae_pixel_validation_olmdistancegradation_extended_exact_20260619_032933.zip ae_pixel_olmdistancegradation_extended_exact_20260619 16 extended_exact
```

## AE Execution Attempts

Primary batch command:

```sh
python3 scripts/run_ae_validation_batch.py \
  --request-id ae_pixel_olmdistancegradation_basic_exact_20260619 \
  --request-id ae_pixel_olmdistancegradation_extended_exact_20260619 \
  --request-id ae_pixel_olmdistancegradation_blur_exact_20260619 \
  --results-base refs/reports/ae_host_regression_20260708/results \
  --timeout 3600
```

Primary log excerpt:

```text
2026-07-08 13:47:56.192 osascript[28358:205250] Error received in message reply handler: Connection invalid
2026-07-08 13:47:56.192 osascript[28358:205252] Connection Invalid error for service com.apple.hiservices-xpcservice.
89:99: syntax error: end of lineがあるべきところですがclass nameが見つかりました。 (-2741)
[FAIL] osascript exited 1
[INFO] run_dir: /Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/ae_host_regression_20260708/batch_run_20260708_134755
```

AE app path/version check:

```sh
find /Applications -maxdepth 3 \( -name '*After Effects*.app' -o -name 'Adobe After Effects*.app' \) -print
osascript -e 'tell application "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app" to get version'
```

Log excerpt:

```text
/Applications/Adobe After Effects 2026/Adobe After Effects Render Engine 2026.app
/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app
26.3.0
```

Batch retry with full app path:

```sh
python3 scripts/run_ae_validation_batch.py \
  --app-name '/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app' \
  --request-id ae_pixel_olmdistancegradation_basic_exact_20260619 \
  --request-id ae_pixel_olmdistancegradation_extended_exact_20260619 \
  --request-id ae_pixel_olmdistancegradation_blur_exact_20260619 \
  --results-base refs/reports/ae_host_regression_20260708/results \
  --timeout 3600
```

Log excerpt:

```text
119:304: execution error: タイプ-10827のエラーが起きました。 (-10827)
[FAIL] osascript exited 1
[INFO] run_dir: /Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/ae_host_regression_20260708/batch_run_20260708_134829
```

Direct launch attempts:

```sh
open -a '/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app'
osascript -e 'tell application "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app" to launch'
osascript -e 'tell application "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app" to activate'
"/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects" -r ".../AE_VALIDATION_BATCH_WRAPPER.jsx"
```

Log excerpts:

```text
The application /Applications/Adobe After Effects 2026/Adobe After Effects 2026.app cannot be opened for an unexpected reason, error=Error Domain=NSOSStatusErrorDomain Code=-10827 "kLSNoExecutableErr: The executable is missing" UserInfo={_LSLine=4257, _LSFunction=_LSOpenStuffCallLocal}
```

```text
120:126: execution error: タイプ-10827のエラーが起きました。 (-10827)
120:128: execution error: タイプ-10827のエラーが起きました。 (-10827)
```

AE diagnostic:

```sh
python3 scripts/diagnose_ae_host_block.py --output-dir refs/reports/ae_host_regression_20260708/ae_host_diag --no-sample
```

Log excerpt:

```text
[OK] AE host diagnostic: ae-not-running
[INFO] JSON: refs/reports/ae_host_regression_20260708/ae_host_diag/ae_host_diagnostic.json
[INFO] Markdown: refs/reports/ae_host_regression_20260708/ae_host_diag/ae_host_diagnostic.md
```

Diagnostic excerpt:

```text
- overall_status: `ae-not-running`
- pids: `none`
- stderr: `59:89: execution error: タイプ-10827のエラーが起きました。 (-10827)`
```

Crash report excerpt from `~/Library/Logs/DiagnosticReports/After Effects-2026-07-08-135000.ips`:

```text
"app_name":"After Effects","timestamp":"2026-07-08 13:50:00.00 +0900","app_version":"26.3.0"
"procPath" : "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects"
"exception" : {"codes":"0x0000000000000000, 0x0000000000000000","rawCodes":[0,0],"type":"EXC_CRASH","signal":"SIGABRT"}
"termination" : {"flags":0,"code":6,"namespace":"SIGNAL","indicator":"Abort trap: 6","byProc":"After Effects","byPid":28889}
"parentProc" : "codex"
```

## 8bpc Per-Case Verification Table

Because AE did not render candidate PNGs, all numeric fields are unavailable for this run. These rows are included to make the 29-case gate explicit.

| Request | Case | Frame | Status | Max diff | Mean diff | Nonzero px | Note |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0001` | `case_0001.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0002` | `case_0002.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0003` | `case_0003.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0004` | `case_0004.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0005` | `case_0005.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0006` | `case_0006.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0007` | `case_0007.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0009` | `case_0009.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0015` | `case_0015.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0017` | `case_0017.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0018` | `case_0018.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_basic_exact_20260619` | `case_0019` | `case_0019.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0008` | `case_0008.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0010` | `case_0010.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0011` | `case_0011.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0012` | `case_0012.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0013` | `case_0013.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0014` | `case_0014.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0016` | `case_0016.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0020` | `case_0020.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0021` | `case_0021.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0022` | `case_0022.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0023` | `case_0023.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0024` | `case_0024.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0025` | `case_0025.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0026` | `case_0026.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0027` | `case_0027.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_extended_exact_20260619` | `case_0028` | `case_0028.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |
| `ae_pixel_olmdistancegradation_blur_exact_20260619` | `case_0029` | `case_0029.png` | not_rendered | N/A | N/A | N/A | AE launch failed before render |

## Regression Decision

- FACT: Previous packaged 8bpc baseline was 29/29 AE exact in `refs/conformance/packaged_8bpc_manifest.json`.
- FACT: This run produced 0 new AE candidate PNGs and 0 verifier JSON/CSV reports.
- INFERENCE: There is no measured worsening list from this run. The correct status is "execution blocked", not "exact maintained".

## 16bpc Status

- FACT: The `ae_pixel_bitdepth16_olmdistancegradation_*_exact_20260625` request directories exist under `handoff/ae_pixel_validation_20260618/requests`.
- FACT: They were not run in this session.
- INFERENCE: Running 16bpc before restoring AE host launch would only reproduce the same host failure and would not add useful per-case pixel metrics.
