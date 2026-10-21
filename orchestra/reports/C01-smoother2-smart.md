status: partial
summary:
- Smart seed-1 n300 improved from 292 exact / 8 mismatch to 298 exact / 2 mismatch / 0 refusal.
- Classifier ordering is committed separately as a prerequisite; this commit closes the remaining C3/C4 nonfinite propagation/sign residuals.
- Seed 2 improved 294/300 → 296/300; saved corpus improved 0/8 → 6/8 exact.
- All base-exact outputs preserved; 608 ASan/UBSan replays match optimized output without diagnostics.
- PF8/PF16 polygon-weight residuals and the independent two-NaN payload boundary remain open.

facts:
- Base: f87b3f1d6b2226a9744559974c86181eb4d7aa8e. Commands below ran successfully; exact evidence is in C01-classifier-verify.json and C01-stages-before.json.
- Original AEX SHA-256: 7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7. Retained worker path/hash recorded in verification provenance. No worker rebuild.
- Paired original-AEX classifier and cce0 replay uses captured source plane, retained descriptor/config ABI, and joins its complete typed output byte-for-byte to the independent exported Smart AEX oracle.
- Retained case 20: first public mismatch at (0,1), alpha; first divergent stage is class plane, then polygon (AEX empty, Mac three samples). Correct comparison ordering makes both stages exact at that pixel. Other pixels retain NaN-sign differences.
- AEX instructions 0x18000b34e..0x18000b36a select dr over unordered dg, then retain that value for unordered db; MAXSS at 0x18000b3e5 selects dy on unordered. The prior balanced std::max tree did not implement that sequence.

| Scope | Before exact/mismatch | After exact/mismatch | Changed cases | Changed case bytes/words before → after |
|---|---|---|---|---|
| Seed 1, 300 | 292/8 | 292/8 | 1 | case 20: 951/328 → 27/27 |
| Seed 2, 300 | 294/6 | 294/6 | 0 | unchanged |
| Saved corpus, 8 | 0/8 | 0/8 | 1 | case 20: 13/6 → 2/2 |

- Sanitized current output equals optimized current output for all 608 cases. ASan+UBSan uses -O2, -fno-sanitize-recover=all, leak detection disabled. No native AE or native Windows/UCRT claim.
- The corpus rebaseline changes only case 20; byte and word mismatch counts strictly decrease. It remains explicitly mismatch, not exact.

inference:
- The classifier defect is a general unordered-comparison ordering error, not an alpha clamp or writer defect.
- The remaining case-20 NaN signs overlap the larger nonfinite arithmetic cluster; the classifier correction is committed as a prerequisite, not falsely reported as a fully closed case.

changed_files:
- mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp
- tools/emulation/trace_olmsmoother2_smart_C01.py
- tools/fuzz/verify_olmsmoother2_C01.py
- tests/fuzz_corpus/olmsmoother2/seed1_case000020_*.json
- orchestra/reports/C01-classifier-verify.json
- orchestra/reports/C01-stages-before.json
- orchestra/reports/C01-classifier-stages-after.json
- orchestra/reports/C01-smoother2-smart.md

verify:
```sh
mkdir -p orchestra/state/C01-smoother2-smart
python3 tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch orchestra/state/C01-smoother2-smart --report orchestra/state/C01-smoother2-smart/before.json --corpus orchestra/state/C01-smoother2-smart/verify-corpus > orchestra/state/C01-smoother2-smart/verify-census.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_olmsmoother2_C01.py --base f87b3f1d6b2226a9744559974c86181eb4d7aa8e --label classifier-verify > orchestra/state/C01-smoother2-smart/verify-classifier.log 2>&1
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_olmsmoother2_smart_C01.py --indices 20 --label classifier-check --reference-trace orchestra/reports/C01-stages-before.json > orchestra/state/C01-smoother2-smart/verify-stages.log 2>&1
git diff --check
```
Expected at this commit: counts/table above, zero base-exact changes and sanitizer errors, case-20 class/polygon exact at retained (0,1), full core/public AEX join exact.

next:
Close NaN arithmetic with operation-level evidence, then investigate PF8/PF16 polygon weights. A 400-pair original-instruction experiment also exposed a separate two-NaN payload-selection boundary; do not infer native Windows payload precedence from Unicorn alone.

Arithmetic closure (second commit):
- Base 90ee9d99, evidence C01-arithmetic-verify.json. Optimized and sanitized seed1: 292/8 → 298/2; seed2: 294/6 → 296/4; retained corpus: 0/8 → 6/2. All six changed corpus rows now exact. Zero changes to base-exact cases.
- C01-arithmetic-stages-after.json: retained case 299 has identical class plane, polygon, center, c0d0, ab00, and b120 bytes, with full reconstructed-core/public-AEX join. Case 20 also joins and is now public exact.
- First case-299 boundary: c0d0 sample green 0 × -inf produces AEX ffc00000 versus previous Mac 7fc00000. In ab00, +inf + -inf similarly creates negative indefinite. Correct the operation itself; no writer/output-byte correction.
- Helpers preserve MULSS/ADDSS/DIVSS operand order and noncontracted arithmetic. The original ab00 adds weighted sample as destination and accumulator as source.
- `test_olmsmoother2_sse_C01.py`: 400 operand pairs / 1200 original instructions. All 1092 operations with at most one NaN match. Fourteen two-NaN pairs (42 operations) disagree in payload priority; full values retained in C01-sse-instructions.json. These are explicitly open, not hidden by a tolerance or asserted exact. The public generated/corpus matrices above do not hit this remaining differing-payload boundary. Do not infer native Windows/UCRT payload precedence from this Unicorn-only result.
- Arithmetic verification: `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_olmsmoother2_C01.py --base 90ee9d99 --label arithmetic-verify` (redirect output to ticket scratch); expected counters above, no base-exact changes, zero sanitizer errors.
- Instruction verification: `PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/test_olmsmoother2_sse_C01.py` (redirect to ticket scratch); expected 0 single-or-no-NaN mismatches and 14 open two-NaN pairs.
- Additional changed files: tools/emulation/test_olmsmoother2_sse_C01.py; six corpus rows; C01-arithmetic-verify.json; C01-arithmetic-stages-after.json; C01-sse-instructions.json.
