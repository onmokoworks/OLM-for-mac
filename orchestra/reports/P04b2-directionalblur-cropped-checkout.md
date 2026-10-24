status: done
summary:
- Removed DirectionalBlur SmartRender's full-layer admission requirement; its existing input-sized workspace and span/budget checks remain in use.
- Four F53 cropped witnesses changed from Mac-only refusal to byte-and-rectangle exact; added a labelled, both-route corpus.
- Required campaigns: 995 Smart exact / 1,000 cases, zero Smart mismatches and zero Mac-only refusals; five original execution failures remain uncompared, not counted as exact.
- All 291 retained/new DirectionalBlur corpus cases replay true on both routes, including P02j and T15b.
- Unit baseline unchanged: 39 files, 7 pass / 32 fail before and after. No release or global AE-exact promotion.

facts:
- Branch `orch/P04b2-directionalblur-cropped-checkout`. `memory_pressure`: 55% free before builds, 59% during verification. All loops use one job; at most two task-owned build/emulator processes ran concurrently.
- Original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`; F53 worker SHA256 `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`. Used cached worker, never rebuilt it.
- `python3 orchestra/reports/P04b2-evidence/witness.py --plugin olmdirectionalblur --label before`: four original successes, four Mac error 516 refusals at `SmartRender:smart-generic-world-or-budget@2710`.
- The same command with `--label after`, after the source change: four Smart exact results. Layer 40x30, input/output 20x15, Front Strength 5; explicit/automatic checkouts at zero and nonzero `[3,4,23,19]` origins. Input-sized plane construction is also visible in the original worker `0x180004a20` excerpts retained under P02j.
- Original and candidate output SHA256s for witness indices 0..3: `0a21ff72492dcdd55e430eb9607534bfa730a2b4340415c461fa1e6104129597`, `315410c9c75f2875ccfab6fd84b1df284319e1b83de2132e6c31099b3124e734`, `0a21ff72492dcdd55e430eb9607534bfa730a2b4340415c461fa1e6104129597`, `f5d0ef7ed0aade04a6f89268c7e76521185b27749839e58a5e2a58ac668af77c`. No Smart first mismatch exists in these comparisons.
- `--label corpus --corpus` records the same four inputs with both routes. Smart is exact; Classic has four mismatches, retained honestly as noncontract route behavior. Standard replay reproduces those outcomes.
- `python3 orchestra/reports/P04b2-evidence/acceptance.py`: seven standard `tools/fuzz/run.py` campaigns, jobs 1, shrinking disabled, max-size 256 except T15b flags (1920 width / 1080 height). Actual command vectors and source/oracle bindings are committed. Default uses standard retained F46; realistic-v1/odd-even use F52c; realistic-v2 uses F53.

| Sampler | Seed | n | Smart exact | Smart mismatch | Mac-only refusal | Original unavailable |
|---|---:|---:|---:|---:|---:|---:|
| default | 1 | 300 | 298 | 0 | 0 | 2 |
| realistic-v1 | 1 | 100 | 100 | 0 | 0 | 0 |
| realistic-v1 | 2049 | 100 | 100 | 0 | 0 | 0 |
| realistic-v2 | 1 | 100 | 100 | 0 | 0 | 0 |
| realistic-v2 | 2049 | 100 | 100 | 0 | 0 | 0 |
| odd-even-v1 + realistic-v1 | 2026 | 150 | 150 | 0 | 0 | 0 |
| odd-even-v1 + realistic-v1 | 2027 | 150 | 147 | 0 | 0 | 3 |

- Every one of F53's 26 seed-1 DirectionalBlur Mac-only refusals is now Smart exact (indices retained in `P04b2-evidence/summary.json`). There is no measured Smart exact-to-non-exact regression; all retained corpus results reproduce unchanged.
- The five initial original outcomes are 10-second wall budgets: default seed 1 indices 274/289, odd-even seed 2027 indices 5/50/54. Extended 60-second attempts are separately retained in `*-retry.json`; they do not overwrite the campaign measurements. All five extended attempts ended in original guest execution stops (`status: reject` in the transport), rather than a returned plugin PF_Err. These cases are not evidence of original plugin refusal, nor of byte agreement.
- `python3 orchestra/reports/P04b2-evidence/acceptance.py --replay-only`: standard replay true for 83 root cases, 200 P02j realistic cases, four T15b cases (matching size sampler and maximum), four new P04b2 cases: 291 total, both routes. No existing corpus expectation was rewritten.
- `OLM_TEST_JOBS=1 python3 orchestra/reports/P04b2-evidence/unit_tests.py --label before` and `--label after`: each 39 files, 7 pass / 32 fail; zero per-file exit changes. These historical failures include stale source-hash assertions and unavailable test dependencies; full per-file diagnostic tails are retained rather than treating them as passing tests.
- Scratch ended at approximately 2.8 MiB; no disposable build tree/executable or task-owned background process remains. No MAIN, emulator source, release gate, ledger, or other plugin source was modified. `git diff --check` passed.
- F53 already implemented the requested opt-in sampler as realistic-v2. Its unchanged all-plugin seed-1 n100 survey (`orchestra/reports/F53-evidence/survey-auto-*.jsonl`) establishes the other-plugin outcomes: ColorKeep has 3 Mac-only alignment refusals; Smoother2 has 39 mismatches (first index 0, original rect `[5,4,6,5]`, Mac `[0,0,11,7]`, 4 vs 308 bytes, first byte expected `af`, actual `00`). OLMBlur, ColorKey and ToonDilate each have 100 exact; DistanceGradation 97 exact / 1 refusal / 2 uncompared; KiraKira 99 exact / 1 refusal; RadialBlur 87 exact / 13 uncompared; Smoother Classic 65 exact / 35 unsupported PF32 refusals. The latter refusals coincide with unavailable/unsupported originals and are not asserted Mac-only. This survey is inherited evidence, not a newly rerun all-plugin campaign; no other plugin changed.

inference:
- The remaining layer-size predicate duplicated an assumption absent from the original. The existing P02j input-sized workspace, request forwarding, local-coordinate sampling and output publication already implement the cropped case; no new allocation or coordinate transform was required.
- Removing only that predicate is supported by the original zero/nonzero-origin witnesses and 200 realistic-v2 cases, including all 26 prior refusal cases. Parameter, world-span, format, lifecycle and work-budget checks remain active.
- Completion here means the requested change and specified measurements are delivered: all comparable Smart outputs are exact and all corpus replays are true. It does not mean the five unavailable originals were compared, that the failing historical unit suite is green, or that Classic has become conformant.

changed_files:
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `tests/fuzz_corpus/olmdirectionalblur/P04b2-cropped-checkout/witness-{0,1,2,3}.json`
- `orchestra/reports/P04b2-evidence/` (witness/unit/campaign/replay/retry scripts, measured results, provenance and summary)
- `orchestra/reports/P04b2-directionalblur-cropped-checkout.md`

verify:
```sh
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 orchestra/reports/P04b2-evidence/witness.py --plugin olmdirectionalblur --label verify
python3 orchestra/reports/P04b2-evidence/unit_tests.py --label verify
python3 orchestra/reports/P04b2-evidence/acceptance.py
python3 orchestra/reports/P04b2-evidence/acceptance.py --replay-only
python3 orchestra/reports/P04b2-evidence/retry_budgets.py default-1 odd-even-2027
python3 orchestra/reports/P04b2-evidence/summarize.py
git diff --check
```
Expected: four Smart exact witnesses; unit baseline 7/39 file passes; campaign table above (wall-time budget counts may vary); all 291 replay matches true. `acceptance.py` logs the exact standard CLI commands, uses correct T15b flags, and stores stdout under ticket scratch. `retry_budgets.py` only retries original budgets, with a 60-second limit and preserved input hashes. The reported 995 exact count excludes all unavailable original outputs.

next:
- Separate oracle follow-up for default seed 1 indices 274/289 and odd-even seed 2027 indices 5/50/54: diagnose original execution stops; do not tune DirectionalBlur pixels against missing output.
- Other-plugin ColorKeep alignment and Smoother2 checkout negotiation remain separate tickets, as identified by F53.
- Historical unit fixture/dependency maintenance and noncontract Classic compatibility remain outside this ticket.
