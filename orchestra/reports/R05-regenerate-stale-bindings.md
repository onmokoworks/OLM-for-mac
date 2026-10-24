status: blocked
summary:
- Made release archive lookup and eight parameter-UI AEX lookups worktree-aware; preserved digest/containment checks.
- Refreshed two Blur PF32 source pins after identical twice-run original-AEX results and current production replays.
- All 18 Radial first-failing witnesses match current Mac final output against two identical F46 executions; intermediate pins remain unresolved.
- Both gates completed: release remains invalid; final generic gate is 45 PASS / 8 FAIL / 0 SKIP.
- Remaining F40 bindings, historical inputs, R03 contracts and real-host evidence are not closed; the requested all-failures-adjudicated target is NOT achieved.

facts:

Base: `bd234fc9`, branch `orch/R05-regenerate-stale-bindings`. No production code, original assets, emulator source, installed bundles, release predicate, forbidden-action lists or existing numerical assertions were changed. No worker was rebuilt or installed into AE. Regenerable build/scratch outputs were removed; remaining ticket scratch is 2.3 MiB, with logs and reports retained. All started task processes have exited.

Before/after gate table (I03 is the historical integration baseline, so R03/R04 contribute to these improvements):

| Check | I03 before | R05 measured result |
|---|---|---|
| Release aggregate | abort: return-archive digest mismatch | completes, exit 1, `releasable=false` |
| Windows archive boundary | unavailable worktree archive | 7 accepted, unchanged archive digests |
| Parameter UI | 3 proven / 7 invalid | 10 proven / 0 invalid |
| Installed identity | 0 valid / 10 invalid | 0 valid / 10 invalid; **requires real AE/Windows** evidence/receipts |
| Native host-smoke binding | 0 proven / 10 invalid | 0 proven / 10 invalid; **requires real AE/Windows** |
| Full fixture records | 34 exit0 / 166 exit1 / 1 exit127 / 3 exit126 | 77 exit0 / 123 exit1 / 1 exit127 / 3 exit126 |
| Commands blocked by installed identity | 89 skipped | 89 skipped; not pass |
| Generic gate | 23 PASS / 30 FAIL | 45 PASS / 8 FAIL / 0 SKIP |
| Fixture 004, Blur PF32 matrix | stale source binding | full-run exit1, then strict focused audit exit0 after the refresh |

The full release/fixture run precedes the one metadata refresh. Its 204 historical records are preserved, not rewritten to claim a second full run. The refreshed fixture was rechecked separately. The final generic gate ran after the refresh and after restoring generated reports. The first generic invocation also reported 45/8, but is explicitly superseded because the initial orchestration wrapper restored fixture-generated reports only after both gates. The committed driver restores them between stages. Both initial and final logs are retained.

Path-resolution verification:

- The original gate's `windows_boundary_gate()` reproduced `Windows AE boundary return_archive digest mismatch` in this worktree.
- The updated gate resolves absent archives against MAIN using the existing `olm_assets.main_assets` resolver. The expected return SHA-256 remains `e582b0f368deb6dfbb34de2675e382d2222372705da043151d90dc895f7d7a0a`; seven accepted rows are historical evidence, not a new Windows run.
- Existing local archives take precedence even when corrupt. Absolute paths, parent traversal, escaping local symlinks and escaping MAIN symlinks are rejected. The focused regression passes and confirms corrupt local/MAIN bytes still fail the digest check.
- Eight setup/update comparator AEX constants now use `resolve_asset`; original AEX hash checks remain intact. The full aggregate's actual-AEX parameter-UI checks prove all ten rows.
- `--results-dir` forwards the fixture runner's existing scratch/log option. No acceptance condition changed.

Eligible metadata regeneration:

- `R05-regenerate-blur.py` and `R05-regenerate-blur.py --apply` completed. The applying run verifies each retained parameter record and source hash, executes each original-AEX case twice with identical bytes and execution metadata, and compares the unchanged expected output hash.
- 12 NonLegacy + 8 Legacy PF32 cases reproduce the retained bytes. Both current UCRT-linked production replay builds pass all 20 cases. The seven formal cases remain uniquely mapped to those fixtures.
- Only two JSON values change in `olmblur_pf32_formal_worker_matrix_20260805.json`: production source SHA-256 pins. NonLegacy is `993e119bde5c877a8086fda37dd3bd0aa69a88f3ab7ed8ca32baf9fdf17db3e4`; Legacy is `bfad34a7b3beb4c865d14079609142262dc4af26ff591ecc3bc6e93869ad1c82`. All numerical pins, fixture bytes and other JSON values are unchanged. Original formatting is retained.
- Matrix report SHA-256 is `0049165c657e201ff34939c3343f8e481aaf43ce98f08d064410689f6ca00f81`.
- The two PF16 exported-owner cases also reproduce identical reports twice. Their report was already current: SHA-256 remains `2077fd254c1c31c4ab8456f9c6c1ac513c1133346402f1c5c0d77be3d0daab7c`; no refresh was necessary.
- `R05-focused-checks.py`: four command invocations exit0: matrix audit, owner validation, four owner tamper/unit tests, and one archive-resolution test. The archive test contains multiple independent tamper checks.

Radial verification:

- `R05-radial-finals.py` independently executed original AEX SHA-256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb` using cached F46 worker SHA-256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- Rechecked first-failing witnesses for records **152, 153, 155, 156, 157, 158, 159, 165, 167, 168, 169, 170, 171, 172, 174, 178, 179, 181**. All 36 original sessions report intact guards and clean sessions. Each pair is byte-identical.
- Current Mac comparisons: 17 freshly built public Smart renders plus the full-size record165 direct production harness. All 18 final outputs match F46: **8,317,728 bytes per repeat, zero differing bytes, first mismatch null**. All 18 F46 hashes also equal the retained F39 F32 final hashes. No new final-output mismatch requiring a fuzz witness was found.
- Record165's direct harness still exits1 on its intermediate-plane assertions while its final output matches. The remaining full legacy commands likewise retain their required planes, negatives and fixture pins. These selected witnesses do not close every case in a multi-case command.
- `R05-trace-capability.py`: F46 raw `session ... --watch ...` exits2 with usage, before rendering. Its `main.rs` hash matches the recorded F46 build manifest; raw sessions require six positional arguments after supported options. `render-trace-png` converts input to RGBA8 before typed promotion. Every one of the 14 checked retained typed sources contains samples not representable by that transport. The cached F49 tracing recipe instead hardcodes DirectionalBlur RVA `0x1ec0`; it is not a configurable Radial tracer.
- No typed intermediate F46 reference was obtained. Replacing these plane pins with Mac captures, final-only checks, or lossy PNG traces would weaken the checks, so replacement stopped at this capability boundary.

Remaining failures / incomplete adjudication:

- Every fixture record and all 53 final generic entries remain in `R05-results.json`, with full logs in the archive. Installed-evidence obligations are explicitly labeled **requires real AE/Windows**, not pass. The three identity preflights skip Smoother 28, Smoother2 47 and ToonDilate 14 commands.
- Apart from fixture004, the requested F40 stale-binding set was not regenerated. Missing historical packages/workers and unresolved contracts remain unresolved; they are not recategorized as native-host requirements or numerical regressions without evidence.
- The 13 R03 runtime/contract failures remain open: fixture047 ColorKey atomic; fixture063/generic Directional cleanup; fixture083 Directional adapter; fixture126 Kira Mode3 fail-close; fixtures162/163 Radial variation/geometry refusals; fixture164 Radial case0009 replay; fixture184 Radial host plumbing; generic Directional back-only, Distance production, Kira UI length and Radial baseline. No rejection predicate was changed in this ticket.
- R03's installed Kira134 and Radial183 bindings require current identity/build receipts and real-host evidence. Its mixed performance binding remains unresolved.
- Final generic failures are the five runtime/contract entries above (Directional contributes two), Kira Windows-owner evidence (**requires real AE/Windows** to renew that claim), support documentation, and performance-runner bindings. The last two are unresolved bindings, not measured pixel differences.

inference:

The Blur source-pin change is justified for its retained matrix by fresh identical original executions plus current production equality. The Radial selected final failures are consistent with F39's oracle-drift explanation, but final equality cannot establish intermediate-plane equality or justify removing a negative assertion. The remaining failures cannot yet all be classified as real-host requirements or genuine production findings. This is an incomplete evidence migration, not a release-ready result.

changed_files:

- `scripts/run_olm_release_gate_20260806.py`: contained archive fallback and fixture scratch forwarding.
- Eight setup/update comparator files: original AEX input resolution only.
- `refs/conformance/olmblur_pf32_formal_worker_matrix_20260805.json`: two source pins only.
- `tests/test_release_archive_resolution_R05.py`: path/digest tamper regression.
- `orchestra/reports/R05-*.py`: reproducible regeneration, gate orchestration, focused checks, Radial replay, capability audit and packaging.
- This report, `R05-results.json`, `R05-evidence.tar.gz`, `R05-artifact-manifest.json`, and `R05-changed-files.txt`.
- The complete file list is in `R05-changed-files.txt`.

verify:

From the worktree root, run stages sequentially (all scratch remains ticket-local; no install):

```sh
bash scripts/setup_ae_sdk_links.sh
export OLM_TEST_JOBS=2 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/R05-regenerate-stale-bindings"
export TMP="$TMPDIR" TEMP="$TMPDIR"
mkdir -p "$TMPDIR"
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"
"$PY" -B orchestra/reports/R05-regenerate-blur.py > "$TMPDIR/recheck-blur.log" 2>&1
python3 -B orchestra/reports/R05-focused-checks.py > "$TMPDIR/recheck-focused.log" 2>&1
"$PY" -B orchestra/reports/R05-radial-finals.py > "$TMPDIR/recheck-radial.log" 2>&1
python3 -B orchestra/reports/R05-trace-capability.py > "$TMPDIR/recheck-trace.log" 2>&1
python3 -B orchestra/reports/R05-run-gates.py > "$TMPDIR/recheck-gates.log" 2>&1
git diff --check
```

Expected: Blur 20 PF32 + 2 PF16 unchanged; four focused command exits0; 18 Radial final-equality rows, 36 clean original sessions; raw tracing still unavailable. Both child gates exit1 and remain not releasable; UI10 and Windows7 pass. Fixture004 now passes after the refresh; the table above preserves the measured pre-refresh full-run count. Gate-driver and Radial-driver exit0 mean orchestration completed, not release acceptance. Inspect their result JSON. The full gate is long (the measured release stage took 1311.91 seconds; final generic 373.56 seconds).

Retained evidence integrity, without regeneration:

```sh
python3 - <<'PY'
import hashlib,json,tarfile
from pathlib import Path
p=Path('orchestra/reports');m=json.loads((p/'R05-artifact-manifest.json').read_text())
with (p/m['archive']).open('rb') as f:
    assert hashlib.file_digest(f,'sha256').hexdigest()==m['sha256']
with tarfile.open(p/m['archive']) as t:
    assert len(t.getmembers())==len(m['files'])
    for r in m['files']:
        assert hashlib.sha256(t.extractfile(r['path']).read()).hexdigest()==r['sha256']
r=json.loads((p/'R05-results.json').read_text())
assert r['generic_counts']=={'PASS':45,'FAIL':8,'SKIP':0}
assert len(r['radial'])==18 and all(x['exact'] for x in r['radial'])
assert all(x['exit']==0 for x in r['focused'])
assert not r['releasable']
print('R05 evidence intact; release remains invalid')
PY
```

Archive: 262 members, SHA-256 `b22bfa2f2e43cb2490f43210f5741613849d4eeb0b27d257681c82420a63535a`.

next:

Authorize/provide a configurable raw typed Radial tracing worker grounded in F46, binding traced final output to the untraced worker before refreshing every required plane and every multi-case input twice. Recover or replace missing historical fixture packages with equally strict current original-AEX evidence. Continue the remaining F40 binding and R03 contract adjudications individually. Obtain current install/build receipts and native AE/Windows evidence through a separately authorized host task; then rerun the release aggregate, including the 89 blocked commands. No new exactness claim extends beyond the measured cells here.
