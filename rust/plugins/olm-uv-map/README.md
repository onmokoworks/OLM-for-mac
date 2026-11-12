# OLM UV Map — Rust

CPU port of the Windows 2025 OLM UV Map effect, with a texture-layer parameter
and Nearest Neighbor, Bilinear, and Trilinear interpolation. Red/green in the
input encode U/V, V is inverted for texture coordinates, and input alpha masks
the sampled alpha. The implementation preserves the original mipmap weighting,
rounding, alpha order, and UV derivative calculations.

`src/algorithm.rs` is independent of AE. `src/ae.rs` supplies the CPU SmartFX
8/16/32bpc adapter, parameter/pixel checkout lifetimes, and output extent walk.
Texture dimensions are independent of input dimensions. `src/ui.rs` enables
Smoothness for Trilinear. Exact Windows PiPL bytes and parameter declarations
are captured from the original; the Mac PiPL declares both Intel64 and ARM64.

See [VALIDATION.md](VALIDATION.md) for measured coverage and limits. Native AE
loading, saved-project round trips, and a macOS build are not yet qualified.
This crate is not installed in AE by any of the following commands.

## Build and tests

From the repository root on this Windows machine:

```powershell
$env:CARGO_TARGET_DIR='D:/olm-rs-target/N-uvmap'
cargo build --manifest-path rust/Cargo.toml --release --offline -p olm-uv-map -j 2
cargo test --manifest-path rust/Cargo.toml --release --offline -p olm-uv-map -j 2
cargo clippy --manifest-path rust/Cargo.toml --release --offline -p olm-uv-map -j 2 -- -D warnings
python rust/plugins/olm-uv-map/verify_reference.py inventory --out rust/plugins/olm-uv-map/local/inventory-new
python rust/plugins/olm-uv-map/verify_reference.py render --cases 103 --seed 20261113 --jobs 3 --out rust/plugins/olm-uv-map/local/seed-a-new
python rust/plugins/olm-uv-map/verify_reference.py render --cases 103 --seed 20261114 --jobs 3 --layer-sizes 8x16,33x17,1x5,2x1,1x1,17x9 --out rust/plugins/olm-uv-map/local/seed-b-new
```

The wrapper stages a single-link `.aex` because Cargo can hardlink its DLL.
`oracle.json` records local original/harness paths; `--candidate` overrides the
job target. The first three oracle cases are default/minimum/maximum, followed
by random cases. Use a fresh output directory for each campaign.

Twelve Rust tests include nine original-backed golden fixtures (all three
methods at all three depths), absent texture/padding, independent texture size,
and the scaffold's opaque-handle lifecycle check. Golden bytes are inputs and
outputs, never original executable code. `capture_golden.py` only accepts
hash-verified exact oracle cases and records provenance beside the fixtures.

`validate_functions.py` calls original functions and Rust ABI bridges through
the witness host. Build with `--features witness`, stage a separate `.aex`,
then pass it with `--candidate` and a fresh `--out`. Rebuild without the feature
for the production DLL. `validate_numerics.py` independently compares the local
logf extension against UCRT. `validate_geometry.py` retains the currently
unsupported custom-world-layout probe rather than silently claiming it passed.

## macOS integration

The pure Rust kernel, AE binding cfg, and Mac PiPL source are present. On a Mac
with cached pinned dependencies, build `olm-uv-map` for
`aarch64-apple-darwin` and `x86_64-apple-darwin`; combine the resulting
`libolm_uv_map.dylib` files into `OLMUVMap.plugin/Contents/MacOS/OLMUVMap`.
The bundle also needs the generated PiPL resource, Info.plist, PkgInfo and
signing, following the workspace's existing bundle layout. The shared packaging
tool is outside this job's ownership and its plug-in list needs an OLMUVMap
entry. No Mac build or bundle is claimed from this Windows job.

Numerical code and extracted UCRT constants are OLM-internal; see
[NUMERICS.md](NUMERICS.md). Do not publish those math artifacts standalone.
