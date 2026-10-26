# B01: refusals that depend on memory addresses (nondeterministic black frames)

depends: Q04-refactor-olmdirectionalblur

## Finding (Q02, 2026-10-26)
- In `native_diff`, the same base binary (sha `a60d18f6…`, arm64 reference) gave two different results for the same ColorKey case in two runs. One run refused with error 516, tag `PrepareSmartRenderWorld:smart-public-admission`. The other run rendered.
  - Case: seed 909, generator index 4935, PF8, input 3×1, full 9×4, downsample 1/4, request [1,0,3,1], padding 1 byte. Details are in `orchestra/reports/Q02-refactor-olmcolorkey.md` (G1).
- Likely cause (inference; prove or refute it):
  - `DisjointPayloads` in `mac/OLMColorKey/Render.inc` measures each world as `rowbytes * height` through `CheckedPayloadBytes`.
  - The bytes a world really touches are `(height-1)*rowbytes + width*pixel_bytes`. With row padding, the last row's tail is not part of the allocation.
  - So when the allocator places a fresh allocation (the Smart `storage` vector, or the output) right after the input, the check sees an overlap that does not exist. The result then depends on the heap layout.
- The same helpers exist in `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`.

## Do
1. Reproduce. Run the case many times. Try forcing the adjacent placement, for example with a custom allocation in the harness that puts the buffers back to back. Record the refusal rate.
2. Audit all 10 plugins and `core/` for checks whose result can depend on addresses, timing or uninitialised memory: pointer-overlap tests, span computations, wall-clock budgets, `std::thread` order, uninitialised reads (use the sanitizer builds or `MallocScribble`). List each one with its file:line.
3. Fix the causes in general code. Overlap checks must use the real touched span. Any refusal must be a deterministic function of the request, not of the heap layout. Do not remove a safety check that guards a real overlap.
4. Prove it:
   - `tools/refactor/native_diff.py` against the pre-fix base for each touched plugin, 3,000 cases, both archs and builds. Every difference must be "base refused, head rendered", and each rendered output must match the oracle (check those cases against the default worker).
   - Run each touched plugin's corpus replay (Mac side).
   - Run the reproduction from step 1 after the fix: 0 refusals over at least 1,000 runs.
5. Report the list from step 2, including the items that were not fixed and why.

## Rules
- Coordinate with the running Q tickets: touch only the admission and span helpers. If a Q ticket for the same plugin is running, keep your diff minimal so the merge stays simple.

## Resume note (orchestrator)
- The first run made the source fixes and the reproduction tools. It stopped during validation because the model session ended. Its work is the WIP commit at `refs/keep/B01a` (`git merge refs/keep/B01a` first to get it back); its report is in that commit.
- Since then, readability refactors of RadialBlur (Q01b) and OLMBlur (Q06) have merged. Q04 (DirectionalBlur) will merge too. First merge `codex/public-beta-roi` into this branch and re-apply your span fixes to the split files. Keep the change minimal.
- Then finish the validation: Do steps 4-5, using `tools/refactor/native_diff.py` per touched plugin against the merge base.
- Size rule: keep the reproduction tooling to one small script plus its test. Delete `replay_mac_B01.py` if the shared tools cover it.
- Write the report in plain engineering terms (span arithmetic, false refusal), describing only what was measured.
