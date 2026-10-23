status: done
summary:
- Routed legacy harness compiler recipes through the shared UCRT launcher; production code, assertions, expected bytes and evidence bindings are unchanged.
- All 93 I03 class-(a) commands now compile/link: 386 successful link invocations, zero compiler/linker failures.
- Their outcomes are 60 pass, 18 numeric failure, 13 runtime/contract failure and two stale installed bindings.
- Including the mixed performance entry, F20 and three parameter-UI audits: 98 commands, 394 successful links, 64 pass; every non-pass is retained and classified.

facts:

Starting revision: `f40209b85623dfeef32b650fa1d004f5c857ef99`. Work is confined to branch `orch/R03-harness-ucrt-link`.

Implementation:

- 443 Python compiler command sites and four shell compiler command sites use `tools/ucrt_cxx.py`. The archive is built with the existing `ucrtmath/build.sh`, just as the fuzz adapter does; no math implementation or build flags in that library changed.
- The shared launcher preserves explicit compiler selections (`--compiler`), the SDK environment of `xcrun clang++` (`--xcrun`), caller flags and multiple `-arch` selections. Compile/preprocess/assembly-only commands do not link an archive. Optional `OLM_UCRT_LINK_LOG` records the actual compiler argv and exit status.
- Three architecture-switch string anchors follow the renamed launcher; these are compiler-recipe anchors, not evidence/hash bindings. F20's SDK-path interceptor recognizes the launcher as well as `clang++`.
- `python3 -B orchestra/reports/R03-audit-recipes.py`: **443 command argument tails checked, zero problems**. The audit also checks that Python assert statements and assertion method calls in those modules are unchanged. `git diff --check` passes.
- The committed `R03-link-smoke.cpp` builds a Universal executable through `--xcrun`. `lipo -archs` reports `x86_64 arm64`; both native execution and `arch -x86_64` exit 0. It references float exp/pow/atan2 and double sin/cos/pow, covering the missing-symbol families. This is a link/dispatch smoke test, not a new all-input math-equivalence claim.

Verification commands executed:

- `bash scripts/setup_ae_sdk_links.sh` — succeeds, creating only worktree SDK links.
- `python3 -B orchestra/reports/R03-rerun.py` — completes the 93 classified commands plus five explicit related checks, in sequence with `OLM_TEST_JOBS=2`, MAIN's absolute-path emulator Python/assets and ticket-local temporary directories.
- `python3 -B orchestra/reports/R03-rerun.py --only 6` — succeeds. The initial fixture-068 invocation preceded migration of its `xcrun` recipe; the final invocation links and passes. The initial log/results are retained separately and are not counted as final outcomes.
- `R03-probe-failure.py` observed ColorKey's hidden child output and Radial fixture-152's assertion locals without changing assertions. `R03-first-differences.py` ran first failing cells for indices `39 41 42 43 44 45 55 56`; all eight diagnostic invocations exit 0 (successful capture, not matching pixels).
- No reference worker was rebuilt, no AE bundle was installed and no MAIN file was edited. Legacy generators' changed conformance reports are saved in the evidence archive and restored to their original bytes. No release gate or ledger was edited.

`R03-results.json` contains **every exact command**, final return code, elapsed time, successful link count, outcome and diagnostic/evidence paths. `R03-evidence.tar.gz` contains the logs, all compiler argv/exit records, generated reports and supplemental diagnostics. `R03-artifact-manifest.json` records the archive and member hashes. Authoritative final counts:

| Commands | Pass | Numeric failure | Runtime/contract failure | Stale binding | Successful links |
|---|---:|---:|---:|---:|---:|
| 71 I03 fixture records | 43 | 18 | 8 | 2 | 357 |
| 22 I03 generic entries | 17 | 0 | 5 | 0 | 29 |
| Mixed performance entry + F20 + 3 parameter-UI audits | 4 | 0 | 0 | 1 | 8 |
| Total | 64 | 18 | 13 | 3 | 394 |

Every command has at least one recorded successful link with `libucrtmath.a`; there are **zero failed compiler/linker invocations** in the final records. F20 and Directional/Distance/Radial parameter-UI audits all pass. All three Smoother2 generic entries (default, gamma/colors, ROI) pass.

Numeric findings, all RadialBlur:

The table identifies the first difference within the indicated required plane for a first failing cell. Byte offsets are zero-based; raw word pairs are little-endian bytes, AEX → production. The complete per-plane counts/hashes and all original per-cell reports are retained. A dash means the original report supplies the index/count, not a raw word pair; no word value has been inferred.

| Fixture record | First differing plane | First index | Raw word pair | Retained final output |
|---|---|---:|---|---|
| 152: size variation, value 1 | accum | byte 8 | `908ab23d` → `918ab23d` | differs |
| 153: noise type 1, NV 0 | accum | byte 8 | `908ab23d` → `918ab23d` | differs |
| 155: ellipse 9×7, ratio 2 / angle 0 | accum | byte 8 | `908ab23d` → `918ab23d` | differs |
| 156: Rotation ellipse 32×18, ratio 2 / angle 0 | accum | byte 8 | `efb32a3f` → `f0b32a3f` | differs |
| 157: strength 5 / NV 25 | accum | byte 8 | `908ab23d` → `918ab23d` | differs |
| 158: offset mode 3 / offset 2 / NV 25 | accum | byte 8 | `908ab23d` → `918ab23d` | differs |
| 159: Zoom inner 50 / NV 0 | post_blur | byte 16 | `66ef123f` → `65ef123f` | differs |
| 165: case-0010 production planes | accum | value index 0 | — | exact |
| 167: Rotation PF16 small | accum | byte 8 | — | differs; first output byte 274 |
| 168: Rotation PF32 small | accum | byte 8 | — | differs; first output byte 4 |
| 169: outer edge fade 50 | prepass_alpha | byte 56 | `28f8773f` → `2af8773f` | differs |
| 170: outer fade 50 × size 50 | prepass_alpha | byte 56 | `28f8773f` → `2af8773f` | differs |
| 171: Rotation PF32 strength 5 | accum | byte 28960 | — | differs; first output byte 60 |
| 172: Rotation PF16 strength 5 | accum | byte 28960 | — | exact |
| 174: Zoom PF16 strength 5 | post_blur | byte 48 | — | exact |
| 178: Rotation PF32 offset UI 3 | accum | byte 76 | — | differs; first output byte 728 |
| 179: Rotation PF32 offset UI 4 | accum | byte 8 | — | differs; first output byte 36 |
| 181: Rotation PF16 offset UI 3 | accum | byte 76 | — | exact |

Fixture-152's first final-output difference is byte 4, `15b383ba` → `16b383ba`. Fixture-165 has 1,801,691 differing accumulation values (first index 0) and 95,441 differing normalized values (first index 541932), but zero differing final PF8 pixels/channels; final raw SHA-256 is `cb39306e0e340bfa121e5ea55c9e1b43f87696237b4d6c855a47ce09dba188fc`. These four internal-only failures remain failures of their stated plane comparisons.

Fixtures 157, 158 and 159 also fail rejection expectations (`strength5_nv50`/`strength6_nv25`, `offset5_nv25`/`offset2_nv50`, and `inner50_noise50`, respectively). They are classified as numeric failures because they also contain measured required-plane differences.

Runtime/contract findings (no pixel mismatch asserted from an exit code alone):

| Record | First observed diagnostic |
|---|---|
| fixture-047, ColorKey source-bound atomic | probe exit 3; `pass=0 positives=0 negatives=0`. Captured first 2304-byte output matches the retained SHA-256 `2b05dfeed6c1385d4818cd727aabc6931581b6d39ce22f84a13461b91a33e740`. |
| fixture-063 and generic Directional cleanup | rc=134: `budget err=-3 alloc=1 output=1 layer=2 out=1 checkin=1 pc=21 pi=21` |
| fixture-083, Directional SmartRender adapter | exit 38: `layer3 err=-1 exact=0 visible=0 pad=1` |
| fixture-126, Kira mode-3 fail-close | child exit 1: `PF8=10 PF16=10 PF32=10` |
| fixture-162, Radial unsupported variation | probe exit 1 |
| fixture-163, Radial unproven geometry | nonzero executable status; `r.returncode == 0` assertion fails |
| fixture-164, Radial case-0009 replay | probe exit 3: render returns nonzero before output comparison |
| fixture-184, Radial type-3 host plumbing | mock exit 10 at SmartPreRender/event expectation |
| generic Directional back-only EffectMain | rc=10; `FAIL code=1568 line=704`, then `FAIL code=10 line=808` |
| generic Distance production beta | normal and sanitizer probes exit 75 (`pf32_blurred_budget_rejects` expectation) |
| generic Kira mode-3 UI length | length 0 rejection reports `ok=0` at depths 8/16/32; length 301 reports `ok=1`; three failed tests |
| generic Radial baseline | probe exit 38 |

Stale bindings:

- Fixture-134: installed Kira executable hash differs from its pinned manifest; source harness links successfully.
- Fixture-183: all compared Zoom PF32 planes/output, padding and fixture hashes match; then installed Radial identity validation fails.
- Extra mixed performance entry: executable-prefix and `OLMDistanceGradation/uhd` command bindings fail; its two compiler invocations now succeed. Exact actual/expected hashes and exception text are in `R03-results.json` and the logs.

inference:

The missing-link-input cause is repaired throughout the inventoried executable recipes. The observed downstream failures are now visible rather than masked by linking errors. The contract failures are candidates for assertion/admission review; this ticket does not prove a historical cause for each one. Likewise, the Radial numeric differences are measurements against the legacy fixtures' AEX path, not proof of a universal production regression or a license to tune bytes. No exactness claim extends beyond the recorded cells. Four numeric failures have matching final output but differing internal planes.

changed_files:

- Full path list: `orchestra/reports/R03-changed-files.txt`.
- `tools/ucrt_cxx.py`: shared compiler launcher options, compile-only handling and optional link audit log.
- Harness recipes in `tests/`, `tools/emulation/`, `tools/fuzz/`, `tools/perf/` and `refs/scripts/`: mechanical launcher routing; SDK interception/architecture anchors where necessary. No production source or library implementation changes.
- `orchestra/reports/R03-{rerun,probe-failure,first-differences,audit-recipes,summarize}.py`, `R03-link-smoke.cpp`: reproducible verification and diagnostics.
- This report, `R03-results.json`, `R03-evidence.tar.gz`, `R03-artifact-manifest.json`, `R03-changed-files.txt`: retained results.

verify:

Fast static/argument verification from the worktree root:

```sh
python3 -B orchestra/reports/R03-audit-recipes.py
git diff --check
```

Expected: `Checked 443 compiler command tails; problems: []`; no whitespace errors.

Archive-integrity and result verification (no rebuild):

```sh
python3 - <<'PY'
import hashlib,json,tarfile
from pathlib import Path
p=Path('orchestra/reports')
m=json.loads((p/'R03-artifact-manifest.json').read_text())
assert hashlib.sha256((p/m['archive']).read_bytes()).hexdigest()==m['sha256']
with tarfile.open(p/m['archive']) as t:
    assert len(t.getmembers())==len(m['files'])
    for r in m['files']:
        assert hashlib.sha256(t.extractfile(r['path']).read()).hexdigest()==r['sha256']
r=json.loads((p/'R03-results.json').read_text())
assert len(r['results'])==98 and r['class_a_links']==386 and r['all_links']==394
assert all(x['links']>0 and x['link_failures']==0 for x in r['results'])
assert r['class_a_counts']=={'pass':60,'numeric failure':18,'runtime/contract failure':13,'stale binding':2}
print('R03 evidence integrity OK; 93/93 class-(a) commands link')
PY
```

Universal link smoke, including both slices:

```sh
export TMPDIR="$PWD/orchestra/state/R03-harness-ucrt-link"
mkdir -p "$TMPDIR"
tools/ucrt_cxx.py --xcrun -std=c++17 -arch arm64 -arch x86_64 -I. \
  orchestra/reports/R03-link-smoke.cpp -o "$TMPDIR/link-smoke"
lipo -archs "$TMPDIR/link-smoke"
"$TMPDIR/link-smoke"
arch -x86_64 "$TMPDIR/link-smoke"
```

Expected: both architectures, both executions exit 0. Delete the executable and its `link-smoke-ucrtmath` directory after use.

Full rerun (long, sequential stages; do not run the stages concurrently):

```sh
bash scripts/setup_ae_sdk_links.sh
python3 -B orchestra/reports/R03-rerun.py
export TMPDIR="$PWD/orchestra/state/R03-harness-ucrt-link"
export TMP="$TMPDIR" TEMP="$TMPDIR" OLM_TEST_JOBS=2 PYTHONDONTWRITEBYTECODE=1
export OLM_MAIN_ASSETS="/Users/onmk/Documents/Projects/Personal/OLM as"
for r03_index in 39 41 42 43 44 45 55 56; do
  "$OLM_MAIN_ASSETS/tools/emulation/.venv/bin/python3" -B \
    orchestra/reports/R03-first-differences.py "$r03_index" \
    > "$TMPDIR/diagnostic-$r03_index.log" 2>&1
done
R03_DIAGNOSTICS="$TMPDIR/diagnostics/38" \
  "$OLM_MAIN_ASSETS/tools/emulation/.venv/bin/python3" -B \
  orchestra/reports/R03-probe-failure.py \
  tools/emulation/test_olmradialblur_rotation_pf32_size_variation_opaque_actual_aex_20260810.py \
  > "$TMPDIR/observed-038.log" 2>&1
python3 -B orchestra/reports/R03-summarize.py
```

Expected on this source/environment: all 98 commands compile/link, outcomes above. The observed fixture-152 invocation deliberately exits 1 on its unchanged numeric assertion; the eight supplemental capture helpers exit 0. Summarizer exit 0 means complete classification/evidence, not passing child tests. Installed-binding results depend on the external installed bundles. The rerun writes evidence under the ticket scratch and restores generated pinned reports; begin with clean `refs/conformance/`.

next:

R04/R05 or follow-up owners should adjudicate the 13 runtime/admission assertions and three stale bindings. Assign a separate numeric ticket for the 18 Radial fixtures, using the saved first differences and existing AEX/reference-worker provenance to distinguish math-mode/reference-path differences from production defects. Re-run the wider release gate after those owners resolve their findings. This ticket neither repins evidence nor changes production pixels.
