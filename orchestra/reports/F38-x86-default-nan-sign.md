status: blocked

summary:
- Added operand-aware SSE generated-NaN correction to Blur's two convolution helpers; propagated NaNs retain their sign/payload and copy paths remain unchanged.
- Blur seed 1 n300 Smart improves 282/1/17/0 → 283/0/17/0; seed 31 improves 275/2/23/0 → 277/0/23/0 (E/M/R/U).
- Sign-only witnesses are seed1/99, seed31/214 and seed31/271; both post-fix campaigns have no pixel mismatch.
- Updated the one repaired Blur corpus expectation with production history; final replay is 39/39.
- All 6,119 prior exact campaign routes and 859 prior exact corpus routes retain their hashes. Strict all-corpus green remains blocked by 23 pre-existing KiraKira T06 saved-result drifts.

facts:
- Read AGENT_GUIDE.md, GOTCHAS.md, compatibility plan, Blur ledger rows and F37/C24 reports. Baseline commit: `395e5d8a`.
- F32 reference worker SHA-256: `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
- Original disassembly (MAIN read-only) includes MULSS/ADDSS at `0x18000202b`/`0x180002033`, `0x18000203b`/`0x180002044`, and DIVSS at `0x180002166`. The helper correction is at these arithmetic boundaries, not final-byte output rewriting.
- First differing words (little-endian): AEX `0000c0ff`, Mac `0000c07f`. Seed1/99 first word54, 10 differing words; seed31/214 word93, 11 words; seed31/271 word310, 14 words. Every differing word in each case is the default-NaN sign pair.
- Classic Blur seed1 remains 13/0/287/0; seed31 remains 14/0/286/0.
- Initial eager bit-check implementation: 4K horizontal RGB radius1 median 246.106 ms vs baseline 127.339 ms. Rejected for cost before production integration. Cold unordered-result branch: three paired seven-run medians baseline 132.048/130.740/131.968 ms, candidate 139.660/139.668/139.453 ms. This measures a full 3840×2160 horizontal convolution pass, not native AE end-to-end render latency.
- Direct arm64 FPCR.DN probe returns `7fc00000` for 0×infinity and restores FPCR. It cannot provide the SSE negative default NaN.
- No worker rebuild, MAIN modification, ledger/release-gate edit, push, stash or history rewrite.


All-plugin census (before → after, E/M/R/U; U retains budget, uncompared and no-write):

| Plugin/seed | Classic | Smart |
|---|---|---|
| colorkeep-seed1 | 74/131/95/0 → 74/131/95/0 | 300/0/0/0 → 300/0/0/0 |
| colorkeep-seed31 | 72/121/107/0 → 72/121/107/0 | 300/0/0/0 → 300/0/0/0 |
| olmblur-seed1 | 13/0/287/0 → 13/0/287/0 | 282/1/17/0 → 283/0/17/0 |
| olmblur-seed31 | 14/0/286/0 → 14/0/286/0 | 275/2/23/0 → 277/0/23/0 |
| olmcolorkey-seed1 | 0/300/0/0 → 0/300/0/0 | 300/0/0/0 → 300/0/0/0 |
| olmcolorkey-seed31 | 1/299/0/0 → 1/299/0/0 | 300/0/0/0 → 300/0/0/0 |
| olmdirectionalblur-seed1 | 4/284/12/0 → 4/284/12/0 | 286/0/12/2 → 286/0/12/2 |
| olmdirectionalblur-seed31 | 8/277/15/0 → 8/277/15/0 | 281/2/15/2 → 281/2/15/2 |
| olmdistancegradation-seed1 | 10/290/0/0 → 10/290/0/0 | 287/0/6/7 → 287/0/6/7 |
| olmdistancegradation-seed31 | 9/289/0/2 → 9/289/0/2 | 281/1/12/6 → 281/1/12/6 |
| olmkirakira-seed1 | 0/48/252/0 → 0/48/252/0 | 269/0/31/0 → 269/0/31/0 |
| olmkirakira-seed31 | 0/44/256/0 → 0/44/256/0 | 266/0/34/0 → 266/0/34/0 |
| olmsmoother-seed1 | 205/0/95/0 → 205/0/95/0 | 205/0/95/0 → 205/0/95/0 |
| olmsmoother-seed31 | 193/0/107/0 → 193/0/107/0 | 193/0/107/0 → 193/0/107/0 |
| olmsmoother2-seed1 | 0/0/300/0 → 0/0/300/0 | 300/0/0/0 → 300/0/0/0 |
| olmsmoother2-seed31 | 0/0/300/0 → 0/0/300/0 | 300/0/0/0 → 300/0/0/0 |
| olmtoondilate-seed1 | 0/0/0/300 → 0/0/0/300 | 300/0/0/0 → 300/0/0/0 |
| olmtoondilate-seed31 | 0/0/0/300 → 0/0/0/300 | 300/0/0/0 → 300/0/0/0 |
| radialblur-seed1 | 1/118/181/0 → 1/118/181/0 | 240/0/59/1 → 240/0/59/1 |
| radialblur-seed31 | 3/140/157/0 → 3/140/157/0 | 247/0/51/2 → 247/0/51/2 |

Corpus saved matches (baseline normalized / final):

| Corpus | Before | After |
|---|---:|---:|
| olmblur | 39/39 | 39/39 |
| olmcolorkey | 3/3 | 3/3 |
| olmdirectionalblur | 56/56 | 56/56 |
| olmdistancegradation | 145/145 | 145/145 |
| olmkirakira | 8/8 | 8/8 |
| olmkirakira_gate_off_T06 | 39/62 | 39/62 |
| olmsmoother | 29/29 | 29/29 |
| olmsmoother2 | 8/8 | 8/8 |
| olmtoondilate | 300/300 | 300/300 |
| olmtoondilate_T13 | 23/23 | 23/23 |
| radialblur | 35/35 | 35/35 |

Completed commands and checks:
- Ran `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/measure_F38.py`, independent `--plugin olmblur --resume`, `--after --plugin olmblur`, and full `--after --resume`. All completed, output redirected to ticket-local logs. Forty n300 campaigns completed (12,000 cases across before/after), plus 22 corpus replays (708 cases per phase).
- Ran `python3 tools/fuzz/rebaseline_corpus.py --plugin olmblur --corpus tests/fuzz_corpus/olmblur --report orchestra/state/F38-x86-default-nan-sign/after/olmblur-replay.json --production-rebaseline F38-x86-default-nan-sign`: one mismatch→exact update, retaining previous result/provenance. Input, reduction, configuration and both oracle objects are unchanged. Final Blur replay: 39/39.
- `sh tools/fuzz/bench_F38.sh` passes invalid arithmetic, qNaN/sNaN sign/payload, signed-zero and finite checks, and both actual convolution helpers with positive-default/custom-NaN inputs and opposing infinities. Final benchmark medians: baseline 132.898/133.942/132.306 ms, candidate 140.572/141.230/142.323 ms. Logs are committed; approximately 6% median overhead on this shared arm64 machine.
- Baseline extraction smoke: ran `run_F38.py --plugin olmblur --n 100 --seed 1 --jobs 1 --shrink-attempts 0 --budget-minutes 10` with `OLM_F38_BASELINE=1`, ticket-local TMPDIR/scratch/corpus/report. All 100 complete results equal the original baseline's first 100 cases. The full committed driver exercises the same extraction mechanism.
- `TMPDIR="$PWD/orchestra/state/F38-x86-default-nan-sign" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p test_framework.py`: 14 tests, OK, 1 skipped.
- `python3 tools/fuzz/summarize_F38.py`: 20 campaign pairs, 11 corpus pairs, 3 sign-only witnesses, zero exact regressions. All 6,119 prior exact campaign routes and 859 prior exact corpus routes retain their hashes. Non-Blur route-result objects remain identical across all 5,400 campaign cases and 669 corpus cases.
- RadialBlur oracle-only differences are retained: 36 rejection-diagnostic string changes; seed1 cases62/280 swap ok↔budget under the 10-second cap. Both Mac routes refuse those two cases before and after. There is no candidate verdict/hash regression. All other full campaign results are identical except the three repaired Blur cases.
- Final saved corpus matches: 685/708. T06's 23 refusal→exact drifts are identical in both phases. Final replay exits 1 only for T06; F37 already reproduced these using F30 and F32. This ticket does not migrate that unrelated corpus.
- No two numerical hypotheses were refuted. The eager implementation was rejected for cost; the cold-path implementation passed correctness checks.
- Automatic approval review rejected one combined report/cleanup command because it contained `rm -f`: “rm -f style commands are not permitted. Use a safer approach.” That command did not execute. Report writes were then run separately; the required blocked report records this rejection. No permission request or escalation was attempted.

inference:
- Checking both operands is necessary to distinguish newly generated default NaNs from identical-bit propagated inputs. The rare NaN path checks raw operand words, so it does not rewrite input default NaNs or custom payloads.
- The arithmetic wrappers retain existing host payload-selection behavior; they do not claim to emulate all SSE operand-selection rules. No admission gates changed.
- CPU-emulation/fake-host evidence is not native Windows/AE or GPU proof.

changed_files:
- `core/x86_float.h`
- `core/olmblur_helper.cpp`
- `core/olmblur_fullworker_helper.cpp`
- `tools/fuzz/adapters/olmblur.py`
- `tools/fuzz/run_F38.py`
- `tools/fuzz/measure_F38.py`
- `tools/fuzz/summarize_F38.py`
- `tools/fuzz/test_F38.cpp`
- `tools/fuzz/bench_F38.cpp`
- `tools/fuzz/bench_F38.sh`
- `tests/fuzz_corpus/olmblur/seed1_case000099_9b13c27c2f2e.json`
- `orchestra/reports/F38-evidence/measurements.json`
- `orchestra/reports/F38-evidence/benchmark-initial.txt`
- `orchestra/reports/F38-evidence/benchmark-and-kernel-tests.txt`
- `orchestra/reports/F38-evidence/framework-tests.txt`
- `orchestra/reports/F38-x86-default-nan-sign.md`

verify:
```sh
mkdir -p orchestra/state/F38-x86-default-nan-sign
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/measure_F38.py > orchestra/state/F38-x86-default-nan-sign/before.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/measure_F38.py --after > orchestra/state/F38-x86-default-nan-sign/after.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/summarize_F38.py > orchestra/state/F38-x86-default-nan-sign/summary.log 2>&1
sh tools/fuzz/bench_F38.sh > orchestra/state/F38-x86-default-nan-sign/benchmark.log 2>&1
git diff --check
```
Expected: the table above, zero exact/hash regressions, Blur corpus 39/39, T06 still 39/62, and passing kernel tests. Use --resume only for unchanged code.

The baseline driver extracts only the two baseline helper translation units into ticket scratch without changing the checkout. Generation uses the current default F32 worker; all replay groups explicitly use F32. Jobs=1, two seeds, n300, no shrinking. Initial replay instrumentation added the diagnostic flag to mismatch-result objects; the evidence extractor removes only that diagnostic key before comparing results. Final replay avoids this diagnostic-key difference.

next:
- Orchestrator should review the completed bounded Blur fix. Full green corpus acceptance requires the separately scoped KiraKira T06 migration already identified by F37.
- No additional sign-only residuals occur in these campaigns. Other mismatches/refusals and native AE/Windows proof remain outside this ticket.

Final hygiene: all started command sessions finished; no ticket emulator/build process remains. Regenerable build trees and benchmark executables were removed. Scratch is 89 MiB (logs, reports, generated corpus and tiny baseline source copies), below 5 GiB. Final `git diff --check` passes.
