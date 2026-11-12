# Integration Smart32 case 0017 follow-up

**Resolved as original nondeterminism; no production algorithm correction.**
The baseline remains a mismatch, never an added exact campaign case.
[Compact evidence](offset-witness.json) records every rerender and control,
hashes, test provenance and localization. The original integration evidence is
preserved unchanged.

The current integrated candidate is SHA-256
`51eaea21f9bd0e0e00c69fa2ab402947cfc8af5c75e17f05afbd217f86c366f3`,
original `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`,
harness `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27`.
The staged integration file was used directly and was not overwritten.

## Controls and all ten predeclared repeats

Same input, parameters, Smart32 route, 3×7, downsample 1/4, Rotation, Noise Type 1.
Changing **only slot 28 Noise Offset** from −318.36653167426726° to **0°** or
**+1°** gives bit-exact original/candidate output in both controls.

Ten additional original/candidate pairs were declared before execution. All
succeeded; candidate output is constant. Together with the original baseline
and three integration repeats, the 14 original outputs have **five** hashes.

| Additional repeat | Result | Mismatching pixels |
|---:|---|---:|
| 1 | mismatch | 6 |
| 2 | mismatch | 6 |
| 3 | mismatch | 6 |
| 4 | mismatch | 6 |
| 5 | mismatch | 6 |
| 6 | mismatch | 6 |
| 7 | mismatch | 8 |
| 8 | exact | 0 |
| 9 | exact | 0 |
| 10 | mismatch | 6 |

No runs were discarded or added after seeing these results. These two exact
repeats also satisfy the former exact-replay rule, independently of the new
offset-control evidence.

## C++ equivalence and pixel localization

`core/dblur_noise.h::generate_radial_noise_plane` folds positions only above
100, truncates the signed position, and calls `read_noise_table` independently
for each endpoint. Negative endpoints return zero; index −1 still has a valid
right endpoint 0. Rust preserves exactly this behavior, MT19937 draws,
float canonical conversion, interpolation order and the two separate half
products. No wrapping or phase clamp was introduced.

The new regression compares **all 465 float words** of the 15×31 noise lattice
against the existing C++ function for each of the three offsets. All match.
The negative phase has bits `c0b1cf36`, with 20 lattice cells reading endpoints
−4 through −1; the two controls have no invalid endpoints.

At cell size 0.25, only source noise samples **(0,6) and (1,6)** are sensitive
to those reads. A test-only hook changes *only invalid table reads* from their
normal zero to −1 and +1. The complete pure Smart32 render at zero first matches
all words of the staged candidate. The two counterfactual renders affect output
pixels (row-major indices) **6,12,14,15,16,17,18,19,20**. All observed differences
over baseline + three earlier + ten new originals are confined to
**6,12,15,16,17,18,19,20**, a subset. The regression asserts this containment.

This is measured numerical sensitivity, not a memory trace of the original.
The original table-under-read explanation remains a source-grounded inference,
supported by unchanged-input instability, exact offset controls, C++ equivalence,
and pixel localization; arbitrary undefined original bytes are not reproduced.

There is **no Smart32-specific noise or Rotation stage** in this path. Float
input unpacking and final unquantized float packing differ by depth. Noise,
scalar span sampling, polar construction, Rotation accumulation and inverse
sampling are shared; Rotation uses floor addressing at every depth. The
depth-dependent Zoom inverse-addressing branch is not executed here. No 32 bpc
translation discrepancy was found.

## Uniform rule

For any saved case, require successful fixed-count repeats, changing original
hashes and stable candidate hashes. Then either an exact identical-input replay
or the **DirectionalBlur-style offset control** may establish the exclusion.
For the latter, require identical input/route/other parameters, exact zero-offset
control (this follow-up additionally requires a small positive control), C++
zero-read equivalence and differences confined to demonstrated under-read
influence. No negative-offset blanket exclusion or case-index blacklist is
allowed. Preserve raw baseline mismatches and never add controls/repeats to
campaign totals. `collect_report.py` accepts the same evidence fields uniformly.

## Reproduction and limits

From the repository root, use fresh output directories for rerenders:

```powershell
python rust/plugins/olm-radial-blur/triage.py rust/local/integration/cross-check-final/OLMRadialBlur/render/case-0017-smart32 --repeats 10 --out rust/plugins/olm-radial-blur/validation/integration-offset-replays
python rust/plugins/olm-radial-blur/offset_controls.py rust/local/integration/cross-check-final/OLMRadialBlur/render/case-0017-smart32 --out rust/plugins/olm-radial-blur/validation/integration-offset-controls
$env:CARGO_TARGET_DIR='D:/olm-rs-target/P-radial'
cargo test --release -p olm-radial-blur -j 2 --manifest-path rust/Cargo.toml -- --nocapture
python rust/plugins/olm-radial-blur/summarize_offset_witness.py
```

The regression fixture contains the 21 input RGBA8 pixels, staged float output
words and the union of observed mismatch pixels; all are derived from the saved
case, not a replacement renderer. The unit-only hook is absent from production
builds and defaults to zero. **8 tests pass, 1 explicit regeneration test stays
ignored.** No production arithmetic changed, so the full campaign was not rerun.

Both process and host deadlines were 600 seconds; at most three harness jobs
were allowed (these runs were sequential). All 24 harness/worker exits were
verified; no task-owned process remains. No GUI, AE, installation, commit or
shared-code edit. Native AE/macOS remain unverified. Local-only artifacts are
under `validation/integration-offset-*`; compact JSON, tests and this report are
retained. Historical campaign hashes/counts still describe their old snapshots.
