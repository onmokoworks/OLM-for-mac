status: done

summary:
- Integrated F43c double pow into F45's Unicorn and native Win64 import paths.
- Switched only audited Mac import call sites; embedded math and captured LUTs remain unchanged.
- Six million shim/callback and 24 million actual Mac-object comparisons pass without mismatches.
- Registered F46 and selected it by default, preserving explicit F45 selection.
- Both seeds n300 for all ten plugins and all 708 saved cases complete: zero exact losses, no rebaseline.

facts:
- Initial HEAD `4fabd3ee40fe564f39441235746b0ccced122fe3`, initially clean, branch `orch/F46-integrate-ucrt-pow`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, F45 and the relevant ledger forbidden-action cells. No MAIN/emulator checkout changes, subagents, gate/ledger changes, push, stash or history rewrite.
- `python3 tools/emulation/aexcompat_patches/build_F46.py` exited 0, memory free 59%, cargo/CMake jobs=1. F45 parent source matched the full retained manifest; existing math sources matched. Rust build finished in 2m44s with the inherited dead-code warning; its regenerable build tree was removed.
- F46 worker SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`; parent F45 `8849565128e4147bb39b145bf392e20da1983c476498ca4448001ea278a38409`. Full source manifest, probe/patch hashes and build command are in `F46-evidence/build-manifest.json`.
- `validate_F46.py` exited 0: each CRT DLL (`api-ms-win-crt-math-l1-1-0.dll`, `ucrtbase.dll`), 1,000,000 full-width random pairs and 1,000,000 plugin-range pairs, FMA mode, zero full-64-bit mismatches; no first mismatch. Actual Unicorn import dispatch/hook and XMM0/XMM1 input/return boundaries are exercised. Pinned Rosetta UCRT 10.0.28000.2705 SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`.
- `validate_native_F46.py` exited 0: manifest-verified production callback body/FFI compiled and invoked through Win64 ABI under Rosetta. 1,000,000 full-width plus 1,000,000 plugin-range pairs, zero mismatches, no first mismatch. This qualifies the isolated callback, not the entire native carrier.
- `check_mode_F46.py` exited 0: 1,024 pairs, unset mode identical to FMA=1; invalid mode rejects without output.
- `build_F46.py --register` exited 0 and appended INDEX under lock; F45 and older entries preserved. Default/explicit-selection assertions passed and paths are retained in `default-selection.json`.
- MAIN's read-only Python ran `audit_imports_F46.py`, exit 0; all ten pinned import tables retained. `audit_boundaries_F46.py` binds original decomp hashes and every named pow call; `boundaries.md` explains Mac correspondence and embedded exclusions.
- `bash tools/fuzz/build_F46.sh` exited 0: OLMBlur, OLMSmoother2 and OLMDistanceGradation Universal x86_64/arm64 builds succeeded. No install, signing or release gate. Binary/log hashes in `mac-builds.json`.
- `validate_mac_F46.py` exited 0: the actual six Xcode pow objects, 1,000,000 full-width plus 1,000,000 signed-exponent-range pairs per object in both modes. 12 million input rows, 24 million full-bit comparisons, zero mismatches, no first mismatch. Object identities/results in `mac-object-results.json`.

- `measure_F46.py --before` and `measure_F46.py` both exited 0: each completed 6,000 generated cases and 708 saved cases with jobs=1. Both KiraKira T06 replay subprocesses exited 1 on the same 23 historical saved-result differences; all other measurement subprocesses exited 0. All 708 replay Smart routes are exact in both variants; saved-result matches remain 685/708.
- `summarize_F46.py` exited 0: 20 complete paired campaigns, 11 complete paired corpora, zero individual exact losses across Classic and Smart, two oracle status changes, and 28 diagnostic-text differences. No successful-pair reference output hash changed. The only candidate comparison change is RadialBlur seed1 case62 becoming comparable/exact. Raw reports and provenance are hash-bound in `measurements.json`.
- `rebaseline_F46.py` audit exited 0: zero qualified updates, zero unqualified saved-reference changes. No corpus expectation was modified.
- `recheck_F46.py` exited 1 (`Unresolved status drift`), preserved rather than suppressed. RadialBlur seed1 case62 originally hit the F45 outer 10-second limit and succeeded with F46; both recaptures succeeded (8.36s / 8.35s), SHA256 `d3d08c4296f99ebc15bfa4e2cb2d9c2dc9890e68802bbcc177a5187d08027042`, matching original F46. Case280 originally hit the F45 outer limit and succeeded with F46; F45 recapture succeeded in 8.89s, SHA256 `5a19de28aece7b23b644e5f2533da7f662677e3d6a837b9a96d88a53726487f8`, matching original F46. Its F46 recapture stopped at 20.02s, RIP `0x180002860`; inherited `x64.rs:299` sets the internal 20-second limit. Case280 is refused by the Mac in both campaigns. No second recapture loop was attempted. Full diagnostics and original results remain in `status-rechecks.json`.
- Fresh seed46 exposes three unchanged ColorKey PF32 Smart mismatches (no fix attempted outside this ticket): case237 first byte144/word36, 12 differing bytes / 3 words, Mac little-endian `00000000` vs reference `4523c17f`; case246 first byte467/word116, 5 differing bytes / 5 words, Mac `0000c07f` vs reference `0000c0ff`; case275 first byte579/word144, 3 differing bytes / 3 words, same signed-NaN word difference. Complete parameters and both output hashes are retained in `measurements.json` residuals.

Paired Smart results, **exact / mismatch / refusal / uncompared / budget**:

| Plugin | Seed1 F45 | Seed1 F46 | Seed46 F45 | Seed46 F46 |
|---|---|---|---|---|
| colorkeep | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 |
| olmblur | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 |
| olmcolorkey | 300/0/0/0/0 | 300/0/0/0/0 | 297/3/0/0/0 | 297/3/0/0/0 |
| olmdirectionalblur | 290/0/8/2/0 | 290/0/8/2/0 | 285/0/14/1/0 | 285/0/14/1/0 |
| olmdistancegradation | 290/0/3/7/0 | 290/0/3/7/0 | 280/0/13/6/1 | 280/0/13/6/1 |
| olmkirakira | 287/0/13/0/0 | 287/0/13/0/0 | 286/0/14/0/0 | 286/0/14/0/0 |
| olmsmoother | 205/0/95/0/0 | 205/0/95/0/0 | 190/0/110/0/0 | 190/0/110/0/0 |
| olmsmoother2 | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 |
| olmtoondilate | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 | 300/0/0/0/0 |
| radialblur | 257/0/40/3/0 | 258/0/40/2/0 | 275/0/25/0/0 | 275/0/25/0/0 |

Smoother v1 Classic equals its Smart counts for both seeds and variants. All other Classic routes were also checked individually for exact preservation.

| Corpus | Cases | Smart exact F45 / F46 | Saved matches F45 / F46 |
|---|---:|---:|---:|
| olmblur | 39 | 39 / 39 | 39 / 39 |
| olmcolorkey | 3 | 3 / 3 | 3 / 3 |
| olmdirectionalblur | 56 | 56 / 56 | 56 / 56 |
| olmdistancegradation | 145 | 145 / 145 | 145 / 145 |
| olmkirakira | 8 | 8 / 8 | 8 / 8 |
| olmkirakira_gate_off_T06 | 62 | 62 / 62 | 39 / 39 |
| olmsmoother | 29 | 29 / 29 | 29 / 29 |
| olmsmoother2 | 8 | 8 / 8 | 8 / 8 |
| olmtoondilate | 300 | 300 / 300 | 300 / 300 |
| olmtoondilate_T13 | 23 | 23 / 23 | 23 / 23 |
| radialblur | 35 | 35 / 35 | 35 / 35 |

- Initial staged `git diff --cached --check` flagged the valid unified patch's blank context line as trailing whitespace. Commit `ae04a8de` retains that original build recipe. Reformatted the patch with zero context, applied it to a fresh five-file F45 snapshot, and verified every result against the built F46 source manifest: all five hashes match. `patch-format-check.json` binds both patch hashes; no worker or arithmetic changed.
- Final `git diff --check`, Python syntax and all 40 campaign worker-hash assertions pass. All started commands exited. Regenerable Rust/Xcode/native/fuzz build products and task-created SDK links were removed; logs/raw reports remain. Cleanup snapshot: scratch 95123260 bytes, below 5 GiB. No permission rejection or numerical-hypothesis stop occurred.

inference:
- The audit supports imported-pow replacement only; it does not justify replacing embedded softdouble/IPP algorithms or regenerating captured LUTs.
- These finite tests qualify the recorded math/ABI boundaries, not all inputs or native AE equivalence.
- Successful old/new outputs agree for both timing-drift cases. The case280 recapture is not a successful same-run pair; its matching successful outputs are from separate runs. This supports execution-time variability, not a demonstrated pow regression, and does not promise completion within either timeout.

changed_files:
- Three core OLMBlur worker CPPs, OLMBlur/DistanceGradation production CPP, both Smoother2 CPPs, and their three Xcode projects.
- `tools/fuzz/run.py` and F46 build/before/measure/summarize/rebaseline/recheck helpers.
- F46 worker patch, build/validation/mode/import/static-audit tools and README.
- `orchestra/reports/F46-evidence/*` and this report.

verify:
Run serially from the worktree:
```sh
s="$PWD/orchestra/state/F46-integrate-ucrt-pow"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1 OLM_UCRT_FMA=1
python3 tools/emulation/aexcompat_patches/validate_F46.py > "$s/validate.log" 2>&1
python3 tools/emulation/aexcompat_patches/check_mode_F46.py > "$s/mode-driver.log" 2>&1
python3 tools/emulation/aexcompat_patches/validate_native_F46.py > "$s/native-driver.log" 2>&1
bash tools/fuzz/build_F46.sh > "$s/mac-build.log" 2>&1
python3 tools/emulation/aexcompat_patches/validate_mac_F46.py > "$s/mac-object-driver.log" 2>&1
python3 tools/fuzz/measure_F46.py --before > "$s/measure-before.log" 2>&1
python3 tools/fuzz/measure_F46.py > "$s/measure-after.log" 2>&1
python3 tools/fuzz/summarize_F46.py > "$s/summary.log" 2>&1
python3 tools/fuzz/rebaseline_F46.py > "$s/rebaseline-audit.log" 2>&1
python3 tools/emulation/aexcompat_patches/audit_boundaries_F46.py > "$s/boundary-audit.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/aexcompat_patches/audit_imports_F46.py > "$s/import-audit.log" 2>&1
git diff --check
```
Expected math/build results: six million shim/callback and 24 million actual Mac-object comparisons, zero mismatches; three Universal builds and mode assertions pass. Regression expectations are the tables above: zero exact losses, 685/708 saved matches in both variants and zero rebaselines. The known T06 replay exit 1 is retained by the driver. Timing statuses may vary; inspect raw reports. Optional independent worker rebuild uses a fresh `--cache-root` as described in README-F46; never replace an existing registered worker. Remove regenerable scratch build outputs after verification.

Optional timing diagnostic: `python3 tools/fuzz/recheck_F46.py > "$s/recheck.log" 2>&1`. The retained run exits 1 due to case280's internal-limit stop; see the matching successful-output evidence above rather than treating this as a numerical mismatch.

next:
- Orchestrator reviews and merges; no push or merge performed.
- Separate numerical follow-up: ColorKey seed46 PF32 cases237/246/275 (NaN payload/sign behavior), unchanged across F45/F46.
- Separate optional follow-up: RadialBlur execution-time variability and the existing KiraKira T06 saved-result drift. Neither warrants a pow rebaseline.
