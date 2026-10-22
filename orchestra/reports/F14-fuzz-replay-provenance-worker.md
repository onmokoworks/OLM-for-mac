status: partial

summary:
- Implemented hash-validated corpus worker selection and timeout inheritance for replay, with explicit CLI overrides.
- Mixed corpora replay in separate worker/timeout groups; new campaigns also record their timeout in corpus provenance.
- Framework tests: 13 passed, 1 skipped. RadialBlur: 35/35 saved-result matches without `--worker`.
- Completed all 708 top-level cases: 597 saved-result matches; all 708 primary oracle records matched.
- The requested all-True verification is unmet because candidate/experimental corpus results differ; no plugin or corpus baselines were changed.

facts:

- Branch: `orch/F14-fuzz-replay-provenance-worker`; starting HEAD: `3f25fe37`.
- The worktree began with an uncommitted implementation in `tools/fuzz/run.py`; it was reviewed, completed, tested, and retained in this ticket's commit.
- Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the compatibility plan, and the ledger's current plugin decision matrix. MAIN and emulator sources were read-only; retained workers were used without rebuilding.
- Ran `python3 -B tools/fuzz/test_framework.py` with the scratch/TMP environment shown below. First run: 14 tests, one error and one skip, caused by the new synthetic test omitting `reduction['accepted']`. Corrected the fixture to `{'accepted': []}`. Final run: 14 tests in 2.691 seconds, `OK (skipped=1)` (13 passed). The skipped opt-in real integration test is separate from the actual corpus runs below.
- Tests cover mixed workers/timeouts with worker-sensitive oracle output, fallback timeout, explicit independent overrides, missing worker/hash/provenance, hash mismatch, invalid timeout, CLI defaults, and a real CLI failure returning exit 2 with the corpus filename. Validation happens before adapter setup; replay differences still exit 1.
- Ran `python3 -B tools/fuzz/run.py --plugin PLUGIN --replay tests/fuzz_corpus/CORPUS --jobs 2 --budget-minutes 30 --scratch orchestra/state/F14-fuzz-replay-provenance-worker --report orchestra/state/F14-fuzz-replay-provenance-worker/CORPUS.json` sequentially for every nonempty top-level directory, with no worker or timeout override. Historical directory plugin names came from their JSON `plugin` fields. Ran the same empty ColorKeep replay separately (default 30-minute budget), which exited 2 with `Replay corpus is empty: tests/fuzz_corpus/colorkeep` before building.
- Every nonempty replay completed within its budget. Current corpora have no `case_timeout_seconds`; each used the 10-second fallback. Timeout inheritance is covered by the synthetic tests.
- `git diff --check`: exit 0. Scratch inspection: 1,467,496 bytes, no remaining build/case directories; only logs and JSON reports. All launched test/replay processes exited.

| Corpus directory | Saved-result matches | `replay_matches_saved` | Exit | Worker groups |
| --- | ---: | --- | ---: | --- |
| colorkeep | 0 cases | N/A (empty) | 2 | none |
| olmblur | 39/39 | True | 0 | frozen: 24; highdepth: 15 |
| olmcolorkey | 0/3 | False | 1 | frozen: 3 |
| olmdirectionalblur | 56/56 | True | 0 | frozen: 56 |
| olmdistancegradation | 145/145 | True | 0 | frozen: 139; containment: 6 |
| olmkirakira | 8/8 | True | 0 | frozen: 8 |
| olmkirakira_gate_off_T06 | 0/62 | False | 1 | containment: 62 |
| olmsmoother | 29/29 | True | 0 | containment: 29 |
| olmsmoother2 | 8/8 | True | 0 | containment: 8 |
| olmtoondilate | 277/300 | False | 1 | frozen: 300 |
| olmtoondilate_T13 | 0/23 | False | 1 | frozen: 23 |
| radialblur | 35/35 | True | 0 | offset: 35 |

Validated worker identities (aliases used only in the table):

| Alias | Absolute executable | SHA-256 |
| --- | --- | --- |
| frozen | `/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker` | `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2` |
| highdepth | `/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker` | `9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7` |
| containment | `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker` | `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` |
| offset | `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker` | `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed` |

First saved-result mismatches and measured boundaries:

- **ColorKey:** `tests/fuzz_corpus/olmcolorkey/seed1_case000020_32358eb88430.json`. Saved Mac output SHA `5a84100cd36b1fcd1313c825a6024399c709c61c71f092b13bd1981f7a7d9bf2`; observed `5acad5ae07164031d1b7dda4ef816b83df950e40d014976545734909f6fcbfb7`. Smart changes from `mismatch` to `exact`. Classic remains `mismatch`: saved first byte/word 3/0 with 11 differing bytes / 4 words; observed first byte/word 4/1 with 10 differing bytes / 3 words. All three cases have unchanged primary and per-route oracle records; all three Smart results now report exact. Source SHA changes from `4ec2b89db41ce06d7ba3fb998f32e40a5967aed3996f09f1d5a94fd63ef40700` to `a7a177101066c8939a9716b079af22aed51430578856fe14b7474b544b2794ed`; other recorded dependencies match.
- **KiraKira diagnostic:** `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000000_7b627ae38e84.json`. Saved Classic/Smart status is `mismatch`, output SHA `25225c9ba28948125b422dcab05d3febddae6eab43b11e2215342852602d7d3d`, first differing byte/word 0/0; production replay refuses both routes with error 516. The saved provenance explicitly records `triage.experiment=all` and `OLM_KIRA_TRIAGE_GATE_OFF=1`; its README requires `triage_kirakira.py --experiment all` and prohibits treating it as production acceptance. All 62 primary oracle records match; the saved results also lack the current `oracles` map. This run measures the requested ordinary runner behavior, not reproduction of that experimental candidate.
- **ToonDilate:** `tests/fuzz_corpus/olmtoondilate/seed1_case000015_9b13c27c2f2e.json`; the T13 directory's first mismatch has the same basename. Saved Smart SHA `827c2540f8ee6d3cfd1b7ce67db6b6c4fab2513621f872b564d73ca294e4b0fc`, first differing byte/word 64/16, 41 differing bytes / 12 words. Observed Smart SHA `501461adefd891bfd5e245ed582c61337157338b79217b077d5ffb647023f3c4` is `exact`. Classic remains `no_write`. All 23 differing cases in each directory change Smart from mismatch to exact, with unchanged primary/per-route oracle records. Source SHA changes from `c49f86774d395f1bbb838f723b0fa830f819b291112fdaa14063d007081724e4` to `509b1c1b3c60bc25f80bb65bcdc46cfcee51d8732a54e2a771f44577ec30f258`; other recorded dependencies match.

inference:

- **INFERENCE:** Worker provenance selection resolves the reported RadialBlur comparison problem and works on actual mixed-worker corpora. The remaining False results are consistent with stale candidate baselines and the distinct historical KiraKira experiment/schema, rather than incorrect worker selection. This is not a claim that all plugin outputs are correct.
- **INFERENCE:** Updating those historical results or recreating experimental candidate settings requires a separately scoped provenance review. Automatically changing expected results would hide the observed differences.

changed_files:

- `tools/fuzz/run.py` — select and validate corpus workers before setup; group by worker/timeout; report group provenance; preserve explicit overrides and generation defaults; record timeouts; print setup failures to stderr.
- `tools/fuzz/test_framework.py` — six provenance regression tests and configurable unit-test scratch directory.
- `tools/fuzz/README.md` — document replay precedence, fail-closed behavior, and grouping.
- `orchestra/reports/F14-fuzz-replay-provenance-worker.md` — this report.

verify:

Run from this worktree. The following unit command should exit 0 with 14 tests, 1 skipped:

```sh
scratch="$PWD/orchestra/state/F14-fuzz-replay-provenance-worker"
mkdir -p "$scratch"
export TMPDIR="$scratch" TMP="$scratch" TEMP="$scratch" PYTHONDONTWRITEBYTECODE=1
OLM_FUZZ_TEST_SCRATCH="$scratch" python3 -B tools/fuzz/test_framework.py > "$scratch/framework-tests.log" 2>&1
tail -5 "$scratch/framework-tests.log"
git diff --check
```

This reproduces every corpus replay, including the intentional empty-corpus failure, without `--worker` or `--case-timeout`. Expect the counts and exit codes in the table on the same plugin source snapshot. The shell continues after expected nonzero exits so all corpora run. Each individual runner streams to a log; the Python loop prints only one summary per corpus.

```sh
python3 -B - <<'PY' > "$scratch/reverify.log" 2>&1
from pathlib import Path
import json, subprocess, sys
scratch = Path('orchestra/state/F14-fuzz-replay-provenance-worker').resolve()
for corpus in sorted(Path('tests/fuzz_corpus').iterdir()):
    if not corpus.is_dir():
        continue
    files = sorted(corpus.glob('*.json'))
    plugin = json.loads(files[0].read_text())['plugin'] if files else corpus.name
    report = scratch / (corpus.name + '.json')
    command = [sys.executable, '-B', 'tools/fuzz/run.py', '--plugin', plugin,
               '--replay', str(corpus), '--jobs', '2', '--budget-minutes', '30',
               '--scratch', str(scratch), '--report', str(report)]
    with (scratch / (corpus.name + '.log')).open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    data = json.loads(report.read_text())
    rows = data.get('replays', [])
    print(corpus.name, 'exit', result.returncode,
          'matches', sum(r['matches_saved'] for r in rows), '/', len(files),
          'all', data.get('replay_matches_saved'), 'status', data['status'],
          'first_mismatch', next((r['path'] for r in rows if not r['matches_saved']), None),
          flush=True)
PY
tail -12 "$scratch/reverify.log"
```

next:

- Orchestrator review/merge of the framework implementation; no push was performed.
- Separate follow-up: review ColorKey and ToonDilate candidate changes and rebaseline the affected corpora with retained historical provenance if appropriate.
- Keep KiraKira's gate-off corpus explicitly experimental; review its dedicated runner and result-schema migration separately. ColorKeep has no saved JSON cases to replay.
