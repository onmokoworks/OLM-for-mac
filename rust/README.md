# OLM Rust workspace

All ten CPU plug-ins are implemented as Rust `rlib`/`cdylib` crates. Shared
`olm-math`, `olm-core` and `olm-ae` provide numerics, checked worlds and AE glue.
The math crate compiles this repository's UCRT C sources; C++ algorithm archives
are reference tests, not the production render path. `olmcolorkey_cli` and the
Python `tools/oracle` are excluded from Cargo workspace membership.

Windows x64 builds and AEXCompat comparisons are available. macOS arm64 and
x86_64 builds and original-verified golden tests run in CI (see below).
**Native After Effects acceptance remains unverified.**
See [integration report](INTEGRATION.md) for the fresh seed-20261120 staged run,
build/lint counts, hygiene inventory and unresolved limitations.

## Status and retained qualification

Counts below are historical exact cases **per depth**, not per size/scale.
All campaigns cover downsample 1, 1/2 and 1/4. The linked reports bind each
campaign to its original candidate hash; the integration run binds fresh builds.
SmartFX is the comparison route except for OLMSmoother's Classic 8/16.

| Plug-in (crate) | Depths | Exact cases at 8 / 16 / 32 bpc | Exclusions and limits | Validation |
| --- | --- | --- | --- | --- |
| ColorKeep (`color-keep`) | 8/16/32 | 203 / 203 / 203 main; +24 palette, +12 crop per depth | One session-creation failure resolved by unchanged replay | [record](plugins/color-keep/VALIDATION.md) |
| DistanceGradation (`olm-distance-gradation`) | 8/16/32 | 275 / 275 / 275 | Per depth: 9 original Median errors, 2 original 300s timeouts; native IPP CPU-index-4/FMA profile | [record](plugins/olm-distance-gradation/VALIDATION.md) |
| OLMBlur (`olm-blur`) | 8/16/32 | 221 / 221 / 221 | No failures in qualified Smart corpus | [record](plugins/olm-blur/VALIDATION.md) |
| OLMColorKey (`olm-color-key`) | 8/16/32 | 203 / 203 / 203 main; +48 palette per depth | Separate crop corpus: 1 exact +11 original failures per depth | [record](plugins/olm-color-key/VALIDATION.md) |
| OLMDirectionalBlur (`olm-directional-blur`) | 8/16/32 | 250 / 251 / 250 of 256 each | 17 baseline mismatches prove original nondeterminism with negative Noise Offset; Type 3 outside declared popup range | [record](plugins/olm-directional-blur/VALIDATION.md) |
| OLMKiraKira (`olm-kirakira`) | 8/16/32 | 240 / 240 / 240 | Patched arbitrary/default transport; dimensions >=4 for approximation; active custom ramps outside qualified render lane | [record](plugins/olm-kirakira/VALIDATION.md) |
| OLMRadialBlur (`olm-radial-blur`) | 8/16/32 | 223 / 222 / 226 | 120 Type-3 plans excluded; 7 original-nondeterministic route-cases; integration Smart32 witness resolved by offset controls/replays, without adding passes; CPU-bound reciprocal profile | [record](plugins/olm-radial-blur/VALIDATION.md) |
| OLMSmoother (`olm-smoother`) | 8/16 | 206 / 206 / ? | Classic only; 32 bpc not declared | [record](plugins/olm-smoother/VALIDATION.md) |
| OLMSmoother2 (`olm-smoother2`) | 8/16/32 | 206 / 206 / 206 | No failures in qualified corpus; retained C++ admission limits | [record](plugins/olm-smoother2/VALIDATION.md) |
| OLMToonDilate (`olm-toon-dilate`) | 8/16/32 | 406 / 406 / 406 | No failures in qualified Smart corpus | [record](plugins/olm-toon-dilate/VALIDATION.md) |

Inventory and complete Windows PiPL resources match for every plug-in in the
individual reports. Original names, match names, entry aliases, versions, flags,
parameter slots/disk IDs, defaults and even inconsistent popup counts are retained.
The pinned PiPL RC text emitter corrupts non-ASCII bytes under this machine's
Japanese code page; build scripts embed binary PiPL resources using `winres`
and preserve the original two-byte `eINF` declaration.

## Build and stage on Windows

Run from `rust/`, with Rust/Cargo 1.88.0 or a separately qualified toolchain,
MSVC linker/Windows SDK and LLVM clang-cl. The reference C/C++ uses GNU
extensions including 128-bit integers. Build scripts honor `CC`/`CXX` and
otherwise use `C:/Program Files/LLVM/bin/clang-cl.exe` when available.
`after-effects` and `pipl` are pinned to commit
`0e0b197850f28c1bb24e8c82fce2e3d4c120d1e9`; retain `Cargo.lock`.

```powershell
Remove-Item Env:CARGO_TARGET_DIR -ErrorAction SilentlyContinue
cargo build --release --workspace
cargo test --release --workspace
cargo fmt --check
cargo clippy --release --workspace
powershell -NoProfile -File tools/stage_windows.ps1 -OutputDir local/stage-new
```

The staging script builds all crates offline with the default `rust/target`,
copies ten `target/release/*.dll` files to the supplied directory with names
`ColorKeep.aex`, `DistanceGradation.aex`, `OLMBlur.aex`, `OLMColorKey.aex`,
`OLMDirectionalBlur.aex`, `OLMKiraKira.aex`, `OLMRadialBlur.aex`,
`OLMSmoother.aex`, `OLMSmoother2.aex`, `OLMToonDilate.aex`, verifies SHA-256,
and writes `manifest.json`. It refuses existing destination AEX files and known
installation paths. It never installs into AE or MediaCore. The first dependency
fetch, if needed on a new machine, precedes the offline staging command.

## Fresh cross-check and exclusion rules

Python requires NumPy and Pillow. Original Windows binaries stay outside this
repository and must never be committed or copied into it. Choose new output
and staging directories for each run. From `rust/`:

```powershell
$originals = 'D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex'
$harness = 'D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\broker\target\release\aexcompat-harness.exe'
$kiraHarness = 'D:\AEXCompatWorktrees\olm-diag-kirakira\broker\target\release\aexcompat-harness.exe'
python tools/validate_windows.py --staged local/stage-new --out local/cross-check-new --reference-dir $originals --harness $harness --kira-harness $kiraHarness
```

This runs `olm_oracle.py inventory` for all ten, then render campaigns with
`--seed 20261120 --cases 12 --jobs 4 --downsample 1,1/2,1/4`. Plug-ins run
sequentially; four independent route-cases may execute within a campaign.
Timeouts are 300 seconds for DistanceGradation, 600 for RadialBlur, 120 otherwise,
with the same internal frame deadline on **both** sides. Sizes are
1x1, 3x7, 11x7, 31x19, 97x61 normally; Radial uses its documented
1x1, 3x7, 11x7, 17x9 envelope; Kira uses 5x5, 11x7, 31x19, 97x61.

- Radial uses its existing `validate.py`: preserve the shared RNG stream and
  case indices, skip only Noise Type 3, record each skipped plan, continue to
  12 admitted cases. Directional's original declared popup count is two;
  the generic generator admits only Types 1/2, checked explicitly by the runner.
- Do not exclude every negative Noise Offset or every mismatch by parameter
  alone. Directional's `classify_mismatches.py` repeats original-vs-original
  three times and adds a separate zero-offset control. Radial's `triage.py`
  repeats saved requests with a predeclared count; its exclusion requires changing
  original hashes, constant candidate hashes and successful repeats, plus either
  an exact replay or the Directional-style offset-control evidence: exact zero
  and small-positive controls with otherwise identical input/route/parameters,
  C++ zero-read equivalence and localized under-read influence. Apply this
  uniformly, never by case index or negative offset alone. See the
  [resolved Smart32 witness](plugins/olm-radial-blur/OFFSET_WITNESS.md).
  Preserve baseline verdicts; replay passes never inflate baseline totals.
- Kira uses the patched harness and its existing `validate.py`: case zero sends
  empty assignments; omit only a generated choice of Gain's invalid declared
  0.1 default, preserving each side's own effective default. No invented ramp
  payload or numeric clamp is substituted.
- Actual original errors/timeouts remain incomplete reference cases, never exact
  comparisons. Do not blacklist old case indices in a new seed. Candidate-only
  failures, unexplained mismatches and tool errors remain unresolved.

For a single normal SmartFX effect:

```powershell
python tools/oracle/olm_oracle.py inventory --reference "$originals/OLMBlur.aex" --candidate "$PWD/local/stage-new/OLMBlur.aex" --out local/blur-inventory-new
python tools/oracle/olm_oracle.py render --reference "$originals/OLMBlur.aex" --candidate "$PWD/local/stage-new/OLMBlur.aex" --cases 12 --seed 20261120 --jobs 4 --routes smart8,smart16,smart32 --downsample 1,1/2,1/4 --out local/blur-render-new
```

Use `classic8,classic16` for OLMSmoother; no forced Classic for SmartFX effects.
See [oracle documentation](tools/oracle/README.md) for replay, failure classes,
owned Windows Job cleanup and fixture limits. Point components are **percent
of layer extent**, not image-local pixels. The request corpus uses PNG-derived
deep worlds; it does not qualify arbitrary HDR, negative alpha, padded/origin
worlds, native AE threading, UI appearance or project round trips.

## Known original and host defects

- Radial active Noise Type 3 forwards an uninitialized layer destination and
  fails ownership/lifecycle checks. The port preserves the documented refusal.
- Directional Type 3 and negative Noise Offset can read undefined memory;
  repeated original outputs change even for procedural Types 1/2. Negative
  PF32 alpha with Back Alpha Fade is another original undefined-memory boundary.
- Radial has repeatable evidence of changing original output at boundary cases.
  Out-of-plane reads are a source-grounded explanation, not a runtime address
  trace. The negative Noise Offset Smart32 witness additionally has exact offset
  controls, C++ lattice equivalence and localized table-under-read influence.
  Rust preserves the C++ deterministic zero-read policy; no 32 bpc-specific
  noise/Rotation discrepancy was found.
- DistanceGradation original Median renders can return SMART_RENDER error 512;
  expensive originals can time out. A timeout is not proof of inability to render.
  Its non-AE Classic stack-state path is unsuitable for deterministic comparison.
- Kira declares Gain 0.1 outside [1,100], while effective untouched Gain is 1.
  The shared baseline harness rejects explicit 0.1 and cannot serialize untouched
  arbitrary ramps; the patched transport preserves defaults. Inactive original
  ramp capacity is unstable stack data; only active payload identity is claimed.
- ColorKey's cropped Smart original often fails the harness worker invariant.
  Several SmartFX originals' Classic selectors produce no valid output; these
  routes are not AE's normal dispatch. Host failures are not automatically
  established original algorithm defects.

CPU-specific native IPP/OpenCV fused arithmetic (DistanceGradation/Kira) and
Radial reciprocal-estimate behavior are compatibility profiles, not numeric
approximations tuned to rendered images. Their per-crate validation limits apply.

## Numerics contract

`olm-math` uses approach (a): `cc` compiles `ucrtmath/src/{expf,powf,atan2f,tables}.c`
and `ucrtmath/ms/{float,double,pow}.c` on every target. It does not import the
platform's sin/cos/exp/log2/pow/atan2 implementations. The C implementation still
uses exact low-level operations such as `fma`, `scalbn`, and square root. Both C
and C++ compile with contraction off and fast math disabled. Rust expressions
retain separate operations; do not replace them with `mul_add` or reassociate.

Every exported transcendental takes `Mode::NoFma` (0) or `Mode::Fma` (1). There is
no process-global mode and no automatic CPU selection in the Rust algorithm.
`mac/OLMColorKey/ColorMath.inc`, its public blur paths, and the relevant
`core/olm_exact_math.h` calls explicitly select `UCRT_FMA`; the Rust ColorKey implementation does too.
`core/ucrt_ms_double_mac.c` is just a Carbon-name-conflict wrapper around the
same `double.c`; Rust compiles that file directly without the Carbon prefix.

Original Windows UCRT chooses the lane from CPU capabilities at runtime. On this
oracle machine `_get_FMA3_enable()` returned 1. The dedicated native test executable
sets and verifies each lane with `_set_FMA3_enable`, then restores the original
state. Its DLL is Windows UCRT 10.0.26100.9711; the vendored implementation's
historical qualification used 10.0.28000.2705. The current probe corpus matches
both modes, but this is not a new exhaustive qualification of the installed DLL.
An original AEX on a NOFMA machine may differ from the explicitly FMA Mac/Rust
lane; bind comparisons to the machine's actual mode and do not tune coefficients.

Round-to-nearest and gradual underflow are required. Alternate rounding, errno,
floating-point exception flags and FTZ/DAZ modes are outside the contract.
`core/x86_float.h` actually contains scalar SSE helpers, not x87 extended precision.
`olm_math::x86` ports first-NaN selection, quieting, negative generated invalid,
second-operand MINSS/MAXSS selection, and CVTTSS2SI. No x87 emulator is needed for those helpers. Embedded AEX trig algorithms remain
distinct from UCRT; KiraKira and RadialBlur retain their own translated kernels.

**Publication restriction:** `ucrtmath/ms/` and these combined Rust math artifacts
are OLM-internal and must not be published standalone, including on crates.io.
All workspace packages set `publish = false`. Preserve `ucrtmath/NOTICE` and the
separate AMD attribution; see `../ucrtmath/ms/README.md`, `README-double.md` and
`pow.md` for provenance.

## Shared-code candidates (deferred)

These are the candidates recorded by the individual jobs; no hoisting is done
in this integration.

| Source job | Candidate |
| --- | --- |
| ColorKeep / ColorKey | Existing shared world/ROI/checkout/numeric helpers; no additional candidate recorded |
| Blur | Fixed sliders, independent checkbox old-project/default values, full-bounds SmartPreRender union, extra-pixels flag, scoped AEGP resources |
| DistanceGradation | Explicit RGBA default, popup count independent of labels, checked UI parameter/suite guards; native IPP/OpenCV arithmetic stays local |
| DirectionalBlur | MT19937, deterministic out-of-range reads and Directional noise plane, fixed/angle/layer params, scoped checkout/suites, atomic output, active-row SHA-256 |
| KiraKira | Angle/arbitrary kinds, independent popup count, handle/suite guards, UI enable/disable, ramp/Drawbot adapter |
| RadialBlur | Point/Angle/Layer/UI flags, checkout/suite guards, MT19937 float32 conversion, hardware-qualified RCP profile mechanism |
| Smoother | Explicit default ARGB color parameter; contour traversal remains local |
| Smoother2 | Source-identity SHA-256, nonblack color defaults, transactional SmartFX output |
| ToonDilate | Optional pixel-checkin, transactional publish after checkin, custom-UI event registration, extra-pixels flags |

Directional and Radial noise sampling have different rounding/accumulation
orders and must not be substituted. The RCP profile is not a generic math helper.
No job requested a new shared UCRT extern wrapper.

## macOS builds and golden CI

On a Mac with Xcode command-line tools and Rust 1.88.0, from `rust/`:

```sh
rustup target add aarch64-apple-darwin x86_64-apple-darwin
export MACOSX_DEPLOYMENT_TARGET=11.0
cargo test --release --workspace
bash tools/stage_macos.sh local/macos-universal
```

The staging script builds both targets, combines each pair of executables using
`lipo`, verifies the PiPL against the C++ Mac declaration, checks architecture,
minimum OS and entry exports, and writes `local/macos-universal.zip`. Choose a
new destination for each staging run. This needs the full repository's `core/`,
`mac/`, and `ucrtmath/` sources. Nothing is installed into AE or MediaCore.
The same vendored UCRT C sources compile with Apple clang; C/C++ contraction
and fast math remain disabled. No transcendental is replaced with platform libm.

The [workflow](../.github/workflows/rust-macos.yml) runs on Rust/native-source
pushes and PRs, and supports manual dispatch. Native `macos-15` arm64 and
`macos-15-intel` x86_64 runners execute the release workspace tests, including
C++ reference tests and the [original-verified golden corpus](tools/golden/README.md).
Intel tests run natively; Rosetta is not used. A Windows 2025 x64 job runs the same
workspace tests. Tests requiring original AEX files remain opt-in/ignored with
an explicit CI skip message. The arm64 job also cross-builds x86_64 and uploads
a zip of all ten universal bundles. A golden mismatch fails CI.

Radial's `native_reciprocal_profile_and_gaussians` is explicitly ignored on
macOS: it qualifies the capture machine's hardware `RCPSS` instruction, whose
seed bits differ on the Intel Mac runner. Production uses the fixed Windows
profile on both Mac architectures, verified by the original-backed golden
hashes; no algorithm or table is changed. The Windows test remains enabled.
Windows 2025 supplies the 26100-generation UCRT used for native DLL comparison;
Windows 2022's older DLL differs for generated NaN signs.

Each bundle has this layout (DistanceGradation uses the C++ Mac name
`OLMDistanceGradation`, while its Windows original is `DistanceGradation.aex`):

```text
Name.plugin/Contents/
  Info.plist
  PkgInfo                         # eFKTFXTC
  MacOS/Name                      # arm64 + x86_64
  Resources/Name.rsrc             # PiPL 16000, both EffectMain entry declarations
  _CodeSignature/CodeResources    # ad-hoc seal only
```

Bundle identifiers, names, PiPL version/flags/match names, package type and
signature match the C++ Mac port. The Rust executable is a Cargo `cdylib`
(Mach-O dylib); the C++ Xcode target is a Mach-O bundle. The generated Rust
resource uses the same declaration values and the pinned `pipl` serializer
instead of Apple's Rez. Plists are based on the C++ templates, with an explicit
11.0 minimum OS. The package includes the license and UCRT notice; it does not
include the C++ release's installer/readme package.

**Still unverified:** loading and rendering in native macOS After Effects,
project round trips, UI/lifecycle behavior and Gatekeeper acceptance. The bundles
have only local ad-hoc seals for binary integrity, like the C++ packaging script;
they have no Developer ID signature or notarization. CI and the Windows oracle
do not substitute for native AE acceptance. `ucrtmath/ms/` and the combined math
artifacts remain OLM-internal and must not be published standalone.

## Repository hygiene

`rust/.gitignore` excludes target/build workspaces, validation runs, binaries,
rendered pixels, logs and local staging. Existing files are retained locally;
nothing is deleted. Keep source, Cargo lock/manifests, per-crate `VALIDATION.md`,
compact identity/summary JSON, regeneration/capture scripts and required test
vectors. Historical JSON may refer to ignored absolute/local artifact paths;
those are local-only evidence, not missing distributable dependencies.

The four DistanceGradation `.bin` files are small native reference vectors read
by tests, not plug-in executables. `olm-smoother/src/generated.rs` is the sole
source larger than 1 MB: its mechanical instruction translation is required by
the build and deliberately retained without numeric refactoring. The integration
report records exact sizes and the complete would-be-added manifest.
