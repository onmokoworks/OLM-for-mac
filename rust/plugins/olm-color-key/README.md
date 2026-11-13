# OLM Color Key

Rust CPU port targeting the **2026-11-12 release, effect 2.3.3**, with the AE
2025 build as the primary reference. The pure kernel supports 8/16/32 bpc;
the AE adapter declares SmartFX. The ordinary direct oracle
passes 226 cases per depth against the new 2025 original, plus 12 per depth
against 2026, at all three preview scales. Full random assignments include
slots above 1,024; see [VALIDATION.md](VALIDATION.md).

Upstream expands the palette from 25 to 200 colors, appending eight controls
per color (223 to 1,623 controls, excluding the input). All Use Color initial
and default values are now on. Number of Colors accepts 0–200; its slider
display range intentionally remains 0–30. The adapter and kernel accept the
full palette, and the crate handles the original visibility/enabled rules for
all 200 colors. Checkbox labels, declaration flags, and PiPL match the captured
upstream definitions.

Existing slot order, disk IDs and types are retained. Colors 101–200 use the
upstream second ID range; extending the first range would create collisions.
The existing duplicate disk ID 16 belongs to group markers and is preserved.
Explicitly stored old values retain their identity, including disabled Use
Color values. New instances and missing/default-substituted values now use the
new defaults. Native AE project loading, animation and round trips are untested.

Only the palette bound changes in the numerical kernel; color conversions,
comparison arithmetic and distance/edge calculations are retained. Parameter
tables and keys use heap vectors, without a fixed 1,024-control setup limit.
The UI acquires suites and its effect reference once per update and addresses
controls by slot, avoiding an ID-map scan for each of 1,603 visibility changes.
Native AE UI responsiveness and large-frame performance have not been measured.

Build and test from the repository root:

```powershell
$env:CARGO_TARGET_DIR = 'D:/olm-rs-target/Up-colorkey'
cargo build --manifest-path rust/Cargo.toml --release --offline -p olm-color-key -j 2
cargo test --manifest-path rust/Cargo.toml --release --offline -p olm-color-key -j 2
```

`verify_update.py` captures inventories/declarations and runs sparse fixture
comparisons. `witness_pixels.py` compares the three native pixel callbacks with
the optional `upstream-witness` adapters. `capture_pixels.py` uses the existing
record debugger on sparse real renders and replays captured inputs. These
adapters are absent from ordinary builds; do not distribute diagnostic builds.
`hub_local.py` isolates this job's headless Ghidra project and lifecycle files
inside ignored `validation/`, without modifying shared tool sources.

No original binary is bundled. Math dependencies are OLM-internal and must not
be published standalone. No AE installation is performed by these scripts.
