# OLMSmoother v1 — Windows Rust validation

Job P-smoother, 2026-11-12. Scope: `rust/plugins/olm-smoother/**`.
Build target directory: `D:\olm-rs-target\P-smoother`.

## Identities

| Artifact | SHA-256 |
| --- | --- |
| Original `ghidra_windows_aex/OLMSmoother.aex` | `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82` |
| Rust staged `validation/OLMSmoother.aex` | `21d3ae696808b7ad188ec0b0994c04bfc9da2efe16eef289557b2a5a7be799f7` |
| AEXCompat harness | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |
| Installed worker at the diagnostic report's default path | `0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302` |
| Windows PiPL, both binaries (298 bytes) | `652dd1cccef7ea16acdf236d5ecad626e08729fe16357bca67050e3798928abd` |

The worker path is `D:\Projects\01_Project\04_Tools\AEXCompat-wt-main\target\minihost-build\aex_worker.exe`.
The request logs do not emit its loaded-module path; this additional hash
identifies the existing default-path file, rather than claiming a fresh module
mapping witness. They report `source_newer_than_worker`. The complete harness
path, OS, test-log identities and provenance caveat are in
[environment.json](environment.json).

## Build and C++ reference tests

From `rust/`:

```powershell
$env:CARGO_TARGET_DIR = 'D:\olm-rs-target\P-smoother'
cargo test --release -p olm-smoother -j 2
cargo build --release -p olm-smoother -j 2
```

Both succeeded. **6 tests passed, 0 failed**:

- 480 complete C++/Rust frame comparisons: 240 per depth, multiple geometries,
  categorical/diagonal/noise patterns, partial alpha, exact color-key hits,
  tolerance 0/1/6/32/128/255, and cropped callback extents.
- 16,384 color-comparison vectors and 16,384 alpha-blend vectors across 8/16 bpc.
- 80 frames compared after every directional classifier, subhandler and dispatch.
- 20 frames of independently compared contour-walker outputs, with 16 direction
  pairs per pixel.
- Identical results with 1/2/4 independent rendering workers. Each frame retains
  the original ordered callback traversal.
- Odd padded 16-bit row strides, retained padding, and rejection before writes
  for an out-of-range tolerance.

The C++ archive is referenced only by `cfg(test)` code. Production rendering
calls the Rust algorithm and generated Rust kernels. The build uses the pilots'
existing `cc`/PiPL/`winres` approach; no new external dependency was added.

## Original-binary oracle

Inventory: **identical**, with zero exposed parameter/host differences.
The independent [PiPL comparison](pipl-comparison.json) is also byte-identical.
The effect preserves `entryPointFunc`, exposes `EffectMain`, and declares
`out_flags=0x02000040`, `out_flags2=0x08000000`, version `0x00090800`.
There are three parameters plus input. SmartFX and 32 bpc remain undeclared.

The initial smoke completed **20/20 exact on classic8 and 20/20 exact on
classic16**, with zero failures or mismatches. The main two-seed campaigns are
recorded below after completion; the overlapping smoke is not added to their
distinct-case totals.

| Seed | Classic 8 | Classic 16 | Random cases per depth |
| --- | ---: | ---: | ---: |
| 20261112 | 103 exact | 103 exact | 100 |
| 20261113 | 103 exact | 103 exact | 100 |
| **Main total** | **206 exact** | **206 exact** | **200** |

**Zero pixel mismatches, reference-unrenderable cases, timeouts, candidate
failures, or inventory differences.** Both campaign exit codes are 0. There are
no original failures to exclude. Each seed/depth includes 35 full-resolution,
34 half-resolution and 34 quarter-resolution cases, counted from saved requests.
The first three cases per seed are default/minimum/maximum; the remaining 100
are randomized. Full data and source identities are in
[validation-report.json](validation-report.json).

All oracle runs use **`--jobs 3`**. Each process timeout is 120 seconds; the
oracle supplies **`AEXCOMPAT_FRAME_DEADLINE_MS=120000` to both binaries**.
Inputs cycle through `1x1,3x7,11x7,31x19,97x61`; downsample cycles through
`1,1/2,1/4`. PNG samples include partial alpha and hidden RGB; deep comparisons
use `.rgba16le`, rather than preview PNG values.

Commands from the repository root (choose fresh output directories to repeat):

```powershell
$ref = 'D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMSmoother.aex'
$cand = 'D:\Projects\01_Project\04_Tools\olm for mac\OLM-for-mac\rust\plugins\olm-smoother\validation\OLMSmoother.aex'
python rust/tools/oracle/olm_oracle.py inventory --reference $ref --candidate $cand --out rust/plugins/olm-smoother/validation/inventory-final
python rust/tools/oracle/olm_oracle.py render --reference $ref --candidate $cand --routes classic8,classic16 --cases 103 --seed 20261112 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --timeout 120 --out rust/plugins/olm-smoother/validation/seed-20261112
python rust/tools/oracle/olm_oracle.py render --reference $ref --candidate $cand --routes classic8,classic16 --cases 103 --seed 20261113 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --timeout 120 --out rust/plugins/olm-smoother/validation/seed-20261113
python rust/plugins/olm-smoother/tools/collect_validation.py smoke seed-20261112 seed-20261113
```

## Resolved differences

1. **Native parameter declaration versus C++ UI range.** Original inspection
   reports tolerance's user maximum as 255. The C++ declaration uses 6, which
   produced one inventory difference. Rust uses the original's 255 maximum;
   the default remains 6. White Color Key defaults also require a local setup
   adapter because shared `Kind::Color` currently initializes black.
2. **Synthetic descriptor address collision.** Initial Rust/C++ differential
   tests exposed a subhandler coordinate difference. Instruction-boundary traces
   localized the first divergence to a generated world-width read. The minimal
   host-free world occupied fewer bytes than the synthetic Windows field span,
   so a logical field address could overlap an adjacent RenderState and match
   its memory interception first. Reserving the complete descriptor span in
   both local carriers removed that address-dependent collision. The original
   C++ algorithm bodies and all arithmetic constants were unchanged.
3. **Rust memory alignment and mutable array decay.** The translation explicitly
   retains aligned curve storage and obtains mutable pointers for mutable local
   arrays. Integer casts retain x86 truncation behavior; separate binary32
   operations preserve the C++ contraction-off arithmetic.

No oracle pixel mismatch was used to tune an arithmetic constant.

## Limits and shared candidates

- These are **AEXCompat CPU results, not native AE results**. AE was not launched;
  no plug-in was installed. macOS compilation, Universal packaging, and native
  UI behavior were not tested on this Windows machine.
- Oracle 16-bit inputs are promoted from PNG bytes. The C++ helper/frame tests
  add native 16-bit samples, but neither corpus exhausts all possible images.
- The request oracle does not cover padded/origin-shifted host worlds. Local
  tests cover padding and cropped extents; they do not replace native host tests.
- The original and C++ supported range stays 8/16 bpc, integer tolerance 0–255,
  maximum side 4096 and maximum pixel count 4096×2160. Neighborhood work remains
  frame-wide even for a restricted output extent. No 32-bit or SmartFX claim is made.
- Hoisting candidate: a shared color-parameter kind with an explicit default
  ARGB value would eliminate the local ParamsSetup adapter. No new UCRT wrapper
  is needed; existing `olm_math::x86` helpers supply the required scalar behavior.
  The contour carrier and ordered traversal are v1-specific and remain local.

Detailed oracle inputs, requests, process logs, and raw outputs stay under the
ignored `validation/` directory. Curated binary/source hashes and per-route counts
are in `validation-report.json`; development build logs and the AST stay in
ignored `tools/work/`. No background service, GUI, browser, or subagent was used.

The final identity recheck found the original, candidate and harness unchanged;
the release DLL is byte-identical to the staged candidate used by both campaigns.
[cleanup.json](cleanup.json) records both oracle exits and a post-run process
check: no task-owned harness, worker or oracle process remained. Windows had
recycled several recorded PIDs for other jobs; command-line scope and parent
ownership distinguished those processes, and none was stopped.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.

## Performance implementation (S-smoother, 2026-11-13)

The production hot pixel routines now use structured Rust for color comparison,
3x3 neighbor extraction, ordered direction iteration, and the 8-bit classifier
prefix. Every integer input makes the color metric's float intermediates finite
and bounded (including the full uint16 range). The original order of multiplies,
adds and divisions is retained; absolute luminance rounded up is equivalent to
the original signed floor/ceil selection. No reciprocal approximation or FMA is
introduced. The 16-bit classifier rejects inactive directions before constructing
its virtual register/stack carrier.

`tools/structure.py` additionally removes runtime dispatch from both classifiers,
direction dispatch, subhandlers, main interpolation and alternate handlers. It
checks every selected CFG for cycles after extracting single-block self loops,
orders all remaining edges topologically, and expresses forward transfers as
lexical block exits. Each original block appears once, with its operations,
condition, successors and return unchanged. This avoids exponential code
expansion and exposes register assignments to LLVM. These large structured
kernels are still mechanically derived; this is not a complete handwritten
replacement of the contour algorithm. Retained walkers and blend/executor loops
are in `kernels.rs`. `generated.rs` is byte-for-byte unchanged and compiled only
under `cfg(all(test, feature = "generated-reference"))`.

Additional reference comparisons (`cargo test --release -p olm-smoother
--features generated-reference`):

- All 256x256 single-channel pairs at four alpha values and four channels;
  all 65,536 uint16 single-channel values against four endpoints, at four
  channels; 1,000,000 random full-range uint16 pixel pairs (also checked as u8).
- All 19,683 three-color 3x3 neighborhoods, four directions, three tolerances,
  both depths: 472,392 classifier comparisons.
- 2,048 complete generated/optimized frame comparisons covering every tolerance,
  both depths, color keys, odd sizes, cropped extents, nonzero layout origins and
  padding. Existing C++ frame/helper/walker/directional tests also remain active.

The finite input bound and the CFG-preserving transformation support the
implementation argument; enumerated/random tests do not exhaust all images.
The v1 traversal remains serial. No parameter, PiPL, depth or route changes.

### Measured result and release gate

1080p Rust/original wall-time ratios (lower is better), baseline -> optimized:

| Depth | Default | Heavy |
|---|---|---|
| Classic8 | 5.294 -> 2.011 | 6.055 -> 1.672 |
| Classic16 | 9.862 -> 3.527 | 9.410 -> 2.282 |

Baseline and final sweeps were separate on a shared machine; this is not a
controlled simultaneous before/after speedup. The final sweep had no overlapping
build from this task. All four cells were exact. The original-speed target is
not yet reached: contour walkers/executor dispatch and checked pixel staging
remain candidates for a subsequent measured optimization.

Release tests: 9 passed with generated-reference; fmt check passed; release
clippy completed successfully with existing/mechanical-code warnings. Golden:
36 exact. Two oracle seeds (20261121/20261122), 103 cases per depth per seed,
including 100 randomized cases, all three downsample factors: 412 exact, zero
errors. Structured-source regeneration reproduced the checked-in files exactly.

Local-only evidence is under D:\olm-rs-target\smoother: accepted-tests.log,
accepted-fmt.log, accepted-clippy.log, accepted-golden-v1.log, oracle/,
bench-before/evidence.json, bench-serial/evidence.json, serial-report.json and
serial-audit.json. The combined benchmark audit passed: 10 exact cells, 60
frame pairs, 120 PNGs and 72 deep files verified. Tested OLMSmoother.aex SHA256:
d116782f0c49ddcd0f23b8d12755902a77c4b157498c10cd9a77aadd29b5485a.

Round 1 withheld the PR because Smoother2's cropped-output oracle gate failed.
Round 2 classified this as an unchanged preexisting port defect on baseline,
main and perf. The user's Round 2 instruction permits the documented exception;
see Smoother2's minimal reproducer and original-vs-original evidence.

### Round 2 implementation and independence argument

The diagnostic `--features profile --example smoother-profile` uses 1080p seeded integer
pixels and records staging, classification, ordered dispatch and packing clocks.
Before the split, staging/packing cost about 23-44 ms and filtering 560-1650 ms
on this shared machine. After the split, classification took about 40-100 ms;
the remaining ordered dispatch dominated. These are diagnostic observations,
not benchmark ratios or isolated CPU measurements.

Classification reads only src_world pixels, tolerance values and immutable
direction tables. Its writes target local neighbor arrays, virtual registers
and synthetic stack addresses; no destination world is provided. Scoped row
workers have private World/RenderState/stack carriers and disjoint classification
records. Source storage stays alive and immutable until all workers join. Worker
count is capped by available_parallelism and 16K pixels per worker. Single-worker
and small-frame execution stays inline. No global mutable cache is introduced.

Destination interpolation is deliberately serial: InterpExecutor compares current
destination with source and blends with previous destination values. Therefore
arbitrary rows or halo tiles cannot be independently committed. The exact y/x
and direction order 5,3,1,7 remains unchanged. Classification type 4 is the
exception: ColorBlend with weight 5 reads only its source neighborhood, so its
value is precomputed alongside classification and written at the original point
in that ordered sequence. It is not moved past other destination writes.

The structured color blend retains row-major neighbor sums (excluding center),
five separate center additions, division/truncation, alpha normalization and
unpremultiplication. It preserves CVTTSS2SI behavior and low-word masking before
the 16-bit clamp. All 256 neighbor-presence masks times 256 randomized full-range
pixel sets at both depths are compared against the frozen generated routine.
The center is always valid for a production in-bounds callback.

`tools/structure_loops.py` extends the CFG transformation to contour walkers and
interpolation executors. Single-entry strongly connected components become
nested loops; header edges become continue, forward exits become lexical breaks.
Every reachable block is emitted once, with operations unchanged; multiple-entry
components and nested closure dispatch remain in their original form. The tool
checks reachability, unique entry, topological ordering and block coverage.
This remains a structured mechanical translation, not a handwritten algorithm.

Added 257x193 reference comparisons cross the actual parallel threshold, with
odd byte stride, nonzero origins, cropped extents, color key, four tolerances,
both depths and 1/2/3/available workers. The reference remains byte-for-byte
unchanged and test-only. The checked allocation budget includes 24-byte per-pixel
classification/blend records plus both contiguous source/destination buffers
(40 bytes/pixel worst case, bounded by the existing image dimensions).

Clippy policy: handwritten code is corrected; generated modules have enumerated
style/ABI exceptions to retain regeneration fidelity (casts, explicit unit
expressions, parentheses, raw-pointer comparisons and source argument lists).
No blanket crate-wide Clippy suppression or shared-crate edits are introduced.

The Classic adapter now validates pixel formats, disjoint byte spans, positive
strides, parameter values and extent once, then uses `render_bytes`. Active row
bytes are copied into the same aligned, contiguous ARGB working buffers; padding
is neither read as pixels nor overwritten. Color-key handling is restricted to
the original extent. The checked View API and new row-copy API call the same
ordered kernel and are compared against generated reference frames. This removes
per-pixel enum/bounds dispatch at the AE boundary. It keeps the color suite's
callback/error handling and balanced suite release; no Smart or float route is
added. A shared checked row-span API is a possible future hoisting candidate;
shared crates remain read-only in this job.

### Round 2 final evidence

All four 1080p cells now meet Rust/original < 1 (median selector times):

| Depth / preset | Original ms | Rust ms | Round 1 ratio | Round 2 ratio |
|---|---:|---:|---:|---:|
| Classic8 default | 265.86 | 200.28 | 2.011 | 0.753 |
| Classic8 heavy | 237.30 | 188.05 | 1.672 | 0.792 |
| Classic16 default | 262.43 | 190.25 | 3.527 | 0.725 |
| Classic16 heavy | 227.93 | 202.18 | 2.282 | 0.887 |

Serial benchmark, normal priority, no overlapping task build. Other jobs may
still use the shared machine. All warm-up and timed frame pairs are exact.
The combined ten-cell audit verified 20 raw reports, 120 PNGs, 72 deep files,
60 frame pairs (50 timed), worker identity and unchanged executables.

Final release tests: 11 passed, including frozen reference, all neighbor masks,
zero-alpha/all-zero/full-range blend edges, worker-count comparisons and byte-row
staging comparisons. Golden: 36 exact. Two-seed oracle: 412 exact, no errors or
mismatches, 103 cases per depth per seed with all three downsample factors.
An additional per-process control (seed 20261123, nine cases per Classic depth,
3x7/31x19/257x193, all three downsample factors) passed 18/18 exactly; evidence
is in round2-classic-process/summary.json under the same local target directory.
The oracle CLI rejects --extent for Classic routes before rendering; cropped
extents are covered by the checked/byte-row/generated differential frame tests,
not claimed as direct-host cropped-output oracle coverage.

Formatting passes. All-target release Clippy with generated-reference enabled
has zero warnings in the two owned Rust crates, including examples/tests.
Read-only shared dependency warnings and the native C++ reference's unused
variable warning remain outside this Rust lint result. Regeneration reproduced
structured.rs and kernels.rs byte-for-byte; generated.rs is unchanged.

Evidence under D:\olm-rs-target\smoother: round2-byte-bench/evidence.json,
round2-final-report.json, round2-final-audit.json, round2-clean2-{fmt,tests}.log,
round2-clean2-clippy.jsonl, round2-final-golden-olm-smoother.log, round2-oracle/.
Final benchmark/oracle binary SHA256:
b8f19b7d61076cb3d6d54d65defbc93f3de9abc80314480933303486605c3da0.
The remaining cost is ordered contour/interpolation dispatch plus classification;
destination dependencies prevent arbitrary row parallelism. No measured cell
remains >= 1. Native AE performance and acceptance are still unverified.
