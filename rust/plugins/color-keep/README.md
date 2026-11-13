# OLM Color Keep 1.1.0

Rust CPU port of the **2026-11-12 upstream release**, using the Windows
64/2025 build as the declaration and rendering reference. The 64/2026 build
has the same parameters and sampled rendering behavior; its PiPL SDK minor is
29 instead of 28. The Rust Windows PiPL targets the primary 2025 build.

## Changes from the previous release

- Up to **200 kept colors**, with 201 controls excluding the input layer.
- Display name `OLM Color Keep`, Windows entry alias `entry_point`, effect
  version **1.1.0**. Match name remains `OLM Color Keep`.
- A match compares **RGB only** at every depth. Source alpha is retained for a
  matching color and cleared otherwise; RGB is preserved either way.
- 8/16-bit source channels are normalized with the original binary32
  multipliers before comparison. Each channel difference must not exceed the
  binary32 value of `0.0001`. This replaces the old integer palette
  quantization. The machine-code unordered-comparison behavior is preserved.

Existing parameter IDs, order, types and palette defaults are retained; colors
101–200 are appended. `Enabled Color Num` retains ID 1 and default 1, with its
valid/display maxima raised from 100 to 200. This preserves the serialized
declaration structure of old projects. Their appearance can change, as it does
with the new original: matching translucent pixels now retain their alpha, and
16-bit near-matches can be accepted. No old-version rendering switch or invented
migration conversion is added. Native AE project loading and round trips are
not verified.

See [VALIDATION.md](VALIDATION.md) and
[upstream-validation.json](upstream-validation.json) for exact counts, identities,
function evidence, the golden-manifest follow-up and qualification limits.

## Reproduce on the configured Windows machine

```powershell
python rust/plugins/color-keep/validate_upstream.py build
python rust/plugins/color-keep/validate_upstream.py metadata
python rust/plugins/color-keep/validate_upstream.py campaigns
python rust/plugins/color-keep/validate_upstream.py witnesses
python rust/plugins/color-keep/validate_upstream.py supplement
python rust/plugins/color-keep/validate_upstream.py recordings
python rust/plugins/color-keep/validate_upstream.py golden
python rust/plugins/color-keep/validate_upstream.py sensitivity
python rust/plugins/color-keep/validate_upstream.py diagnose_change
python rust/plugins/color-keep/validate_upstream.py report
```

Use a fresh `OUT` location in the script for another run; completed evidence is
not overwritten by campaign tools. The helper compiles the actual `src/lib.rs`
and `build.rs` through a private manifest under ignored `validation/build/` and
uses `CARGO_TARGET_DIR=D:/olm-rs-target/Up-colorkeep`, two workers maximum. This
avoids changing the shared Cargo.lock while other jobs update workspace members.
The normal workspace package remains `color-keep`.

The `report` phase aggregates the runtime results together with the retained
Ghidra/funcdb/triage and build-equivalence artifacts from this job. A fresh
qualification must also collect those static artifacts; the render commands
alone do not recreate them.

`upstream_hub.py` redirects the shared hub implementation into this crate's
private ignored project; use `start --port <free-port> --workers 2`, then
`stop` and `status`. It does not open the shared Ghidra project. The test-only
`witness_adapter.rs`, `record_adapter.rs` and `golden_probe.rs` call the production
pixel/render API; they are not included in the production plugin manifest.

No original binaries are included or installed. Local binary/renderer artifacts
remain ignored. Combined artifacts using `olm-math`/UCRT-derived code are
OLM-internal and must not be published standalone.
