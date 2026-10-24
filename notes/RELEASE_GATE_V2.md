# Release gate v2

Run from a worktree with MAIN's existing emulation venv, original AEX assets,
SDK links, Xcode, Rosetta, and cached F46/F47d/F51 workers available:

```sh
python3 -B scripts/run_olm_release_gate_v2.py
```

The script selects MAIN's Python automatically. It runs sequentially with
`OLM_TEST_JOBS=2`, fuzz `--jobs 1`, Xcode `-jobs 1`, and ticket-local temporary
files. `memory_pressure` is recorded before building. The default output is
`orchestra/state/R09-release-gate-v2/run`; an existing directory is rejected to
prevent stale reports passing. Use `--state orchestra/state/R09-release-gate-v2/another-run`
for a new run. Each command has a log, command line, exit code and elapsed time.
`summary.json` records stage PASS/FAIL and counts. Failures do not skip later
stages. Regenerable Universal bundles are removed after checks; hashes remain.

1. **Framework:** discovers every `tools/fuzz/test_*.py`. Records test and skip
   counts; optional integration tests remain explicitly skipped. This checks the
   measurement machinery, not native AE.
2. **Build:** builds ten Universal Release bundles through `build_F47_bundles.py`.
   Requires both slices and records executable SHA-256s. These are temporary
   candidates, not installed identities or durable reference oracles.
3. **Corpus:** recursively inventories all saved JSON files, including auxiliary
   and nested corpus directories. Replays with the recorded hash-bound worker;
   no oracle override or rebaseline. Ordinary acceptance is complete saved-result
   equality, including historical refusals/mismatches. It proves regression
   stability, not that every saved output is correct. Empty plugin corpora are
   counted explicitly. New original guest stops that break saved-result equality are retried once alone with
   `--case-timeout 120`. A persistent stop is ORACLE-STOP only if each affected Mac
   route produces the saved **original reference** hash, the saved original was
   successful, and unaffected routes still match. A missing saved reference,
   changed Mac hash, Mac error, harness error, or missing worker fails. ORACLE-STOP
   is neither a fresh oracle comparison nor a pixel mismatch.
4. **Fresh seeds:** 2026 and 2027, 300 cases each for all ten source adapters.
   The decision uses Smart, except Smoother v1 Classic, following T14's advertised
   ownership. Full route results and witnesses are retained. E=exact, M=mismatch,
   R=Mac refusal/rejection, U=uncompared/other unfinished comparison. Any M,
   framework error, unresolved cleanup, or incomplete campaign fails. R/U remain
   coverage limitations and are never counted as E. Non-owner Classic diagnostics
   are retained but do not decide this Smart campaign.
5. **Bundles:** F47d n100 per plugin compares the actual arm64 Release executable
   against AEX. JSON completion/counts decide acceptance, since the wrapper's exit
   code does not aggregate child failures. F51 n100 plus every corpus compares
   x86_64 and arm64 slices; any difference or incomplete count fails. Equal
   refusals are distinguished from equal renders. Shared fake-host limitations,
   declared parameter profiles and default Kira ramps remain in scope boundaries.
6. **Selected tests:** the script explicitly lists R05's 45 green generic entries
   and eight exclusions with one-line reasons linked to R05/R07 reports. Test
   files are executed with the established generic gate collector (script-style
   probes execute their main). An excluded contract stays an open finding; these
   tests do not replace the entire historical fixture matrix.
7. **Static:** checks effective Release compiler flags for C/C++, Universal
   architectures and deployment 11.0; parses original PE PiPL and newly built Mac
   resource PiPL flags with the T14/F18 parser; verifies original AEX hashes and
   presence/hash of `notes/KNOWN_ORIGINAL_BUGS.md`. Resource flags do not prove
   host selector behavior, UI, persistence or GPU equivalence.

Exit 0 / `local_gate_pass=true` means all seven local stages passed. This is the
v2 local release decision. Installed identity, native host smoke and Windows
owner evidence are always REQUIRES-REAL-HOST, and `release_authorized` remains
false: local evidence alone cannot authorize a claim of AE-exact completion.
The 2026-08 gate remains unchanged as the legacy report, including its unresolved
intermediate-plane, historical-package and host-evidence obligations.

Exclusion evidence: [R05](../orchestra/reports/R05-regenerate-stale-bindings.md)
and [R07](../orchestra/reports/R07-gate-contracts-and-bindings.md).

The first completed run is recorded in [R09](../orchestra/reports/R09-release-gate-v2.md).
It rejects DistanceGradation's unpinned project deployment target (effective 26.2),
although the builder's explicit 11.0 override produced numerically passing bundles.
The project is unchanged; this finding requires a separate configuration ticket.
