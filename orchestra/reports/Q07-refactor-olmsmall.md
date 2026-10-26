status: done

summary:
- Split Smoother v1/v2 into responsibility-based includes while preserving one translation unit and the original evaluation order.
- Kept UI, dispatch, and the Smoother2 RenderBits diagnostic insertion point in the main files.
- Removed only three unused Smoother2 helpers and their address-only warning suppression; generated translations and captured LUT bytes are unchanged.
- Final G1: 48,048 comparisons, zero differences/new refusals/execution errors. All 1,398 corpus witnesses also preserve their Mac-side results.

facts:
- Start HEAD and merge base: `2387237a8012432bcdf5078803ecfdce795f6129`. `git merge codex/public-beta-roi` returned `Already up to date.`
- Structural commits: `a2a60249` (Smoother2), `4a944a75` (Smoother v1 and shared-header comments). `0c3624f3` keeps RenderBits visible to the existing diagnostic harness and passed a separate full G1 rerun.
- No real translation units were added. Existing Xcode and native-differential entry points compile the includes without project changes. Text-reading tests expand the moved includes without changing their assertions.
- ColorKeep's five existing named quantization/tolerance constants are now `static constexpr float`: `kColorKeep8Bias`, `kColorKeep8Scale`, `kColorKeep16Bias`, `kColorKeep16Scale`, `kColorKeepFloatTolerance`. Values, widths and bit patterns are unchanged. ToonDilate's refusal-log `n` is renamed `length`. No speculative renaming of register/decompiler variables was attempted.
- Smoother2 dead code removed: `weight_samples` had no invocation (only a commented call and address-only warning suppression); `pow_rgb` and `win_FUN_180004c30_lut` had no callers. `luma_bt709` remains because adaptive gamma uses it. The separate older pipeline still has its own active weight/pow functions and was not substituted for production.
- Existing per-depth variants, generated-instruction adapters, reference/fast selection, and `OLM_PARALLEL_MAX` behavior are preserved. Comments clarify SSE operation order, active-row padding, SHA-256 constants, and remove stale stage/unused claims.
- Shared-header review covered `olm_checked_allocation.h`, `olm_checked_rect.h`, `olm_parallel.h`, `olm_roi_contract.h`, `olm_sha256_rows.h`, and `olm_world_safety.h`. Only comments in the latter two changed.

Line counts (physical / non-comment nonblank; removed block and line comments with the same textual regex used by the previous report, not a C++ lexer):

| File | Before | After |
| --- | ---: | ---: |
| `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp` | 5536 / 4399 | 785 / 607 |
| `mac/OLMSmoother2/OLMSmoother2.cpp` | 1029 / 753 | 351 / 274 |
| `mac/OLMSmoother/Mac/OLMSmoother_port.cpp` | 4389 / 3747 | 668 / 548 |
| `mac/ColorKeep/ColorKeep.cpp` | 666 / 599 | 667 / 599 |
| `mac/OLMToonDilate/OLMToonDilate.cpp` | 899 / 808 | 899 / 808 |
| `mac/OLMSmoother/Mac/OLMSmoother_subhandler8.inc` | 0 / 0 | 564 / 521 |
| `mac/OLMSmoother/Mac/OLMSmoother_render.inc` | 0 / 0 | 492 / 409 |
| `mac/OLMSmoother/Mac/OLMSmoother_subhandler16.inc` | 0 / 0 | 453 / 394 |
| `mac/OLMSmoother/Mac/OLMSmoother_state_math.inc` | 0 / 0 | 176 / 115 |
| `mac/OLMSmoother/Mac/OLMSmoother_edge_walkers.inc` | 0 / 0 | 531 / 471 |
| `mac/OLMSmoother/Mac/OLMSmoother_pixel_helpers.inc` | 0 / 0 | 520 / 448 |
| `mac/OLMSmoother/Mac/OLMSmoother_interpolation.inc` | 0 / 0 | 451 / 426 |
| `mac/OLMSmoother/Mac/OLMSmoother_classifiers.inc` | 0 / 0 | 488 / 423 |
| `mac/OLMSmoother2/OLMSmoother2_legacy_pipeline.inc` | 0 / 0 | 675 / 480 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_constants.inc` | 0 / 0 | 215 / 169 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_classification.inc` | 0 / 0 | 473 / 365 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_polygon_scan.inc` | 0 / 0 | 493 / 386 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_gamma_composite.inc` | 0 / 0 | 485 / 355 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_corner_samples.inc` | 0 / 0 | 632 / 459 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_admission.inc` | 0 / 0 | 422 / 369 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_frame_setup.inc` | 0 / 0 | 477 / 326 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_polygon_dispatch.inc` | 0 / 0 | 640 / 586 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_cardinal_leaves.inc` | 0 / 0 | 426 / 383 |
| `mac/OLMSmoother2/Mac/OLMSmoother2_polygon_weights.inc` | 0 / 0 | 447 / 378 |

Total executable-line count across the five original main files and all new includes: **10,306 -> 10,299**. Other in-scope files are unchanged. The largest refactored handwritten file is 899 lines. The two 3,337-line runtime-capture LUT headers remain unchanged generated data; all `*.generated.inc` files are unchanged.

G1 (native_diff.py, seed 909, 3,000 small + 3 added 4K cases per architecture/build, jobs=1):

| Plugin | Comparisons | Exact | Identical refusals | Differences | New refusals | Execution errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| olmsmoother2 | 12012 | 10216 | 1796 | 0 | 0 | 0 |
| olmsmoother | 12012 | 8008 | 4004 | 0 | 0 | 0 |
| olmtoondilate | 12012 | 12012 | 0 | 0 | 0 | 0 |
| colorkeep | 12012 | 12012 | 0 | 0 | 0 | 0 |

All four commands exited 0. First mismatch: none. Per-build native executable hashes and coverage counters are retained in [Q07-refactor-olmsmall-evidence.json](Q07-refactor-olmsmall-evidence.json).

The first Smoother2 split also passed 12,012 comparisons (10,216 exact, 1,796 identical refusals, zero differences/new refusals/execution errors) before keeping RenderBits in the main file. Binary hashes are not assumed identical: refusal attribution line numbers and source layout change. Output bytes and normalized tags are the compared contract.

G2 (Mac-only):

| Plugin | Corpus witnesses | Routes per revision | OK | Refusal | Base/head differences |
| --- | ---: | ---: | ---: | ---: | ---: |
| OLMSmoother2 | 112 | 224 | 112 | 112 | 0 |
| OLMSmoother | 303 | 380 | 308 | 72 | 0 |
| OLMToonDilate | 562 | 1,124 | 1,124 | 0 | 0 |
| ColorKeep | 421 | 842 | 464 | 378 | 0 |

The 2,570 paired route results represent 5,140 candidate invocations. All 1,398 corpus JSON files, including sibling realistic directories and nested P04/P05/T15b directories, were loaded with their recorded max-size, height, size/color sampler, geometry, and timeout. Worker bindings were validated with `tools/fuzz/run.py::replay_groups`. Mac replay used the shared adapters' `build`/`candidate`, `core.load_corpus`, and `geometry.require_host`, in isolated base/head processes. `require_host` selects the existing Classic-only geometry route for v1; it does not invent unsupported Smart geometry coverage. Compared fields were native status/error/metadata, raw SHA-256/length, and refusal tags with source line suffixes removed. First mismatch: none. No oracle-side results or timing outcomes were promoted to pixel evidence. Smoother2's final layout was replayed again and its 224 serialized results equal base.

G4/G5:

| Xcode Release, arm64 + x86_64 | Base | Head | Warnings base -> head |
| --- | --- | --- | ---: |
| OLMSmoother2 | success | success (including final layout) | 350 -> 346 |
| OLMSmoother | success | success | 410 -> 410 |
| OLMToonDilate | success | success | 350 -> 350 |
| ColorKeep | success | success | 332 -> 332 |

Warning counts include SDK pragma-pack, project configuration, and compiler diagnostics; no warning category increased. Xcode used `-jobs 1`, scratch OBJROOT/SYMROOT/SHARED_PRECOMPS_DIR, and read-only SDK links to MAIN.

- `tests/ui_oracle/compare_mac.py --scratch .../ui`: exit 0; ColorKeep 4 updates / 8 checks and Smoother2 18 updates / 36 checks, all zero mismatches. The same command also checks the other UI-supported plugins; no out-of-scope source was edited.
- Six focused unittest modules (default lane, full-frame ROI, gamma-color UI, v1 Classic/Smart beta, and source contracts): **26/26 passed** on base and head after adapting source reads. Initial post-split head failures were source-reader failures, fixed by reading the includes with unchanged assertions.
- Five pytest modules (ColorKeep generic/ROI, ToonDilate generic/ROI, v1 PF16 classifier direction): **13 passed, 2 failed** identically on base/head. The failures are ColorKeep `test_generic_admission_is_not_fixture_bound` and `test_exported_effectmain_nonzero_origin_classic_and_smart`: Smart callback accounting reports `co=101 cc=100 ci=101 li=1` at all three depths.
- Two old mixed-plugin Classic dispatch tests fail at the untouched KiraKira and DistanceGradation assertions on both base/head. Selecting each test's in-scope source runs the unchanged assertions successfully for older Smoother2 and ToonDilate on both revisions.
- Smoother2 color-weight/gamma-composition/key-gamma-HDR tests: **1 passed, 5 failed, 1 error**, identical at base/head. Five failures are stale captured dependency hashes (probe/shim dependencies, including actual `6ca358aa...` vs expected `22636eb6...` and `7153fc6d...` vs `807ee172...`). The PreRender test binary returns 10 on both. The successful public replay is **252 optimized + 252 ASan/UBSan renders, all 504 raw exact**.
- ADA0 input differential: one error on both revisions because the legacy trace log is untracked and absent from both worktree source trees. The error occurs before the adjusted text assertion; no numerical claim is made from it.
- Per the revised spec, G3 has no separate campaign, and no G6 is defined. Release-v2 and packaging belong to the orchestrator; neither was run or modified here.

inference:
- The measured native/corpus results support behavior preservation for these finite cases, not universal Windows or AE conformance.
- Suspicious existing code left unchanged: both Smoother refusal loggers pass a positive `snprintf` return length to `write` without clamping it to the 384-byte buffer. A sufficiently long future function/tag could over-read; current tested tags did not demonstrate that failure.
- `olm::roi::byte_offset` subtracts signed frame/storage origins before casting to unsigned. Extreme opposite-sign coordinates could overflow before the later bounds checks; reachability from current admitted plugin worlds was not established.
- `TightStaging::prepare` is noexcept and catches `bad_alloc` but not `length_error`; extreme vector lengths merit a separate boundary investigation. No production behavior fix was attempted.
- The existing Smoother2 curve-index mapping uncertainty remains documented; this refactor does not resolve or retune it.

changed_files:
- Smoother2 main files and their responsibility includes listed above.
- Smoother v1 main file and its eight includes listed above.
- `mac/ColorKeep/ColorKeep.cpp`, `mac/OLMToonDilate/OLMToonDilate.cpp`.
- Comment-only: `core/olm_sha256_rows.h`, `core/olm_world_safety.h`.
- Source-read-only test changes: `test_olmsmoother2_ada0_input_differential_20260718.py`, `test_olmsmoother2_default_beta_lane_20260820.py`, `test_olmsmoother2_roi_fullframe_contract_20260820.py`, `test_olmsmoother_source_contract_20260813.py`, `test_olmsmoother_v1_pf16_classifier_direction_pair_20260806.py` under `tests/`.
- This report and the numeric evidence JSON.

verify:
Run from the ticket worktree. Use a fresh recheck suffix if rerunning; all commands keep scratch below this ticket.

```sh
BASE=2387237a8012432bcdf5078803ecfdce795f6129
STATE="$PWD/orchestra/state/Q07-refactor-olmsmall/recheck"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
mkdir -p "$STATE"
export TMPDIR="$STATE" TMP="$STATE" TEMP="$STATE" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
for plugin in olmsmoother2 olmsmoother olmtoondilate colorkeep; do
  python3 tools/refactor/native_diff.py --plugin "$plugin" --base "$BASE" --head HEAD --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch "$STATE/g1" > "$STATE/g1-$plugin.log" 2>&1
done
git diff --check "$BASE"
git diff "$BASE" -- '*.generated.inc'
```

Expected G1 counts are above, all exits 0; generated-file diff and whitespace check are empty. The initial structural runs used `--head WORKTREE`, `.../g1` (all four plugins), and `.../g1-final` (final Smoother2 layout), with stdout/stderr redirected to ticket logs.

Create the same isolated base source tree for base/head tests and corpus replay:

```sh
mkdir -p "$STATE/base"
git archive "$BASE" mac core cli tools ucrtmath tests reports refs/conformance | tar -xf - -C "$STATE/base"
```

Mac-only corpus replay uses the shared adapters directly so oracle diagnostics cannot affect the comparison. This is the invocation used by the temporary `replay_mac.py` orchestration during this ticket, expressed inline here; no replacement renderer or persistent test tool is added:

```sh
python3 - <<'PY_REPLAY'
import os, subprocess, sys
from pathlib import Path
root = Path.cwd()
state = Path(os.environ['TMPDIR'])
worker = r"""
import hashlib, importlib, json, os, re, sys, tempfile, time
from pathlib import Path
from types import SimpleNamespace
root, corpus_root, state, plugin = map(Path, sys.argv[1:5])
plugin = str(plugin)
sys.path.insert(0, str(root / 'tools/fuzz'))
from core import load_corpus
from geometry import require_host
Adapter = importlib.import_module('adapters.' + plugin).Adapter
main = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
state.mkdir(parents=True, exist_ok=True)
adapter = Adapter(SimpleNamespace(main=main, worker=Path('/unused'), max_size=256,
                                 size_max_height=None, case_timeout=10))
adapter.env.update(TMPDIR=str(state), TMP=str(state), TEMP=str(state))
paths = sorted(p for p in (corpus_root/'tests/fuzz_corpus').rglob('*.json')
               if plugin in p.parts or p.parent.name.startswith(plugin+'_'))
with tempfile.TemporaryDirectory(dir=state, prefix='build-') as build:
    adapter.binary, _ = adapter.build(Path(build), time.monotonic()+300)
    with (state/'rows.jsonl').open('w') as output:
        for path in paths:
            saved = json.loads(path.read_text())
            adapter.max_size = saved['max_size']
            adapter.size_max_height = saved.get('size_max_height')
            adapter.size_sampler = saved.get('size_sampler', 'default')
            adapter.color_sampler = saved.get('color_sampler', 'default')
            adapter.timeout = saved.get('provenance', {}).get('case_timeout_seconds', 10)
            case, _ = load_corpus(path, adapter)
            require_host(adapter, case)
            for route in adapter.routes:
                with tempfile.TemporaryDirectory(dir=state, prefix='case-') as work:
                    work = Path(work)
                    adapter.env['OLM_REFUSAL_TRACE'] = str(work/'trace')
                    outcome = adapter.candidate(case, work, route, time.monotonic()+adapter.timeout)
                    result, raw = outcome[:2]
                    tags = outcome[2] if len(outcome)>2 else ((work/'trace').read_text().splitlines() if (work/'trace').exists() else [])
                    row = dict(path=str(path.relative_to(corpus_root)), route=route,
                               result=result, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                               tags=[re.sub(r'@\d+$', '', tag) for tag in tags])
                    output.write(json.dumps(row, sort_keys=True)+'\n'); output.flush()
                    del raw, outcome
"""
for plugin in ('olmsmoother2', 'olmsmoother', 'olmtoondilate', 'colorkeep'):
    for side, source in (('base', state/'base'), ('head', root)):
        destination = state/'g2'/f'{plugin}-{side}'
        with (state/f'g2-{plugin}-{side}.log').open('w') as log:
            subprocess.run([sys.executable, '-c', worker, str(source), str(root),
                            str(destination), plugin], stdout=log, stderr=log, check=True)
    before = (state/'g2'/f'{plugin}-base/rows.jsonl').read_bytes()
    after = (state/'g2'/f'{plugin}-head/rows.jsonl').read_bytes()
    assert before == after, plugin
    print(plugin, len(before.splitlines()), 'equal native route results')
PY_REPLAY
```

Expected route counts: 224 / 380 / 1124 / 842, zero differences. Worker binding validation was also run over every corpus parent via `tools/fuzz/run.py::replay_groups` with no worker/timeout override; all 15 directories validated.

Xcode recheck (the same command was run for head and the archived base): provide SDK `Headers`, `Util`, and `Resources` as read-only links to MAIN in each source root if absent, then run:

```sh
for plugin in OLMSmoother2 OLMSmoother OLMToonDilate ColorKeep; do
  xcodebuild -project "mac/$plugin/Mac/$plugin.xcodeproj" -configuration Release -jobs 1 'ARCHS=arm64 x86_64' ONLY_ACTIVE_ARCH=NO "OBJROOT=$STATE/xcode-$plugin/obj" "SYMROOT=$STATE/xcode-$plugin/products" "SHARED_PRECOMPS_DIR=$STATE/xcode-$plugin/pch" build > "$STATE/xcode-$plugin.log" 2>&1
done
python3 tests/ui_oracle/compare_mac.py --scratch "$STATE/ui" > "$STATE/ui.log" 2>&1
python3 -m unittest tests.test_olmsmoother2_default_beta_lane_20260820 tests.test_olmsmoother2_roi_fullframe_contract_20260820 tests.test_olmsmoother2_gamma_colors_beta_20260820 tests.test_olmsmoother_v1_generic_classic_beta_20260820 tests.test_olmsmoother_v1_smart_beta_20260822 tests.test_olmsmoother_source_contract_20260813 > "$STATE/focused-tests.log" 2>&1
python3 -m pytest -q -p no:cacheprovider tests/test_colorkeep_generic_beta_20260820.py tests/test_colorkeep_roi_tile_beta_20260820.py tests/test_olmtoondilate_generic_beta.py tests/test_olmtoondilate_roi_safety.py tests/test_olmsmoother_v1_pf16_classifier_direction_pair_20260806.py > "$STATE/pytest.log" 2>&1
python3 -m unittest tests.test_olmsmoother2_color_weight_20261001 tests.test_olmsmoother2_gamma_composition_20261001 tests.test_olmsmoother2_key_gamma_hdr_20261001 > "$STATE/capture-tests.log" 2>&1
python3 -m unittest tests.test_kirakira_smoother2_classic_render_bitdepth_dispatch_20260716 tests.test_olmdg_toondilate_classic_render_bitdepth_dispatch_20260716 tests.test_olmsmoother2_ada0_input_differential_20260718 > "$STATE/legacy-tests.log" 2>&1
```

Expected: all Xcode builds, UI comparison, and 26 focused tests pass; the baseline failures described above reproduce. Run the same test commands from `$STATE/base` to compare baseline failures. pytest 9.1.1 was installed only into ticket scratch (`python3 -m pip install --target .../pydeps --no-cache-dir pytest`); use an environment with pytest or set PYTHONPATH to that scratch installation. The two mixed-plugin tests' unchanged in-scope assertions were additionally run with `OWNED_SOURCES = OWNED_SOURCES[1:]`, passing on both revisions.


next:
- Orchestrator review/merge, then aggregate release gate and packaging.
- Separate maintenance tickets can repair the base-failing test/capture bindings and investigate the suspicious boundaries above. Do not change numerical behavior under this readability ticket.

Cleanup: all started commands finished and their exits were collected. Regenerable build trees, baseline source archive, temporary pytest dependencies, and the three SDK symlinks were removed. The final scan found zero Mach-O/object/archive files in ticket scratch. Logs and native observation JSONL remain; MAIN and installed bundles were not modified. No push was performed.
