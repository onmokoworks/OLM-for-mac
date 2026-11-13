# OLMRadialBlur Rust port

The pure Rust renderer implements Zoom and Rotation at ARGB8, ARGB16 (white =
32768) and ARGB32F. It follows the C++ polar producer, size-component pass,
noise composition, fade prepass, ordered scatter, normalization and inverse
sampler. The host adapter preserves the 30 parameters, disk IDs, metadata and
Windows `entry_point` export. The Windows PiPL is byte-identical to the original.

`algorithm.rs` contains no AE types. `math.rs` retains the embedded AEX
polynomials; UCRT imports go through `olm-math` in FMA mode. `noise.rs` implements
MT19937 and the original float32 canonical conversion. `glue.rs` is a local
extension of the pilot AE boundary for Point, Angle and Layer declarations,
because those types are not yet exposed by shared `olm-ae`.

Active Noise Type 3 is refused before writing output. As in the C++ owner, an
all-zero Strength/Offset/Fade tuple first takes the identity-copy shortcut.
The original exported path
forwards an uninitialized Noise Layer destination and violates host ownership
invariants. This is the documented RadialBlur Type 3 refusal, not a fabricated
reference image. Type 3 is excluded and explicitly recorded in every comparison
campaign. See `refs/conformance/olmradialblur_type3_exported_upstream_boundary_20260814.*`
and `.codex-jobs/A-diag/report.md` section 2.

The native Windows Gaussian builder uses an RCPPS estimate followed by separate
Newton operations. The C++ emulator substitutes division for that initial
estimate. This port records the validation CPU's estimate as a 4096-entry
significand profile and uses exponent scaling, independently qualified against
all 8,388,608 normal significands and all Gaussian-length denominators from 2
through 30,000. The profile is CPU-instruction data, independent of image
fixtures. Tests retain the C++ division-seed comparison and separately compare
the production profile to native SSE. See `VALIDATION.md` for the hardware bound.

Rotation at high Quality is computationally expensive, as in the original.
No FFT approximation or reassociation is used. Row jobs have disjoint output
ownership; the AE adapter uses one worker per frame and validation runs three
independent frames concurrently.

```powershell
$env:CARGO_TARGET_DIR='D:\olm-rs-target\P-radial'
cargo build --release -p olm-radial-blur -j 2
cargo test --release -p olm-radial-blur -j 2
```

Run these commands from `rust/`. The hardware-profile regeneration test is
ignored by default because it deliberately writes an owned source file.
Ordinary tests verify the committed profile without changing it.

The crate is OLM-internal and `publish = false`. In particular, the combined
`ucrtmath/ms` implementation must not be published standalone. Its existing
NOTICE and provenance apply.
