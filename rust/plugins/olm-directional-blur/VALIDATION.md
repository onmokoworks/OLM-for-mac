# OLMDirectionalBlur Rust validation (P-dblur)

Status: implementation and final two-seed validation complete, with an original nondeterminism limitation. **751/768 baseline renders are bit-exact; all 17 mismatches independently demonstrate changing original output.** The brief's unconditional all-renderable-cases exact definition is therefore not met. No native AE exact claim.

## Implementation

Only `rust/plugins/olm-directional-blur/` is owned/edited. Production image processing is Rust: `algorithm.rs`, `rotate.rs`, `rowdriver.rs`, `noise.rs`. The adapter extends the pilot boundary locally in `host.rs`, with parameter/entry glue in `ae.rs`, AEGP registration/dynamic controls in `ui.rs`, and retained C++ admission/source gates in `admission.rs`/`sha256.rs`.

The Windows PiPL is **310 bytes, identical to the original**, including `entryPointFunc`, name/category/match name, versions, flags, and the two-byte `eINF`. Inventory is identical across **21 parameters**, excluding input. The original popup declares two choices but has three strings; both the declared count and `Smooth | Block | Layer` spacing are retained. Group-end names retain the original preceding control names.

Fixed and angle controls use the signed high word of 16.16, including flooring negative fractional angles. Distance counts and Thickness use the horizontal FLOAT32 downsample ratio. Work geometry, 32-partition remainder rows, depth-specific unpack/pack, channel accumulation order, SSE NaN/min/max semantics, component bounds, Gaussian tables, MT19937 stream and UCRT FMA calls follow the current C++ sources. No constants were fitted to images.

C++ references are compiled into an archive for tests; the production entry does not call C++ kernels. UCRT C remains supplied by `olm-math`. This uses the already-present `cc`/`winres` build dependencies; no new numerical/runtime dependency was added. `ucrtmath/ms` and combined math artifacts remain OLM-internal and must not be published standalone.

## Build and tests

```powershell
$env:CARGO_TARGET_DIR='D:\olm-rs-target\P-dblur'
cargo build --manifest-path rust/Cargo.toml --release -p olm-directional-blur -j 2
cargo test --manifest-path rust/Cargo.toml --release -p olm-directional-blur -j 2
```

Both commands pass. Six tests cover 360 randomized C++ full-image comparisons across 8/16/32-bit storage; identical one-thread/four-thread output for those images; 24 additional PF32 Layer/HDR/negative/nonfinite cases against C++; 5,498 Gaussian words; SHA-256 admission hashing; rational validation; and checkout cleanup after failure. C++ cases use six geometries up to 64x36 and explicit UCRT FMA.

## Final measured results

Each seed has 128 cases per depth: three default/min/max cases and 125 random cases. The combined campaign has **250 random cases per depth**, with downsample 1, 1/2 and 1/4 distributed across the cases.

| Seed | Route | Rendered | Bit-exact | Mismatched | Random bit-exact / random total |
| --- | --- | ---: | ---: | ---: | ---: |
| 20261112 | Smart8 | 128 | 124 | 4 | 121 / 125 |
| 20261112 | Smart16 | 128 | 126 | 2 | 123 / 125 |
| 20261112 | Smart32 CPU | 128 | 125 | 3 | 122 / 125 |
| 20261113 | Smart8 | 128 | 126 | 2 | 123 / 125 |
| 20261113 | Smart16 | 128 | 125 | 3 | 122 / 125 |
| 20261113 | Smart32 CPU | 128 | 125 | 3 | 122 / 125 |
| Combined | Smart8 | 256 | 250 | 6 | 244 / 250 |
| Combined | Smart16 | 256 | 251 | 5 | 245 / 250 |
| Combined | Smart32 CPU | 256 | 250 | 6 | 244 / 250 |

There were **zero reference render failures, candidate render failures or render timeouts**. There was one aggregate-file write failure, described below. `validation-report.json` records counts by seed/depth/downsample, executable identities and every mismatch witness.

All 17 mismatches have negative Noise Offset. For each exact saved input and parameter set, three original-vs-original pairs plus the saved baseline reference produced **2–5 distinct original pixel hashes**. All 17 supplementary Rust-vs-original controls with only Offset changed to zero were bit-exact. The baseline 17 remain mismatches, and the 17 controls and 102 original rerenders are not added to the main counts. This measures original nondeterminism; the table-underread explanation is an inference grounded in `core/dblur_noise.h`, not a new memory trace. No translation correction or numerical tuning was applied to these cases.

The second seed's oracle aggregate writer failed while renaming `summary.json.tmp` over `summary.json` with Windows error 5 (access denied). A concurrent read may have caused the sharing conflict, but that cause is not proven. The executor still finished all queued cases: **384 unique saved `diff.json` files**, matching all planned case/route pairs, all successful process exits, and the frozen manifests. `summarize_validation.py` reconstructs `summary-recovered.json` from those unchanged per-case verdicts using the oracle's own summary function. The interrupted `summary.json` is preserved. The oracle process exited 1; this is not represented as a successful uninterrupted campaign. No renders were rerun for this recovery.

Initial workspace builds were blocked by another job's incomplete `olm-smoother` member. A temporary foundation snapshot under this crate's ignored `validation/build-workspace` was tried, then abandoned once the shared workspace became valid. The delivered candidate and reported tests use the **normal shared workspace**. The temporary build exposed the need for `/EHsc` for test-reference C++ exceptions. No other job or shared crate was edited.

## Limitations and evidence boundaries

- AEXCompat CPU host emulation only. macOS was not built here; native After Effects, native UI appearance and scheduling were not tested. The source includes the dynamic-control implementation, but inventory/render comparisons do not certify UI behavior.
- PNG inputs contain partial alpha and hidden RGB, promoted by the harness for deep routes. Native HDR/negative-alpha source inputs are only covered by C++ unit tests, not by an original-AEX/native-AE campaign.
- Original Noise Type 3 instability and the PF32 negative-alpha/Back Alpha Fade undefined-memory boundary remain limitations. Type 3 is outside the original's declared popup range in the generic oracle. Core Layer arithmetic is C++-tested; no universal original-AEX Type-3 equivalence is claimed.
- **Negative Noise Offset also exposes original nondeterminism in Types 1/2.** `core/dblur_noise.h` documents reads before its 101-entry noise table, with deterministic zero reads in the C++ port. Rust retains that policy. A saved original-vs-original repetition changes raw pixels, while changing only Offset to zero yields an exact Rust comparison. Such cases are recorded as mismatches/reference nondeterminism, never silently counted as passes or relabelled as render failures.
- Smart cropped/padded/origin-shifted worlds and Classic are outside the final random request campaign. The adapter preserves local-coordinate output staging and the retained source gates; this report does not claim exhaustive world/ROI qualification.
- The installed harness reports `source_newer_than_worker`. Original/candidate/harness hashes bind each campaign; the known worker executable and current UCRT hashes are additionally recorded in `runtime-identities.json`, with the worker-path provenance limit stated there.

## Shared-code candidates

`mac/OLMRadialBlur/OLMRadialBlur.cpp` includes `core/dblur_noise.h`. Keep this job's translation self-contained: MT19937, deterministic out-of-range table reads, and the Directional noise plane are candidates for later hoisting. The Radial generator/sampler use different rounding and accumulation order and must not be substituted for Directional's. Fixed/angle/layer parameter handling, scoped suite/checkouts and atomic publish can be considered for `olm-ae`; SHA-256 active-row admission hashing is another local helper candidate. No new UCRT extern wrapper was needed.

## Process ownership

Oracle runs use `--jobs 3` and matching `AEXCOMPAT_FRAME_DEADLINE_MS=120000` on both sides with a 120-second process limit. The oracle owns each suspended harness and descendants through a Windows Job Object, terminates the owned job on completion/error, checks active process count reaches zero, then waits for the child. No AE, GUI, integration server, daemon, installation, Git operation, commit or subagent was used.

The superseded preliminary campaign was intentionally stopped before completion after the UI-complete candidate was built. Its completed cases are retained but excluded from final qualification counts. The exact owned Python PID and descendant PIDs were captured, stopped and verified absent; see `validation/preliminary-cleanup.json`. The initial 15-case smoke is also separate, not added to the final campaign.

Both final campaign orchestration and diagnostic execution were awaited to exit. The final scoped process check is retained in `validation/final-cleanup.json`; no matching owned Python or harness process remained. No unrelated process was terminated.

## Frozen executable identities

| Artifact | SHA-256 |
| --- | --- |
| reference | `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e` |
| candidate | `9cb49720dd34ac114436904bd040eaaa517371fed9747228dcf41b61348a3297` |
| harness | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |

The candidate is `D:\olm-rs-target\P-dblur\OLMDirectionalBlur-qualified.aex`; its bytes equal `release/olm_directional_blur.dll`. `source-identities.json` pins the corresponding source/build/test inputs. `pipl-comparison.json` records complete resource equality.

## Final oracle commands

From repository root, with fresh output directories:

```powershell
$reference='D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMDirectionalBlur.aex'
$candidate='D:\olm-rs-target\P-dblur\OLMDirectionalBlur-qualified.aex'
python rust/tools/oracle/olm_oracle.py inventory --reference $reference --candidate $candidate --out rust/plugins/olm-directional-blur/validation/inventory-final
python rust/tools/oracle/olm_oracle.py render --reference $reference --candidate $candidate --cases 128 --seed 20261112 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --routes smart8,smart16,smart32 --out rust/plugins/olm-directional-blur/validation/final-seed-20261112
python rust/tools/oracle/olm_oracle.py render --reference $reference --candidate $candidate --cases 128 --seed 20261113 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --routes smart8,smart16,smart32 --out rust/plugins/olm-directional-blur/validation/final-seed-20261113
python rust/plugins/olm-directional-blur/classify_mismatches.py rust/plugins/olm-directional-blur/validation/final-seed-20261112 rust/plugins/olm-directional-blur/validation/final-seed-20261113 --out rust/plugins/olm-directional-blur/validation/final-mismatch-diagnosis
python rust/plugins/olm-directional-blur/summarize_validation.py
```

Each seed has default/min/max followed by 125 randomized cases. Cases are distributed across sizes/downsamples; counts are per depth, not per size/scale combination. Raw float words and native 16-bit samples are compared, not preview PNGs. The negative-offset diagnostics preserve baseline mismatches and use original-vs-original repeats plus separately labelled zero-offset controls; controls are excluded from the main exact counts.

## Delivered files

`Cargo.toml`, `build.rs`, `.gitignore`, the ten `src/*.rs` modules, `tests/reference.cpp` and `tests/conformance.rs` contain the crate and reference checks. `diagnose.py`, `classify_mismatches.py` and `summarize_validation.py` preserve the diagnostics and aggregation method. `VALIDATION.md`, `validation-report.json`, `source-identities.json`, `runtime-identities.json`, `inventory-comparison.json`, `pipl-comparison.json` and `candidate-path.txt` record the result. Raw images, per-case requests/diffs, test log, interrupted summary, recovered summary and process records remain in the crate-local ignored `validation/` directory.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.


## Performance - S-blurs (2026-11-13)

The AE adapter takes an exact no-op path when the four scaled front/back and
tail lengths truncate to zero. Matching worlds copy active byte rows, including
all alpha/RGB bits, leaving output padding untouched. Smaller output worlds use
the original legacy `PF_COPY` utility callback: it resamples the entire input,
not a top-left crop. Output remains staged until parameter/pixel checkins succeed.
Actual kernels and forward/inverse rotations use bounded independent row chunks;
small images stay single-threaded. Per-pixel accumulation order is unchanged.
No shared crates, parameter metadata or saved-project flags changed.

1080p median selector-time Rust/original ratios, one warmup and five samples:

| Depth | Default before | Default after | Heavy before | Heavy after |
|---|---:|---:|---:|---:|
| 8 | 8.529 | 1.568 | 4.002 | 0.515 |
| 16 | 7.914 | 1.747 | 3.710 | 0.455 |
| 32 | 8.100 | 1.858 | 3.369 | 0.442 |

Baseline is `5033dd45`; before/after resident campaigns were separate runs on a
shared machine. All measured frame pairs were exact; timing is not isolated
hardware qualification. Transactional output allocation/publication and checked
input/output staging remain costs, especially at no-op defaults. The local
thread-selection and row-copy helpers are candidates for later shared hoisting.

Release tests, rustfmt and release Clippy pass (warnings); all 54 golden hashes
match. Seeds 20261114/20261115 each contain 103 cases/depth (100 random), sizes
1x1,3x7,11x7,31x19,97x61 and scales 1,1/2,1/4, at two concurrent renders maximum.
Resident exact counts summed over seeds were 205/205/202 at 8/16/32 bpc; three
32-bpc discrepancies became exact under mandatory per-process replay. Per-process
authority therefore retained 205 exact plus one evidenced original-nondeterministic
exclusion per depth. All three residuals received three fixed reference/candidate
replays plus the existing original-original and zero-offset controls: originals
varied, candidate hashes were stable, all processes succeeded and every zero-offset
control matched. Exclusions are not counted as exact cases. No errors or timeouts.

`perf_noop.py` passed 66 original comparisons across both Directional and Radial:
54 parameter/scale/cropped-demand cases and 12 native fixture checks with padded
rows, nonzero origin and clipped extent. Unit tests separately preserve arbitrary
pixel bits and padding at every depth. Native AE/macOS remain untested.

Local evidence: `D:/olm-rs-target/blurs/bench-before`, `bench-final5`,
`perf-final-audit.json`, `oracle4-OLMDirectionalBlur-*`, `triage-final4`,
`noop-final4` and `tests-final6.log`. Raw outputs/originals/binaries are not committed.

Performance candidate SHA-256: `67bff3262614191da1e0becd742de776db0da0530489c2ff913c5d8d0765ea31`.


## Performance round two - S-blurs

Round two removes the no-op output allocation and second publication copy.
Only the four controlling values are checked out to establish identity; active
renders then obtain the full parameter set and retain transactional staging.
Parameter checkins finish before the no-op copy; primary input pixels stay
checked out until copying finishes. As in the original direct-copy route, a
subsequent input-pixel checkin failure can occur after output publication.
Tightly packed equal-sized worlds use one contiguous byte copy; padded worlds
copy only active rows; different sizes retain the legacy host PF_COPY callback.
No-op ancillary controls do not trigger unnecessary secondary-layer checkouts.

Merged `origin/main` before revalidation. Historical round-one raw run directories
were deleted at the user's request; compact summaries remain under
`D:/olm-rs-target/blurs-evidence/round1`. Round-two exact-case pixels are deleted
after hashing; only mismatches remain temporarily for triage. No shared source
was authored by this job. Final results and compact evidence follow below.

Final 1080p median Rust/original ratios, one warmup plus five samples:

| Depth | Default round 1 | Default round 2 | Heavy round 1 | Heavy round 2 |
|---|---:|---:|---:|---:|
| 8 | 1.568 | 1.057 | 0.515 | 0.511 |
| 16 | 1.747 | 0.880 | 0.455 | 0.474 |
| 32 | 1.858 | 0.957 | 0.442 | 0.471 |

**Acceptance not fully met:** 8-bpc defaults remain 1.057 (3.521 ms Rust versus
3.3322 ms original), a 0.1888 ms median gap. Minima were 2.958/3.0578 ms, so
samples overlap; this is not evidence that the median requirement passed. Staging
is gone. Remaining work is host dispatch/checkouts and byte copying. The pure
copy profile suggests cache-sensitive row/bulk selection as the next experiment:
8-bpc 1080p has the same 8.3 MB payload as the 32-bpc 540p microbenchmark, where
warm row copies beat bulk copies. That is an inference, not an isolated attribution
of the host gap. The requested single final 1080p campaign was not repeated.

Verification: 22 release tests across the three crates pass (one explicit profile
regeneration ignored), rustfmt and release Clippy pass (warnings), and 148 admitted
golden hashes match (14 historical Radial exclusions unchanged). Two cleanup-helper
tests pass. Both seeds include 103 admitted cases/depth at scales 1, 1/2, 1/4.
This plugin retained 205 exact at 8 bpc, 204 exact at 16 bpc, 205 exact at 32 bpc.
Its 4 remaining cases qualified under the existing original-nondeterminism
rule; they are exclusions, not exact passes. All received three fixed pairs.
The existing original-original and exact zero-offset controls also passed.
No unexplained stable mismatch, render failure or timeout remained. The 66 targeted
Directional/Radial no-op and fixture comparisons passed again. No native AE/macOS
performance qualification is claimed.

[Compact round-two evidence](performance-round2.json) records samples, hashes,
case plans, exclusion proofs and counts. The resident audit verified 15 exact cells
and 90 frame pairs; its three incomplete cells are original Radial heavy. Raw
run folders were deleted after compaction; local compact summaries/logs are under
`D:/olm-rs-target/blurs-evidence`.
