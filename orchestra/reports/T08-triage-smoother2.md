status: done

summary:
- Added behavior-neutral `OLM_REFUSAL_TRACE` tags and per-route adapter attribution; the 8-case replay is 8/8 `matches_saved`, and the 300-case census counters are unchanged.
- All 300 baseline Classic refusals attribute to `Render:classic-entry-unowned@5238`; there are zero Smart refusals, zero unattributed refusals, and at most one guard per case.
- The original AEX Classic route returns success on 300/300 but writes no pixels: every output slot is all-zero. This matches the source comment that the exported classic command is a no-op; the zeros are the worker's initialized output buffer, not a numerical owner.
- A scratch-only gate-off of the Classic guard unblocks 300/300 and produces the same bytes as Mac Smart on 300/300: 292 exact / 8 mismatch against AEX Smart (the baseline distribution), and 0 exact / 300 mismatch against the empty AEX Classic slot. ASan+UBSan results are identical with zero sanitizer errors or crashes.
- The gate-off does not fix the 8 Smart mismatches. The four retained clusters (eight cases) remain unexplained; the PF32 nonfinite clusters show a NaN/`-inf` propagation pattern, while PF8/PF16 are one finite pixel each.
- No production guard was removed and no numerical behavior changed.

facts:

Scope and provenance:
- Branch `orch/T08-triage-smoother2`; starting HEAD `dda5660ca7ea9100be21ad0a33223a67d838a6a2`. Baseline report `reports/fuzz/olmsmoother2_20261021.json`, SHA-256 `6c03a88446fc0b99e1fd48107c8b7346a381ce5bb9b654944ca39dd453dca220`: AEX 300 ok, Classic 300 refusal, Smart 292 exact / 8 mismatch, four clusters.
- Original AEX SHA-256 `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`; original candidate SHA-256 `005d1e5fe0cc07733adf505a732101cbf2f7b35ad05c10bd29d639e09dd30b62`; original source SHA-256 `0a7e7ef2c14943716210fe19bb3dd2e09e60a88960b1223dc17f60d22268271b`.
- Retained worker `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. No emulator rebuild or worker substitution.
- Final instrumented source SHA-256 `f5ca3ba3b01114162b218acf46158bfa91d64d5236b5842283e59b4efc3820b1`; rebuilt candidate SHA-256 `037be912903230db7343cf1138bf3372b1dce2218cc1970cbb4e7c8ee7c9799e`. Scratch gate-off source SHA-256 `6bb0ce93c1af3dfeef2c063e9c536000ad04567669910df20ea1e27809c8bd33`; gate-off binary `4cb785601892e6f767b78b8a81900c1ae6ec6d4f3dab54a40ed149af4c7cf65e`; sanitized binary `fa0bde55571d6b489dd7f2134befe14d8c1aeb418f346b270ced4dff1b9d3741`. ASan builds can embed build-local identity; compare behavior, not this binary hash.
- Triage script SHA-256 `227209086ba97c08717deb0bce9a42705cce0108bca7c0c164a30d9ee5948f8a`. Evidence JSONs: `reports/fuzz/olmsmoother2_T08_triage.json` SHA-256 `c4f929340077127d8277eaf2494e2e794b2cdc633dc7f3e9c66d814f94c0e6a2`; `reports/fuzz/olmsmoother2_T08_neutrality.json` SHA-256 `b3f607cd0667e905f6ed62436268cf9d4c117c49f683468b3c0d0afb07e5d8af`.
- This is Unicorn CPU AEX versus public `EffectMain` in the retained SDK shim. Host imports and emulator-route observations do not establish native Windows UCRT or native AE equivalence.
- The ledger freezes the closed 8bpc and declared 32bpc case-07 arithmetic, forbids `-O0` conformance builds, forbids more 8bpc traces without a new inconsistency, forbids premultiplied-PNG source truth, forbids generalizing case-07 to untested 32bpc, and forbids claiming AE exact from CLI output. This work adds no numerical patch and observes all of those boundaries.

Neutrality and refusal census:
- `python3 tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2 --jobs 2 --budget-minutes 10 --scratch orchestra/state/T08-triage-smoother2 --report orchestra/state/T08-triage-smoother2/replay.json` exited 0: 8 completed, 8 `matches_saved`.
- `python3 tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --budget-minutes 10 --scratch orchestra/state/T08-triage-smoother2 --report orchestra/state/T08-triage-smoother2/census.json --corpus orchestra/state/T08-triage-smoother2/census-corpus` exited 0: AEX 300 ok; Classic 300 refusal; Smart 292 exact / 8 mismatch. These equal the baseline route counters.
- The census covers PF8 91, PF16 114, PF32 95; profiles are SDR 260, HDR 18, signed 16, nonfinite 6. Classic guard tags are `Render:classic-entry-unowned@5238` on all 300 refusals; unattributed Classic refusals 0; Smart guard tags 0; maximum guards per case 1. The unshrunk census has eight signatures, while the original reduced baseline has four clusters; the four original clusters are used below.
- The refusal helper only opens `OLM_REFUSAL_TRACE` on an error path and returns the same error code as before. The adapter copies the environment per call, reads and unlinks the route-local trace outside the compared result, and does not mutate shared adapter state. The only added early return (`prerender-checkout`) returns the same `err` before two `if (!err)` blocks. Replay and census results are identical with and without the attribution.

Ranked guards (baseline legal control cases):

| Rank | Guard | Classic | Smart | AEX ok among refused | Trigger / boundary |
|---|---|---:|---:|---:|---|
| 1 | `Render:classic-entry-unowned` (line 5238) | 300 | 0 | 300 | Classic entry passes world validation, then fails closed; the AEX Classic selector returns success with no pixel writes |
| — | All other tagged guards | 0 | 0 | — | Not observed; this does not prove unreachability |

- The Mac refusal code is `PF_Err_BAD_CALLBACK_PARAM` (25). The AEX Classic selector returns `render_error=0`; this is a policy refusal, not an AEX error.

Classic owner audit:
- The worker's `--fixture-render-path classic` path reaches `render_resident_pixels_mode(..., smart=false)` and invokes the exported `RENDER` selector. On 300/300 baseline cases the status is ok with intact guards and a clean session.
- The Classic output slot is all-zero on 300/300 cases; it equals the input on 0/300 and equals AEX Smart on 0/300. Three repeat calls on the C3 and C4 representatives produced identical hashes.
- The all-zero slot is consistent with a no-op command that does not write, not with a numeric classic renderer. The source comment's "classic command is a no-op" claim is therefore supported for this corpus. This is still an emulator-route observation; it is not proof of native AE classic buffer semantics.
- Consequence: replacing the guard with `RenderBits` publishes the Smart core on an entry with no observed Classic numerical owner. That is not a conformance improvement.

Gate-off experiment:
- `python3 tools/fuzz/triage_olmsmoother2.py --jobs 2 --report orchestra/state/T08-triage-smoother2/triage.json` exited 0. It regenerated all 300 seed/index inputs and asserted each baseline input hash before execution.
- The script generates a scratch translation unit with `#if OLM_SM2_TRIAGE_CLASSIC_OFF` in `Render` only. No switch is in production source. The same headers, typed core, validation, and public routes are used. Sanitizers use `-fsanitize=address,undefined -fno-sanitize-recover=all`, `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`, and `ASAN_OPTIONS=detect_leaks=0`; leak checking is not claimed.

| Classic configuration (300 inputs) | Unblocked | Exact vs AEX Smart | Mismatch vs AEX Smart | Exact vs AEX Classic | Mismatch vs AEX Classic | Refusal | Crash | Sanitizer error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Production | 0 | 0 | 0 | 0 | 0 | 300 | 0 | not enabled |
| Guard off | 300 | 292 | 8 | 0 | 300 | 0 | 0 | not enabled |
| Guard off / ASan + UBSan | 300 | 292 | 8 | 0 | 300 | 0 | 0 | 0 |

- Guard-off output equals Mac Smart output on 300/300 cases. The 292/8 split against AEX Smart is exactly the baseline Smart split; the guard-off changes the route, not the numbers.
- The 0/300 exact result against AEX Classic is a comparator artifact: the AEX Classic slot is empty on every case, so computed pixels cannot match it. It is not evidence of a numerical regression or of a second classic algorithm.
- No gate-off case crashed, and no sanitizer error was reported. This checks only the guard-off experiment, not all code paths.
- The 8 remaining Smart mismatches are unchanged by the gate-off, so the Classic guard is not their cause.

Cluster classification:
- Representatives are the smallest saved greedy shrinks by pixel count, then active input bytes, then corpus path. These are bounded witnesses, not globally minimal inputs. All retained Mac hashes still match their saved hashes.
- Cluster rows use the retained reduced corpus input. Shrinking can change parameter values as well as pixels, so a representative can have a different mismatch magnitude than the original generated case at the same seed/index. The eight-case evidence list is the generated set, not the reduced representatives; `reports/fuzz/olmsmoother2_T08_triage.json` records both scopes.
- The worker session exposes final raw output only, and `first_stage()` returns no paired stages. There is no captured AEX internal stage for these inputs, so the first differing internal stage is unverified for all four clusters. Mac trace knobs exist, but without a paired AEX stage they cannot establish the first differing operation.
- Units are different bytes/typed words; max absolute byte difference/max absolute sample difference (PF16 in 0..32768 units, PF32 floats). Channels are ARGB memory channels. All four representatives first differ in A.

| ID | Nondefault slots; depth | Baseline cases | Smallest saved case; geometry | Diff bytes/words; max byte/sample | Spatial/channel pattern | Classification |
|---|---|---:|---|---|---|---|
| C1 | 6,9,10,11,12,13,14,15; PF8 | 1 (case 67) | case000067; 11×8 | 1/1; 11/11 | A; 1/88 pixels; first (6,1) A; AEX 32, Mac 21 | unexplained |
| C2 | 6; PF16 | 1 (case 134) | case000134; 48×18 | 7/4; 185/3250 | A/R/G/B; 1/864 pixels; first (25,1) A; AEX A 13268, Mac 10018 | unexplained |
| C3 | 7; PF32 | 1 (case 20) | case000020; 2×5 | 13/6; 255/0.0 | A-first; 2/10 pixels; first (0,1) A; AEX `0xff800000` (`-inf`), Mac `0x00000000`; 13 nonfinite pairs | unexplained (nonfinite) |
| C4 | defaults; PF32 | 5 (cases 17,223,245,262,299) | case000299; 3×3 | 1/1; 128/0.0 | A; 1/9 pixels; first (2,2) A; AEX `0xffc00000` (negative NaN), Mac `0x7fc00000` (positive NaN) | unexplained (NaN sign) |

- C4's five baseline cases share the same nondefault-slot signature. The smallest saved shrink is case 299 at 3×3; the other four retain their generated cases and were not separately reduced.
- C3 is not merely a NaN-sign difference: the AEX `-inf` and finite words become Mac zero and positive NaN at the two differing pixels.
- C1 and C2 are finite, one-pixel differences at PF8 and PF16. They are consistent with a rounding/tie or edge-sample difference, but the first stage is unverified.
- C4 is consistent with x86 SSE indefinite NaN versus ARM default NaN, and C3 with nonfinite clamping/propagation. Both are inferences from final bytes, not proven root causes.
- The common A-first pattern is an observation, not evidence of one shared alpha defect.

inference:
- Keep the Classic fail-closed guard. The AEX Classic command succeeds without writing, while the gate-off candidate writes Smart pixels; the guard prevents an unowned numerical result from being published. The correct follow-up is to document or emulate the no-write contract, not to route Classic through `RenderBits`.
- The gate-off does not change conformance because gate-off Classic and Mac Smart agree byte-for-byte on all 300 cases, and the remaining mismatch set is exactly the baseline Smart set. The 8 mismatches are therefore in the shared typed core on these inputs, not in the Classic wrapper or stride staging.
- The highest-yield numerical investigation is PF32 nonfinite handling (C3/C4, six of eight cases), followed by the separate finite PF8/PF16 witnesses. Do not apply a global tolerance, global rounding, or a case-07 generalization.
- No claim is made that the AEX Classic route is the native AE classic owner, or that the all-zero slot is the correct output for a caller. It is evidence that this emulator route supplies no numerical classic reference for this corpus.

changed_files:
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp` — optional refusal attribution only; error codes and output bytes unchanged.
- `tools/fuzz/adapters/olmsmoother2.py` — route-local trace collection only.
- `tools/fuzz/triage_olmsmoother2.py` — reproducible scratch gate-off, Classic audit, sanitizer run, and smallest-cluster statistics.
- `reports/fuzz/olmsmoother2_T08_triage.json` — compact experiment/representative evidence.
- `reports/fuzz/olmsmoother2_T08_neutrality.json` — replay/census counts and provenance.
- `orchestra/reports/T08-triage-smoother2.md` — this report.

verify:
```sh
mkdir -p orchestra/state/T08-triage-smoother2
python3 tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2 --jobs 2 --budget-minutes 10 --scratch orchestra/state/T08-triage-smoother2 --report orchestra/state/T08-triage-smoother2/verify-replay.json > orchestra/state/T08-triage-smoother2/verify-replay.log 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --budget-minutes 10 --scratch orchestra/state/T08-triage-smoother2 --report orchestra/state/T08-triage-smoother2/verify-census.json --corpus orchestra/state/T08-triage-smoother2/verify-census-corpus > orchestra/state/T08-triage-smoother2/verify-census.log 2>&1
python3 tools/fuzz/triage_olmsmoother2.py --jobs 2 --report orchestra/state/T08-triage-smoother2/verify-triage.json > orchestra/state/T08-triage-smoother2/verify-triage.log 2>&1
git diff --check
```
Expected: replay exit 0 with 8/8 `matches_saved`; census exit 0 with AEX 300, Classic 300 refusal, Smart 292/8, all 300 Classic tags `Render:classic-entry-unowned@5238`; triage exit 0 with 300 Classic production refusals, gate-off 292/8 vs AEX Smart and 300 mismatches vs the all-zero AEX Classic slot, 300/300 AEX Classic outputs all-zero, zero sanitizer errors, and four representatives. AEX wall-time counts can vary under shared-machine load; inspect each explicit oracle status before interpreting counts. Build hashes, especially sanitized ones, may change; compare behavior. All scratch remains under this ticket and is ignored by git. No `/tmp` writes, MAIN writes, push, history rewrite, or native AE interruption were performed.

next:
Proposed follow-up fix/investigation tickets (one evidence-backed scope each):
- **SM2-CLASSIC-NOOP:** keep the fail-closed Classic guard and add a regression that the Classic entry returns error 25 with tag `Render:classic-entry-unowned` while the AEX Classic selector is a no-write success. If a caller requires the route, define host no-write semantics explicitly; do not implement it by calling `RenderBits`.
- **SM2-STAGE-TRACE:** add a paired internal-stage capture or bounded differential probe for the eight Smart mismatch cases. Final raw bytes and the unpaired Mac trace cannot identify the first differing operation.
- **SM2-PF32-NONFINITE:** investigate C3/C4 (six of eight cases) with default-parameter and slot-7 witnesses, covering `-inf` clamping/conversion and NaN sign/payload propagation. Preserve the existing closure; do not add a blanket nonfinite tolerance.
- **SM2-PF8-ALPHA:** trace C1's single A byte at (6,1), AEX 32 versus Mac 21, at PF8. This is a new inconsistency, so a narrow trace is allowed; do not retune the frozen 8bpc arithmetic or LUTs.
- **SM2-PF16-PIXEL:** trace C2's single pixel at (25,1), where A/R/G/B all differ and the maximum sample delta is 3250 at PF16. Keep it separate from the PF8 and PF32 tickets.
- **SM2-COMPARATOR-CLASSIC:** make the fuzz comparator distinguish a no-write/empty Classic reference from a numerical mismatch. A future gate-off must not report "300 Classic mismatches" as a numerical failure when the reference route wrote nothing.
- **SM2-DESCRIPTOR-DISPATCH:** if the ledger's descriptor/dispatch lane is resumed, use the C1/C2 witnesses as narrow inputs against the current Windows lane; do not reopen closed 8bpc or case-07 arithmetic.
