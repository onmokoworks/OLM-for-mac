# Original-verified cross-platform golden corpus

`cargo test --release -p olm-golden --test golden -- --nocapture` runs the
plug-ins' public pure algorithm APIs, without an AE host or AEXCompat. It also
runs as part of `cargo test --release --workspace`. Separate small executables
avoid collisions between the ten crates' exported `EffectMain` symbols. The
tests call Rust algorithms directly; they do not call the C++ reference archives
or the exported AE callbacks.

`golden.json` contains only case IDs and SHA-256 output hashes. `exclusions.json`
contains the input/parameter fingerprints of evidenced original-nondeterministic
cases. The test rejects missing or extra cases, overlapping manifests, duplicate
IDs, and exclusions whose inputs or parameters have changed. Exclusions do not
count as passes. The exact verification counts and original/harness/runner
identities are in `verification.json`.

The Windows verification on 2026-11-12 retained **508 exact cases**: 54 each for
ColorKeep, Blur, ColorKey, DirectionalBlur, DistanceGradation, KiraKira,
Smoother2 and ToonDilate; 36 for Smoother; and 40 for RadialBlur (12/15/13 at
8/16/32 bpc). Radial's other 14 route-cases met the fixed replay exclusion rule
below. All 18 Radial parameter tuples retain coverage. The complete successful
run used `--jobs 2` and 684 original renders (522 baselines plus 162 Radial
replays), with no original errors or timeouts. Full local evidence is under
`rust/local/macos-golden-03/`; the compact committed record retains the
exclusions' original hash sequences and exact-replay results.

There are 18 predefined parameter tuples per plug-in, at every declared depth:
54 planned cases for each of nine effects and 36 for Smoother (522 total).
Every tuple uses a reproducible xorshift32 image, with seed
`0x4f4c4d01 + 7919 * tuple_index`, dimensions 9x7/11x9/17x9 and downsample
1, 1/2 or 1/4. Inputs include opaque palette hits, partial alpha
1/32/128/254, and nonblack RGB under zero alpha. These are finite SDR,
PNG-promoted deep worlds, not arbitrary HDR/NaN or cropped/padded worlds.

| Effect | Parameter coverage |
| --- | --- |
| ColorKeep | Palette counts 0/1/2/5/9/100; exact white/black hits and rejections |
| Blur | Legacy on/off, both bias directions, three amounts/smoothness/repeat values |
| ColorKey | All six spaces, all three precision modes, keep/remove, replacement, premultiplication, component/per-color thresholds, all thin/blur distance and direction modes |
| DirectionalBlur | Angles 0/45/90, front/back/fades/tails, variation and procedural Noise Types 1/2 |
| DistanceGradation | In/Out 1/2/3, both render modes, invert/background, all four interpolation modes, no blur/Box/Gaussian/Bilateral |
| KiraKira | All six declared channels × three declared blur modes, both merge modes, approximated input, all five ray lengths/colors |
| RadialBlur | Zoom/Rotation, both procedural noise types, all three inner/outer offset modes, repeat border on/off, ellipse angle/ratio, strength/fade/size/noise |
| Smoother | Key on/off, six tolerance values including 0 and 255; Classic 8/16 only |
| Smoother2 | Both versions, all gamma modes, key/inverted key, smoothness/extra/range |
| ToonDilate | Six radii including 0, fractional radii and downsample rounding |

The finite corpus chooses nonnegative procedural noise offsets. It makes no
claim that all negative offsets are invalid. Noise Type 3 is outside the
Directional declared popup count and Radial's qualified lifecycle lane; it is
not generated. Active DistanceGradation Median is omitted because originals
can return error 512. Kira's undeclared Blur 4 and custom ramps are outside its
qualified render lane. Its Gain is explicitly 1, within the declared [1,100]
range, and the prescribed patched harness preserves untouched ramp defaults.
See the respective plug-ins' `VALIDATION.md` for the retained boundaries.

## Regenerate on Windows against the originals

From `rust/`, with Python, Pillow, NumPy, Rust 1.88.0, MSVC SDK and clang-cl:

```powershell
python tools/golden/regenerate.py `
  --originals 'D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex' `
  --harness 'D:/Projects/01_Project/04_Tools/AEXCompat-wt-main/broker/target/release/aexcompat-harness.exe' `
  --kira-harness 'D:/AEXCompatWorktrees/olm-diag-kirakira/broker/target/release/aexcompat-harness.exe' `
  --out local/golden-new --jobs 2
cargo test --release -p olm-golden --test golden -- --nocapture
```

Use a fresh output directory. The command builds the pure runners, exports
their exact PNG source bytes and parameter assignments, renders the original
AEX with the same assignments/downsample, and compares complete buffers before
hashing. Hashes are packed RGBA bytes at 8 bpc, little-endian AE-range uint16
words at 16 bpc, and little-endian IEEE binary32 words at 32 bpc. No tolerance,
float comparison, NaN canonicalization or image encoding enters the comparison.
PNG-to-world promotion matches the experimental harness's
`minihost/src/render_pixel_transport.cpp`: binary32 multiplication by `1/255`,
then `*32768 + 0.5` and truncation for PF16. Parameter colors use the separate
host color conversion. They must not be conflated.

The baseline plus **three fixed replays** is run for every Radial case, and its
pure runner is independently executed four times. A Radial exclusion requires
all original renders to succeed, changing original hashes, identical pure
buffers and at least one exact original/pure pair. Stable mismatches, missing
outputs, errors and timeouts fail regeneration. At least 30 Radial cases,
10 per depth, and every parameter tuple must survive. This applies the
original-vs-original exclusion rule in Radial's validation report; there is no
case-index blacklist, retry-until-pass or offset-based dismissal. Other
effects receive one original render per case and no automatic exclusions.

Only a complete, successful all-ten run writes the committed manifests.
`--only` and `--limit` are diagnostic options and never publish golden files.
`--bin-dir` selects already-built runners; their executable hashes are recorded.
Originals stay external and are never copied into the repository. Full raw
outputs, requests and process logs stay in the local output directory. The
shared oracle's Windows Job owner waits for each process tree to exit; a cleanup
failure raises an error. CI has no originals and cannot regenerate these files.

## macOS packaging helper

`package_macos.py` is called by `../stage_macos.sh`. The pinned PiPL crate writes
classic resource files directly, with resource type `PiPL` and ID 16000; Rez and
an Adobe SDK installation are unnecessary for the Rust build. The helper parses
the resource map and checks declarations against the C++ `*PiPL.r`, checks the
two architecture resources are identical, and uses the C++ plist/Xcode bundle
identifier. It checks both executable exports and minimum deployment versions,
then creates and verifies an ad-hoc seal after `lipo`. There is no Developer ID
signature or notarization, and the helper does not install into MediaCore.
