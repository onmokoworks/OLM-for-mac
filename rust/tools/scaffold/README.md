# Original-AEX Rust scaffold generator

`olm_scaffold.py new --aex X.aex --crate-name NAME --out DIR` creates a standalone,
building Windows x64 Rust effect crate. It copies declarations and the original
PiPL resource, **not the original algorithm**. `algorithm.rs` is an explicitly
marked input-copy TODO. No existing plug-in crate is read by the generator or
modified by this tool.

## Usage

Requirements: Windows x64, Python 3.11+, `pefile`, NumPy and Pillow, Cargo/Rust
(tested with the installed 1.88 toolchain), MSVC/Windows resource compiler, and
the shared AEXCompat harness. Rust dependencies must already be cached: proxy
bootstrap uses `cargo build --offline --locked -j 2`. The bundled proxy lockfile
pins its dependencies; generated packages pin the AE bindings to
`0e0b197850f28c1bb24e8c82fce2e3d4c120d1e9` and `winres` to `0.1.12`.

From the repository root:

```powershell
python rust/tools/scaffold/olm_scaffold.py new --aex 'D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex/OLMBlur.aex' --crate-name scaffold-worked-blur --out rust/tools/scaffold/local/worked-example
cargo build --release --offline --manifest-path rust/tools/scaffold/local/worked-example/Cargo.toml -j 2
cargo test --release --offline --manifest-path rust/tools/scaffold/local/worked-example/Cargo.toml -j 2
python rust/tools/scaffold/local/worked-example/verify_reference.py inventory --out rust/tools/scaffold/local/worked-example/local/inventory
```

Choose **new directories** when repeating the example. `new` refuses existing
outputs and destinations beneath `rust/plugins`. Generated packages contain an
empty `[workspace]`, so the ten verification crates do not join the production
workspace. Their generated `oracle.json` describes the original, candidate,
harness, declared routes, seed and one-worker render settings.

`--harness PATH` overrides the harness. `--timeout SECONDS` bounds each inspection.
`--probe PATH` reuses an already built bundled capture proxy; without it, the
generator stages one in a fresh ignored `local/capture-*` directory. Compilation
honors `CARGO_TARGET_DIR` when set, otherwise uses that capture's `target/`.
This keeps concurrent jobs' build artifacts in their assigned target directory. The proxy
is only an inspection instrument and must not be installed in AE.

`verify_reference.py` reads `oracle.json`, stages a single-link `.aex` copy of
the generated DLL under `local/`, and invokes `olm_oracle.py`. Cargo DLLs can be
hardlinks, which AEXCompat rejects for dependency closure inspection. Its `render`
mode is a reference-test entry point **expected to differ until the algorithm is
ported**. It does not rewrite mismatches or treat them as passing.

## Generated files

| File | Purpose |
| --- | --- |
| `Cargo.toml`, `build.rs`, `resources/pipl-*.bin` | Standalone rlib/cdylib; `winres` embeds each complete original resource, preserving ID, type and language |
| `src/params.rs` | Ordered raw AE declarations, saved-project IDs, flags, UI flags/sizes, exact numeric bits, popup strings/counts, groups and distinct initial/default values |
| `src/ae.rs` | Original PiPL entry alias plus `EffectMain`; runtime version/flags; CPU SmartFX or Classic dispatch, depth checks, checked world spans and scope-bound pixel checkin |
| `src/algorithm.rs` | Pure, AE-free byte-copy stub; crop/origin handling and untouched row padding |
| `src/arbitrary.rs` | Opaque flat-byte handle lifecycle, including copy and save/load |
| `src/ui.rs` | Explicit dynamic/custom UI TODO |
| `oracle.json`, `verify_reference.py` | Configured inventory/render entry point |
| `VALIDATION.md` | Fill-in validation record; explicitly not a completed algorithm port |
| `tests/reference.rs` | Ignored original-reference skeleton that fails if enabled without implementation |
| `tests/passthrough.rs`, `src/arbitrary_tests.rs` | Copy/layout and opaque-callback tests |
| `inventory.json`, `declarations.json`, `scaffold.json` | Original inspection, supplementary declarations, hashes, provenance and per-effect limitations |

Only the Windows PiPL is generated. A macOS compile can exercise the pure module,
but it is **not** a usable Mac AE plug-in: Mac entries, PiPL and bundle packaging
still need implementation. Unsupported parameter types, conflicting PiPL effects,
unavailable arbitrary defaults, non-contiguous slots, and PluginData registration
contracts are rejected rather than guessed.

## Why supplementary capture is necessary

The public AEXCompat inventory exposes parameter kinds/defaults, UI and host
ranges, popup choices, control sizes, supervision and host flags. It does not
expose all disk IDs, flags, numeric display fields, raw byte labels, or the
distinction between `value` and `dephault`. PiPL does not contain those fields.
Filling them from inventory alone would silently produce an incompatible crate.

The Rust `probe/` cdylib therefore runs **inside AEXCompat's worker** and loads
the original in place. It forwards selectors and intercepts the real host's
`add_param` and `register_ui` callbacks during `PARAMS_SETUP`. It records typed
scalar fields and strings, restores the callbacks, and asks the original's own
arbitrary callbacks for flattened defaults. It neither copies the original
executable nor invents host suites. Every captured type/slot/count/runtime flag
is checked against the independent public inventory before generation.

Floats are emitted with `from_bits`; fixed sliders retain raw 16.16 integers.
Labels retain original bytes, including checkbox labels. Pointer addresses,
reserved/padding bytes and original in-memory arbitrary layouts are not emitted.
This is declaration capture, not automatic reverse engineering of behavior.

All harness and bootstrap invocations use the shared oracle's suspended-child
Windows Job ownership. Normal completion, exceptions and timeouts close the
owned job, wait for its process tree to reach zero, and reap the child. Logs keep
the exact command/PID/result. The proxy module lasts only for that worker's
lifetime. There are no watchers, detached servers, AE launches, installations,
commits, or original-AEX copies. Local captures and verification outputs remain
ignored; only this directory is owned. The tiny outer Cargo package is a marker
for the existing `tools/*` workspace glob, avoiding a root-manifest edit.

## What the existing ten crates have in common

The implementation study covered their parameter setup, build scripts, exported
aliases, local adapters, shared `olm-ae`, UI modules and KiraKira's arbitrary ABI
test. The generated adapter is self-contained over the pinned `after-effects-sys`
bindings because the shared `Kind` abstraction cannot represent all declarations.

- All ten retain Windows PiPL binary resources through `winres`. The pinned PiPL
  RC string emitter is code-page sensitive; the original short `eINF` declaration
  and non-ASCII version bytes must survive unchanged. The generator extracts
  bytes directly, requiring no reconstruct-and-patch step.
- Aliases are `entryPointFunc` or `entry_point`; `EffectMain` remains a usable
  standard entry. Native Mac PluginData entry registration is a separate concern.
- Nine use SmartFX 8/16/32; Smoother is Classic 8/16 only. Existing adapters have
  effect-specific Classic refusals, ROI rules, extra-pixel behavior and host
  state. The generic copy stub uses only the normal declared routes, without
  pretending those effect-specific contracts were reconstructed.
- Blur distinguishes an initial Legacy value from its new-instance default and
  has a fixed percentage slider. Color defaults differ by effect. KiraKira and
  Directional contain inconsistent popup declaration/label counts. None of these
  are normalized. KiraKira Gain's declared approximately 0.1 default remains
  outside its [1,100] range.
- Dynamic UI uses ParamUtils and/or AEGP streams; KiraKira additionally implements
  Drawbot/editor interaction and arbitrary ramps. Inventory snapshots reveal
  declarations, not conditional update rules.

## Per-plug-in result and remaining work

All rows passed release build, full public inventory equality, complete PiPL
byte/resource identity, and supplemental declaration recapture. Counts exclude
input slot zero. Every algorithm is a TODO; the final column lists additional
behavior that was not generated. A zero event mask is not proof that an original
has no dynamic UI.

| Original | Params | Normal CPU routes | Additional manual work |
| --- | ---: | --- | --- |
| ColorKeep | 101 | Smart 8/16/32 | Palette-count behavior beyond declarations and original host/ROI semantics |
| DistanceGradation | 12 | Smart 8/16/32 | In/Out, interpolation, color/background and blur UI enable rules; original ROI/layer processing |
| OLMBlur | 5 | Smart 8/16/32 | Legacy migration behavior beyond captured value/default; original Classic/debug contract |
| OLMColorKey | 223 | Smart 8/16/32 | Palette/replace and edge-control behavior beyond declarations; cropped/ROI contract |
| OLMDirectionalBlur | 21 | Smart 8/16/32 | Noise-type/layer visibility, AEGP state and secondary-layer use |
| OLMKiraKira | 40 | Smart 8/16/32 | Five ramp semantics, Drawbot editor/events and dynamic controls; event mask 4 is retained |
| OLMRadialBlur | 30 | Smart 8/16/32 | Zoom/Rotation enable rules, noise-layer visibility/use, geometry and host state |
| OLMSmoother | 3 | Classic 8/16 | Original extent behavior and saved-project/native-host acceptance; no Smart/32 route added |
| OLMSmoother2 | 15 | Smart 8/16/32 | Key/gamma enable rules and conditional gamma-palette visibility |
| OLMToonDilate | 1 | Smart 8/16/32 | Original custom-event behavior (mask 4), sequence/context and ROI expansion |

KiraKira slots 14, 20, 26, 32 and 38 each capture a **325-byte** flattened default.
The stub stores flattened bytes in a host handle behind its own length header.
Unflatten → copy → flatten preserves all bytes, including unknown or inactive
ones. New-instance defaults use the captured bytes; no original in-memory pointer
or 324-byte ramp structure is reused. Original inactive capacity can contain
unstable data, so repeat captures may differ there. No semantic validity is
inferred. Bytewise comparison is provided; interpolation succeeds only at exact
endpoints or identical payloads. Interior interpolation, semantic equality,
print/scan, parsing, editing and original ramp rendering require a port.

## Verification and worked run

On this Windows machine, the worked OLMBlur command above (without `--probe`)
built its own proxy and generated five parameters. Its release build exited 0;
the generated verification wrapper printed:

```text
inventory: identical (all exposed parameter and host fields)
```

The full runner performs ten sequential generations, release builds and tests,
then invokes **`olm_oracle.py inventory`** for each original/candidate pair. It
also extracts and compares full PiPL bytes, resource names/types/languages, and
recaptures generated declarations to cover fields omitted by the public oracle.

```powershell
python -m unittest discover -s rust/tools/scaffold -p test_scaffold.py -v
python rust/tools/scaffold/verify_all.py --out rust/tools/scaffold/local/all-ten-final
python rust/tools/scaffold/smoke_routes.py --summary rust/tools/scaffold/local/all-ten-final/summary.json --out rust/tools/scaffold/local/routes-final
```

The retained run has **10/10 builds**, **10/10 inventories**, **10/10 complete PiPL
matches**, **451 parameter declarations** with no supplemental differences,
**30 generated Rust tests passed** and **10 deliberately ignored reference
skeletons**. The Python unit suite passes **10 tests**. See
[`evidence/verification.json`](evidence/verification.json) for binary/resource
hashes, commands, log bindings and per-effect results.

The separate route smoke checks **29 normal route/depth cells**, one 7×5 input
per cell at full resolution, against independently constructed 0/maximum endpoint
RGBA pixels (PNG8, raw uint16 and float bit-pattern outputs). All copy exactly.
This tests the scaffold's AE wiring, not original algorithm equivalence. Padding,
origins/crops and all-depth arbitrary pixel bits are covered by the pure tests;
the opaque tests exercise empty and unknown payloads, copy, flatten/unflatten,
compare, interpolation refusal, guard bytes and handle/suite cleanup.

No original-render equivalence, randomized original render campaign, native AE
UI/project round trip, Mac binary/bundle, temporal behavior, GPU behavior or full
SmartFX geometry contract is claimed. `VALIDATION.md` keeps those gates open.
