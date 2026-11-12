# OLM Anti Anti Alias (Rust)

A new CPU implementation of the Windows 2025 OLM Anti Anti Alias, with Smart8,
Smart16 and Smart32 rendering, palette detection and the three palette buttons.
The original parameter declarations and Windows PiPL are preserved.

**Status: direct ordinary-oracle qualification passes.** With the updated
shared AEXCompat host, the new 2025 original matches at 226 cases per depth
and the 2026 sample at 12 per depth; all three preview scales are covered.
The historical bridge is no longer required. See [VALIDATION.md](VALIDATION.md) for exact counts,
identities, failures and remaining acceptance gaps.

## Palette state and project storage

- `Use automatic colors` detects opaque 3×3 color plateaus during each render.
  Those temporary colors do not modify the saved palette.
- `Initalize colors` (the original spelling) clears all 100 colors, detects the
  upstream image at full resolution, and writes detected colors from slot 7.
- `Add automatic colors` preserves active nonblack colors and the first active
  black slot, then fills duplicate-black and inactive slots with new colors.
- `Clear colors list` writes transparent black to all 100 color streams and
  leaves `Number of Colors` unchanged. Init/Add only increase the count.
- The count is ordinary parameter slot/disk ID 1; colors are slots/IDs 7–106.
  Buttons write these through AEGP Stream Suite. There is no arbitrary-data
  palette or persistent sequence-data payload. Native project save/load and
  Undo/Redo remain untested; no AE application was launched.

The match name is exactly `OLM OLM Anti Anti Alias`. The crate contains no
original AEX, runtime DLL forwarding, embedded output tables or network access.
`src/generated/` contains three bounded autoport translations used by the actual
renderer; the remaining render/host logic was translated manually.

## Build and test on this Windows workspace

Run from the repository root, with new output directories each time:

```powershell
python rust/plugins/olm-anti-anti-alias/build_local.py --out rust/plugins/olm-anti-anti-alias/local/my-build
python rust/plugins/olm-anti-anti-alias/build_local.py --test --out rust/plugins/olm-anti-anti-alias/local/my-tests
python rust/plugins/olm-anti-anti-alias/verify_reference.py inventory --candidate rust/plugins/olm-anti-anti-alias/local/my-build/OLMAntiAntiAlias.aex --out rust/plugins/olm-anti-anti-alias/local/my-inventory
```

The helper copies only this crate into an isolated workspace and uses
`D:/olm-rs-target/N-antialias`, offline Cargo and two build jobs. It leaves the
shared workspace lockfile alone. `plugins/*` already admits the new crate; the
shared workspace lockfile now includes both new plug-ins.

On a Mac with Xcode tools and both Rust targets installed:

```sh
python3 rust/plugins/olm-anti-anti-alias/stage_macos.py --out /absolute/new/output
```

That standalone staging helper builds only this crate for arm64 and x86_64,
checks PiPL/entry points, and creates an ad-hoc-signed universal `.plugin`.
The Mac bundle ID is new (`local.olm-rs.anti-anti-alias`); saved-effect identity
continues to use the original match name. No Mac build or native AE acceptance
is claimed. Nothing is installed into an Adobe directory.

## Source and evidence

`algorithm.rs` is independent of AE types. `ae.rs` owns SmartFX checkouts and
snapshots. `ui.rs` owns the AEGP stream/receipt/option lifecycle. `palette.rs`
contains button insertion rules. The `witness` feature is diagnostic-only and
adds direct ABI adapters around the production detector.

`inventory.json`, `declarations.json`, `resources/` and `scaffold.json` are the
initial measured capture, retained as provenance. The TODO descriptions inside
`scaffold.json` describe that capture stage, not the current implementation.
Current results are in [VALIDATION.md](VALIDATION.md) and
[validation-evidence.json](validation-evidence.json). Large raw runs are ignored
under `local/`; regeneration scripts are included beside this README.
