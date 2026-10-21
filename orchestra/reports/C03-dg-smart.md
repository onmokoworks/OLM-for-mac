status: partial

summary:
- Closed Smart unblurred Layer source composition and the Smart source-mask quantization boundary in separate commits.
- Seed 1 Smart: 177/65/51/7 -> 199/43/51/7 -> 216/26/51/7 (E/M/R/U); every prior exact output preserved.
- Fresh seed 2: 168 -> 191 -> 208 exact; sanitized replays agree with ordinary output.
- Independent Layer matrix now 324/324 exact across three depths; all 24 prior mask residuals are resolved.
- Three retained corpus cases have improved to exact across the two fixes. Refusal guards remain unchanged.

facts:

Cluster 1 (commit `9b7401f9`, Layer source composition):
- Starting HEAD: `1b656d418ba44543da2225097108796f0937d9cc`, branch `orch/C03-dg-smart`.
- Read AGENT_GUIDE, GOTCHAS, the DG forbidden-action row, compatibility plan, T07, F01/F02 and F10/F12 methods. MAIN and emulator sources are read-only. Worker INDEX was inspected; the existing retained public worker remains `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. No rebuild.
- Original AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. All comparisons use original AEX Smart against production Mac public Smart, with typed raw bytes. Native AE/UCRT equivalence is not claimed.
- `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0` with ticket scratch/corpus reproduces 177 exact / 65 mismatch / 51 refusal / 7 uncompared. Original AEX Smart: 290 success / 8 reject / 2 budget. Classic is separately compared to AEX Classic (10 exact / 290 mismatch); no Classic numerical code is changed.
- Scratch-only all-gates-off ASan/UBSan seed 1: 200 exact / 90 mismatch / 9 uncompared / 1 candidate timeout, no sanitizer diagnostic. Thus the broad admission hypothesis is refuted: 23 refusals become exact, 25 become mismatches, two become uncompared, one times out. Source profiles separate nonnegative HDR, signed, and nonfinite counterexamples; no gate is promoted. Seed 2 profile-only gate-off is also retained in `olmdistancegradation_C03_gates.json`. Timeout is not counted as sanitizer success for that input.
- Natural AEX public owner captures preserve builder-generated refcon, source, and staged field. Relocating only the two world pointers and replaying the original PF8 callback reproduces the full public output hash in all six RGB/Layer x Inside/Outside/Both controls. Original source normalization and staged field equal the Mac values. Before the fix, Layer first differs at color selection/composition. Example 3x1 source `004080c0804080c0ff4080c0`, Inside Layer: AEX `000000003f4080c0004080c0`, Mac `004080c03f1f3f3f00000000`. The first byte difference is R at pixel 0 (AEX 00, Mac 40); the owned center pixel has the same alpha 3f but AEX RGB 4080c0 versus Mac 1f3f3f.
- Original `FUN_181170870` source loads at `181170a09..a5b` and Layer selects XMM12/13/14 at `181170be9..bf1`; no alpha division or RGB premultiplication occurs. PF16/PF32 sibling callbacks have the same source selection. The original cutoff bytes at `181504a84` are `17b7d138` (FLOAT32 0.0001). An initial diagnostic candidate used 0.001; reading this new binary boundary corrected it before commit. That rejected intermediate candidate is not the production result.
- The final six paired controls are all exact. `verify_distancegradation_smart_C03.py` re-renders before/current/sanitized current: 600 campaign cases plus 324 independent matrix cases plus 145 retained corpus cases. No sanitizer errors; sanitized status/metadata/raw bytes equal ordinary current output. Seed 1 exact 177->199; seed 2 168->191. Seed 2 final E/M/R/U is 191/39/62/8 using its 291 successful AEX references. The initial 10-second sanitized campaign had one candidate timeout; the verifier uses a 30-second per-case limit and completes all 300.
- Independent matrix spans PF8/PF16/PF32, 3x1/1x3/7x3, zero/half/full and low-alpha sources, Inside/Outside/Both, invert off/on, Constant/Linear/Sphere, odd source/destination strides. 300 newly exact; 24 PF8 low-alpha cases remain mismatched. Original public mask for alpha bytes [0,1,255] is [0,0,255], while current Mac mask is [0,1,1]. This is a newly captured upstream boundary, not a compose rounding inference.
- Existing generic-production and PF32-unblurred beta tests: 9 passed (`python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py'`), including existing sanitizer coverage. Smart transactional tests also pass (2 tests). `git diff --check` passes.

Corpus rebaseline (fresh base/current Smart, Classic unchanged):

| Case | Before | After | Saved action |
| --- | --- | --- | --- |
| `seed1_case000135_12bacfc8ca6e.json` | mismatch, `c47adf5274bdeb9dbbe73e1e406537f8ca25384e46fb2e96aaefedd2118b396d` | exact, `692f214afe1bf717b00d342c0d6753912543c7e717b2f11ac0714ea88799ded5` | result/provenance refreshed |
| Other 144 | 139 exact / 5 mismatch | unchanged | none |

Cluster 2 (Smart source-mask quantization; base `9b7401f9`):
- `source_mask_owns_alpha` now accepts the owner. Smart uses FLOAT32 `alpha*255 >= 1.5`, matching nearest-even 8-bit conversion followed by threshold strictly above 1; Classic retains the original depth-dependent rule. The actual mask builder and logging use the same owner selection. No EDT/normalization/blur/writer operation changes.
- Natural Smart source bytes `[0,1,255]` produce original mask `00 00 ff` (plus one padding byte); before Mac mask is `00 01 01`, after `00 00 01`. First differing mask sample is x=1, before field generation. Six original public/callback hashes remain bound; after the fix all six source, staged-field and final-output pairs agree. For Inside RGB the pre-fix first output difference is alpha at x=1, AEX `01`, Mac `00`.
- Full seed-1 census exits 0, 300 complete: Smart 216 exact / 26 mismatch / 51 refusal / 7 uncompared, AEX 290 success / 8 reject / 2 budget, Classic unchanged at 10/290. `verify_distancegradation_smart_C03.py --before-ref 9b7401f9` verifies 199->216 exact on seed 1 and 191->208 on fresh seed 2, no exact changes; seed 2 final E/M/R/U is 208/22/62/8.
- Sanitized and ordinary current runs agree for all 600 campaign inputs, 324 independent matrix inputs and 145 corpus inputs; no sanitizer diagnostics. Matrix: 300 prior exact unchanged, 24 mismatch->exact. Existing beta tests: 9 pass. Build outputs are automatically removed.
- Public production corpus replay after each of clusters 1 and 2 exits 0, 145 completed and all 145 `matches_saved` (report aggregate is boolean true).
- Corpus comparison to `9b7401f9`: 140 exact unchanged, 2 mismatch->exact, 3 mismatch unchanged. Only result/provenance are rebaselined for the two improvements below. Inputs, controls, reduction history and oracle hashes are preserved. Full hashes and transition data are in `reports/fuzz/olmdistancegradation_C03_mask.json`.

| Corpus case (Smart only) | Before | After |
| --- | --- | --- |
| `seed1_case000091_92552f06afe6.json` | mismatch; `4de36cd696c423238792fc42f583878a3cf38bacda2fa2da6f1550811f8e3e3a` | exact; `b0570697ecf859f4e0f3768f0c7edb0fdc7e668cfd89be3f2a65d7afef5fa8ed` |
| `seed1_case000139_92552f06afe6.json` | mismatch; `f6fc2d44ee3319c47476a7918d2e0d35cba8e801bebc910296dd4a6cfbb11a9f` | exact; `8007046ac31b84e8d5b2ecf91b30307308d01a0064779a9faf9ce3f109eea89a` |

inference:
- The Layer residual is caused by applying legacy Classic source-color heuristics to the Smart callback. The restored operation is limited to unblurred Layer/no-background, preserving Classic and blurred contracts.
- The 24 first-commit matrix differences were caused by Smart inheriting the Classic PF8 inclusive mask. The second commit restores the public Smart owner boundary; it does not retune EDT or final-byte rounding.
- Broad PF32 gate removal is unsafe on the measured inputs. Inactive Blur Modes 2–4 at size zero are a promising separate rule (7 exact gate-off cases on each seed), but no admission is claimed here.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/emulation/trace_distancegradation_smart_C03.py`
- `tools/fuzz/probe_distancegradation_smart_C03.py`
- `tools/fuzz/verify_distancegradation_smart_C03.py`
- `reports/fuzz/olmdistancegradation_C03_{layer,mask,stages,gates}.json`
- `tests/fuzz_corpus/olmdistancegradation/seed1_case000135_12bacfc8ca6e.json` and the two mask cases listed above
- `orchestra/reports/C03-dg-smart.md`

verify:
```sh
s="$PWD/orchestra/state/C03-dg-smart"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$s" --report "$s/verify-seed1.json" --corpus "$s/verify-corpus" > "$s/verify-seed1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 2 --jobs 2 --shrink-attempts 0 --scratch "$s" --report "$s/verify-seed2.json" --corpus "$s/verify2-corpus" > "$s/verify-seed2.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C03.py --scratch "$s/verify-layer" --report "$s/verify-layer.json" --campaign "$s/verify-seed1.json" --campaign "$s/verify-seed2.json" --matrix --corpus > "$s/verify-layer.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C03.py --scratch "$s/trace" --report "$s/verify-trace.json" > "$s/verify-trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --scratch "$s" --report "$s/replay.json" > "$s/replay.log" 2>&1
```
Expected after cluster 2: seed 1 216/26/51/7; verifier base-exact preserved, 324/324 matrix rows exact, sanitizer equality for all rows, three corpus improvements versus starting source; six public/callback/paired traces; replay 145/145 matches_saved. Timeouts may vary under shared-machine load; compare explicit oracle statuses. Reproduce the gate-off experiment with `probe_distancegradation_smart_C03.py --experiment all --sanitized --smart-only` plus the same campaign arguments (diagnostic only).

next:
- Continue with the captured Smart early ownership exit: Outside/background at full source alpha currently writes foreground RGB after AEX has already exited. The six background-control captures are retained in the stages artifact.
- Keep HDR/signed/nonfinite, Power, effective blur and native dependency/host boundaries explicit. No release gate, ledger, MAIN, external worker, installed bundle or other plugin changed; no push or history rewrite.
