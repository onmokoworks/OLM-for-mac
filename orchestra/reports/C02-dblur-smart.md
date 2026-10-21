status: done

summary:
- Smart seed1 improves 235 → 262 exact, 23 → 1 mismatch, 40 → 35 refusals; all baseline exact outputs remain byte-identical.
- One general component-map fix closes ten pre-existing T10 signature clusters; bounded generated-Noise admission closes five more seed1 refusals.
- Fresh seed2 improves 243 → 269 exact; corpus improves 37 → 54 exact / 56, with 17 improvements and no Smart regressions.
- Each production change passed 656-case O2/ASan/UBSan verification; ten paired rotated planes/maps/final outputs and two generated-Noise witnesses are exact.
- Remaining expf and nonfinite NaN boundaries are documented; no Gaussian, writer, NaN-payload policy, or negative-Offset workaround was promoted.

facts:

Starting revision `ae083498` on `orch/C02-dblur-smart`. Read AGENT_GUIDE.md, GOTCHAS.md, the DirectionalBlur ledger rows/forbidden actions, compatibility plan, and T10/F05/F06/F16 reports. MAIN, original AEX, emulator source/workers, release gates and ledger were not modified. All scratch/compiler temporary paths are under this ticket's scratch; no push/history rewrite.

**First divergent stage.** The paired probe executes the original parameter builder, typed populate/output callbacks, rotate, component-map and rowdriver instructions. Only host callbacks/imports are emulated; no rotate/rowdriver detours. It checks the stack ABI with an original prepass leaf. Original fixture final bytes equal cached Smart session bytes in all ten representatives. Original and Mac rotated planes agree exactly. Their first differing image/map stage is the component map (2–6 float words, divisor exact). The initial C02 double-round fixture also differs in two of 561 weight words, without changing its final frame. A separate native-f32 import replay (`map-c02-native-before/after.json`) matches all 561 weights and the session reference, and confirms the component map is the first differing captured stage: four words before, zero after; final bytes 2 → 0. The other nine initial witnesses have exact captured weights. Example C02: work pixel (2,3) AEX record `[2,3,1,-1]`, Mac `[2,3,3,0]`; center word at byte offset 376 is `0000803f` vs `00004040` little endian.

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


## Remaining import and oracle boundaries (no production changes)

facts:

**Neutral PF16 index84 / T10 C15.** Original AEX with the fixture's `double-round` expf import produces exactly the Mac frame, SHA-256 `6bb98821691911721b0b1908a0082239a9aa7d29ca4f565b90721ed4299ce5f6`. Cached Smart worker instead produces `7eb2b5dc8155d28a5e26d42fe923fc5715bb44bacdb6730f41cd07ed9c1fe365`: the red PF16 word at (4,18) is `c04e` vs Mac `c14e`. The fixture and Mac rotated planes and 752 Gaussian words agree with double-round expf. Keeping every AEX instruction/input/host callback fixed and changing **only** the fixture import to host float32 expf reproduces the cached worker frame exactly. The 752 input arguments are identical; eight returned float words differ. First: table index3, argument LE `5e3196b8`, double-round `4ffb7f3f`, host expf `4efb7f3f`.

**Size×Fade refusal index200 (seed1).** With the public guard bypassed only in scratch, Mac and the original double-round fixture have exactly equal rotated component inputs, maps, divisor, 22 Front weights, 80 Fade weights, rowdriver destination, denominator and alpha-max. Their final frames agree at SHA-256 `97fca2b1b95ac332d5fe0e2bff9d3d08aab5080c8ba20ecb8544de4d9213e8f4`; cached worker SHA-256 is `cc908bb5b2dc8a3bbccce8a35bacc47bae294083bcea7f3c6b25e004c4f28d33` (11 byte differences, first byte73 `31` → Mac `32`). Changing only powf to host float32 leaves all those stages/output unchanged. Changing only expf to host float32 makes the original AEX final output exactly match the worker. Of 102 expf calls, input arguments are all identical and exactly one result changes: Fade table index25 (combined call47), argument `0100e1be`, double-round `a9f6243f`, host expf `a8f6243f`. It propagates to 1459 row-output words, 381 denominator words and 54 alpha words. This directly isolates an imported-function boundary, not a final-byte issue. The fresh-seed Size×Fade mismatch remains independently unlocalized; it is not automatically assigned the same cause.

The cached worker source's `imports.rs:2648` installs `f32::exp`; the local fixture explicitly offers double-round and native-f32 imports. Static sources and the unchanged accepted `core/dblur_gaussian.h` are hash-bound in `boundary-bindings.json`. Native Windows UCRT has not been executed here. The ledger-preserved double-exp-then-float model and proven writer remain unchanged; neither dependency experiment was promoted.

**PF32 nonfinite indices109/299.** Scratch-only finite-input gate bypass, original typed callbacks and no rotate/rowdriver detours. Both original fixture outputs exactly match the cached session. Populated planes agree with Mac (0 differing words). First stage divergence is rotation: 440 / 310 float words, including AEX LE `0000c0ff` versus ARM `0000c07f`. Final differences remain 2942 / 2025 bytes. The second case also has 688 map-word differences and one divisor-word difference because unordered alpha comparisons differ. Full writer-entry planes were captured, with 1464 / 787 word differences; the production writer is not changed.

A proposed first-NaN-operand arithmetic model was tested and withdrawn. Direct execution of **original AEX** ADDSS/SUBSS/MULSS/DIVSS/MINSS instruction bytes covers 12 raw input words × 12 × 5 = **720 conditions**. The same scalar instructions compiled into a local x86_64 executable and run under macOS Rosetta match **704**, differ **16** (4 each in add/sub/mul/div, 0 in min). Example `ADDSS 7fc12345, ffc12346`: Unicorn returns `ffc12346`, x86_64 execution returns `7fc12345`. The cached Unicorn vendor code describes its default selection as x87-style: quiet NaN preference, then larger significand, positive sign tie-break. This agrees with the observed emulator boundary. It is not a native Windows proof, nor sufficient grounds to bake that emulator selection into the port. All experimental arithmetic/map/writer changes were removed; final production hashes exactly match the already-sanitized generated-Noise verification manifest.

The fixture initially sampled a PF32 writer during its own callback calibration, causing a plane-length assertion; the trace now waits for the real rowdriver/rotated stage. This was instrumentation setup, not a rendering hypothesis. No permissions were rejected. The two-refuted-hypotheses/no-new-boundary stop condition was not reached: the expf experiment captured exact new return words, and the NaN model test captured an independent instruction-level counterexample.

inference:
- The remaining neutral mismatch and the measured Size×Fade rejection depend on the reference host's expf implementation. Switching a proven Gaussian contract solely to satisfy that host would not establish Windows compatibility.
- The nonfinite residual mixes actual port semantic differences (NaN sign, unordered map/writer behavior) with an oracle-specific NaN-selection boundary. Broad admission cannot be justified without separating those contracts. Production refusal is retained.
- The requested bounded reduction is complete: more than three existing signature clusters closed (C02/C03/C08/C09/C10/C11/C12/C13/C14/C18) through a single general cause, and a separately committed admission expansion. Shared-cause signatures were committed together rather than splitting one operation into artificial case-specific changes. This is not an all-input or native AE-exact completion claim.

changed_files (final evidence commit):
- tools/emulation/probe_directionalblur_c02_stages.py — populated/rowdriver/writer stage capture and scratch-only nonfinite bypass
- tools/emulation/probe_directionalblur_c02_sse.py — independent original-instruction vs x86_64 boundary probe
- reports/fuzz/c02_dblur_smart/{neutral-double,neutral-native,sizefade-double,sizefade-nativepow,sizefade-nativeexp,nonfinite-boundary,sse-oracle-boundary,boundary-bindings}.json
- orchestra/reports/C02-dblur-smart.md

verify (dependency boundaries, same S/W/P environment as above):

```sh
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/neutral-double-recheck.json" --clusters 15 --allow-fixture-difference > "$S/neutral-double-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/neutral-native-recheck.json" --clusters 15 --expf-leaf native-f32 > "$S/neutral-native-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/sizefade-double-recheck.json" --indices 200 --gate-off --allow-fixture-difference > "$S/sizefade-double-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/sizefade-native-recheck.json" --indices 200 --gate-off --expf-leaf native-f32 > "$S/sizefade-native-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --worker "$W" --report "$S/nonfinite-recheck.json" --indices 109 299 --nonfinite-off > "$S/nonfinite-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_sse.py --report "$S/sse-boundary-recheck.json" > "$S/sse-boundary-recheck.log" 2>&1
```

Expected: neutral fixture/session 1 byte different with double-round, 0 with native-f32 (8 table words changed); Size×Fade fixture/session 11 bytes different with double-round, 0 with native-f32 (1 table word changed); nonfinite fixture/session both exact but Mac bypass mismatches 2942/2025 bytes; SSE probe 720 complete, 704 equal / 16 different. `--allow-fixture-difference` records this intentional reference disagreement rather than treating it as success against the session.

**Final acceptance:** Smart seed1 **262 exact / 1 mismatch / 35 refusal / 2 uncompared**, +27 exact over the starting revision, zero base-exact changes. Fresh seed2 **269 / 1 / 28 / 2**, +26 exact. Corpus **54 exact / 2 mismatch**, 17 Smart improvements and 39 unchanged, replay 56/56. Two production commits each have 656 O2/sanitizer cases. No release gate/ledger/other-plugin/MAIN changes, no push or worker rebuild.

next:
- Follow-up: reconcile the reference expf import with existing accepted Gaussian evidence for the newly observed arguments, preserving previously accepted proofs; isolate fresh-seed Size×Fade index152 separately.
- Follow-up: establish the intended PF32 NaN opcode/host contract independently of Unicorn's x87-style selection, then re-open nonfinite admission with paired stages.
- Negative Noise Offset remains the previously proven native out-of-allocation-read boundary; no wrap/clamp emulation was added.
- Two budget cases in each campaign remain uncompared. Larger instruction/time budgets are a separate coverage follow-up, not exact evidence here.


Final review checks: `acceptance.json` composes the two production transitions and verifies all 235 original exact hashes, all 17 corpus improvements, final 56/56 replay, and exact current production hashes against the sanitizer manifest. The latest stage tool also rechecked C02/C03/C08; their rotated planes/maps/final bytes remain exact. C02's separate native-f32 replay aligns all 561 weights and removes the initial fixture-import confound. No incompatible numerical candidate remains in production. These final replay/stage/acceptance JSON files are also part of the evidence commit.
Final scratch after removing regenerable corpora/builds: **12,093,034 bytes**, below 5 GiB. Temporary build contexts removed their binaries automatically.
