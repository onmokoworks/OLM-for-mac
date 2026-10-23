status: done
summary:
- Verification and failure classification completed at 9ede338310809b508cd79a21e96090ff7fc65e5b; integration is NOT gate-clean.
- Requested fresh routes: 2,837 exact / 0 mismatch / 131 rejection / 32 uncompared (3,000 cases).
- Universal arm64/AEX: 941/0/46/13; x86_64/arm64: 1,764 equal renders + 46 equal refusals, zero differences.
- Generic gate: 23 PASS / 30 FAIL. Release aggregate aborts on an unavailable worktree archive; fixture and component failures retained.
- All 1,194 supplementary Classic mismatches are saved. No production code, gate, ledger, or pinned evidence was changed.

facts:

All commands used `OLM_TEST_JOBS=2` (ticket-specific override), sequential stages, redirected logs, MAIN's absolute-path Python venv and original assets, and existing cached workers. Exact argv, exit codes and durations are in the evidence archive's `commands.jsonl`. This is hostless AEX/production verification, not a native Windows or macOS After Effects run.

E/M/R/U means exact/mismatch/rejected-or-refused/uncompared. Only completed exact comparisons count as E. Smoother v1 uses Classic; the other primary columns use Smart. Bundle comparison uses seed 1; fresh source comparison uses seed 777. All ten Universal builds returned zero.

| Plugin | Corpus saved equality | Fresh n300 E/M/R/U | arm64 bundle/AEX n100 E/M/R/U | x86_64/arm64 render/refuse/diff |
|---|---:|---:|---:|---:|
| Blur | 39/39 | 300/0/0/0 | 100/0/0/0 | 139/0/0 |
| ColorKeep | 0/0 (empty) | 300/0/0/0 | 100/0/0/0 | 100/0/0 |
| ColorKey | 9/9 | 300/0/0/0 | 100/0/0/0 | 109/0/0 |
| DirectionalBlur | 83/83 | 297/0/1/2 | 100/0/0/0 | 183/0/0 |
| DistanceGradation | 147/147 | 287/0/4/9 | 95/0/1/4 | 246/1/0 |
| KiraKira, including T06/nested | 47/111 | 283/0/17/0 | 97/0/3/0 | 208/3/0 |
| Smoother2 | 8/8 | 300/0/0/0 | 100/0/0/0 | 108/0/0 |
| ToonDilate, including T13 | 323/323 | 300/0/0/0 | 100/0/0/0 | 423/0/0 |
| RadialBlur | 60/61 | 265/0/14/21 | 84/0/7/9 | 154/7/0 |
| Smoother v1 Classic | 29/29 | 205/0/95/0 | 65/0/35/0 | 94/35/0 |
| Total | 745/810 | 2837/0/131/32 | 941/0/46/13 | 1764/46/0 |

Corpus equality compares saved result objects, not just pixels. There were 769 top-level files and 41 nested T06 reductions. The 64 Kira differences are legacy result transitions: 23 top-level Smart refusal→exact; nested 23 refusal→exact and 18 mismatch→exact. Nested primary `oracle` objects are unchanged, but old files lack the new `oracles` ownership metadata; Classic changes there are 31 mismatch→refusal and ten mismatch→mismatch. No primary-route new byte mismatch was found in replay.

Radial `C46_seed1_case000280.json` changes Smart exact→uncompared solely because the original stopped before guest return. Retrying that file alone with `--case-timeout 120` still stops at RIP `0x180002860` (28.9388 seconds). Candidate SHA-256 remains `5a19de28aece7b23b644e5f2533da7f662677e3d6a837b9a96d88a53726487f8`. Classification: oracle-budget event, unresolved by the prescribed retry; not a measured byte regression.

Fresh supplementary Classic routes have 1,194 mismatches: ColorKeep 132, ColorKey 300, DirectionalBlur 299, DistanceGradation 294, KiraKira 39, RadialBlur 130. All witnesses are in `I03-evidence.tar.gz:witnesses/`; first witnesses are also loose files in `I03-witnesses/`. No shrinking or fixes were applied. First mismatching byte / expected→actual raw word bytes:

| Plugin | First case | First byte | Raw word bytes | Different bytes |
|---|---:|---:|---|---:|
| ColorKeep | 0 | 1 | 0000→0080 | 76 |
| ColorKey | 0 | 2 | 0000→8241 | 1061 |
| DirectionalBlur | 0 | 0 | 0000→e50e | 805 |
| DistanceGradation | 0 | 0 | 9f05→cf02 | 351 |
| KiraKira | 0 | 1 | 0000→0080 | 737 |
| RadialBlur | 1 | 0 | 00→b8 | 364 |

The 95 fresh Smoother v1 refusals are depth32. These and all U counts remain outside exactness claims.

Gate and test facts:

- Release fixture runner: 204 records: 34 exit0, 166 exit1, one exit127, three exit126 installed-identity failures; 89 commands skipped behind the latter failures (Smoother 28, Smoother2 47, ToonDilate 14). These are invocation/identity counts, not individual assertions.
- Release aggregate exits1 before final report: `Windows AE boundary return_archive digest mismatch`. The return archive is absent in this worktree. MAIN's original archive has the expected SHA-256 `e582b0f368deb6dfbb34de2675e382d2222372705da043151d90dc895f7d7a0a`. The contract archive matches `6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652`. The gate's root containment and path resolution were not bypassed.
- Generic gate: 23 PASS, 30 FAIL, zero SKIP.
- Five framework test entrypoints, integration enabled: adapters 5, framework 14, rebaseline 2, route-oracles 6, timeout-cleanup 7; all 34 pass. The sixth `test_colorkey_existing_F20.py` main fails at missing UCRT linkage.
- 349 plugin-related test files inventoried: 84 reused gate invocation records, 265 additional pytest invocations, with six script-style entrypoints rerun directly. Final file-invocation outcomes: 51 exit0, 284 exit1, 14 exit2/collection failures. Reused multi-module invocations can contain mixed results; this is not a count of individual test passes. Logs/inventory retain missing-input, binding, compilation, and assertion diagnostics.
- Standalone pytest also finds `test_run_olm_generic_beta_gate.py` 19 pass/one fail: real pytest's skipif decorator is not honored by the lightweight gate loader (expected77, got0). The gate's intended stdlib-loader rerun passes all 20. This is runner interoperability, not a pixel failure.
- Installed identity audit: all ten hash bindings invalid; all ten Universal/codesign checks true. Host-smoke audit: all ten invalid evidence bindings. These audits do not reinstall bundles or perform new AE host runs.
- Parameter-UI audit: ColorKeep, KiraKira and ToonDilate proven; seven invalid. Blur/ColorKey/Smoother/Smoother2 lack legacy worktree-relative AEX paths. Directional and Distance setup and Radial setup/selectors fail UCRT linkage; Directional/Distance dynamic checks also lack legacy AEX paths. Full tails and hashes are retained in `parameter-ui-full.json`.

Classified gate failures (complete command-by-command list in `I03-classification.json`):

| Classification | Fixture records | Generic entries | Evidence / boundary |
|---|---:|---:|---|
| (a) Missing UCRT link inputs | 71 | 22 | F31/F45/F46 below; compile failures, not pixel mismatches |
| (a) Admission assertion drift | 0 | 5 | R02/F41b below; changed acceptance policy |
| (b) Existing F40 stale bindings | 68 | 0 | Exact normalized-command F40 index/note retained; listed only |
| Existing F40 unresolved inputs/contracts | 31 | 0 | Includes installed identity/skip blockers; not reclassified as pixel regressions |
| (b) Windows-owner evidence binding | 0 | 1 | Kira owner report semantic/hash assertion |
| (b) Documentation/source/performance bindings | 0 | 1 | Full diagnostic: 19 tests/four failures; already present in I02 |
| Mixed performance binding + link failure | 0 | 1 | Executable-prefix and canonical command mismatch; selected harness compilation fails |
| Total | 170 | 30 | 167 failed fixture commands + three identity records |

Bisection facts: historical `core/` and `mac/` against the current test harness, support files and read-only fixtures/SDK. The primary search ran 216 probes for 24 boundaries; supplemental adjacent controls cover sanitizer/gamma/edge and six warp fixtures. Policy tests were separately bisected. This identifies source dependency/behavior boundaries; successful linking does **not** imply the historical whole test or all pixels passed. Detailed parent/merge results and logs are archived.

- F31 `1979c3a986b5c4541d37d2c4e6f47f739b08a5f3`: missing float UCRT helpers in Blur/ColorKey/Directional/Distance/Kira/Radial legacy harness link recipes. Direct controls cover 22 primary tests plus Blur sanitizer and both edge harnesses. Other same-symbol fixture failures are grouped by the demonstrated shared cause, not claimed individually full-bisected.
- F45 `d246aef871ae798548c94f1f450636f1e0e9ab29`: six Kira warp fixtures begin missing `_ucrt_cos`/`_ucrt_sin`; all six adjacent parent/merge compilation controls confirm this boundary.
- F46 `1a5b279e6ea05dd3443d3d9e4fe678a5fb4d1df0`: Smoother2 default/ROI/gamma harnesses lack `_ucrt_pow`; all three confirmed.
- R02 `8857fbc3077b355f036b0ea2dadc846a9cf507bd`: ColorKeep generic/ROI negative assertions begin failing after DEEP-flag checks are removed to match AEX bitdepth dispatch. Both parent passes/merge fails. The diagnostic 44 is a count of satisfied negative expectations, not a case index.
- F41b `7a0cd797d52c9564c1f89191488f095c73f11b02`: Blur lane, Distance pf32-unblurred and Radial budget assertions begin failing after Smart work/size caps are relaxed. All three parent passes/merge fails.
- Edge fixture169/170 print only `mismatch`; retained generated reports show four production child failures each and zero matching planes. Adjacent compile-only probes demonstrate the F31 link cause; these are not completed numeric comparisons.

Provenance and execution boundaries:

- Existing source reference worker SHA-256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- Existing F47d worker SHA-256: `8057af6313d851f7e00939400b6b64a302fd00addc8f22c0812715216c49c35b`.
- F51 plugin host SHA-256: `7a5bc8c328503b6cd3918ae1db9b29ef9b0d0e3f274ae31904de0354aa3f0f28`.
- Verified bundles are durable at `/Users/onmk/.cache/olm-emu/I03-bundles-545f06bd924497e5/bundles`, registered in `~/.cache/olm-emu/INDEX.json`. `I03-cached-bundles.json` contains all ten executable hashes. No worker was rebuilt and no plugin was installed into AE.
- First release attempt was interrupted to confine fixture scratch; authoritative rerun uses `I03-release.py`, which only appends the fixture runner's supported `--results-dir`. Legacy generators' changed reports were retained as evidence and restored before proceeding. No retained bindings were refreshed.
- The41 nested corpus files were discovered during F51 enumeration and replayed as a supplemental sequential stage after bundles; the reproduction driver now recursively enumerates them from the start. Initial framework-loader mistakes were superseded by direct integration entrypoints. These are execution deviations, not omitted cases.

inference:

The requested sampled rendering paths show no measured byte regressions, and both bundle slices agree on all 1,810 comparisons. This does not establish all-input equivalence: refusals, oracle stops, legacy Classic mismatches, failed/blocked unit invocations and skipped fixture commands remain. Gate regressions are primarily legacy harness link dependencies and assertions that no longer match admitted inputs. The integrated branch cannot be declared release-ready from this run. The additional Classic witnesses require separate ownership/behavior investigation; they were not silently dismissed or patched.

changed_files:

- `orchestra/reports/I03-integration-check.md` — this report.
- `orchestra/reports/I03-*.py` and `I03-pytest-requirements.txt` — scratch-confined verification, bisection, classification and packaging helpers.
- `I03-results.json`, `I03-classification.json`, `I03-cached-bundles.json`, `I03-artifact-manifest.json` — measured results and provenance.
- `I03-evidence.tar.gz` — 2,330 logs/reports/witnesses; all 1,194 mismatch witnesses included.
- `I03-witnesses/` — six loose first witnesses for review.
- External authorized durable cache/INDEX registration described above; MAIN, production, gates and ledger unchanged.

verify:

From this worktree, inspect/archive-integrity verification (no builds):

```sh
python3 - <<'PY'
import hashlib,json,tarfile
from pathlib import Path
p=Path('orchestra/reports');m=json.loads((p/'I03-artifact-manifest.json').read_text())
assert hashlib.sha256((p/m['archive']).read_bytes()).hexdigest()==m['sha256']
with tarfile.open(p/m['archive']) as t:
    assert len(t.getmembers())==m['files']
    for r in m['members']:
        assert hashlib.sha256(t.extractfile(r['path']).read()).hexdigest()==r['sha256']
assert m['witnesses']==1194
print('I03 evidence integrity OK')
PY
```

Expected: `I03 evidence integrity OK`. Archive SHA-256: `f3808d1d143ef480f4d97c36e33efcbcbaefd41f0d0865c5f961405f5dbb0037`.

Full independent rerun (long; each command completes before the next; scripts log under the ticket scratch). Existing MAIN venv/assets, SDK and registered workers are prerequisites. Do not parallelize stages:

```sh
bash scripts/setup_ae_sdk_links.sh
python3 -B orchestra/reports/I03-run.py gates
python3 -B orchestra/reports/I03-run.py units
python3 -B orchestra/reports/I03-run.py replay
python3 -B orchestra/reports/I03-run.py fresh
python3 -B orchestra/reports/I03-run.py bundles
python3 -B orchestra/reports/I03-bisect-links.py
python3 -B orchestra/reports/I03-run.py classify-followup
python3 -B orchestra/reports/I03-run.py classify-warp
python3 -B orchestra/reports/I03-run.py parameter-ui
python3 -B orchestra/reports/I03-summarize.py
python3 -B orchestra/reports/I03-classify.py
```

Expected on this revision/environment: gate failures above, no requested-route fresh or bundle byte mismatches, no slice differences; oracle timeout counts can depend on execution resources. Driver exit0 indicates completed orchestration, not passing child checks. Exact child argv and return codes are in `commands.jsonl`. For a single supplementary witness, use MAIN's Python with `tools/fuzz/run.py --plugin <plugin> --replay orchestra/reports/I03-witnesses/<plugin>/<file>.json --jobs 1 --case-timeout 120 --scratch orchestra/state/I03-integration-check/recheck --report orchestra/state/I03-integration-check/recheck.json`.

next:

Separate tickets should repair legacy harness UCRT link recipes (F31/F45/F46), adjudicate R02/F41b admission assertions, resolve the existing F40 input/binding blockers, and investigate Classic witnesses. Worktree-aware legacy asset lookup and release archive resolution need their own changes. Re-run affected fixtures and the 89 skipped commands after those fixes; investigate the persistent Radial oracle stop separately. No evidence repinning or production repair belongs to I03.
