status: done

summary:
- Reproduced seed46 cases 237/246/275 against the retained F46 original-AEX worker and retained all three as corpus witnesses.
- Restored SSE generated-NaN sign at PF32 alpha arithmetic and preserved unordered alpha through negative Thin.
- Separated stored NaN matte values from the ordered nonzero mask used by native boundary/blur branches.
- Seeds 1/46/47 n300: 900/900 Smart exact, zero refusals; all 897 previously exact route hashes retained.
- Corpus replay 9/9 saved results; independent NaN boundaries 16/16 exact. No admission restriction needed.

facts:
- Baseline commit: `caf79245b17524996d8e2dc0a4c23f298f9a4ced`. Read AGENT_GUIDE.md, GOTCHAS.md, compatibility plan, ColorKey ledger row, and F38 arithmetic helper/report.
- Original AEX and SDK assets were read from MAIN; no worker was rebuilt. Worker: `/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker`, SHA-256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. Full source/AEX/worker bindings and pre-fix exact hashes are committed in `C42-evidence/baseline.json`.
- Ran the following campaign command for seed=1,46,47 before edits (phase=before), after the initial arithmetic/erosion edit (phase=after), and after the topology correction (phase=final), with jobs=1 and no shrinking:

```sh
s="$PWD/orchestra/state/C42-colorkey-pf32-nan-mismatch"
corpus="$s/$phase-corpus$seed"
if [ "$phase" = before ]; then corpus="$s/corpus$seed"; fi
python3 tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed "$seed" --jobs 1 \
  --shrink-attempts 0 --worker /Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker \
  --scratch "$s/$phase$seed" --report "$s/$phase$seed.json" \
  --corpus "$corpus" > "$s/$phase$seed.log" 2>&1
```

| Seed | Before Smart exact/mismatch | Final Smart exact/mismatch | Prior exact routes retaining hash |
|---|---:|---:|---:|
| 1 | 300/0 | 300/0 | 300 |
| 46 | 297/3 | 300/0 | 297 |
| 47 (fresh) | 298/2 | 300/0 | 300 (298 Smart, 2 Classic) |

- All input and per-route oracle bindings are unchanged across before/final. Classic remains 300/300/298 mismatches respectively; this ticket does not claim Classic parity.
- Seed46 first differing words, little-endian, before → final:
  - 237: 3 words; first word36 Mac `00000000`, AEX `4523c17f`; final exact.
  - 246: 5 words; first word116 Mac `0000c07f`, AEX `0000c0ff`; final exact.
  - 275: 3 words; first word144 Mac `0000c07f`, AEX `0000c0ff`; final exact.
- Fresh seed47 also exposed sign-only cases 22 (1 word, first word0) and 178 (194 words, first word40), the same positive/negative default-NaN pair; both final exact and retained.
- Static facts from MAIN `disasm/OLMColorKey.aex.asm.txt` and `decomp/OLMColorKey.aex.c.txt`: negative Thin at `0x180009c7c` uses UCOMISS followed by JZ, skipping both zero and unordered matte alpha. Boundary generation at `0x180008ef7`/`0x180008f60` likewise uses UCOMISS with JZ/JNZ. The curve at `0x18000548f` uses the same unordered-as-zero branch. PF32 blur writeback uses MULSS at `0x1800089a7`/`0x1800089b6`; final alpha subtraction is the existing `0x180004170` callback (SUBSS at `0x18000417a`).
- Initial arithmetic/erosion edit repaired all three seed46 witnesses, but changing only the stored matched mask was insufficient: fresh seed47 case191 (previously exact) acquired 162 differing words, and the Thin=-1 boundary variations had a finite neighbor discrepancy at word116 (`1fb7bc3e` versus zero). This was new boundary evidence, not accepted output. It identified the stored-matte/topology distinction above; final seed47/191 and all boundary variants are exact. The initial boundary data is retained in `C42-evidence/initial-boundaries.json`.
- `python3 tools/fuzz/verify_colorkey_C42.py`: final 16/16 Smart exact. These independently vary positive/negative quiet/signaling NaN payloads, Thin=-1/-2929, and Keep on/off on the retained case237 RGB/classifier input. Temporary binaries are automatically removed.
- Replayed the complete corpus before migration: existing 3 results and added exact regression case191 unchanged; 5 repaired witnesses changed mismatch→exact on Smart. `rebaseline_corpus.py --production-rebaseline C42-colorkey-pf32-nan-mismatch` changed only those 5 new witness files, preserving old results/provenance in history. Final replay: 9/9 matches_saved, all Smart exact. Expected pre-migration replay exit=1 was saved-result drift; final exit=0.
- `python3 tools/fuzz/summarize_colorkey_C42.py` passed: 897 prior exact route hashes retained, identical input/oracle bindings, 900 Smart exact, 16 boundaries exact, 9 corpus matches. Summary and boundary results are committed under `C42-evidence/`.
- `git diff --check` passed. Scratch remains below 5 GiB; no regenerable build trees/executables or started background processes remain. No MAIN, emulator source, release gate, ledger, or other plugin code was modified; no push/stash/history rewrite.

inference:
- The reproduced payload loss came from applying erosion to unordered matte alpha and conflating alpha storage with the native boundary predicate. The sign mismatches came from generated invalid arithmetic results. The correction operates at those general arithmetic/branch boundaries, with no coordinate or expected-output patches.
- This is original-AEX CPU emulation and public fake-host evidence, not native Windows/AE/GPU proof or proof of all nonfinite parameter combinations.

changed_files:
- `mac/OLMColorKey/OLMColorKey.cpp`
- `tools/fuzz/adapters/olmcolorkey.py` (include the existing shared helper in source provenance)
- `tools/fuzz/verify_colorkey_C42.py`
- `tools/fuzz/verify_colorkey_C42.sh`
- `tools/fuzz/summarize_colorkey_C42.py`
- `tests/fuzz_corpus/olmcolorkey/seed46_case000{237,246,275}_C42.json`
- `tests/fuzz_corpus/olmcolorkey/seed47_case000{022,178,191}_C42.json`
- `orchestra/reports/C42-evidence/{baseline,summary,boundaries,initial-boundaries}.json`
- `orchestra/reports/C42-colorkey-pf32-nan-mismatch.md`

verify:
```sh
bash tools/fuzz/verify_colorkey_C42.sh
git diff --check
```
Expected: each seed 300/300 Smart exact, zero Smart mismatches/refusals, 897 prior exact route hashes unchanged, 16/16 boundary cases exact, 9/9 corpus saved results. The wrapper runs the same commands measured above sequentially; logs and reports stay under ticket scratch. It does not rebaseline or modify corpus expectations.

next:
- Orchestrator review/merge. No remaining C42 seed/corpus mismatch or fallback refusal.
- Broader positive-Thin/nonfinite combinations and native AE verification remain outside the measured coverage; do not infer universal equivalence from these campaigns.
