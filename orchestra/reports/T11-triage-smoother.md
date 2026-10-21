status: done

summary:
- Added optional refusal attribution only; production admission, rendering, and flags are unchanged. Corpus replay remains 29/29 `matches_saved`.
- All 95 Classic refusals are unsupported PF32 inputs; zero guards refused an oracle-renderable case. The other 114 oracle rejects are a PF16 emulator callback limitation.
- Scratch-only gate removal finds no valid PF32 fall-through: both gates removed gives 95 uncompared outputs and 95/95 sanitizer failures.
- Both PF8 clusters expose an oracle/host disagreement: a second original-AEX Classic harness matches Mac on all 29 retained cases, while the frozen worker differs on all 29.
- Recorded byte statistics, an equal classifier boundary, a separate pre-existing UBSan defect, and four proposed follow-up tickets; no numerical fix or reference rebaseline.

facts:

Base: `97ed4fd0b38b3d2abf509346546eb5a99df306e1`, branch `orch/T11-triage-smoother`. The worktree initially contained the uncommitted source/adapter tracing, two diagnostic scripts, a census, and scratch evidence. Those were reviewed, the scripts corrected, and the evidence below freshly rerun. Historical scratch results are not substituted for the fresh committed JSONs.

Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the OLMSmoother v1 decision-matrix row in `notes/CONFORMANCE_LEDGER.md`, the plan's classification table, T04's olmsmoother entries, and T03. F17, F18, and T05 were absent from this branch and read from MAIN's HEAD without modifying it. F17/F18 establish original **Classic** as this plugin's compatibility owner; the Mac Smart wrapper is diagnostic only. This branch predates their framework/flag changes; no shared framework or capability changes were imported into T11. Both wrappers already compare with original Classic in this adapter, so the route correction does not change the Smoother v1 comparisons.

**Fresh census and generator audit.** The exact commands are in `verify` below. The seed-1, n-300, jobs-2 campaign completed with:

| Depth | Cases | Original worker outcome | Mac Classic outcome | Interpretation of the rejection |
|---|---:|---|---|---|
| PF8 | 91 | 91 successful | 62 exact, 29 mismatch | Numerical comparisons available |
| PF16 | 114 | 114 reject | 114 successful but uncompared | `legacy new-world requested unsupported DEEP_PIXELS` |
| PF32 | 95 | 95 reject | 95 refusal | `AEX did not advertise support for argb32f pixel depth` |

There are no oracle budgets or candidate crashes in this production census. The manually driven Smart wrapper has identical verdict counts and output hashes. All 300 input hashes and all 300 paired Mac result dictionaries equal T04's baseline. Original PF8 output/status records and PF16 rejection records agree as well; PF32's diagnostic wording changed with the indexed worker, so full result dictionaries agree on 205/300, not 300/300.

All 900 generated control values satisfy the captured declarations: Use Color Key integer 0–1, Color Key four integer bytes 0–255, Do Smooth Range integer 0–255. There are **zero parameter-range violations**. Original F18 flags advertise deep color but neither native float nor Smart. Thus sampling PF32 is useful rejection coverage, but those 95 rows are not legal native render cases or lost Mac functionality. PF16 is advertised; its 114 failures originate in the emulator callback, not an out-of-range slider. Read-only source inspection finds that error in `AEXCompat/guest/crates/aex-guest-worker/src/x64/iterate_and_suites.rs`, `emulate_new_world_common`: the legacy allocator stops on `flags & 0x2`. The observed cached-worker error is the runtime evidence; current emulator source is supporting inspection, not a claim that it is the cached worker's exact source revision.

**Refusal ranking (AE-target Classic counts; Smart is separate).** “Legal comparable” means the original actually returned pixels. Supported PF16 cases remain unverified rather than being counted as exact or rejected by the plugin.

| Rank | Guard | Classic refused | Legal comparable refused | Diagnostic Smart refused | Depth / error |
|---|---|---:|---:|---:|---|
| 1 | `ValidatePublicWorlds:world-depth-32-unsupported` | 95 | **0** | 95 | PF32 / shim error 25 |
| — | All other instrumented guards | 0 | 0 | 0 | Not reached as refusals |
| — | Unattributed refusals | 0 | 0 | 0 | 100% attribution of observed refusals |

The ranking contains no rejected legal render cases. In particular, `classic-admission` does not reject PF8/PF16 in this campaign: `V1ClassicAdmission` already admits both depths generally. It is a secondary PF32 stop, exposed only by the scratch experiment below. Error 25 is the shim's existing nonzero refusal constant, not a new native AE error definition.

`SmootherRefusal` mirrors the RadialBlur pattern: on refusal, append `function:tag@line` to `$OLM_REFUSAL_TRACE` when set, then return the original error. Compound validation is split in the same short-circuit order to distinguish causes. The adapter collects a per-route trace outside the compared result. No trace path is installed globally and no output bytes are adjusted.

**Neutrality.** Fresh default-build corpus replay is **29/29 `matches_saved`**. The triage runner also compares tracing enabled versus unset on all 300 generated cases, both wrappers: **600/600 identical status/metadata/raw-output comparisons**. An unwritable trace path leaves **10/10** additional wrapper comparisons unchanged. This proves the measured corpus/campaign behavior, not every native AE path. Existing corpus records were only read; campaign shrinking used a ticket-local scratch corpus.

**Scratch gate-off experiment.** `triage_olmsmoother.py` makes a temporary source copy and adds `OLM_SMOOTHER_TRIAGE_WORLD32_OFF` / `OLM_SMOOTHER_TRIAGE_ADMISSION32_OFF` preprocessor switches there. Neither switch exists in production source. The second switch extends the admission predicate solely to inspect the downstream path. Every row below uses the same 95 baseline-refused inputs; Classic is the AE target. The diagnostic Smart wrapper gives the same counts independently.

| Scratch switches | Cases | Unblocked outputs | Exact | Mismatch | Uncompared | Still refused | Unsanitized crash | Sanitizer errors in corresponding sanitized run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| World-depth guard off | 95 | 0 | 0 | 0 | 0 | 95 (`classic-admission`) | 0 | 0 |
| Admission PF32 off, world guard retained | 95 | 0 | 0 | 0 | 0 | 95 (`world-depth-32-unsupported`) | 0 | 0 |
| Both off | 95 | 95 | 0 | 0 | 95 | 0 | 0 | **95** |

Both-off ASan reports are heap-buffer-overflow and terminate the candidate (`returncode=-6`); they are counted as sanitizer failures, not an additional 95 independent crash cases. There is no PF32 reference, so the 95 unsanitized outputs cannot be called correct. Source inspection explains the unsafe fall-through: `Render`'s staging pixel size is 4 for PF8 and 8 otherwise, while `DispatchRender`'s remaining branch uses 16-byte `PF_PixelFloat`. Removing the two guards does not create a valid PF32 implementation. No promotion is proposed.

**PF8 clusters and smallest retained shrunk cases.** Selection minimizes payload size, then nondefault controls, then path among each baseline cluster's saved corpus. Signature population counts refer to the original 300-case campaign, not a claim of distinct root causes. Both representatives have key disabled and white key color. Statistics below compare frozen-worker expected bytes with Mac Classic; Smart produces identical bytes. Coordinates are zero-based, channels are memory-order ARGB.

| Cluster / population | Smallest retained case | First differing byte and pixel | Byte diff / maximum absolute diff | Channels and spatial pattern | Plan classification |
|---|---|---|---|---|---|
| `["raw-output",[3],8]` / 6 | `seed1_case000000_eaba52d5eacc.json`, 1×19, tolerance 170 | Byte 64, A at (0,16), worker `41`, Mac `00` | 4 of 76 bytes / 130 | A,R,G,B each once; one pixel at row 16; Mac pixel equals input | **Comparator/reference boundary, provisional**; underlying host difference unexplained |
| `["raw-output",[],8]` / 23 | `seed1_case000006_92552f06afe6.json`, 1×3, tolerance 6 | Byte 0, A at (0,0), worker `c6`, Mac `ce` | 4 of 12 bytes / 20 | A,R,G,B each once; one top-edge pixel; worker pixel equals input | **Comparator/reference boundary, provisional**; underlying host difference unexplained |

Packing away Mac input/output padding leaves both representatives unchanged. This is a measured layout control, not proof that the worker and Mac fake hosts are equivalent in every field.

The existing Mac `[cls8]` trace was paired with direct original `Classifier8` at `0x180008060`, using the same per-pixel 3×3 neighborhood and raw tolerance. All **22 pixels × four directions = 88 classifier results agree**. At the first differing output pixel the four results (directions 5,3,1,7) are respectively `(0,0,0,0)` and `(0,0,0,4)`. Equal center classifiers do not exclude neighboring interpolation writes. This is a matched intermediate boundary, **not the first differing stage of the frozen worker**: the worker adapter exposes final bytes only, and the direct leaf comparison does not capture its natural caller state.

To avoid misclassifying that equality as a downstream port defect, a second original exported `PF_Cmd_RENDER` execution reused the existing `test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810.actual` harness. Only its AEX path, geometry, key RGB, payload, and tolerance were rebound; its serial guest iterator and host copy/allocation behavior were unchanged. All **29/29** retained PF8 cases match Mac exactly under that original-AEX host; **0/29** match the frozen worker (126 differing bytes in aggregate). The two representative hashes are:

| Case | Frozen worker SHA256 | Mac = second original-AEX host SHA256 |
|---|---|---|
| 1×19 | `f08a7d4dc586eee162a6bc89d8a3a7e8b9762628c8ee9b9166ae9e051d90d39a` | `e4f44ecd351477f9861716f65c27796d24403ed225a363f1f6e4db89d880db3c` |
| 1×3 | `71a368f23d17753295e7423d46a50325de390846956a8d24fbc40e387ac0cb6f` | `490b976bf36201c4ba4731b7550a741f9974a17354ddee7f9eca79860da1a998` |

The second host hand-materializes parameter unions and uses zero-initialized InData; it is a diagnostic comparison, not a replacement production oracle or native AE proof. No first differing internal stage between these two hosts was captured. Final output is the first *available* differing observation. The committed generic triage JSON therefore retains its earlier `unexplained` classification; this report adds the cross-host evidence from the separate classifier/owner JSON. Neither cluster is asserted to be a proven arithmetic bug or a Windows-library difference.

**Separate sanitizer defect.** Both representatives fail the production-control ASan/UBSan build, on both wrappers, before a sanitizer output can be compared: `Classifier8TailMemory::read32`, production source line 1358, reports `index 123145302311056 out of bounds for type const uint8_t[384]`. The expression is `stack+a-kStack`: the left-associative intermediate pointer addition uses the synthetic absolute address before subtraction. Related read/write expressions should be audited together. This is a concrete C++ port defect, independent of the unresolved numerical oracle disagreement; no causal link to the 29 mismatches was proved.

Provenance: original AEX SHA256 `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82`; indexed worker `/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker`, SHA256 `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`; traced production source SHA256 `90bec42cbcfc859d4d27756979679d39c71ea89b6151c3142177289f19d430c7`; candidate SHA256 `5b0b45966efad9daf67dd26b125608d1b4be74e3f03a9115c439801f681c20a7`. The reports bind build commands, source/declaration/helper hashes, corpus paths, and outcomes. Mach-O build hashes need not remain identical after unrelated future changes.

inference:

- PF32 guard removal is not a compatibility fix. The original does not advertise the route, and the forced Mac path is unsafe. Keep those refusals.
- The meaningful missing coverage is the 114 advertised PF16 cases blocked by a host callback. Repairing that oracle boundary may reveal new residuals; successful Mac execution is not evidence of exactness.
- The 29 retained PF8 mismatches should first be investigated as an oracle/host-state disagreement. Two original-code hosts disagree, while one matches Mac; that is stronger evidence than the initial one-pixel copy/interpolation pattern. It does not establish which host models Windows AE correctly.
- Classifier equality and the second public-owner equality provide new boundaries. No series of two refuted numerical hypotheses without a new boundary was pursued. This ticket closes the triage deliverable, not full compatibility.

changed_files:
- `mac/OLMSmoother/Mac/OLMSmoother_port.cpp` — refusal tracing only.
- `tools/fuzz/adapters/olmsmoother.py` — optional trace attribution outside compared results.
- `tools/fuzz/triage_olmsmoother.py` — range/census analysis, neutrality, scratch compile-time gates, sanitizer controls, byte statistics.
- `tools/fuzz/compare_olmsmoother_classifier8.py` — paired classifier and independent original-owner diagnostics.
- `reports/fuzz/olmsmoother_refusals_20261022.json`
- `reports/fuzz/olmsmoother_triage_20261022.json`
- `reports/fuzz/olmsmoother_classifier8_20261022.json`
- `reports/fuzz/olmsmoother_t11_replay_20261022.json`
- `orchestra/reports/T11-triage-smoother.md`

verify:

Run from this worktree; all fuzz/triage commands explicitly cap jobs at 2. Reports below go to scratch to preserve the committed evidence. The indexed worker and MAIN venv/AEX are used by absolute path and are not rebuilt or copied.

```sh
set -e
s="$PWD/orchestra/state/T11-triage-smoother"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
worker=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
python3 tools/fuzz/run.py --plugin olmsmoother --n 300 --seed 1 --jobs 2 \
  --worker "$worker" --scratch "$s" --budget-minutes 10 \
  --report "$s/verify-census.json" --corpus "$s/verify-corpus" > "$s/verify-census.log" 2>&1
python3 tools/fuzz/triage_olmsmoother.py --jobs 2 --worker "$worker" \
  --census "$s/verify-census.json" --report "$s/verify-triage.json" > "$s/verify-triage.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" \
  tools/fuzz/compare_olmsmoother_classifier8.py --jobs 2 --worker "$worker" \
  --corpus tests/fuzz_corpus/olmsmoother/seed1_case000006_92552f06afe6.json \
  --corpus tests/fuzz_corpus/olmsmoother/seed1_case000000_eaba52d5eacc.json \
  --owner-corpus tests/fuzz_corpus/olmsmoother \
  --report "$s/verify-classifier.json" > "$s/verify-classifier.log" 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother --jobs 2 --worker "$worker" \
  --replay tests/fuzz_corpus/olmsmoother --scratch "$s" --budget-minutes 10 \
  --report "$s/verify-replay.json" > "$s/verify-replay.log" 2>&1
git diff --check
```

Expected: census complete 300; Classic 62 exact / 29 mismatch / 95 refusal / 114 uncompared; one observed refusal guard, zero legal comparable refusals and zero parameter-range violations; neutrality 600/600; gate table above (sanitized both-off failures are expected findings); classifier 22/22 pixels, 88/88 directions; owner 29 Mac-equal / 0 worker-equal; replay exit 0 with 29/29 `matches_saved`. No frozen reference/corpus changes are needed to obtain these results.

next:
- **SM1-ORACLE-PF16:** implement/validate the legacy `DEEP_PIXELS` world-allocation callback in a separately authorized emulator ticket; 114/300 cases currently stop before reference output despite advertised PF16 support.
- **SM1-ORACLE-HOST-BOUNDARY:** capture matching parameter-builder, world, callback/dispatch and writeback state in the frozen worker and retained direct host; all 29 saved PF8 cases disagree across original hosts, including the 1×3 and 1×19 minimal witnesses. Preserve the existing oracle until the first differing stage is proved.
- **SM1-CLASSIFIER-STACK-UB:** repair general synthetic-stack address translation and audit related read/write helpers; both minimal PF8 cases trigger UBSan at `stack+a-kStack`. Require sanitizer-clean replay and unchanged bytes, without coordinate-specific adjustments.
- **SM1-FUZZ-DEPTH-ACCOUNTING:** separate advertised-depth campaigns from explicit unsupported-depth probes, with generator-version/corpus migration discipline; 95 PF32 cases currently inflate the apparent refusal rate. Keep PF16 marked unverified until its oracle callback is fixed.

No MAIN/emulator-source writes, worker rebuilds, installations, pushes, history rewrites, release-gate/ledger edits, or other-plugin production changes were made. Scratch remained below 5 GiB; regenerable build outputs were removed after verification. All new scratch was under this ticket directory, with TMPDIR/TMP/TEMP rebound there.
