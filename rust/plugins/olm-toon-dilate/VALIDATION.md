# OLMToonDilate Rust validation — P-toon

## Performance round 2 (2026-11-13)

Round 2 preserves the two chamfer raster orders in `mac/OLMToonDilate/OLMToonDilate.cpp:276`: forward left/upper-left/up/upper-right, then backward right/lower-right/down/lower-left. Strict first-neighbor ties and immediate color copies matter; a separable distance-only transform would not establish color equivalence. This is source-backed reconstruction corroborated by original-AEX comparisons below, not a new native disassembly claim.

Equal-sized worlds now use contiguous pixel/distance planes with a one-pixel sentinel border. Fixed-size byte pixels retain float payloads. Each scan keeps the same neighbor order; the backward scan skips distances 0/1 because no strict improvement exists. Distances above the radius can remain infinity because they cannot produce or block a visible write. Independent horizontal bands include a radius-sized vertical halo: a copied color's predecessor chain has at most radius steps and each step changes y by at most one, so all influencing paths and equal-distance choices remain inside the halo. Both raster scans remain serial within each band. Workers are bounded by available parallelism and ceil(height / max(128, 4*radius)). Differently sized/cropped outputs retain the old ordered implementation, including out-of-output copy no-ops.

The 960x540 microprofile isolated propagation as the dominant cost: radius-zero copying took 0.05-0.27 ms; active radius 5/50 took 6.75-9.15 ms before and 0.99-2.72 ms after, across all depths and dense/sparse seed patterns. See `examples/profile.rs`. This is kernel time, not host selector time.

One final 1080p original-AEX benchmark, one warm-up plus five timed frames per cell, serial normal-priority harness execution. Rust/original ratios (lower is faster):

| bpc | Round 1 default / heavy | Round 2 default / heavy |
|---:|---:|---:|
| 8 | 1.156 / 1.209 | 0.296 / 0.304 |
| 16 | 1.233 / 1.253 | 0.401 / 0.443 |
| 32 | 1.375 / 1.413 | 0.679 / 0.710 |

All six cells are below 1. All 36 frame pairs (30 timed) are exact; audit verifies 12 raw reports, 72 PNGs, 48 deep outputs and four unchanged executable identities. Prior round ratios are retained as historical separate-campaign observations; shared-machine timing is not native AE/macOS performance.

After merging current main: `cargo test --release -j 1` passes **130 tests**, with two existing opt-in ignores, and all **616 golden hashes** (14 historical RadialBlur exclusions retained). Serial compilation avoids inherited duplicate `profile` example output names. ToonDilate fmt and release Clippy pass, retaining inherited warnings. Added tests exhaust all 4,096 masks of a 3x4 image over four radii and four band heights (**65,536 comparisons**); **270** larger 257x259 padded/raw-payload comparisons cover all depths, no/all/dense/sparse seeds, radii 1/2/5/50/100/400, and forced 1/2/7 workers. Existing 3,318 production-C++ differential comparisons also pass, including cropped/larger outputs.

`tools/qualify.py` records **390/390 original-AEX comparisons**: seeds 20261123/20261124 each have 53 cases per depth (100 random plans plus default/min/max across both seeds); seed 20261125 adds 24 targeted cases per depth. Downsample 1, 1/2, 1/4; random radius plans span the full declared range. Targeted 257x259, 13x541 and 1x541 inputs include competing equal-distance seeds, sparse grids, seeds around band boundaries, and no/all seeds. No mismatches, original errors, candidate failures or timeouts. Per-process authority remains enabled for any non-exact resident result; none required replay.

Compact record: `performance-round2.json`. Original and final candidate identities, timing samples and full campaign index are retained in `D:/olm-rs-target/misc-evidence/r2-qualification.json`. Round-one raw files were compacted by the director; historical paths below may no longer exist. Per the subsequent no-deletion instruction, new raw artifacts and the worktree are left for director cleanup (listed in the final report); retained job target/evidence total was 3.18 GB after the runs. No other round-one effect implementation changed. Remaining cost is deep-pixel halo copying/allocation and ordered scans inside each band; native AE MFR/macOS throughput remains unmeasured.


## Performance (S-misc, 2026-11-13)

Active source rows are copied in bulk and seed rows use bounded workers. The AE adapter reuses its existing transaction buffer, avoiding duplicate staging; publication still follows successful pixel checkin. Fixed 4/8/16-byte pixel copies compile separately. Propagation splits adjacent distance rows once per scan row; ordered propagation and first-neighbor ties remain serial and unchanged.

Final frozen DLL oracle: 106/106/106 exact at 8/16/32 bpc, out of 106 attempts per depth across seeds 20261130 and 20261201. Downsample 1, 1/2, 1/4; resident batches with per-process authority for every non-exact result; at most two render jobs. No pixel mismatches, failures, or timeouts. Default/min/max plans plus at least 100 random plans per depth; sizes 1x1/3x7/11x7/31x19/97x61.

Workspace release tests: **123 passed, 2 existing opt-in tests ignored**; all **616 original-verified golden hashes** pass, retaining the 14 historical RadialBlur exclusions. Owned-crate fmt and release Clippy pass (existing Clippy warnings retained). Workspace-wide fmt still reports 25 unchanged files outside this job's ownership. Shared row tests preserve padding/short final rows and compare serial/parallel results; the SIMD column test checks 53,592 scalar/vector lane results bit-for-bit.

1080p median selector-time ratio (Rust/original; lower is faster), measured serially against the same originals with the previous Rust build and this build in one session. Each cell has one warm-up and five timed frames; all benchmark output pairs are exact. Shared-machine timings are not native AE measurements.

| bpc | Before default | After default | Before heavy | After heavy |
|---:|---:|---:|---:|---:|
| 8 | 1.573 | 1.156 | 1.639 | 1.209 |
| 16 | 1.795 | 1.233 | 1.853 | 1.253 |
| 32 | 1.776 | 1.375 | 2.057 | 1.413 |

Local-only identities, requests, outputs, logs, fixed replays, and before/after timing samples are retained under `D:/olm-rs-target/misc-evidence/`; `qualification.json` indexes the final evidence and frozen DLL hashes. Rust 1.88.0, Windows x64, ordinary headless AEXCompat; no original binary or run output is committed, and no AE installation is changed.


Windows x64, 2026-11-12. This report describes **AEXCompat CPU comparisons**, not
native After Effects or macOS validation. Authored files are confined to this crate.

## Implementation

- `Cargo.toml`, `build.rs`: pilot-compatible rlib/cdylib build, pinned workspace
  dependencies, binary PiPL embedding through winres, original `entry_point`
  alias and macOS registration. No new dependency outside those used by the pilots.
- `src/lib.rs`: public algorithm module and private AE adapter wiring.
- `src/algorithm.rs`: pure Rust translation of the current Mac `RenderTyped`
  Smart worker. Input-sized distance plane, ordered forward/backward passes,
  strict first-neighbor ties, immediate copies from the current output, local
  coordinates, output-size clipping, and bit-preserving pixels.
- `src/ae.rs`: Smart checkout/format/admission handling, transactional output,
  original optional pixel-checkin behavior, extra-pixels pre-render flag,
  unchanged checkout request with zero-alpha preservation disabled, Classic
  no-op, and exact Search Radius declaration. Per-frame state is local.
- `tests/reference.cpp`, `tests/kernel.rs`: ABI shim and differential tests.
  `build.rs` extracts the actual traits, accessors, validation and `RenderTyped`
  functions from `mac/OLMToonDilate/OLMToonDilate.cpp`, compiling them without
  contraction or fast math. The static archive member is referenced only by
  tests; release rendering calls Rust.
- `pipl-comparison.json`, `validation-report.json`: retained compact evidence.
  Full inputs, requests, process logs, raw outputs and summaries are retained
  locally under ignored `validation/`.
- `.gitignore`: keeps generated validation artifacts local to this crate.
- `collect_validation.py`: verifies completion, unique case/depth pairs, counts
  and executable identities before regenerating the compact JSON report.

The current C++ plug-in, rather than the older CLI's output conversion, is the
numerical authority. No additional semi-alpha premultiply is applied. Search
Radius first narrows to float, multiplies the float X downsample ratio, then
promotes to double for ceiling. No transcendental/UCRT wrapper is needed.
PF32 seeds include alpha exactly 1 and NaNs; PF16 seeds require exactly 32768.

## Builds and tests

From the repository root:

```powershell
$env:CARGO_TARGET_DIR='D:\olm-rs-target\P-toon'
cargo build --release -p olm-toon-dilate --manifest-path rust/Cargo.toml -j 2
cargo test --release -p olm-toon-dilate --manifest-path rust/Cargo.toml -j 2
```

Both passed. Seven test functions passed:

- 3,150 byte-exact production-C++ comparisons: all three depths, seven shapes,
  ten radii, five scales, and equal/smaller/larger output worlds. Odd strides,
  nonzero origins, padding, raw HDR/negative/NaN/infinity float data, and PF16
  alpha boundary values are included. Input remains unchanged.
- Independent-frame scheduling at 1, 2 and 7 threads: 42 frames per run,
  168 additional C++ comparisons including the repeated serial baseline.
  Within-frame raster passes intentionally remain serial.
- Invalid parameter/storage rejection without output mutation.
- All-depth Smart lifecycle success/failure tests, optional checkin and
  checkin-error atomicity; pre-render request/rectangle/flag behavior;
  original parameter/UI registration; Classic no-op.

An initial normal build was temporarily blocked by another concurrently created
workspace member lacking `src/lib.rs`. A crate-local isolated manifest was used
for an initial compile check; after that member became valid, the normal
workspace commands above passed. The isolated build is not the qualified binary.
Toolchain: rustc 1.88.0 (`6b00bc388`), Cargo 1.88.0 (`873a06493`).

## Binary identities

| Artifact | SHA-256 |
| --- | --- |
| Original `ghidra_windows_aex/OLMToonDilate.aex` | `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3` |
| Candidate `D:\olm-rs-target\P-toon\release\olm_toon_dilate.dll` | `b695f68a13ef13c0e8cf8be633897f8930030a390306340a5c5d24b64cdf2967` |
| Shared AEXCompat harness | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |
| Shared AEXCompat worker | `0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302` |
| Oracle Python tool | `657b40b68902ac64a9c3d2175e383ae97b9940f2d30a817b9962b350d76b5ab3` |

The candidate is staged as `validation/OLMToonDilate.aex`. The original was not
copied or modified. The harness and worker paths are recorded in the JSON report.

## Inventory and render comparison

`validation/inventory-release/summary.json`: identical across every exposed
parameter/host field, one parameter excluding the input slot. The complete
Windows PiPL resource is identical, **298/298 bytes**, including the match name,
category, version `0x88800`, flags `0x02000044`/`0x08021400`, and entry alias.

Commands (run from the repository root; output directories must be new):

```powershell
$original='D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMToonDilate.aex'
$candidate=Join-Path $PWD 'rust/plugins/olm-toon-dilate/validation/OLMToonDilate.aex'
Copy-Item 'D:\olm-rs-target\P-toon\release\olm_toon_dilate.dll' $candidate
$env:PYTHONUTF8='1'
$env:AEXCOMPAT_FRAME_DEADLINE_MS='120000'
python rust/tools/oracle/olm_oracle.py inventory --reference $original --candidate $candidate --out rust/plugins/olm-toon-dilate/validation/inventory-release
foreach ($seed in 20261112,20261113) {
  python rust/tools/oracle/olm_oracle.py render --reference $original --candidate $candidate --routes smart8,smart16,smart32 --cases 203 --seed $seed --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --timeout 120 --out "rust/plugins/olm-toon-dilate/validation/seed-$seed"
}
python rust/plugins/olm-toon-dilate/collect_validation.py
```

Each seed has 200 randomized cases plus explicit default/min/max cases, per
depth. Inputs cycle 1x1, 3x7, 11x7, 31x19 and 97x61; scales cycle 1, 1/2, 1/4
(68/68/67 cases per depth per seed). Both sides receive the same input and
120000 ms frame deadline; the outer process timeout is 120 seconds. Concurrent
route jobs are limited to 3. Deep results compare native raw words, not previews.

| Seed | Smart8 | Smart16 | Smart32 CPU | Mismatch / reference failure / timeout / candidate failure |
| --- | --- | --- | --- | --- |
| 20261112 | 203 exact | 203 exact | 203 exact | 0 / 0 / 0 / 0 |
| 20261113 | 203 exact | 203 exact | 203 exact | 0 / 0 / 0 / 0 |

**Final total: 1,218 exact comparisons**, 406 per depth including 400 randomized
cases per depth. Each depth has 136/136/134 cases at scales 1, 1/2 and 1/4.
There were no pixel mismatches, reference-unrenderable cases, timeouts,
candidate failures, or tool errors. Both oracle processes exited zero and
completed owned-process cleanup. The final collector verified all case/depth
pairs, both complete summaries, and unchanged original/candidate/harness/tool
identities; the worker hash matched its earlier observation and final check.

Earlier smoke on candidate `21b3b69d8cbee059bc6807c599a959f2f926aea0e1d1a6f775cb711fad3af4de`
was 12 exact per depth, zero failures. That earlier binary is not substituted for
the final candidate in the main campaigns.

## Investigated difference

The first inventory comparison found only `/parameters/0/custom_ui_events`:
original 4, candidate 0. Original diagnostics show `inter.register_custom_ui`
before `inter.add_param`; the existing Mac source and shared adapter omit this
registration. The local adapter now registers `PF_CustomEFlag_EFFECT` (4) with
zero control sizes, preserving the parameter's zero flags/UI flags. Inventory
then matched; a callback-order/parameter-declaration regression test passes.
No numerical constant was tuned.

## Limits and shared-crate candidates

- Native AE loading, UI event drawing/interaction, saved-project round trips,
  and macOS arm64/x86_64 builds were not run. No installation was performed.
- Oracle inputs are RGBA8 PNGs promoted to deep worlds. Arbitrary native deep
  HDR/negative/NaN inputs, padded worlds, and differing input/output dimensions
  are C++ unit-test coverage, not new original-AEX/native-AE coverage.
- Normal AE dispatch is SmartFX. Classic deliberately remains a no-op; a
  Classic rendering claim is not made. Existing numerical/admission semantics
  are retained, including rejecting nonfinite/out-of-range public radius and
  invalid scales/formats/overlapping worlds.
- No exhaustive domain proof, thrown-host-callback coverage, or actual
  allocation-failure injection is claimed. C++'s unused pre-render ref-width
  allocation is omitted because SmartRender does not consume it.
- Hoisting candidates: optional pixel-checkin policy, transactional commit
  after checkin, custom-UI event registration, and pre-render extra-pixels flags
  in `olm-ae`. They are implemented locally in `src/ae.rs`; shared crates were
  not edited. There are no math-wrapper candidates.
- Oracle processes run in owned Windows Job Objects; its runner terminates
  remaining descendants and verifies the active count reaches zero before
  returning. No GUI, Adobe process, integration server, or subagent was used.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.
