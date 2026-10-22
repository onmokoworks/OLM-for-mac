status: partial

summary:
- Cluster 1 restores blurred Smart callback ownership and Layer source selection; seed 1 improves 225 -> 235 exact, preserving every previous exact byte.
- Fresh seed 3 improves 217 -> 227 exact; 432/432 independent typed blurred cases are exact.
- Ordinary/current ASan+UBSan outputs agree across both campaigns, matrix and all 145 corpus entries.
- Broad PF32 gate removal remains rejected; no admission rule is promoted by this commit.
- Further field-staging and admission investigation continues within C08.

facts:
- Starting HEAD `b4350d648947640ebdc3459c5e0451cbef54c64f`, branch `orch/C08-dg-smart-r2`. Read AGENT_GUIDE, GOTCHAS, DistanceGradation ledger restrictions, compatibility plan, T07/F01/F02/C03 and F10/F12 method. MAIN and emulator sources remain read-only; no worker rebuild.
- Original AEX SHA-256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; retained worker SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`, absolute path `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`. Cache INDEX inspected, no substitution. Typed original-AEX CPU Smart is the oracle; no native AE/UCRT claim.
- `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0` with ticket scratch corpus exits 0: Smart 225 exact / 17 mismatch / 51 refusal / 7 uncompared. AEX Smart 290 success / 8 reject / 2 budget. Classic 10 exact / 290 mismatch.
- Current-base all-gates-off ASan/UBSan experiment, `probe_distancegradation_smart_C03.py --experiment all --sanitized --smart-only` with seed 1, n300, jobs2, timeout30: 258 exact / 32 mismatch / 10 uncompared, no sanitizer diagnostic/candidate failure. Original AEX 290 success / 10 reject. Among previously refused: HDR 12 exact; signed 10 exact / 1 mismatch / 1 uncompared; nonfinite 1 exact / 7 mismatch; SDR 10 exact / 7 mismatch / 2 uncompared. This refutes broad admission; it is diagnostic only.
- Six natural PF8 public Smart captures (RGB/Layer × Inside/Outside/Both, Box size 1) preserve original builder state, source and staged field. Relocated callbacks reproduce every public output hash. Source normalization and distance scalar match Mac before the change. Inside field bytes are `2a2a2a0080808080d4d4d4ff`. AEX first unowned output is `002a2a00`, before Mac RGB is `002ad500` and Layer `004080c0`. First divergent stage: callback ownership/color selection; G byte 2 for RGB, R byte 1 for Layer. All six full outputs are exact after the change.
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

inference:
- The blurred callback residual inherited Classic heuristics and omitted the original early exit's distinct blue field lane. The measured operation is restored; this does not establish general blur/kernel equivalence.
- Broad PF32 refusal removal is unsafe. Finite-domain and inactive-filter subrules need independent boundary evidence; successful sampled HDR outputs alone do not authorize admission.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/emulation/trace_distancegradation_smart_C08.py`
- `tools/fuzz/verify_distancegradation_smart_C08.py`
- `reports/fuzz/olmdistancegradation_C08_blurred.json`
- `orchestra/reports/C08-dg-smart-r2.md`

verify:
```sh
s="$PWD/orchestra/state/C08-dg-smart-r2"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$s" --report "$s/verify-seed1.json" --corpus "$s/verify-corpus" > "$s/verify-seed1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 3 --jobs 2 --shrink-attempts 0 --case-timeout 30 --scratch "$s" --report "$s/verify-seed3.json" --corpus "$s/verify3-corpus" > "$s/verify-seed3.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C08.py --scratch "$s/verify-blurred" --report "$s/verify-blurred.json" --campaign "$s/verify-seed1.json" --campaign "$s/verify-seed3.json" --blur-matrix --corpus > "$s/verify-blurred.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C08.py --blur-mode 2 --blur-size 1 --scratch "$s/verify-trace" --report "$s/verify-trace.json" > "$s/verify-trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --scratch "$s" --report "$s/verify-replay.json" > "$s/verify-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/verify-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/verify-transactional.log" 2>&1
git diff --check
```
Expected at cluster 1: seed1 235/7/51/7, seed3 227 exact on the recorded oracle completion set; 432/432 matrix exact, every base-exact byte preserved, sanitizer equality throughout, six exact traces, 145/145 replay, 9+2 tests. Oracle timeout/reject labels can vary with time limit and shared-machine load; compare explicit successful-reference sets.

next:
- Continue C08: PF8 normalized field staging has a newly captured boundary (AEX distance5 -> 212.5 before byte packing); investigation is not yet promoted.
- Three positive-blur mismatches, 51 refusals and native host/dependency boundaries remain. No release gate, ledger, other plugin, MAIN, worker or installed bundle changed. No push/history rewrite/stash; regenerable builds auto-clean, scratch below 5 GiB.
