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
