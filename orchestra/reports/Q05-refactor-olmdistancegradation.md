status: done
summary:
- Split OLMDistanceGradation into five responsibility-based includes, retaining a single translation unit and UI/entry code in main.
- Named exact IPP coefficients and conversion boundaries; removed three unused declarations/helpers without changing algorithms.
- Structural and final G1 each pass 12,012 comparisons with zero differences.
- Corpus Mac replay: 890 Classic/Smart results, hashes and refusal-tag lists identical. Universal Xcode builds pass; warnings decrease 370 to 366.
- Source/UI tests have no new failures; 21 failures were reproduced at base. Revised G3/G6 and the release/package gate are not per-ticket requirements.

facts:
- `git merge codex/public-beta-roi`: already up to date. Start HEAD and
  `git merge-base HEAD codex/public-beta-roi`: `2387237a8012432bcdf5078803ecfdce795f6129` (base).
- Implementation commits: `d2320a87` (split/dead code), `c83c8fdf` (constants/helper placement).
  No MAIN writes, worker rebuilds, release/ledger edits, push, stash, or history rewrite.
- Five includes preserve textual definition order and a single translation unit.
  Main retains params/UI, Classic/Smart entry, staging and dispatch. Existing
  fuzz adapters and Xcode source lists require no changes. Pixel normalization
  and stores now accompany composition. Scalar/vector and per-depth differences
  remain documented and separate. No ambiguous decompiler-style identifiers were
  found to rename; numeric iteration variables retain their meanings.
- Removed `reflect101` (9 code lines), `ShadeCtx` (4), and
  `DGPreRenderData`/`DeleteDGPreRenderData` (8): repository symbol search found
  no call sites/uses beyond these declarations. Retained PF8/PF16 preseed helpers
  because historical harnesses call them. No experiment branches or `#if 0`
  blocks were found. `OLM_REFERENCE_BUILD` and parallel controls are unchanged.
- Named constants include `kScalarExpTiny`, `kScalarLog2Scale`,
  `kScalarRoundBias`, `kScalarExpQuadratic`, `kScalarExpLinear`, `kVectorLog2E`,
  `kVectorRoundBias`, `kVectorLn2High/Low`, `kVectorExpC1` through `C5`,
  `kBilateralExpCutoff`, `kMaskRoundThreshold`, `kInt32Overflow`,
  `kOwnershipCutoff`, `kNativeUcrtPowerInput`, and `kGlobalOutFlags/2`.
  Existing exp table, indefinite NaN bits and native UCRT result bits became
  constexpr. Hex representations, floating widths, polynomial order and
  noncontracting products are preserved. Comments identify the existing IPP/AEX
  provenance and sensitive scalar/vector rounding order.
- Size count strips C/C++ block/line comments and blank lines from top-level
  `.cpp`, `.h`, `.inc`, `.r` files. Non-comment nonblank total: **2,384 → 2,384**.
  The previous attempt's reported 2,484 total was an arithmetic error.

| File | Before physical / code | After physical / code |
| --- | ---: | ---: |
| OLMDistanceGradation.cpp | 2651 / 2205 | 785 / 665 |
| DistanceFilters.inc | — | 406 / 341 |
| BilateralFilters.inc | — | 341 / 293 |
| DistanceField.inc | — | 399 / 313 |
| PixelCompose.inc | — | 489 / 398 |
| Admission.inc | — | 234 / 195 |
| OLMDistanceGradation.h | 110 / 95 | 110 / 95 |
| OLMDistanceGradationPiPL.r | 33 / 31 | 33 / 31 |
| OLMDistanceGradation_Strings.cpp | 33 / 30 | 33 / 30 |
| OLMDistanceGradation_Strings.h | 24 / 23 | 24 / 23 |

- G1 structural command: native_diff invocation below with `--head WORKTREE`
  and scratch `g1-structure`, run after the split/dead-code step.
  Exit 0: 12,012 comparisons, 11,912 exact renders, 100 identical refusals,
  zero differences/new refusals/execution errors; first mismatch: none.
  Each architecture/build: 3,003 comparisons = 2,978 exact + 25 refusals.
  Summary SHA256: `77234f82bf0c042848f20ca0a9ebbc39281122a250dc51fd3be8676dfd336ad4`.
- G1 final: same command with scratch `g1-final`, after the constants/helper
  changes; exit 0. **12,012 comparisons, 11,912 exact renders, 100 identical
  refusals; zero differences, new refusals or execution errors. First mismatch:
  none.** Each of arm64/reference, arm64/fast, x86_64/reference, x86_64/fast
  has 3,003 comparisons (2,978 exact + 25 identical refusals).
  Each depth has 4,004 comparisons; 12 full 4K comparisons, 6,004 odd/even
  samplings; default/realistic-v1/realistic-v2 geometry 4,020/3,996/3,996.
  Summary SHA256: `c85b174b2c36339d36b4261e98f0ddaf2997ccf041edc9c3e501099012b7f315`.
  Final comment attachment/whitespace cleanup was checked to leave every
  non-comment token unchanged in the three affected includes.
- G2 corpora: normal 147, P04a 72 (`--max-size 64`), realistic_P02b 226;
  N02 contains zero JSON witnesses. Base full oracle replay: 445/445 matches_saved.
  Head full oracle replay: 445/445 matches_saved (all three commands exit 0). Mac-only replay of both routes:
  890/890 rendered results equal, 890 saved Mac hashes match on each side,
  zero refusals, zero refusal-tag differences, zero result differences.
  Identical Mac JSONL SHA256 on both sides:
  `ac131de74c2f84b617ba7c8b571592f7611c84636b3b7e9a33ab4a5044ab3ef9`.
  Corpus workers/timeouts were retained; no worker override. Oracle diagnostics
  and budget timing are not used to excuse any Mac-side difference.
- G4: clean Release Xcode Universal builds at base/head both exit 0. Initial
  base attempt lacked untracked SDK links (`AEConfig.h` missing); fixed only
  scratch setup with read-only links to MAIN's Headers/Resources/Util, then
  reran clean builds on both sides. Both arm64 and x86_64 compile/link.
- G4 UI: `tests/ui_oracle/compare_mac.py` exits 0 at both revisions;
  DistanceGradation 3 update rows, 6 checks including reload, 0 mismatches.
- G4 source/host tests below: base **23 passed / 21 failed**; head **23 passed /
  21 failed**. The failure-name lists are identical. Both transactional tests
  and the DistanceGradation decomp/PiPL test pass. Source readers follow moved
  includes; the PiPL test resolves named constants then applies the unchanged
  flag-value comparison. No assertion was removed or relaxed.
- G5: warning occurrences **370 → 366**, zero new warning messages.
  Removed: unused `reflect101` twice and unused `DeleteDGPreRenderData` twice.
  Existing SDK pack, conversion, macro and build-system warnings remain.
- `git diff --check`: exit 0. Completed source snapshots, Xcode trees, native
  binaries, Python environment and package cache were removed; logs, summary
  reports and compact result records remain in ticket scratch. All started
  build/replay processes finished; no background job was retained.

Existing test failures (not fixed):
- Public Smart owner contract: 17 tests fail because the historical executable
  `/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker`
  is absent. Tests: `test_alpha_bits_tamper`, `test_boundary_tamper`,
  `test_chain_tamper`, `test_color_suite_tamper`, `test_exception_cleanup_tamper`,
  `test_field_word_tamper`, `test_lifecycle_tamper`, `test_matrix_one_away`,
  `test_mode5_public_count_tamper`, `test_power_fail_closed_count_tamper`,
  `test_power_oracle_tamper`, `test_public_selector_tamper`, `test_report`,
  `test_selector_tamper`, `test_validate_only`, `test_worker_build_revision_tamper`,
  `test_worker_checkout_tamper`.
- PF16 capture: `test_pf16_instrumentation_is_env_gated_and_logging_only`:
  `ValueError: substring not found` while seeking the old `dst[i].blue  = db;`.
- Classic dispatch: `test_classic_render_dispatch`: expected
  `world_suite->PF_GetPixelFormat(input, &format)` is absent at base/head.
- Generic production beta: `test_depths_geometry_strides_params_padding_and_overflow`
  returns 46; `test_oracle_profile_under_address_and_undefined_sanitizers`
  returns 75, at both revisions.

inference:
- The measured refactor equivalence supports these structural/name changes;
  it is not a new claim of Windows AE exactness or a repair of existing behavior.
- Possible latent issues deliberately unchanged: DistanceRefusal passes
  snprintf's would-have-written length to write without bounding it to the
  384-byte buffer (a future sufficiently long tag/function could over-read).
  edt_sep describes floor division although C++ signed division truncates
  toward zero. Neither was diagnosed as a current output mismatch here.
- The existing admitted PF32 Power input/output bit override
  `0x3f4d07a5 → 0x3f1b5786` remains unchanged and may merit a separate provenance
  review. Older Layer/no-bg heuristics and their conformance comments were not
  retuned. Known baseline test failures warrant separate maintenance work.

changed_files:
- mac/OLMDistanceGradation/OLMDistanceGradation.cpp
- mac/OLMDistanceGradation/DistanceFilters.inc
- mac/OLMDistanceGradation/BilateralFilters.inc
- mac/OLMDistanceGradation/DistanceField.inc
- mac/OLMDistanceGradation/PixelCompose.inc
- mac/OLMDistanceGradation/Admission.inc
- tests/test_olmdistancegradation_pf16_boundary_capture_integration_20260728.py
- tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py
- tests/test_olmdistancegradation_public_smart_owner_contract_20260812.py
- tests/refs/conformance/test_binary_contracts.py (DistanceGradation only)
- orchestra/reports/Q05-refactor-olmdistancegradation.md

verify:
Run from this worktree; all scratch and TMPDIR stay below the ticket directory.
Commands below reproduce the measured gates. The prebuilt original workers
remain at their corpus-recorded absolute paths.

```sh
S="$PWD/orchestra/state/Q05-refactor-olmdistancegradation/recheck"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
BASE=2387237a8012432bcdf5078803ecfdce795f6129
mkdir -p "$S"
export TMPDIR="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 tools/refactor/native_diff.py --plugin olmdistancegradation \
  --base "$BASE" --head HEAD --cases 3000 --seed 909 \
  --arch both --build both --jobs 1 --scratch "$S/g1" > "$S/g1.log" 2>&1
```
Expected G1: exit 0, 12,012 comparisons, 11,912 exact, 100 identical refusals,
0 differences, 0 new refusals, 0 execution errors.

Prepare isolated source trees for the remaining gates (no MAIN modification):
```sh
for side in base head; do
  rev="$BASE"
  if [ "$side" = head ]; then rev=HEAD; fi
  mkdir -p "$S/$side"
  git archive "$rev" | tar -x -C "$S/$side"
  for asset in Headers Resources Util decomp; do
    ln -s "$MAIN/$asset" "$S/$side/$asset"
  done
done
python3 -m venv "$S/venv"
PIP_CACHE_DIR="$S/pip-cache" "$S/venv/bin/pip" install pytest pillow numpy > "$S/pip.log" 2>&1
```
G2, exact recorded flags (run all three at both revisions):
```sh
for side in base head; do
  tree="$S/$side"
  for corpus in olmdistancegradation olmdistancegradation_P04a olmdistancegradation_realistic_P02b; do
    size=256
    if [ "$corpus" = olmdistancegradation_P04a ]; then size=64; fi
    out="$tree/orchestra/state/Q05-refactor-olmdistancegradation/$corpus"
    python3 "$tree/tools/fuzz/run.py" --plugin olmdistancegradation \
      --replay "$PWD/tests/fuzz_corpus/$corpus" --max-size "$size" \
      --jobs 1 --budget-minutes 45 --main "$MAIN" --scratch "$out" \
      --report "$out.json" --corpus "$out/witnesses" > "$S/$side-$corpus.log" 2>&1
  done
done
```
Expected: complete 147/72/226 at each revision. Compare `replays[].result.routes`
by witness; all Mac hashes/pass-fail outcomes should match. Full replay exit 0
was observed; oracle-only diagnostic differences are outside this gate.

Supplemental Mac-only hash/refusal-tag replay (uses the shared adapter and corpus
loader, with a 180-second per-case ceiling; the recorded-timeout full replay above
remains the G2 replay). No standalone probe script is committed.
```sh
cat > "$S/replay_mac.py" <<'PYMAC'
import sys,json,time,re,hashlib,os
from pathlib import Path
from types import SimpleNamespace
root,corpora,scratch=map(lambda x:Path(x).resolve(),sys.argv[1:4]);sys.path.insert(0,str(root/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import load_corpus,sha
scratch.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),worker=Path('/unused'),max_size=256,case_timeout=180))
a.env.update(TMPDIR=str(scratch),OLM_PARALLEL_MAX='1');deadline=time.monotonic()+3600
a.binary,_=a.build(scratch,deadline)
with (scratch/'mac.jsonl').open('w') as out:
 for folder in sorted(corpora.glob('*distancegradation*')):
  for path in sorted(folder.glob('*.json')):
   saved=json.loads(path.read_text());a.max_size=saved['max_size'];case,_=load_corpus(path,a)
   for route in a.routes:
    result,raw,tags=a.candidate(case,scratch,route,deadline)
    record=dict(corpus=folder.name,witness=path.name,route=route,result=result,sha256=sha(raw),tags=[re.sub(r'@\d+$','',v) for v in tags])
    record['matches_saved_mac_hash']=record['sha256']==saved['result']['routes'][route].get('raw_sha256') if result['status']=='ok' else None
    out.write(json.dumps(record)+'\n');out.flush()
print('completed',flush=True)
PYMAC
for side in base head; do
  python3 -B "$S/replay_mac.py" "$S/$side" "$PWD/tests/fuzz_corpus" \
    "$S/mac-$side" > "$S/mac-$side.log" 2>&1
done
cmp "$S/mac-base/mac.jsonl" "$S/mac-head/mac.jsonl"
```
Expected: cmp exit 0; 890 identical records, every saved Mac hash matches,
all refusal-tag lists empty. The JSONL hash is recorded above.

G4/G5 (retain logs and compare compiler warning messages/counts):
```sh
for side in base head; do
  tree="$S/$side"
  xcodebuild -project "$tree/mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj" \
    -configuration Release -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
    CODE_SIGNING_ALLOWED=NO SYMROOT="$S/xcode-$side/products" \
    OBJROOT="$S/xcode-$side/objects" clean build > "$S/xcode-$side.log" 2>&1
  python3 -B "$tree/tests/ui_oracle/compare_mac.py" \
    --scratch "$S/ui-$side" > "$S/ui-$side.log" 2>&1
  "$S/venv/bin/python" -m pytest -q -p no:cacheprovider \
    "$tree/tests/test_olmdistancegradation_update_params_ui_20260810.py" \
    "$tree/tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py" \
    "$tree/tests/test_olmdistancegradation_public_smart_owner_contract_20260812.py" \
    "$tree/tests/test_olmdistancegradation_pf16_boundary_capture_integration_20260728.py" \
    "$tree/tests/test_olmdg_toondilate_classic_render_bitdepth_dispatch_20260716.py" \
    "$tree/tests/test_olmdistancegradation_smart_transactional_20260822.py" \
    "$tree/tests/test_olmdistancegradation_generic_production_beta_20260820.py" \
    "$tree/tests/refs/conformance/test_binary_contracts.py::TestDistanceGradation" \
    > "$S/tests-$side.log" 2>&1
done
```
Expected: Xcode/UI exit 0; UI DistanceGradation 6/6; warnings 370/366 with no
new warnings. Pytest exits 1 at both revisions with 23 passed and the same 21
failures listed above.

next:
- No required ticket work remains; ready for orchestrator review/merge.
- Orchestrator owns the final release gate and packaging after the Q-series.
- Follow-up separately: repair stale test assumptions/worker paths and investigate
  existing generic-test exits 46/75; do not change render behavior in this ticket.
