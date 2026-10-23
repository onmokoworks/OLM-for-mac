status: blocked
summary:
- Ran release, generic, framework, and all corpus replays sequentially with OLM_TEST_JOBS=2; repeated release/generic after restoring SDK links.
- Bisected gate-self regression to F25 merge dd7d8fa1 and 748-byte DistanceGradation retained-fixture regression to F02 merge f7ce7e67.
- Final generic: 48 PASS / 5 FAIL / 0 SKIP; framework: 14 PASS; corpora: 686/708 saved matches, other 22 Smart refusal→exact with unchanged oracles.
- No process threshold trip; identified historical ellipse recursion and measured top 10 commands. Missing inputs and remaining unclassified release failures prevent completion.

facts:
- Source HEAD c67a52fb388110966df4c8712cc570af69163929, branch orch/I02-integration-finish.
- Exact stage commands, exits, timing, hashes, corpus transitions, per-command failure triage and bisection records: reports/integration_I02_evidence.json.
- Full logs and five-second cross-PGID samples: reports/integration_I02_logs.tar.gz; archive SHA-256 recorded in reports/integration_I02.md.
- Release exits 1: required return ZIP missing here; MAIN ZIP matches expected e582b0f368deb6dfbb34de2675e382d2222372705da043151d90dc895f7d7a0a.
- SDK-provisioned fixture runner: 19 PASS, 194 command FAIL, 3 installed-identity failures; 89 commands skipped. Top sampled command descendant count 2; release-stage tree at most 4 descendants. Only 17 commands identifiable in five-second samples, so these are lower bounds on actual peaks.
- Gate self-test: fe69053a passes; dd7d8fa1 and HEAD raise SystemExit(2) under OLM_SELF_SPAWN_CHILD=1.
- DistanceGradation: eight isolated revision probes; first parent a95eebfc passes two 2992-byte fixtures; f7ce7e67 and HEAD report 748 differing bytes on the first fixture. Existing harness does not print first mismatch index/value.
- Preflight: 302 commands, zero literal over-limit pools; old ellipse dispatch reaches inert main, all current tested dispatches exit 2 without calling main.
- Final generic: five failures, no timeouts. Framework 14 tests PASS. Corpus has 708 actual replays; unchanged saved mismatches remain, not an all-exact claim.
- Ignored Headers/Util/Resources links read MAIN SDK locations; no MAIN edits. No monitored process-group members remain; regenerable scratch directories removed.

inference:
- F25 breaks intentional mocked gate invocations by inheriting its child guard; test integration regression, not numerical evidence.
- F02 changes a retained numerical fixture result; which rendering agrees with original AEX requires a fresh witness, not a fixture-fitting patch.
- Four remaining generic failures are stale evidence/contracts, including the zero-ray negative contract superseded by F10. Release failures with missing assets or unresolved behavior cannot honestly all be assigned to (a)/(b).

changed_files:
- reports/integration_I02.md
- reports/integration_I02_evidence.json
- reports/integration_I02_logs.tar.gz
- reports/integration_I02_preflight.json
- orchestra/reports/I02-integration-finish.md
- orchestra/reports/I02-integration-finish-preflight.py
- orchestra/reports/I02-run-monitored.py
- orchestra/reports/I02-release-with-log.py
- orchestra/reports/I02-replay-corpora.py
- orchestra/reports/I02-summarize-processes.py
- orchestra/reports/I02-bisect-gate-self.py
- orchestra/reports/I02-bisect-distance.py

verify:
- Set OLM_TEST_JOBS=2, PYTHONDONTWRITEBYTECODE=1, and TMPDIR/TMP/TEMP to this ticket's scratch directory. Use exact commands and SDK/worker setup documented in reports/integration_I02.md; never overlap gates.
- `python3 -B orchestra/reports/I02-integration-finish-preflight.py` => exit 0, 302 commands, zero over-limit literal sites.
- `python3 -B orchestra/reports/I02-bisect-gate-self.py` => exit 0; parent good, merge/HEAD bad.
- `python3 -B orchestra/reports/I02-bisect-distance.py` => FIRST_BAD f7ce7e67e71e79fe99de37493b903c7f4aaeba57; 748-byte mismatch at merge/HEAD.
- `git diff --check` => clean.

next:
- Repair F25 self-test interaction; independently re-witness F02's numerical fixture change.
- Supply read-only worktree asset/worker resolution and current installed identities, then complete release-failure classification and full numerical runtime coverage.
- Reconcile stale generic evidence/negative contracts without changing evidence to claim unsupported PASS.
