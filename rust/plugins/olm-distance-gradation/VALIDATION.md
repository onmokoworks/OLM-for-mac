# DistanceGradation — integrated 2026-11-12 release

## Current direct qualification (2026-11-13)

The final twelve-plug-in workspace candidate passes the **ordinary direct oracle**
using AEXCompat `032a187621353bac7b92a76ae394ac387ddedf51`. No bridge or sparse
fixture is used. Smart8/16/32, downsample 1, 1/2 and 1/4, fresh per-process
renders, at most three concurrent renders. Counts below are **per depth**.

| Reference | Smart8 | Smart16 | Smart32 |
| --- | ---: | ---: | ---: |
| New 64/2025 | 30 exact | 30 exact | 30 exact |
| New 64/2026 sample | 12 exact | 12 exact | 12 exact |
| New original-verified golden | 18 exact | 18 exact | 18 exact |

Zero pixel mismatches, reference/candidate failures or timeouts remain in these
campaigns. Inventory matches the 2025 original. This quick regression bounds thresholds
to 0–128 and blur size to 0–12; other controls use their full declared ranges.
Historical original instability and expensive-extrema limits remain.

[Integration report](../../INTEGRATION.md),
[hash-bound qualification](../../evidence/integration-20261112/qualification.json),
[staged identity](../../evidence/integration-20261112/staged-identities.json) and
[golden verification](../../tools/golden/verification.json) are the current
authority. Native AE UI/project acceptance remains unverified. Prior job reports
below retain their original hashes and diagnostic observations as **history**;
their old bridge, harness-limit, pending-golden or local-only hoisting statements
are superseded by the direct evidence above.

---

# 2026-11-12 upstream update (Up-dgrad)

The current source targets the new **2025 Windows build**. Qualification below
is AEXCompat CPU evidence, with explicit original-instability exclusions; it is
**not native AE exact**. The earlier P-dgrad report is retained below as history,
not as qualification of this release.

Machine-readable results and identities:
[upstream-validation-report.json](upstream-validation-report.json) and
[upstream-static-report.json](upstream-static-report.json).
All edits are inside this crate. No Git operations, shared-source edits,
subagents, GUI, AE launch, installation, or changes to original binaries occurred.

## Upstream findings and implementation

| Area | New-release evidence and port change |
|---|---|
| Declarations | Use Padding appended at slot/disk ID 13, default off; slider display maxima 512 → 1000; valid maxima remain 1000. Existing IDs/types retained. |
| PiPL / setup | Version `0x41800` (0.8.3 Develop), out_flags `0x06000240`, out_flags2 `0x08001400`; complete Windows PiPL byte-identical to 2025. |
| SmartPreRender `0x1174330` | Expands result and maximum extents by truncated preview padding. Implemented in local `pre_render.rs`; parameter checkouts are balanced. |
| Drivers `0x1171050`, `0x1171f20`, `0x1172df0` | Build transparent padded input, reconstruct full-resolution dimensions, and offset source coordinates. Both mode copies each field through the original mask. |
| Pixel callbacks `0x1170460`, `0x1170880`, `0x1170cc0` | Reviewed padding offsets and composition against the new drivers. |
| Field `0x11750f0` | Zero truncation threshold uses 0.1. Normalization retains observed_max/requested_threshold when the field does not reach the threshold. |
| Existing IPP sqrt path | Dispatch index 4 reaches `0x4a940`, then `0x190ee0` / `0x2f1e20`; translated RSQRT/FMA refinement, 8-float alignment, 16-float groups and zero fallback. |
| Existing IPP resize path | `0x12af8c0` → `0x12addd0` / IPP → `0x363e80`; row routines `0x729e60` and `0x72a040` use delta interpolation, FMA groups of four, and non-fused tails. |
| Bilateral size zero | Native `cvSmooth` still executes a radius-one filter. Removed the old U16 bypass. |

The old and new 2025 binaries are 26,289,664 and 26,292,736 bytes respectively.
No PE imports were added or removed. `IPPCODE` and `IPPDATA` are byte-identical
old/new and 2025/2026. OpenCV 4.5.5 was already statically linked; the large file
is not evidence of a newly added library. Padding exposes existing numeric
paths that the previous Rust staging did not reproduce fully.

The saved U-triage results were verified against exact original hashes:
12 behavior cases/depth (9 changed), 26 sensitivity cases/depth (24 changed),
139 changed functions (90 normalized-code changes, 49 referenced-data-only),
60 added and 59 removed. Funcdb reports 15,956 exact, 601 fuzzy and 13 unknown
functions. These counts guide review, not proof of equivalence. Nine effect
functions were reviewed explicitly; hash-bound details are in the static report.

Complete scaffold declaration capture has **zero differences**, including
checkbox labels and Power's 2025 curve tolerance. The 2026 declaration differs
in SDK minor 29 versus 28 and Power curve tolerance 0 versus 0.05. The port uses
2025 declarations, with separate 2026 pixel checks below.

## Final oracle counts

Every row covers Smart8, Smart16 and Smart32 at downsample 1, 1/2 and 1/4.
Equality is exact sample/word equality; no tolerance or NaN canonicalization.
Candidate SHA-256:
`fae669a69389d3292f94d87a3854607d6eab13f5756f64cd6bd2dce7d3365318`.

| Corpus | Planned per depth | Exact 8 / 16 / 32 | Original-varying 32-bit cases | Original errors per depth |
|---|---:|---:|---:|---:|
| 2025 seed 20261112 | 133 | 130 / 130 / 129 | 1 | 3 |
| 2025 seed 20261113 | 133 | 131 / 131 / 129 | 2 | 2 |
| 2025 fully opaque edges / slider boundaries | 42 | 42 / 42 / 40 | 2 | 0 |
| 2026 fully opaque edges / slider boundaries | 42 | 42 / 42 / 39 | 3 | 0 |
| 2026 mixed-alpha sample | 18 | 18 / 18 / 18 | 0 | 0 |

There are **255 successfully rendered random cases per depth over two seeds**,
in addition to six default/minimum/maximum cases. Of the random cases, 255 are
exact at each integer depth and 252 at float depth. This exceeds the requested
200 random cases per depth. Original error cases (seed 1: 60/75/78; seed 2:
111/112) remain errors, not passes. Final candidate-only failures: zero.

Random thresholds sample 0–128, Blur Size 0–12, with other controls over their
full exposed ranges. Sizes are 1×1, 3×7, 11×7, 17×11 and 31×19. This is a
declared bounded corpus, not full-range random qualification. The separate
42-case opaque corpus covers padding on/off, all In/Out and Render modes,
all three scales, and explicit thresholds 512 and 1000. The initial full-extrema
attempt is retained in `validation/upstream/smoke-v1`; all-max padding plus blur
timed out in the original at each depth. It was not clamped or counted as exact.

The two seed originals were rendered in fresh per-process workers. After the
last implementation change, the final candidate was rendered again against
their immutable original outputs with executable/input/request/output hashes
checked. These are `final-v8-seed-20261112` and `final-v8-seed-20261113`.
Both opaque corpora and the 2026 sample are fresh paired per-process runs.
All campaigns use at most two render workers. Raw evidence is under ignored
`validation/upstream/`; no historical failed run was overwritten.

A direct original-2025 versus original-2026 comparison also verifies all 18
mixed-alpha samples per depth exactly, with input/request identity checked.
The opaque pair comparison is 42/42/41 exact at 8/16/32 bpc; its one float
difference is covered by the original-variation evidence below.

## Residuals and native alignment

All eight retained float mismatch pairs were classified with **eight original
and eight candidate fresh-process repeats each**. Every original produced two
different outputs; every candidate produced one, also observed in the original
population. Maximum retained difference is `5.960464477539063e-8`.

`tests/update_report.py` separately checks the actual saved campaign pairs
against each complete variation mask: **zero mismatch pixels outside observed
original variation**, and both saved outputs occur in the original population.
This explicit check matters because ubdetect's automatic-exclusion flag is
false when its own first trial happens to be exact. Baseline differences stay
in the table; classifications are not added to exact totals. No poisoning or
out-of-bounds-read claim is made.

There is binary-grounded evidence for address-sensitive square-root rounding.
The captured 267×263 distance plane starts at address 16 modulo 32. Applying
the native group/fallback arithmetic at that offset matches every recorded
word; canonical offset zero differs at 19 words. This arithmetic check recovers
integer squared distances from the recorded roots and is not an independent
EDT proof. It supports the alignment explanation for observed instability.
The Rust implementation deliberately uses a deterministic canonical alignment.
The RSQRT table is a tested CPU profile: 140,960 instruction probes cover 8,192
bins plus random normal inputs. Other CPU implementations are not qualified.

## Stage evidence and regression checks

- Captured field, resize, EDT, normalization and filter planes with the local
  IplImage adapter and the unchanged shared record/witness tools. Input/output
  blobs and native records have SHA-256 provenance.
- The 75×71 / 300×284 case exposed sqrt/FMA differences; its final five mapped
  stages are exact. The 69×63 / 282×258 case isolated resize and is exact after
  the FMA/tail fix. The 117×121 / 236×244 case has exact fields, EDTs and Bilateral
  output; driver inspection then localized the Both-mode masked-copy bug.
- Four recorded native fields and a complete ARGB8 masked-copy regression are
  checked-in small fixtures. The old C++ field oracle is retained explicitly
  as `normalized_legacy`; it does not validate the new normalization semantics.
- `python tests/update_build.py test`: **13 passed, 0 failed**, including the
  new native fixtures, UI callbacks, existing numerical filters and concurrency.
- Default release build succeeds without warnings. The copied v8 candidate and
  the current default Cargo DLL have the same SHA-256. Diagnostic exports are
  feature gated and absent from that artifact.

The shared diverge maps cover Distance's Gaussian passes, not its new field
staging/resize paths. Job-local capture/witness adapters provide the needed
stage comparisons without changing shared tools. Ghidra's inferred non-returning
thunks hid part of IPP initialization; bounded disassembly resolved those paths.

## Compatibility, handoff and limits

Old AE projects retain their effect match name and existing parameter IDs/types.
Use Padding is appended and off by default. New upstream normalization changes
the image even when padding is off; this is intentional release compatibility,
not preservation of old pixels.

The shared golden owner must:

1. Add `use_padding: false` to the `Params` literal in
   `rust/tools/golden/src/bin/golden-olm-distance-gradation.rs`. The new public
   field otherwise makes that runner fail to compile. No shared file was edited.
2. Regenerate the **54 DistanceGradation golden hashes** against the new 2025
   original. Current `--only` is diagnostic; publication requires a complete
   all-ten run, so existing shared manifests were not rewritten.
3. Resolve the shared workspace lockfile update independently. Builds here use
   an isolated offline snapshot of this crate and its three shared dependencies,
   with `CARGO_TARGET_DIR=D:/olm-rs-target/Up-dgrad`.

No native AE/macOS build or execution is claimed. HDR/nonfinite inputs, arbitrary
cropped/strided worlds, other CPUs, and untested high-cost parameter families
remain outside this qualification. Existing Classic-route limitations remain;
Classic is not advertised as an AE-dispatched route here.

Owned Ghidra hub PIDs 60012 and 59484 were stopped and their exits verified;
the latter's five owned PIDs all exited without force. The unrelated shared hub
was left running. Render/record/witness/ubdetect tools own and verify their worker
trees; all task exec sessions completed. No background helper was installed.

---

# Historical OLMDistanceGradation Rust validation (P-dgrad)

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
