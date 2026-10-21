status: done

summary:
- Added behavior-neutral `OLM_REFUSAL_TRACE` tags and per-route adapter attribution; corpus replay is 145/145 `matches_saved`.
- All 300 baseline Smart refusals are a fake-host checkout reference-size failure, not a numerical admission census.
- Scratch gate-off and corrected-host builds agree on all 300 cases: 166 exact / 76 mismatch / 51 refusal / 7 uncompared; sanitized results are identical with zero sanitizer errors or crashes.
- Classified all 12 retained clusters using their smallest saved shrink; two singleton clusters are proven cross-route comparator differences, ten remain unexplained.
- No production guard, rendering behavior, baseline report, corpus, release gate, ledger, or other plugin was changed.

facts:

Scope and provenance:
- Branch `orch/T07-triage-distancegradation`; starting HEAD `6ec72ab80c0407b2bad998906187acaf22a9cacc`.
- Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the DistanceGradation ledger rows (especially forbidden actions at line 4996), the plan classification table, T03, and the DistanceGradation entries in T04. T05's ticket is present; its report is absent in this worktree.
- The worker is the baseline's retained absolute executable `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Inspected `/Users/onmk/.cache/olm-emu/INDEX.json`; did not substitute its differently hashed workers or rebuild any emulator.
- Original AEX SHA-256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; baseline report SHA-256 `fb7297dc5e4b9aef6e185a5b5bfea6638111ff62702ef186fd3640fd50724b1e`. AEX assets are read in place from MAIN. Full candidate, source dependency, scratch-source and compiler-flag bindings are in the committed evidence JSON.
- This is Unicorn CPU AEX versus public `EffectMain` in the retained SDK shim. Host imports and fake-host observations do not establish native Windows UCRT or native AE equivalence.

Neutrality and refusal census:
- `python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --budget-minutes 10 --scratch orchestra/state/T07-triage-distancegradation --report orchestra/state/T07-triage-distancegradation/replay.json > orchestra/state/T07-triage-distancegradation/replay.log 2>&1` exited 0: 145 completed, 145 `matches_saved`.
- `python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --budget-minutes 10 --scratch orchestra/state/T07-triage-distancegradation --report orchestra/state/T07-triage-distancegradation/census.json --corpus orchestra/state/T07-triage-distancegradation/census-corpus > orchestra/state/T07-triage-distancegradation/census.log 2>&1` exited 0: AEX 290 ok / 8 reject / 2 budget; Classic 145 exact / 145 mismatch / 0 refusal / 10 uncompared; Smart 300 refusal. These equal the original route counters. No shrinking was requested for this census (121 unreduced signatures); the 12 original reduced clusters below are retained unchanged.
- Nineteen explicit bad-callback guard sites now append `function:tag@line` through `DistanceRefusal`, with the same PF_Err and no output-world writes. Callback-propagated errors and OOM/exception returns are not comprehensively tagged; none caused this baseline's refusals. The adapter uses a per-call copied environment and reads/unlinks its route-local trace outside the compared result. It does not mutate shared adapter state.

Ranked guards (baseline legal control cases; source profiles separately identified):

| Rank | Guard | Classic | Smart | AEX ok among refused | Trigger / boundary |
|---|---|---:|---:|---:|---|
| 1 | `SmartPreRender:prerender-reference-size` | 0 | 300 | 290 | `pre_checkout` leaves `ref_width/ref_height` at zero; all generated widths/heights are positive |
| — | All other tagged guards | 0 | 0 | — | Hidden behind the first failure, not proven reachable by the baseline |

- Coverage: 300/300 refusals attributed. Depths: PF8 91, PF16 114, PF32 95. PF32 profiles: SDR 62, HDR 12, signed 12, nonfinite 9. Controls are within the captured builder ranges, including corrected legal In/Out default 1; extended PF32 samples are not claimed to lie inside the Mac Smart SDR admission contract.
- Source boundary: `SmartPreRender` zero-initializes `PF_CheckoutResult`, calls `pre_checkout`, then requires reference dimensions equal `in_data` dimensions. The retained callback sets only result/max-result rectangles. Content rectangles do not supply storage dimensions.

Gate-off experiment:
- `python3 tools/fuzz/triage_distancegradation.py --jobs 2 --report orchestra/state/T07-triage-distancegradation/triage.json > orchestra/state/T07-triage-distancegradation/triage.log 2>&1` exited 0. Re-generated all 300 seed/index inputs and asserted each baseline input hash before execution; observed the same 290/8/2 AEX statuses.
- The script generates a scratch translation unit with `!OLM_DG_TRIAGE_GATE_OFF &&` on only the reference-size condition. No switch is in production source. `OLM_DG_TRIAGE_HOST_FIX` fills callback reference dimensions in the scratch host. Other validation, staging, public routes and numerical code are unchanged.

| Smart configuration (300 inputs) | Unblocked to output | Exact | Mismatch | Still refused | Uncompared | Crash | Sanitizer error |
|---|---:|---:|---:|---:|---:|---:|---:|
| Production / original host | 0 | 0 | 0 | 300 | 0 | 0 | not enabled |
| Reference-size gate off | 249 | 166 | 76 | 51 | 7 | 0 | not enabled |
| Gate on / callback dimensions supplied | 249 | 166 | 76 | 51 | 7 | 0 | not enabled |
| Reference-size gate off / ASan + UBSan | 249 | 166 | 76 | 51 | 7 | 0 | 0 |

- The gate-off path exists and reaches normal Smart staging/RenderBits. Gate-off versus host-fix result dictionaries, including raw hashes, error codes, callback counts and guard tags, agree for 300/300 cases. Sanitized versus unsanitized dictionaries also agree for 300/300. Sanitizers use `-fsanitize=address,undefined -fno-sanitize-recover=all`, `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`, and `ASAN_OPTIONS=detect_leaks=0`; leak checking is not claimed. This checks the Smart experiment only, not Classic alignment or all code paths.
- By depth after gate-off: PF8 49 exact / 39 mismatch / 3 uncompared; PF16 89 / 22 / 3; PF32 28 exact / 15 mismatch / 51 refusal / 1 uncompared.

Newly exposed refusal ranking (conditional on repairing/bypassing the first guard):

| Rank | Guard | Cases | AEX ok/reject | Source profile |
|---|---|---:|---|---|
| 1 | `RenderBits:pf32-smart-bounded-sdr` | 32 | 31/1 | HDR 12, signed 12, nonfinite 8 |
| 2 | `RenderBits:pf32-smart-profile` | 19 | 17/2 | SDR 19 |

These two downstream guards remain enabled in every experiment. Their removal is unverified; the gate-off claim is strictly about the sole baseline top guard. There is no claim that HDR/nonfinite refusal is itself a bug.

Cluster classification:
- Selected minimum retained pixel count, then active input bytes, then corpus path as a deterministic tie-break. These are the smallest *saved* greedy shrinks, not globally minimal inputs. All 12 Mac hashes still match their saved Classic hashes.
- `first_stage()` provides no paired stages, and the retained worker session exposes final raw output only. Mac's `OLM_DG_DEBUG_DUMP_PATH` can print alpha/d_alpha/field values, but there is no corresponding captured AEX stage for these inputs. Therefore the FIRST differing internal stage is **unverified for all 12**, and no field/blur/compose cause is inferred from output alone.
- Table units: different bytes/typed words; max absolute byte difference/max absolute sample difference (PF16 in 0..32768 units, PF32 float units). Channels are ARGB memory channels. All representatives differ at one pixel only; C04 is the last pixel of a 4×1 row, the others are 1×1. Full bounding boxes, first little-endian word hex, hashes, parameters and corpus paths are in `reports/fuzz/olmdistancegradation_T07_triage.json`.

| ID | Nondefault slots; depth | Baseline cluster cases | Smallest saved case; geometry | Diff bytes/words; max byte/sample | Spatial/channel pattern | Plan classification |
|---|---|---:|---|---|---|---|
| C01 | 10,11,12; PF16 | 1 | case000186; 1×1 | 1/1; 128/32768 | G; 1/1 pixels; first (0,0) G | unexplained |
| C02 | 11,12; PF16 | 3 | case000084; 1×1 | 1/1; 128/32768 | G; 1/1 pixels; first (0,0) G | unexplained |
| C03 | 11,12; PF8 | 2 | case000167; 1×1 | 1/1; 255/255 | G; 1/1 pixels; first (0,0) G | unexplained |
| C04 | 2,6; PF16 | 1 | case000243; 4×1 | 1/1; 128/32768 | R; 1/4 pixels; first (3,0) R | unexplained |
| C05 | 2; PF8 | 2 | case000000; 1×1 | 1/1; 255/255 | R; 1/1 pixels; first (0,0) R | unexplained |
| C06 | 5; PF16 | 3 | case000138; 1×1 | 1/1; 128/32768 | G; 1/1 pixels; first (0,0) G | unexplained |
| C07 | 5; PF8 | 9 | case000009; 1×1 | 3/3; 80/80 | R/G/B; 1/1 pixels; first (0,0) R | unexplained |
| C08 | 6; PF16 | 1 | case000287; 1×1 | 1/1; 128/32768 | A; 1/1 pixels; first (0,0) A | comparator (cross-route) |
| C09 | 6; PF8 | 1 | case000061; 1×1 | 1/1; 255/255 | A; 1/1 pixels; first (0,0) A | comparator (cross-route) |
| C10 | default; PF16 | 16 | case000001; 1×1 | 1/1; 128/32768 | R; 1/1 pixels; first (0,0) R | unexplained |
| C11 | default; PF32 | 81 | case000002; 1×1 | 2/1; 128/1.0 | R; 1/1 pixels; first (0,0) R | unexplained |
| C12 | default; PF8 | 25 | case000004; 1×1 | 1/1; 255/255 | R; 1/1 pixels; first (0,0) R | unexplained |

- First mismatch example C01: byte 5, typed G word at (0,0), AEX `0000`, Mac `0080` (little-endian 0 versus 32768). C11: byte 6, R at (0,0), AEX `00000000`, Mac `0000803f` (0 versus 1).
- Additional owner audit: all 12 representatives successfully ran original-AEX Classic. C08 and C09 match Mac Classic exactly but differ from AEX Smart; both clusters contain one case, so this explains those two baseline mismatches as cross-route comparisons. The Smart host-fix candidate still differs from AEX Smart on those same inputs; that is a separate unresolved Smart result, not an excuse to discard it.
- For the other ten representatives, Mac Classic also differs from AEX Classic. AEX Classic equals AEX Smart on C01/C02/C03/C05/C06/C07/C11, and differs on C04/C10/C12. Correcting only the comparator route therefore does not close those ten representatives. C01/C02/C11 become exact on Mac Smart with the callback fixed; the remaining nine Smart representatives mismatch.

inference:
- The baseline's apparent total Smart incompatibility is dominated by an adapter host contract defect: fixing reference dimensions produces exactly the same outputs as bypassing the guard. Keep the production guard and fix the fake callback in a follow-up with intentionally updated replay expectations.
- C08/C09 are comparator/reference problems for the existing Classic-versus-Smart metric. The remaining clusters are classified unexplained rather than prematurely labeled port bugs or Windows dependency differences. Final bytes alone do not identify their first failing operation, and cluster signature/count is not a root-cause equivalence proof.
- PF32 admission and default-color/owner-specific composition merit separate investigations. The current measurements do not justify global rounding, EDT, powf, OpenCV, or final-byte edits.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp` — optional refusal attribution only.
- `tools/fuzz/adapters/olmdistancegradation.py` — route-local trace collection only.
- `tools/fuzz/triage_distancegradation.py` — reproducible scratch builds, gate/host/sanitizer experiments, smallest-cluster statistics and owner audit.
- `reports/fuzz/olmdistancegradation_T07_neutrality.json` — replay/census summary and full build provenance.
- `reports/fuzz/olmdistancegradation_T07_triage.json` — per-case experiment and representative evidence.
- `orchestra/reports/T07-triage-distancegradation.md` — this report.

verify:
```sh
mkdir -p orchestra/state/T07-triage-distancegradation
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --budget-minutes 10 --scratch orchestra/state/T07-triage-distancegradation --report orchestra/state/T07-triage-distancegradation/verify-replay.json > orchestra/state/T07-triage-distancegradation/verify-replay.log 2>&1
python3 tools/fuzz/triage_distancegradation.py --jobs 2 --report orchestra/state/T07-triage-distancegradation/verify-triage.json > orchestra/state/T07-triage-distancegradation/verify-triage.log 2>&1
git diff --check
```
Expected: replay exit 0, 145/145 `matches_saved`; triage exit 0, 300 original Smart refusals, gate/host/sanitizer counts in the table, 12 representatives, no sanitizer errors, C08/C09 same-owner exact. AEX wall-time budget counts can vary under shared-machine load; compare each result's explicit oracle status before interpreting counts. Source/candidate hashes and compiler identity changes are evidence to review, not values to force. Builds and sidecar worlds are automatically deleted; all scratch remains under this ticket and below 5 GiB. No `/tmp` writes, MAIN writes, push, history rewrite, or native AE interruption were performed.

next:
Proposed follow-up fix/investigation tickets (one evidence-backed scope each):
- **DG-HOST-REFSIZE:** populate checkout reference dimensions in the fuzz host; all 300 refusals share this missing field, and host-fix matches gate-off 300/300 while unblocking 249 outputs.
- **DG-COMPARATOR-OWNERS:** retain separate Classic-to-Classic and Smart-to-Smart comparisons; singleton C08/C09 are already Classic exact, while their Smart output remains mismatched.
- **DG-SMART-PF32-ADMISSION:** investigate the 19 SDR profile refusals exposed after host correction (17 AEX successes), preserving existing guard behavior until paired boundary witnesses support general code.
- **DG-PF32-EXTENDED-DOMAIN:** define and witness HDR/signed/nonfinite Smart behavior behind the 32 bounded-SDR refusals (31 AEX successes); do not equate AEX completion with permission for unchecked nonfinite arithmetic.
- **DG-DEFAULT-OWNER-COMPOSE:** trace the first differing field/compose stage for C10/C11/C12 (122 baseline cases grouped by signature); each representative first differs only in R, and C11 is Smart exact but Classic mismatched against both AEX owners.
- **DG-BLURRED-OWNER-COMPOSE:** paired-stage trace C01/C02/C03 (6 baseline cases); representatives differ only in G, with PF16 Smart exact and PF8 Smart still mismatched after the host fix.
- **DG-LAYER-RENDER-MODE:** trace C06/C07 (12 baseline cases); Render Mode slot 5 representatives differ in G at PF16 and RGB at PF8, with both Mac routes still mismatching.
- **DG-INOUT-BACKGROUND:** trace C04/C05 (3 baseline cases); isolate the last-pixel R difference on the 4×1 C04 input and the 1×1 C05 R difference, keeping the owner split explicit.
