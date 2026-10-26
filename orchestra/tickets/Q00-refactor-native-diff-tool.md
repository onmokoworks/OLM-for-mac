# Q00: tools/refactor/native_diff.py: native output differential between two git revisions

Read `orchestra/REFACTOR_SPEC.md` first.

## Do
- Write `tools/refactor/native_diff.py`, modelled on `tools/perf/ref_vs_fast.py`, which already builds native harnesses through the fuzz adapters:
  - `--plugin P --base <sha> [--head <sha|WORKTREE>] --cases N --seed S --arch arm64|x86_64|both --build reference|fast|both`.
  - Build the plugin's harness from the base revision (use `git worktree add --detach` into the scratch dir, or `git archive`) and from the current tree.
  - Generate cases with the fuzz samplers, covering every sampler and option listed in the spec's G1 and including 4K cases.
  - Run both builds, compare raw output bytes plus refusal and error tags, and print a JSON summary: counts, plus the first 10 differences with case parameters.
  - x86_64 runs under Rosetta (see V01 for how it was done).
- Make it support every plugin, including Smoother v1 (Classic), ColorKeep and ToonDilate.
- Self-test: base = HEAD vs HEAD gives 0 differences for all 10 plugins (small N is fine). Then plant a deliberate 1-ulp change in a copy and confirm the tool catches it. Revert the plant.
- Add a short README section in `tools/refactor/README.md`.

## Done when
- The tool works for all plugins on both archs and both builds, and the self-tests pass. Record the self-test commands in the report.
