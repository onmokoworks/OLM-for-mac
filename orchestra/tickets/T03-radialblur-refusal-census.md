## Goal
Attribute every Mac-side refusal in the RadialBlur fuzz campaign to the exact guard
that produced it, and rank guards by how many legal cases they reject.

## Facts
- Fuzzer: `tools/fuzz/` (read `tools/fuzz/README.md`). Campaign report:
  `reports/fuzz/radialblur_20261021.json` (do NOT load it whole into context; use
  small python one-liners that print counts).
- In 500 seeded legal cases the original AEX rendered 462. Mac refused 413 (Classic)
  and 370 (Smart) with error 516 (`PF_Err_BAD_CALLBACK_PARAM`), plus 19 Smart 710.
- `mac/OLMRadialBlur/*.cpp` has ~70 sites that can return 516.
- These refusals are deliberate "unsupported / unproven" admission guards from earlier
  work. They are the largest compatibility gap: Windows renders these inputs.

## Steps
1. Add refusal attribution WITHOUT changing behavior: e.g. a compile-time-off macro or
   an env var (`OLM_REFUSAL_TRACE=<file>`) that appends a stable guard id
   (function + short tag) when a guard refuses. Output bytes and error codes must be
   identical with tracing on or off.
2. Prove no behavior change: replay `tests/fuzz_corpus/radialblur` (must remain 35/35
   `matches_saved`) and run `OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py`.
3. Make the fuzzer record the guard id per refusing route when tracing is available
   (small change in `tools/fuzz/adapters/radialblur.py`; keep it optional).
4. Re-run `--n 500 --seed 1 --jobs 4` and produce a ranked table:
   guard id, file:line, Classic count, Smart count, which parameters/profiles/depths
   trigger it (top 3 features), and the guard's comment/intent quoted in one line.
5. Write that table into your report and as `reports/fuzz/radialblur_refusals_20261021.md`.

## Done when
>= 95% of refusals are attributed to a named guard and the replay/tests still pass.
Do not remove or relax any guard in this ticket.
