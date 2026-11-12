# OLMBlur Rust validation - P-blur

Windows x64, 2026-11-12. **221 exact cases per Smart depth**, including
**209 random cases per depth across two seeds**. Zero mismatches, reference
failures, timeouts or candidate failures. This is AEXCompat evidence, not native AE.

| Corpus | Seed | Random/depth | Smart8 exact | Smart16 exact | Smart32 CPU exact |
|---|---:|---:|---:|---:|---:|
| final-seed-20261112 | 20261112 | 9 | 12 | 12 | 12 |
| final-seed-20261113 | 20261113 | 200 | 203 | 203 | 203 |
| supplemental | targeted | 0 | 6 | 6 | 6 |

Main runs cycle sizes `1x1,3x7,11x7,31x19,97x61` and downsample `1,1/2,1/4`.
The first three cases are explicit default/min/max assignments. Other cases sample
the full declared parameter ranges. Inputs contain partial alpha and hidden RGB.
Deep comparisons use native u16/f32 words, not preview PNGs. All runs use jobs=3,
process timeout 120 seconds and AEXCOMPAT_FRAME_DEADLINE_MS=120000 for both sides.

Supplemental: three untouched-default requests and three cropped demands
`[1,1,6,5]` within `11x7`, each cycling all three scales. This verifies full-frame
checkout union and RETURNS_EXTRA_PIXELS, not separately cropped output worlds.

## Identities

- reference: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- candidate: `d374df21e013d5c78dbae6370b55a86f51ceb952ac660410b47cbcbc9b6bbec0`
- harness: `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27`
- tool: `657b40b68902ac64a9c3d2175e383ae97b9940f2d30a817b9962b350d76b5ab3`
- Worker: `0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302`
- PiPL: `147f220be4bb05cb95d845c71699015a86deb41fe544fb55afa0a3fbe695f78e`; **294 bytes identical**.
- Final candidate: `validation/final-bin/OLMBlur.aex`.
- Build output: `D:/olm-rs-target/P-blur/release/olm_blur.dll`.

[validation-report.json](validation-report.json) retains complete paths, source
hashes, per-seed/depth/mode/scale counts and all exposed inventory comparisons.
Full inputs, requests, raw outputs and owned process PIDs are in ignored
`validation/`. The worker warns `source_newer_than_worker`; evidence binds the
recorded binary, not newer host source. Native UCRT FMA3 was measured enabled.

## Commands and results

From the repository root in PowerShell (use new output directories for reruns):

```powershell
$env:CARGO_TARGET_DIR='D:/olm-rs-target/P-blur'
cargo build --release -p olm-blur -j 2 --manifest-path rust/Cargo.toml
cargo test --release -p olm-blur -j 2 --manifest-path rust/Cargo.toml
$env:PYTHONUTF8='1'
$env:AEXCOMPAT_FRAME_DEADLINE_MS='120000'
$original='D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex/OLMBlur.aex'
$candidate=(Resolve-Path 'rust/plugins/olm-blur/validation/final-bin/OLMBlur.aex').Path
python rust/tools/oracle/olm_oracle.py inventory --reference $original --candidate $candidate --out rust/plugins/olm-blur/validation/final-inventory
python rust/tools/oracle/olm_oracle.py render --reference $original --candidate $candidate --cases 12 --seed 20261112 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --routes smart8,smart16,smart32 --timeout 120 --out rust/plugins/olm-blur/validation/final-seed-20261112
python rust/tools/oracle/olm_oracle.py render --reference $original --candidate $candidate --cases 203 --seed 20261113 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --routes smart8,smart16,smart32 --timeout 120 --out rust/plugins/olm-blur/validation/final-seed-20261113
python rust/plugins/olm-blur/validate_supplemental.py --reference $original --candidate $candidate --out rust/plugins/olm-blur/validation/supplemental
python rust/plugins/olm-blur/collect_validation.py
```

Build and tests pass: **4 tests**, including 576 tuples covering all six C++ workers
at Rust thread counts 1 and 4 (1152 comparisons). Cases include transparent barriers,
zero-radius previews, both biases, repeated/large radii, full-range u16, HDR/negative
float RGB, signed zero, infinity and distinct quiet/signaling NaN payloads. Other
assertions cover low-byte/word stores and odd-stride output padding. Rustfmt passes.
Inventory is identical across all exposed fields; PiPL was independently compared.

## Implementation and investigation

- Current `mac/OLMBlur` adapters and `core/olmblur_*` workers are authoritative.
  Older CLI/IR rounding notes were not substituted. RGB staging is unnormalized
  f32; integer writers use floorf(value+0.5), CVTTSS2SI and low-byte/word stores.
  PF16 does not saturate at nominal white 32768. PF32 stays float; alpha is preserved.
- Non-Legacy uses f32 powf decay, f64 pow radius, f32 radius materialization before
  truncation, and f32 expf coefficients. All UCRT calls use FMA mode. Denominator
  order is (sigma+sigma)*sigma. Smoothness discards its fixed-point fractional bits.
- Legacy preserves six carry partitions, backward exclusion of coordinate zero,
  asymmetric transparent writes and zero-radius pass execution. Production is
  serial; the pure non-Legacy API supports deterministic parallel rows.
- Optimized C++ reference compilation initially differed on mixed NaN payloads.
  `validation/fullworker-o2.asm` proves operand commutation: ADDSS has the new tap
  as destination and the old accumulator second, despite source add(accumulator,
  product). /Od retains source order and all 432 tuples match. Rust math was not
  changed. This test does not establish original-AEX nonfinite conformance.
- No original-AEX pixel mismatch required correction. Before validation, setup
  review corrected the alias to entryPointFunc, Legacy flags to 128 and version
  to 591872. The pre-format candidate passed 103 cases/depth; formatting changed
  its PE hash, so those results are excluded from the final binary counts above.
- A concurrent incomplete workspace member temporarily prevented Cargo parsing.
  Initial tests used an isolated manifest under owned validation/isolated. Final
  build/tests use the normal workspace; no other crate was edited.

## Preserved limits and remaining gaps

Smart worlds must have equal full-frame dimensions and zero origins. Extent hints
are not filtering clips. Public parameter bounds match C++. Small PF32 worlds
(both dimensions <=24) reject finite samples outside [-16,16]; nonfinite values
are admitted. Classic is default-tuple copy-only (Amount=5, Smoothness=100, Repeat=2),
with C++ bounds 4096x2160 and 3840*2160 pixels, and rejects PF32. It is not the AE
SmartFX dispatch route and is not counted as validated here.

No native AE or macOS build was run on this Windows machine. Smoothness hiding
mirrors the C++ callback but native UI remains unverified. PNG-promoted deep oracle
inputs do not cover arbitrary HDR/nonfinite native worlds; those have C++ kernel
tests only. Odd strides are unit-tested, not native AE qualified. Oracle jobs are
independent processes, not AE callback threads.

The oracle owns each child tree via a Windows Job Object, terminates residual
descendants and verifies ActiveProcesses=0 before returning. No background server,
AE application, browser, remote action, commit or installation was used. A final
PID audit checked 1,944 process records (1,427 unique PIDs): no owned process
remained. Reused PIDs were distinguished by creation time; an access-denied PID
was confirmed to be a newer svchost process and another had already exited.
Unrelated processes were left untouched. See validation/cleanup.json.

## Files and shared candidates

Only `rust/plugins/olm-blur/**` was authored: manifest/build script, algorithm,
AE adapter/local support, C++/Rust tests, validation scripts and evidence/report.
Cargo can automatically update the workspace lock. No new dependency beyond the
pilots was introduced. The OLM-internal math publication restriction is retained.

`src/ae_support.rs` locally extends olm-ae with fixed sliders, distinct checkbox
old-project value/default, full-bounds SmartPreRender union and extra-pixels flag,
and scope-bound AEGP suite/stream/effect cleanup. These are shared-hoisting
candidates. Shared crates were not edited; no additional UCRT wrapper was needed.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.
