# Q08: delete one-off investigation scripts that nothing uses anymore

depends: Q07-refactor-olmsmall

Read `orchestra/REFACTOR_SPEC.md` (the size-limits section).

## Why
- `tools/` and `scripts/` hold about 545k tracked lines. Most of it is one-off probe, verify, summarize, recheck and measure scripts from finished tickets: about 275 files in `tools/fuzz` alone.
- The git history keeps them, so they do not need to stay in the tree.

## Do
1. Build the keep list: everything reachable from the current entry points.
   - `tools/fuzz/run.py` with its adapters, harnesses, geometry, sizes, core and declarations; nightly; rebaseline_corpus; replay
   - `tools/perf/ref_vs_fast.py`; `tools/refactor/`
   - `tools/ae_smoke/`; `tools/emulation/`
   - `scripts/package_mac_plugins.sh`, `scripts/run_olm_release_gate_v2.py` and everything they call
   - `tests/` and what the tests import
   - files linked from README, docs, AGENT_GUIDE.md, orchestra/BRIEF.md or REFACTOR_SPEC.md
   Find reachability by imports, subprocess calls and path strings, not by guessing from names.
2. Delete the rest with `git rm` in one commit per directory. Write the deleted list to the report and to `notes/REMOVED_TOOLS.md` (paths plus the last commit that had them, one line each), so they can be restored with `git checkout <sha> -- <path>`.
3. Do not delete corpora (`tests/fuzz_corpus`), reference data, `decomp/`, `disasm/` or anything a test reads.
4. Gates: release gate v2 local stages pass; `tools/fuzz/test_*.py` / pytest suites that remain pass; nightly.sh `--hours 0.05` smoke runs; packaging still builds; one corpus replay per plugin gives the same results as before.
