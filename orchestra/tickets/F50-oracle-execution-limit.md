# F50: reference worker — "execution stopped before the guest returned" (uncompared cases)

## Facts
- RadialBlur and DistanceGradation have uncompared Smart cases where the original AEX does not finish in the F46 worker:
  `aex_guest_error: ... execution stopped before the guest returned (RIP=0x1800...)`. Examples:
  `tests/fuzz_corpus/radialblur/C49_seed1_case000117.json` (RIP 0x180002cc3; it succeeded on a standalone 60 s retry),
  `tests/fuzz_corpus/radialblur/C46_seed1_case000280.json` (RIP 0x180002860; succeeded at 120 s).
  So the stop depends on load/time, which makes verdicts non-deterministic. See C48/C49 reports.

## Do
1. In a copy of the F46 worker source (`~/.cache/olm-emu/src-F46/`), find what stops execution: wall-clock emu timeout,
   instruction-count limit, or the harness's per-case timeout. Report the exact mechanism and default values.
2. Make the stop deterministic and generous: an instruction-count budget (not wall time) high enough that every case in
   S01's DG/Radial uncompared lists that is merely slow completes. The harness timeout must exceed it. Keep a hard
   upper bound so a real hang still ends.
3. Build `~/.cache/olm-emu/worker-F50-budget/`, INDEX entry, and commit the patch and build script under
   `tools/emulation/aexcompat_patches/`. Never edit `04_Tools/AEXCompat*`.
4. Prove the worker is otherwise identical: every corpus of every plugin replays byte-identically under F50 vs F46.
   Rerun RadialBlur and DistanceGradation seed 1 n300 and report how uncompared moves (to exact / mismatch / refusal).
5. Propose (do not apply) switching the fuzz default worker to F50 in `next`.

## Rules
1-2 processes; `memory_pressure` >= 30% free before the Rust build; delete build trees afterwards.
No plugin source changes; report any new mismatch it exposes as a finding.
