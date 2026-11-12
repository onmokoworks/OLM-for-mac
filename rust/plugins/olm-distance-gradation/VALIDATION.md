# OLMDistanceGradation Rust validation (P-dgrad)

This crate is a pure Rust SmartFX implementation with a small AE adapter. The C++
reference archive is used only by unit tests. All work and evidence are confined
to this crate; build products use `D:\olm-rs-target\P-dgrad`. No AE installation,
GUI, shared-crate edit, Git operation, or delegated agent was used.

## Implementation and compatibility

- Ported `core/olmdistancegradation_fieldgen.cpp` and the Smart portions of
  `mac/OLMDistanceGradation/{DistanceFilters,BilateralFilters,DistanceField,PixelCompose}.inc`.
- Preserved full-resolution mask reconstruction, raw distance thresholds,
  separately rounded float operations, nearest-even field packing, truncating
  final integer stores, hidden RGB, mask census, and source ownership.
- Both integer depths and float depth are declared. Only SmartFX is compared;
  Classic is not AE-dispatched and the original's Classic stack state is defective.
- Original match name, version, flags, disk IDs, parameter order, defaults, ranges,
  precision, flags, and popup strings are retained. Blur Mode deliberately declares
  five values with only three labels, and In/Out retains declared default zero.
  The harness presents the effective In/Out default as one.
- The complete 310-byte Windows PiPL is identical to the original. Its Windows
  entry is `entryPointFunc`; the Rust DLL also exports `EffectMain`.
- The local parameter setup extension supports the red Gradation Color default
  and the independent popup count. These are candidates to hoist into `olm-ae`.
  No new dependency was introduced beyond the pilots' existing dependencies.

## Native IPP CPU-dispatch finding

The first 23-case campaign matched all 8/16-bit outputs, but four float Bilateral
cases differed by at most 2.384185791015625e-7. Those failures are retained in
`validation/smoke-01`; they are not included in passing totals.

The translated SSE C++ filters were bit-exact against the C++ unit-test oracle.
A controlled original-binary call to the scalar radius-one body (RVA `0x6bd600`)
also matched the Rust result. Calling the original IPP initializer and public
filter dispatch (RVAs `0xc280` and `0xc2f0`) instead reproduced the harness output.
The native IPP CPU index at RVA `0x18a2ae0` was **4**. Thus the difference was the
reference C++ implementation's emulated SSE lane versus the native AVX/FMA lane,
not an output rounding or constant-tuning issue.

Focused static inspection identified the scalar AVX radius-one, radius-two, and
generic bodies at RVAs `0x6cafe0`, `0x6cb360`, and `0x6cbb00`; vector bodies at
`0x6c2980`, `0x6c3260`, and `0x6c4340`. The scalar exponential is `0x1450f60`,
with the 32-entry table and coefficients at `0x145105b`; vector exponential is
`0xba6880`. The Rust implementation preserves their explicit fused operations,
reduction order, scalar side tiles, and vector dispatch boundaries. Radius-two
vector distance-one accumulation starts with Left then Top, unlike the SSE
reference's Top then Left grouping. The original scalar and vector algorithms
remain available to the C++ regression tests.

Production selects the native IPP FMA lane explicitly on every platform, just as
other workspace math uses an explicit UCRT FMA lane. It does not switch based on
host hardware. The retained native qualification is for CPU index 4; a different
original IPP CPU dispatch can produce different last bits. This is an intentional,
binary-grounded difference from the current C++ reference, necessary for the
requested native Windows oracle. Shared C++ sources were not modified.

`tests/capture_native_ipp.py` loads the original without copying it, calls only the
bounded native initializer/filter/exp functions, and exits. Its 126 float-plane
fixtures and 10,001 scalar-exp pairs are retained with hashes and CPU provenance
in `tests/native-ipp-provenance.json`. The fixtures exercise dimensions 1x1, 1x7,
3x7, 11x7, 17x11, 31x19; radii 1,2,3,4,7,12,32; ranges 1,255,32768.

The REA MCP was unavailable in this session. Focused read-only PE/Capstone
inspection and isolated ctypes probes used the installed local tooling; no REA
server, download, helper daemon, or global configuration change was started.

## Native Gaussian SIMD finding

Seed 20261112 case 39 (97x61, Smart32, Gaussian radius 4096) exposed a second
native-versus-emulated arithmetic difference: 1,706 samples differed by at most
5.960464477539063e-8 in candidate v2. This historical result remains retained.

Direct `cvSmooth` calls at RVA `0x12864d0` isolated the filter, and direct
`getGaussianKernelBitExact` calls at `0x1285230` showed identical final float
coefficients for 12 kernel lengths from 1 through 8193. The native SIMD row and
column filters fuse multiply-adds in complete eight-float blocks; scalar tails
retain separate operations. The five-tap SIMD row filter starts with the near
pair product, fuses the center, and then fuses the far pair. This matches the
[OpenCV 4.5.5 filter source](https://github.com/opencv/opencv/blob/4.5.5/modules/imgproc/src/filter.simd.hpp)
(`RowVec_32f`, `SymmRowSmallVec_32f`, `SymmColumnVec_32f`). No coefficients were
fitted to output pixels.

`tests/capture_native_gaussian.py` retains 99 direct native filter fixtures:
11 geometries (including singleton axes and widths 8/9/15/16/17), seven square
apertures through 8193, and two asymmetric apertures. The Rust native lane is
bit-exact on all 99; the 12 float coefficient arrays are also exact. The SSE
arithmetic remains separately tested against the unchanged C++ source.

## Tests and oracle commands

```powershell
$env:CARGO_TARGET_DIR='D:\olm-rs-target\P-dgrad'
cargo build --manifest-path rust/Cargo.toml --release -p olm-distance-gradation -j 2
cargo test --manifest-path rust/Cargo.toml --release -p olm-distance-gradation -j 2

$env:AEXCOMPAT_FRAME_DEADLINE_MS='300000'
# REF = original absolute path in ghidra_windows_aex/DistanceGradation.aex
# CAND = absolute staged Rust .aex path recorded in validation-report.json
python rust/tools/oracle/olm_oracle.py inventory --reference $REF --candidate $CAND --out <new-directory>
python rust/tools/oracle/olm_oracle.py render --reference $REF --candidate $CAND --cases 203 --seed 20261112 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --routes smart8,smart16,smart32 --downsample '1,1/2,1/4' --timeout 300 --out <new-directory>
```

Both process sides record `AEXCOMPAT_FRAME_DEADLINE_MS=300000`. No timeout or
reference failure is a pixel pass. The 16/32-bit comparisons use raw native
sidecars, not preview PNGs. The first three cases are default/min/max; subsequent
cases sample the entire exposed parameter ranges.

Unit tests cover 360 C++ distance/resize/normalization cases, 504 C++ filter
cases, 200,002 C++ scalar/vector exp inputs, 30,000 C++ composition vectors,
32 concurrently repeated distance fields, the native IPP and Gaussian fixtures
above, and UI callback lifetime checks. The final 10 tests passed;
`unit-test-report.json` binds that observed result to source hashes.

## Scope limits

This is Windows x64 AEXCompat evidence, **not native AE conformance**. macOS
arm64/x86_64 builds and native AE were not available or launched. The regular
oracle's input is straight RGBA8 promoted to deep formats, including partial
alpha and nonzero hidden RGB; it does not qualify HDR/nonfinite input or padded,
origin-shifted AE worlds. The implementation retains the C++ float Median
restrictions (including arbitrary Power with radius above two and radius above
500); no refusal is counted as an exact render.

The C++ `UpdateParamsUI` behavior is also ported locally: Power, thresholds,
colors, and Blur Size are enabled/disabled in the same sequence, replacing the UI
flags with exactly zero or `PF_PUI_DISABLED`. Mock-host tests cover normal state
changes and resource cleanup after a failed update. Native AE UI execution is
not qualified. Allocation products are checked for image dimensions; no memory
stress or native AE memory-budget qualification is claimed.

The first 203-case campaign ran candidate v2. After its native Gaussian mismatch
was fixed, `tests/requalify_candidate.py` renders the final candidate against all
retained original outputs using the unchanged shared oracle decoder, comparator,
and Windows Job process cleanup. It verifies original/harness/tool/input/request
hashes, records reference-output hashes, and preserves every original failure.
This avoids repeating the slow original render solely because the candidate
changed. A second seeded `olm_oracle.py render` campaign runs both sides directly.
Only the final candidate results count in the totals below.

Final run counts, identities, and reference failures are recorded below and in
`validation-report.json`.

## Final measured results

| Seed | Route | Exact | Random exact | Reference errors | Reference timeouts | Mismatches / candidate failures |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 20261112 | smart8 | 192 | 189 | 9 | 2 | 0 / 0 |
| 20261112 | smart16 | 192 | 189 | 9 | 2 | 0 / 0 |
| 20261112 | smart32 | 192 | 189 | 9 | 2 | 0 / 0 |
| 20261113 | smart8 | 83 | 80 | 0 | 0 | 0 / 0 |
| 20261113 | smart16 | 83 | 80 | 0 | 0 | 0 / 0 |
| 20261113 | smart32 | 83 | 80 | 0 | 0 | 0 / 0 |

All successful original outputs are bit-exact with the final candidate. Original
failures and timeouts are excluded from pass and random-case totals. Downsample
1, 1/2, and 1/4 were exercised at every depth. Full per-case manifests, original
failure reasons and output hashes are linked from `validation-report.json`.
All 825 successful final renders passed the host checks for guard bytes, output
validity, parameter checkouts, suite leases, handles, and world lifetimes.

### Binary identities

| Binary | SHA-256 |
| --- | --- |
| reference | `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae` |
| candidate | `54252757b3e574326adf03dade4c0db7778c174df5576eadee92ff6ff85652f2` |
| harness | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |
| tool | `657b40b68902ac64a9c3d2175e383ae97b9940f2d30a817b9962b350d76b5ab3` |
| worker | `0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302` |

### Excluded original cases

| Seed | Status | Case indices | Observed reason |
| --- | --- | --- | --- |
| 20261112 | reference_unrenderable | 33, 40, 48, 100, 106, 121, 136, 169, 202 | Median: SMART_RENDER returns 512, SEH code 0 |
| 20261112 | reference_timeout | 54, 129 | 300-second reference process deadline |

The final candidate is `validation/DistanceGradation-v4.aex`; the same DLL is in
`D:\olm-rs-target\P-dgrad\release\olm_distance_gradation.dll`.

The second direct campaign uses `--cases 83 --seed 20261113`; all other render
options match the 203-case first campaign. Final first-seed qualification:

```powershell
python rust/plugins/olm-distance-gradation/tests/requalify_candidate.py --source rust/plugins/olm-distance-gradation/validation/seed-20261112-v2 --candidate rust/plugins/olm-distance-gradation/validation/DistanceGradation-v4.aex --out rust/plugins/olm-distance-gradation/validation/seed-20261112-final
```

Across both seeds, each depth has **275 exact cases, including 269 random cases**.
The exact counts at downsample 1, 1/2, and 1/4 are 92, 89, and 94 respectively,
for each depth. The requalification command exits 2 because it preserves original
reference failures; the second direct campaign exits 0. Neither final campaign
has a mismatch, candidate failure on a renderable reference case, or tool error.

`validation/DistanceGradation-final.aex` is an identical delivery alias for v4.
The build DLL, v4 candidate, and delivery alias share the candidate SHA-256 above.
Every render subprocess used the shared oracle's Windows Job ownership and its
active-process-zero cleanup check. All task exec sessions ended; a final scoped
process check found zero remaining task Python/harness commands. Evidence is in
`validation/process-cleanup.json`. No AE install or persistent helper was created.

## Files and shared candidates

- `Cargo.toml`, `build.rs`: pilot structure, test reference build, PiPL embedding.
- `src/algorithm.rs`, `field.rs`, `filters.rs`, `bilateral*.rs`: portable kernels.
- `src/ae.rs`, `ui.rs`, `shared_candidates.rs`: AE entry, parameters, UI callbacks.
- `src/reference_tests.rs`, `tests/reference.cpp`, native fixtures and capture
  scripts: C++ and original-binary regression witnesses.
- `tests/requalify_candidate.py`, `summarize_validation.py`: final evidence replay
  and aggregation; the shared oracle remains unchanged.
- `VALIDATION.md`, `validation-report.json`, `unit-test-report.json`,
  `pipl-comparison.json`, `worker-identity.json`: retained qualification records.

Hoisting candidates for `olm-ae`: an explicit RGBA color default, a popup count
independent of its labels, and reusable checked-parameter/suite lifetime guards
for UI callbacks. The binary-grounded IPP/OpenCV arithmetic stays local to this
plugin. No new UCRT wrapper or external dependency was needed.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.
