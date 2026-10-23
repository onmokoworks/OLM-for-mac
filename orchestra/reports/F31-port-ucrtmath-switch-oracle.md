status: blocked

summary:
- Integrated independent UCRT float math (explicit FMA mode) into six Universal Mac builds and public fuzz/regression builds; F30 is the generation default, prior workers remain selectable.
- Final paired measurements: each variant ran seed 1 + fresh seed 31, n300 for all ten plugins, and all 708 saved cases. Zero Classic or Smart exact→non-exact transitions.
- Smart gains: Blur +5/+6, DirectionalBlur +3/+3, KiraKira +0/+3 (seed 1/31). Only three hash-proven reference migrations were rebaselined.
- Strict acceptance remains blocked: 69 admitted Smart mismatches across the two final seeds (six in touched plugins, 63 in untouched Smoother); none were hidden by rebaseline/refusal.
- Existing test failure at historical DirectionalBlur fixture 137 is a stale reference: independently rebuilt Mac and F30 AEX both produce e27c16ee…d3c37. Historical test expectations remain unchanged.

facts:

Read AGENT_GUIDE.md, emulator GOTCHAS, compatibility plan, relevant forbidden-action matrix rows, F30 report/evidence, and completed C28 reports. Branch is `orch/F31-port-ucrtmath-switch-oracle`. MAIN, original emulator sources/workers, release gates and ledger were not modified. No push, stash, history rewrite, plugin installation, permissions rejection, or numerical stopping-rule event occurred.

Implementation:
- Original FLOAT32 exp/pow/atan2 boundaries now call `ucrt_expf`, `ucrt_powf`, `ucrt_atan2f` with `UCRT_FMA`. Explicit double-exp/atan2 substitutes at documented float boundaries were replaced as requested.
- Additional DirectionalBlur powf boundaries were verified in disassembly at 0x1800037cf / 0x1800039b6 / 0x180003a5b. The first exponent constant at RVA 0xb218 is `00000040` (2.0f); the other calls pass FLOAT32 quotient/exponent. This covers noise interpolation and the rowdriver's former double-pow substitutes.
- `F31-evidence/call-sites.txt` and `boundaries.md` list replacements and excluded double/unconfirmed sites. No Smoother/Smoother2/ToonDilate/ColorKeep plugin source changed.
- Six Xcode projects compile the four independent C sources using `-O2 -ffp-contract=off -fno-fast-math`. Plugins only include the library header; no reverse dependency was added. The library build accepts an optional architecture; the reusable C++ harness wrapper links per-architecture archives, including Universal output.
- Public adapters link the library; RadialBlur's separate probe builder also links it and explicitly receives the tested source path. The DirectionalBlur CLI build uses the same wrapper. The regression runner supplies that wrapper to existing direct compiler calls.
- Generation selects `~/.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker`; SHA256 `8b51d0456ff55aa2034a0bbb00b822bd2339cbe27247021c289170a78a3fb53b`. `--worker` and `OLM_AEX_WORKER` still select the prior worker. Saved replay's existing hash-bound worker policy is preserved; every F31 replay explicitly selects F30. Unset reference FMA mode is 1; all measurements explicitly set `OLM_UCRT_FMA=1`.

Measurement commands actually run (output redirected to ticket-local logs):

```sh
python3 tools/fuzz/measure_F31.py
python3 tools/fuzz/measure_F31.py --before
python3 tools/fuzz/measure_F31.py --plugin olmdirectionalblur --campaigns-only
python3 tools/fuzz/summarize_F31.py
```

All use jobs 1, n300, seeds 1/31, no shrinking, explicit F30, and separate scratch subtrees. At most two build/emulator workloads ran concurrently. `before_F31.py` pins the original parent commit, extracts only core/Mac source into scratch, and keeps SDK/AEX assets read-only. All final 20 campaigns + 11 corpus reports completed for each variant. The last DirectionalBlur campaign rerun follows the additional verified powf replacements; its initial 600-case run is retained in scratch and is not counted as the final result. The 708-case final corpus replay already used those replacements.

The committed comparison binds report hashes, source/worker provenance, every changed result, input equality, residuals and individual Classic/Smart exact preservation. There are **zero exact losses**, **zero successful-reference byte changes**, and one oracle execution change: RadialBlur seed1 case62 was `ok` before and hit the 10-second budget after; the candidate refused both times. Thirty-seven diagnostic strings differ (including that timeout); their hashes are retained separately from numerical comparisons. These are not assigned a UCRT numerical cause. F30 report totals and this worktree's parent differ for DistanceGradation and KiraKira due to preceding work, including C28; those gains are not attributed to F31.

Smart E/M/R/U (U includes uncompared or uncompleted candidate comparisons):

| Plugin | F30 report seed1 | Parent seed1 | F31 seed1 | Parent seed31 | F31 seed31 |
|---|---|---|---|---|---|
| colorkeep | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmblur | 277/6/17/0 | 277/6/17/0 | 282/1/17/0 | 269/8/23/0 | 275/2/23/0 |
| olmcolorkey | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmdirectionalblur | 283/3/12/2 | 283/3/12/2 | 286/0/12/2 | 278/5/15/2 | 281/2/15/2 |
| olmdistancegradation | 284/1/8/7 | 287/0/6/7 | 287/0/6/7 | 281/1/12/6 | 281/1/12/6 |
| olmkirakira | 263/0/37/0 | 269/0/31/0 | 269/0/31/0 | 263/3/34/0 | 266/0/34/0 |
| olmsmoother | 62/29/95/114 | 62/29/95/114 | 62/29/95/114 | 65/34/107/94 | 65/34/107/94 |
| olmsmoother2 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmtoondilate | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| radialblur | 240/0/59/1 | 240/0/59/1 | 240/0/59/1 | 247/0/51/2 | 247/0/51/2 |

DistanceGradation seed31 U=6 comprises four `uncompared` and two candidate `budget` outcomes, identical before/after; the underlying statuses are retained rather than relabeled in evidence. No claim of full-domain or native AE exactness is made.

Residual first mismatches in touched plugins (word strings are little-endian byte strings):

| Plugin / seed / case | First byte | Different words | Mac | F30 AEX |
|---|---:|---:|---|---|
| Blur / 1 / 99 | 219 | 10 | 0000c07f | 0000c0ff |
| Blur / 31 / 214 | 375 | 11 | 0000c07f | 0000c0ff |
| Blur / 31 / 271 | 1243 | 14 | 0000c07f | 0000c0ff |
| DirectionalBlur / 31 / 187 | 0 | 49 | b86d4f3e | b16d4f3e |
| DirectionalBlur / 31 / 295 | 16 | 17 | 282cd03d | 242cd03d |
| DistanceGradation / 31 / 253 | 222008 | 5950 | 5806 | 5706 |

These six cases were already mismatches under the pinned parent/F30 comparison. The three Blur first differences are NaN sign differences; no general NaN propagation fix or unsupported admission change was attempted in this math-import ticket. All 69 Smart residual rows, including untouched Smoother, are in `measurements.json`.

Corpus replay before rebaseline:

| Corpus | Cases | Saved matches under final F31/F30 |
|---|---:|---:|
| olmblur | 39 | 37 |
| olmcolorkey | 3 | 3 |
| olmdirectionalblur | 56 | 55 |
| olmdistancegradation | 145 | 145 |
| olmkirakira | 8 | 8 |
| olmkirakira_gate_off_T06 | 62 | 39 |
| olmsmoother | 29 | 29 |
| olmsmoother2 | 8 | 8 |
| olmtoondilate | 300 | 300 |
| olmtoondilate_T13 | 23 | 23 |
| radialblur | 35 | 35 |

`python3 tools/fuzz/rebaseline_F31.py --apply` exited 0 and invoked the existing `tools/fuzz/rebaseline_corpus.py` for exactly:
1. `olmblur/seed1_case000040_1e01a8a5cbd2.json` — F30 UCRT reference change; candidate is now exact.
2. `olmblur/seed1_case000099_9b13c27c2f2e.json` — F29 SSE NaN reference change; candidate remains a mismatch, with the new mismatch recorded honestly.
3. `olmdirectionalblur/seed1_case000084_9e50cab1bcf7.json` — F30 UCRT reference change; candidate is exact.

Every old/new changed reference hash matches F30's committed default→F30 evidence; `rebaseline.json` retains the hashes and narrower NaN/UCRT attribution. Case inputs, parameters and reduction history compare identical to git HEAD. Three fresh individual `run.py --replay <case> --worker <F30> --jobs 1` executions subsequently exited 0, each 1/1 saved match. Thus Blur becomes 39/39 and DirectionalBlur 56/56 saved matches. RadialBlur's 29 default→F30 reference changes already agree with its saved expectations; no rewrite is needed. KiraKira diagnostic T06's 23 disagreements (22 historical plus the prior C28 case214 improvement) occur equally in this parent and final replay and were not rebaselined. No unexplained reference migration was eligible.

Builds/tests:
- `tools/fuzz/build_F31.sh`: exit 0, all six Universal arm64+x86_64 builds. Final executable SHA256/architectures are in `build-identities.json`. No install/signing/release gate was performed.
- `tools/ucrt_cxx.py -I "$PWD" -arch arm64 -arch x86_64 <scratch>/math-smoke.cpp -o <scratch>/math-smoke`: exit 0; the executable checks UCRT expf(0)=1, exits 0, and `lipo -archs` reports both architectures.
- `refs/scripts/build_olmdirectionalblur_cli.sh <scratch>/dblur-cli`: exit 0.
- Initial broad historical pytest collection: 28 errors from unavailable Python dependencies and absent historical handoffs/assets; no blanket historical-suite PASS is claimed. A scratch venv installed pytest, pillow, numpy, unicorn and pefile; SDK and required original AEX/PNG paths use absolute read-only symlinks.
- First selected current suite: 20 passed, three missing-AEX errors. Expanded selected suite via `test_F31.sh`: **39 passed, 4 failed, 2 skipped, 37 subtests passed**. Three failures were missing reference PNGs; after adding the MAIN read-only asset link, `pytest -q tests/test_olmdirectionalblur_remaining6_ucrt_powf_census_20260814.py` reports **3 passed**. Previously passing tests include compiled Blur/Kira/Radial sanitizer paths, ColorKey and DistanceGradation current tests, and fuzz framework/adapter/migration unit tests.
- The remaining existing failure is `test_directionalblur_general_features_20261001.py`, first fixture index137 (37×29 PF32 limits/front). Its historical reference is `f05d4c86389d67091ca888df535c6c58cc6311940932f0f8debb5a292f3e8029`; the new Mac hash is `e27c16ee00128b50b629b8b5243eaddd3942b5665781f33a4259bcbd607d3c37`.
- `check_fixture_F31.py` rebuilds that production harness and directly runs the original AEX under F30 with the identical input hash and parameter payload: **Mac equals F30**, hash `e27c16ee…d3c37`. `fixture137.json` records both references and input/worker/AEX hashes. The first diagnostic rerun encountered the worker's exclusive sidecar-file creation rule; the tool now removes only its own generated output/world files before replay. Subsequent independent recapture/build succeeds. No tolerance or output patch was used, and the historical fixture was not rewritten.
- F30 default and explicit old-worker environment override were asserted successfully. `git diff --check` passes.

inference:

The isolated before/after comparison supports the UCRT import replacements on these campaigns and corpora, including preserved individual exact results. The fixture137 failure is consistent with the corrected F30 oracle, not a Mac/F30 regression. It does not authorize rewriting all historical expected hashes. Strict all-admitted-exact acceptance is still false: unresolved pre-existing NaN/filtering cases and untouched Smoother remain. Broad refusals would discard existing exact cases, and fixes to other plugin kernels would exceed this ticket. Therefore this is a blocked acceptance report, not a claim that all requested numerical compatibility is complete.

changed_files:
- `core/dblur_gaussian.h`
- `core/dblur_noise.h`
- `core/dblur_rowdriver.cpp`
- `core/olmblur_worker16_legacy.cpp`
- `core/olmblur_worker16_nonlegacy.cpp`
- `core/olmblur_worker32_legacy.cpp`
- `core/olmblur_worker32_nonlegacy.cpp`
- `core/olmblur_worker8_legacy.cpp`
- `core/olmblur_worker_orchestration.cpp`
- `mac/OLMBlur/Mac/OLMBlur.xcodeproj/project.pbxproj`
- `mac/OLMBlur/OLMBlur.cpp`
- `mac/OLMColorKey/Mac/OLMColorKey.xcodeproj/project.pbxproj`
- `mac/OLMColorKey/OLMColorKey.cpp`
- `mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj/project.pbxproj`
- `mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj/project.pbxproj`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj/project.pbxproj`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj/project.pbxproj`
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `refs/scripts/build_olmdirectionalblur_cli.sh`
- `tests/fuzz_corpus/olmblur/seed1_case000040_1e01a8a5cbd2.json`
- `tests/fuzz_corpus/olmblur/seed1_case000099_9b13c27c2f2e.json`
- `tests/fuzz_corpus/olmdirectionalblur/seed1_case000084_9e50cab1bcf7.json`
- `tools/emulation/probe_radialblur_topology_20261001.py`
- `tools/fuzz/adapters/public.py`
- `tools/fuzz/adapters/radialblur.py`
- `tools/fuzz/before_F31.py`
- `tools/fuzz/build_F31.sh`
- `tools/fuzz/check_fixture_F31.py`
- `tools/fuzz/measure_F31.py`
- `tools/fuzz/rebaseline_F31.py`
- `tools/fuzz/run.py`
- `tools/fuzz/summarize_F31.py`
- `tools/fuzz/test_F31.sh`
- `tools/ucrt_cxx.py`
- `ucrtmath/build.sh`
- `orchestra/reports/F31-evidence/` — measurement comparison/residuals, source/build manifests, boundary inventory, fixture recapture and exact rebaseline audit.
- `orchestra/reports/F31-port-ucrtmath-switch-oracle.md`

verify:

From this worktree, with MAIN assets and the registered F30 worker available:

```sh
s="$PWD/orchestra/state/F31-port-ucrtmath-switch-oracle"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/measure_F31.py --before
python3 tools/fuzz/measure_F31.py
python3 tools/fuzz/summarize_F31.py
tools/fuzz/build_F31.sh
cat > "$s/math-smoke.cpp" <<'CPP'
#include "ucrtmath/include/ucrtmath.h"
int main() { return ucrt_expf(0.0f,UCRT_FMA)!=1.0f; }
CPP
tools/ucrt_cxx.py -I "$PWD" -arch arm64 -arch x86_64 "$s/math-smoke.cpp" -o "$s/math-smoke"
"$s/math-smoke"
python3 tools/fuzz/rebaseline_F31.py  # audit only; do not rewrite unrelated results
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/fuzz/check_fixture_F31.py
python3 -m venv "$s/test-venv"
PIP_CACHE_DIR="$s/pip-cache" "$s/test-venv/bin/pip" install pytest pillow numpy unicorn pefile
OLM_TEST_PYTHON="$s/test-venv/bin/python" tools/fuzz/test_F31.sh
git diff --check
```

Expected: all campaigns/replays complete, campaign tables above, zero per-route exact losses, six successful Universal builds, fixture137 `f31_exact_f30=true`. After migration, saved matches are Blur39/39 and DirectionalBlur56/56; other saved-match counts remain as recorded. Oracle timeout/diagnostic details may vary; preserve them and do not classify them as numerical UCRT changes. The current selected test runner should report **42 passed, 1 failed, 2 skipped, 37 subtests passed** once all assets are linked; the one expected historical-reference failure is fixture137, not a hidden PASS. Individual corpus replay uses the same explicit F30 command with `--replay <case>`, `--scratch "$s/post"`, `--report "$s/<name>.json"`; all three migrated cases have been freshly verified 1/1. Corpus T06 drift remains intentional/historical.

next:
- Orchestrator review is required before merging a default-oracle switch with strict acceptance still blocked; no push or merge was attempted.
- Separate bounded tickets for Blur's NaN sign propagation; DirectionalBlur seed31 cases187/295; DistanceGradation seed31 case253; and Smoother's pre-existing admitted mismatches. Preserve existing exact cases while closing them.
- Separately migrate/extend historical regression fixtures using freshly hash-bound F30 original-AEX evidence, starting with DirectionalBlur fixture137; do not blindly rebaseline the old 180-row suite.
- Native AE and genuine double-UCRT boundaries remain outside this qualification.

Final hygiene: all started build/emulator/test command sessions completed. Regenerable Xcode trees, harness executables/archives, parent source snapshot and scratch Python environment were deleted; logs, reports and small raw diagnostics remain. Temporary original-asset symlinks were removed. Scratch is below 5 GiB. Source manifest (41 files), all three unchanged corpus input objects, and final diff whitespace were checked.
