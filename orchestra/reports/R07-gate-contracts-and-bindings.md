status: blocked
summary:
- Reproduced all ten in-scope R03 contract command failures against current builds; no assertion was weakened.
- Fixtures162–164 are reserved for R08 under the explicit prohibition on touching Radial fixtures152–181.
- Contract failures are not numerical Mac-versus-original witnesses; replacing them requires more than changing an expected rejection to acceptance.
- Refreshed three Blur owner reports after twice-identical originals/current builds: six consumers pass; remaining bindings are enumerated.
- Fresh performance20/20 passes; documentation/host obligations remain open. No release promotion is made.

facts:

Branch `orch/R07-gate-contracts-and-bindings`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, the relevant ledger decision rows and R03/R05/R06 reports. SDK links were prepared with `bash scripts/setup_ae_sdk_links.sh`. No production code, MAIN assets, cached workers, release predicate, installed bundle or forbidden-action list is changed.

Group1 before/after table. “Before” is R03/R05 retained evidence; “after” is the fresh `R07-check-items.py --group contracts` run. All ten child commands return1; the driver returns0 to indicate completion, not acceptance. Exact commands, elapsed times and full diagnostics are in `R07-contracts-evidence.tar.xz` with a member-hash manifest.

| Item | Before | After / reason it remains blocked |
|---|---|---|
| fixture047 ColorKey atomic | probe3 | probe3; the test requires 63 positive / 567 negative cases, including rejection after flipping one active source byte. A generic source-admitting implementation cannot be repinned to this source-whitelist contract. Need paired original output for every newly admitted mutation, retaining genuine layout/alias/atomicity negatives. |
| fixture063 Directional cleanup | probe134 | probe134: err=-3, allocation attempts=1, output unchanged=1, layer/output/checkin=2/1/1, parameter checkout/checkin=21/21. Test requires BAD_CALLBACK_PARAM and zero allocations for a 1×2 world with output stride1,700,000,000. This is a safety/lifecycle finding; changing the expected error alone removes its pre-allocation guarantee. No production fix is authorized. |
| fixture083 Directional adapter | probe38 | probe38: layer3 err=-1, exact=0, visible=0, padding=1. PF16 source uses alpha65535 with Layer noise100/front8. Rejection occurs before equality; no actual-original pixel mismatch has been established. Need typed original/production admission and budget trace for this exact world. |
| fixture126 Kira Mode3 | PF8/16/32=10 | Same three codes; the test demands fail-close for the modulo-192-alpha 32×18 source. Need a replacement original-backed accepted-source contract across all three depths, preserving precommit failures. |
| fixtures162,163,164 | failed | Not rerun or edited: reserved Radial152–181 range. R08 owns adjudication; not silently dropped or passed. |
| fixture184 Radial Type3 host plumbing | mock10 | mock10 at SmartPreRender/checkout event expectation. Requires original public callback/order evidence before changing the lifecycle assertion. Not a measured pixel difference. |
| generic Directional back-only | probe10 / code1568 | Same: operation-budget rejection assertion. The UHD guard-mapped test is a budget contract, not an original-output reference. Need explicit current admission/budget proof plus retained atomicity checks. |
| generic Directional cleanup | probe134 | Same as fixture063; duplicate gate entry retained. |
| generic Distance production | probe75 | Current normal probe46 and sanitizer probe75. Both identify `pf32_blurred_budget_rejects`: 67×43 PF32, Sphere, Layer/Both, Median size500. Need original-backed acceptance/output plus replacement safety boundary; simply accepting success would remove the budget check. |
| generic Kira UI length | 3 failed tests | 8 tests run, 3 failures; length0 reject check reports ok=0 at all depths. Need original-backed zero-length contract; length301's reject check reports ok=1. No all-UI completion claim. |
| generic Radial baseline | probe38 | probe38; PF32 baseline center-domain assertion (`30*type + 8` for type1). Need fresh original boundary output and admission evidence; no final-byte pin is implicated by this code alone. |

inference:

The source-whitelist failures are consistent with later generalization, but that is not evidence permitting wholesale deletion of negatives. Allocation ordering, budget guarantees, host callback order and typed Layer rejection need distinct adjudication. These are open contract findings/blocked migrations, not newly proven Mac-versus-original pixel differences. No fuzz witness is emitted from an exit code alone.

changed_files:

- `orchestra/reports/R07-check-items.py`: sequential confined rerunner, restoring any generated tracked conformance reports.
- `orchestra/reports/R07-package.py`: streaming evidence archive/manifest writer.
- `orchestra/reports/R07-contracts-evidence.tar.xz`, `R07-contracts-manifest.json`.
- This report. Later groups append their artifacts below.

verify:

```sh
bash scripts/setup_ae_sdk_links.sh
python3 -B orchestra/reports/R07-check-items.py --group contracts
python3 -B orchestra/reports/R07-package.py contracts
git diff --check
```

Expected: ten command exits1; no source/assertion or conformance-pin changes. The archive checksum can change with temporary paths; every listed member digest must verify. All child execution temporaries use `orchestra/state/R07-gate-contracts-and-bindings`, `OLM_TEST_JOBS=2`, MAIN's existing absolute-path Python and assets. The driver never runs reserved fixtures152–181.

next:

Resolve source-whitelist assertions by capturing all affected positive/mutation outputs twice through a current registered original worker; retain independent malformed-world, alias and lifecycle checks. Investigate the allocation/budget and callback contracts separately; production fixes require a follow-up ticket. R08 handles162–164. Group2/group3 adjudication follows below.

Group2 facts — F40 bindings and historical packages:

`R07-check-items.py --group f40` completed 100 commands sequentially: **3 exit0, 96 exit1, 1 exit2**. Then six focused commands passed after the refresh below. No whole-release rerun is inferred from the subset. `R07-f40-items.md` enumerates **all110** F40 records: 9 currently passing, 83 blocked, 11 installed/real-host obligations (including three historical identity preflights), four overlapping group1 contract findings and three reserved R08 records. The archived JSON records each command's full log and checks missing paths against MAIN. A blocked entry still requires a complete replacement proof; the inventory is not that proof.

| Group2 check | Fresh before | Fresh after |
|---|---|---|
| fixture012/013: Blur PF16 7×5 owner + tests | exit1 / exit1 | exit0 / exit0; 4 tests including tamper checks |
| fixture018/019: Blur PF16 retained owner + tests | exit1 / exit1 | exit0 / exit0; 4 tests including tamper checks |
| fixture020/021: Blur PF16 Legacy owner + tests | exit1 / exit1 | exit0 / exit0; 5 tests including mismatch/tamper checks |
| Remaining 94 commands in this measured F40 subset | 3 pass / 91 nonzero | Not repeated wholesale; unchanged consumers retained |
| ColorKeep missing historical worker | original checkout absent | registered F46 original outputs reproduce twice; complete legacy Mac lifecycle contract still fails |

`R07-refresh-blur-owner.py --apply` changes **only six runner SHA values** in three owner JSON reports, the Legacy report's canonical digest, and its two external test pins. All non-identity JSON fields, source/output hashes, row layouts, instruction counts, callbacks, padding and numerical assertions are unchanged. Each of seven owner rows is reproduced twice identically using the original AEX; each original worker is also independently executed twice with byte/metadata equality. Fresh UCRT-linked current production worker replays pass all seven cells, **12,056 bytes**, zero differences. The initial Legacy build omitted `olmblur_fullworker_helper.cpp`; the driver was corrected to use the existing smoke recipe, and the successful run is authoritative. The initial linker log is retained.

The Legacy row at20×16/Smoothness62.5 still has **369 differing bytes between its original worker and original public owner**, with status `fail_closed_public_mismatch`. This is the previously retained original-path difference, not a new Mac-versus-original finding. Its public mismatch count/output pin and tamper checks remain strict. No claim is extended to installed or native AE execution.

ColorKeep fixture033/034 investigation (`R07-colorkeep-oracle-probe.py`):

- Original historical worker `AEXCompat-issue1135-typed-iterate-suites` is absent; the cache has no identical historical worker pin.
- Registered F46 (`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`) runs the original ColorKeep AEX at all three depths twice. The existing expected hashes, suite sequences and public command completion checks pass in all six executions. PF8 `ad5a9e2d70f0adcc6318d340b3fa47ef4b5d89e79d9827554197da41d81da3dd`; PF16 `67b738b61c8197b32885019e6395612b7d065b42c8efd5070fc0ab3e84637392`; PF32 `5304a3f80f4ed6be0e210e9d925ac4fa7350feacb1035778a0adfc3edec9f469`.
- Current Universal ColorKeep build succeeds, binary SHA `bf001b1de9401233e8c3f8d7e066a9b02eac3e32cda9e6701aa9f82f5964c020`. The unmodified legacy probe exits4 before returning positive bytes. A diagnostic-only copy supplies full input dimensions/downsample/aspect and records bytes without changing any pass predicate. Classic PF8/PF16 then pass; Smart PF8/PF16/PF32 render with rc0 and preserve input/padding, but fail the legacy lifecycle/phase checks (`life=0 phase=1 iterate=1`).
- The diagnostic's five padded outputs are **600/600 bytes exact**, SHA `2e68fc7a643641652edb27b6400cbdb2358b10c438893a8c346f8efd1ef7aebe`, first mismatch null. These bytes do **not** close the callback/order or136-negative contract. No worker/report pin for this consumer is changed. The current bundle is a temporary comparison product, not an installed oracle; its regenerable build directory is deleted.
- The second hypothesis, that completing missing host dimensions alone restores the whole positive contract, is refuted by the callback results. The new boundary is lifecycle, not arithmetic; further callback/negative migration is left blocked rather than deleting these checks.

Missing package audit distinguishes real absence from lookup bugs. Blur v4 candidate/verify script, ColorKey toggle24 build identity, Directional exported-smart worker package, Distance fail-close Universal candidate and Radial cleanup candidate are absent in MAIN as well. The batch-UCRT request, Directional expf vectors and Radial Strength290 UCRT request exist in MAIN but some legacy consumers address only the worktree; those are explicitly recorded as resolution failures, not missing historical evidence. Original assets were not copied. Replacing those complete consumer contracts (including their independent source/host predicates) remains unfinished; static history alone was not used to renew pins.

Group2 inference:

The three Blur owner migrations are justified metadata updates for the exact retained cells. ColorKeep demonstrates why merely swapping an absent worker path is insufficient even when the new original oracle reproduces every positive hash: the live Mac host harness has a separate lifecycle contract. Remaining stale-source assertions need complete per-consumer original/current replay, and missing install/host receipts remain **requires real AE/Windows**. No six-command improvement is generalized to the full release gate.

Group2 changed_files:

- Three `refs/conformance/olmblur_pf16_{7x5,retained_tuples,legacy_retained}_exported_public_owner_20260813.json` reports.
- `tools/emulation/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py`: canonical digest only.
- `tests/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py`: generator/report pins only.
- `orchestra/reports/R07-{refresh-blur-owner,verify-blur-owner,colorkeep-oracle-probe,adjudicate-bindings}.py`.
- `R07-f40-items.md`, `R07-f40-evidence.tar.xz`, `R07-f40-manifest.json`; packaging driver extension and this report.

Group2 verify:

```sh
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"
"$PY" -B orchestra/reports/R07-refresh-blur-owner.py
python3 -B orchestra/reports/R07-verify-blur-owner.py
"$PY" -B orchestra/reports/R07-colorkeep-oracle-probe.py
```

Expected: seven current worker cases exact; owner reports reproduce twice; six focused commands exit0 (13 test methods total). ColorKeep diagnostic exits0 after recording the unresolved legacy probe4 and complete600-byte pixel equality; driver exit0 is not closure of fixture033. No numerical claims beyond the measured cells.

Group3 facts — support documentation and performance bindings:

The mixed R03 performance entry was rerun before changes: its two failures were invocation-executable prefix mismatch and stale command-catalog binding (the first reported lane varies with catalog iteration). `tools/perf/run_generic_beta_smoke.py --output orchestra/state/R07-gate-contracts-and-bindings/performance-current.json` then measured **20/20 HD/UHD cells successfully**, zero unavailable/failed cells. Pre/post dependency and toolchain identities match. The fresh measured report replaces `reports/generic_beta_perf_smoke.json`; no retrospective relabeling or verifier relaxation was used. The old report is preserved in the group3 archive and Git history.

| Group3 check | Before | After |
|---|---|---|
| Performance runner / R03 mixed entry | exit1, two binding failures | exit0; all36 standalone test functions complete, including tamper/timeout/failed-measurement checks |
| Canonical report strict `--verify-only` | old interpreter/worktree/catalog bindings | exit0 with fresh execution-pre-and-post provenance |
| Performance measured cells | stale report, no new measurement | 20 passed / 0 failed / 0 unavailable |
| Support documentation tests | 19 tests, 4 failures | 19 tests, 4 failures; timing binding is repaired, fourth test reaches an obsolete Radial policy assertion |
| Full generic gate | R05:45 PASS /8 FAIL /0 SKIP | **46 PASS /7 FAIL /0 SKIP**, fresh completed run, exit1 |
| Release aggregate | R05 `releasable=false` | Not rerun; unresolved contracts, bindings and host obligations prevent a completion claim |

`docs/BETA_SUPPORT.md` now quotes the measured Kira HD36.90s /528,908,288 bytes and UHD136.29s /1,559,150,592 bytes. The new bounded Radial paragraph records HD10.68s /284,622,848 bytes and UHD23.62s /801,767,424 bytes for the existing12 cases/geometry. Historical Radial measurements remain explicitly historical. These are hostless Mac performance observations, **not original-AEX pixel or native-AE evidence**. No supported-domain or numerical-exactness claim was expanded from timing data.

Remaining documentation failures, individually:

1. ColorKeep native-AE source binding: retained report expects `7d47836709f9a6dc76285ce249ed0de55a04329e0fa1900f7214553563a8301e`, current source is `5a8502ad3cd11a78f16cd800736fb53ac43c6c4abf2eacdebb192f3a1924e284`. Renewing this current native-host claim **requires real AE/Windows**; no source-only repin is made.
2. Dispatch-code text predicate: expects `PF_OutFlag2_SUPPORTS_SMART_RENDER` directly in Smoother v1 source. The current source lacks that literal. Replacing a source-string assertion requires a validated current registration/dispatch contract; the20 performance cells are not that proof. Blocked, assertion retained.
3. Parameter/geometry text predicates: first failure is the old Blur `width > 4096 || height > 2160` literal; the same test also contains obsolete Radial/Directional support restrictions. No blanket token deletion or expanded supported-domain assertion is made without fresh original-backed coverage. Blocked.
4. The performance/documentation test now passes the new Kira/Radial timing comparisons, then fails on absent `portable右端処理`. Current Radial arithmetic-policy documentation superseded that historical phrase. Adding the phrase solely to pass the test or silently removing its predicate would not establish the current policy's original-backed contract. Blocked; no Radial production or reserved fixture is edited.

The performance verifier deliberately retains exact interpreter, worktree, source, SDK and toolchain bindings. This report is valid in the measured R07 checkout. The orchestrator must remeasure from its release checkout before claiming a current binding there; copying paths or weakening identity checks is not part of this change.

Group3 changed_files:

- `reports/generic_beta_perf_smoke.json`: fresh20-cell measurements and execution provenance.
- `docs/BETA_SUPPORT.md`: measured timing/memory values and explicit hostless/worktree boundary only.
- `orchestra/reports/R07-finalize.py`, `R07-results.json`, `R07-bindings-evidence.tar.xz`, `R07-bindings-manifest.json`; packaging extension and this report.

Group3 verify:

```sh
export TMPDIR="$PWD/orchestra/state/R07-gate-contracts-and-bindings"
export TMP="$TMPDIR" TEMP="$TMPDIR" OLM_TEST_JOBS=2 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"
"$PY" -B tools/perf/run_generic_beta_smoke.py --verify-only reports/generic_beta_perf_smoke.json
python3 -B orchestra/reports/R07-check-items.py --group bindings
"$PY" -B scripts/run_olm_generic_beta_gate.py --report "$TMPDIR/generic-recheck.json" > "$TMPDIR/generic-recheck.log" 2>&1
```

Expected in this measured checkout: report verification0; documentation1 and performance tests0. A fresh performance run in another checkout uses `--output "$TMPDIR/performance-recheck.json"`; all20 cells must independently satisfy the unchanged budgets/shape/evidence checks. New timings need not equal these measurements.

Final next:

R07 is **blocked, not complete**. Six historical fixture commands and the mixed performance entry are repaired, but the requested release-gate closure is not achieved. Group1 needs per-contract admission/lifecycle/atomicity evidence (and separate production authorization where a real safety defect is confirmed). Remaining F40 consumers need complete replacement packages and twice-original/current-build proofs; the per-item inventory keeps their concrete failures visible. Documentation predicates need current semantic contracts rather than stale source snippets. Current installed/native-host evidence remains a separately authorized **requires real AE/Windows** task. R08 owns the reserved Radial152–181 fixtures. No measured genuine Mac-versus-original pixel mismatch was found in the new Blur/ColorKeep comparisons, so no fuzz-format numerical witness is manufactured.

Final verification and cleanup facts:

- Full generic gate:46 PASS /7 FAIL /0 SKIP. Remaining failures are Directional back-only and cleanup, Distance production, Kira UI length, Kira Windows-owner renewal (**requires real AE/Windows**), Radial baseline and support documentation.
- All three evidence archives pass SHA-256/member-count/member-digest validation. All R07 Python drivers parse; `git diff --check` passes.
- No task subprocess remains running. Scratch is3.0MiB after completed checks; regenerable ColorKeep products/build tree were removed and all temporary build contexts closed. No durable oracle worker was built or changed.
- Release aggregate was not rerun and no release status/manifest is promoted.

Offline retained-evidence verification:

```sh
python3 - <<'PY_VERIFY'
import hashlib,json,tarfile
from pathlib import Path
p=Path('orchestra/reports')
for name in ('contracts','f40','bindings'):
    m=json.loads((p/f'R07-{name}-manifest.json').read_text())
    with (p/m['archive']).open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==m['sha256']
    with tarfile.open(p/m['archive']) as t:
        assert len(t.getmembers())==len(m['files'])
        for row in m['files']:
            with t.extractfile(row['path']) as f:
                assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
r=json.loads((p/'R07-results.json').read_text())
assert r['status']=='blocked'
assert r['generic_counts']=={'PASS':46,'FAIL':7,'SKIP':0}
assert all(x['exit']==0 for x in r['blur_after'])
assert r['performance']['cells']==20 and r['performance']['status']=='PASS'
print('R07 evidence intact; release closure remains blocked')
PY_VERIFY
```
