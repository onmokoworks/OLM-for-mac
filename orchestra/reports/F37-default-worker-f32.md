status: blocked

summary:
- Switched generation default from F30 to F32; F30 and the frozen worker remain selectable through `--worker` and `OLM_AEX_WORKER`.
- Replayed all 708 cases across 11 corpora with F32. 685 match saved results; the 23 discrepancies are existing KiraKira T06 Smart refusal→exact improvements.
- Independently replayed all 62 T06 cases with F30: every complete result is identical to F32. The ticket's all-non-Smoother-corpora-match requirement nevertheless remains unmet.
- Smoother v1's 29 saved cases are all PF8 and all match; no eligible PF16 rebaseline exists and no corpus was changed.
- Seed 1 n300 qualification and full Classic/Smart baseline are recorded below. No plugin, release gate, ledger, MAIN, or emulator source was changed.

facts:

Read AGENT_GUIDE.md, tools/emulation/GOTCHAS.md, compatibility plan, Smoother v1 ledger row, and F31/F32 reports. Work is on `orch/F37-default-worker-f32`. No worker rebuild, push, stash, history rewrite, or permission rejection occurred.

Workers (actual SHA-256 recorded by the runner):
- F32 default: `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
- F30 control: `8b51d0456ff55aa2034a0bbb00b822bd2339cbe27247021c289170a78a3fb53b`.

Commands run (logs and full reports in `orchestra/state/F37-default-worker-f32/`):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/measure_F37.py
TMPDIR="$PWD/orchestra/state/F37-default-worker-f32" PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --budget-minutes 120 --worker /Users/onmk/.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$PWD/orchestra/state/F37-default-worker-f32/control" --report "$PWD/orchestra/state/F37-default-worker-f32/t06-f30.json"
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/summarize_F37.py
TMPDIR="$PWD/orchestra/state/F37-default-worker-f32" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p test_framework.py
git diff --check
```

The driver uses jobs 1, seed 1, n300, no shrinking, 10-second per-case limits, 120-minute campaign budgets, and ticket-local scratch. Generation omits `--worker` and removes any inherited `OLM_AEX_WORKER`, testing the new default. Replay explicitly uses `default_worker()` because ordinary replay intentionally honors saved worker bindings. At most two emulator/build workloads ran concurrently (the serial campaign driver and T06 F30 control). Existing framework tests: 14 run, OK, 1 skipped. Default selection, F30 and frozen-worker CLI/environment overrides were additionally asserted against their existing executables.

Corpus results:

| Corpus | Saved matches / cases |
|---|---:|
| olmblur | 39/39 |
| olmcolorkey | 3/3 |
| olmdirectionalblur | 56/56 |
| olmdistancegradation | 145/145 |
| olmkirakira | 8/8 |
| olmkirakira_gate_off_T06 | 39/62 |
| olmsmoother | 29/29 |
| olmsmoother2 | 8/8 |
| olmtoondilate | 300/300 |
| olmtoondilate_T13 | 23/23 |
| radialblur | 35/35 |

Non-Smoother v1: 656/679 saved results match. First saved-result drift: `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000000_7b627ae38e84.json`, Smart saved refusal/error 516 → exact/error 0, output SHA-256 `902a585f5fab885262d441d31452ade16998baf24acf634f319d90800cfcdad6`. All 23 changes have this refusal→exact status transition; Classic remains refusal. F30 control exit 1, 39/62 saved matches, **62/62 complete observed result objects identical to F32**. No rebaseline tool was invoked because the only allowed migration (newly rendering exact Smoother PF16) has no saved cases.

The committed `F37-evidence/measurements.json` binds full-report hashes, worker/AEX/source provenance, every corpus discrepancy, per-route summaries and the first mismatch per campaign route. Full reports can be regenerated using the committed driver.

Seed 1, n300 per plugin (3,000 cases):

E = exact, M = mismatch, R = refusal, U = other verdicts. Smart U is `uncompared`; Classic ToonDilate U=300 is `no_write`, not 300 failed renders. Raw status counts are preserved in evidence.

| Plugin | Classic E/M/R/U | Smart E/M/R/U |
|---|---:|---:|
| colorkeep | 74/131/95/0 | 300/0/0/0 |
| olmblur | 13/0/287/0 | 282/1/17/0 |
| olmcolorkey | 0/300/0/0 | 300/0/0/0 |
| olmdirectionalblur | 4/284/12/0 | 286/0/12/2 |
| olmdistancegradation | 10/290/0/0 | 287/0/6/7 |
| olmkirakira | 0/48/252/0 | 269/0/31/0 |
| olmsmoother | 205/0/95/0 | 205/0/95/0 |
| olmsmoother2 | 0/0/300/0 | 300/0/0/0 |
| olmtoondilate | 0/0/0/300 | 300/0/0/0 |
| radialblur | 1/118/181/0 | 240/0/59/1 |

All ten generation commands exited 0 with `status=complete` and 300 cases (runner completion does not mean every case is exact). All eleven replays completed; ten exited 0, T06 exited 1. Driver exit 0; summary exit 0. Smart totals match the F31 seed1 table except Smoother v1, now 205/0/95/0 instead of 62/29/95/114.

First/only Smart pixel mismatch: Blur seed1 case99, PF32 1×127, first byte219/word54, 10 different bytes/words; F32 word `0000c0ff`, Mac `0000c07f` (little-endian bytes). Reference hash `61a7edb92ad4bc4cbbf74669f2aceee2ed02a3908c2b2bac26a942b5596df894`; Mac hash `cbbacd2a14c6ef4efc6a6896b788a3b30cffdfb6191556429f1e86b4fc19fcbc`. This is the same reported F31 NaN-sign mismatch. The Classic mismatch counts are retained honestly, without expanding this ticket into plugin fixes.

inference:

The controlled T06 replay establishes that its saved-result drift is pre-existing relative to F32: F30 and F32 have identical full outcomes on all 62 cases. The new default reproduces the stated Smoother improvement and the prior non-Smoother Smart baseline in this campaign. This is bounded CPU-emulation evidence, not a full-domain or native AE equivalence claim. Acceptance is blocked solely because the requested saved-result condition cannot be satisfied without an out-of-scope T06 corpus migration. No numerical hypothesis loop or workaround was attempted.

changed_files:
- `tools/fuzz/run.py` — F32 generation default, unchanged override/replay policy.
- `tools/fuzz/README.md` — default and explicit old-worker/replay selection documentation.
- `tools/fuzz/measure_F37.py` — reproducible serial all-corpus/all-plugin measurement driver.
- `tools/fuzz/summarize_F37.py` — compact evidence extraction and F30 control comparison.
- `orchestra/reports/F37-evidence/measurements.json` — measured provenance, counts, first mismatches and all saved-result drift.
- `orchestra/reports/F37-default-worker-f32.md` — this report.

verify:

Run the commands in facts from this worktree with MAIN assets and registered F30/F32 workers available. Redirect each long command to a log under the ticket scratch directory. The driver creates scratch and configures TMPDIR/TMP/TEMP itself; `--resume` is optional for already complete reports. Expected results: 10 completed n300 campaigns with the table above; 11 completed replays with 685/708 saved matches; T06 control 62/62 identical to F32 and 39/62 saved matches; 14 framework tests run with 1 skipped, OK; clean `git diff --check`. Per-case timeout verdicts may vary with load and must be retained as measured, not silently rebaselined.

Worker selection can be rechecked without rendering:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PYVERIFY'
import os, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, 'tools/fuzz')
from run import default_worker, options
os.environ.pop('OLM_AEX_WORKER', None)
assert default_worker() == Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'
for worker in (
    Path.home()/'.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker',
    Path('/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker'),
):
    assert worker.is_file()
    with patch.dict(os.environ, {'OLM_AEX_WORKER': str(worker)}):
        assert default_worker() == worker
    with patch.object(sys, 'argv', ['run.py', '--plugin', 'olmsmoother', '--worker', str(worker)]):
        assert options().worker == worker
print('PASS')
PYVERIFY
```

next:
- Orchestrator should decide whether to accept the default switch with the documented pre-existing T06 corpus discrepancy.
- Suggested follow-up: authorize a bounded KiraKira T06 saved-result migration for these 23 hash-bound refusal→exact improvements, then rerun all corpus checks. F37 does not authorize that rewrite.
- Existing Blur Smart NaN-sign mismatch and Classic route differences remain separate plugin work.

Final hygiene: all started command sessions finished. The runner removed its temporary build/harness trees; empty run/control directories were removed. Ticket scratch is 24 MiB (logs, JSON reports and generated counterexamples), below 5 GiB. Evidence validation confirms 3,000 campaign cases, 708 corpus cases, 685 saved matches, F32 provenance throughout, and 62/62 identical T06 F30/F32 outcomes. Final whitespace check passes.
