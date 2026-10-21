status: done

summary:
- Added optional refusal tracing to ColorKeep/ColorKey and their adapters; production admission and numerical behavior remain unchanged by default.
- Smart-only seed-1 census attributes 95/95 ColorKeep and 41/41 ColorKey refusals; all 600 pre-instrumentation result dictionaries are unchanged.
- Scratch flag bypass / host correction makes ColorKeep 95/95 newly exact; ColorKey zero-count bypass gives 40 exact and one signaling-NaN mismatch.
- Retained ColorKey replay is 3/3 matches_saved; ColorKeep's historical corpus is empty, supplemented by a 300/300 pre-instrumentation snapshot replay.
- Two retained PF32 alpha clusters, one oracle limitation, and existing odd-stride UB are separated into proposed follow-up tickets below.

facts:

Base: `e3f887b5`, branch `orch/T12-triage-colorkeep-colorkey`. Read AGENT_GUIDE, GOTCHAS, the two plugin decision-matrix/forbidden-action rows, the plan's classification table, T03/T05 and T04's two plugin entries. F17/F18 are **absent from this worktree's history**. Read F17 from MAIN and F18 from the sibling F18 worktree, both read-only. Their measured original capabilities select **Smart for both plugins**. `triage_colors_T12.py --target-only` restricts this older runner to its already-correct Smart→Smart pair; no Classic numerical conclusion is drawn. The wrapper also works with F17's paired runner. No unrelated framework or plugin was imported, no capability flags were changed, and no historical corpus was rebaselined.

Machine-readable evidence: `reports/fuzz/colors_T12.json`. It retains all 600 input hashes, baseline Smart result dictionaries, per-case guards, original/current source and build provenance, campaign hashes, sanitizer summaries, and four raw witness comparisons. Inputs reproduce through the unchanged version-1 generators or the three committed corpus JSONs. Full campaign logs/results live under ticket scratch. The retained cached worker was used directly; no worker/source rebuild or MAIN write occurred.

- Worker: `/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker`, SHA256 `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`.
- Original ColorKeep AEX SHA256: `6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86`.
- Original ColorKey AEX SHA256: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- Instrumented ColorKeep source SHA256: `650421a70899b79c232620465859808b15e6b341c4ae710abcfab8b9e3690755`.
- Instrumented ColorKey source SHA256: `25570267e1fec46b7aa8185771cbdc2b8f0bd3d886356ad19bf32d4632918f52`.

**Tracing and neutrality.** Wrapped 22 ColorKeep and 32 ColorKey error sites with named `function:tag@line` traces. They append through `O_APPEND` only when `OLM_REFUSAL_TRACE` names a file, preserve errno, and return the original error 516. Each adapter uses a separate trace file per case/route; attribution is the third return item, outside compared results. Sanitizer diagnostics are also kept outside harness metadata. There is no shared per-case environment mutation between the two jobs.

Ran pre-edit and traced campaigns with `--n 300 --seed 1 --jobs 2 --shrink-attempts 0`, the worker above, ticket-local `--scratch`, `--report`, and `--corpus`. All completed. Exact equality of complete Smart comparison dictionaries, including reference status/hash, candidate metadata/hash and byte diffs: **ColorKeep 300/300, ColorKey 300/300**. ColorKeep: 205 exact / 0 mismatch / 95 refusal. ColorKey: 255 exact / 3 mismatch / 41 refusal / 1 uncompared. The difference from T04's 256 exact is seed-1 index 96: this indexed worker rejects an unsupported `api-ms-win-crt-math-l1-1-0.dll!atan2f`; it is not a new candidate residual. F17 reported the same rejection with this worker.

Ranked first-guard table (Smart, one case per row; all controls are generator-legal):

| Rank within plugin | Plugin / guard | Cases | Share of refusals | Depths 8/16/32 | Trigger and legality |
|---|---|---:|---:|---|---|
| 1 | ColorKeep `ColorKeepValidateWorldPair:world-flags-or-bounds` | 95 | 100% | 0/0/95 | All PF32. Adapter sets `world_flags=DEEP` for both 16 and 32; source expects DEEP only for 16. Thus legal pixels/controls but a malformed fake-host flag, **not 95 proven refusals of valid native worlds**. |
| 1 | ColorKey `CheckoutSmartInfo:color-count` | 41 | 100% | 13/16/12 | All slot 22 count=0, within captured original slider bounds; original Smart renders all 41. Mac requires count≥1. |

First witnesses: ColorKeep index 2, 10×19 PF32, guard line 216; ColorKey index 5, 16×67 PF16, guard line 633. No other traced guard fired. Count-zero ColorKeep is outside this generator's sampled count set and is not assessed here.

**Gate-off experiment.** `OLM_COLORKEEP_EXPERIMENT_BYPASS` and `OLM_COLORKEY_EXPERIMENT_BYPASS` default to 0. Only the scratch adapter host compilation defines them when `OLM_COLOR_TRIAGE_BYPASS=1`. ColorKeep skips the DEEP-flag clause only, retaining bounds/layout validation. ColorKey permits exactly count zero, retaining negative/out-of-range rejection. Both fall through existing checkout/render/commit code; neither returns synthetic success. No gate is relaxed in default builds.

| Smart baseline guard population | Cases | Unblocked | Exact | Mismatch | Still refused / uncompared | Crash / harness error | UBSan rows in that population | ASan rows |
|---|---:|---:|---:|---:|---|---|---:|---:|
| ColorKeep world flags, bypass | 95 | 95 | 95 | 0 | 0 / 0 | 0 / 0 | 65 | 0 |
| ColorKey count zero, bypass | 41 | 41 | 40 | 1 | 0 / 0 | 0 / 0 | 16 | 0 |
| ColorKeep host-flag correction only, guards retained | 95 | 95 | 95 | 0 | 0 / 0 | 0 / 0 | not run for this control | not run for this control |

The host control changes only the scratch harness's world flag to `depth==16 ? DEEP : 0`. Its entire 300-case result set equals the ColorKeep bypass result set; the production guard stays active. Gate-off full populations: ColorKeep 300 exact; ColorKey 295 exact / 4 mismatch / 1 original-oracle reject. The fourth mismatch is index 116, 7×6 PF32, with count zero and two signaling-NaN alpha words (details below).

Sanitizers: ran **all 300 Smart cases** for each plugin in both default and bypass builds, `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`, with recoverable UBSan. Default→bypass UB case counts: ColorKeep **83→148**, ColorKey **88→104**. All reported runtime errors are misaligned typed accesses/references, not arithmetic overflow. No candidate crashes, harness errors, ASan reports, or timeouts. Every sanitized candidate result equals its unsanitized counterpart after removing the sanitizer diagnostics: 300/300 in all four campaigns. UB counts overlap exact/mismatch counts; exact output is **not** sanitizer cleanliness. Leak checking is disabled/not claimed.

First default UB witnesses: ColorKeep index 3, PF16, input/output padding 1/11, member access in `ColorKeep16Func` at source line 276; ColorKey index 2, PF32, input padding 7 (shared with output by its host), reference binding in `RenderTyped` at line 1857. Both are pre-existing under the padded fake-host contract. No native AE odd-stride reachability is claimed.

**Retained cluster classification.** T04 retained two signatures across three ColorKey files; ColorKeep has none. Took the smallest retained case by active pixel count in each signature: index 20 (1 pixel) and index 126 (20 pixels, smaller than index 99's 31). Measured all three again against original Smart. The public hosts expose final raw output only; no paired intermediate trace exists for these PF32 cases. The older `probe_olmcolorkey_combined_numerical_stage_witness_20260716.py` is a fixed 5×5 PF8 Replace/Thin/Blur witness, not an intermediate capture for these inputs. FIRST differing stage therefore remains **unlocated**, not inferred from final bytes.

| Cluster / witness | Smallest retained geometry | Diff bytes / samples | First byte; AEX→Mac little-endian sample | Channels / spatial pattern | Max absolute difference | Plan classification |
|---|---|---|---|---|---|---|
| signed-zero alpha, index 20 / `32358eb88430` | 1×1 PF32 | 1 / 1 | 3; `00000000`→`00000080` | A only at (0,0); source has −0, Mac preserves it, AEX writes +0 | byte 128; finite float 0 | **unexplained** numerical-operation/owner difference; no first-stage proof |
| signaling-NaN alpha, index 126 / `9b13c27c2f2e` | 5×4 PF32 | 1 / 1 | 210; `4623c1ff`→`462381ff` | A only at (3,2); isolated source sNaN, AEX quiets it, Mac preserves bits | byte 64; float abs diff undefined (NaN), not zero/tolerance | **unexplained** numerical-operation/owner difference; no first-stage proof |
| same NaN signature's other retained case, index 99 | 1×31 PF32 | 1 / 1 | 274; `4623c1ff`→`462381ff` | A only at (0,17) | byte 64; float undefined | same unexplained cluster |
| newly exposed zero-count case, index 116 | 7×6 PF32 (unreduced) | 2 / 2 | 258; `4623c1ff`→`462381ff` | A only at (2,2), (0,4); RGB exact | byte 64; float undefined | same observed NaN **signature**, common root cause unproven |

For all four measurements, Mac output SHA256 equals input SHA256. Index 20's input/Mac hash is `5a84100cd36b1fcd1313c825a6024399c709c61c71f092b13bd1981f7a7d9bf2`, AEX `5acad5ae07164031d1b7dda4ef816b83df950e40d014976545734909f6fcbfb7`. Index 126's input/Mac hash is `6b5b55752abf2dd9620180445794a5c839e8240f5299096806e1ba5a9fe1fc5e`, AEX `e8da6f751871100eb2a2c21e195cf3c85a667186fa61d3beb82f7fc59c773d75`. Other hashes and every differing coordinate are in the evidence JSON. No claim of globally minimal inputs; the new case was intentionally not counted as a third retained root-cause cluster. Unshrunk campaigns have 3/4 syntactic signatures, which are not new cause counts.

Other classifications: ColorKeep flag refusal is **comparator/reference (fake-host construction)**; ColorKey zero-count refusal is a **port admission difference** at the measured public boundary; alignment reports are **port/harness typed-access UB**, with native host reachability **unverified**; index 96 is a **comparator/reference limitation** (unimplemented emulator import), not evidence of native Windows dependency rounding.

**Replay.** Both literal corpus commands were run with `--jobs 2`. ColorKey: `replay_complete`, 3/3 `matches_saved`, exit 0. ColorKeep: `setup_error`, `Replay corpus is empty`; there are no historical `matches_saved` values to preserve. This was not counted as passing. `analyze_colors_T12.py` creates a scratch corpus from **all 300 pre-instrumentation ColorKeep results**, preserving generated input hashes. `--target-only --replay orchestra/state/T12-triage-colorkeep-colorkey/colorkeep-neutrality-corpus --jobs 2` then gives `replay_complete`, **300/300 matches_saved**, exit 0. No permanent historical fixture was overwritten.

Final verification: `bash tools/fuzz/verify_colors_T12.sh` completed with exit 0; both 300-case result sets, guard/gate/sanitizer counts, four witnesses and both replay totals reproduced. `git diff --check` passed. Removed regenerable scratch corpora/builds; remaining logs/results total 139,790,207 bytes (below 5 GiB). No `/tmp` writes, installation, push, release-gate/ledger edits, other-plugin edits, or history rewrite.

inference:
- ColorKeep's 95 historical refusals motivate a host adapter fix, not production guard removal. The independent host-only control recovers exactly the same outputs as the diagnostic bypass.
- ColorKey's zero-count path has a usable fall-through implementation, but the 40/41 exact result does not justify blindly promoting it: preserve the nonfinite witness and address alpha semantics/UB as separate evidence obligations.
- `RenderTyped` copies source pixels before conditional alpha operations. Combined with unchanged Mac output and alpha-only AEX changes, this makes the float alpha writer/operation order a useful investigation boundary. It does **not** prove which original stage first differs or whether both bit signatures share one operation. No output-bit patch is justified.
- These are bounded CPU-AEX/fake-host findings, not native AE, Windows UCRT, GPU, all-parameter, or arbitrary-layout equivalence. No two speculative numerical fixes were attempted/refuted; the ticket stops at the requested triage boundary.

changed_files:
- `mac/ColorKeep/ColorKeep.cpp`
- `mac/OLMColorKey/OLMColorKey.cpp`
- `tools/fuzz/adapters/colorkeep.py`
- `tools/fuzz/adapters/olmcolorkey.py`
- `tools/fuzz/adapters/color_triage.py`
- `tools/fuzz/triage_colors_T12.py`
- `tools/fuzz/analyze_colors_T12.py`
- `tools/fuzz/verify_colors_T12.sh`
- `reports/fuzz/colors_T12.json`
- `orchestra/reports/T12-triage-colorkeep-colorkey.md`

verify:

```sh
s="$PWD/orchestra/state/T12-triage-colorkeep-colorkey"
mkdir -p "$s"
bash tools/fuzz/verify_colors_T12.sh > "$s/verify.log" 2>&1
tail -6 "$s/verify.log"
git diff --check
```

The script runs all campaigns sequentially with **jobs 2**, uses only the indexed cached worker and MAIN assets by absolute path, redirects individual logs to scratch, compares fresh baseline Smart dictionaries to committed evidence, checks gate/sanitizer counts, remeasures all four raw witnesses, and performs the 3/3 plus 300/300 replays. Expected: exit 0; both plugins print `300/300 unchanged; guards and gate-off/sanitizer counts reproduced`, then `olmcolorkey 3/3 matches_saved` and `colorkeep-300 300/300 matches_saved`. It reconstructs the neutrality snapshot from tracing-disabled current code; the evidence JSON separately retains the actual pre-edit provenance. No Classic raw-output equality against Smart is used as new evidence. Scratch corpus/build outputs are disposable; leave the report/logs if needed.

next:
- Proposed **ColorKeep fake-host PF32 flags**: correct DEEP only for PF16; 95/95 formerly refused cases become exact with production guards retained.
- Proposed **ColorKeep byte-safe padded rows**: remove unaligned typed pixel access through the public iterate path; 83 default UB cases plus 65 newly reachable PF32 cases, despite exact bytes.
- Proposed **ColorKey zero-color public admission**: original legal count zero renders all 41; existing fall-through is 40 exact/1 NaN mismatch. Validate no-color semantics across toggles and retain nonfinite coverage before promotion.
- Proposed **ColorKey signed-zero alpha first divergence**: retained 1×1 index 20 differs only in alpha sign; trace original builder/classifier/writer and restore the general operation, never a final-bit correction.
- Proposed **ColorKey signaling-NaN alpha first divergence**: retained index 126/99 and gate-off index 116 isolate alpha quieting; determine original arithmetic/owner and prove payload/sign behavior with adjacent inputs.
- Proposed **ColorKey byte-safe padded pixel access**: 88 default plus 16 newly reachable zero-count UB cases; make typed loads/stores alignment-safe without changing arithmetic or bytes.
- Proposed **ColorKey comparator atan2f support/calibration**: seed-1 index 96 cannot be compared with the indexed worker; separate controlled import implementation and native-UCRT validation from pixel fixes. No worker rebuild was authorized here.
