# OLM Distance Gradation — Rust port

Targets the **2026-11-12 upstream release**, with the Windows 2025 AEX as the
declaration and pixel reference. The upstream effect version is 0.8.3 Develop.
The implementation is Rust; production rendering does not load the original
AEX, OpenCV, or IPP. The C++ reference archive is used only by unit tests.

## Release changes

- Appends **Use Padding**, slot/disk ID 13, default off. It creates transparent
  space around the input, so fully opaque layers can have an edge gradient.
  SmartPreRender reports the expanded extent; rendering offsets the source
  within that extent. Inside uses at least one preview pixel of border;
  Outside/Both can use the outside threshold as the full-resolution border.
- Raises the Inside and Outside slider display maxima from 512 to 1000.
  Their valid maxima were already 1000.
- Updates PiPL/global version and flags, including `RETURNS_EXTRA_PIXELS`.
- Changes distance normalization: a field whose maximum is below the requested
  threshold retains that reduced range instead of stretching to full range.
  This intentionally changes existing renders even with padding disabled.
- Matches the exercised native IPP square-root and linear-resize arithmetic,
  including FMA, vector groups, and scalar tails. Bilateral size zero still
  executes its radius-one filter, including at 16 bpc.
- Uses masked copies to combine Inside and Outside in Both mode. This matters
  when fractional preview padding makes the resized fields overlap at edges.

The approximately 26 MB upstream binary already contained OpenCV 4.5.5 and IPP.
The release adds no PE imports; its `IPPCODE` and `IPPDATA` sections are identical
to the old binary. See [the static audit](upstream-static-report.json).

## Project compatibility

Existing slots/disk IDs 1–12, types, order, defaults, and effect match name are
retained. The new checkbox is appended, not inserted. Old projects can resolve
their existing controls, but the upstream normalization change means their
appearance is not guaranteed to remain the same. No migration conversion is
invented. The unusual native popup count/labels and default In/Out declaration
are intentionally preserved.

The complete parameter declarations and Windows PiPL target the 2025 build.
The 2026 build changes the PiPL SDK minor version and Power's curve tolerance;
pixel samples are qualified separately in [VALIDATION.md](VALIDATION.md).

## Build and qualification

Normal workspace commands are `cargo build --release -p olm-distance-gradation`
and `cargo test --release -p olm-distance-gradation`, from `rust/`.
For the concurrent update job, `python tests/update_build.py build` and
`python tests/update_build.py test` use an isolated dependency/source snapshot
under the ignored `validation/upstream/build-tree/`, with Cargo output in
`D:/olm-rs-target/Up-dgrad`. This avoids changing the shared workspace lockfile.

`stage-dump` is an opt-in diagnostic feature. Its native witness exports,
captured CPU table generator, and render-stage hooks are absent from the
default build. Do not install diagnostic AEX files.

[VALIDATION.md](VALIDATION.md) and [the compact update report](upstream-validation-report.json)
record the exact corpus, failures, original instability, and limitations.
Qualification uses AEXCompat Smart8/16/32 on Windows, not native AE or macOS.
The square-root approximation table represents the tested x86 CPU profile;
native allocation alignment can also alter the original's last-bit results.
The Rust implementation uses a deterministic canonical alignment. These
differences are measured explicitly rather than hidden behind a tolerance.

The shared golden owner must regenerate the 54 DistanceGradation hashes against
the new original. Its current tool only publishes a complete all-ten corpus,
so this crate-only update does not rewrite the shared golden manifests.
The runner's explicit `Params` literal also needs `use_padding: false` to compile;
the exact handoff is listed in VALIDATION.md.
