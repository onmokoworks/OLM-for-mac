# R09: release gate v2 — one reproducible command built on current end-to-end evidence

## Why
The 2026-08 release gate (`scripts/run_olm_release_gate_20260806.py`) verifies intermediate planes of the old proof
method and depends on historical packages; R05–R08 showed most remaining failures are unrecoverable bindings, not pixel
problems (R07: 83 of 110 F40 records blocked). Meanwhile the fuzz framework, corpora, Universal bundle checks (F47d/F51)
and I03 give stronger end-to-end evidence. Keep the old gate as a legacy report; add a v2 gate that decides releases.

## Build `scripts/run_olm_release_gate_v2.py` (single command, sequential, OLM_TEST_JOBS=2, logs + JSON summary)
Stages, each PASS/FAIL with counts:
1. Fuzz framework unit tests (`tools/fuzz/test_*.py`).
2. Build the ten Universal Release bundles (`build_F47_bundles.py`) and record executable SHA-256s.
3. Every corpus replay for all ten plugins (`run.py --replay`) with the documented rule: saved-result equality; an
   original-side guest stop is retried once alone at `--case-timeout 120` and, if it persists, counted as ORACLE-STOP
   (not a failure) only when the Mac output hash equals the saved reference hash.
4. Fresh-seed Smart campaign (Smoother v1 Classic): a fixed release seed set (e.g. seeds 2026, 2027) n300 per plugin.
   FAIL on any mismatch. Report E/M/R/U.
5. Bundle checks: `verify_F47d.py` arm64 bundle vs AEX n100 per plugin (0 pixel mismatch) and `verify_F51.py --n 100`
   x86_64 vs arm64 slices (0 differences).
6. Plugin unit tests that are currently green (record the selected list in the script with a one-line reason per
   excluded legacy test, pointing to R05/R07 reports).
7. Static: Release configs (`-ffp-contract=off -fno-fast-math`, arm64+x86_64, deployment 11.0), PiPL flags equal to the
   originals (T14), and `notes/KNOWN_ORIGINAL_BUGS.md` present.
Real-AE items (installed identity, native host smoke, Windows owner evidence) are listed as REQUIRES-REAL-HOST, never pass.

## Do
Write the script and a short `notes/RELEASE_GATE_V2.md` (what each stage proves and does not prove), run it to completion
once, and commit the summary under `orchestra/reports/`. Do not modify or delete the legacy gate.

## Rules
1-2 processes; jobs=1 for fuzz; check `memory_pressure` before bundle builds. No plugin production changes; any
mismatch is a finding with a saved witness.
