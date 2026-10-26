status: done
summary:
- Fixed the shared zero-component-divisor / wrapping-sign prepass cause of all three nightly Smart PF32 witnesses; all three are byte-exact.
- Narrowed P06a's original-bug classification to actual ungenerated-weight reads, preserving the previous safe fallback there.
- Added three labelled both-route witnesses; four existing Smart mismatches become exact with unchanged original outputs.
- Final-source campaigns have zero Smart mismatches/Mac-only refusals; all 306 corpus replays match; reference/fast is 675/675 exact.

facts:
- Branch `orch/N02-olmdirectionalblur-nightly-20261025`. No MAIN, AEX worker/source, release gate, ledger, other-plugin production code, or git history was changed. No push/stash. Standard campaigns use `--jobs 1`; at most two task-owned emulator/build processes run concurrently.
- Original AEX SHA256: `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`. Original worker bindings remain F52c for realistic-v1/odd-even and F53 for realistic-v2; default uses retained F46. Full hashes and command vectors are retained in evidence and corpus provenance.
- Initial standard replay reproduced the Smart oracle/candidate hashes and first differing words for all three witnesses. Standard replay returned 1 because nightly saved only Smart while normal replay also records Classic; this was not a failure to reproduce Smart. Original nightly files remain unchanged.

| Witness | Sampler | Original first word | Old Mac first word | Different words before / after |
|---|---|---|---|---|
| fdd4da1dfc62f6a1e40cd84a | realistic-v1 | 1f50eabf | 56fb63c0 | 2 / 0 |
| 33736bb7ba8bbc31e737404a | realistic-v2 | 9dd8cfbe | acf426bf | 4 / 0 |
| 7f02accac670dc615c92f894 | odd-even-v1 + realistic-v1 | 9c5841bf | c043c0bf | 3 / 0 |

- `trace.py` uses the existing C02 fixture/paired-stage instrumentation with typed PF32 input, sampled scale and a Back Alpha Fade read watch. For each witness, its original output equals the retained worker output. All nine captured paired stages match after the fix: populated, rotated, component map, divisor, generated weights, row output, denominator, alpha maximum and writer plane. Source alpha is negative, component divisor is zero; each original reads only float index 1 at instruction `0x18000134f`. Generated Back Alpha Fade counts are respectively 9, 3 and 20. Thus these concrete cases do not read ungenerated weights and must not be excluded as undefined originals.
- Static cause: `P06a-evidence/disassembly.txt` shows `0x1800061f6` storing zero component maximum; `0x1800010a8 CVTTSS2SI` maps the resulting NaN count to INT32_MIN; `0x180001234 CMP / 0x180001237 CMOVS` tests the wrapping subtraction sign. The port previously floored the divisor to one and used an overflowing signed subtraction. The correction uses the original zero only where all `[1,x)` backward weights are initialized, and implements the sign test through uint32 subtraction. No output-byte adjustment or added weights.
- `edge.py --sanitize`: the inherited P06a 12-case grid completes without sanitizer abort/error (9 exact, 3 mismatch). The 3 remaining mismatches are 3x1/fade2 and 7x5/fade2 or fade3, in the out-of-generated-weight domain. No undefined read is reproduced in the port. These are explicit original-bug-domain checks, not claimed exact output.
- Standard corpus replay: 306/306 saved results true, both Classic and Smart recorded. Four intentional Smart mismatch→exact updates (P05a original case, P06a original-cropped/reduced/negative-alpha control) are recorded before/after in `corpus-transitions.json`; original oracle records are identical. All other corpus expectations remain unchanged. Classic is still a nonconformant route; replay true does not mean Classic exact.
- Default seed1/n300: 298 Smart exact, 2 original time budgets. Compared with `P05a-evidence/default-1.json`, all 600 candidate route hash/error pairs are unchanged and there are zero exact→non-exact transitions.


Final-source standard campaigns (all jobs 1, no shrinking; odd-even uses max width 1920 / height 1080):

| Sampler | Seeds | Cases | Smart exact | Smart mismatch | Mac-only refusal | Original unavailable |
|---|---|---:|---:|---:|---:|---:|
| realistic-v1 | 2026102601/02/03 | 600 | 600 | 0 | 0 | 0 |
| realistic-v2 | 2026102601/02/03 | 600 | 600 | 0 | 0 | 0 |
| odd-even-v1 + realistic-v1 | 2026102601 | 200 | 196 | 0 | 0 | 4 |
| odd-even-v1 + realistic-v1 | 2026102602 | 200 | 197 | 0 | 0 | 3 |
| odd-even-v1 + realistic-v1 | 2026102603 | 200 | 198 | 0 | 0 | 2 |
| default | 1 | 300 | 298 | 0 | 0 | 2 |

The nine new-seed campaigns have 1791 Smart exact / 1800 observations, with nine
unavailable originals. Seeds were selected before the implementation and not
replaced. Five campaigns started on the baseline were rerun on final sources;
`refresh-campaigns` verifies dependency hashes before reusing an already-final
run. Both route records remain in the compressed evidence. Noncontract Classic
mismatches/refusals are not presented as Smart failures or exact results.

- `tools/perf/ref_vs_fast.py --plugin olmdirectionalblur --scratch .../perf`: 675 exact comparisons, 0 mismatch, 0 refusal (200 small + 20 1080p + 5 4K cases, thread caps 1/2/8). Separate reference-build replay of all three nightly witnesses also matches their both-route records.

- Cleanup: regenerable build/trace/perf directories removed; retained scratch logs/reports total 12,532,838 bytes (below 5 GiB). All task-owned workers finished. `git diff --check` passes.

inference:
- The earlier blanket P06a classification combined a deterministic arithmetic mismatch with a separate backing-storage bug. Generated table count is the relevant boundary. Keeping the previous fallback only when an actual prepass visit can exceed generated storage preserves safety without treating initialized cases as undefined.
- The R10 reference/fast split is intact; both implementations use the same corrected prepass contract. This establishes local CPU-AEX comparisons, not a new native AE or arbitrary-input conformance claim.

changed_files:
- `core/dblur_frontonly.cpp`, `core/dblur_rowdriver.cpp`
- `notes/KNOWN_ORIGINAL_BUGS.md` (N02 boundary correction)
- `tests/fuzz_corpus/olmdirectionalblur/N02-nightly-20261025/` (3 new cases)
- `tests/fuzz_corpus/olmdirectionalblur/P05a-performance/preexisting-realistic-v1-seed2053-case9.json`
- `tests/fuzz_corpus/olmdirectionalblur/P06a-investigation/{alpha--1.0,original-cropped,reduced}.json`
- `orchestra/reports/N02-evidence/`, this report

verify:
```sh
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/N02-olmdirectionalblur-nightly-20261025"
mkdir -p "$TMPDIR"
python3 orchestra/reports/N02-evidence/verify-directionalblur.py witnesses
python3 orchestra/reports/N02-evidence/verify-directionalblur.py reference-witnesses
python3 orchestra/reports/N02-evidence/verify-directionalblur.py campaigns
python3 orchestra/reports/N02-evidence/verify-directionalblur.py corpora
python3 orchestra/reports/N02-evidence/edge.py --sanitize
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" orchestra/reports/N02-evidence/trace.py
python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur --scratch "$TMPDIR/perf"
python3 orchestra/reports/N02-evidence/summarize.py
git diff --check
```
Expected: three Smart exact witnesses in fast and reference builds; 306 corpus matches; 0 Smart campaign mismatches/Mac-only refusals; no default exact→non-exact; sanitizer grid as above; paired stages equal; clean reference/fast comparison. Original execution availability can vary with machine load; raw unavailable outcomes are retained. `witnesses` deliberately replays the unchanged pre-fix nightly records (inner CLI exit1), asserts unchanged oracle and new exact output, and writes the labelled both-route set. Other verification modes do not update corpus expectations.

next:
- Orchestrator review/merge. Preserve the narrowed original-bug domain and noncontract Classic outcomes; no unrelated performance or release-gate change is requested.
