status: done
summary:
- Added the sequential v2 gate, scope notes, decision tests, and reproducible evidence packaging; legacy gate unchanged.
- One complete run finished: six stages PASS, static stage FAIL; local release decision is FAIL.
- 810/810 corpus records match saved results; fresh owner routes have E=5684/M=0/R=263/U=53.
- Universal bundle checks have zero owner pixel mismatches and zero arm64/x86_64 differences; 45 selected test files pass.
- Finding: DistanceGradation's effective project Release deployment target is 26.2, not 11.0. Real-host obligations remain required.

facts:

Branch: `orch/R09-release-gate-v2`. The complete run used the exact script SHA recorded in `R09-results.json`, from `2026-10-24T01:25:58.376835+00:00` through `2026-10-24T02:05:08.411545+00:00`. The command completed with exit **1**, correctly rejecting the configuration finding:

```sh
python3 -B scripts/run_olm_release_gate_v2.py \
  --state orchestra/state/R09-release-gate-v2/complete \
  > orchestra/state/R09-release-gate-v2/complete.log 2>&1
```

The script selects MAIN's existing absolute-path emulation Python. Child commands, exits, durations and log paths are recorded in the JSON summary. All stages are sequential, fuzz uses `--jobs 1`, Xcode uses `-jobs 1`, and `OLM_TEST_JOBS=2`. `memory_pressure` reported **56%** system-wide free memory before the completed build.

| Stage | Result | Measured evidence |
| --- | --- | --- |
| Framework | PASS | 34 tests run: 32 pass, 2 optional integration tests skipped |
| Universal build | PASS | 10 Release bundles, both arm64 and x86_64; all executable SHA-256s recorded |
| Corpus | PASS | 810 saved-result matches, 0 failures, 0 retries, 0 ORACLE-STOP exceptions; ColorKeep has 0 saved cases |
| Fresh seeds | PASS | Seeds 2026/2027, 300 per plugin per seed, all 6000 cases complete; E=5684, M=0, R=263, U=53, framework errors=0 |
| Bundle checks | PASS | F47d n100 ×10: E=942, M=0, R=46, U=12. F51 n100 ×10 plus corpus: 1764 equal renders +46 equal refusals =1810 pairs, 0 differences |
| Selected plugin tests | PASS | 45 files pass, 0 fail; eight legacy exclusions remain explicitly documented, not passed |
| Static | **FAIL** | Floating-point flags and Universal architectures satisfy the requirement for all ten projects; deployment satisfies it for 9/10. PiPL flags equal original AEX resources for 10/10; known-original-bugs document present |

Fresh owner-route counts (Smart except Smoother v1 Classic):

| Plugin | E | M | R | U |
| --- | ---: | ---: | ---: | ---: |
| Blur | 600 | 0 | 0 | 0 |
| ColorKeep | 600 | 0 | 0 | 0 |
| ColorKey | 600 | 0 | 0 | 0 |
| DirectionalBlur | 596 | 0 | 1 | 3 |
| DistanceGradation | 575 | 0 | 15 | 10 |
| KiraKira | 573 | 0 | 27 | 0 |
| Smoother2 | 600 | 0 | 0 | 0 |
| ToonDilate | 600 | 0 | 0 | 0 |
| RadialBlur | 559 | 0 | 1 | 40 |
| Smoother v1 | 381 | 0 | 219 | 0 |

First failing release condition:

- `mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj/project.pbxproj` SHA-256: `5036dc81b03faafc4fc02adf5adf691f870153ea7c8a1aa9909b868d60c84032`.
- `xcodebuild -configuration Release -showBuildSettings -json` reports `MACOSX_DEPLOYMENT_TARGET=26.2`; required value is `11.0`. The project contains no explicit `MACOSX_DEPLOYMENT_TARGET` setting.
- Witness: archived `settings-OLMDistanceGradation.log`; also summarized under `static_configuration_findings` in `R09-results.json`.
- The required builder explicitly passes `MACOSX_DEPLOYMENT_TARGET=11.0`. Thus its successfully tested bundles do not establish that the project's default Release configuration is correct. The static predicate was not weakened and the project was not edited.
- No first owner-route pixel mismatch exists in these campaigns; F51 has no differing pair. Non-owner diagnostics include **2359 Classic mismatches**, with all witnesses saved and **0 omitted witnesses**. These remain outside the specified Smart release decision and are not claimed to be fixed or newly adjudicated.

Additional verification:

- `python3 -B tests/test_release_gate_v2.py`: **5 tests pass**. Covers incomplete/mismatching campaigns, refusal accounting, missing original hashes and unchanged other-route requirements for the ORACLE-STOP exception. The live corpus did not require this exception.
- `git diff --check`: passes.
- Three framework tests now honor the already-established `OLM_FUZZ_TEST_SCRATCH` override. Assertions and default paths are unchanged; all execution scratch remains under this ticket.
- Two preliminary invocations were interrupted during bundle builds while reviewing refusal-status accounting and saved-result-equality precedence. They supply no acceptance evidence; their build products were removed. The completed run is authoritative and uses the committed gate content.
- Regenerable build trees were removed. Remaining ticket scratch is approximately **109 MiB**, containing logs, JSON and witnesses. All processes started for these runs have exited. No production code, legacy gate, ledger, MAIN asset, installed plugin or cached reference worker was changed; no worker was rebuilt and nothing was pushed.

Evidence package:

- `R09-results.json`: complete stage/command summary, executable hashes, configuration finding, non-owner counts and host obligations.
- `R09-evidence.tar.gz`: **2521 files**, **10,258,514 bytes**, SHA-256 `36aa5feb473fe67c1b55b541f23fe3b73f7a980f82814d44f25e54776d005add`.
- `R09-artifact-manifest.json`: per-member byte count and SHA-256. Independently verified every archived member and the archive digest.
- Installed identity, native host smoke and Windows owner evidence each remain `REQUIRES-REAL-HOST`; `release_authorized=false`.

inference:

The measured CPU-emulation/fake-host evidence supports zero owner-route pixel mismatches within this finite campaign scope. Refusals and uncompared outputs do not establish full-input compatibility, and non-owner Classic differences remain visible. The deployment finding is consistent with an unpinned project inheriting the installed SDK's default. Pinning that setting is a separate configuration change, not a numerical correction. Native AE/Windows, UI, ROI/downsample, custom ramps/layers and general native-UCRT equivalence are not established by this gate.

changed_files:

- `scripts/run_olm_release_gate_v2.py`
- `notes/RELEASE_GATE_V2.md`
- `tests/test_release_gate_v2.py`
- `tools/fuzz/test_adapters.py`
- `tools/fuzz/test_rebaseline_production.py`
- `tools/fuzz/test_route_oracles.py`
- `orchestra/reports/R09-package.py`
- `orchestra/reports/R09-results.json`
- `orchestra/reports/R09-artifact-manifest.json`
- `orchestra/reports/R09-evidence.tar.gz`
- `orchestra/reports/R09-release-gate-v2.md`

verify:

Run from this worktree, using a new output directory:

```sh
python3 -B tests/test_release_gate_v2.py
python3 -B scripts/run_olm_release_gate_v2.py \
  --state orchestra/state/R09-release-gate-v2/recheck \
  > orchestra/state/R09-release-gate-v2/recheck.log 2>&1
# Expected exit 1 until DistanceGradation's project deployment target is fixed.
# Inspect recheck/summary.json even after a nonzero exit.
git diff --check
```

Expected: five decision tests pass; complete local gate rejects the unpinned deployment target, with all ten PiPL comparisons passing. Numerical acceptance requires zero owner mismatches / slice differences and complete case counts. E/R/U can vary with machine load and original-side wall budgets; the table above records this run, not fabricated future counts. No real-host item may turn PASS.

To verify the retained evidence without rerunning builds or emulation:

```sh
python3 -B - <<'PY'
import hashlib, json, tarfile
from pathlib import Path
p = Path('orchestra/reports')
m = json.loads((p/'R09-artifact-manifest.json').read_text())
with (p/m['archive']).open('rb') as f:
    assert hashlib.file_digest(f, 'sha256').hexdigest() == m['sha256']
expected = {r['path']: r for r in m['files']}
with tarfile.open(p/m['archive'], 'r:gz') as t:
    seen = set()
    for entry in t:
        r = expected[entry.name]
        assert entry.name not in seen and entry.size == r['bytes']
        with t.extractfile(entry) as f:
            assert hashlib.file_digest(f, 'sha256').hexdigest() == r['sha256']
        seen.add(entry.name)
    assert seen == set(expected)
r = json.loads((p/'R09-results.json').read_text())
assert len(r['stages']) == 7 and not r['local_gate_pass']
assert not r['release_authorized'] and r['omitted_witnesses'] == 0
assert [(s['name'], s['status']) for s in r['stages'] if s['status'] != 'PASS'] == [('static', 'FAIL')]
print('2521 evidence members intact; local release gate FAIL is preserved')
PY
```

`python3 -B orchestra/reports/R09-package.py --state <completed-ticket-state>` regenerates the report/archive/manifest from an actual completed run; it does not rerun or promote the gate.

next:

Assign a configuration follow-up to pin DistanceGradation's project Release deployment target to 11.0 and rerun v2. Keep original-stop/uncompared coverage, Mac refusals, excluded R05/R07 contracts, and non-owner Classic behavior as separate follow-ups. Installed identity, native AE smoke and Windows owner evidence require their real hosts. No numerical production fix is justified by this ticket's zero owner-mismatch result.
