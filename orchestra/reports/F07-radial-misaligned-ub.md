status: partial

summary:
- Replaced RadialBlur world pixel dereferences with byte-addressed memcpy loads/stores through aligned locals; no arithmetic or admission guards changed.
- Current default baseline: 15 UBSan route rows; patched default: 0/1,000. T05's historical count was 35, not the current baseline count.
- Production seed-1 campaign: all 600 candidate route statuses, hashes and diff records unchanged; exact counts remain Classic 1, Smart 148.
- Retained corpus replay: 35/35 matches_saved, also 35/35 under ASan/UBSan with no diagnostics. Two existing fast plugin tests pass.
- Alignment goal is complete; status is partial because the brief also requires numerical exactness of target clusters, while pre-existing mismatches remain unchanged.

facts:
- Base revision: `0e3481cbba7c9b63e3c23480d8abb081fe03733f`. Changes are confined to this ticket's worktree. Read AGENT_GUIDE.md, the RadialBlur ledger entries, compatibility plan, emulation GOTCHAS, T05 report and KiraKira memcpy precedent.
- Root cause: `PixelAtConst` and `PixelAt` constructed typed addresses from byte strides. Odd row padding makes subsequent rows misaligned. References were bound before traits calls, including admission probes before refusal. The fix also covers direct row casts and noise-layer reads, leaving the original alignment admission checks intact.
- Static original-AEX evidence (read-only MAIN): `decomp/OLMRadialBlur.aex.c.txt:14488` / `disasm/OLMRadialBlur.aex.asm.txt:21249`: FUN_180017440 multiplies floats, CVTTSS2SI converts, then stores low words at ARGB offsets. FUN_180017490 (`:14508` / `:21265`) uses scalar MOVSS stores at offsets 4,12,8,0. The patch retains these conversions and channel values; it changes only the C++ memory access mechanism.
- Default production campaigns were run before and after the edit using the command below, with NAME=`before` and `after`. Both completed 300/300, exit 0. `--jobs 1` follows the brief's machine-limit rule, overriding the acceptance example's `--jobs 2`.

```sh
python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 1 --budget-minutes 30 --corpus orchestra/state/F07-radial-misaligned-ub/NAME-corpus --scratch orchestra/state/F07-radial-misaligned-ub/NAME-scratch --report orchestra/state/F07-radial-misaligned-ub/NAME.json
```

| Route / measure | Before | After |
|---|---:|---:|
| Classic exact | 1 | 1 |
| Classic mismatch | 118 | 118 |
| Classic refusal | 181 | 181 |
| Smart exact | 148 | 148 |
| Smart mismatch | 92 | 92 |
| Smart refusal | 59 | 59 |
| Smart uncompared | 1 | 1 |
| Candidate status/hash/diff changed rows | — | 0 / 600 |
| AEX Smart timeout/budget | 4 | 5 |
| AEX Smart reject | 20 | 20 |
| Retained corpus matches_saved | 35 saved cases | 35 / 35 |
| Corpus files modified | 0 | 0 |

- The extra AEX timeout affected a candidate refusal, not an exact count or output comparison. No generated scratch corpus was promoted.
- Fresh sanitizer runs use the same generator seed 1, indices 0..499, both routes, default guards, ASan/UBSan and original source revision versus patched source. Each has 592 successful candidate renders and 408 refusals. Baseline UB appears on Classic indices 109,123,127,138,173,193,257,298,302,316,349,380,418,425,434. First diagnostic: baseline line 1780:5, reference binding to misaligned PF_PixelFloat (requires 4-byte alignment). Other observed sites: 2679:46,2693:43,3174:88,3580:6. After: zero sanitizer rows. All 1,000 statuses, raw hashes and stable refusal tags match.
- The checker initially failed on 389 refusal traces solely because their `@source_line` suffixes moved. Verified zero status/hash/intermediate-trace differences, then changed the checker to compare stable refusal tags and reran. This is a measurement correction, not a production change.
- Production intermediate debug traces at (0,0)/(0,1) for cases 193 and 425 match before/after on both routes. These are port-to-port intermediate invariance checks, not claims of AEX intermediate equality. Original-AEX session renders were separately rerun for both route owners:

| Case | Route | Before / after AEX verdict | First differing byte (candidate / AEX) |
|---|---|---|---|
| 193 | Classic | mismatch / mismatch | 0: 75 / 0 |
| 193 | Smart | exact / exact | none |
| 425 | Classic | mismatch / mismatch | 0: 58 / 0 |
| 425 | Smart | mismatch / mismatch | 2016: 223 / 248 |

- Case 193 Smart raw SHA-256: `61419588ac096ac05cd390e83bc6a71aa4f6db1c7b50b1d36ab130dc272ccde8`. Case 425 Smart candidate: `8405927c8b78605ecd5b76dd15eb2a7b5d0b85df52ce708a410305069cd117dc`; AEX: `c7592da2c43efa9358be0b2400b7659fde4b8f5df419fb82c4f0fe75341b9861`. These existing differences are not alignment-fix targets; no claim that the generic numerical-closure acceptance condition is achieved for them.
- Production source SHA-256 before: `d569b69db194cb60734e02eb9cd25d49080021daf998b6f6415e0eb5d7940801`; after: `88cf9482af17eafeed61da5f9fefd87b0c542c88b33d6a564f28957b64800a7c`.
- AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`; campaign/sanitizer worker: `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Replay uses each retained corpus's hash-bound worker (including cache worker `93622cbc...`), without rebuilding. Full provenance, witness hashes/traces and corpus per-file results are in the companion evidence JSON.
- Existing tests executed directly through runpy because system Python has no pytest: `test_olmradialblur_generic_budget_20260821.py::test_generic_radial_budget_bounds_memory_work_and_smart_staging` and `test_olmradialblur_generic_baseline_20260820.py::test_generic_baseline_accepts_arbitrary_pixels_geometry_and_padding`: 2/2 pass.

inference:
- The reproduced UB is caused by typed C++ access to odd byte strides. memcpy transfers representation bits without creating references into unaligned world storage; unchanged arithmetic and measured byte identity support this fix.
- T05's 35-row count is stale relative to this base (which includes later Smart staging/admission changes); the fresh controlled count is 15. The wider all-gates-off population was not rerun and no bypass is enabled or promoted.
- Existing renderer/AEX numerical differences are independent follow-up work. The fix preserves them deliberately to satisfy this ticket's byte-identical-output goal; it does not establish native Windows AE/UCRT or all-input equivalence.

changed_files:
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- tools/fuzz/verify_radialblur_alignment_F07.py
- orchestra/reports/F07-radial-misaligned-ub.md
- orchestra/reports/F07-radial-misaligned-ub-evidence.json

verify:
Run from this worktree. All output/scratch stays under the ticket directory. Redirect long command output to individual `.log` files there.

```sh
mkdir -p orchestra/state/F07-radial-misaligned-ub
python3 tools/fuzz/verify_radialblur_alignment_F07.py --revision 0e3481cbba7c9b63e3c23480d8abb081fe03733f --scratch orchestra/state/F07-radial-misaligned-ub/sanitize-before --report orchestra/state/F07-radial-misaligned-ub/sanitize-before.json
python3 tools/fuzz/verify_radialblur_alignment_F07.py --scratch orchestra/state/F07-radial-misaligned-ub/sanitize-after --compare orchestra/state/F07-radial-misaligned-ub/sanitize-before.json --report orchestra/state/F07-radial-misaligned-ub/sanitize-after.json
python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 1 --budget-minutes 30 --corpus orchestra/state/F07-radial-misaligned-ub/verify-corpus --scratch orchestra/state/F07-radial-misaligned-ub/verify-scratch --report orchestra/state/F07-radial-misaligned-ub/verify.json
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 1 --budget-minutes 20 --scratch orchestra/state/F07-radial-misaligned-ub/replay-scratch --report orchestra/state/F07-radial-misaligned-ub/replay.json
OLM_RADIAL_CANDIDATE_SANITIZE=1 python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 1 --budget-minutes 20 --scratch orchestra/state/F07-radial-misaligned-ub/sanitize-replay-scratch --report orchestra/state/F07-radial-misaligned-ub/sanitize-replay.json
```

Expected: sanitizer before=15, after=0, zero changed rows and exit 0; production exact Classic=1 / Smart=148 (oracle wall-time budgets can vary); both replays 35/35 matches_saved, sanitized replay zero diagnostics. No numerical mismatch is silently promoted to exact.

For existing tests, use worktree-local SDK symlinks `Headers`, `Util`, `Resources` pointing to MAIN's corresponding read-only paths if absent, then:

```sh
TMPDIR="$PWD/orchestra/state/F07-radial-misaligned-ub" python3 - <<'PY'
import runpy
for path in ('tests/test_olmradialblur_generic_budget_20260821.py', 'tests/test_olmradialblur_generic_baseline_20260820.py'):
    for name, function in runpy.run_path(path).items():
        if name.startswith('test_') and callable(function):
            function()
            print('PASS', path, name)
PY
```

Expected: two PASS lines. Temporary build trees are automatically deleted; remove any SDK symlinks created for this verification afterward.

- Cleanup: scratch is 7.8 MiB, no build directories remain, temporary SDK links removed, all started processes completed; no MAIN edits, pushes, stash, release-gate or ledger changes.

next:
- No alignment work remains in the measured default-build population. Keep the existing gates unchanged.
- Existing Classic route semantics and Smart case425 numerical mismatch remain separate tickets; do not infer numerical closure from UBSan cleanup.
