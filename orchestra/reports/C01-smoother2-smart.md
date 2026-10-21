status: done
summary:
- Smart seed-1 n300: 292 exact / 8 mismatch / 0 refusal → 300 exact / 0 mismatch / 0 refusal.
- Closed all four retained signature clusters through three general causes: classifier comparison order, SSE invalid arithmetic, and row-zero scanner termination.
- Fresh seed 2: 294/300 → 299/300 exact; retained corpus: 0/8 → 8/8 exact, with 8/8 matches_saved after rebaseline.
- Every base-exact Smart case stayed byte-identical; optimized and ASan/UBSan outputs agree for all 608 validation cases per change.
- One fresh-seed case and an independent two-NaN payload-priority boundary remain for follow-up; no native AE/Windows claim.

facts:

Provenance and commands:
- Starting commit: f87b3f1d6b2226a9744559974c86181eb4d7aa8e on orch/C01-smoother2-smart.
- Original AEX SHA-256: 7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7.
- Retained worker: /Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker, SHA-256 3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261. No emulator rebuild/substitution.
- `tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 2 --shrink-attempts 0` with ticket scratch/report/corpus arguments completed before and after: 292/8 → 300/0 Smart. Classic remains 300 refusals. Final unshrunk mismatch clusters: 0.
- Initial campaign report SHA-256: 7c20fc9c7fa59a43875dfea219ddd5ef93b62bbb5fd696a1e546d4711bdf02c6; final: eb413c05d018f2a241b6f48cbf6c4a36bbe45b8f53a85e3963182c8406ee7c98. Compact provenance/counters are committed in C01-final-summary.json.
- Final `run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2 --jobs 2` completed: 8 Smart exact, 8 matches_saved. Replay report SHA-256: 9cd4faaa877d3e18510df2d00f4dbdde77afba11b82329ebd8a829514a515035.
- `verify_olmsmoother2_C01.py` compares the named git base, current -O2 production, and -O2 ASan/UBSan against independently rendered original AEX Smart for seeds 1/2 plus eight saved inputs. Zero base-exact changes and zero sanitizer diagnostics in each of the three 608-case validations. Leak detection is disabled; no leak-check claim.

Before/after rebaseline:

| Commit/cause | Seed 1 exact/mismatch | Seed 2 exact/mismatch | Corpus exact/mismatch | Corpus changes |
|---|---|---|---|---|
| Baseline | 292/8 | 294/6 | 0/8 | — |
| 90ee9d99: classifier prerequisite | 292/8 | 294/6 | 0/8 | case 20: 13 bytes / 6 words → 2 bytes / 2 words; still mismatch |
| 65834249: scalar arithmetic | 298/2 | 296/4 | 6/2 | cases 17,20,223,245,262,299 become exact |
| This commit: scanner termination | 300/0 | 299/1 | 8/0 | cases 67,134 become exact |

Each step preserves all prior exact cases and decreases both byte and word mismatch counts for every changed unresolved case. No tolerance or expected-value patch is used. The classifier is a prerequisite commit, not falsely declared a closed case. C3's remaining NaN signs close with C4's general arithmetic cause; C1/C2 share the same scanner defect and close together.

Paired stage evidence:
- `trace_olmsmoother2_smart_C01.py` instruments a scratch production translation unit. It captures the source/class planes, center, polygon, c0d0 premultiply, ab00 accumulation, and b120 postprocess as bytes. Original AEX classifier/cce0 execute the retained ABI and config offsets. Its full typed frame is independently required to equal exported AEX Smart output, establishing the join rather than treating a constructed core as the public oracle.
- C01-stages-before.json captures the four retained representatives. C01-classifier-stages-after.json, C01-arithmetic-stages-after.json, and C01-finite-stages-before/after.json retain the boundaries and final exact joins. No source-plane injection is claimed to be a native AE frame capture.

1. **Classifier / C3.** Retained case 20 first differs at (0,1), alpha, AEX -inf versus Mac zero. The first divergent stage is class plane, followed by polygon (AEX empty, Mac three samples). AEX 0x18000b34e..0x18000b36a selects dr for unordered dg, then keeps it for unordered db; MAXSS at 0x18000b3e5 selects dy on unordered. Replacing the balanced std::max tree with this ordered sequence makes the paired class/polygon boundary exact. Generated case 20 falls from 951 differing bytes / 328 words to 27 / 27, all remaining differences being NaN signs. Corpus case 20 falls 13/6 → 2/2 before the arithmetic fix.

2. **Invalid arithmetic / C4 and remaining C3.** Retained case 299 at (2,2) has identical center and polygon; first divergence is c0d0 sample green: 0 × -inf gives AEX ffc00000 versus Mac 7fc00000. ab00's +inf + -inf also generates negative indefinite. Operation-level helpers implement invalid MULSS/ADDSS/DIVSS results and explicit NaN operand order. ab00 uses weighted sample as destination, accumulator as source. No writer correction is applied. Afterward all captured stages and public outputs for these representatives are exact.

3. **Scanner / C1+C2.** Retained case 67 at (6,1) and case 134 at (25,1) have exact class planes and centers; the first difference is polygon weight. AEX scan_cee0 returns row zero after decrementing from row one. Mac incorrectly re-probed row-zero A and incremented back to row one. AEX 0x18000cf84 branches to INC only for an A==0 stop; reaching zero via 0x18000cf91 exits directly. Restoring the exit reason changes case 67's second weight 0.0625 → 0.125 and case 134's weight 0.125 → 0.25. Final class/polygon/c0d0/ab00/b120 and public outputs all match. The independent scanner matrix covers 128 seeded class planes plus eight stop configurations, 12 coordinates each: **1632 cases, 37 mismatches → 0**, ASan/UBSan clean. First old scanner mismatch: input (3,1), AEX (3,0,0), Mac (3,1,0). C01-scanner-boundary.json retains the cases.

Explicit open boundary:
- `test_olmsmoother2_sse_C01.py` executes individual MULSS/ADDSS/DIVSS instructions at original AEX addresses for 400 operand pairs / 1200 operations. All **1092 operations with at most one NaN** agree. Fourteen two-NaN pairs / 42 operations disagree in payload selection; C01-sse-instructions.json retains every mismatch. The test explicitly asserts only the supported single/no-NaN boundary and reports the two-NaN residual. No all-NaN conformance claim or tolerance is made.
- A hypothesis that destination-NaN priority completely described this Unicorn boundary was refuted by those new payload values. Native arithmetic alone also failed a public payload case. Explicit ordering restores the measured public cases, but the separate two-NaN discrepancy is not silently promoted as exact or attributed to native Windows without evidence.
- Fresh seed 2 case 273 remains PF32/nonfinite, 19×15: 4 bytes / 1 word differ. First word 332 (pixel (7,4), A), AEX bytes ae47413f versus Mac 00000000. C01-seed2-residual.json records controls, input hash, and both output hashes. Its first divergent internal stage is unverified.

inference:
- The four retained signature clusters resolve to three general control/arithmetic causes; signature count was not a proof of distinct root causes.
- The remaining seed-2 case needs another paired-stage ticket. Two-NaN payload priority also needs independent native Windows/x86 evidence before choosing between port and oracle behavior. Neither boundary is covered by this ticket's exact seed-1 result.

changed_files:
- mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp
- tools/emulation/trace_olmsmoother2_smart_C01.py
- tools/emulation/test_olmsmoother2_sse_C01.py
- tools/emulation/test_olmsmoother2_scan_C01.py
- tools/fuzz/verify_olmsmoother2_C01.py
- tests/fuzz_corpus/olmsmoother2/seed1_case*.json (all eight existing rows, inputs unchanged)
- orchestra/reports/C01-*.json (three comparison reports, stage evidence, scanner/instruction evidence, summary, fresh residual)
- orchestra/reports/C01-smoother2-smart.md

verify:
Run from this worktree; every command below writes scratch beneath this ticket. No emulator rebuild is required.
```sh
mkdir -p orchestra/state/C01-smoother2-smart
python3 tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch orchestra/state/C01-smoother2-smart --report orchestra/state/C01-smoother2-smart/before.json --corpus orchestra/state/C01-smoother2-smart/verify-corpus > orchestra/state/C01-smoother2-smart/verify-census.log 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2 --jobs 2 --scratch orchestra/state/C01-smoother2-smart --report orchestra/state/C01-smoother2-smart/verify-replay.json > orchestra/state/C01-smoother2-smart/verify-replay.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_olmsmoother2_C01.py --base f87b3f1d6b2226a9744559974c86181eb4d7aa8e --label full-verify > orchestra/state/C01-smoother2-smart/verify-full.log 2>&1
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_olmsmoother2_smart_C01.py --indices 299 20 67 134 --label final-stages --reference-trace orchestra/reports/C01-stages-before.json > orchestra/state/C01-smoother2-smart/verify-stages.log 2>&1
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/test_olmsmoother2_scan_C01.py > orchestra/state/C01-smoother2-smart/verify-scanner.log 2>&1
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/test_olmsmoother2_sse_C01.py > orchestra/state/C01-smoother2-smart/verify-sse.log 2>&1
git diff --check
```
Expected: census 300 Smart exact, replay 8/8 exact and matches_saved; full comparison seed1 292→300, seed2 294→299, corpus 0→8 exact, no base-exact changes or sanitizer errors. All four stage joins/public outputs exact; scanner 1632/1632 exact; SSE single/no-NaN mismatches 0 with 14 explicitly open two-NaN pairs. Worker wall-time variability must be inspected as an oracle status, not miscounted as a numerical mismatch.

next:
- Follow-up SM2-SEED2-273: trace the retained procedural seed-2/index-273 alpha residual; do not assume a writer issue.
- Follow-up SM2-TWO-NAN: compare original instruction payload selection against native Windows/x86 and assess the Unicorn boundary.
- Review/merge the three commits. No push, MAIN modification, release-gate/ledger edit, or other-plugin edit was performed. Regenerable build directories are removed after verification; committed tests regenerate all required evidence.
