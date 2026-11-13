# OLM Smoother2 — upstream 2026-11-12

Rust CPU port of effect 2.2.0. Windows AE 2025 is the primary reference;
the AE 2026 original is separately sampled. See [VALIDATION.md](VALIDATION.md)
for measured coverage and retained evidence. No native AE or macOS validation
is implied by the Windows headless results.

This update adds the original's `v2 (Oklab)` mode, including its exact matrix
operation order, UCRT `cbrtf`, Oklab distance metric and output conversion.
Gamma correction is disabled in that mode and its color controls are hidden.
The Version popup is supervised and retains default 2. Smooth Range is now a
one-decimal float slider. The new release also fixes the penultimate column's
top-right classification and uses float multiplication by 0.01 for the range.
Clamping occurs after conversion back to the output color space.

The match name, 15 control slots and disk IDs are retained. **Saved-project
migration risk:** slot 6 / disk ID 5 changes from integer to float. This port
matches the new original declaration without inventing an integer/keyframe
conversion. Native saved-project and animated-keyframe migration is untested.
Older versions remain selectable, but their right-edge output follows the
new upstream fix.

The pure `Params` integer-range API remains source-compatible. Call
`algorithm::render_with_range` with a float range in UI units for fractional
values; the AE adapter always uses that entry point.

`oklab::cbrtf` is a local **olm-math hoisting candidate**. It implements the
observed scalar UCRT algorithm using `olm_math::x86` arithmetic, with no host
libm, power approximation or output lookup table. Like the shared UCRT ports,
it is OLM-internal and must not be published standalone. Its contract is return
bits under round-to-nearest and gradual underflow, not errno/FP exception flags.

Build and test from the repository root:

```powershell
$env:CARGO_TARGET_DIR = 'D:/olm-rs-target/Up-smoother2'
cargo build --manifest-path rust/Cargo.toml --release --offline -p olm-smoother2 -j 2
cargo test --manifest-path rust/Cargo.toml --release --offline -p olm-smoother2 -j 2 --lib
```

The diagnostic example `upstream_witness` exposes only test ABI adapters.
`verify_upstream_leaves.py`, `verify_upstream_classes.py`,
`replay_upstream_record.py`, and `minimize_upstream_class.py` retain focused
native checks. `run_upstream_validation.py --resident --prefix NEW_NAME`
runs the final two-seed corpus plus fresh-process 2025/2026 controls against
`upstream-work/OLMSmoother2-final.aex`. Output directories must be fresh.
The isolated `update_hub.py` launcher must be explicitly stopped after use.

Shared golden manifests still describe the old release. The golden tool's
`--only olm-smoother2` is diagnostic and cannot publish a per-plugin update;
its owner must regenerate the 54 Smoother2 hashes against the new original,
and add Oklab/fractional-range tuples. No shared golden/tool source is edited
by this crate update.
