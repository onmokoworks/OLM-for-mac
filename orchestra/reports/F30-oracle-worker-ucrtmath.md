status: done

summary:
- Built and registered an isolated F29 + UCRT expf/atan2f/powf reference worker; default and saved corpora unchanged.
- Real Unicorn import-hook validation: 12 million calls, zero raw-bit mismatches against the F27c Rosetta PE oracle.
- Both DLL names and both FMA modes tested; FMA defaults to 1. Other math imports remain unchanged.
- Completed 3,000 seed cases and all 708 saved cases for each of default/F29/F30; all numerical transitions attributable, zero unexplained findings.
- RadialBlur Smart improves 148→240 exact; native-carrier checking exposes only the same pre-existing F29 UI-interface failures.

facts:

Read AGENT_GUIDE.md, GOTCHAS.md, the compatibility plan, current per-plugin
forbidden-action matrix, F29 build/report and F27/F28 validation artifacts.
Branch: `orch/F30-oracle-worker-ucrtmath`. No plugin, release gate, ledger,
MAIN, original AEXCompat source, default-worker setting, or saved corpus changed.

Built from the **final actual-default-lineage F29** snapshot at
`~/.cache/olm-emu/src-F29/reference-guest`, not the older C24 lineage.
`F30-evidence/parent-source.json` pins all 436 parent files. The committed patch
plus the repository's unchanged `ucrtmath/` reconstructs all 484 compiled source
files identically; all F29 vendor/Unicorn files remain identical to the parent.
The source snapshot is `~/.cache/olm-emu/src-F30/reference-guest`.

The new safe Rust dependency compiles `expf.c`, `atan2f.c`, `powf.c`, `tables.c`
into a C static library with `-O2 -ffp-contract=off -fno-fast-math`. Only its FFI
module uses unsafe code; the worker's existing forbid-unsafe policy stays intact.
Legacy callbacks and native Win64 callbacks call these wrappers; native dispatch
now admits atan2f. Both `api-ms-win-crt-math-l1-1-0.dll` and `ucrtbase.dll` are
covered by the existing legacy dispatch and native symbol dispatch.
`OLM_UCRT_FMA` is fixed on first use: absent or `1` selects FMA, `0` non-FMA;
other values panic instead of silently selecting an unintended mode.

**Still host-math / unchanged:** log2f, sinf, cosf and double sin/cos/exp/pow.
Their prior dispatch support/refusals are preserved. No extra math imports
are enabled, and no double computation is routed through a float function.

Build and identity:

- `memory_pressure | tail -5`: **52% free** before release build, above 30%.
- `CARGO_BUILD_JOBS=1 CMAKE_BUILD_PARALLEL_LEVEL=1 AEXCOMPAT_BUILD_REVISION=F30-ucrtmath`; TMPDIR/TMP/TEMP point to ticket scratch; CARGO_TARGET_DIR points to the isolated F30 cache build tree.
- `cargo build --manifest-path /Users/onmk/.cache/olm-emu/src-F30/reference-guest/Cargo.toml --release --offline -j 1 -p aex-guest-worker --bin aex-guest-worker --example f30_import_probe`: exit 0, **2m58s**, one existing dead-code warning.
- Final worker: `~/.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker`, SHA256 `8b51d0456ff55aa2034a0bbb00b822bd2339cbe27247021c289170a78a3fb53b`.
- Parent F29 SHA256 `1c8fb695596e5cf9be21b7c644a3680011ea5b88f4be6e092d93383e3ed4f369`.
- Actual default SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`.
- `python3 tools/emulation/aexcompat_patches/build_F30.py --register`: exit 0; adds only `worker-F30-ucrtmath` to INDEX.json, retaining existing entries. Durable metadata: `~/.cache/olm-emu/F30-ucrtmath-build.json`.
- The committed builder uses the generated locked Cargo.lock. Its preparation/build steps were executed as constituent commands; independent fresh-destination end-to-end invocation has not been run.

Shim validation:

`python3 tools/emulation/aexcompat_patches/validate_F30.py`: exit 0.
For **each** of expf/atan2f/powf, each DLL spelling, and each mode 0/1:
**1,000,000 inputs, 0 mismatches, no first mismatch**. Twelve rows are retained
in `F30-evidence/shim-results.json`. SplitMix64(index XOR 0xf30) produces full
32-bit random operands, including random expf inputs, without domain filtering.
The diagnostic asserts actual DLL dispatch, writes XMM arguments, executes a
NOP at the installed production Unicorn import hook, and reads raw XMM result
bits. A bounded scratch stream feeds the F27c PE loader under Rosetta. Oracle
DLL version 10.0.28000.2705, SHA256
`385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`.
The loader sets/asserts FMA mask and MXCSR 0x1f80. No tolerance is used.
Native-carrier Win64 source routing is included, but native-carrier execution
was not exercised by this arm64 Unicorn diagnostic.

Additional checks and recovered harness failure:

- `python3 tools/emulation/aexcompat_patches/check_mode_F30.py`: exit 0; for each of the three functions, 1,024 raw records with unset mode equal explicit FMA1, and malformed mode exits 101 with no output. Results are in `mode-results.json`.
- An optional `cargo check --manifest-path /Users/onmk/.cache/olm-emu/src-F30/reference-guest/Cargo.toml --target x86_64-apple-darwin --features native-carrier --offline --locked -j 1 -p aex-guest-worker` exits **101**. Running the exact same check with `src-F29` instead of `src-F30` also exits **101**, with the same three errors: missing `CustomUiRegistration`, `register_ui_callback_address`, and `custom_ui_registration` in the native backend. These are pre-existing Classic UI interface gaps outside the ticket. `native-carrier-check.json` preserves both error lists. Memory was 56% free before these checks; their separate check build tree was deleted. No native-carrier executable or numerical qualification is claimed.
- The initial default replay driver exited 1 after ColorKey replay because `run.py`'s scratch-size scan raced a temporary-file deletion in the concurrent F30 run; that replay wrote no report. The driver now gives each variant its own scratch subtree. The missing replay and remaining default measurements were rerun successfully. Completed campaigns were retained; no numerical result was filled in or omitted. This was a harness concurrency issue, not a rejected numerical hypothesis.

Complete remeasurement:

Executed `python3 tools/emulation/aexcompat_patches/replay_F30.py default f29` (initial driver), `.../replay_F30.py f30`, then separate `.../replay_F30.py default` and `.../replay_F30.py f29` invocations after scratch isolation. Each final variant has 10 complete n300 seed-1 campaigns and 11 replay-complete directories, **3,000 generated + 708 saved cases**. The existing harness also records Classic; Smart is the requested primary result. `summarize_F30.py` and `verify_nan_F30.py` both exit 0. All AEX/source-input provenance hashes agree across variants; all candidate raw hashes and oracle execution statuses are unchanged. The compact comparison records **zero findings**. Full before/after hashes, case identities, status transitions, first differences and report bindings are committed in `F30-evidence/measurements.json`.

Numbers below are **exact / mismatch / refusal / uncompared** for Smart. Default and F29 have identical totals for every plugin. Changed-output columns compare default→F29 (SSE NaN) and F29→F30 (UCRT), including reference changes in refused cases.

| Plugin | Default = F29 E/M/R/U | F30 E/M/R/U | NaN changes | UCRT changes | UCRT imports implicated by source/import inventory |
|---|---|---|---:|---:|---|
| colorkeep | 300/0/0/0 | 300/0/0/0 | 0 | 0 | no observed change |
| olmblur | 281/2/17/0 | 277/6/17/0 | 4 | 7 | expf/powf |
| olmcolorkey | 300/0/0/0 | 300/0/0/0 | 0 | 0 | no observed change |
| olmdirectionalblur | 285/1/12/2 | 283/3/12/2 | 2 | 6 | expf/powf |
| olmdistancegradation | 284/1/8/7 | 284/1/8/7 | 0 | 1 | powf |
| olmkirakira | 263/0/37/0 | 263/0/37/0 | 0 | 0 | no observed change |
| olmsmoother | 62/29/95/114 | 62/29/95/114 | 0 | 0 | no observed change |
| olmsmoother2 | 300/0/0/0 | 300/0/0/0 | 0 | 0 | no observed change |
| olmtoondilate | 300/0/0/0 | 300/0/0/0 | 0 | 0 | no observed change |
| radialblur | 148/92/59/1 | 240/0/59/1 | 3 | 106 | expf/atan2f |

ColorKeep, ColorKey, KiraKira, Smoother, Smoother2, and ToonDilate have no changed campaign results. ColorKey has **300/300 Smart exact even on the actual default**; the earlier C20 25-uncompared atan2f observation is not reproduced with this newer parent. Its legacy atan2f dispatch was already present; F30 changes its implementation and adds native-carrier dispatch. No 25-case recovery is invented.

Saved results (`matches_saved` compares the full saved result, not merely whether the Mac is exact):

| Saved directory | Cases | Default saved matches | F29 saved matches | F30 saved matches | NaN / UCRT changed results |
|---|---:|---:|---:|---:|---:|
| olmblur | 39 | 39 | 38 | 37 | 1 / 1 |
| olmcolorkey | 3 | 3 | 3 | 3 | 0 / 0 |
| olmdirectionalblur | 56 | 56 | 56 | 55 | 0 / 1 |
| olmdistancegradation | 145 | 145 | 145 | 145 | 0 / 0 |
| olmkirakira | 8 | 8 | 8 | 8 | 0 / 0 |
| olmkirakira_gate_off_T06 | 62 | 40 | 40 | 40 | 0 / 0 |
| olmsmoother | 29 | 29 | 29 | 29 | 0 / 0 |
| olmsmoother2 | 8 | 8 | 8 | 8 | 0 / 0 |
| olmtoondilate | 300 | 300 | 300 | 300 | 0 / 0 |
| olmtoondilate_T13 | 23 | 23 | 23 | 23 | 0 / 0 |
| radialblur | 35 | 6 | 6 | 35 | 0 / 29 |

There are **32 saved result changes vs default**: one SSE-NaN Blur case plus 31 UCRT changes (Blur 1, DirectionalBlur 1, RadialBlur 29). The 22 KiraKira gate-off saved-result disagreements predate F30 and are identical under all three workers. RadialBlur's 29 prior mismatches become exact and agree with the saved results. DirectionalBlur saved case 84 also becomes exact, so its saved *mismatch* result intentionally no longer matches.

Every exact→non-exact transition is **exact→mismatch under the math-only F29→F30 comparison**, with identical candidate raw output. There are no other route losses, candidate-output changes or oracle execution-status changes. All eight campaign losses and the saved Blur loss are listed here; word strings are the comparator's little-endian bytes, not decimal float values.

| Set | Case | First byte | Different words | Mac word bytes | F30 reference word bytes |
|---|---|---:|---:|---|---|
| olmblur-replay | seed1_case000040_1e01a8a5cbd2.json | 31292 | 1 | `9a3f` | `993f` |
| olmblur-seed1 | 40 | 62668 | 3 | `9a3f` | `993f` |
| olmblur-seed1 | 63 | 148 | 109 | `64fd083f` | `65fd083f` |
| olmblur-seed1 | 71 | 104 | 21 | `266a183f` | `256a183f` |
| olmblur-seed1 | 182 | 52 | 63 | `9621a93e` | `9521a93e` |
| olmblur-seed1 | 258 | 1596 | 2 | `7d7c913b` | `7b7c913b` |
| olmdirectionalblur-seed1 | 141 | 974 | 7 | `f93a` | `fa3a` |
| olmdirectionalblur-seed1 | 216 | 15082 | 1 | `7627` | `7527` |
| olmdirectionalblur-seed1 | 272 | 928 | 1 | `2501733f` | `2601733f` |

Campaign gains are Blur 272, DirectionalBlur 84, and all 92 formerly mismatching RadialBlur cases. Individual expf versus powf contributions in Blur/DirectionalBlur, and expf versus atan2f in RadialBlur, are **not separately ablated**; the unchanged F29 parent and restricted patch isolate the UCRT-import set, while the pinned import table narrows the possible functions per plugin. DistanceGradation campaign 125 changes its oracle under powf but remains a mismatch.

Independent raw NaN recapture (`verify_nan_F30.py`) verifies **10 changed default→F29 cases**, hash-bound to both runs: saved Blur 99; campaign Blur 99/116/290/299, DirectionalBlur 109/299, RadialBlur 17/89/238. Every changed word is NaN before and after; no candidate status changes. First saved Blur difference: word 29, `ffc12346`→`7fc12345`, 9 changed words. DirectionalBlur 109 first word 8 changes `ffc12346`→`ffc00000` (137 words); RadialBlur 17 first word 4 changes `ffc12346`→`7fc12345` (1,425 words). `nan-recaptures.json` retains all changed words and hashes.

inference:
- The import-hook measurements qualify the patched arm64 reference shim on the stated random domain and modes; they are not an exhaustive proof of the ABI or native-carrier execution.
- F29-to-F30 successful-output changes isolate the three UCRT imports. Default-to-F29 successful-output changes isolate SSE NaN propagation. Execution-status changes are findings rather than automatically assigned either numerical cause.
- More Mac mismatches under a corrected oracle expose remaining port work; they do not justify changing saved expected results in this ticket.

changed_files:
- `tools/emulation/aexcompat_patches/F30-ucrtmath.patch`
- `tools/emulation/aexcompat_patches/build_F30.py`
- `tools/emulation/aexcompat_patches/compare_F30.c`
- `tools/emulation/aexcompat_patches/validate_F30.py`
- `tools/emulation/aexcompat_patches/replay_F30.py`
- `tools/emulation/aexcompat_patches/summarize_F30.py`
- `tools/emulation/aexcompat_patches/audit_imports_F30.py`
- `tools/emulation/aexcompat_patches/verify_nan_F30.py`
- `tools/emulation/aexcompat_patches/check_mode_F30.py`
- `tools/emulation/aexcompat_patches/README-F30.md`
- `tools/emulation/aexcompat_patches/F30-evidence/` — source/build manifests, shim results, call-site inventory and measurement evidence.
- `orchestra/reports/F30-oracle-worker-ucrtmath.md`
- Outside git: authorized isolated cache source/binaries/metadata and additive INDEX entry.

verify:

```sh
python3 tools/emulation/aexcompat_patches/validate_F30.py
python3 tools/emulation/aexcompat_patches/check_mode_F30.py
python3 tools/emulation/aexcompat_patches/replay_F30.py default f29 f30
python3 tools/emulation/aexcompat_patches/summarize_F30.py
python3 tools/emulation/aexcompat_patches/verify_nan_F30.py
git diff --check
```

Expected shim: 12 rows, each 1,000,000 calls and zero mismatches. Replay uses
explicit worker paths, `--jobs 1`, seed 1 n300, no shrinking; saved expectations
are never modified. Replay exit 1 can report historical/new expectation drift;
inspect report completion and the retained comparison, not exit status alone.
Reports are rerun by default; `--resume` reuses completed reports. Counts and exact changed case identities are recorded above.

next:
- Separate ticket: review the F30 oracle contract and **explicitly switch the default worker**, then rebaseline only demonstrated saved reference changes. Preserve residual Mac mismatches and historical corpus lineage differences.
- Separate port tickets: replace the corresponding original float import call sites with ucrt_expf/ucrt_powf/ucrt_atan2f in FMA mode. The requested grep inventory is committed as `F30-evidence/mac-call-sites.txt`; additional std::pow/std::atan2 sites are inventoried separately. Double-math calls need their own UCRT work and must not be blindly converted to float.
- Float exp candidates: `core/olmblur_worker_orchestration.cpp:92`, `core/olmblur_worker16_nonlegacy.cpp:113`, `core/olmblur_worker32_nonlegacy.cpp:88`, `core/olmblur_worker16_legacy.cpp:72`, `core/olmblur_worker8_legacy.cpp:54`, `core/dblur_gaussian.h:28`, `mac/OLMBlur/OLMBlur.cpp:1317`, `mac/OLMRadialBlur/OLMRadialBlur.cpp:2224`.
- Float pow candidates: `mac/OLMBlur/OLMBlur.cpp:1336`, `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:1184,1187`, float std::pow in Blur orchestration/nonlegacy decay, KiraKira seed/fade, and ColorKey color conversion also needs matching by original import boundary.
- atan2f boundaries: `mac/OLMColorKey/OLMColorKey.cpp:927` and `mac/OLMRadialBlur/OLMRadialBlur.cpp:193` (the latter currently substitutes double atan2 then casts despite its original atan2f import).
- Float-import substitutes using double evaluation also need review/replacement: `mac/OLMRadialBlur/OLMRadialBlur.cpp:1546` explicitly documents an original expf boundary; `core/olmblur_worker32_legacy.cpp:51` and `core/dblur_gaussian.h:23` similarly cast a float argument to double exp then back. Include these in expf port tickets rather than classifying them by the current C++ overload alone.
- Keep actual double Gaussian paths (`core/kirakira_gaussian.h:52`, DistanceGradation lines 394/423) and genuine double pow/atan2 boundaries for separately grounded double-UCRT work.

Import inventory fact: `PYTHONDONTWRITEBYTECODE=1 "/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/aexcompat_patches/audit_imports_F30.py` reads the exact campaign AEX paths and checks their hashes; it finds expf/powf in Blur and DirectionalBlur, powf in DistanceGradation and KiraKira, atan2f/powf in ColorKey, expf/atan2f in RadialBlur, and none of these three in ColorKeep/Smoother/Smoother2/ToonDilate. `F30-evidence/aex-float-imports.json` retains this inventory. Therefore the grep hits in `mac/OLMSmoother2/OLMSmoother2.cpp:549-551` and `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp:3920-3922` require original-boundary review; the grep alone does **not** justify switching them to ucrt_powf.

Final hygiene: no permissions rejection, push, stash, history rewrite, or stop-condition event occurred. Rust release and native-check build trees were deleted; the isolated worker and probe remain. The scratch comparator is removed after checks. All launched build/emulator processes completed. Source/worker/index hashes and tracked change scope were checked before commit. Native-carrier UI repair remains a separate follow-up; it does not block the arm64 Unicorn reference delivered here.
