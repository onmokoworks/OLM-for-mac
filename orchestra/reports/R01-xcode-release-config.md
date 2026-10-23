status: done
summary:
- Added project and target Release configurations to all ten Mac plugin projects.
- Release uses O2, x86_64 + arm64, unchanged deployment targets/defines/sources, and disabled testability.
- Both configurations explicitly retain -ffp-contract=off and -fno-fast-math; signing settings are unchanged.
- All ten Release builds and universal-slice checks passed. All ten seed-1 n100 public fuzz runs completed.
- Fuzz observed 392 Classic mismatch cases; no Smart pixel mismatches. Refusals/uncompared cases are not passes.

facts:
- Ran `scripts/setup_ae_sdk_links.sh` successfully, creating worktree-only SDK symlinks.
- Ran `python3 tools/fuzz/verify_R01_release.py --phase build` with output in `orchestra/state/R01-xcode-release-config/build-driver.log`: ten xcodebuild exit codes 0, ten `lipo -info` results containing x86_64 and arm64. Builds used `-configuration Release -jobs 1 CODE_SIGNING_ALLOWED=NO`; no optimization/architecture overrides. Exact commands, effective OTHER_CFLAGS/OTHER_CPLUSPLUSFLAGS and GCC_* settings are committed in `R01-xcode-release-config-evidence.json`.
- All effective FP flags match Debug/Release. Effective GCC differences are optimization 0→2 (except DistanceGradation and Smoother2 already effectively O2), and GCC_SYMBOLS_PRIVATE_EXTERN NO→YES due to ENABLE_TESTABILITY YES→NO. Deployment target remains 11.0 for all ten.
- Parsed original HEAD and edited projects with `plutil -convert json -o - -`: every non-configuration object was unchanged in all ten projects; corresponding Debug/Release GCC_PREPROCESSOR_DEFINITIONS were identical. Thus source/build-phase graphs are unchanged.
- Ran `python3 tools/fuzz/verify_R01_release.py --phase fuzz`: ten exit codes 0 and 100 completed cases each, seed 1, jobs 1, no shrinking. The existing public source harness uses arm64 O2, -ffp-contract=off and -fno-fast-math. Used MAIN's Python environment/assets by absolute path and the prebuilt F46 worker, SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- Exact AEX/candidate/source hashes, full-report hashes, route counts and first mismatch output hashes/words are committed in the evidence JSON.

| Plugin | Classic exact | Classic mismatch | Classic refusal | Classic no-write | Smart exact | Smart refusal | Smart uncompared |
|---|---:|---:|---:|---:|---:|---:|---:|
| ColorKeep | 22 | 43 | 35 | 0 | 100 | 0 | 0 |
| OLMBlur | 3 | 0 | 97 | 0 | 100 | 0 | 0 |
| OLMColorKey | 0 | 100 | 0 | 0 | 100 | 0 | 0 |
| OLMDirectionalBlur | 0 | 98 | 2 | 0 | 98 | 2 | 0 |
| OLMDistanceGradation | 1 | 99 | 0 | 0 | 93 | 3 | 4 |
| OLMKiraKira | 0 | 16 | 84 | 0 | 97 | 3 | 0 |
| OLMRadialBlur | 0 | 36 | 64 | 0 | 77 | 21 | 2 |
| OLMSmoother | 65 | 0 | 35 | 0 | 65* | 35* | 0 |
| OLMSmoother2 | 0 | 0 | 100 | 0 | 100 | 0 | 0 |
| OLMToonDilate | 0 | 0 | 0 | 100 | 100 | 0 | 0 |

*The Smoother adapter is Classic-only; its runner's duplicated Smart-labelled counts do not establish Smart support. Every Smart mismatch count is zero. There were four AEX Smart budget results (two DistanceGradation, two RadialBlur); additional AEX rejections and Mac refusals are preserved in the evidence.

First mismatches (zero-based generated case and byte offset; expected AEX → actual Mac):

| Plugin | Case | Depth | Geometry | First byte | First word hex | Differing bytes |
|---|---:|---:|---|---:|---|---:|
| ColorKeep | 0 | 8 | 21×19 | 8 | 00 → ff | 191 |
| OLMColorKey | 0 | 8 | 21×19 | 1 | 00 → 93 | 1461 |
| OLMDirectionalBlur | 0 | 8 | 21×19 | 0 | 00 → a9 | 382 |
| OLMDistanceGradation | 0 | 8 | 21×19 | 0 | 00 → b4 | 1065 |
| OLMKiraKira | 2 | 32 | 10×19 | 2 | 00000000 → 0000803f | 2023 |
| OLMRadialBlur | 0 | 8 | 21×19 | 4 | 00 → 1a | 1589 |

inference:
- The Release-configuration blocker is resolved. These bounded source-harness observations do not establish universal bit-exactness, x86_64 numerical parity, native AE behavior, or direct bundle-render parity.
- The harness does not consume Xcode configuration settings, and no rendering source was changed. The observed differences are not evidence of a newly introduced Release regression; no Debug/O0 differential was performed. Root causes were not investigated under this configuration-only ticket.

changed_files:
- `mac/{ColorKeep,OLMBlur,OLMColorKey,OLMDirectionalBlur,OLMDistanceGradation,OLMKiraKira,OLMRadialBlur,OLMSmoother,OLMSmoother2,OLMToonDilate}/Mac/<plugin>.xcodeproj/project.pbxproj`
- `tools/fuzz/verify_R01_release.py`
- `orchestra/reports/R01-xcode-release-config.md`
- `orchestra/reports/R01-xcode-release-config-evidence.json`

verify:
Run from this worktree, sequentially:

```sh
mkdir -p orchestra/state/R01-xcode-release-config
scripts/setup_ae_sdk_links.sh > orchestra/state/R01-xcode-release-config/sdk.log 2>&1
python3 tools/fuzz/verify_R01_release.py --phase build > orchestra/state/R01-xcode-release-config/build-driver.log 2>&1
python3 tools/fuzz/verify_R01_release.py --phase fuzz > orchestra/state/R01-xcode-release-config/fuzz-driver.log 2>&1
git diff --check
```

Expected: ten successful universal builds, FP settings assertions pass, ten complete 100-case fuzz reports. Counts above are the observed result, not an all-exact acceptance assertion; time-budget outcomes can vary with shared-machine load. The verifier deletes regenerable build trees and fuzz executables, retaining logs, reports and mismatch corpus in scratch. Its exit status reports execution/setup failures; inspect numerical counts separately.

next:
- Orchestrator reviews/merges this commit and handles signing later.
- Separate tickets may investigate the recorded Classic differences/refusals, reference timeouts/rejections, x86_64 numerical behavior, and direct Release bundle rendering. No AE installation, release-gate/ledger changes, or emulator rebuild was performed.
