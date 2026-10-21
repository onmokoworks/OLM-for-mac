status: partial

summary:
- Cluster 1 closed: restore the original component-map row bounds; Smart seed 1 improves 235 → 257 exact, 23 → 1 mismatch.
- All 235 baseline exact Smart outputs are unchanged; fresh seed 2 improves 243 → 265 exact with no exact regressions.
- Ten T10 representative signatures now have exact rotated planes, component maps, divisors and final pixels; 17 saved Smart mismatches become exact.
- 656 cases agree between O2 and ASan/UBSan on both Mac routes; two retained regression tests pass (684 renders).
- Cluster 2 admits bounded generated Noise: Smart seed1 257 → 262 exact, seed2 265 → 269; no new mismatch or exact regression.
- Size×Fade and the remaining mathematical-import boundary are retained for separate investigation.

facts:

Starting revision `ae083498` on `orch/C02-dblur-smart`. Read AGENT_GUIDE.md, GOTCHAS.md, the DirectionalBlur ledger rows/forbidden actions, compatibility plan, and T10/F05/F06/F16 reports. MAIN, original AEX, emulator source/workers, release gates and ledger were not modified. All scratch/compiler temporary paths are under this ticket's scratch; no push/history rewrite.

**First divergent stage.** The paired probe executes the original parameter builder, typed populate/output callbacks, rotate, component-map and rowdriver instructions. Only host callbacks/imports are emulated; no rotate/rowdriver detours. It checks the stack ABI with an original prepass leaf. Original fixture final bytes equal cached Smart session bytes in all ten representatives. Original and Mac rotated planes agree exactly. Their first differing stage is the component map (2–6 float words, divisor exact). Example C02: work pixel (2,3) AEX record `[2,3,1,-1]`, Mac `[2,3,3,0]`; center word at byte offset 376 is `0000803f` vs `00004040` little endian.

The original run graph seeds min=row and max=0. Assembly `0x18000284e..0x18000285a` updates min and max in mutually exclusive arms; the initial run does not set max. Thus a component confined to its first row retains max=0. The raster-first seed is the component's minimum row. The pixel traversal now preserves this general run-level rule. No coordinate, source, expected-value or quantization correction was introduced. Cross-row components keep their existing maximum.

**Measured Smart table:**

| Input set | Before exact/mismatch/refusal/uncompared | After | Existing exact changed |
|---|---|---|---:|
| seed 1, n300 | 235 / 23 / 40 / 2 | 257 / 1 / 40 / 2 | 0 |
| fresh seed 2, n300 | 243 / 23 / 32 / 2 | 265 / 1 / 32 / 2 | 0 |
| saved corpus, 56 | 37 / 19 / 0 / 0 | 54 / 2 / 0 / 0 | 0 |

The required `run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2` before/after campaigns both exited 0. Each has 298 completed Smart AEX renders; indices 274/289 hit the 10-second wall timeout. Index289 output changes while uncompared; it is explicitly not counted exact. Fresh-seed index36 similarly changes while uncompared. The current F18 framework pairs Classic with its own original Classic reference (zero output here), unlike the older T10/F06 reports. Classic remains 3 exact / 257 mismatch / 40 refusal in seed1; this ticket makes no Classic compatibility claim. Corpus numerical improvement is asserted for **Smart**; route-aware Classic diffs are recorded faithfully where shared-core output changes.

`verify_directionalblur_c02.py` runs baseline, current O2 and current ASan/UBSan builds: 600 generated plus 56 saved cases, both Mac routes; all current/sanitized result metadata and bytes agree. Flags include `-fsanitize=address,undefined -fno-sanitize-recover=all`; leak checking disabled. No sanitizer diagnostics/crashes. The recheck script's saved-corpus validation was subsequently made idempotent for already-rebased corpus; numerical execution is unchanged. `test_directionalblur_general_input_owner_20261001` and `test_directionalblur_general_features_20261001` passed (2 tests, 684 live O2/sanitized renders). Corpus replay exited 0, 56/56 matches_saved.

**Corpus before/after (17 changed; other 39 unchanged).** Original inputs, parameters and reduction/provenance remain intact; the current observed result and C02 revalidation record were updated.

| File under tests/fuzz_corpus/olmdirectionalblur | Smart different bytes | Mac hash prefix before → AEX/current |
|---|---:|---|
| `seed1_case000025_3cbdb094278a.json` | 4 → 0 | `b78d4b3495de` → `c317271f8cf7` |
| `seed1_case000026_6a83c3772974.json` | 1 → 0 | `a835e5584cb7` → `c2b8a1f5754b` |
| `seed1_case000038_dd2462acc10c.json` | 2 → 0 | `0b9fad93f8f0` → `641ab24d2940` |
| `seed1_case000063_c722483c6e21.json` | 6 → 0 | `bf11bbeff724` → `54c9d5c41188` |
| `seed1_case000069_6a83c3772974.json` | 8 → 0 | `5b4d1fc787c4` → `0a5ae1f61b15` |
| `seed1_case000072_4aadf2615b0e.json` | 2 → 0 | `3908cb39c1d1` → `c072a1c07eed` |
| `seed1_case000083_dd2462acc10c.json` | 14 → 0 | `a99ad2012f8a` → `9e5602e485f5` |
| `seed1_case000134_bf3e93799c19.json` | 7 → 0 | `44c7afe2fe70` → `21665e70912c` |
| `seed1_case000143_96c04fce153a.json` | 4 → 0 | `cf4f6b3b002f` → `b6f753ec50e9` |
| `seed1_case000147_96c04fce153a.json` | 8 → 0 | `3fab0cd0adc1` → `ef29aaa5f0ed` |
| `seed1_case000149_dd2462acc10c.json` | 2 → 0 | `cbdd14195f21` → `a37b1f74056f` |
| `seed1_case000157_96c04fce153a.json` | 5 → 0 | `3f234ab50b3e` → `b810f4bd712e` |
| `seed1_case000211_6a83c3772974.json` | 3 → 0 | `9f9228fb042e` → `1d197fc99148` |
| `seed1_case000213_4aadf2615b0e.json` | 3 → 0 | `b70112b8ad49` → `9c960f931046` |
| `seed1_case000223_172802d3457b.json` | 32 → 0 | `e42a92f1d439` → `b54792e01cc9` |
| `seed1_case000277_da7b8a17bffd.json` | 19 → 0 | `b08270486584` → `db3872f2c9b5` |
| `seed1_case000287_714cd4993615.json` | 6 → 0 | `f8f1d48d51a0` → `c4761c71c2f7` |

The 10 representatives are T10 C02/C03/C08/C09/C10/C11/C12/C13/C14/C18. Their final differing-byte counts were 2/6/1/19/6/4/2/7/32/4, now all zero. This is one general root-cause fix spanning multiple signature clusters, so it is committed together.

inference:
- The old code reconstructed geometric bounds conventionally instead of preserving the original run accumulator initialization/branch order. Exact incoming planes and differing records, followed by exact corrected maps and outputs, support this cause.
- Finite campaigns and corpus are not arbitrary-input or native Windows AE/UCRT proof. The original single-row behavior may be unintended, but is the binary contract.

changed_files:
- core/dblur_frontonly.cpp
- tools/emulation/probe_directionalblur_c02_stages.py
- tools/fuzz/verify_directionalblur_c02.py
- 17 corpus files listed above
- reports/fuzz/c02_dblur_smart/{before,map-after,map-verify,map-stages-before,map-stages-after,map-replay}.json
- orchestra/reports/C02-dblur-smart.md

verify:

Run from this worktree (the commands below regenerate evidence in scratch):

```sh
S="$PWD/orchestra/state/C02-dblur-smart"
W=/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2 --scratch "$S" --worker "$W" --report "$S/recheck.json" --corpus "$S/recheck-corpus" --shrink-attempts 0 > "$S/recheck.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c02.py --baseline ae083498 --worker "$W" --report "$S/verify-recheck.json" --corpus > "$S/verify-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/stages-before-recheck.json" --core-ref ae083498 > "$S/stages-before-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/stages-after-recheck.json" > "$S/stages-after-recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 2 --replay tests/fuzz_corpus/olmdirectionalblur --scratch "$S" --worker "$W" --report "$S/replay-recheck.json" --corpus "$S/replay-unused" > "$S/replay-recheck.log" 2>&1
export PYTHONPATH=tests
export CPLUS_INCLUDE_PATH='/Users/onmk/Documents/Projects/Personal/OLM as/Headers:/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP:/Users/onmk/Documents/Projects/Personal/OLM as/Util:/Users/onmk/Documents/Projects/Personal/OLM as/Resources'
"$P" -m unittest test_directionalblur_general_input_owner_20261001 test_directionalblur_general_features_20261001 > "$S/tests-recheck.log" 2>&1
git diff --check
```

Expected at this commit: 257 exact / 1 mismatch / 40 refusal / 2 uncompared Smart; verifier PASS 656; ten stage/final pairs exact after; replay 56/56; two tests pass. Wall budgets can vary with load. The remaining seed1 mismatch is index84 (PF16 neutral), unchanged.

next:
- Gate-off PF8 generated-Noise and Size×Fade families separately; retain any unproven cross or negative-Offset allocator boundary.
- Record the PF16 neutral expf dependency boundary without changing the ledger-preserved Gaussian contract.


## Cluster 2 — bounded generated-Noise fallback

facts:
- Baseline is cluster-1 commit `08216d532f12921d9d3fce1352a772d717336650`. The public PF8 fallback now permits generated Noise when Offset is nonnegative, Noise Type is not Layer, and Size×Fade is absent. Existing exact/retained routes keep precedence and all world/workspace/staging/budget checks remain. No noise generator arithmetic, negative-index policy or output conversion changed.
- The blanket scratch-only gate experiment ran seed1+seed2 n300 with O2 and ASan/UBSan, 600 Smart cases. Seed1: 26 changed refusals → 21 exact / 1 mismatch / 4 core refusals. Seed2: 20 changed → 17 exact / 1 mismatch / 2 core refusals. No sanitizer disagreement. The two mismatches both have Size×Fade without Noise: seed1 index200 differs by 11 bytes (first offset73, `31` → `32`); seed2 index152 differs by 1 byte (offset30895, `f7` → `f6`). This refutes blanket admission and provides new byte boundaries. Production retains that cross guard. Negative Offset and Layer stay excluded from the new fallback.
- F16's unresolved generated-Noise index102 has a now-paired first divergence: rotated plane, divisor and 1818 weights exact, old component map differs by eight words and final output by one byte. With the restored map, all stages/final bytes agree. Index145 has two old map-word differences but identical final bytes; corrected map and final bytes are exact. Both original fixtures match cached Smart session outputs. These are generated unshrunk inputs, not the already-exact saved reductions.
- Production verifier passes 656 cases (600 generated + 56 saved), both routes, normal vs ASan/UBSan. All base-exact Smart bytes remain unchanged, all newly rendered outputs are exact in both seeds. No corpus file changes in this commit.

| Smart set | Before exact/mismatch/refusal/uncompared | After | New exact indices |
|---|---|---|---|
| seed1 n300 | 257 / 1 / 40 / 2 | 262 / 1 / 35 / 2 | 102,131,139,145,226 |
| seed2 n300 | 265 / 1 / 32 / 2 | 269 / 1 / 28 / 2 | 72,163,254,271 |
| saved corpus | 54 / 2 / 0 / 0 | 54 / 2 / 0 / 0 | none |

The required n300/seed1/jobs2 campaign exits 0 with 298 completed AEX Smart renders and two wall budgets. No accepted-output hash changes except refusal→exact. Corpus before/after is 56 identical current result dictionaries. The verifier was invoked with `--baseline HEAD` while HEAD was `08216d5`; its committed evidence additionally resolves that revision explicitly.

inference:
- The component-map fix closes the F06/F16 positive-Offset generated-Noise counterexample. General admission of the demonstrated feature shape is supported; arbitrary Noise×Size×Fade and negative-Offset native allocation semantics are not.
- A successful blanket case does not establish all crosses: the production rule deliberately preserves the independently disproven Size×Fade boundary.

changed_files (cluster 2):
- mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp
- tools/fuzz/probe_directionalblur_c02_admission.py (scratch-only experiment; pinned baseline for repeatability)
- tools/emulation/probe_directionalblur_c02_stages.py (generated-input/leaf/stage options)
- reports/fuzz/c02_dblur_smart/{noise-after,noise-verify,noise-stages-before,noise-stages-after,gate}.json
- orchestra/reports/C02-dblur-smart.md

verify (cluster 2, same S/W/P and temporary environment as above):

```sh
python3 tools/fuzz/verify_directionalblur_c02.py --baseline 08216d532f12921d9d3fce1352a772d717336650 --worker "$W" --report "$S/noise-verify-recheck.json" --corpus > "$S/noise-verify-recheck.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c02_admission.py --baseline 08216d532f12921d9d3fce1352a772d717336650 --worker "$W" --report "$S/gate-recheck.json" > "$S/gate-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/noise-stages-recheck.json" --indices 102 145 > "$S/noise-stages-recheck.log" 2>&1
```

Expected: verifier PASS 656, production Smart 262/1/35/2 (seed1) and 269/1/28/2 (seed2), gate 600 O2/sanitized matches with the two recorded Size×Fade mismatches, two generated-Noise stage/final pairs exact. Cluster1 historical counts remain tied to its commit; current campaign is 262 exact.
