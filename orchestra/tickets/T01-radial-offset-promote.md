## Goal
Promote the interrupted RadialBlur **Offset** fix into production
(`mac/OLMRadialBlur/OLMRadialBlur.cpp`) and prove no regression.

## Background (facts)
- The Codex session built and validated an Offset candidate on 2026-10-02 but was
  interrupted before promotion. The candidate file in /tmp is gone.
- It is reproducible: `tools/emulation/probe_radialblur_offset_20261002.py` has
  `before_source()` and `candidate_source(source, budget=True)`. Codex's last
  validated candidate was `candidate_source(before_source())` (with the budget).
- Reported results then: 390 offset conditions exact on O2/strict/sanitizer builds
  and Classic/Smart; 512x512 Quality5 Offset500 loop count measured ~5.30e8 vs new
  estimate ~5.75e8 under the 3.5e8 cap (see the probe_radialblur_offset_budget /
  _planes scripts in tools/emulation/). The regression over prior conditions
  (9,645 conditions / previously 57,870 public replays) had NOT finished.

## Steps
1. Read the three `tools/emulation/*radialblur_offset*_20261002.py` scripts
   (headers + argparse only first). Determine how to (a) regenerate the candidate,
   (b) check whether production already differs from `before_source()` (production
   may have moved since BEFORE_REVISION — if so, the candidate must be re-based:
   apply the same semantic diff to current production, do not overwrite newer work).
2. Write the candidate into production. Build per the existing RadialBlur build
   scripts (find them; do not invent flags).
3. Run the offset probe (390 conditions) and the existing RadialBlur public
   regression suites (look for `reports/radialblur_*_validation_20261002.json`
   producers and `tests/test_olmradialblur*`). Run long ones in background with logs.
4. Commit production change + any committed probe outputs that are small (<2 MB).

## Done when
Offset 390 exact AND previously-exact RadialBlur suites still exact (0 diffs,
0 new rejections), with counts reported. If anything regresses: do not "fix" by
editing expectations — report the first mismatch and stop (status: blocked).

## Update (orchestrator)
- Reference workers are rebuilt in `/Users/onmk/.cache/olm-emu/` (see `orchestra/reports/emu_index.json`
  and `orchestra/reports/T00-rebuild-reference-workers.md`). Use `radial_offset_reference_20261002`
  wherever the scripts expect `/tmp/radial_offset_bound_reference_20261002` (pass by argument).
  Binary hashes differ from recorded ones only because the build path is embedded; before relying
  on a worker, calibrate it: replay a few recorded original-AEX output hashes and confirm equality.
- The new fuzzer (`tools/fuzz/`, README) can also be used: after promotion, replay
  `tests/fuzz_corpus/radialblur` and run `--n 500 --seed 1`; report how the Offset mismatch
  cluster (PF8 Outer Offset, slot 6) changes. Corpus hash changes are evidence, not failures.
- A previous attempt of this ticket stopped on a permissions error; that is fixed.
