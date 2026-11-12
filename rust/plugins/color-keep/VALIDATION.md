# ColorKeep Rust validation ? F-core pilot

Windows x64 AEXCompat CPU evidence, 2026-11-12; not native AE acceptance.
The original pilot record was in the workspace README. This per-crate index
preserves its claims without attributing the old campaigns to a new build.

| Corpus | Smart8 | Smart16 | Smart32 CPU |
| --- | ---: | ---: | ---: |
| Main, seed 20261112 | 203 exact | 203 exact | 203 exact |
| Palette hits | 24 exact | 24 exact | 24 exact |

Main counts are per depth: default/min/max plus 200 random cases. Sizes cycle
1x1, 3x7, 11x7, 31x19, 97x61; downsample cycles 1, 1/2, 1/4. PNG-promoted
deep inputs include partial alpha and hidden RGB; deep output compares raw words.

[validation-report.json](validation-report.json) binds binary identities, counts,
failures and local artifact paths. [pipl-comparison.json](pipl-comparison.json)
records complete 294-byte Windows resource equality; exposed inventories match
(101 parameters excluding input).
[build-equivalence.json](build-equivalence.json) distinguishes the frozen campaign
binary from later metadata-only rebuilds. Both declare 8/16/32-bit SmartFX.

The main Smart8 case 168 initially failed to create a resident session (Windows
error 80). Its unchanged saved input/request replay was exact; 203 counts unique
cases, not the extra attempt. Twelve cropped-demand requests per depth were
exact. Forced Classic 8/16 diagnostics had 12 exact each; these are not normal
AE dispatch or part of the main totals.

Reproduce from `rust/` after staging with `tools/stage_windows.ps1`:

```powershell
cargo build --release -p color-keep
cargo test --release -p color-keep
python tools/oracle/olm_oracle.py inventory --reference '<original absolute path>/ColorKeep.aex' --candidate '<staged absolute path>/ColorKeep.aex' --out local/color-keep-inventory-new
python tools/oracle/olm_oracle.py render --reference '<original absolute path>/ColorKeep.aex' --candidate '<staged absolute path>/ColorKeep.aex' --cases 203 --seed 20261112 --jobs 3 --sizes 1x1,3x7,11x7,31x19,97x61 --downsample 1,1/2,1/4 --routes smart8,smart16,smart32 --out local/color-keep-render-new
```

The shared supplemental runner is
[validate_pilots.py](../olm-color-key/validate_pilots.py); select `--plugin ColorKeep`.
Shared foundation/pilot tests included 24,576 color vectors, 648 distance scans,
216 boundary masks, 131,072 numeric probes and 82,080 native UCRT comparisons.
The original two-pilot workspace had 12 passing test functions. Current full
workspace results are recorded separately in [integration](../../INTEGRATION.md).

Native AE, macOS, arbitrary HDR/nonfinite worlds and exhaustive UI/project
compatibility remain unverified. Original UCRT FMA3 was enabled. The historical
worker reported source_newer_than_worker; hashes qualify the installed binaries.
No additional hoisting candidate was recorded for this pilot: common geometry,
world, checkout and parameter helpers already live in the shared crates.

Evidence policy: all `validation/` paths, absolute machine paths, candidate-path
files, rendered images, logs and DLL/AEX paths in this document or its JSON
reports are **local-only evidence**, ignored and not included in Git. The linked
compact JSON files and rerun script are versioned candidates. No original
plug-in binary is included.
