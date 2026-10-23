status: blocked

summary:
- Reproduced Smart seed 1 n300: 281 exact / 2 mismatch / 17 refusal; no production change or cluster promotion.
- Classified PF32 Legacy coefficient witnesses as `ucrt-math`; deferred their expf boundary to F28 as instructed.
- Located the Legacy and non-Legacy nonfinite payload boundary in original AEX ADDSS instructions; Unicorn disagrees with both arm64 and macOS x86_64/Rosetta.
- Gate-off is rejected: seed 1 admits 5 mismatches, fresh seed 11 admits 1; all 563 predecessor exact cases remain unchanged.
- Committed optional instruction tracing, independent scalar replay, compact evidence and reproduction driver; sanitized corpus remains 39/39 unchanged.

facts:

Base: `4ae2f4f8`, branch `orch/C24-olmblur-smart-r6`. Read AGENT_GUIDE, plugin ledger restrictions, compatibility plan, GOTCHAS, T09/C05/C10/C12/C15/C21 reports and F10/F12 method. No production renderer/core, corpus expectation, release gate, ledger, other plugin, MAIN, external emulator or cached worker was changed. No reference-worker rebuild, push, stash, history rewrite or installation. All campaign jobs=1. Scratch and compiler temporary files are inside this ticket's orchestra/state directory.

Evidence: `reports/fuzz/olmblur_C24_diagnostics.json`, SHA256 `178be3ea800a37a9cb68baa325734aad7dfa185bc5c0313b3d033781441728b2`. It retains residual case definitions and input hashes, oracle/public results, complete paired helper comparisons, 432 independent instruction-matrix rows per probe, first native scalar differences per case, report hashes and provenance. Repeated instruction observations are compacted; the committed driver regenerates full observations.

| Identity | SHA256 |
|---|---|
| MAIN/plugins_2025/OLMBlur.aex | f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b |
| Cached radial_noop_highdepth_reference_20261002 worker | 9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7 |
| Unchanged mac/OLMBlur/OLMBlur.cpp | cfe0cf913fb0757fe4149502c9a6bd9704450c7d8cfba24b041c2d6e0c495786 |
| Unchanged core/olmblur_fullworker_helper.cpp | 0c0643143abafd5bd5635fd18755a95e8a297b38786b58913e3af2f5df5c6ad2 |

**Census and admission experiment.** Executed `run.py --plugin olmblur --n 300 --seed 1 --jobs 1`, explicit cached worker, shrink-attempts 0, scratch corpus. Executed `blur_campaign_C12.py --blur-small-off --blur-sanitize` for seeds 1 and 11, n300/jobs1. Fresh production seed 11 also uses `--blur-sanitize`. Exact complete commands are in the reproduction driver below; each command's output was redirected to its scratch log.

| Seed | Production E/M/R | Scratch gate-off E/M/R | Exact unchanged | Refusal->exact | Refusal->mismatch |
|---|---|---|---:|---:|---:|
| 1 | 281/2/17 | 293/7/0 | 281 | 12 | 5 |
| 11 | 282/4/14 | 295/5/0 | 282 | 13 | 1 |

All oracle objects and Classic results remain identical under the experiment. The complete sanitized gate-off campaigns contain no sanitizer/error result. They disable both the small Legacy tuple refusal and the small PF32 source scan, exclusively in scratch. No rule is promoted from the 25 newly exact individual cases. Seed-1 rejected admissions are 116, 194, 220, 290, 299. Production's 17 refusals remain 15 PF32 Legacy and 2 PF32 non-Legacy nonfinite cases.

**Largest group: PF32 Legacy coefficients — `ucrt-math`.** Paired public traces bind to the cached AEX output. Case 220 first differs in helper weights at stage 0, word 16: AEX `e6507f3f`, Mac `e5507f3f`. Case 272 first differs at stage 48, word 17: AEX `dca97d3f`, Mac `dba97d3f`. Values here are little-endian bytes. Static MAIN disassembly identifies builder `0x180009e10`, call site `0x180009e83 CALL 0x18000ccae`, expf thunk `0x18000ccae JMP [0x18000d0c8]`. The tracer records native host expf imports; production Legacy PF32 uses binary64 exp then float conversion. Per the ticket instruction, no expf substitution, frozen-reference reinterpretation or math candidate is attempted. The earlier C15/C21 frozen-fixture regression remains a negative control, not overridden here.

**Legacy nonfinite payload — oracle boundary.** Case 99's first paired helper difference is the output at stage 13, plane word 21: AEX `4623c1ff`, Mac `4523c17f`; all preceding helper records match. Final production output has 32 differing bytes / 17 words, first word 29 with the same two payloads. Optional instruction hooks capture raw register/memory words before and after ADDSS/MULSS/DIVSS without modifying them.

The first native scalar-replay difference occurs within the preceding helper (stage 12) at `0x180002108 ADDSS XMM12,XMM0`: operands `7fc12345`, `ffc12346`; Unicorn result `ffc12346`; arm64 FADD and macOS x86_64 ADDSS both return `7fc12345` (these are uint32 bit patterns). This is not a UCRT import. Isolated execution of the original OLMBlur instructions over 12×12 inputs × 3 operations gives 432 conditions: x86_64 matches 420 / differs 12, arm64 matches 396 / differs 36. For case 99's 17,874 observed nonfinite operations, native scalar replay differs 11 times on x86_64 and 21 on arm64. These are isolated-operand replay counts, not counts of independently paired Mac renderer instructions.

**Non-Legacy source refusals.** Cases 116 and 290 bind to the cached worker with gates bypassed. First paired helper-input difference is at stage 6: plane words 0 and 1 respectively, again AEX `4623c1ff`, Mac `4523c17f`. First native scalar boundary for case 116 is `0x180001362 ADDSS XMM4,XMM0`, stage 0, the same two NaN operands/results as case 99. Across both cases: 29,527 observed nonfinite operations, 189 x86_64 replay differences and 225 arm64 differences. Thus widening the source predicate would admit an unresolved oracle contract.

**Invalid-operation NaN sign is a distinct port boundary, mixed with the oracle issue.** Case 194 first differs at helper-output stage 1, word 9: `0000c0ff` vs `0000c07f`. First scalar boundary is `0x1800017a7 ADDSS`, +inf + -inf: Unicorn/x86_64 yield `ffc00000`, arm64 `7fc00000`. Case 299 first differs at stage 1, word 131; first scalar boundary is `0x18000203b MULSS`, +inf × 0, with the same sign split. However both cases also reach Unicorn/x86_64 payload disagreements: case 194 at `0x1800017b8` stage 14; case 299 at `0x180002119` stage 0. Replay differences (arm64/x86_64) are 7/1 over 886 observations for 194 and 267/124 over 5,944 for 299. A sign-only production correction is not implemented or claimed to close these mixed-domain cases.

**Verification and rebaseline table.** `blur_campaign_C12.py --blur-sanitize --replay tests/fuzz_corpus/olmblur` returns strict 39/39 matches_saved. Smart corpus transitions: 38 exact->exact, 1 mismatch->mismatch, zero changes. No rebaseline required. The scalar arm64 harness is ASan/UBSan enabled, exits zero, and emits no stderr; x86_64 scalar execution also exits zero with empty stderr. Both trace variants bind to the cached worker. `verify_blur_C24.py` passes every assertion; `bash -n tools/fuzz/recheck_blur_C24.sh` and `git diff --check` pass. The full shell wrapper was not rerun after assembling it; its constituent commands above were run, and the aggregator was run on their results.

Instrumentation development encountered an assertion when disassembly extended into the following function, then an empty pending-observation KeyError at a branch target. The final hook scanner stops at RET and ignores after-hooks without a preceding observation; final completed traces and oracle bindings above validate that repair. These were instrumentation failures, not numerical hypotheses. No permission rejection occurred.

inference:
- No numeric cluster is closed and Smart exact has not increased. The 3-cluster promotion threshold is not claimed.
- Coefficient promotion is deferred to F28 by explicit ticket instruction. Nonfinite admission is blocked by demonstrated Unicorn/native SSE disagreement; encoding the emulator's payload preference in the port would target the wrong reference contract.
- Invalid-operation NaN sign remains a real, separately actionable port concern. These mixed-source witnesses do not establish a safe independent admission rule; a future ticket should isolate it after fixing or explicitly resolving the oracle's payload contract. This report does not claim sign normalization is impossible or experimentally refuted.
- Stop with status blocked: remaining broad PF32 Legacy/nonfinite promotion lacks an acceptable math/oracle contract. This is an external-boundary stop, not the two-refuted-hypotheses condition. No general finite-only Legacy admission proof was established here.
- Evidence is CPU AEX emulation/fake-host and macOS native scalar execution. Rosetta is not native Windows; no AE/GPU/UCRT exact claim is made.

changed_files:
- tools/emulation/trace_olmblur_legacy_C15.py — optional raw nonfinite operation tracing.
- tools/emulation/trace_olmblur_stages_C12.py — same optional tracing for non-Legacy helpers.
- tools/emulation/olmblur_nonfinite_trace_C24.py — shared register/memory SSE observation hooks.
- tools/emulation/probe_olmblur_nan_C24.py — original AEX instruction matrix and arm64/x86_64 operand replay.
- tools/fuzz/verify_blur_C24.py — diagnostic assertions and compact evidence generation.
- tools/fuzz/recheck_blur_C24.sh — serial scratch-only reproduction driver.
- reports/fuzz/olmblur_C24_diagnostics.json — measured evidence.
- orchestra/reports/C24-olmblur-smart-r6.md — this report.

verify:

From this worktree:
```sh
bash tools/fuzz/recheck_blur_C24.sh
```
Expected: production seed 1 281/2/17 and seed 11 282/4/14; gate-off 293/7 and 295/5; all paired traces cached_binding=true; each scalar matrix 432 conditions, 36 arm64 differences / 12 x86_64 differences; sanitized corpus 39/39; final `PASS: 563 base-exact campaign cases unchanged under bypass; corpus 39/39 unchanged; instruction boundaries reproduced`. Generated reports and logs remain in `orchestra/state/C24-olmblur-smart-r6/`; committed evidence/corpus are not overwritten. Compiler binary hashes may vary with temporary build paths.

To recheck the existing scratch results without rebuilding:
```sh
python3 tools/fuzz/verify_blur_C24.py --scratch orchestra/state/C24-olmblur-smart-r6 --report orchestra/state/C24-olmblur-smart-r6/verified.json
bash -n tools/fuzz/recheck_blur_C24.sh
git diff --check
```

next:
- F28: integrate the agreed UCRT math reference and revisit Legacy PF32 coefficients, preserving the frozen fixture as a negative control.
- Oracle follow-up: validate/fix SSE NaN propagation using the OLMBlur instruction witnesses; pin the resulting reference worker before remeasuring nonfinite cases. Native Windows validation remains distinct from Rosetta evidence.
- Port follow-up: isolate invalid-operation NaN sign from input-payload selection, then evaluate general arithmetic semantics and nonfinite admission against a resolved oracle; preserve all finite exact cases.
- Revisit finite-only Legacy admission with independent seed/boundary proof after the coefficient contract is resolved. No per-case promotion list is supplied.

Final hygiene: scratch is 43 MiB, below 5 GiB; temporary build trees were automatically removed. No task emulator/build process remains. Python syntax parsing passes for all five changed/new Python files. `git diff --name-only 4ae2f4f8 -- core mac tests/fuzz_corpus` is empty.
