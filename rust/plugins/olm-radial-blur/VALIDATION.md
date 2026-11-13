# OLMRadialBlur Rust validation — P-radial

Integration follow-up: [Smart32 negative-offset witness](OFFSET_WITNESS.md) is
resolved as original nondeterminism with exact 0°/+1° controls, all ten additional
replays, and C++/pixel-localization evidence. The integrated candidate differs
from the historical DLL below; historical counts and hashes are unchanged.

The Windows crate builds and seven unit tests pass. Inventory and the 294-byte
Windows PiPL are identical. Across two seeds, the final DLL produced 219 / 218 /
222 exact random cases at 8 / 16 / 32 bpc respectively, plus four default/minimum
cases per depth. Seven original-output-nondeterministic cases are explicitly
excluded, not counted as bit-exact passes. There are no unresolved stable
mismatches or render failures in this bounded campaign. Native AE and macOS
remain unverified.

## Final results

Every row ran 113 admitted plans: 111 random and two default/minimum. Counts are
from the original baseline verdicts, not replacements selected from replays.

| Seed | Route | Exact random | Exact default/minimum | Original nondeterministic | Unresolved |
|---|---|---:|---:|---:|---:|
| 20261112 | smart8 | 109 | 2 | 2 | 0 |
| 20261112 | smart16 | 109 | 2 | 2 | 0 |
| 20261112 | smart32 | 111 | 2 | 0 | 0 |
| 20261113 | smart8 | 110 | 2 | 1 | 0 |
| 20261113 | smart16 | 109 | 2 | 2 | 0 |
| 20261113 | smart32 | 111 | 2 | 0 | 0 |
| **Total** | **smart8** | **219** | **4** | **3** | **0** |
| **Total** | **smart16** | **218** | **4** | **4** | **0** |
| **Total** | **smart32** | **222** | **4** | **0** | **0** |

Both seeds have zero reference failures, reference timeouts, candidate failures
and tool errors. The raw oracle render commands exit 1 because they correctly
retain the seven baseline mismatches. The identity-checked collector reports
`qualification_passed: true` under the explicit nondeterminism exclusion rule.
This is not a claim that the original's undefined boundary reads are reproducible.

| Seed | Downsample 1 / 1/2 / 1/4 | Zoom / Rotation | Noise 1 / 2 | Excluded Type 3 plans |
|---|---|---|---|---:|
| 20261112 | 40 / 40 / 33 | 66 / 47 | 95 / 18 | 47 |
| 20261113 | 39 / 36 / 38 | 77 / 36 | 98 / 15 | 73 |

Each listed plan was exercised at all three depths. Sizes were 1×1, 3×7, 11×7,
and 17×9; numeric ranges include Quality 1–50. The 120 Type 3 plans were skipped
before rendering and are listed verbatim in the two campaigns' `exclusions.json`.

Final nondeterministic cases, each replayed three times with unchanged assets:

| Campaign | Case | Route | Distinct original outputs including baseline | Distinct candidate outputs |
|---|---:|---|---:|---:|
| final-a | 55 | smart16 | 3 | 1 |
| final-a | 103 | smart8 | 2 | 1 |
| final-a | 122 | smart8 | 3 | 1 |
| final-a | 150 | smart16 | 2 | 1 |
| final-b | 159 | smart8 | 2 | 1 |
| final-b | 162 | smart16 | 2 | 1 |
| final-b | 183 | smart16 | 2 | 1 |

All 21 replay pairs succeeded; every case has at least one exact replay.
`validation/triage-final/summary.json` retains the raw output hashes and
individual verdicts. `validation-report.json` contains source/binary identities,
counts, full exclusion evidence and coverage; `pipl-comparison.json` records
identical resource SHA-256
`ca613a0dbdb5df801cfdac8896b544c7a2f146dc8bde953dba6cfa01723ed7b0`.

## Scope and implementation

All implementation and job evidence is contained in this crate. The renderer is
pure Rust: Zoom/Rotation, both procedural noise types, component factors,
ordered polar scatter, fade/normalization, inverse sampling and ARGB8/16/32F
conversion. AE declarations, disk IDs, Point/Angle/Layer plumbing, SmartFX
checkout guards and dynamic controls are local to this crate. No shared source,
C++ owner, reference binary, installation directory or repository configuration
was changed. Cargo may update the shared lockfile automatically.

The checked allocation budget is 1 GiB. The AE boundary uses one renderer thread;
the pure API can use independent row workers. Windows exports `EffectMain` and
the original PiPL's `entry_point` alias. macOS exports are provided but unbuilt.

| Files | Purpose |
|---|---|
| `Cargo.toml`, `build.rs`, `src/lib.rs` | Crate, pilot-style build, binary PiPL and module wiring |
| `src/algorithm.rs`, `src/math.rs`, `src/noise.rs`, `src/reciprocal_table.rs` | Pure renderer and deterministic numerical behavior |
| `src/ae.rs`, `src/glue.rs`, `src/ui.rs` | AE entry points, parameters, checkout/suite ownership and UI updates |
| `tests/reference.cpp`, `src/reference_tests.rs` | Existing C++ and native-SSE reference comparisons |
| `validate.py`, `triage.py`, `collect_report.py`, `audit_processes.py` | Bounded oracle campaign, replay, aggregation and lifecycle evidence |
| `README.md`, `VALIDATION.md`, `original-inspect.json`, `pipl-comparison.json`, `validation-report.json`, `.gitignore` | Documentation, identities, results and generated-artifact exclusion |

Raw reproducibility artifacts and the staged `.aex` remain in the ignored local
`validation/` directory. They are not copies of the original plug-in.

## Binary identities

| Item | SHA-256 |
|---|---|
| Original `ghidra_windows_aex/OLMRadialBlur.aex` | `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb` |
| Final `validation/OLMRadialBlur-final.aex` | `b437bf3dceacb99e16efb18b290d4be26cdf685cd1461d51f0aabfa2f963a06b` |
| AEXCompat `broker/target/release/aexcompat-harness.exe` | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |

The machine is AMD Ryzen 9 5900X, AuthenticAMD, ProcessorId
`178BFBFF00A20F12`. Manifests record absolute paths, original/candidate/harness
and oracle hashes, input/request hashes, commands, process PIDs and exit codes.
The installed `target/minihost-build/aex_worker.exe` file has SHA-256
`0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302`;
this is a file identity, not an observed module-binding claim. The harness warns
`source_newer_than_worker`; results qualify the recorded installed executables.

## Build and unit checks

From the repository root:

```powershell
$env:CARGO_TARGET_DIR='D:/olm-rs-target/P-radial'
cargo test --release -p olm-radial-blur -j 2 --manifest-path rust/Cargo.toml
cargo build --release -p olm-radial-blur -j 2 --manifest-path rust/Cargo.toml
```

Seven tests passed; the explicit hardware-profile regeneration test is ignored.
C++ test shims compile the existing owner math, procedural-noise and sampler
functions with contraction and fast-math disabled. Production does not call
those reference functions. Checks cover 20,000 trig vectors, Gaussian tables,
60 procedural-noise settings, 2,400 samples each for RGBA/scalar samplers,
exceptional IEEE words including signed zero/NaN/infinity, one-versus-three
thread output, active Type 3 rejection without output modification, and failed
output checkout releasing the input exactly once.

Native SSE checks exhaust all 8,388,608 normal significands and every Gaussian
denominator for lengths 2–30,000 against the stored reciprocal profile. Gaussian
arrays also compare against a C++ native-RCP reference. The profile regeneration
test is never part of an ordinary build or test run.

## Inventory and PiPL

`validation/inventory-final/summary.json` reports `identical: true`, `diff: []`.
The original 30-slot declaration and all fields exposed by the inspection tool
match. `pipl-comparison.json` records the byte-level comparison of the 294-byte
Windows resources. A binary resource is used to avoid code-page expansion of
the pinned PiPL serializer's RC text, and the original two-byte `eINF` size is
preserved.

The inventory command was the shared oracle's `inventory` command with the
same absolute `--reference` and `--candidate` paths as the render command below,
and `--out rust/plugins/olm-radial-blur/validation/inventory-final`.

## Campaign method

`validate.py` delegates to the unchanged shared `olm_oracle.py`. It retains the
shared generator's random stream and original case indices, rejecting only
Noise Type 3 plans and saving them verbatim in `exclusions.json`. Parameter
ranges are not narrowed. Center components are host percentages of layer extent.
Each admitted plan runs on smart8, smart16 and smart32, comparing native channel
words (deep results are not compared through their preview PNG).

```powershell
python rust/plugins/olm-radial-blur/validate.py render `
  --reference 'D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex/OLMRadialBlur.aex' `
  --candidate 'D:/Projects/01_Project/04_Tools/olm for mac/OLM-for-mac/rust/plugins/olm-radial-blur/validation/OLMRadialBlur-final.aex' `
  --cases 113 --seed 20261112 --jobs 3 --routes smart8,smart16,smart32 `
  --sizes '1x1,3x7,11x7,17x9' --downsample '1,1/2,1/4' --timeout 600 `
  --out rust/plugins/olm-radial-blur/validation/final-a
```

Repeat with seed `20261113` and output `validation/final-b`. Each side receives
`AEXCOMPAT_FRAME_DEADLINE_MS=600000` as well as the 600-second process timeout.
The campaigns run sequentially with three concurrent route-cases, including
expensive high-Quality Rotation. Each seed includes default/minimum plans;
those two plans are separated from random counts. No all-maximum Type 3 plan is
included. Raw mismatches remain mismatches in the saved oracle summaries.

`triage.py` replays each saved mismatch three times without changing its inputs,
request or reference identity. It records raw output hashes from the baseline
and repeated runs. A reference-nondeterministic exclusion additionally requires
constant final-candidate output and successful replays. It additionally requires
either an exact reference/candidate replay or the uniformly applied
[offset-control rule](OFFSET_WITNESS.md#uniform-rule): exact zero/small-positive
offset controls with otherwise unchanged input/parameters/route, C++ zero-read
equivalence, and localized under-read influence. Negative offset alone is never
sufficient. The historical cases below used the exact-replay branch. Other cases
remain unresolved. `collect_report.py`
checks final candidate identities, inventory and Type 3 exclusions before
counting baseline exact random cases across the two seeds.

Final replay and collection commands (repository root):

```powershell
python rust/plugins/olm-radial-blur/triage.py `
  rust/plugins/olm-radial-blur/validation/final-a `
  rust/plugins/olm-radial-blur/validation/final-b `
  --candidate rust/plugins/olm-radial-blur/validation/OLMRadialBlur-final.aex `
  --repeats 3 --out rust/plugins/olm-radial-blur/validation/triage-final
python rust/plugins/olm-radial-blur/collect_report.py `
  --campaign rust/plugins/olm-radial-blur/validation/final-a `
  --campaign rust/plugins/olm-radial-blur/validation/final-b `
  --triage rust/plugins/olm-radial-blur/validation/triage-final `
  --candidate rust/plugins/olm-radial-blur/validation/OLMRadialBlur-final.aex
python rust/plugins/olm-radial-blur/audit_processes.py `
  rust/plugins/olm-radial-blur/validation `
  --out rust/plugins/olm-radial-blur/validation/process-audit-final.json
```

Use fresh output directories when reproducing a campaign or replay. The final
process audit reads only this crate's validation tree. All 2,334 saved harness
records (including preliminary work) have exit code 0 and worker exit code 0;
all harness exits are verified. Live reused PIDs were identified by later
creation time and another image, including targeted CIM checks for two protected
system processes. No unrelated process was stopped and no task helper remains.

## Fixed differences and original behavior

The initial literal C++ translation differed at 32 bpc in Gaussian fade cases.
`notes/OLMRadialBlur_ASM_FACTS.md` documents native B680 using an RCPPS estimate
and separate Newton steps; `RadialSampling.inc` uses a division estimate for
the emulator. On this CPU, for example, length 43 gives refined words
`3b1f7f84` with division versus native `3b1f7f83`. This difference propagates
to output words. A portable 4096-entry significand profile plus exponent scaling
reproduces the native instruction. It is qualified independently of image data,
not a fitted pixel correction. The previously differing cases 3, 10 and 13
became exact. This profiles the recorded CPU; a different original CPU's RCP
implementation is not qualified.

Other preliminary differences were traced to changing original output under
identical saved input/request. `validation/triage-preliminary` records nine
such cases with constant candidate output. These preliminary files use earlier
candidate identities and do not contribute to final qualification counts.
The C++ owner defines out-of-plane scalar/mask reads as zero in
`core/radialblur_plane_read.h` (Issue #3), which Rust preserves. Boundary reads
are a plausible explanation for the observed original instability, but these
replays alone do not prove the address or instruction responsible.

Active **Noise Type 3 is refused**, matching the documented C++ behavior. The
original forwards an uninitialized Noise Layer destination and fails host
ownership/lifecycle checks; see `.codex-jobs/A-diag/report.md` section 2 and
`refs/conformance/olmradialblur_type3_exported_upstream_boundary_20260814.*`.
The C++ no-op shortcut precedes this refusal: all-zero Strength/Offset/Fade
still copies the input. Type 3 is never counted as bit-exact campaign coverage.

## Remaining qualification limits

- AEXCompat Windows CPU routes only; native After Effects and macOS builds were
  not run. No plug-in was installed, no GUI or unrelated integration launched.
- Deep campaign inputs are PNG-promoted host worlds. Arbitrary native HDR,
  negative alpha, nonzero origins, anisotropic downsample and large production
  frames are not qualified by this campaign.
- Dynamic UI code compiles; actual native AE visibility/disabled-state behavior
  and project round trips remain unverified.
- The documented deterministic boundary-read policy cannot reproduce arbitrary
  uninitialized data read by the original.
- The allocation limit, high-Quality Rotation cost and CPU-specific original
  reciprocal profile remain explicit limits.

## Shared-code candidates

The local AE adapter's Point, Angle, Layer and UI-flag declarations, balanced
suite/checkout guards, MT19937 float32 canonical conversion, and native-RCP
profile mechanism could be reviewed for shared crates separately. The RCP
profile needs hardware qualification before reuse; it is not a generic math
replacement. No new UCRT wrapper was necessary. `cc` is used for the same C++
reference-test pattern as the pilots; no new runtime dependency was added.

The crate is `publish = false`; the existing OLM-internal `ucrtmath/ms` NOTICE
and provenance restrictions apply.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.


## Performance - S-blurs (2026-11-13)

Zero zoom/rotation lengths and tails now bypass checked pixel loops. Matching
worlds copy active rows verbatim (alpha and hidden RGB included), preserving
padding. Different geometry uses the original legacy `PF_COPY` utility callback;
cropped no-op SmartPreRender requests now return the requested intersection while
keeping the full maximum extent. This reproduces the original's whole-input
resampling into a smaller requested output. No parameter IDs, PiPL or flags change.

Polar preparation traverses contiguous rows; preparation, independent kernels
and inverse sampling use bounded scoped row workers. Ordered output publication
preserves error-prefix behavior. The extra result buffer is charged to the existing
1 GiB allocation budget. Existing weight/offset tables and every pixel's arithmetic
order remain unchanged. Crucially, `math.rs` and the Zen 3 RCPSS capture profile are
unchanged: host-native reciprocal instructions are not substituted. The exhaustive
reciprocal-profile test passes; profile regeneration remains intentionally ignored.

1080p median selector-time Rust/original ratios, one warmup and five samples:

| Depth | Default before | Default after |
|---|---:|---:|
| 8 | 7.289 | 0.926 |
| 16 | 5.966 | 0.939 |
| 32 | 7.015 | 1.137 |

The original cannot complete heavy Rotation through the resident protocol.
`perf_bench.py` instead runs one warmup plus five measured fresh processes per
side/depth, alternates original/before/after ordering, uses normal priority and a
120-second per-process bound, and verifies complete native output hashes. Its
clock is oracle process wall time including startup and image IO, **not selector
time**. All 54 warmup/measured output hashes agree within their depth.

| Depth | Original ms | Before ms | After ms | Before/original | After/original |
|---|---:|---:|---:|---:|---:|
| 8 | 1375 | 2875 | 969 | 2.091 | 0.705 |
| 16 | 1500 | 2890 | 1015 | 1.927 | 0.677 |
| 32 | 2109 | 3250 | 1469 | 1.541 | 0.697 |


Baseline is commit `5033dd45`. Resident before/after campaigns were separate;
heavy per-process runs interleave all three binaries. Shared-machine contention
limits precision. Remaining costs include checked output publication and scalar
coordinate/reciprocal emulation; any future SIMD must match the captured scalar
profile, not native RCPSS. Local row/thread helpers are shared-hoisting candidates.

Release tests, rustfmt and Clippy pass (warnings); all 40 admitted golden hashes
match, with 14 historical exclusions unchanged. Seeds 20261114/20261115 each have
103 admitted cases/depth (101 random plus two fixed), sizes 1x1,3x7,11x7,17x9 and
scales 1,1/2,1/4. Existing Type-3 noise refusal is retained by `validate.py` with
all excluded generated plans saved. All cases ran per-process with at most two
concurrent renders and 600-second bounds. Baseline exact counts were 200/204/200
at 8/16/32 bpc; the other 6/2/6 cases qualify as original nondeterminism, not exact
passes. Every residual received three fixed replay pairs. Two unresolved cases
then received a predeclared additional ten pairs each (all retained): all renders
succeeded, original hashes varied, candidate hashes stayed fixed and at least one
original/candidate pair matched exactly for every exclusion. No reference failure,
timeout, candidate failure, tool error or unexplained stable mismatch remained.

The shared `../olm-directional-blur/perf_noop.py` passed 66 targeted original
comparisons across both plugins, including ancillary extremes, three scales,
cropped demands and padded native fixtures with nonzero origins/extents. Arbitrary
bit-pattern and padding unit tests pass at all depths. Native AE/macOS and arbitrary
HDR native-host qualification remain outside these Windows CPU-harness results.

Local-only evidence under `D:/olm-rs-target/blurs`: `bench-before`, `bench-final5`,
`perf-final-audit.json`, `radial-process-wall-final6`, `oracle4-OLMRadialBlur-*`,
`triage-final4`, `triage-radial-additional10`, `noop-final4`, `tests-final6.log`.
Candidate SHA-256: `5d8c36120122c37a7007e721938ab799811d2a9bb939ea9f5a4a95dc09077653`.
Raw outputs, originals and binaries are not committed.


## Performance round two - S-blurs

Round two checks only the six controlling values before a no-op. Matching,
tightly packed worlds use one contiguous copy; padded worlds retain active-row
copies, and different geometry retains legacy PF_COPY. The 32-bpc default pure
copy profile at 960x540 (`examples/profile.rs`) compared row/bulk/two/four/eight
worker copies. Warm row copies measured 0.14 ms versus bulk 0.30 ms; with eight
rotating buffers exceeding cache, bulk measured 0.46 ms versus rows 0.73 ms.
Thread startup lost at this size. A bounded host-callback variant tied the
original at 540p and was not selected. Active kernels and Zen 3 reciprocal
emulation are unchanged from round one.

Merged `origin/main` before revalidation. Historical round-one raw run directories
were deleted at the user's request; compact summaries remain under
`D:/olm-rs-target/blurs-evidence/round1`. Round-two exact-case pixels are deleted
after hashing; only mismatches remain temporarily for triage. No shared source
was authored by this job. Final results and compact evidence follow below.

Final 1080p median Rust/original ratios, one warmup plus five samples:

| Depth | Default round 1 | Default round 2 | Heavy round 1 | Heavy round 2 |
|---|---:|---:|---:|---:|
| 8 | 0.926 | 0.866 | 0.705 | 0.633 |
| 16 | 0.939 | 0.936 | 0.677 | 0.705 |
| 32 | 1.137 | 0.928 | 0.697 | 0.719 |

Defaults use resident selector time. Heavy uses fresh-process wall time including
startup/IO because the original still fails the resident Rotation protocol.
Original/after medians at 8/16/32 bpc are 1359/860, 1375/969, 1500/1078 ms;
all 36 output hashes agree within depth. The prior binary was deleted per the
round-two cleanup instruction; round-one ratios are historical separate-run data.

Verification: 22 release tests across the three crates pass (one explicit profile
regeneration ignored), rustfmt and release Clippy pass (warnings), and 148 admitted
golden hashes match (14 historical Radial exclusions unchanged). Two cleanup-helper
tests pass. Both seeds include 103 admitted cases/depth at scales 1, 1/2, 1/4.
This plugin retained 205 exact at 8 bpc, 204 exact at 16 bpc, 203 exact at 32 bpc.
Its 6 remaining cases qualified under the existing original-nondeterminism
rule; they are exclusions, not exact passes. All received three fixed pairs.
One case also received the predeclared ten-pair block: changing original, stable
candidate, successful renders and at least one exact replay were required.
No unexplained stable mismatch, render failure or timeout remained. The 66 targeted
Directional/Radial no-op and fixture comparisons passed again. No native AE/macOS
performance qualification is claimed.

[Compact round-two evidence](performance-round2.json) records samples, hashes,
case plans, exclusion proofs and counts. The resident audit verified 15 exact cells
and 90 frame pairs; its three incomplete cells are original Radial heavy. Raw
run folders were deleted after compaction; local compact summaries/logs are under
`D:/olm-rs-target/blurs-evidence`.
