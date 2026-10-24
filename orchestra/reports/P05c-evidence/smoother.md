status: done
summary:
- Specialize only the PF16 classifier/edge-walker virtual-stack storage to 192/160 bytes; retain every virtual address and all kernel arithmetic.
- Heavy PF16 corpus00 improved from 2.143 to 1.418 s at 1080p and 8.555 to 5.766 s at 4K.
- Contract Classic campaigns: 516 exact, 284 original PF32 rejects, 0 mismatches and 0 Mac-only refusals; all 303 corpus records replay true.
- Before/after unit module exit statuses are identical; the new windows also pass 1,386 sanitized offset/width checks.
- One initial legacy test scratch-path deviation was corrected and both unit baselines rerun, as documented below.

facts:

| Depth | Before 1080p | After 1080p | Before 4K | After 4K |
|---|---:|---:|---:|---:|
| PF8 control | 1.495605 | 1.546868 | 6.169607 | 6.072230 |
| PF16 target | 2.142729 | 1.417640 | 8.555471 | 5.765996 |

`build_F47_bundles.py --plugins OLMSmoother` succeeded before/after for arm64 and x86_64. `ae_realism_audit.py --phase matrix --plugins olmsmoother --cases corpus00 --situations full 4k --jobs 1` used the Classic route and reported 4 OK / 2 expected PF32 refusals for both builds. Single-frame, shared-machine SDK-host timings; no native AE timing claim. PF8 keeps the original 4 KiB storage and has no claimed speedup.

- `sample PID 2 1 -file PATH` succeeded for both PF16 4K runs; host and sample returned 0. `_platform_memset` top-of-stack samples fell from 444 to 29. `read32` remains prominent; it was not retuned. Counts are sampled stacks, not call counts.
- `smoother_stack_bounds.py` propagates RSP across every reachable block and rejects unsupported/escaping RSP expressions. Classifier: 1,724 blocks / 45 stack-access sites, `[0x7a8,0x830)`; walker: 392 blocks / 28 sites, `[0x7d8,0x848)`, including wrapper return/argument writes. Chosen storage is padded to `[0x780,0x840)` and `[0x7c0,0x860)`. Source CFG hashes are in `smooth-stack-bounds.json.gz`. Generated CFG files were not changed.
- Other synthetic-memory users retain the full `[0,0x1000)` window through the SubHandler8Memory alias. Template methods keep the existing bounds checks and state/world/table translation; only the backing-array base and size are specialized.
- `smoother_memory_windows.py`: 1,386 byte-offset/width checks exact under fatal ASan/UBSan; bounds, unaligned native-pointer fallback and ptr translation passed. No first differing byte.
- Default seed 1 n300, before/after: 205 Classic exact, 95 original rejects. All 600 paired Classic/Smart statuses and output hashes are identical; no exact→non-exact. The original has no Smart advertisement; this default harness compares the existing Mac Smart wrapper against original Classic.
- Final realistic-v1 n100: seed 1 = 65 exact / 35 unavailable, fresh seed 2026102505 = 58 / 42. Odd-even-v1 n150 at max width 1920 / height 1080: seed 2026 = 92 / 58, seed 2027 = 96 / 54. Every unavailable case across these five campaigns is PF32, unsupported by original Smoother v1. No Classic mismatch or Mac-only refusal was observed.
- Standard saved-route replay: root 29, T15b 2, P02g-realistic 224, new P05c-stack-frames 48; all 303 have `replay_matches_saved=true`. New original-AEX witnesses cover PF8/PF16, four directional SDR patterns, key on/off and Tolerance 0/6/255.
- Final redirected before/after unittest module statuses: 12 invoked, 6 exit 0, 3 exit 1, 3 exit 5 (empty class collection), exactly the same modules. Module-level function suites: 2 invoked, the same 1 success / 1 failure. Existing evidence/asset failures remain; this is not an all-green suite claim.
- Workflow deviation: the initial baseline synthetic-stack test explicitly used its legacy `orchestra/state/F22-smoother-classifier-stack-ub` path despite TMPDIR. It created temporary files outside this ticket's scratch but within this worktree. The test removed its temporary files; the empty parent directory was removed successfully. The runner now overrides the module's SCRATCH global before loading tests, and both before/after suites were rerun using only the ticket scratch. No `/tmp` write, MAIN modification or oracle rebuild was performed by these corrections.
- Generated baseline/final bundles are registered at `~/.cache/olm-emu/P05c-smooth-before` and `~/.cache/olm-emu/P05c-smooth`; identities are retained in `smooth-cache.json`. The initial memory check was 61% free, above the 30% minimum.

inference:
- Zeroing bytes that the two literal CFGs cannot access was redundant. Bounded smaller storage preserves their initial zero values and every read/write address while removing most of this clearing cost.
- Remaining read32 translation work is a possible future performance topic; this ticket's measured target is already met without changing it.

changed_files:
- mac/OLMSmoother/Mac/OLMSmoother_port.cpp
- tests/fuzz_corpus/olmsmoother/P05c-stack-frames/*.json
- orchestra/reports/P05c-evidence/smoother_stack_bounds.py, smoother_memory_windows.py, smoother_witnesses.py, check_smoother_units.py
- orchestra/reports/P05c-evidence/functions.py, units.py, smooth-* and smoother.md
- orchestra/reports/P05c-blur-colorkey-smoother-performance.md

verify:
```sh
python3 orchestra/reports/P05c-evidence/smoother_stack_bounds.py
python3 orchestra/reports/P05c-evidence/smoother_memory_windows.py
python3 orchestra/reports/P05c-evidence/check_plugin.py olmsmoother smooth-recheck
python3 orchestra/reports/P05c-evidence/units.py olmsmoother smooth-units-recheck
python3 orchestra/reports/P05c-evidence/functions.py olmsmoother smooth-functions-recheck
python3 tools/fuzz/ae_realism_audit.py --phase matrix --cache "$HOME/.cache/olm-emu/P05c-smooth" --state orchestra/state/P05c-blur-colorkey-smoother-performance/smooth-performance-recheck --plugins olmsmoother --cases corpus00 --situations full 4k --jobs 1
```
Expected: stack intervals above; 1,386 sanitized checks; campaign counts above with 0 mismatches / Mac-only refusals and all 303 replays true; identical inherited unit statuses; 4 OK / 2 PF32 refusal timing rows. Run at most two build/emulator processes at once. The before/after unit comparison script temporarily restores the pre-ticket source in this worktree and uses `finally` to restore the candidate; it must not run concurrently with another source-consuming Smoother build/campaign.

next:
- No remaining requested Smoother implementation work. Native AE timing and restoration of historical unit-test dependencies are separate follow-ups.
