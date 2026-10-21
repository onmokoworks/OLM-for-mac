status: partial

summary:
- Closed the unblurred Smart Layer/no-background source-color operation: raw source RGB, original ownership cutoff, and normal alpha interpolation.
- Seed 1 Smart: 177/65/51/7 -> 199/43/51/7 (exact/mismatch/refusal/uncompared); all 177 base-exact outputs unchanged.
- Fresh seed 2: 168 -> 191 exact; all base-exact outputs unchanged. Sanitized replays agree byte-for-byte.
- Independent typed Layer matrix: 300/324 exact; the 24 remaining PF8 cases first diverge at the source mask, now captured for the next cluster.
- One retained corpus case improves to exact; 144 retain their output/status. Refusal guards remain unchanged.

facts:
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

inference:
- The Layer residual is caused by applying legacy Classic source-color heuristics to the Smart callback. The restored operation is limited to unblurred Layer/no-background, preserving Classic and blurred contracts.
- The remaining matrix differences are upstream mask ownership. They require a separate Smart mask fix; they do not justify retuning EDT, final-byte rounding, or accepting tolerance.
- Broad PF32 gate removal is unsafe on the measured inputs. Inactive Blur Modes 2–4 at size zero are a promising separate rule (7 exact gate-off cases on each seed), but no admission is claimed here.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/emulation/trace_distancegradation_smart_C03.py`
- `tools/fuzz/probe_distancegradation_smart_C03.py`
- `tools/fuzz/verify_distancegradation_smart_C03.py`
- `reports/fuzz/olmdistancegradation_C03_{layer,stages,gates}.json`
- `tests/fuzz_corpus/olmdistancegradation/seed1_case000135_12bacfc8ca6e.json`
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
Expected at this cluster commit: seed 1 199/43/51/7; verifier base-exact preserved, 324 matrix rows with 300 exact and 24 explicitly retained mask residuals, sanitizer equality for all rows, one corpus improvement versus starting source; six public/callback/paired traces; replay 145/145 matches_saved. Timeouts may vary under shared-machine load; compare explicit oracle statuses. Reproduce the gate-off experiment with `probe_distancegradation_smart_C03.py --experiment all --sanitized --smart-only` plus the same campaign arguments (diagnostic only).

next:
- Continue with the captured Smart source-mask boundary; then re-rank the residuals and investigate the next cluster.
- Keep HDR/signed/nonfinite, Power, effective blur and native dependency/host boundaries explicit. No release gate, ledger, MAIN, external worker, installed bundle or other plugin changed; no push or history rewrite.
