status: partial
summary:
- Consolidated typed input packing for all six routes and output unpacking for five; retained the PF16 non-Legacy observed-store loop verbatim.
- Simplified redundant small-world predicates, reused shared checked multiplication, and removed a provably redundant Classic overflow check.
- Plugin non-comment/nonblank lines: 1,456 -> 1,365 (-91). Universal Debug warnings: 352 -> 338.
- Production fixture admissions and diagnostic hooks remain: they affect callback, padding, and observation behavior and are not unused test code.
- G4 is not green: two source-text assertions need updates outside this ticket's source scope; one Classic-dispatch assertion already fails at base.

facts:
- Baseline: `62a470a98bb4dce1c9a371209f0d0261a1840580`. First structural commit: `8908b34f`.
- Intermediate G1, seed 909, arm64/reference+fast, 500 small + 3 UHD per build: 1,006 exact comparisons; zero differences/new refusals/execution errors.
- An attempted final run was interrupted after 5,219 exact comparisons (zero differences/errors) when a build warning exposed a missing diagnostic call in the first refactor. Those counts are not final validation. The entire original observed-store loop was restored before the completed final run.
- Final G1 (seed 909), both arm64/x86_64 and reference/fast: 3,000 small + 3 UHD cases per combination, **12,012 exact comparisons**, **0 differences, 0 new refusals, 0 execution errors**; first mismatch: none. Final source was frozen throughout this completed run. Summary SHA256: `a0331e1fb59d67104c4b92a81d77387fd6078b04797326b6445c4a3787430911`.
- G2: all recorded OLMBlur corpora, recorded samplers/geometry/timeouts, both native routes: 278 observations per side, identical result dictionaries, raw output hashes, and refusal tags (line suffixes ignored). Base/final JSONL SHA256: `2d09cf9d211fb697a56125cfedf3f670f4751d039b04b0b2cc206347faa7c5ac`. First mismatch: none. No oracle runs or changes.
- G4 builds: base and final Xcode Debug builds succeeded with arm64+x86_64 and `-jobs 1`. Total warning occurrences 352 -> 338, including two unchanged build-system warnings; compiler warnings 350 -> 336. Seven logical-op-parentheses warnings per architecture were eliminated; no arithmetic type or precedence changed.
- UI oracle: Blur 4/4 checks, all-plugin shared runner 240/240 checks, zero mismatches. UI source is unchanged by the later diagnostic restoration.
- Final `tests/test_olmblur_generic_beta_sanitizers_20260820.py` exited 0 (both normal and ASan/UBSan probe executions).
- Text tests: Generic Classic 3/3 pass; ROI/halo five function tests pass. Generic Beta 4/4 pass at base, 2/4 pass at final: `test_geometry_representation_and_control_limits_are_explicit` expects the old inline multiplication guard, and `test_exact_small_fixtures_remain_owned_by_exact_lane` expects the redundant four-boolean expression. Tests were not modified or bypassed.
- Classic dispatch text test errors identically at base and final: `ValueError: substring not found` at line 36, looking for a literal `return PF_Err_BAD_CALLBACK_PARAM;` where the existing source uses `OLM_BLUR_REFUSAL`. This inherited failure is separate from the two new text failures.
- MAIN venv lacks pytest (`No module named pytest`); unittest modules and module-level ROI functions were invoked directly instead.
- Cleanup: all owned verification processes exited; Xcode build trees, native build directories/source snapshots, and ticket-created SDK links were removed. No executable files remain in scratch; logs/reports total 28 MiB.
- Release gate was not run, per ticket instruction. No MAIN, other-plugin, release-gate, or ledger changes; no emulator rebuilds, installation, or push.

inference:
- After the existing legacy-domain check, `radius_small || legacy_small` is true for every supported depth. The other two small-world predicates cannot change admission. The simplified unsupported-depth refusal retains the same tag and ordering.
- Classic width/height bounds (4096/2160) make multiplication representable on both supported 64-bit architectures, so the preceding overflow check was redundant. Its pixel-count limit remains.
- Generic world/tuple multiplication uses the existing `olm::world_safety::checked_multiply`; TightStaging already owns layout/disjointness admission. Shared headers needed no changes.
- `OLMBlur_Fixtures.inc` is live production admission, not a test fixture compilation accident. Exact owners copy row padding and use PF_COPY without the generic checkin/staging lifecycle. Removing or test-gating it would change behavior even if random raw-pixel G1 cases stayed equal. No standalone test entry points are compiled into this plugin. The retained environment-controlled PF16 observation is also a diagnostic contract, not an unused fixture.
- Numeric kernels, FP evaluation order, arithmetic types, reference/fast split, and OLM_PARALLEL_MAX remain unchanged. Finite native comparisons establish equality for measured witnesses, not universal AE exactness.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp`: admission simplification/shared multiplication, warning parentheses.
- `mac/OLMBlur/OLMBlur_Workers.inc`: typed packing/unpacking templates, with observed PF16 unpack retained.
- `orchestra/reports/C02-cleanup-olmblur.md`: this report.

Non-comment/nonblank line counts (strip block comments, line comments, then blank lines):

| File | Before | After |
|---|---:|---:|
| OLMBlur.cpp | 746 | 738 |
| OLMBlur_Workers.inc | 394 | 311 |
| OLMBlur_Fixtures.inc | 220 | 220 |
| OLMBlur.h | 63 | 63 |
| OLMBlur_Strings.cpp | 20 | 20 |
| OLMBlur_Strings.h | 13 | 13 |
| Total | 1456 | 1365 |

No constants were added or retuned; all source files remain below 1,000 physical lines.

verify:
Run from this worktree at its final commit, using a fresh scratch directory:

```sh
ROOT="$PWD"
BASE=62a470a98bb4dce1c9a371209f0d0261a1840580
S="$ROOT/orchestra/state/C02-cleanup-olmblur/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
scripts/setup_ae_sdk_links.sh > "$S/sdk.log" 2>&1
python3 tools/refactor/native_diff.py --plugin olmblur --base "$BASE" \
  --cases 3000 --arch both --build both --jobs 1 --scratch "$S/G1" > "$S/G1.log" 2>&1
python3 -B tests/ui_oracle/compare_mac.py --scratch "$S/ui" > "$S/ui.log" 2>&1
python3 -B tests/test_olmblur_generic_beta_sanitizers_20260820.py > "$S/sanitizers.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmblur_generic_classic_beta_20260822.py' > "$S/text-classic.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmblur_generic_beta_lane_20260820.py' > "$S/text-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmblur_colorkey_classic_render_bitdepth_dispatch_20260716.py' > "$S/text-dispatch.log" 2>&1
```

Expected: G1 12,012 exact comparisons, zero differences/new refusals/execution errors; UI zero mismatches; sanitizer exit 0; Classic text 3 pass; Beta text 2 pass/2 failures; inherited dispatch error as above. The last two commands intentionally document outstanding failures, not passing gates.

G2 uses the already committed C01 report's native-only replay recipe (extract it unchanged), with only this plugin selected:

```sh
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$ROOT/$name" "$S/base/$name"; done
python3 - "$S/replay_native.py" <<'PY'
from pathlib import Path
import sys
report=Path('orchestra/reports/C01-cleanup-shared-math-and-tests.md').read_text()
script=report.split("<<'PY_NATIVE'\n",1)[1].split('\nPY_NATIVE',1)[0]
Path(sys.argv[1]).write_text(script)
PY
for side in base head; do
  TREE="$ROOT"
  if [ "$side" = base ]; then TREE="$S/base"; fi
  python3 -B "$S/replay_native.py" "$TREE" "$ROOT/tests/fuzz_corpus" "$S/G2-$side.jsonl" olmblur > "$S/G2-$side.log" 2>&1
  OUT="$S/xcode-$side"
  xcodebuild -project "$TREE/mac/OLMBlur/Mac/OLMBlur.xcodeproj" \
    -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
    MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$OUT/objects" \
    SHARED_PRECOMPS_DIR="$OUT/pch" CONFIGURATION_BUILD_DIR="$OUT/products" \
    build > "$S/xcode-$side.log" 2>&1
  rm -rf "$OUT"
done
cmp "$S/G2-base.jsonl" "$S/G2-head.jsonl"
```

Expected: cmp exit 0, 278 records each and the SHA256 above; both Xcode builds succeed, 352/338 warning occurrences. Run the five ROI functions directly (they are plain functions, not unittest cases):

```sh
python3 - <<'PY'
from pathlib import Path
p=Path('tests/test_olmblur_roi_halo_contract_20260820.py').resolve()
ns={'__file__':str(p)}
exec(compile(p.read_text(),str(p),'exec'),ns)
for name,fn in list(ns.items()):
    if name.startswith('test_') and callable(fn):
        fn()
        print(name,'PASS')
PY
```

next:
- Authorize a scoped test-maintenance follow-up for the two Generic Beta source assertions: validate the simplified admission and shared overflow contract without preserving obsolete implementation strings. Repair the inherited Classic-dispatch literal-return assertion separately or in that follow-up. Until then, G4 remains incomplete and this ticket is partial.
- Keep the live exact-fixture/diagnostic contracts unless a separate behavioral change is authorized and callback/padding/observation boundaries are verified. No further numeric-kernel refactor is proposed here.
- Orchestrator owns release-gate execution after all C02 tickets.
