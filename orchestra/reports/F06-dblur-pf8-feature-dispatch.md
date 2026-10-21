status: done

summary:
- Replaced the legacy PF8 approximation/input-copy fallback with bounded binary-grounded dispatch or an explicit refusal.
- C04/C05/C06/C07/C16/C17 are exact on Classic and Smart; paired AEX/core writer-entry float words are exact for all six.
- Saved corpus: 37 mismatches become exact, 19 results unchanged; updated corpus replay is 56/56 matches_saved.
- Seed 1 / 300: each route improves 228 -> 235 exact; eight improve, one formerly exact input now refuses, and 25 formerly mismatching inputs now refuse.
- Production O2/sanitizer equality: 300 campaign + 56 corpus cases, both routes; seven selected existing tests pass, including 684 live O2/sanitized renders.

facts:

Branch `orch/F06-dblur-pf8-feature-dispatch`; starting commit `a253fd15011c970469a24ff201e262d8ca875fbc`. Read the shared guide, DirectionalBlur ledger row (including forbidden actions), emulation gotchas, compatibility-plan classification rules, and T10. MAIN, original AEX, cached workers, emulator source, release gates and forbidden-action lists were not modified. No push or history rewrite. Final scratch after removing regenerable campaign corpora: 4258092 bytes; temporary build directories were automatically removed. All temporary files and compiler TMPDIRs were inside this ticket's scratch directory.

**Cause and binary boundary.** Original PF8 owner `0x180004a20` copies the input at `0x180004abb`, scales the four counts, then tests Front Strength, Back Strength, Front Fade, Back Fade at `0x180004b50..0x180004b5f`. Any nonzero count enters work at `0x180004b69`; only all four zero return the copied input. The decompilation of `FUN_180004a20` agrees. Sources read by absolute path: MAIN `disasm/OLMDirectionalBlur.aex.asm.txt` and `decomp/OLMDirectionalBlur.aex.c.txt`.

The old Mac `CanUseExact8` and `render_rgba8` required an active Strength. Five representatives have only Fade active, so they reached `RenderDirectional8`'s copy. C07 was excluded by the Size/Back Sharp cross predicate and reached the same copy. The new core work predicate includes Fade. The fallback reuses the existing rotate, component-map, rowdriver, normalization and PF8 writer; no arithmetic, pixel correction, lookup, or expected-value patch was added. The now-unreachable approximation and its private helpers were removed. PF8 all-four-zero copies use the same validated-world path as deep copies.

**Admission.** Existing retained and `CanUseExact8` routes keep precedence. The new fallback requires unit scale, valid controls/worlds, no Noise, and excludes Size x Fade. It uses the existing checked float-workspace/feature budget (conservative PF16 wrapper estimate; the preliminary world check also overcounts PF8 wrapper storage). Smart includes atomic staging bytes and the full-frame/origin policy before allocation. Existing Layer and generated-Noise routes are not expanded. Unsupported fallback inputs now return error 516, rather than successful copied/approximated pixels.

**Intermediate trace.** `probe_directionalblur_pf8_dispatch_trace.py` drives the real AEX parameter builder and unchanged render worker with original populate/output callbacks and no rotate/rowdriver detours. A sentinel-filled transparent prepass at RVA `0x1000` checks stack arguments 5/6 before the witness. Hooks record both the work predicate and taken work entry, then the exact float32 RGBA at writer `0x6b30`. Scratch-only instrumentation records the corresponding core float words before quantization. All six paired words and all three final byte sources (Python AEX trace, cached session AEX, Mac public Classic) agree. Both public routes separately agree in corpus replay. The fixture's large-image component diagnostic coordinates are replaced with in-bounds diagnostic coordinates only; rendering is unchanged. Fixed getter truncation is respected for the trace controls; all six have angle zero and Noise disabled.

| Cluster | Actual counts [Front, Front Fade, Back, Back Fade] | Old first differing byte: AEX -> Mac | Old differing bytes | New ARGB8 hex | Paired float32 RGBA LE hex |
|---|---|---|---:|---|---|
| C04 | `[0, 0, 0, 29]` | offset 0: `69` -> `d2` | 1 | `69205aec` | `8180003eb5b4b43eedec6c3f3863d33e` |
| C05 | `[0, 0, 0, 35]` | offset 1: `00` -> `a0` | 3 | `00000000` | `00000000000000000000000000000000` |
| C06 | `[0, 0, 0, 23]` | offset 1: `00` -> `ff` | 1 | `00000000` | `00000000000000000000000000000000` |
| C07 | `[0, 0, 909, 0]` | offset 1: `00` -> `ff` | 2 | `00000000` | `00000000000000000000000000000000` |
| C16 | `[0, 52, 0, 0]` | offset 0: `55` -> `ff` | 1 | `55a442c5` | `a5a4243f8584843ec6c5453fd823ab3e` |
| C17 | `[0, 3, 0, 0]` | offset 1: `00` -> `ff` | 2 | `00000000` | `00000000000000000000000000000000` |

**Gate-off experiment.** A scratch source copy replaces only the legacy fallback with `RenderExact8` for active feature shapes and includes Fade in the core predicate. The committed runner always obtains these two pre-fix sources from the starting commit, rather than depending on mutable MAIN. Production files are not changed by the experiment. All 37 saved target-cluster cases become exact; the other 19 remain byte-identical. For the unshrunk 300 cases, the blanket bypass changes 25 mismatches to exact, leaves 27 mismatches, and changes four mismatches to core refusal. Four changed-but-still-mismatching outputs disprove blanket admission:

| Seed-1 index | Different bytes after blanket bypass | First byte AEX -> scratch | Boundary |
|---|---:|---|---|
| 102 | 1 | offset 297: `ff` -> `c8` | Size + Back Sharp + generated Noise |
| 152 | 22 | offset 81: `a8` -> `a9` | Size + Back Fade |
| 168 | 36 | offset 0: `3a` -> `00` | Size + Back Fade |
| 200 | 11 | offset 73: `31` -> `32` | Size + Front Fade |

Indices 167/183/222/246 reach core refusal under the blanket bypass. Those boundaries are excluded from the new fallback. Every changed, newly rendered output admitted by production is exact in the tested campaign/corpus. Gate-off and production O2/ASan/UBSan pairs agree on all 300 campaign cases and 56 corpus cases, on both routes; no sanitizer diagnostics/crashes were observed (`-fsanitize=address,undefined -fno-sanitize-recover=all`, leak detection disabled). Only the blanket hypothesis was refuted, with new concrete byte boundaries; the two-hypothesis/no-new-boundary stop rule was not triggered.

**Required campaign, before/after per route.** Both `run.py` campaigns exited 0, n=300, seed=1, jobs=2, scratch corpus, shrink-attempts=0. Each has AEX 298 ok / 2 budget (indices 274/289), no reject; all completed oracle result dictionaries agree before/after. The baseline includes F05 deep-dispatch work already present in this worktree and therefore differs from T10's historical 115-exact baseline.

| Route | Exact before -> after | Mismatch before -> after | Refusal before -> after | Uncompared before -> after |
|---|---:|---:|---:|---:|
| Classic | 228 -> 235 | 56 -> 23 | 14 -> 40 | 2 -> 2 |
| Smart | 228 -> 235 | 56 -> 23 | 14 -> 40 | 2 -> 2 |

Per route: 227 exact results remain exact; indices 35/110/112/159/176/221/236/292 become exact; 23 mismatch outputs are unchanged; 25 mismatches become refusal; the existing 14 refusals remain; two oracle budgets remain uncompared. **One previously exact case becomes refusal:** index 145, 1x1, Size20 + FrontSharp25 + Back17 + BackSharp40 + Noise33 (materialized fixed getters), now outside the generated-Noise fallback. Old copied bytes happen to match AEX SHA-256 `4d40845b0c45343db56b329169828118e861a39cc5c445f7d2147aac7bf0e3f4`; the blanket core bypass also matches for this one input, but index102 disproves general admission of that family. No dimension/coordinate/source exception was added to preserve this accidental exact input. The ticket's aggregate exact-count requirement passes; this specific refusal regression remains explicit.

**Corpus update table.** Every row below changes mismatch -> exact on both routes; `ΔB` is before -> after. All 37 inputs, parameters, reduction histories and original provenance remain intact; only observed results and a revalidation/provenance annotation were updated. Full hashes, oracle dictionaries and before/after route metadata are in `corpus.json`. The other 19 files are unchanged. Replay after update exited 0, 56/56 `matches_saved`.

| Corpus file under tests/fuzz_corpus/olmdirectionalblur | ΔB | Old Mac hash prefix -> new Mac/AEX hash prefix |
|---|---:|---|
| `seed1_case000000_0ff79f8bee87.json` | 1 -> 0 | `e890f350f4385cfe` -> `df3f619804a92fdb` |
| `seed1_case000035_0f4b356bb556.json` | 2 -> 0 | `10db5223d19bd1d5` -> `df3f619804a92fdb` |
| `seed1_case000045_733fd829658d.json` | 3 -> 0 | `c4f6c1908f679071` -> `df3f619804a92fdb` |
| `seed1_case000048_876ee866f02e.json` | 1 -> 0 | `6ab1a483810edcda` -> `213a382ab3261215` |
| `seed1_case000056_0f4b356bb556.json` | 3 -> 0 | `9e83509b5f2891c3` -> `df3f619804a92fdb` |
| `seed1_case000058_0f4b356bb556.json` | 1 -> 0 | `bf4571113cd8c226` -> `df3f619804a92fdb` |
| `seed1_case000061_876ee866f02e.json` | 1 -> 0 | `2344380cc9f3d30a` -> `abffa8fba7d23ecb` |
| `seed1_case000067_876ee866f02e.json` | 1 -> 0 | `b05a236f47b97b93` -> `435bd4833aceb674` |
| `seed1_case000073_0f4b356bb556.json` | 1 -> 0 | `e890f350f4385cfe` -> `df3f619804a92fdb` |
| `seed1_case000077_733fd829658d.json` | 1 -> 0 | `9e65d40a65320894` -> `e785726888158b5b` |
| `seed1_case000078_0f4b356bb556.json` | 1 -> 0 | `e890f350f4385cfe` -> `df3f619804a92fdb` |
| `seed1_case000088_0ff79f8bee87.json` | 3 -> 0 | `9e83509b5f2891c3` -> `df3f619804a92fdb` |
| `seed1_case000102_eec7cb1faf25.json` | 2 -> 0 | `7a7bf454c5f3cb1b` -> `df3f619804a92fdb` |
| `seed1_case000110_0ff79f8bee87.json` | 1 -> 0 | `5fc1f3b5dfc3af9f` -> `dea48ca587d32d51` |
| `seed1_case000112_0ff79f8bee87.json` | 2 -> 0 | `7a7bf454c5f3cb1b` -> `df3f619804a92fdb` |
| `seed1_case000118_0ff79f8bee87.json` | 1 -> 0 | `81ff65efc4487853` -> `60f2e332c71bcda8` |
| `seed1_case000131_0f4b356bb556.json` | 3 -> 0 | `9e83509b5f2891c3` -> `df3f619804a92fdb` |
| `seed1_case000139_0f4b356bb556.json` | 1 -> 0 | `08efea1c0957a5a1` -> `dbe589edce1e47df` |
| `seed1_case000152_0ff79f8bee87.json` | 1 -> 0 | `5fc1f3b5dfc3af9f` -> `ccf0957f690d66a2` |
| `seed1_case000159_0ff79f8bee87.json` | 1 -> 0 | `08efea1c0957a5a1` -> `dbe589edce1e47df` |
| `seed1_case000160_0ff79f8bee87.json` | 1 -> 0 | `f7f9e13d8ace3958` -> `d6770775d4bc2809` |
| `seed1_case000163_0ff79f8bee87.json` | 1 -> 0 | `34aaa746c25a0f10` -> `a1adb0deb29afcc9` |
| `seed1_case000167_876ee866f02e.json` | 1 -> 0 | `8944c5b1cbe0e6a7` -> `1cd9eadb73619f1c` |
| `seed1_case000168_0ff79f8bee87.json` | 1 -> 0 | `e890f350f4385cfe` -> `df3f619804a92fdb` |
| `seed1_case000169_0ff79f8bee87.json` | 3 -> 0 | `9e83509b5f2891c3` -> `df3f619804a92fdb` |
| `seed1_case000174_876ee866f02e.json` | 1 -> 0 | `306b504615172186` -> `c47ec719bd179507` |
| `seed1_case000175_0ff79f8bee87.json` | 1 -> 0 | `81ff65efc4487853` -> `96416924980729fa` |
| `seed1_case000176_0f4b356bb556.json` | 1 -> 0 | `3554726ba0f5404f` -> `646871356e43639e` |
| `seed1_case000183_c38294d58dcf.json` | 1 -> 0 | `d445b3a5ffb84150` -> `25298323c900c4b2` |
| `seed1_case000200_0f4b356bb556.json` | 1 -> 0 | `e3820096cb82366b` -> `df3f619804a92fdb` |
| `seed1_case000221_0ff79f8bee87.json` | 2 -> 0 | `b7d1b3a1104cc86b` -> `df3f619804a92fdb` |
| `seed1_case000222_733fd829658d.json` | 1 -> 0 | `a6d54d35020607cb` -> `0643db80b51cf9fb` |
| `seed1_case000226_0f4b356bb556.json` | 1 -> 0 | `e3820096cb82366b` -> `df3f619804a92fdb` |
| `seed1_case000241_0ff79f8bee87.json` | 1 -> 0 | `e3820096cb82366b` -> `df3f619804a92fdb` |
| `seed1_case000246_876ee866f02e.json` | 1 -> 0 | `2c3c3d1304b7c932` -> `a80d5e2049d99a8d` |
| `seed1_case000248_876ee866f02e.json` | 1 -> 0 | `cadd7538cdefdaac` -> `87b18399311fdf9c` |
| `seed1_case000292_0ff79f8bee87.json` | 3 -> 0 | `9e83509b5f2891c3` -> `df3f619804a92fdb` |

**Existing tests.** Five fast tests passed in `tests-fast.log`: checked general-feature budget plus four Type-3 owner-boundary evidence tests (generator pin, exact rows, row tamper, claim tamper). Two live tests passed in `tests-live.log`: `test_directionalblur_general_input_owner_20261001` replays 162 retained cases at O2 and ASan/UBSan; `test_directionalblur_general_features_20261001` replays 180 cases at both builds, total 684 renders. SDK include directories were read by absolute path from MAIN; the compiled plugin/core were from this worktree.

An additional attempt to run the whole `test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812` suite failed (11 tests, 19 error events including subtests): its historical identity validator requires the absent `/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker`. This was an unavailable prerequisite, not a measured render regression. No worker was rebuilt, substituted into that pinned proof, or copied. The selected fast/live subset above passes.

**Evidence/provenance.** JSON artifacts are in `reports/fuzz/f06_dblur_pf8_dispatch/`. `gate_off` means the tested candidate in the shared probe schema; `production: true` distinguishes production results from the blanket scratch experiment. Scratch-baseline builds are bound by `baseline_ref` and explicit baseline source/core hashes; their general dependency manifest also records current workspace files, so the explicit baseline bindings take precedence for those two replaced files. The cached worker was used by absolute path from INDEX.json, without rebuilding. Full raw input/parameter generation is reproducible from the recorded seed and corpus.

| Artifact | SHA-256 |
|---|---|
| `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp` | `e02a2973a032a77c861a0c86bb8043da6a72f2820141b7a950460c436f9c9156` |
| `core/dblur_frontonly.cpp` | `82cf90b237ec0ea9e76dfb47f1fa4b80d2940e8d05b990fefab5a03a527df651` |
| `reports/fuzz/f06_dblur_pf8_dispatch/after.json` | `a9ebf24ac23534a69042670aed5c3dce896a358dcc3cd136b9d8f4350dec2d5d` |
| `reports/fuzz/f06_dblur_pf8_dispatch/before.json` | `f3ecfa8644ce64f3cd5fea5f68de2319394ebf8ac7951d8241423ddefe71277c` |
| `reports/fuzz/f06_dblur_pf8_dispatch/corpus.json` | `890ceab8506376e7f7340a00da96ee0f602f1cafa1cd200c669ed241ceef8858` |
| `reports/fuzz/f06_dblur_pf8_dispatch/gate_campaign.json` | `e7367dd66e00135ad536d1df3508fd8125284855d5bb7bbd4c809f46b58cb8ac` |
| `reports/fuzz/f06_dblur_pf8_dispatch/production_campaign.json` | `20424a652cd9444a693a1efb5bc4dc1af169687b3dbe8ebaaf8bef4a563b43ca` |
| `reports/fuzz/f06_dblur_pf8_dispatch/replay.json` | `d6c9a2b879dbc9e760cd66be09e81df167b4fd8b0e80e668f6c26677be7a5069` |
| `reports/fuzz/f06_dblur_pf8_dispatch/trace.json` | `64cc1c79fbb43b01ee5a0174f6fabda2bfb6c0a1b1e341cf6de0703656349d68` |

Original AEX SHA-256: `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`. Cached worker SHA-256: `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c`. Build paths and binary hashes are retained in each JSON. Probe assertions/provenance reporting were tightened after initial captures; reproduction uses the committed runner and pinned baseline, with identical candidate transformations. Production source/core hashes match the campaign manifest.

inference:
- The six target counterexamples are dispatch bugs: the AEX executes its feature pipeline while the old Mac bypassed it. Identical pre-writer words after routing through the existing core support that cause without changing the proven writer.
- Size x Fade and generated-Noise fallback combinations still need separate intermediate investigations. Remaining discrepancies are not established Windows dependency/host/comparator issues.
- Refusal is an explicit unimplemented boundary, not exact rendering. No native AE/Windows UCRT equivalence or all-input compatibility is claimed. This evidence covers CPU AEX emulation versus the SDK fake host, packed AEX input versus padded Mac rows, origin 0, full frame, scale 1, time 0/24, no independent Layer.

changed_files:
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`: remove legacy renderer, bounded feature fallback, PF8 no-work predicate, Smart budget/frame integration.
- `core/dblur_frontonly.cpp`: include Fade in PF8 work admission.
- `tools/fuzz/probe_directionalblur_pf8_dispatch.py`: pinned-baseline scratch gate experiment, production comparison and sanitizers.
- `tools/emulation/probe_directionalblur_pf8_dispatch_trace.py`: original AEX and scratch-core branch/writer trace.
- `tools/fuzz/verify_directionalblur_pf8_dispatch.py`: compact evidence/corpus/production-binding checks.
- `reports/fuzz/f06_dblur_pf8_dispatch/{before,after,gate_campaign,production_campaign,corpus,trace,replay}.json`: actual measurements.
- The 37 corpus files explicitly listed in the table above.
- `orchestra/reports/F06-dblur-pf8-feature-dispatch.md`: this report.

verify:

Run in this worktree. Commands below redirect long output into the ticket scratch. No install, push, MAIN write or worker rebuild is needed.

```sh
S="$PWD/orchestra/state/F06-dblur-pf8-feature-dispatch"
W=/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/verify_directionalblur_pf8_dispatch.py
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2 --scratch "$S" --worker "$W" --report "$S/after-recheck.json" --corpus "$S/corpus-recheck" --shrink-attempts 0 > "$S/after-recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 2 --replay tests/fuzz_corpus/olmdirectionalblur --scratch "$S" --worker "$W" --report "$S/replay-recheck.json" --corpus "$S/replay-unused" > "$S/replay-recheck.log" 2>&1
python3 tools/fuzz/probe_directionalblur_pf8_dispatch.py --production --worker "$W" --report "$S/corpus-recheck.json" > "$S/corpus-recheck.log" 2>&1
python3 tools/fuzz/probe_directionalblur_pf8_dispatch.py --production --campaign --worker "$W" --report "$S/production-campaign-recheck.json" > "$S/production-campaign-recheck.log" 2>&1
python3 tools/fuzz/probe_directionalblur_pf8_dispatch.py --campaign --worker "$W" --report "$S/gate-campaign-recheck.json" > "$S/gate-campaign-recheck.log" 2>&1
"$P" tools/emulation/probe_directionalblur_pf8_dispatch_trace.py --worker "$W" --report "$S/trace-recheck.json" > "$S/trace-recheck.log" 2>&1
export PYTHONPATH=tests
export CPLUS_INCLUDE_PATH='/Users/onmk/Documents/Projects/Personal/OLM as/Headers:/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP:/Users/onmk/Documents/Projects/Personal/OLM as/Util:/Users/onmk/Documents/Projects/Personal/OLM as/Resources'
"$P" -m unittest test_directionalblur_general_input_owner_20261001 test_directionalblur_general_features_20261001 > "$S/tests-live-recheck.log" 2>&1
"$P" -m unittest test_directionalblur_general_feature_budget_20261001 test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_generator_is_externally_pinned test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_exact_rows test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_recanonicalized_row_tamper_rejected test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_claim_tamper_rejected > "$S/tests-fast-recheck.log" 2>&1
git diff --check
```

Expected: all commands exit 0. Current campaign 235 exact / 23 mismatch / 40 refusal / 2 uncompared per route; saved replay 56/56; corpus comparison 37 improved / 19 unchanged; sanitizer equality 56/56 and 300/300; trace 6 paired writer/final matches; seven selected tests pass. Original timeout classifications may vary with machine load; budgets are never counted as exact. The `--production --campaign` probe reconstructs the 228-exact baseline from the pinned commit while compiling production separately. Its aggregate exact assertion implements the ticket requirement and does not conceal index145's refusal.

next:
- Separate tickets for Size x Fade PF8 residuals (indices152/168/200) and generated-Noise PF8 combinations (index102 residual;167/183/222/246 core failures), with stage traces and noise-table bounds before admission expansion.
- Include index145's formerly exact 1x1 Noise case when the generated-Noise fallback is grounded; do not restore a special copy exception.
- Preserve the existing C01/C12 PF8 numerical-residual investigation and other plugins/depth work outside this ticket.
- Restore the historical Type-2 worker prerequisite separately if that old identity-validation suite is required.
