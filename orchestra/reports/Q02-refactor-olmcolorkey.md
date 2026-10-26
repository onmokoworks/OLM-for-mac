status: blocked
summary:
- Retained the single-translation-unit split, keeping ParamsSetup, UpdateParameterUI and dispatch in main.
- Split G1 passed 12,012 comparisons; the subsequent cleanup run had one admission-status difference and was reverted.
- The identical base binary changed its response to an identical case across those runs; the cause is unresolved. A base/base identity run then passed 3,003 comparisons.
- G2 and G3 match baseline; UI oracle and Universal Xcode build pass. Full G5 is incomplete.
- This is NOT a completed Q02 refactor: exhaustive constant naming and the size cap remain unfinished after rollback.

facts:
- Start branch: `orch/Q02-refactor-olmcolorkey`; clean working tree. Start HEAD and `git merge-base HEAD codex/public-beta-roi`: `e55bc78a463786e79261b8c251c41e361b218c6c` (BASE below).
- `git diff --exit-code 12622f6881f39150eda238812a32a3c01b2e7d30 BASE -- mac/OLMColorKey` returned 0. Thus the previous report's G3 baseline source is identical to this resume's baseline.
- Read REFACTOR_SPEC, AGENT_GUIDE, GOTCHAS, compatibility plan and targeted ColorKey ledger rows. No float-v1 blocker is asserted: depth-32 pixels provide the specified float coverage.
- Commits: `b5e4c865` split; `6eee3860` numerical names/declaration cleanup; `362e1c86` forward revert of that cleanup; `c4c8e7c4` restores only the test reader adjustments. No history rewriting.
- Final production files are byte-identical to `b5e4c865`: `git diff --exit-code b5e4c865 -- mac/OLMColorKey` returned 0.

G1:
- Split invocation: `python3 tools/refactor/native_diff.py --plugin olmcolorkey --base BASE --head WORKTREE --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch orchestra/state/Q02-refactor-olmcolorkey/G1-split`.
- Exit 0. Each arm64/x86_64 × reference/fast pair completed 3,003 comparisons: total 12,012 exact, 0 differences, 0 refusals, 0 new refusals, 0 execution errors. No first mismatch.
- Coverage: 12,000 small + 12 UHD comparisons; 4,004 per depth. Geometry default 4,020, realistic-v1 3,996, realistic-v2 3,996. Default sizes 6,008; odd-even-v1 6,004. Downsample includes 1/1, 1/2, 1/3, 1/4, 1/8 and asymmetric 1/2 × 1/3. Each build/architecture's PF32 profiles: SDR 657, nonfinite 42, HDR 137, signed 165.
- Summary SHA256: `ef026878c402eb5aba9ecea92da9a17b9160e2170c385fe25c967486143351a9`.
- The same command at `6eee3860`, scratch `G1-final`, exited 1: 12,011 exact / 12,012 comparisons, 1 difference, 0 refusals classified equal, 0 new refusals, 0 execution errors. Summary SHA256: `391a3b141d4c42b0c539137410597ad8863bc1cc7999c381867d421e245879a5`.
- First difference: arm64/reference, seed 909, generator index 4935, sequence index 1932, PF8 SDR; input geometry 3×1, full geometry 9×4, downsample 1/4 on both axes, request [1,0,3,1], padding 1 byte. Base returned error 516, tag `PrepareSmartRenderWorld:smart-public-admission`, no output; candidate returned error 0, rect [1,0,3,1], eight zero bytes. Tool first_byte_difference=0 denotes empty-versus-nonempty output here, not an observed changed pixel value.
- Input SHA256: `352bee204602201794b673362fc72b034b5ca3683aa58624425b78908a817866`. Canonical case JSON SHA256 (`json.dumps(case, sort_keys=True).encode()`): `2224c1eccfb6bf4c2ce9e88a62212581d5445d4bfa8b3f14dad6c68791268162` in both runs.
- Both runs' arm64/reference BASE executable SHA256 is `a60d18f6d9e70e13d54242d4c24a59a8ce9458da714383738bf53d3e3282142c`. In the split run, that same base binary returned success for this case, with output SHA256 `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc` (matching both candidates). Thus the baseline response itself varied across executions.
- Reverted the entire cleanup step rather than accepting the difference. The later base/base diagnostic used `--head BASE --arch arm64 --build reference`, otherwise the same 3,000 cases/seed. Exit 0: 3,003 exact, 0 differences/refusals/errors. Summary SHA256: `696e6472eea50ff8a374975928de6345bffdcfb0b51424e96e1c033b296b154b`. This one successful identity run does not erase the observed inconsistent baseline response.
- Progress commentary initially called completed architecture runs exact based only on processed-line counts; that was incorrect for the cleanup run. The final summary above is authoritative, and the error was explicitly corrected in chat.

G2:
- Replayed every JSON under `tests/fuzz_corpus/olmcolorkey` with `tools/fuzz/run.py --plugin olmcolorkey --replay DIR --jobs 1`, using MAIN's absolute emulation Python and recorded worker/timeout bindings.
- Both archived BASE and split source: root 9, C01-pf32-nan 4, N02-nightly-20261025 3, P02i-realistic 8, P05c-lab-key-cache 24, T15b-odd-even-realistic 3. All six runs on each source exited 0 and reported `replay_matches_saved=true`: 51/51 each, including saved failures.
- T15b requires `--max-size 1920 --size-max-height 1080 --size-sampler odd-even-v1 --geometry realistic`. Initial omission produced setup_error `Replay requires the corpus --max-size`; corrected rerun completed all three. No worker replacement or recorded-result edit.

G3:
- MAIN venv Python ran `tools/fuzz/run.py --plugin olmcolorkey --main MAIN --geometry realistic --seed 909 --n 100 --jobs 1 --shrink-attempts 0` with scratch/report/corpus explicitly in this ticket.
- Completed 100: Smart 87 exact / 13 uncompared due to oracle rejection; Classic 86 mismatches / 14 refusals. Same as the prior source-identical baseline in `6fc44fc1`.
- First Classic mismatch index 1: first byte/word 0, expected word `00000000`, actual `aacd3e40`, 851 differing bytes / 236 words of 992 bytes. No behavior fix attempted.
- Report SHA256: `6e8810af9573fa407b48c5f5e8e635070f2bec552b20813bee43ef1dcdb40382`.

G4:
- `python3 tools/perf/ref_vs_fast.py --plugin olmcolorkey --jobs 1 --scratch orchestra/state/Q02-refactor-olmcolorkey/G4` completed 675 exact comparisons, 0 refusals, 0 mismatches (200 small, 20 HD, 5 UHD × caps 1/2/8). This run covered an intermediate cleanup snapshot, not the final retained split.
- Retained-split rerun with scratch `G4-retained` exited 0: 675 exact, 0 refusals, 0 mismatches, using the same default counts and caps. Summary SHA256: `67086b7e52a9f3af9457db9a029e2ecf3bf59feb30205293d4f27f75cc3bf4c7`.

G5:
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMColorKey --scratch orchestra/state/Q02-refactor-olmcolorkey/G5-xcode` exited 0. Actual project Release build, Universal `x86_64 arm64`, `-jobs 1`; no project/build entrypoint source changes.
- `python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/Q02-refactor-olmcolorkey/G5-ui-oracle` exited 0. ColorKey: 36 updates / 72 checks including reload / 0 mismatches. ParamsSetup, UpdateParameterUI and EffectMain dispatch remain in main.
- Direct parameter-UI test: all 3 functions pass. Neither MAIN emulation venv nor system Python has pytest; attempted `-m pytest` invocations failed with `No module named pytest`, so applicable static functions/unittest classes were executed directly.
- Legacy parameter-order test fails at its pre-existing ParamsSetup regex on both BASE and current source. Legacy classic-dispatch test fails on unchanged OLMBlur before reaching ColorKey, both on BASE and current. Legacy typed tinyworld ColorKey static test fails the pre-existing `mean <= threshold` literal assertion on both BASE and current. Assertions were not changed; two readers were adjusted only to read the moved fragments.
- Unmodified `scripts/run_olm_release_gate_v2.py --state orchestra/state/Q02-refactor-olmcolorkey/G5-release` exits 2: it restricts state to `R09-release-gate-v2`. Its hard-coded OLM_TEST_JOBS is also 2. Planned in-memory resource-only overrides and package staging were queued but canceled BEFORE execution after the G1 difference. No release-gate file was modified.
- Full seven-stage release gate and `scripts/package_mac_plugins.sh` did NOT run. G5 is incomplete, not passed.

G6:
- All eight native differential compiler logs for the split contain 0 `warning:` occurrences (both revisions, architectures and modes).
- Retained Universal Xcode log contains 342 warning occurrences. BASE Universal Xcode log contains 344 (0 added / 2 removed warning messages); the two removed diagnostics are unused-function warnings for LabKeyReference. G6 passes for the retained split. The initial baseline-build attempt lacked archived `scripts/setup_ae_sdk_links.sh`; archiving that unchanged baseline script and rerunning succeeded.

inference:
- The observed inconsistent response of the identical base binary prevents attributing this refusal difference to the renamed constants. The source/harness/runtime cause is unproven; a successful retry is not a resolution or permission to ignore it.
- The split has one complete exact differential run, not proof of universal equivalence. Do not merge this as a completed Q02 ticket.
- Suspicious but untouched: narrow captured blur planes and case_0009 shell weights coexist with general recovered curves; capture claim files survive some I/O failures; ClassicWorldsMatch is production-unused but is directly exercised by a retained hostless test.
- Static reachability inference for follow-up: IsBoundedLab76NativeTuple and IsBoundedToggleInfo require both Thin and Blur zero, whereas IsPublicAdmission already returns from its pixel_local branch for that condition. The test-facing helpers and the old tail admission checks were left intact; removal was not validated here.

changed_files:
- mac/OLMColorKey/OLMColorKey.cpp
- mac/OLMColorKey/{Diagnostics,Parameters,Distance,ColorMath,AdmissionFixtures,BlurMath,Pixels,Kernel,Render}.inc
- tests/test_colorkey_toondilate_mac_typed_tinyworld_matrix_20260728.py (read included source text)
- tests/test_olmblur_colorkey_classic_render_bitdepth_dispatch_20260716.py (ColorKey path to Render.inc)
- orchestra/reports/Q02-refactor-olmcolorkey.md

refactor_accounting:
- Final retained operation is a source split only. No named constants, numerical variable renames or dead-code removal remain after reverting `6eee3860`.
- Reverted trial examples: kDistanceCap/kFirstNonseed, kSquaredDistanceInfinity/kEnvelopeInfinity, five Lab constants, kByteToUnit, kNativePi/kNativeHalfPi/kNativeHalfPiDouble, and local kPi. Trial removed unused is_16bpc methods, redundant includes and ExactColor forward declarations. All of this was reverted as one failing step.
- No generated file, algorithm, arithmetic type/order, OLM_REFERENCE_BUILD branch or OLM_PARALLEL_MAX policy is intentionally changed in the retained split.
- Counts strip C/C++ block and line comments, then count nonblank lines; source extensions cpp/h/inc/r. Projects/plists unchanged.

| File under mac/OLMColorKey | Physical before / after | Code before / after |
|---|---:|---:|
| AdmissionFixtures.inc | 0 / 409 | 0 / 374 |
| BlurMath.inc | 0 / 260 | 0 / 215 |
| ColorMath.inc | 0 / 129 | 0 / 104 |
| Diagnostics.inc | 0 / 169 | 0 / 157 |
| Distance.inc | 0 / 213 | 0 / 188 |
| Kernel.inc | 0 / 647 | 0 / 575 |
| OLMColorKey.cpp | 2975 / 333 | 2668 / 287 |
| OLMColorKey.h | 161 / 161 | 146 / 146 |
| OLMColorKeyPiPL.r | 33 / 33 | 31 / 31 |
| OLMColorKey_Strings.cpp | 44 / 44 | 41 / 41 |
| OLMColorKey_Strings.h | 35 / 35 | 34 / 34 |
| Parameters.inc | 0 / 234 | 0 / 224 |
| Pixels.inc | 0 / 176 | 0 / 161 |
| Render.inc | 0 / 423 | 0 / 392 |
| Total | 3248 / 3266 | 2920 / 2929 |

- Largest retained file: Kernel.inc, 647 lines. The nine include directives increase code lines by 9: the spec's size cap is NOT met. Exhaustive constant naming is also incomplete.

verify:
Run from this worktree. Commands below use existing shared tools, not new probe scripts. MAIN is read-only.

```sh
BASE=e55bc78a463786e79261b8c251c41e361b218c6c
STATE="$PWD/orchestra/state/Q02-refactor-olmcolorkey/recheck"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
PY="$MAIN/tools/emulation/.venv/bin/python3"
mkdir -p "$STATE"
export TMPDIR="$STATE" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 tools/refactor/native_diff.py --plugin olmcolorkey --base "$BASE" --head WORKTREE --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch "$STATE/G1" > "$STATE/G1.log" 2>&1
python3 tools/refactor/native_diff.py --plugin olmcolorkey --base "$BASE" --head "$BASE" --cases 3000 --seed 909 --arch arm64 --build reference --jobs 1 --scratch "$STATE/identity" > "$STATE/identity.log" 2>&1
```

Observed retained split: 12,012 exact. Observed identity: 3,003 exact. The intermittent base refusal described above remains an open reproducibility risk; a rerun returning 0 does not resolve it. To reproduce the reverted trial source, use `--head 6eee3860` with a separate scratch directory and the same 3,000-case parameters; it is not guaranteed to reproduce the intermittent rejection.

```sh
for dir in tests/fuzz_corpus/olmcolorkey tests/fuzz_corpus/olmcolorkey/C01-pf32-nan tests/fuzz_corpus/olmcolorkey/N02-nightly-20261025 tests/fuzz_corpus/olmcolorkey/P02i-realistic tests/fuzz_corpus/olmcolorkey/P05c-lab-key-cache; do
  name=$(basename "$dir")
  "$PY" tools/fuzz/run.py --plugin olmcolorkey --main "$MAIN" --replay "$dir" --jobs 1 --scratch "$STATE/G2-$name" --report "$STATE/G2-$name.json" > "$STATE/G2-$name.log" 2>&1
done
"$PY" tools/fuzz/run.py --plugin olmcolorkey --main "$MAIN" --replay tests/fuzz_corpus/olmcolorkey/T15b-odd-even-realistic --max-size 1920 --size-max-height 1080 --size-sampler odd-even-v1 --geometry realistic --jobs 1 --scratch "$STATE/G2-T15b" --report "$STATE/G2-T15b.json" > "$STATE/G2-T15b.log" 2>&1
"$PY" tools/fuzz/run.py --plugin olmcolorkey --main "$MAIN" --geometry realistic --seed 909 --n 100 --jobs 1 --shrink-attempts 0 --scratch "$STATE/G3" --report "$STATE/G3.json" --corpus "$STATE/G3-corpus" > "$STATE/G3.log" 2>&1
python3 tools/perf/ref_vs_fast.py --plugin olmcolorkey --jobs 1 --scratch "$STATE/G4" > "$STATE/G4.log" 2>&1
python3 tests/ui_oracle/compare_mac.py --scratch "$STATE/UI" > "$STATE/UI.log" 2>&1
python3 tests/test_olmcolorkey_parameter_ui_parity_20260806.py
python3 tools/fuzz/build_F47_bundles.py --plugins OLMColorKey --scratch "$STATE/xcode" > "$STATE/xcode.log" 2>&1
```

Expected measured results: G2 51 saved-result matches; G3 Smart 87 exact/13 uncompared and Classic 86 mismatches/14 refusals; G4 675 comparisons; UI ColorKey 72 checks/0 mismatches; Universal build succeeds. Do not reinterpret the baseline Classic failures as new failures or all-exact oracle coverage.

For BASE G2/G6, materialize tracked source with `git archive "$BASE" mac core cli tools ucrtmath scripts/setup_ae_sdk_links.sh reports/radialblur_public_getters_aligned_20261001.json` into a new directory under STATE. Run that checkout's tools with explicit `--main "$MAIN"`; put its fuzz scratch/report under its own `orchestra/state/` (the fuzz CLI requires that). Replay absolute paths to this worktree's six corpus directories with the same flags. Both sources measured 51/51 saved matches. Run its `tools/fuzz/build_F47_bundles.py --plugins OLMColorKey --scratch "$STATE/xcode-base"` to compare warning counts.

next:
- Investigate the identical-base binary's intermittent smart-public-admission rejection at the recorded case before treating repeated G1 greens as sufficient.
- Resume Q02 constant naming/dead-code review and meet the size cap; current split is only an intermediate step.
- Resolve the release runner's resource configuration within ticket constraints, then run package and all seven release stages. Repair stale source-test contracts separately without weakening numerical assertions.
- No push, MAIN edits, emulator rebuilds, release-gate edits or forbidden-list edits were performed. All started runs finished or were canceled before their queued work began. Removed archived source/build trees, generated corpus, candidate bundles, compiler caches and task-created SDK symlinks; retained logs/results occupy approximately 282 MiB, below the 5 GiB cap. No background process started by this worker remains.
