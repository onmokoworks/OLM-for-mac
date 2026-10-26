status: partial
summary:
- Removed unreachable ToonDilate fixture admission and Smoother v1 fixture branches; preserved the latter's digest audit under tests.
- Shared ColorKeep's PF8/PF16 callback body and checked address spans; retained the distinct PF32 comparisons.
- Removed Smoother2's unreachable parameter-ready refusal and duplicated shim cleanup branch.
- Scoped production non-comment lines: 2,566 -> 2,320 (-246); Universal warning occurrences: 1,438 -> 1,424 (-14).
- G4 retains two baseline source-text assertion failures; no assertion was weakened. Release gate intentionally not run.

facts:
- Baseline: `62a470a98bb4dce1c9a371209f0d0261a1840580`. Verified code revision: `37faf7c6`.
- Intermediate G1: `native_diff.py --cases 500 --arch arm64 --build both --jobs 1`, seed 909, each against baseline. Each includes three UHD cases per build. All differences, new refusals and execution errors were zero; first mismatch: none.

| Plugin | Comparisons | Exact renders | Matched refusals |
|---|---:|---:|---:|
| ColorKeep | 1,006 | 1,006 | 0 |
| ToonDilate | 1,006 | 1,006 | 0 |
| Smoother v1 | 1,006 | 672 | 334 |
| Smoother2 | 1,006 | 852 | 154 |

- Final G1: seed 909, 3,000 small + three UHD cases per architecture/build/plugin, both arm64/x86_64 and reference/fast. **48,048 comparisons: 42,248 exact renders and 5,800 matched refusals. Zero differences, new refusals and execution errors; first mismatch: none.** This full run was executed once, serially, at frozen revision `37faf7c6`.

| Plugin | Comparisons | Exact renders | Matched refusals |
|---|---:|---:|---:|
| colorkeep | 12,012 | 12,012 | 0 |
| olmtoondilate | 12,012 | 12,012 | 0 |
| olmsmoother | 12,012 | 8,008 | 4,004 |
| olmsmoother2 | 12,012 | 10,216 | 1,796 |

- SHA256 of the four final `summary.json` files concatenated in the table order: `b6f72fc33750f3dd5ba508bf0a877a94635d58bfb0b8130f60a86b57bef140b4`. This identifies this run; paths/build hashes in summary files may differ on rerun.

- G2: replayed all four plugins' `tests/fuzz_corpus` witnesses on base/head using recorded size/color/geometry settings, timeouts and supported routes. All 2,570 native observations per side compare byte-for-byte as JSONL, including native hashes, result dictionaries and refusal tags (excluding line numbers). No AEX/oracle was run or altered.

| Plugin | Observations per side | Identical base/head JSONL SHA256 |
|---|---:|---|
| ColorKeep | 842 | `05b85b184df2a94c362f3920e676731ec37f44a98a9c5a7a20c734c003dd0e6c` |
| ToonDilate | 1,124 | `005579222d14788108216ce86f451373838fe8aef7f656b6ea6c94f0fbebf3b8` |
| Smoother v1 | 380 | `b32df87a2076100f81456c7e29955390e12242ae835a8c4241a10ba0e04caa9f` |
| Smoother2 | 224 | `ffd106d234488d1331529c2f692f280d1c52ed1705ed5572df1db4e0c9353f20` |

- G4/G5: eight successful Universal Debug Xcode builds, `ARCHS='arm64 x86_64'`, `-jobs 1`, deployment target 11.0. Counts include two unchanged build-system warnings per build; compiler warning counts are the table values minus two. ToonDilate removed seven unused-function warnings per architecture. Generated sources were untouched.

| Scoped source | Non-comment lines before | After | Warnings before | After |
|---|---:|---:|---:|---:|
| `mac/ColorKeep/ColorKeep.cpp` | 603 | 589 | 332 | 332 |
| `mac/OLMToonDilate/OLMToonDilate.cpp` | 808 | 646 | 350 | 336 |
| `mac/OLMSmoother/Mac/OLMSmoother_port.cpp` | 548 | 485 | 410 | 410 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp` | 607 | 600 | 346 | 346 |

Complete tracked plugin `.cpp/.h/.inc` totals (including unchanged generated files and plugin-local tests):

| Plugin | Before | After |
|---|---:|---:|
| ColorKeep | 719 | 705 |
| OLMToonDilate | 886 | 724 |
| OLMSmoother | 18,725 | 18,662 |
| OLMSmoother2 | 11,947 | 11,940 |

- Remaining warnings include 328 SDK pragma-pack warnings per plugin. Smoother v1's non-SDK warnings are in included `.inc`/generated files, outside the scoped `port.cpp`; Smoother2's are in its included implementation/math files. They were not suppressed.
- Shared header adds 10 non-comment lines (162 -> 172); historical test catalogue adds 73. Thus production reduction is not solely a move. Counts strip block/line comments and blank lines. No new arithmetic constants or arithmetic types were introduced.
- `tests/ui_oracle/compare_mac.py`: 240 checks, zero semantic mismatches, including ColorKeep and Smoother2 handlers.
- Eleven targeted test modules: head **42 pass, 2 fail**. Baseline has the same outcome after supplying unchanged evidence paths. The failures are `ColorKeepWindowsContractTests.test_parameter_schema_and_zero_count_ui_boundary` (expects obsolete `enabledCount` clamping in `SetColorsEnabled`) and `ToonDilateTypedCoreTests.test_source_keeps_explicit_smart_depth_dispatch` (expects the obsolete full-row output-span expression). Neither expectation was edited.
- Initial test setup lacked pytest and baseline evidence paths. Installed pytest 9.1.1 into ticket scratch only and linked the baseline's `refs` and `reports/fuzz` to unchanged worktree evidence. The complete baseline pytest run reported 41 pass / 3 fail before the `reports/fuzz` link; its sole missing-file case then passed individually (1/1). This is setup recovery, not a numerical mismatch. MAIN's venv was used read-only.
- The historical Smoother digest test now reads its exact former catalogue from `tests/fixtures/OLMSmoother_admission.inc`; all digest and ordering assertions remain intact. The historical Toon corner candidate builder recognizes the later beta owner rather than attempting to inject obsolete fixture admission into it.
- Cleanup: serial verification queues exited; generated build trees, baseline archive, scratch dependencies, test binaries and owned SDK links were removed. Logs/reports remain (`147M`); final audits found no owned verification processes or Mach-O artifacts (the parent orchestrator/Codex processes remain).
- No tool call was rejected. No release gate, emulator rebuild, install, push, MAIN modification, or generated-file edit was performed.

inference:
- The removed Smoother v1 branches cannot execute: every one requires PF8/PF16, and the preceding beta check already returns true for both. Remaining unsupported depths still return false. The copied catalogue is historical test evidence, not an active admission policy.
- ToonDilate's old `ValidateToonPublicAdmission` and its private fixture generators have no callers; Smart uses `ValidateToonBetaAdmission`. Removing them does not broaden admission.
- Smoother2 cannot enter the render block after a failed `FetchParams`, so the separate readiness flag/refusal was redundant. Its source-bound fixture precedence and case-07 world checks remain active and unchanged.
- ColorKeep PF8/PF16 differ only in pixel/channel type and quantizer; the shared body preserves comparison order, aligned-local copies and alpha clearing. PF32 remains separate because ordered-greater-than rejection and NaN behavior differ.
- Other scoped depth dispatches already call templates, or select different SDK suites. Their numerical implementations and operation widths/order were retained.
- The measured regressions establish refactor equivalence for these cases, not a new all-input or native-AE exactness claim.

changed_files:
- `core/olm_world_safety.h`: separate overload for checked prevalidated byte spans; existing helpers unchanged.
- `mac/ColorKeep/ColorKeep.cpp`: shared integer callback, shared span validation, unused experiment macro and parameter name removed.
- `mac/OLMToonDilate/OLMToonDilate.cpp`: dead fixture generator/admission family removed.
- `mac/OLMSmoother/Mac/OLMSmoother_port.cpp`: unreachable source-bound fixture checks and unused SHA include removed.
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`: redundant readiness guard/shim branch and unused parameter name removed.
- `tests/fixtures/OLMSmoother_admission.inc`: historical catalogue relocated out of production.
- `tests/test_olmsmoother_source_contract_20260813.py`: catalogue read path only.
- `tools/emulation/test_olmtoondilate_corner_seed_public_candidate_20260814.py`: recognize current beta source.
- `orchestra/reports/C02-cleanup-olmsmall.md`: this report.

verify:
Run from this worktree, with a fresh scratch destination. Do not run the release gate.

```sh
ROOT="$PWD"
BASE=62a470a98bb4dce1c9a371209f0d0261a1840580
HEAD=37faf7c6
S="$ROOT/orchestra/state/C02-cleanup-olmsmall/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
for plugin in colorkeep olmtoondilate olmsmoother olmsmoother2; do
  python3 -B tools/refactor/native_diff.py --plugin "$plugin" --base "$BASE" \
    --head "$HEAD" --cases 3000 --arch both --build both --jobs 1 \
    --scratch "$S/G1" > "$S/G1-$plugin.log" 2>&1 || break
done
scripts/setup_ae_sdk_links.sh > "$S/sdk-links.log" 2>&1
python3 -B tests/ui_oracle/compare_mac.py --scratch "$S/ui" > "$S/ui.log" 2>&1
```

Expected G1: 12,012 comparisons per plugin; zero differences/new refusals/execution errors. Expected UI: 240 checks, zero mismatches.

For G2, extract the unchanged native replay script from the C01 report (no oracle needed), prepare baseline and replay:

```sh
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath tests \
  reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$ROOT/$name" "$S/base/$name"; done
python3 - "$S/replay_native.py" <<'PY'
from pathlib import Path
import sys
text = Path('orchestra/reports/C01-cleanup-shared-math-and-tests.md').read_text()
script = text.split("<<'PY_NATIVE'\n", 1)[1].split('\nPY_NATIVE', 1)[0]
Path(sys.argv[1]).write_text(script)
PY
for plugin in colorkeep olmtoondilate olmsmoother olmsmoother2; do
  for side in base head; do
    TREE="$ROOT"; if [ "$side" = base ]; then TREE="$S/base"; fi
    python3 -B "$S/replay_native.py" "$TREE" "$ROOT/tests/fuzz_corpus" \
      "$S/G2-$plugin-$side.jsonl" "$plugin" > "$S/G2-$plugin-$side.log" 2>&1
  done
  cmp "$S/G2-$plugin-base.jsonl" "$S/G2-$plugin-head.jsonl" || break
done
for plugin in ColorKeep OLMToonDilate OLMSmoother OLMSmoother2; do
  for side in base head; do
    TREE="$ROOT"; if [ "$side" = base ]; then TREE="$S/base"; fi
    OUT="$S/xcode/$plugin/$side"; mkdir -p "$OUT"
    xcodebuild -project "$TREE/mac/$plugin/Mac/$plugin.xcodeproj" \
      -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
      MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$OUT/objects" \
      SHARED_PRECOMPS_DIR="$OUT/pch" CONFIGURATION_BUILD_DIR="$OUT/products" \
      build > "$S/xcode-$plugin-$side.log" 2>&1
    rm -rf "$OUT"
  done
done
```

Expected G2: all four `cmp` calls exit 0, counts/hashes above. Expected build: all eight succeed, warning counts above.

Targeted tests (run on head and the prepared baseline; baseline needs read-only `refs` and `reports/fuzz` links as above). Use a Python with pytest and Pillow available; the run used MAIN's emulation Python with pytest installed via `pip --target` into scratch.

```sh
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python"
"$PY" -B -m pip install --target "$S/python" --no-cache-dir pytest==9.1.1 > "$S/pytest-install.log" 2>&1
export PYTHONPATH="$S/python:$ROOT"
ln -s "$ROOT/refs" "$S/base/refs"
ln -s "$ROOT/reports/fuzz" "$S/base/reports/fuzz"
"$PY" -B -m pytest -q -p no:cacheprovider --basetemp "$S/pytest-tmp" \
  tests/test_colorkeep_windows_callback_contract_20260731.py \
  tests/test_colorkeep_generic_beta_20260820.py tests/test_colorkeep_roi_tile_beta_20260820.py \
  tests/test_olmtoondilate_typed_core.py tests/test_olmtoondilate_generic_beta.py \
  tests/test_olmtoondilate_roi_safety.py tests/test_olmsmoother_source_contract_20260813.py \
  tests/test_olmsmoother_v1_generic_classic_beta_20260820.py \
  tests/test_olmsmoother2_default_beta_lane_20260820.py \
  tests/test_olmsmoother2_roi_fullframe_contract_20260820.py \
  tests/test_olmsmoother2_gamma_colors_beta_20260820.py
```

Repeat from `$S/base` with `PYTHONPATH="$S/python:$S/base"` and a distinct `--basetemp` for the baseline. Expected on both: 42 pass and the two named inherited source-text failures, exit 1. This is not a G4 all-tests-pass claim.

next:
- Orchestrator: review/merge the bounded cleanup and run the aggregate release gate once after all C02 tickets.
- Follow-up test-maintenance ticket: reconcile the two inherited source-text expectations with their current runtime contracts, preserving substantive assertions. This ticket does not change UI or span behavior to satisfy stale text.
