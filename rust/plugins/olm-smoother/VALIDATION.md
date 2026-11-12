# OLMSmoother v1 — Windows Rust validation

Job P-smoother, 2026-11-12. Scope: `rust/plugins/olm-smoother/**`.
Build target directory: `D:\olm-rs-target\P-smoother`.

## Identities

| Artifact | SHA-256 |
| --- | --- |
| Original `ghidra_windows_aex/OLMSmoother.aex` | `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82` |
| Rust staged `validation/OLMSmoother.aex` | `21d3ae696808b7ad188ec0b0994c04bfc9da2efe16eef289557b2a5a7be799f7` |
| AEXCompat harness | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |
| Installed worker at the diagnostic report's default path | `0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302` |
| Windows PiPL, both binaries (298 bytes) | `652dd1cccef7ea16acdf236d5ecad626e08729fe16357bca67050e3798928abd` |

The worker path is `D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\target\minihost-build\aex_worker.exe`.
The request logs do not emit its loaded-module path; this additional hash
identifies the existing default-path file, rather than claiming a fresh module
mapping witness. They report `source_newer_than_worker`. The complete harness
path, OS, test-log identities and provenance caveat are in
[environment.json](environment.json).

## Build and C++ reference tests

From `rust/`:

```powershell
$env:CARGO_TARGET_DIR = 'D:\olm-rs-target\P-smoother'
cargo test --release -p olm-smoother -j 2
cargo build --release -p olm-smoother -j 2
```

Both succeeded. **6 tests passed, 0 failed**:

- 480 complete C++/Rust frame comparisons: 240 per depth, multiple geometries,
  categorical/diagonal/noise patterns, partial alpha, exact color-key hits,
  tolerance 0/1/6/32/128/255, and cropped callback extents.
- 16,384 color-comparison vectors and 16,384 alpha-blend vectors across 8/16 bpc.
- 80 frames compared after every directional classifier, subhandler and dispatch.
- 20 frames of independently compared contour-walker outputs, with 16 direction
  pairs per pixel.
- Identical results with 1/2/4 independent rendering workers. Each frame retains
  the original ordered callback traversal.
- Odd padded 16-bit row strides, retained padding, and rejection before writes
  for an out-of-range tolerance.

The C++ archive is referenced only by `cfg(test)` code. Production rendering
calls the Rust algorithm and generated Rust kernels. The build uses the pilots'
existing `cc`/PiPL/`winres` approach; no new external dependency was added.

## Original-binary oracle

Inventory: **identical**, with zero exposed parameter/host differences.
The independent [PiPL comparison](pipl-comparison.json) is also byte-identical.
The effect preserves `entryPointFunc`, exposes `EffectMain`, and declares
`out_flags=0x02000040`, `out_flags2=0x08000000`, version `0x00090800`.
There are three parameters plus input. SmartFX and 32 bpc remain undeclared.

The initial smoke completed **20/20 exact on classic8 and 20/20 exact on
classic16**, with zero failures or mismatches. The main two-seed campaigns are
recorded below after completion; the overlapping smoke is not added to their
distinct-case totals.

| Seed | Classic 8 | Classic 16 | Random cases per depth |
| --- | ---: | ---: | ---: |
| 20261112 | 103 exact | 103 exact | 100 |
| 20261113 | 103 exact | 103 exact | 100 |
| **Main total** | **206 exact** | **206 exact** | **200** |

**Zero pixel mismatches, reference-unrenderable cases, timeouts, candidate
failures, or inventory differences.** Both campaign exit codes are 0. There are
no original failures to exclude. Each seed/depth includes 35 full-resolution,
34 half-resolution and 34 quarter-resolution cases, counted from saved requests.
The first three cases per seed are default/minimum/maximum; the remaining 100
are randomized. Full data and source identities are in
[validation-report.json](validation-report.json).

All oracle runs use **`--jobs 3`**. Each process timeout is 120 seconds; the
oracle supplies **`AEXCOMPAT_FRAME_DEADLINE_MS=120000` to both binaries**.
Inputs cycle through `1x1,3x7,11x7,31x19,97x61`; downsample cycles through
`1,1/2,1/4`. PNG samples include partial alpha and hidden RGB; deep comparisons
use `.rgba16le`, rather than preview PNG values.

Commands from the repository root (choose fresh output directories to repeat):

```powershell
$ref = 'D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMSmoother.aex'
$cand = 'D:\Projects\01_Project\04_Tools\olm for mac\OLM-for-mac\rust\plugins\olm-smoother\validation\OLMSmoother.aex'
python rust/tools/oracle/olm_oracle.py inventory --reference $ref --candidate $cand --out rust/plugins/olm-smoother/validation/inventory-final
python rust/tools/oracle/olm_oracle.py render --reference $ref --candidate $cand --routes classic8,classic16 --cases 103 --seed 20261112 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --timeout 120 --out rust/plugins/olm-smoother/validation/seed-20261112
python rust/tools/oracle/olm_oracle.py render --reference $ref --candidate $cand --routes classic8,classic16 --cases 103 --seed 20261113 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --timeout 120 --out rust/plugins/olm-smoother/validation/seed-20261113
python rust/plugins/olm-smoother/tools/collect_validation.py smoke seed-20261112 seed-20261113
```

## Resolved differences

1. **Native parameter declaration versus C++ UI range.** Original inspection
   reports tolerance's user maximum as 255. The C++ declaration uses 6, which
   produced one inventory difference. Rust uses the original's 255 maximum;
   the default remains 6. White Color Key defaults also require a local setup
   adapter because shared `Kind::Color` currently initializes black.
2. **Synthetic descriptor address collision.** Initial Rust/C++ differential
   tests exposed a subhandler coordinate difference. Instruction-boundary traces
   localized the first divergence to a generated world-width read. The minimal
   host-free world occupied fewer bytes than the synthetic Windows field span,
   so a logical field address could overlap an adjacent RenderState and match
   its memory interception first. Reserving the complete descriptor span in
   both local carriers removed that address-dependent collision. The original
   C++ algorithm bodies and all arithmetic constants were unchanged.
3. **Rust memory alignment and mutable array decay.** The translation explicitly
   retains aligned curve storage and obtains mutable pointers for mutable local
   arrays. Integer casts retain x86 truncation behavior; separate binary32
   operations preserve the C++ contraction-off arithmetic.

No oracle pixel mismatch was used to tune an arithmetic constant.

## Limits and shared candidates

- These are **AEXCompat CPU results, not native AE results**. AE was not launched;
  no plug-in was installed. macOS compilation, Universal packaging, and native
  UI behavior were not tested on this Windows machine.
- Oracle 16-bit inputs are promoted from PNG bytes. The C++ helper/frame tests
  add native 16-bit samples, but neither corpus exhausts all possible images.
- The request oracle does not cover padded/origin-shifted host worlds. Local
  tests cover padding and cropped extents; they do not replace native host tests.
- The original and C++ supported range stays 8/16 bpc, integer tolerance 0–255,
  maximum side 4096 and maximum pixel count 4096×2160. Neighborhood work remains
  frame-wide even for a restricted output extent. No 32-bit or SmartFX claim is made.
- Hoisting candidate: a shared color-parameter kind with an explicit default
  ARGB value would eliminate the local ParamsSetup adapter. No new UCRT wrapper
  is needed; existing `olm_math::x86` helpers supply the required scalar behavior.
  The contour carrier and ordered traversal are v1-specific and remain local.

Detailed oracle inputs, requests, process logs, and raw outputs stay under the
ignored `validation/` directory. Curated binary/source hashes and per-route counts
are in `validation-report.json`; development build logs and the AST stay in
ignored `tools/work/`. No background service, GUI, browser, or subagent was used.

The final identity recheck found the original, candidate and harness unchanged;
the release DLL is byte-identical to the staged candidate used by both campaigns.
[cleanup.json](cleanup.json) records both oracle exits and a post-run process
check: no task-owned harness, worker or oracle process remained. Windows had
recycled several recorded PIDs for other jobs; command-line scope and parent
ownership distinguished those processes, and none was stopped.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.
