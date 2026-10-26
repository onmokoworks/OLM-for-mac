status: blocked
summary:
- Split OLMDirectionalBlur into four same-translation-unit responsibility sections; UI and dispatch entry remain in the main file.
- Named numeric contracts, clarified deep-kernel locals, removed duplicate Gaussian evaluation and dormant boundary capture.
- C++ non-comment/non-blank lines decreased 5083 -> 5044; largest source is 882 lines.
- G5 release-gate CLI cannot run within the required Q04 scratch boundary; no gate source or assertion was weakened.

facts:
- Start branch: `orch/Q04-refactor-olmdirectionalblur`; start HEAD and merge base with MAIN's integration branch (`codex/public-beta-roi`): `e55bc78a463786e79261b8c251c41e361b218c6c`.
- Initial use of the stale local `main` branch yielded `f4e4dac86925b512d4c7b8784d250f1a68871cb7`; its archive lacks `ucrtmath`. That setup attempt exited 2 with **0 comparisons** and is not counted as validation.
- Structural commit: `d5f46cc0`. Numeric naming/dead-code/test-reader commit: `b366ab7d`. No new translation units or build-entry edits.
- G1 structural step: 12012 exact comparisons, 0 differences, 0 execution errors, 0 refusals, 0 new refusals. Both architectures and both builds each ran 3000 small + 3 full 3840x2160 cases. Summary SHA-256: `b13f52ff605354ea5c340247aec4c62a9aed03140d635b252049e2ef101997d6`.
- G1 final commit `b366ab7d`: **12012 exact / 0 differences / 0 execution errors / 0 refusals / 0 new refusals**, exit 0. Same coverage as the structural run; first differing byte: none. Final summary SHA-256: `eb4626d246376dbac8dbdb657f034fce821669e8e107d480b86c836f7a9855b2`.
- G1 coverage per complete run: 4004 comparisons per depth; 12000 small / 12 4K; default geometry 4020, realistic-v1 3996, realistic-v2 3996; odd-even-v1 6004; downsample ratios include 1, 1/2, 1/3, 1/4, 1/8 and asymmetric 1/2 x 1/3. This plugin uses the existing byte-derived/exceptional PF32 generator, not Smoother2's independent float sampler.
- G2: **106/106** corpus replays match saved results at both base and final code; normalized base/head result differences **0**. Corpus tree: `59e2e608bb8ff226a0ff52d2e3946af5ae073d11`. Inventory: root 83, P04b2 4, P05a 7, P06a 5, T15b 4, N02 3. Mixed N02 size settings initially caused a setup rejection; replaying its files separately with recorded flags passed. Recorded worker hashes and timeouts were retained, never overridden.
- G3: seed 909, realistic geometry, 100 cases: base and head each **Smart 100 exact / 0 mismatch**, Classic **5 exact / 95 mismatch**; complete normalized result dictionaries match for all 100. First existing Classic mismatch: case index 0, PF16, 3x8, first byte/word 0, expected word `0000`, actual `6119`; actual raw SHA-256 `53e44e5f4f1fcd25e45ed454007b019e05f3bb783c40870ef958d216f330f1dd`. No Classic behavior was repaired.
- Original AEX (read in place from MAIN): `plugins_2025/OLMDirectionalBlur.aex`, SHA-256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- G3 default geometry oracle: `/Users/onmk/.cache/olm-emu/worker-F52c-geom/aex-guest-worker`, SHA-256 `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
- G4: parallel cap 1: **206 exact / 0 mismatch / 0 refusal** (200 small + HD and 4K at all three depths). Caps 2 and 8: **412 exact / 0 mismatch / 0 refusal** on the same 206 cases; **618 comparisons total** across caps 1/2/8.
- G5 Xcode: base and final code Universal Debug builds **SUCCEEDED**, arm64+x86_64, minOS 11.0. Package: initial Universal Release build verified **10 plugins**; initial packaging lacked MAIN's untracked reference manifests. With `OLM_REFERENCE_ROOT` set to MAIN, packaging succeeded for **10 plugins**. Final-code package rerun: **10 Universal plugins built/verified and packaged, exit 0**.
- G5 UI oracle: DirectionalBlur **3 updates / 6 checks including reload / 0 mismatches**. `test_olmdirectionalblur_update_params_ui_20260810.py`: **1 test PASS**. UI handler and command dispatch remain in the main `.cpp`.
- G5 source readers now expand only DirectionalBlur `.inc` includes, preserving assertions. Classic dispatch test fails at the **same pre-existing assertion on base and head**: it expects literal `return PF_Err_BAD_CALLBACK_PARAM`, while production uses `OLM_DIRECTIONAL_REFUSAL("classic-format")`. The dispatch-documentation test passes DirectionalBlur checks then fails on unchanged Smoother's missing literal `PF_OutFlag2_SUPPORTS_SMART_RENDER`.
- G5 release gate attempted exactly with `--state "$S/release-gate"`: argparse exits **2**, `state must be inside this ticket scratch`. Its implementation only accepts `orchestra/state/R09-release-gate-v2`, conflicting with this worker's mandatory Q04-only scratch. **None of its seven local stages ran.** No bypass or release-gate file modification was made.
- G6: Xcode warning counts **380 base / 380 final**, identical warning-message multisets. The structural/final all-plugin Release package builds also both emitted 3622 warnings. No warnings were suppressed or compiler options changed to obtain this result.
- Direct PE reads from MAIN's original AEX confirmed nine constants: RVA b358=`0.587`, b350=`0.299`, b348=`0.114`, b33c=`2^-15`, b370=`90.0`, b378=`180.0`, b384=`100.0f`, b1ec=`3.0f`, b1e0=`1e-5` (double). The existing representations and arithmetic widths were preserved.
- Cleanup: all started verification processes completed; native run trees, baseline source archive, Xcode trees, package bundles/zips, SDK/build symlinks and one-off scratch script were removed. Logs and measurement reports remain; final `du -sh` is **64M**, below the 5 GiB limit. No durable oracle was built or installed.
- Static check: expanding the four main-file includes, removing the original four disabled capture blocks, expanding the two fixed-word constants, and stripping comments/whitespace produces an identical main-file token stream before/after.
- The RadialBlur subsection of `core/dblur_noise.h` is byte-for-byte unchanged. `OLM_REFERENCE_BUILD` and `OLM_PARALLEL_MAX` logic is unchanged. Generated files, release gate files, forbidden-action lists and other plugins' source are unchanged.

Named constants (sample): `kGaussianSigmaDivisor`, `kGaussianEpsilon`, `kGreenLuma`, `kRedLuma`, `kBlueLuma`, `kAngleQuarterTurn`, `kAngleHalfTurn`, `kPercentUnit`, `kInt32Limit`, `kMagnitudeMask`, `kSignMask`, `kNoiseTableSamples`, `kNoisePeriodF32`, `kFixedWholeSign`, `kMaximumStrength`. Literal UI declarations and retained fixture tuples retain their existing text contracts.

Removed code:
- `gaussian_weight_expfloat`: its body was identical to `gaussian_weight`, including `UCRT_FMA`. The internal selector remains accepted, with a comment explaining why both selections are identical.
- Four `OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE` blocks (62 lines), including the file writer: no shipped/reference build enables them; repository search found no active caller/definition outside this code. Historical T10 documentation mentions this diagnostic.
- Test-seam helpers and intentionally different per-depth kernels remain: they are used by retained probes or preserve different unpack, alpha and writeback contracts.

Line counts (physical / non-comment non-blank C++ lines; comments stripped before counting):

| File | Before | After |
|---|---:|---:|
| `core/dblur_field.cpp` | 158 / 146 | 164 / 150 |
| `core/dblur_field.h` | 36 / 29 | 36 / 29 |
| `core/dblur_float.h` | 34 / 27 | 34 / 27 |
| `core/dblur_frontonly.cpp` | 814 / 758 | 822 / 763 |
| `core/dblur_frontonly.h` | 159 / 139 | 159 / 139 |
| `core/dblur_gaussian.h` | 32 / 25 | 31 / 23 |
| `core/dblur_generic_budget.h` | 342 / 288 | 344 / 289 |
| `core/dblur_noise.h` | 207 / 167 | 214 / 173 |
| `core/dblur_rotate.cpp` | 206 / 180 | 206 / 180 |
| `core/dblur_rotate.h` | 39 / 24 | 39 / 24 |
| `core/dblur_rowdriver.cpp` | 517 / 473 | 521 / 476 |
| `core/dblur_rowdriver.h` | 61 / 44 | 61 / 44 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp` | 2837 / 2607 | 367 / 317 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur.h` | 122 / 110 | 122 / 110 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp` | 39 / 36 | 39 / 36 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.h` | 32 / 30 | 32 / 30 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_admission.inc` | 0 / 0 | 882 / 807 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_dispatch.inc` | 0 / 0 | 739 / 695 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_host.inc` | 0 / 0 | 598 / 547 |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_kernels.inc` | 0 / 0 | 201 / 185 |

No individual C++ file exceeds 882 lines after the split. Counts include `.cpp`, `.h`, `.inc` in the ticket scope; unchanged project/resources/tests are excluded from this C++ metric.

inference:
- The measured cases support bit-exact preservation for these configurations; they do not prove all inputs or native AE/UCRT equivalence.
- Suspected latent issue, left alone: `gaussian_argument` computes `index * index` as signed int before conversion. A direct core call with an index above 46340 could overflow; the public Strength limit is 4000, so this is not evidence of a supported-UI failure.
- The legacy core truncates processed rows to a multiple of its partition count unless full-height mode is selected. This may look like a remainder bug, but it is retained behavior and was not changed.
- The high-precision host pi and the core's AEX `3.14159265` literal intentionally remain distinct. Unifying them would be a numerical change.

changed_files:
- `core/dblur_field.cpp`
- `core/dblur_frontonly.cpp`
- `core/dblur_gaussian.h`
- `core/dblur_generic_budget.h`
- `core/dblur_noise.h`
- `core/dblur_rowdriver.cpp`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur_admission.inc`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur_dispatch.inc`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur_host.inc`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur_kernels.inc`
- `tests/test_beta_support_documentation.py`
- `tests/test_directional_radial_classic_render_bitdepth_dispatch_20260716.py`
- `orchestra/reports/Q04-refactor-olmdirectionalblur.md`

verify:
Run from this worktree. These commands use MAIN only for read-only SDK/reference assets:

```sh
S="$PWD/orchestra/state/Q04-refactor-olmdirectionalblur"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
PY="$MAIN/tools/emulation/.venv/bin/python3"
BASE=e55bc78a463786e79261b8c251c41e361b218c6c
mkdir -p "$S"
export TMPDIR="$S" OLM_TEST_JOBS=1

python3 tools/refactor/native_diff.py --plugin olmdirectionalblur \
  --base "$BASE" --head HEAD --cases 3000 --seed 909 \
  --arch both --build both --jobs 1 --scratch "$S/recheck-G1" \
  > "$S/recheck-G1.log" 2>&1
# Expected: 12012 exact, differences/refusals/new refusals/execution errors all zero.

"$PY" tools/fuzz/run.py --plugin olmdirectionalblur --n 100 --seed 909 \
  --geometry realistic --jobs 1 --shrink-attempts 0 --shrink-seconds 0 \
  --scratch "$S/recheck-G3" --report "$S/recheck-G3.json" \
  --corpus "$S/recheck-G3-corpus" > "$S/recheck-G3.log" 2>&1
# Expected: Smart 100 exact; Classic 5 exact / 95 mismatch, unchanged from base.

python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur \
  --small 200 --hd 3 --uhd 3 --seed 909 --jobs 1 --parallel 1 \
  --scratch "$S/recheck-G4-1" > "$S/recheck-G4-1.log" 2>&1
python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur \
  --small 200 --hd 3 --uhd 3 --seed 909 --jobs 1 --parallel 2 8 \
  --scratch "$S/recheck-G4-2-8" > "$S/recheck-G4-2-8.log" 2>&1
# Expected: 206 and 412 exact comparisons respectively; no mismatches/refusals.

python3 tests/ui_oracle/compare_mac.py --scratch "$S/recheck-ui" \
  > "$S/recheck-ui.log" 2>&1
"$PY" tests/test_olmdirectionalblur_update_params_ui_20260810.py \
  > "$S/recheck-parameter-ui.log" 2>&1
# Expected: DirectionalBlur 6 UI oracle checks with zero mismatches; 1 unittest PASS.
```

G2, including recorded flags for the mixed N02 directory (each listed corpus file is replayed once):

```sh
replay_q04() {
  label="$1"; corpus_path="$2"; shift 2
  "$PY" tools/fuzz/run.py --plugin olmdirectionalblur --replay "$corpus_path" \
    --jobs 1 --scratch "$S/recheck-G2/$label" --report "$S/recheck-G2-$label.json" \
    "$@" > "$S/recheck-G2-$label.log" 2>&1
}
C=tests/fuzz_corpus/olmdirectionalblur
replay_q04 root "$C"
replay_q04 P04b2 "$C/P04b2-cropped-checkout"
replay_q04 P05a "$C/P05a-performance"
replay_q04 P06a "$C/P06a-investigation"
replay_q04 T15b "$C/T15b-odd-even-realistic" --max-size 1920 \
  --geometry realistic --size-sampler odd-even-v1 --size-max-height 1080
replay_q04 N02-v2 "$C/N02-nightly-20261025/33736bb7ba8bbc31e737404a.json" \
  --max-size 256 --geometry realistic-v2
replay_q04 N02-odd "$C/N02-nightly-20261025/7f02accac670dc615c92f894.json" \
  --max-size 1920 --geometry realistic --size-sampler odd-even-v1 --size-max-height 1080
replay_q04 N02-v1 "$C/N02-nightly-20261025/fdd4da1dfc62f6a1e40cd84a.json" \
  --max-size 256 --geometry realistic
# Expected: all eight invocations exit 0; 106 matches_saved=true in total.
```

Base measurements used a source-only `git archive`, not a modified MAIN checkout:

```sh
mkdir -p "$S/base-recheck"
git archive "$BASE" mac core cli tools ucrtmath \
  reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base-recheck"
"$PY" "$S/base-recheck/tools/fuzz/run.py" --plugin olmdirectionalblur \
  --main "$MAIN" --n 100 --seed 909 --geometry realistic --jobs 1 \
  --shrink-attempts 0 --shrink-seconds 0 \
  --scratch "$S/base-recheck/orchestra/state/G3" \
  --report "$S/base-recheck/orchestra/state/G3.json" \
  --corpus "$S/base-recheck/orchestra/state/G3-corpus" > "$S/recheck-G3-base.log" 2>&1
# Expected: same counts and result dictionaries as final G3.
# Base G2 used the same eight replay commands with this archive's run.py,
# --main "$MAIN", and scratch/report paths inside base-recheck/orchestra/state.
```

G5/G6 build commands actually used (Xcode outputs stay in ticket scratch):

```sh
bash scripts/setup_ae_sdk_links.sh > "$S/recheck-sdk-links.log" 2>&1
xcodebuild -project mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj \
  -configuration Debug -jobs 1 'ARCHS=arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
  MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$S/recheck-xcode/obj" \
  SYMROOT="$S/recheck-xcode/products" SHARED_PRECOMPS_DIR="$S/recheck-xcode/pch" \
  build > "$S/recheck-xcode.log" 2>&1
# Expected: BUILD SUCCEEDED, 380 warning diagnostics with this SDK/toolchain.
# Baseline used the same command pointing -project at the base archive,
# with separate xcode-base output paths and SDK links to MAIN.
```

For package verification, this run created SDK links and temporary `mac/*/Mac/build` symlinks into `$S/package-build/<plugin>` before invoking the unchanged script. Those build symlinks and outputs are removed during cleanup. In a fresh worktree, recreate them without replacing existing paths:

```sh
python3 - <<'PY'
from pathlib import Path
root=Path.cwd(); main=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
state=root/'orchestra/state/Q04-refactor-olmdirectionalblur'
for name in ('Headers','Util','Resources'):
    link=root/name
    if not link.exists(): link.symlink_to((main/name).resolve(), target_is_directory=True)
for name in ('ColorKeep','OLMBlur','OLMColorKey','OLMDirectionalBlur','OLMRadialBlur',
             'OLMKiraKira','OLMToonDilate','OLMDistanceGradation','OLMSmoother','OLMSmoother2'):
    link=root/'mac'/name/'Mac/build'; target=state/'package-build'/name
    if link.exists() or link.is_symlink(): raise RuntimeError(f'Existing path: {link}')
    target.mkdir(parents=True,exist_ok=True); link.symlink_to(target,target_is_directory=True)
PY
OLM_REFERENCE_ROOT="$MAIN" bash scripts/package_mac_plugins.sh --configuration Release \
  --output "$S/recheck-plugins.zip" > "$S/recheck-package.log" 2>&1
# Expected: ten Universal bundles built/verified and ten packaged plugins.

"$PY" scripts/run_olm_release_gate_v2.py --state "$S/release-gate" \
  > "$S/recheck-release-gate.log" 2>&1
# Current expected BLOCKER: exit 2, "state must be inside this ticket scratch".
# Do not redirect it to R09 scratch under this worker's rules.
```

The two source-text checks can also be reproduced without changing their assertions:

```sh
python3 tests/test_directional_radial_classic_render_bitdepth_dispatch_20260716.py \
  > "$S/recheck-classic-source.log" 2>&1
python3 -m unittest \
  tests.test_beta_support_documentation.BetaSupportDocumentationContract.test_depth_and_route_claims_are_anchored_in_dispatch_code \
  > "$S/recheck-dispatch-doc.log" 2>&1
# Expected pre-existing failures described above; do not count them as passes.
```

next:
- Orchestrator/tool-owner follow-up: allow the release gate to use caller-selected ticket scratch and respect `OLM_TEST_JOBS=1`, without changing any gate assertions/stages. Then run all seven G5 stages; this ticket cannot claim completion until they pass or the orchestrator explicitly revises the contract.
- Resolve the pre-existing source-text test drift in its own ticket; this refactor only adjusts where source is read.
- No behavior fixes or promotion of conformance scope are proposed here.
