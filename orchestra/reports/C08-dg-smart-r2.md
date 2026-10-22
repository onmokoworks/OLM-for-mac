status: done

summary:
- Closed three clusters in separate commits: blurred Smart staging/composition, unblurred PF8 normalization, and PF32 zero-size Box/Gaussian/Median admission.
- Seed1 Smart: 225/17/51/7 -> 246/3/44/7 (exact/mismatch/refusal/uncompared); every base-exact byte and every Classic result is preserved.
- Fresh seed3 exact: 217 -> 227 -> 230 -> 236; final 236/4/53/7 on its captured original-reference set.
- Independent matrices 432/432, 216/216 and 648/648 exact; campaign/matrix/corpus ASan+UBSan agree; existing 9+2 tests pass.
- Two retained corpus mismatches become exact; 145/145 final Smart corpus outputs are exact. Three-cluster stop condition reached.

facts:
- Starting HEAD `b4350d648947640ebdc3459c5e0451cbef54c64f`, branch `orch/C08-dg-smart-r2`. Read AGENT_GUIDE, GOTCHAS, DistanceGradation ledger restrictions, compatibility plan, T07/F01/F02/C03 and F10/F12 method. MAIN and emulator sources remain read-only; no worker rebuild.
- Original AEX SHA-256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; retained worker SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`, absolute path `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`. Cache INDEX inspected, no substitution. Typed original-AEX CPU Smart is the oracle; no native AE/UCRT claim.
- `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0` with ticket scratch corpus exits 0: Smart 225 exact / 17 mismatch / 51 refusal / 7 uncompared. AEX Smart 290 success / 8 reject / 2 budget. Classic 10 exact / 290 mismatch.
- Current-base all-gates-off ASan/UBSan experiment, `probe_distancegradation_smart_C03.py --experiment all --sanitized --smart-only` with seed 1, n300, jobs2, timeout30: 258 exact / 32 mismatch / 10 uncompared, no sanitizer diagnostic/candidate failure. Original AEX 290 success / 10 reject. Among previously refused: HDR 12 exact; signed 10 exact / 1 mismatch / 1 uncompared; nonfinite 1 exact / 7 mismatch; SDR 10 exact / 7 mismatch / 2 uncompared. This refutes broad admission; it is diagnostic only.
- Six natural PF8 public Smart captures (RGB/Layer × Inside/Outside/Both, Box size 1) preserve original builder state, source and staged field. Relocated callbacks reproduce every public output hash. Source normalization and distance scalar match Mac before the change. Inside field bytes are `2a2a2a0080808080d4d4d4ff`. AEX first unowned output is `002a2a00`, before Mac RGB is `002ad500` and Layer `004080c0`. First differing output: G byte 2 for RGB, R byte 1 for Layer. The completed auxiliary-plane pairing below locates an earlier missing pre-blur lane in staging; callback ownership/color selection also differs despite the matching distance scalar. All six full outputs are exact after the change.
- Static `181172906..18117291b` merges blurred planes with the pre-blur scalar; PF8 callback `18117098f..1811709c3` loads its independent field RGB lanes, and `181170a7d..181170a88` branches before interpolation at FLOAT32 0.0001. Layer selection `181170be9..181170bf1` uses original source RGB. PF32 sibling `181170f79..181170f92` has the same selection. Mac now retains/typed-stages the pre-blur scalar and uses it for the early-exit blue lane, extends early ownership and direct Layer selection to blurred Smart, and prevents Classic PF16 color inheritance/PF32 Both bypass from affecting Smart.
- `verify_distancegradation_smart_C08.py` runs ordinary before/current and current ASan+UBSan on 600 campaign inputs, 432 independent matrix inputs, and 145 corpus inputs. No diagnostic, timeout or byte/status disagreement. All base-exact outputs remain byte-identical. Fresh seed 3 census originally had one Mac timeout at 10 seconds; the verifier's 30-second limit completes it. Its AEX completion set is 289 success / 8 reject / 3 budget.

| Cluster 1 source | Seed 1 Smart exact | Fresh seed 3 Smart exact |
| --- | ---: | ---: |
| Before | 225 | 217 |
| After | 235 | 227 |

- Seed 1 now has 7 mismatches / 51 refusals / 7 uncompared using the same original references. Ten newly exact cases: 39,48,62,77,133,167,173,174,186,222. Three positive-blur cases remain nonexact (45,200,214); their field/blur cause is not declared closed.
- Independent matrix: 196 previous exact unchanged, 236 mismatch->exact, 432/432 final exact. PF8/PF16/PF32, 7×1/1×7, Box/Gaussian size1, Constant/Linear/Sphere, Inside/Outside/Both, RGB/Layer, background off/on, nontrivial colors and 3/5-byte padding.
- Corpus rebaseline table: all 145 unchanged (143 exact, two retained mismatches); no expectation edits. Production replay exits 0, all 145 match saved results.
- Existing beta tests: 9 pass; transactional tests: 2 pass. `git diff --check` passes. Evidence with hashes and full per-case comparisons: `reports/fuzz/olmdistancegradation_C08_blurred.json`. Cosmetic comment/brace cleanup after the first verifier build does not change arithmetic; the follow-on census binds final source.

Cluster 2 (base `d3fe5c3e`, PF8 direct-range normalization):
- Original helper `18117490b` selects the 255 normalization maximum, `181174942` calls cvNormalize, then owner `181172932` converts the merged world. The paired trace calls original public Smart without guest detours and binds both scaled planes and final public raw hashes.
- Saved case58 (1×70): first different scaled field word at y=53, AEX little-endian `00805443` (212.5), Mac `01805443` (212.50001525878906). Two scaled words differ. Case236 (1×40): the same first word at y=38; one word differs. AEX thresholded distance at those points is 5 with maximum 6. The new Mac scaled plane equals every original float word (70/70 and 40/40), before unchanged nearest-even byte packing. Final Smart outputs equal AEX hashes.
- General fix: distance helper accepts its normalization range maximum, default 1 to preserve every existing caller. Unblurred Smart PF8 requests 255 directly, then packs nearest-even and converts the byte to the callback's normalized scalar. Monotonic packing commutes with the Both maximum. Classic, PF16 reciprocal normalization/roundtrip, and positive-blur field arithmetic retain their prior contracts. No output-byte correction or special coordinate/value case is used.
- `verify_distancegradation_smart_C08.py --before-ref d3fe5c3e` replays 600 campaign inputs, 216 independent field inputs, and 145 retained corpus inputs through before/current/sanitized current. Seed1 235->239 exact; seed3 227->230 exact. No base-exact changes or sanitizer/ordinary disagreement. Seed1 remaining E/M/R/U: 239/3/51/7 on the recorded oracle set.
- Matrix: 194 previous exact preserved, 22 mismatch->exact, 216/216 final exact. 17×1 runs and 13×7 islands, thresholds3/6/13, Inside/Outside/Both, invert off/on, Constant/Linear/Sphere, RGB with background and Layer without, odd strides. Captured source/field semantics and the independent matrix are evidence for this unblurred PF8 operation only.
- Corpus update changes only result/provenance in the two rows below; input/control/reduction data, original oracle hashes, and Classic results are unchanged. Other 143 cases are unchanged exact. Production replay exits 0: `replay_matches_saved=true`, 145 completed; all 145 actual Smart outputs exact.

| Corpus case | Before Smart hash/status | After/AEX Smart hash/status |
| --- | --- | --- |
| `seed1_case000058_92552f06afe6.json` | mismatch `5832287e608ff319a3d2d04808d8693479d1d65d94c127060db4f770f50c41d7` | exact `76e3b8146375dd2ae3ad6b75971ea687c3cfef82a2da89ae1767bf8d27446806` |
| `seed1_case000236_92552f06afe6.json` | mismatch `49ca803bc1bbf1d905affbf79da3572dfb50d23756fa646ec133168b62cec4d3` | exact `5d89d966579f74a853f35e1f0c81b8f4f444ffbd4e65a6edb50581e912deb498` |

- Existing beta9 + transactional2 tests pass again; diff check passes. Two initial diagnostic builds exposed a missed debug-call/forward-declaration update; those compile defects were corrected before any rendering measurements. Evidence: `reports/fuzz/olmdistancegradation_C08_field.json`.

Cluster 3 (base `d9236d8c`, inactive PF32 filters):
- Narrow gate-off experiment changes only the unblurred admission predicate in a scratch source: Blur Modes2/3/4 at Size0 join Mode1, with existing Constant/Linear/Sphere, owner, threshold, downsample and bounded-SDR guards retained. Original owner `1811728aa..181172901` forms `2*scaled_size+1`, hence a 1×1 kernel at Size0. Mode5 is excluded; broad gate-off already demonstrates its nonidentity counterexamples at zero size.
- Gate-off before promotion: `verify_distancegradation_smart_C08.py --before-ref d9236d8c --candidate-source <ticket scratch>/inactive-experiment.cpp --strict-admission` with seed1+fresh seed3 campaigns and corpus, then `--inactive-matrix`. All 600 campaign runs and 145 corpus runs agree with ASan+UBSan. Seed1 admits exactly indices15/32/63/182/194/199/220 (7/7 exact); seed3 admits113/171/235/265/268/299 (6/6 exact). Every previously rendered output, including residual mismatches, is unchanged. There are zero admitted mismatches or admitted cases without successful original-AEX output.
- The committed `--inactive-gate-off` option reproduces that exact source mutation from `--before-ref`; its generated source SHA-256 agrees with the initial scratch experiment (`296867fd057e4d73de71997ea12425d2780798fd8ed5d1d1c11d63eb80521943`). No diagnostic switch exists in production.
- Independent matrix: 648/648 original public Smart PF32 cases change refusal->exact, with ordinary/sanitized raw bytes and statuses identical. It spans 7×1/1×7/7×5, all three admitted zero-size modes, three In/Out modes, invert off/on, Constant/Linear/Sphere, RGB/Layer, both background states, nontrivial colors, ownership-cutoff neighbors, mask threshold, zero/full/partial alpha, and odd input/output padding.
- Seven negative controls remain clean refusals: Mode5, Power, alpha just above1, RGB just above1, negative RGB subnormal, infinity, and NaN. The public host verifies source preservation, destination padding, no destination writes on refusal, and balanced parameter checkout/checkin. Gate-off and production negative-result records are identical.
- After promotion, ordinary before/current and ASan+UBSan current recheck all 600 campaign cases, all 648 matrix cases, all seven negative controls, and all 145 corpus inputs. Every per-case comparison record is identical to its gate-off counterpart. Production matrix is 648/648 exact; no sanitizer diagnostic/timeout or regression. Corpus stays 145/145 exact with no further edits.
- Final full `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0` census exits0: **246 exact / 3 mismatch / 44 refusal / 7 uncompared**; original AEX Smart290 success / 8 reject / 2 budget. All 300 input hashes and Classic result dictionaries equal starting census (Classic10 exact /290 mismatch). All 225 originally exact Smart result dictionaries, including raw hashes, are identical. Source SHA-256: `c05ebb53f1f089d050959decc1629673b2874da478e4c88372c82f5ae1d315f7`.

| Source stage | Seed1 Smart E/M/R/U | Fresh seed3 Smart exact |
| --- | --- | ---: |
| Starting `b4350d64` | 225/17/51/7 | 217 |
| Blurred `d3fe5c3e` | 235/7/51/7 | 227 |
| PF8 field `d9236d8c` | 239/3/51/7 | 230 |
| Inactive filters (this commit) | 246/3/44/7 | 236 |

- Starting-to-final seed1 transitions: exact->exact225; mismatch->exact14; refusal->exact7; mismatch unchanged3; refusal unchanged44; uncompared unchanged7. Refusals comprise bounded-SDR32 and profile12; 41 of the refused cases have successful original-AEX renders. These remain unresolved, not accepted mismatches.
- Final production replay exits0, `replay_matches_saved=true`, 145 completed and all Smart exact. Aggregate git audit finds only the two corpus files listed above changed, and only result/provenance; all original oracle hashes, inputs, controls, reduction history and Classic results are preserved. Final beta9 + transactional2 tests pass; diff check passes.
- Completed blurred-stage pairing re-renders original `b4350d64` and final source with the same natural public/callback captures. The original blue field lane is the pre-blur scalar; Mac's old sole auxiliary lane instead contains the post-blur scalar. They differ in14/18 sampled words (first Inside pixel: Mac `a9a8283e`, AEX `00000000`), before composition. Final auxiliary words match18/18, all source/distance-scalar pairs still match, and all six final public outputs are exact. This sharpens the first-stage attribution: retain the pre-blur plane at staging, then restore Smart callback selection. Unconsumed staging differences on owned pixels are not independently counted as output fixes.
- Final evidence: `reports/fuzz/olmdistancegradation_C08_admission.json`, including gate/production equality, negative controls, final census/replay, source/tool/worker bindings and extended stage pairing. Scratch is about23MiB (21,303,849 logical bytes at audit); no compiled `mac`, `.o` or `.dylib` files remain after automatic temporary-build cleanup.

inference:
- The PF8 residual comes from normalizing to 1 and then scaling, which adds a floating-point rounding absent from the original direct-to-255 operation. The new paired pre-packing values distinguish this from a writer tie-rule error.
- The blurred callback residual inherited Classic heuristics and omitted the original early exit's distinct blue field lane. The measured operation is restored; this does not establish general blur/kernel equivalence.
- Zero-size Modes2–4 are an identity-filter admission rule grounded by the original kernel-size construction and exact independent cases; this does not generalize to Mode5, effective blur, Power or extended source domains.
- Broad PF32 refusal removal is unsafe. Finite-domain and inactive-filter subrules need independent boundary evidence; successful sampled HDR outputs alone do not authorize admission.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `core/olmdistancegradation_fieldgen.cpp`
- `core/olmdistancegradation_fieldgen.h`
- `tools/emulation/trace_distancegradation_smart_C08.py`
- `tools/emulation/trace_distancegradation_field_C08.py`
- `tools/fuzz/verify_distancegradation_smart_C08.py`
- `reports/fuzz/olmdistancegradation_C08_blurred.json`
- `reports/fuzz/olmdistancegradation_C08_field.json`
- `reports/fuzz/olmdistancegradation_C08_admission.json`
- `tests/fuzz_corpus/olmdistancegradation/seed1_case000058_92552f06afe6.json`
- `tests/fuzz_corpus/olmdistancegradation/seed1_case000236_92552f06afe6.json`
- `orchestra/reports/C08-dg-smart-r2.md`

verify:
Run from this worktree. These commands validate the **final** source, while the before refs retain each operation's historical baseline:
```sh
s="$PWD/orchestra/state/C08-dg-smart-r2"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$s" --report "$s/verify-seed1.json" --corpus "$s/verify-corpus" > "$s/verify-seed1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 3 --jobs 2 --shrink-attempts 0 --case-timeout 30 --scratch "$s" --report "$s/verify-seed3.json" --corpus "$s/verify3-corpus" > "$s/verify-seed3.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C08.py --before-ref b4350d64 --scratch "$s/verify-blurred" --report "$s/verify-blurred.json" --campaign "$s/verify-seed1.json" --campaign "$s/verify-seed3.json" --blur-matrix --corpus > "$s/verify-blurred.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C08.py --before-ref d3fe5c3e --scratch "$s/verify-field" --report "$s/verify-field.json" --field-matrix --corpus > "$s/verify-field.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C08.py --before-ref d9236d8c --strict-admission --scratch "$s/verify-admission" --report "$s/verify-admission.json" --campaign "$s/verify-seed1.json" --campaign "$s/verify-seed3.json" --inactive-matrix --corpus > "$s/verify-admission.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C08.py --before-ref d9236d8c --inactive-gate-off --strict-admission --scratch "$s/verify-gateoff" --report "$s/verify-gateoff.json" --campaign "$s/verify-seed1.json" --campaign "$s/verify-seed3.json" --inactive-matrix --corpus > "$s/verify-gateoff.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C08.py --source-ref b4350d64 --blur-mode 2 --blur-size 1 --scratch "$s/verify-trace-before" --report "$s/verify-trace-before.json" > "$s/verify-trace-before.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C08.py --blur-mode 2 --blur-size 1 --scratch "$s/verify-trace" --report "$s/verify-trace.json" > "$s/verify-trace.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_field_C08.py --scratch "$s/verify-field-trace" --report "$s/verify-field-trace.json" > "$s/verify-field-trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --scratch "$s" --report "$s/verify-replay.json" > "$s/verify-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/verify-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/verify-transactional.log" 2>&1
git diff --check
```
Expected final: seed1 246/3/44/7; seed3 236/4/53/7 on the recorded original-reference completion set. All base-exact bytes preserved; matrices432/432,216/216,648/648 exact; gate/production admission rows equal; seven unchanged clean refusals; sanitizer equality throughout. The blurred trace preserves18/18 auxiliary words after versus14 differing before and six exact final outputs. Both PF8 scaled planes and public outputs exact. Replay145/145 matches saved, all Smart exact; tests9+2 pass. Oracle timeout/reject labels can vary with time limit and workstation load; compare explicit successful-reference sets.

next:
- Three independently committed clusters are closed; stop under the ticket rule. Overall plugin compatibility remains incomplete.
- **DG-PF32-SMART-ADMISSION-R3:** 32 bounded-SDR and12 profile refusals remain, 41 with successful AEX renders. Broad admission is refuted. Successful finite gate-off examples alone do not prove a general domain; pair conversion/ownership boundaries before promoting any rule. Keep Power, nonfinite, Mode5 and effective-filter policies separate.
- **DG-BLUR-STAGING-R3:** isolate the first internal difference of the three seed1 residuals below. Their final-byte differences do not justify a writer adjustment or establish an external-dependency cause.

| Case | Geometry/depth/filter | Different typed words | First byte / original / Mac |
| --- | --- | ---: | --- |
|45|14×20 PF8 Gaussian size4|6|32 / `e9` / `ea`|
|200|239×1 PF8 Bilateral size18|45|28 / `de` / `dd`|
|214|34×23 PF16 Gaussian size10|1|4042 / word `b956` / word `ba56`|

- Preserve native AE/UCRT/IPP, ROI/downsample and installed-bundle boundaries. No release gate, ledger, other plugin, MAIN, external worker/source or installed bundle changed. No push, merge, history rewrite or stash. All scratch is ticket-local, well below5GiB, and regenerable compiled outputs are removed.
