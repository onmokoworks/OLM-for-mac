# P-kira — OLMKiraKira Rust validation

**Completed:** the verified Rust AEX is bit-exact on all **720/720 SmartFX route-cases** against the retained original outputs. Inventory and the complete Windows PiPL match. Eight C++ reference tests and both native ramp-callback runs pass.

## Deliverables and scope

`olm-kirakira` is an independent workspace member, producing an `rlib` and Windows `cdylib`. Only this crate was edited. No shared Rust code, C++ implementation, original AEX, harness/worktree, AE installation, Git state, or external service was changed. Cargo may register this member in the workspace lockfile automatically.

- `src/algorithm.rs`, `filters.rs`, `trig.rs`, `trig_tables.rs`: ordered scalar/color seeds, four directional rays and Highlight, box/Gaussian/legacy exponential filters, rotation, approximation, union aggregation, composition, and typed output.
- `src/params.rs`, `ae.rs`, `adapter.rs`, `build.rs`: original declarations, saved IDs, entry aliases, SmartFX host boundary, arbitrary callbacks, and PiPL.
- `src/ramp.rs`, `presets.rs`, `editor.rs`, `ae_ui.rs`: original ramp ABI, 34 presets, editing state machine, Drawbot commands, color picker, clipboard, and Use Ramp UI updates. UI instance state is removed on sequence/global setdown. Suite/object ownership is scoped; host callbacks are made outside the UI-state mutex.
- `tests/`: C++ reference comparisons and an opt-in native arbitrary-callback test.
- `validate.py`: local, narrowly scoped default-transport adapter around the unchanged shared oracle. `revalidate.py` compares new candidate renders against hash-bound original evidence using the shared process/compare code. `summarize.py` checks and aggregates the final evidence.

The C++ reference archive is test support; the shipped effect's rendering and UI implementation are Rust. No new external crate was introduced beyond dependencies already used by the workspace/pilots. The OLM-internal `ucrtmath` dependency must not be published standalone.

## Binary identities

The tested AEX is `validation/OLMKiraKira-verified.aex`, retained locally and not installed. Build output uses `D:\olm-rs-target\P-kira`.

| Artifact | SHA-256 |
| --- | --- |
| Original `OLMKiraKira.aex` | `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7` |
| Tested Rust AEX | `443084c071e40268f64f82215b0db5facb0f4596688fab87dba54740ab906611` |
| Patched diagnostic harness | `41a939afc290a750a698a9ec55ea09431bf9a0291e85ebd08bbf3f46f0c2fee7` |
| Patched diagnostic worker | `1ee0a3d824b677be551d1d3ee69aa0a00602ca7d750d6eb3836417e859bbca93` |
| Shared oracle Python | `657b40b68902ac64a9c3d2175e383ae97b9940f2d30a817b9962b350d76b5ab3` |

The harness is exactly `D:\AEXCompatWorktrees\olm-diag-kirakira\broker\target\release\aexcompat-harness.exe`; its worker is `D:\AEXCompatWorktrees\olm-diag-kirakira\target\minihost-build\aex_worker.exe`. Neither was rebuilt or modified. Complete paths/hashes and source hashes are recorded in `validation-report.json`. Rebuilding can change PE timestamps/debug identifiers; the retained AEX is the precise artifact used for the final corpus.

The complete **298-byte Windows PiPL is byte-identical**, SHA-256 `1d3ffb7c9189da6d6a14ae253ff82821f239f3c902456157cba2595cb492b97f`. This includes `entry_point`, version 3.2 development, match name `OLM OLM Kira Kira`, category, flags `0x02008040`/`0x08001400`, and the original two-byte `eINF` declaration. The pilot's binary resource embedding avoids the pinned RC emitter's Japanese-code-page corruption. `EffectMain` remains an additional exported alias.

Inventory comparison covers all 40 non-input parameters (41 including input). The declared popup counts intentionally retain the original inconsistencies: Channel count 6 with four labels; Blur count 3 with four labels. Disk IDs are preserved independently of slot order.

## Gain and untouched defaults

Slot 5 declares **`0.10000000149011612`**, outside both its valid and slider ranges **[1,100]**. The Rust declaration is unchanged. The measured/default host behavior is **1**, consistent with the evidence cited in `.codex-jobs/A-diag/report.md` section 1. This job did not run AE itself.

The shared oracle generator still emits that raw declaration as an explicit numeric assignment when choosing the default. Strict rejection of such an explicit edit is correct. `validate.py` removes slot 5 only when the generator chose that declaration; it never clamps an explicit in-range edit. Case zero uses **an empty assignment list**, so each plug-in supplies its own defaults independently. The patched harness preserves the untouched arbitrary handles; no printable ramp text is fabricated and no original ramp tail is injected into the candidate.

All ordinary generated assignments, input images, rendering, comparisons, hashes, and Windows Job Object cleanup remain the shared oracle's implementation. The cases record each omission in `default_transport`.

## Final render corpus

| Seed | Smart 8bpc | Smart 16bpc | Smart 32bpc | Mismatches / failures |
| --- | --- | --- | --- | --- |
| 20261112 | 120/120 exact | 120/120 exact | 120/120 exact | 0 / 0 |
| 20261113 | 120/120 exact | 120/120 exact | 120/120 exact | 0 / 0 |
| Total | **240/240** | **240/240** | **240/240** | **0 / 0** |

Maximum absolute difference is **0** at every depth. No original failures were excluded from these totals.

Two seeds: **20261112, 20261113**, 120 cases each, at every route: `smart8`, `smart16`, `smart32` (native `-32-cpu`). Each seed contains one independent default case, two min/max boundary cases, and 117 randomly generated parameter cases: **234 random cases, four boundary cases, and two defaults per depth**. Sizes are **5×5, 11×7, 31×19, 97×61**; downsample metadata cycles through **1, 1/2, 1/4**. PNG-derived inputs are finite SDR. Integer raw 16-bit and IEEE binary32 sidecars are compared, not preview PNGs for higher depths.

Runs use **3 concurrent jobs**, 120-second process timeout, and **`AEXCOMPAT_FRAME_DEADLINE_MS=120000` on both sides**. No forced classic route is included. The original full two-sided runs remain in `validation/final-<seed>/`. After correcting the color SIMD tail, `revalidate.py` rendered every case with the final candidate against those retained original outputs, verifying the original input/request manifests and recording original raw-output/process hashes. It explicitly marks the reference as reused actual evidence, never as a new process. Candidate rerenders and comparisons are in `validation/verified-<seed>/`; the compact versionable report binds both summaries and case manifests by hash.

## Root causes resolved

1. **Typed default transport:** the out-of-range declared Gain default and untouched arbitrary params are host transport concerns, not altered plug-in ranges. The prescribed patched harness plus the local omission adapter makes default-only renders meaningful.
2. **Native Gaussian arithmetic:** a direct nonfused translation agrees with the C++ baseline but differed slightly from this original's native AVX2 path. The original `opt_AVX2::RowVec_32f` string identifies the function at RVA around `0x1319472`: it uses `VFMADD231PS` in eight-float groups; the RowFilter tail uses separate multiplication/addition. Rust explicitly reproduces that arithmetic, including the five-tap ordering and scalar tail. Four-component filters count **w?4 floats**, so an odd final pixel is nonfused. This was exposed by seed 20261113 case 92 (5?5, color Gaussian): four output components differed at one pixel by at most 1.49e-8. Correcting the component count made the full case and all six isolated ray combinations exact. Read-only disassembly is retained in `validation/gaussian-avx2-disassembly.txt`.
3. **Approximation resize:** the original native IPP four-component resize uses fused interpolation, including one-axis edge operations. Reproducing only interior FMA left mismatches at image edges. The complete native profile matches the retained output. Relevant original kernel evidence is in `validation/focused-disassembly.txt` (e.g. RVA `0x6e7040` and neighboring resize kernels).
4. **Angle and conversion semantics:** the original consumes raw signed 16.16 angle bits as degrees in its ray state, materializes percentages/downsample in binary32, and truncates typed output. These operations and UCRT FMA-mode calls remain explicit.

Selection of the native arithmetic profile is inferred from controlled output deltas plus the instruction evidence; this job did not record a runtime trace of CPU-dispatch calls.

`Params::fused_filters=false` and `fused_resize=false` retain the source C++ baseline for independent translation tests. The AE adapter uses the verified native profile. No fitted pixel constants or fixture-dependent output substitutions are used. Embedded trigonometry tables and presets are translated from the existing C++ files.

## Saved ramp ABI and UI tests

Memory payload: **324 bytes** (`repr(C)`: `u32 count`, sixteen records of five binary32 fields: position, alpha, red, green, blue). Flattened payload: **325 bytes**, byte 0 = 1, bytes 1–4 = little-endian count, bytes 5 onward = the records. The parser follows the C++ version-byte tolerance and rejects count >16 or truncated active records.

NEW/COPY/DISPOSE/FLAT_SIZE/FLATTEN/UNFLATTEN/INTERP/COMPARE and empty PRINT/SCAN behavior are implemented. Interpolation repeats the last endpoint of the shorter ramp and preserves the C++ multiply/add order. Defaults match the original's three-stop ramp.

The opt-in native test loads each real AEX and calls its entry point. For **each plug-in** it checks five default ramps and **255 UNFLATTEN→COPY→FLATTEN round trips** (five slots × [17 counts from 0 through 16 + all 34 presets]), plus the reported flat size. It compares header and active records exactly. **Original inactive capacity is unstable stack data; Rust zeroes it, as the C++ port does. Whole unused-buffer identity is not claimed.**

The test is a deliberately minimal arbitrary-callback host, not a complete AE lifecycle host. An early attempt to simulate original GLOBAL_SETDOWN in the minimal host ended with a process heap failure; its cause was not established, and it is not classified as an original plug-in defect. The final callback-only test does not invoke that selector: it disposes all mock-owned handles and exits the isolated test process, which releases the loaded DLL/runtime. Both original and candidate tests exited with code 0; native handle allocations have checked trailing canaries.

Eight regular C++/Rust tests pass:

- 40,000 sine/cosine angle pairs; 1,820 filter configurations, including tiny images and large angles.
- 108 seed vectors, 11,858 source/glow compositions, and four resize geometries.
- 72 full C++ pipelines across channels 1–6, modes 1–3, two geometries, and approximation on/off, using the nonfused source profile.
- Ramp layout/flattening; 1,734 interpolation combinations; ten retained Mode 4 pipeline comparisons.
- Four simultaneous render calls reproduce the single-call result; the current kernels are serial and have no render-global mutable state.
- **2,017 UI events** compare ramp/clipboard/state/RNG exactly and hash every ordered draw-command field/text against `RampEditor.h`.

The native callback test is ignored in the ordinary test command because it requires an explicit local AEX path. It was also run explicitly against both artifacts.

## Limits and unverified surfaces

- **AEXCompat is a host emulator.** This establishes same-host CPU output parity for the listed corpus, not native AE acceptance. No AE launch, installation, project reopen, native undo, native UI rasterization, or macOS build/signing was performed.
- Active **non-default custom ramps are still refused by the render admission**, matching the C++ supported Smart lane. Their editing, serialization, copying, interpolation, and saved payloads are implemented independently. This port does not expand that render proof.
- Approximation with a source dimension below four remains refused. Development smoke case 6 (`3×7`, approximation on at full resolution) demonstrated this existing C++ boundary while the original rendered. It is retained as a known limitation and is not silently counted as an exact case. Main corpus dimensions are within the supported lane.
- Mode 4 is outside the original declared popup range. The retained C++ generic legacy tuple family and its filter are implemented/reference-tested, but no native oracle coverage is claimed for the hidden Mode 4 or classic compatibility/fixture routes. Tiny legacy fixture-only admissions are not part of this Rust SmartFX validation.
- Native HDR/nonfinite input, production-sized images, arbitrary ROI/layout combinations, and non-AVX2 original dispatch were not exercised by the PNG-based final corpus. Explicit FMA/nonfused arithmetic makes the selected profile deterministic across architectures; macOS equivalence still requires an actual build/run.
- The shared AE adapter was copied and extended locally because this job owns only its crate. Hoisting candidates: Angle/arbitrary parameter kinds, independently declared popup counts, handle/suite lifetime helpers, UI enable/disable updates, and the ramp/Drawbot adapter. No shared crate was edited.

## Reproduction

Run from the repository root. Choose unused output labels for new campaigns; the retained final summaries bind the tested AEX above.

```powershell
$env:CARGO_TARGET_DIR='D:\olm-rs-target\P-kira'
cargo build --manifest-path rust/Cargo.toml --release -p olm-kirakira -j2
cargo test --manifest-path rust/Cargo.toml --release -p olm-kirakira -j2
$env:OLM_KIRA_ORIGINAL='D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMKiraKira.aex'
cargo test --manifest-path rust/Cargo.toml --release -p olm-kirakira --test original_ramp -- --ignored --nocapture
# Repeat the ignored test with OLM_KIRA_ORIGINAL set to the retained candidate AEX.
$env:AEXCOMPAT_FRAME_DEADLINE_MS='120000'
$h='D:\AEXCompatWorktrees\olm-diag-kirakira\broker\target\release\aexcompat-harness.exe'
$o='D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex\OLMKiraKira.aex'
$c='rust/plugins/olm-kirakira/validation/OLMKiraKira-verified.aex'
python rust/tools/oracle/olm_oracle.py inventory --harness $h --reference $o --candidate $c --out rust/plugins/olm-kirakira/validation/inventory-recheck
foreach ($seed in @(20261112,20261113)) {
  python rust/plugins/olm-kirakira/validate.py render --harness $h --reference $o --candidate $c --out "rust/plugins/olm-kirakira/validation/recheck-$seed" --cases 120 --seed $seed --jobs 3 --timeout 120 --routes smart8,smart16,smart32 --sizes 5x5,11x7,31x19,97x61 --downsample 1,1/2,1/4
}
# Revalidate the retained corpus without relaunching the original:
foreach ($seed in @(20261112,20261113)) {
  python rust/plugins/olm-kirakira/revalidate.py --baseline "rust/plugins/olm-kirakira/validation/final-$seed" --candidate $c --out "rust/plugins/olm-kirakira/validation/revalidate-$seed"
}
# Aggregates the retained verified-* runs, not the new recheck labels:
python rust/plugins/olm-kirakira/summarize.py
```

`validation/` is ignored because it contains binaries, pixels, verbose process logs and diagnostic disassembly. `validation-report.json` and this document retain the reviewable summary. Every owned oracle process is enclosed in the shared runner's Windows Job Object; that runner terminates remaining descendants and verifies zero active processes before closing each job. The final task waits for its build/test/oracle shell sessions to exit. No detached helper, watcher, server, or installation is created.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.
