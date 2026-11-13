# Native first-divergence localization

`olm_diverge.py` compares ordered, hash-bound original/Rust stage maps through
[the existing witness](../witness/README.md). It reports the first differing
**element and exact value/bit pair**, retains every stage result, and verifies a
single-call reproducer. `capture.py` starts from a saved
[oracle](../oracle/README.md) render/minimize case, captures the optional Rust
hooks during rendering, then calls the original functions with those exact
inputs. Originals are used in place. There is no L-record dependency.

**Coverage is explicit:** the supplied maps cover DistanceGradation's Gaussian
row/column passes and DirectionalBlur's RGBA rotations. A result is the first
**mapped** divergent stage, not a claim about unobserved earlier stages. The
historical Gaussian issue and deliberate render faults are localized below.
A mismatch confined to other stages is reported as unlocalized, never exact.

## Build

Windows x64, Rust/MSVC, clang-cl, Python 3.11+, `pefile`; capture also uses the
oracle's NumPy/Pillow dependencies. The native witness host must already be built
as described in its README. All combined math artifacts are **OLM-internal and
must not be published standalone**.

Only two production crates have changes: optional `stage-dump = []` features,
new private `stage_dump.rs` modules, their cfg-gated declarations, and cfg-gated
capture calls in `rotate.rs` / `filters.rs`. The features have no default entry.
There are no changes to the oracle, witness, triage, scaffold, shared crates,
workspace manifest, or production build scripts.

From the repository root:

```powershell
powershell -NoProfile -File rust/tools/diverge/build.ps1 `
  -Tree rust/tools/diverge/local/my-build -Target rust/tools/diverge/target
```

Choose a new tree. This copies only these two crates' source/build inputs and
three shared crates into an owned snapshot. Exact junctions to `core/`, `mac/`
and `ucrtmath/` supply read-only C/C++ build inputs. Do not recursively delete or
scan those junctions. Cargo builds offline with two workers in an owned Windows
Job, verifies cleanup, and leaves two diagnostic `.aex` files in `my-build/`.
This avoids depending on other jobs' unfinished `tools/*` workspace members.
The snapshot is for building diagnostic binaries, not the existing Rust test
suite (its reference-test fixture files are not copied).

When the shared workspace is complete, ordinary Cargo works too:

```powershell
cargo build --manifest-path rust/Cargo.toml --release --offline -j 2 `
  -p olm-directional-blur -p olm-distance-gradation `
  --features olm-directional-blur/stage-dump,olm-distance-gradation/stage-dump
```

Never install the diagnostic builds in AE. No GUI or AE is used by this tool.

## Start from an oracle mismatch

```powershell
$harness = 'D:/Projects/01_Project/04_Tools/AEXCompat-wt-main/broker/target/release/aexcompat-harness.exe'
python rust/tools/diverge/capture.py path/to/case-0039-smart32 `
  --candidate rust/tools/diverge/local/my-build/olm_distance_gradation.aex `
  --harness $harness --out rust/tools/diverge/runs/capture-new
```

The case directory must contain `case.json` and its hash-bound assets (the same
format emitted by oracle/minimize). The original and assets are verified. A new
candidate is an explicit diagnostic replacement; its new hash is recorded.
A changed historical harness requires explicit `--harness`. Each side uses the
same saved requests. Outputs include:

- `render/`: actual paired render, requests, comparison and process records.
- `captures/`: actual Rust inputs, intermediates and shape/parameter metadata.
- `stage-NNN/`: exact witness calls on both binaries, comparisons and reproducer.
- `capture-report.json`: first divergent mapped stage and coverage statement.

Capture replay is checked against the actual Rust intermediate hashes, so a
separate diagnostic implementation cannot silently stand in for the render.
The original Gaussian decomposition is checked against a direct full `cvSmooth`
call on **every** run. Directional rotations replay with the actual destination
initializer, preserving the original no-write border behavior.

`--inject INDEX` increments one nonnegative finite float at the middle stage by
one representable word: Gaussian row output or the first rotation output.
The following real render stages consume the changed value. `--historical-sse`
selects DistanceGradation's retained old Gaussian arithmetic. Both options exist
only in explicitly feature-enabled builds. Environment controls are scoped and
restored by `capture.py`: `OLM_STAGE_DUMP_DIR`, `OLM_STAGE_FAULT_INDEX`, and
`OLM_STAGE_HISTORICAL_SSE`. With the feature disabled, none of these controls or
diagnostic exports exist.

## Standalone stage maps and minimal reproducers

Generate a pilot map from a raw stage input, or omit `--input` for the fixed
seed-20261112 input:

```powershell
$originals = 'D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex'
python rust/tools/diverge/stage_maps.py distance `
  --original "$originals/DistanceGradation.aex" `
  --candidate rust/tools/diverge/local/my-build/olm_distance_gradation.aex `
  --width 17 --height 11 --kx 11 --ky 11 --inject 0 `
  --out rust/tools/diverge/runs/map-new.json
python rust/tools/diverge/olm_diverge.py rust/tools/diverge/runs/map-new.json `
  --out rust/tools/diverge/runs/localize-new
python rust/tools/diverge/olm_diverge.py rust/tools/diverge/runs/localize-new/reproducer.json `
  --out rust/tools/diverge/runs/replay-new
```

Input is tightly packed little-endian float32: one field channel for Distance,
RGBA for Directional. Directional `--angle` is the internal angle in **radians**,
not the UI angle. Input/output staging and row padding are not guessed.

Single-call reproducers freeze the pre-call buffers, retain only the transitive
argument/pointer-relocation buffer closure, clear transient pointer addresses,
and remove all other calls. They are independently replayed and their complete
stage hashes must match the first observation. This requires stateless replayable
calls; maps with global-state dependencies can disable `stateless_calls` and keep
the complete batch instead.

Reduce the same input on both sides without changing geometry, parameters or
arithmetic mode:

```powershell
python rust/tools/diverge/minimize.py path/to/reproducer.json `
  --buffer middle --budget 64 --out rust/tools/diverge/runs/reduced-new
```

The reducer zeroes chunks, then single float words. It never accepts timeouts or
errors as preserved mismatches. `one_minimal_under_single_word_zeroing` is true
only after the complete single-word pass; exhausted budgets are explicitly
labelled. This is not globally minimal geometry/parameters. A final fresh replay
is mandatory. Select `input` (the default) for the first pass, `middle` for an
extracted Gaussian column call.

## Generic JSON contract

Schema version 1 has:

- `scope`: mandatory coverage description; `stateless_calls`: opt-in extraction.
- `reference` / `candidate`: `sha256`, `witness` (unchanged public witness spec),
  optional `expected_fma` and `return_bits` keyed by call index.
- Ordered `stages`: unique `id`, `dtype`, positive `shape`, `grounding`, and
  per-side `{call, buffer, offset?}` selectors. Calls must be in nondecreasing
  order. `dtype` is any signed/unsigned 8/16/32/64-bit integer or `f32`/`f64`.
- Optional `controls`: `{side, call, left, right}` buffer-equality invariants.

A candidate call can use `export` instead of `rva`; the PE export table is read
without loading the binary in Python. Everything else is delegated to witness's
typed ABI, bounds, guard bytes, timeout and owned-process machinery. Binary
hashes prevent reusing RVAs against an unreviewed version. Changed signatures,
missing outputs, failing diagnostic returns, failed controls and unstable
reproducers produce `incomplete`, never a successful localization.

`olm_diverge.py` exit codes: 0 exact mapped stages, 1 divergent, 2 incomplete.
`capture.py`: 0 actual render plus mapped stages exact, 1 localized within mapped
stages, 2 incomplete/unlocalized. Signed zeros and NaN payloads compare as raw
bits. Reports include nonfinite values as JSON strings, retaining authoritative
bit patterns.

## Grounded maps

| Original | RVA / native ABI | Rust boundary | Authority |
| --- | --- | --- | --- |
| DirectionalBlur | `0x1ec0(src*, dst*, u32 w, u32 h, f32 angle)` | `rotate::rgba` | [IR input rotate](../../../notes/IR_OLMDirectionalBlur.md), [native ABI witness](../../../tools/emulation/test_dblur_rotate_exact.py) |
| DistanceGradation | `0x12864d0(CvMat*, CvMat*, i32 mode, i32 kx, i32 ky, f64, f64)` | `filters::gaussian_mode` row / column | [VALIDATION](../../plugins/olm-distance-gradation/VALIDATION.md), [CvMat capture ABI](../../plugins/olm-distance-gradation/tests/capture_native_gaussian.py) |

Original SHA-256s are pinned in `stage_maps.py`. Gaussian uses mode 2, zero
sigmas, 40-byte x64 CvMat headers with data relocation at offset 24. It separates
`kx x 1` then `1 x ky` and verifies equivalence to `kx x ky`. The supplied
separable map refuses singleton axes and the special 3x3 dispatch rather than
asserting an unqualified equivalence. Apertures are odd, 1..8193.

## Measured verification on this machine

Windows x64, Python 3.11.9, Rust 1.88.0, native UCRT FMA enabled. Full local
artifacts are ignored under `runs/verified-final/`, `runs/case39-minimized/`,
`runs/directional-render-{clean,injected}/`, `runs/distance-render-injected/`.
Compact, hash-bound results are retained in [evidence](evidence/verification.json).

| Run | Result |
| --- | --- |
| Directional 17x11 rotation-pair control | Input, forward and inverse stages exact |
| Directional one-ULP injection, element 372 | First `rotate.forward`; 1 middle element differs; downstream output differs; single-call replay verified |
| Distance 17x11, 11x11 Gaussian control | Input, row and column exact; full native filter control exact |
| Distance one-ULP injection, element 0 | First `gaussian.row`; 1 middle element differs; downstream output differs; single-call replay verified |
| Actual Directional Smart32 31x19 render | Clean exact; injected first rotation at padded element 3360 changes **3 output samples**, correctly names `rotate[0]` |
| Actual Distance Smart32 97x61 render | Injected row element 0 changes **31 output samples**, correctly names `gaussian.row` |
| Historical seed-20261112 case 39, 97x61, radius 4096 | **1,706 output samples** differ with old SSE arithmetic, exactly reproducing the documented issue; row exact, first `gaussian.column` (2,362 float elements differ) |
| Same saved historical case, current FMA | Actual render and every mapped stage exact |

Historical first column difference: element 4, `(y=0,x=4)`, original
`0x3cf45516` / `0.02982572838664055`, old Rust `0x3cf45517` /
`0.029825730249285698`. Captured row and column outputs equal independent Rust
replays; the isolated column reproducer also matches complete stage hashes.

The historical column input reduces from **5,917 nonzero floats to one** in
14 reduction trials. The remaining value is index 5915, bits `0x3c9784c5`.
Zeroing it removes the mismatch. Geometry stays 97x61, vertical aperture 8193.
It yields 51 differing words, first index 192: original `0x3c11c35b`, old Rust
`0x3c11c35a`. Regenerate this compact reproducer without historical run files:

```powershell
python rust/tools/diverge/examples.py historical-column `
  --original "$originals/DistanceGradation.aex" `
  --candidate rust/tools/diverge/local/my-build/olm_distance_gradation.aex `
  --out rust/tools/diverge/runs/historical-small-new.json
python rust/tools/diverge/olm_diverge.py rust/tools/diverge/runs/historical-small-new.json `
  --out rust/tools/diverge/runs/historical-small-new
```

Automated native suite and Python tests:

```powershell
python -m unittest discover -s rust/tools/diverge -p 'test_*.py' -v
python rust/tools/diverge/validate.py --originals $originals `
  --directional rust/tools/diverge/local/my-build/olm_directional_blur.aex `
  --distance rust/tools/diverge/local/my-build/olm_distance_gradation.aex `
  --historical-case rust/plugins/olm-distance-gradation/validation/seed-20261112-v2/case-0039-smart32 `
  --harness $harness --out rust/tools/diverge/runs/verification-new
```

**21 unittest tests pass**; Python compilation, new Rust-module formatting and
PowerShell parsing pass. Tests cover bit/shape comparisons, failed children,
identity rejection, pointer-closure replay, stage-map ABIs, preserved destination
initializers, reduction correctness and budget honesty. No native AE or macOS
qualification is claimed.

To repeat the additional actual Directional fault test, use `examples.py
directional-render` with the existing `validation/smoke-01/case-0003-smart32`
directory and a new output, then `capture.py` clean and with `--inject 3360`.
The fixture retains that image but explicitly selects no noise, gain 1,
front/back 8/3, zero angle/size/fades/tails. For the actual Distance fault test,
use the historical case with `capture.py --inject 0` (without historical SSE).

## Feature-off release byte identity

[Raw proof](evidence/release-proof.json) compares complete before/after DLL bytes,
not rendered pixels, section hashes, or normalized executables. Both diagnostic
exports are absent. Before removes exactly this job's feature declarations,
module declarations, capture call sites and diagnostic access function in the
private snapshot. After restores the current sources; neither enables the feature.

The comparison uses **release optimization, debug=0, `/Brepro`, `/DEBUG:NONE`,
`/INCREMENTAL:NO`, and the exact same frozen resource input** for each pair.
The private build script reuses a captured Rust-generated `resource.lib`; the
production build scripts are untouched. No DLL is modified after linking.

| DLL | Before and after SHA-256 | Bytes |
| --- | --- | ---: |
| DirectionalBlur | `81c19c8525254604e57776bd923c5fa0c44e5a85e2c1c5279f6aa8223539ebad` | 260608 |
| DistanceGradation | `d355e0d29eebd1ca6236b19ee4f12972a656ba4f4ebb9af9d723f6ab0be758e6` | 247808 |

```powershell
python rust/tools/diverge/prove_release.py `
  --tree rust/tools/diverge/local/my-build --target rust/tools/diverge/target `
  --out rust/tools/diverge/local/proof-new
```

The stock workspace release profile has debug=1. Ordinary builds changed debug
identities and version-resource field ordering even while `.text` was identical;
**unqualified reproducibility of those stock build artifacts is not claimed**.
The fixed-input experiment isolates this change from that build nondeterminism.
Capture calls deliberately stay on existing source lines: moving later panic
locations changes Rust's runtime source-location constants even with debug=0.
Do not run a whole-file formatter over these pre-existing algorithm files if
preserving this exact proof is required.

## Limits and lifecycle

This is localization for explicitly mapped boundaries, not automatic recovery of
unknown native ABIs or full coverage of all ten plug-ins. Distance mask creation,
distance transform, packing/composition, and Directional component/noise/rowdriver
stages are not mapped here. In render capture, the original is replayed with the
**Rust-captured input**; equality at that boundary does not prove its upstream
input matches the original render. Reports preserve this conditional scope.
More boundaries can be added as grounded witness maps without editing this tool.

Original functions must be safe bounded calls under witness's ABI contract.
Global/heap state is not serialized by a buffer dump. The Gaussian equivalence
control, binary pins, FMA checks and verified reproducers are safeguards, not
cross-CPU conformance. Native crashes and timeouts remain incomplete.

Witness and oracle own each native child in a kill-on-close Windows Job, close
the job and wait before returning. Builds launched by the supplied scripts use
the same ownership mechanism. There are no daemons, GUI, AE, installations,
commits, original-binary copies, or process-name kills. Artifacts are retained in
ignored directories; no sessions, caches or unrelated application state are
removed. [Cleanup evidence](evidence/verification.json) checks recorded task PIDs
only, distinguishing exited processes from subsequently reused PIDs.
