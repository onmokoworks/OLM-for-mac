# Rust integration — 2026-11-12 upstream release

Job I-integrate-20261112, measured on Windows x64 on 2026-11-13. **Twelve CPU
plug-ins build and stage together.** All six release plug-ins pass the ordinary
direct oracle against the new 64/2025 originals and separate 64/2026 samples.
There are no residual failures in these final campaigns. Native AE acceptance
is still unverified; no GUI, AE, installation or original-binary modification was used.

## Harness and host-lifecycle repair

The tool-only detached AEXCompat worktree moved from
`7418be04e400c5020ea5b088e904db3fdf82b052` to origin/main
`032a187621353bac7b92a76ae394ac387ddedf51`, including #1824/#1827/#1828/#1830/#1832.
The native worker was rebuilt with `tools/build-native.ps1 -Target aex_worker`
and the Rust harness with `cargo build --manifest-path broker/Cargo.toml --release
-p aexcompat-harness -j 3`. Native dependency tracking verified 217 translation units.

| Binary | Old SHA-256 | New SHA-256 |
| --- | --- | --- |
| Harness | `68a251fed8131d3a32cdcbd8797aba9959be417d8da68d1e80f44d087c75e9ba` | `92280aa7ca441a59f9edb0b9343779ebf237e6d6949a3e33d2d54515d4130dbc` |
| Worker | `186f0f00b1e9ff793f6ff5f9f23d6167188af3276d298b2ce6764bb6cf9b94f1` | `7a6598974b903fd4b068587b726d41c8adb8b198a294add88d544582482c71cf` |

[Harness evidence](evidence/integration-20261112/harness.json) binds the builds
and the before/after sample: Blur Smart8/16/32 and Smoother Classic8/16,
three sizes/scales per depth, 15 comparison pairs and all 30 side outputs
byte-identical across the harness update. A separate final-port default sample
of all six unchanged plug-ins passes **51/51** route-cases at 1, 1/2 and 1/4;
see [older-port evidence](evidence/integration-20261112/older-ports.json).

The first integrated render attempt exposed a real Rust adapter defect:
parameter checkouts were moved by value before checkin. The host binds each
checkout to its address. Shared and duplicated guards now allocate the parameter
before checkout and preserve that address through checkin; Anti Anti Alias uses
caller-owned storage. Focused tests move a guard and assert exact pointer
identity. No pixel arithmetic was changed by this fix. Failed initial attempts
remain local history and are not counted below.

## Final direct qualification

Every row uses fresh per-process ordinary oracle renders, **no bridge, no sparse
fixture**, Smart8/16/32, downsample **1, 1/2, 1/4**, with at most three concurrent
renders. Counts are exact cases **per depth**, not per scale. Inventories of all
six candidates match their 2025 originals with zero exposed-field differences.
[Qualification evidence](evidence/integration-20261112/qualification.json)
retains original/candidate/tool hashes, commands, plan and summary hashes,
parameter coverage and every baseline result count.

| Plug-in | New 2025 exact 8 / 16 / 32 | New 2026 exact 8 / 16 / 32 | New golden cases |
| --- | --- | --- | ---: |
| ColorKeep 1.1.0 | 30 / 30 / 30 | 12 / 12 / 12 | 54 |
| OLM Color Key 2.3.3 | 226 / 226 / 226 | 12 / 12 / 12 | 54 |
| DistanceGradation 0.8.3 Develop | 30 / 30 / 30 | 12 / 12 / 12 | 54 |
| OLM Smoother2 2.2.0 | 30 / 30 / 30 | 12 / 12 / 12 | 54 |
| OLM UV Map 1.1.1 Develop | 30 / 30 / 30 | 12 / 12 / 12 | 54 |
| OLM Anti Anti Alias | 226 / 226 / 226 | 12 / 12 / 12 | 54 |

Anti Anti Alias and Color Key each use seeds **20261121 and 20261122**, each
with **110 random + default/min/max plans**. Thus each has 220 distinct random
plans per depth; combined scale counts are 76/76/74 (random 74/74/72).
Color Key random plans assign every one of the 1,617 value-bearing controls,
including all **599 slots 1025–1623**. No high-slot filter is used. Its golden
corpus additionally matches the final key of a 200-entry palette.

Other 2025 samples use seed 20261121; every 2026 sample uses 20261123. UV Map
has independent textures sized 17x9, 1x5 and 33x17. DistanceGradation's declared
quick-regression domain limits thresholds to 0–128 and blur size to 0–12, with
other controls sampled over their full declared ranges; it is not a new claim
about all expensive extrema. Its prior original Median/timeout/instability
findings remain applicable. No final residual required ubdetect classification;
no baseline failure was converted into a pass or silently excluded.

## Golden, shared math, staging and tests

The [golden tool](tools/golden/README.md) now supports complete per-plug-in
regeneration and secondary layers. All **324/324** new golden route-cases are
verified byte-for-byte against the new 2025 originals through the ordinary
oracle. Unselected original identities and exclusions are preserved.
The full corpus is **616 exact + 14 historical RadialBlur exclusions**:
54 each for ColorKeep, Blur, ColorKey, DirectionalBlur, DistanceGradation,
KiraKira, Smoother2, ToonDilate, UV Map and Anti Anti Alias; 36 Smoother; 40 RadialBlur.
Golden exclusions do not count as passes.

Smoother2's verified `cbrtf` moved unchanged into `olm-math`. Its bit-exact
native UCRT test passes **1,033,289 raw-word probes**; the optional exhaustive
2^32 check was not run. UV Map's logf and the remaining scope/suite helpers stay
local; broader hoisting is deferred. All combined math artifacts remain OLM-internal.

| Check | Result |
| --- | --- |
| `cargo build --release --workspace` | Pass |
| `cargo test --release --workspace` | 115 passed, 0 failed, 2 ignored |
| Python tool unit suites (12 tools) | 212 passed |
| Windows staging | 12 AEX files; all hashes match the final release build |
| macOS staging | Script covers 12 universal bundles; architecture, PiPL, exports, min OS and ad-hoc seal checked in CI |

[Checks](evidence/integration-20261112/checks.json),
[tool tests](evidence/integration-20261112/tool-tests.json), and
[staged identities](evidence/integration-20261112/staged-identities.json)
bind the local results. The witness descendant-cleanup test now retains the
live child's process handle before releasing its parent, avoiding PID-reuse
and Store-alias ambiguity; production cleanup behavior is unchanged.

Windows and macOS arm64/x86_64 CI also run the complete workspace and golden
tests. The arm64 job packages all twelve universal bundles, while Windows
stages all twelve AEX files. Six updated Mac declarations use captured 2025
metadata; existing bundle IDs remain, with `local.olm-rs.uv-map` and
`local.olm-rs.anti-anti-alias` for the two new effects. No PR or release is created.

## Limits and evidence hygiene

Native AE loading, UI, saved-project migration, Undo/Redo and round trips remain
unverified. The Windows comparison corpus is finite SDR/PNG-promoted deep data;
it does not establish arbitrary HDR/nonfinite or every cropped/padded-world case.
Historical Directional/Radial nondeterminism and DistanceGradation limits remain.
Universal bundles are ad-hoc signed, not Developer ID signed or notarized.

Raw runs, binaries and logs remain ignored under `local/I-integrate-20261112/`.
Only source, compact evidence, declarations and required small test vectors are
versioned. The hygiene audit is scoped to this repository's `rust/`, with the
workflow checked separately. No original AEX or large run outputs are included.
All task-owned processes were waited on; no host-managed or unrelated process
was stopped. The following report is retained as **historical ten-plug-in evidence**;
its blockers, no-push statement and counts do not describe this integration.

---

# Rust integration ? Job I-integrate

Windows x64, 2026-11-12. Ten crates build together with the default `rust/target`
and stage under their original Windows file names. No commits, index writes,
pushes, remote actions, original-binary copies, installations, GUI or AE actions
were performed. All authored changes are under `rust/`. Local artifacts were
ignored, not deleted. No helper/server or unrelated process was stopped.

The integration is reviewable, with existing formatting debt still open. The
RadialBlur Smart32 witness was resolved by the bounded follow-up below as original
nondeterminism; its baseline mismatch is preserved. This is not an all-green
release gate or native AE qualification.

## Changes

- Added workspace artifact exclusions, `tools/stage_windows.ps1`,
  `tools/validate_windows.py`, `tools/audit_hygiene.py`, and compact integration
  evidence. The staging script copies only built Rust DLLs, checks hashes and
  refuses overwrites/application installation paths.
- Added missing ColorKeep/ColorKey `VALIDATION.md` indexes from the retained
  pilot records; marked local-only evidence in every plug-in validation document.
- Replaced the pilot-only workspace README with all-ten status, commands,
  exclusion rules, original/host defects, macOS requirements and hoisting list.
  Corrected oracle point units in documentation and its explanatory source comment.
- Added only narrow lint allowances to Radial's original TURN literal,
  Directional's original angle literal and Smoother's generated module.
  The latter preserves TEST/XOR same-operand instructions, dispatch loops and
  disabled tracing predicates. No constant, operation, algorithm, generated body,
  dependency or reference source changed. No mass formatter or Clippy fix ran.

## Workspace checks

[Machine-readable checks](evidence/integration/checks.json) bind the local logs.
All commands were run in `rust/` with `CARGO_TARGET_DIR` removed.

| Check | Result |
| --- | --- |
| `cargo build --release --workspace` | Pass; all ten DLLs; two Rust dead-code warnings and one C++ unused-variable warning |
| Final staging build (`--offline`) | Pass; hashes of all ten copies match `target/release` |
| `cargo test --release --workspace` | **80 passed, 0 failed, 2 ignored** |
| `cargo fmt --check` | Exit 1; **60 diff blocks in 19 files**; formatting left unchanged |
| `cargo clippy --release --workspace` | Exit 0, no errors; **13,705 Rust warning diagnostics** by Cargo target summaries, plus one C++ unused-variable warning |
| Oracle Python unit suite | **18 passed** |

The ignored tests are Kira's explicitly opted-in original arbitrary-callback
ABI test and Radial's hardware-profile regeneration test (which writes source).
They were not invoked by this integration. The final Clippy log has 13,730
`warning:`-prefixed lines including 21 target summaries and four C++ forwarded
context lines; this is not 13,730 distinct diagnostics. Smoother accounts for
12,921 Rust warnings and Smoother2 library for 625. They mostly concern mechanical
translation/style. Clippy's initial 1,057 deny-by-default findings were the three
scoped source locations described above; only their scoped allowances were added.

Formatting differences span Smoother, Smoother2 and DistanceGradation's
`bilateral.rs`. Making that check green would require the broad formatting pass
explicitly excluded from this task. The exact file list is in checks.json.

## Final staged cross-check

[Cross-check evidence](evidence/integration/cross-check.json) records commands,
identities, route summaries and skipped plans. [Staged identities](evidence/integration/staged-identities.json)
bind the current release DLLs and staged AEX files. Inventory is identical for
all ten, with zero exposed-field differences. Seed **20261120**, **12 admitted
cases per depth**, **jobs 4**, downsample **1, 1/2, 1/4**. Counts are not per scale.

| Plug-in | Inventory | Route | Exact 8 / 16 / 32 | Excluded / unresolved route-cases |
| --- | --- | --- | --- | --- |
| ColorKeep | identical | Smart | 12 / 12 / 12 | 0 / 0 |
| DistanceGradation | identical | Smart | 12 / 12 / 12 | 0 / 0 |
| OLMBlur | identical | Smart | 12 / 12 / 12 | 0 / 0 |
| OLMColorKey | identical | Smart | 12 / 12 / 12 | 0 / 0 |
| OLMDirectionalBlur | identical | Smart | 12 / 12 / 12 | 0 / 0 |
| OLMKiraKira | identical | Smart | 12 / 12 / 12 | 0 / 0 |
| OLMRadialBlur | identical | Smart | **10 / 12 / 11** | **3 original nondeterminism / 0 unresolved** (Smart32 follow-up below) |
| OLMSmoother | identical | Classic | 12 / 12 / ? | 0 / 0 |
| OLMSmoother2 | identical | Smart | 12 / 12 / 12 | 0 / 0 |
| OLMToonDilate | identical | Smart | 12 / 12 / 12 | 0 / 0 |

Total: **345 exact baseline route-cases, 3 baseline mismatches, zero original
errors/timeouts and zero candidate-only failures**. All three Radial mismatches
now qualify for exclusion with the follow-up evidence below. Raw oracle
render exit codes are zero except Radial (1); the all-ten runner correctly exits
1. Exclusions do not turn those baseline mismatch verdicts into passes.

Radial's existing generator wrapper skipped **9 Type-3 plans** at original indices
2, 5, 6, 7, 9, 11, 14, 15, 18, keeping the RNG stream and continuing to 12
admitted plans. Directional's declared popup count is two; all 12 generated
plans were audited to use Types 1/2. No blanket negative-offset exclusion was
applied and no old-seed failure indices were blacklisted.

Kira uses the exact prescribed patched harness and its existing default-omission
wrapper. Others use the shared harness. Both binaries receive the same internal
frame deadlines: DistanceGradation 300000 ms, Radial 600000 ms, others 120000 ms;
outer process timeouts match those seconds. Normal sizes are
1x1, 3x7, 11x7, 31x19, 97x61; the documented Radial envelope ends at 17x9;
Kira uses 5x5, 11x7, 31x19, 97x61 to stay within its approximation admission.

### Radial nondeterminism rule and resolved witness

[Three-replay evidence](evidence/integration/radial-triage.json) retains baseline
and repeated pixel hashes, process outcomes and exact-case identities.

| Saved case | Route | Distinct original / candidate outputs (baseline + 3 replays) | Exact replay? | Decision |
| --- | --- | --- | --- | --- |
| 0003 | Smart8 | 2 / 1 | yes | Excluded original nondeterminism |
| 0017 | Smart8 | 3 / 1 | yes | Excluded original nondeterminism |
| 0017 | Smart32 | 2 / 1 | **no in these three** | Initially unresolved; resolved by follow-up below |

All nine original integration replay pairs rendered successfully. Under the
then-published exact-replay rule, Smart32 case 17 remained unresolved. Those
records and their classifications in `evidence/integration/radial-triage.json`
remain unchanged as historical evidence.

The authorized [Radial follow-up](plugins/olm-radial-blur/OFFSET_WITNESS.md), with
[all results](plugins/olm-radial-blur/offset-witness.json), used the same staged
candidate (`51eaea21…66f3`) and saved 3x7, quarter-resolution, Rotation, Noise Type 1
request. Changing only Noise Offset to **0° and +1° is bit-exact at Smart32**.
Exactly **10 additional pairs** were declared up front and all reported:
repeats 1–7 mismatch, 8–9 exact, 10 mismatch; all succeed and the candidate is
constant. Across all 14 original outputs there are five hashes. Nothing is added
to baseline exact counts.

All 465 lattice words at each of the negative/zero/positive offsets match the
C++ noise generator. Twenty lattice cells read negative table indices; the
C++ and Rust policies return zero per invalid endpoint. Test-only changes to
those reads affect source noise samples (0,6)/(1,6) and nine output pixels;
all eight observed differing output pixels lie within that support. The pure
Smart32 output at zero reads matches the staged DLL exactly. There is no
Smart32-specific noise/Rotation stage; float unpack/pack differs, while the
Zoom-only depth branch is not executed. Original table under-read remains a
source-grounded inference, not a native address trace. No production arithmetic
was changed; eight tests pass and the full campaign was not rerun.

Uniform Radial rule: require changing original hashes, stable candidate hashes
and successful fixed-count repeats, plus either an exact replay or the same
offset-control evidence used by DirectionalBlur. For the latter require exact
zero/small-positive controls with identical input/route/other parameters, C++
zero-read equivalence and differences confined to demonstrated under-read
influence. Negative offsets and case indices are never blanket exclusions.
This witness also satisfies the older exact-replay branch via repeats 8 and 9.
All 24 follow-up harness/worker exits were verified; no AE/GUI was used.

A preliminary full cross-check used the pre-lint-annotation staged build. It is
retained locally but not combined with final counts. The final complete run was
performed after rebuilding/staging the lint-only source revision. All final
staged hashes still match the release outputs after the test run.

## Hygiene decisions

The authoritative [would-be-added manifest](evidence/integration/hygiene.json)
contains `git add -n -- rust` output, every selected path/size, totals, largest
files, area counts and link checks. It uses no Git index mutation. Existing
tracked `rust/olmcolorkey_cli` files are reported separately and unchanged.

Final dry-run selection: **246 files, 6,736,385 bytes** (about 6.4 MiB).
Largest entries are Smoother's generated Rust (1,266,649 bytes), the existing
oracle Radial diagnostics JSON (633,600 bytes), and DistanceGradation's
validation report (625,500 bytes). Only the first exceeds 1 MB, justified below.


| Crate | Commit evidence / inputs | Local-only artifacts ignored |
| --- | --- | --- |
| ColorKeep | Validation index, report, original inventory, PiPL/build-equivalence JSON, source | validation runs, candidate inventory/path, binaries |
| DistanceGradation | Report, inventory/PiPL/worker/unit identities, capture/requalification scripts, four native reference `.bin` vectors and provenance | validation, AEX, raw images, logs |
| OLMBlur | Report, inventory/PiPL/build-equivalence, supplemental/collector scripts, C++ test shim | validation, isolated workspace, binary and process outputs |
| OLMColorKey | Validation index, report, inventory/PiPL/build-equivalence, pilot runner, reference tests | validation, candidate path, binaries |
| DirectionalBlur | Validation/report, inventory/PiPL/source/runtime identities, diagnostic/collector scripts, reference tests | validation/build-workspace, per-case evidence, candidate-path |
| KiraKira | Validation/report, rerun/revalidation scripts, Rust/C++/native callback tests | validation binaries, verbose disassembly, images and logs |
| RadialBlur | Validation/report, inspect/PiPL, rerun/triage/collector/audit scripts, reference tests | validation campaigns, binaries, raw output/process logs |
| Smoother | Validation/report, PiPL/environment/cleanup, translator/reference tests, required generated Rust | validation, tools/work AST/build logs, binaries |
| Smoother2 | Validation/report, campaign/process summaries, geometry provenance, PiPL/rebuild identities, generator/reference tests | campaign-*, inventory-*, oracle-*, original-inventory-run, standalone, root AEX/logs |
| ToonDilate | Validation/report/PiPL, collector and C++/Rust reference tests | validation, isolated build, binary/pixel/log outputs |

Shared sources, Cargo manifests/lock, oracle source/tests and existing compact
oracle evidence are retained. No PE executable or plug-in binary is selected.
DistanceGradation's `.bin` data are test-consumed native float vectors, **not
executables**: 516,528, 150,192, 87,808 and 80,008 bytes.

The only selected file over **1,000,000 bytes** is
`plugins/olm-smoother/src/generated.rs` (**1,266,649 bytes**). It is required Rust
source imported by the crate and preserves a mechanical instruction translation;
`tools/translate.py` is retained. Omitting it breaks a normal build; regenerating
or refactoring it is outside this integration. This is the explicit size exception.
All explicit local Markdown links in the ten `VALIDATION.md` files resolve to
tracked or would-be-added files. Ignored/absolute raw-evidence paths are expressly
marked local-only. No repo-root `.gitignore` change was needed.

## Reproduction, lifecycle and limits

See [README](README.md) for build/stage/cross-check commands. To audit hygiene
from repository root:

```powershell
python rust/tools/audit_hygiene.py --out rust/evidence/integration/hygiene.json
```

Raw run data/logs are **local-only** under `rust/local/integration/`:
`staged-final/`, `cross-check-final/`, `radial-triage-final/`, and command logs.
No original binary is present there. Per-crate original records are not rewritten
to claim that old campaigns used the new DLL hashes.

[Process cleanup](evidence/integration/process-cleanup.json) checks only recorded
owned PIDs; 1,222 unique recorded PIDs were absent or demonstrably reused after
the saved exit. No current owned process remained and no process was killed by
name. All task exec sessions were awaited. The shared oracle encloses each
harness tree in a Windows Job, terminates residual descendants, checks
ActiveProcesses reaches zero and waits before returning. Known worker file hashes
are recorded with the limitation that they are default-path file identities,
not new loaded-module mapping evidence.

Unresolved: existing fmt/lint debt, macOS builds and
native AE/GUI/project qualification. Existing per-crate CPU-profile, admission,
PNG-promoted deep-world and original undefined-memory limits continue to apply.
No algorithm hoisting or refactor was attempted.
