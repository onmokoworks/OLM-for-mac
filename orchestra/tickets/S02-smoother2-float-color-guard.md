# S02: Smoother2 refuses in real AE when a colour param's float value is not exactly byte/255 (`smartrender-decoded-colors@5403`)

## Facts (A02h, `orchestra/reports/A02h-real-ae-retest-downsample.md`)
- In real AE 2026, Smoother2 corpus case `tests/fuzz_corpus/olmsmoother2/.../seed1_case000067_65ee3b1d9cdf.json` (11x8 PF8) renders nothing. The trace shows `SmartRender:smartrender-decoded-colors@5403`.
- The guard `DecodedColorsMatch` (`mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp:364`) byte-compares the floating-point colour that `FetchParams` decodes against the legacy 8-bit `u.cd.value/255`. Real AE keeps colour params at higher precision, set from the UI, scripting, expressions or 16/32 bpc projects, so they can differ. The fake hosts derive float from 8-bit, so they always agree.

## Do
1. From disassembly (`decomp/OLMSmoother2*.c.txt`, P02f/U01 notes), confirm how the original reads the Key Color and Gamma Colors: the PF_ColorParamSuite floating-point call, the 8-bit `u.cd.value`, or both, and in which order and where.
2. Make Mac read colours exactly like the original, and remove the guard where the original has no equivalent check. If the original uses the float suite, Mac must use the float value AE gives, including when it is not byte/255.
3. **Oracle coverage.** Teach the fake host(s) and the F53/F54 oracle adapters to supply a float colour that differs from byte/255, as real AE does. Use an opt-in sampler flag, and keep default generation and replay identical. Then compare the original and Mac on such cases: Smart, PF8/16/32, several seeds, n100.
4. Check whether any other plugin has the same "float colour must equal byte/255" guard (grep `u.cd.value` and colour suite usage in all `mac/*`). Report them. Fix them in this ticket if they are the same pattern.

## Acceptance
- The A02h witness renders exactly against the original in the fake host, with its float colours reproduced.
- The new float-colour campaign shows 0 mismatches and 0 Mac-only refusals.
- Default fuzz seed 1 n300 shows no exact→non-exact.
- All corpora replay true, and `ref_vs_fast` is clean for the touched plugins.

## Rules
- Use 1-2 processes. Do not touch the release gate or ledger. The stop rule applies.

## Resume note (orchestrator)
- The first run's code change is in your worktree. The worker build failed only because of the spaces-in-path QEMU restriction; see the new "Building AEXCompat / Unicorn workers" section in `orchestra/BRIEF.md`. Build in the space-free locations it describes, then finish the float-colour campaigns, the A02h witness, all-corpus replay and `ref_vs_fast`.
