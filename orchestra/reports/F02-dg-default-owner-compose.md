status: partial

summary:
- Restored the original owner's uniform-mask flag and its early compose branch; no coordinate/value patches or admission changes.
- Named C10/C11/C12 representatives are exact on both Mac routes; 118/122 retained target shrinks are exact. Four nonuniform C12 field residuals remain.
- Seed 1 / 300 unreduced inputs: Classic exact 145 -> 158; Smart exact 166 -> 177; no exact regressions.
- Corpus: 139 cases changed only toward exact (193 route results); 6 cases unchanged; 11 existing tests pass.
- Independent 171 conditions / 342 sanitized route runs: every changed output becomes exact; unresolved mixed-mask controls remain unchanged.

facts:

Identity and scope:
- Starting commit `b7c1a8b0b5b1981e5e3524442dc401f4016131a0`; branch `orch/F02-dg-default-owner-compose`.
- AEX SHA-256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; retained worker SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` at `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`. Inspected cache INDEX; no emulator rebuild or substitution. Original assets and disassembly read from MAIN by absolute path.
- The checkout-reference fix already exists at the starting commit. The before measurements therefore use working Smart callbacks, not T07's historical 300 refusals.
- All counts below compare both Mac public routes to the existing **AEX Smart** oracle, unchanged from the fuzz framework. This does not establish Mac Classic-to-AEX Classic equivalence or native AE/UCRT equivalence.

First differing owner/compose boundary:
- Original AEX `FUN_1811749a0` converts alpha to an 8-bit plane and thresholds at 1. `FUN_181183000` counts nonzero mask pixels. Owner sites `0x18117199a` (PF16), `0x1811726aa` (PF8), `0x1811733ba` (PF32) set context byte `+0x90` when count is 0 or width*height.
- The three typed callbacks test that flag at `0x18117048d`, `0x18117087d`, `0x181170c9d`, **before field reads, interpolation and RGB selection**. With background disabled they return all-zero ARGB; with background enabled they return alpha 1 and the background RGB, independent of source alpha/foreground.
- Natural public Smart traces (18 rows) captured the actual builder-produced owner context, source pixels, mask and staged field. No refcon was fabricated and no guest values were patched. For each depth, alpha bytes `[1,2]` become mask `00ff` with flag 0, while `[1,1]` and `[2,2]` set flag 1. Endpoint uniform/mixed controls also agree. The trace script asserts each observation, raw output guards and zero render error.
- Function/indirect-iterate watches initially returned explicit `unhookable_watches` (checkpoint worker cannot hook indirect callbacks). Successful capture uses direct owner calls and the final field-copy/wrapper boundary; this was an instrumentation limitation, not numerical evidence.
- Matched representative source bytes, source-linked Mac field/shade traces and original AEX fields are retained in the stage/trace artifacts:

| Cluster | Source ARGB bytes | AEX mask / +0x90 | AEX staged field | Mac field scalar (before and after) | Mac Classic output before | Mac output after / AEX Smart |
| --- | --- | --- | --- | --- | --- | --- |
| C10 PF16 | `0080008000800080` | `ff` / 1 | all zero | 1 | `0000008000000000` | 8 zero bytes |
| C11 PF32 | 16 zero bytes | `00` / 1 | all zero | 0 | `000000000000803f0000000000000000` | 16 zero bytes |
| C12 PF8 | `ffffff00` | `ff` / 1 | all zero | 1 | `00ff0000` | 4 zero bytes |

- First output mismatch is R at (0,0): PF16 byte 3 / word 1 (`0000` AEX vs `0080` Mac); PF32 byte 6 / word 1 (`00000000` vs `0000803f`); PF8 byte 1 / word 1 (`00` vs `ff`). C11 Smart was already zero because its existing transparent-pixel branch masked the absent owner flag.
- The earliest restored decision is the uniform-mask owner flag. C10/C12 also have an unused staged-field difference (AEX 0 versus Mac 1); the original callback bypasses it. The fix preserves the existing EDT, field mask, PF16 roundtrip and writer instead of retuning an unconsumed field.
- Same-run standalone AEX Classic audit remains C10=`0080008000800080`, C11=16 zero bytes, C12=`ffffffff`. These differ from AEX Smart for C10/C12 and are retained explicitly; this ticket does not rewrite the comparator or claim to close that separate owner contract.

General implementation:
- A finite normalized alpha is owned when its FLOAT32 `alpha*255` reaches 1.5 (nearest-even conversion makes the tie 2, which passes threshold 1). The owner census is uniform if every pixel has the same ownership. Non-SDR/nonfinite alpha retains previous behavior; the existing Smart admission guards remain in force.
- `DGParams::degenerate_mask` carries the census into the first compose branch. Background output uses the original color values and existing typed stores. No per-case/coordinate tables, tolerance, output-byte adjustment, field rewrite or guard relaxation was introduced.

Regression commands and results:
- Before and after: `python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch orchestra/state/F02-dg-default-owner-compose --corpus orchestra/state/F02-dg-default-owner-compose/{before,after}-corpus --report orchestra/state/F02-dg-default-owner-compose/{before,after}.json` (expand braces into two separate runs; logs `{before,after}.log`). Both exit 0 and complete 300; shrinking disabled for the unreduced census, existing reduced corpus retained separately.

| Route/status | Before | After |
| --- | ---: | ---: |
| AEX ok / reject / budget | 290 / 8 / 2 | 290 / 8 / 2 |
| Classic exact / mismatch / uncompared | 145 / 145 / 10 | 158 / 132 / 10 |
| Smart exact / mismatch / refusal / uncompared | 166 / 76 / 51 / 7 | 177 / 65 / 51 / 7 |
| Both routes exact | 139 | 151 |

- All 300 input hashes agree before/after. Compared changes: 13 Classic and 11 Smart mismatch -> exact; no other compared result changes. Classic case189 also changes while remaining **uncompared**: original AEX rejects the PF32 median-blur request with an OpenCV depth assertion. This is not counted as a fix or exact evidence.
- `python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --scratch orchestra/state/F02-dg-default-owner-compose --report .../replay-before.json` exits 0, 145/145 matches_saved. Candidate replay exits 1 as expected before refreshing expectations: all 145 complete, 139 cases change (139 Classic + 54 Smart mismatch -> exact), with **zero changes to a non-exact result** and all reference/input hashes unchanged. Post-update replay (`.../replay-final.json`) exits 0, **145/145 matches_saved**. A git-HEAD audit confirms all 139 corpus edits change only result/provenance, preserve oracle/input/controls/reduction data, and change only toward exact.
- `python3 tools/fuzz/probe_distancegradation_default_owner.py --report .../independent-final.json` exits 0: 171 conditions, Classic 29 exact retained + 101 newly exact + 41 unchanged mismatches; Smart 47 exact retained + 92 newly exact + 32 unchanged mismatches. All 342 ASan/UBSan route executions match ordinary outputs/metadata; no sanitizer errors. Includes 1x1, 3x2, 1x5, 7x1, independent colors, background off/on, alpha 0/full, PF8 1/2, PF16 192/193 and adjacent FLOAT32 words `0x3bc0c0c0/0x3bc0c0c1`, uniform/split/straddling masks. Remaining mixed-mask controls are data, not promoted to exact.
- `python3 tools/fuzz/probe_distancegradation_default_owner.py --representatives-only --report .../stages.json` exits 0: 3 representatives, both routes exact, 6 sanitizer matches; before/after field and shade traces recorded.
- MAIN's emulation `.venv/bin/python tools/fuzz/probe_distancegradation_default_owner.py --trace --report .../trace-final.json` exits 0: 18 public original-AEX traces with source/owner/field bindings and disassembly assertions.
- Existing tests run with TMPDIR/TMP/TEMP set to ticket scratch and PYTHONDONTWRITEBYTECODE=1: `python3 -m unittest discover -s tests -p 'test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py'` (7 pass), `... -p 'test_olmdistancegradation_generic_production_beta_20260820.py'` (2 pass, including sanitizer), `... -p 'test_olmdistancegradation_smart_transactional_20260822.py'` (2 pass, including sanitizer). `git diff --check` passes.

Orchestrator-visible corpus update table:
- Directory: `tests/fuzz_corpus/olmdistancegradation/`. Only the following 139 saved results and their provenance are refreshed. Input bytes, controls, reduction history and filenames remain unchanged. E=exact, M=mismatch; each route column is before -> after. Full before/after hashes, diffs and oracle identities are in `reports/fuzz/olmdistancegradation_F02_regression.json`.

| Corpus filename | Cluster | Classic | Smart |
| --- | --- | --- | --- |
| seed1_case000000_02a341f3b641.json | C05 | M -> E | M -> E |
| seed1_case000001_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000002_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000003_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000004_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000006_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000009_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000015_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000016_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000017_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000018_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000020_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000023_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000024_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000027_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000028_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000030_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000032_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000034_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000036_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000039_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000040_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000041_02a341f3b641.json | C05 | M -> E | M -> E |
| seed1_case000043_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000045_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000046_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000048_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000051_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000052_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000059_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000061_0f4b356bb556.json | C09 | M -> E | M -> E |
| seed1_case000062_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000064_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000066_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000068_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000071_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000077_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000078_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000080_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000082_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000084_3bf382f96c54.json | C02 | M -> E | E -> E |
| seed1_case000085_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000089_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000092_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000094_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000095_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000099_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000100_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000103_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000104_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000106_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000107_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000109_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000112_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000116_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000119_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000125_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000126_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000129_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000133_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000138_9e50cab1bcf7.json | C06 | M -> E | M -> E |
| seed1_case000141_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000143_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000146_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000150_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000151_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000152_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000154_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000156_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000160_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000161_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000162_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000165_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000167_c6eaa715b127.json | C03 | M -> E | M -> E |
| seed1_case000169_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000170_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000171_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000173_3bf382f96c54.json | C02 | M -> E | E -> E |
| seed1_case000174_c6eaa715b127.json | C03 | M -> E | M -> E |
| seed1_case000175_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000177_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000179_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000180_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000182_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000186_91db5e3c6b3a.json | C01 | M -> E | E -> E |
| seed1_case000187_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000188_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000194_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000198_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000199_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000200_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000202_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000204_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000208_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000213_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000214_3bf382f96c54.json | C02 | M -> E | E -> E |
| seed1_case000215_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000216_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000217_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000219_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000220_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000221_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000222_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000223_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000224_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000226_12bacfc8ca6e.json | C07 | M -> E | M -> E |
| seed1_case000228_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000233_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000235_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000238_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000245_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000249_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000250_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000252_9e50cab1bcf7.json | C06 | M -> E | M -> E |
| seed1_case000253_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000254_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000255_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000258_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000259_9e50cab1bcf7.json | C06 | M -> E | M -> E |
| seed1_case000261_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000262_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000267_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000268_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000270_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000272_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000275_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000277_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000281_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000283_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000286_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000287_b0140ce5f1be.json | C08 | M -> E | M -> E |
| seed1_case000290_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000292_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000293_92552f06afe6.json | C12 | M -> E | M -> E |
| seed1_case000294_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000295_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000297_ced0f1718a01.json | C10 | M -> E | M -> E |
| seed1_case000298_9b13c27c2f2e.json | C11 | M -> E | E -> E |
| seed1_case000299_9b13c27c2f2e.json | C11 | M -> E | E -> E |

- Unchanged residual corpus: 6 cases, Classic/Smart both still mismatch. Target clusters now have C10 16/16, C11 81/81, C12 21/25 exact retained shrinks. The three *named minimum representatives* pass, but full target-cluster closure is not claimed.

Remaining C12 boundary evidence (all captured original owner flags are **0**, not degenerate):

| Case | Geometry | First output mismatch | Original AEX intermediate | Current Mac intermediate |
| --- | --- | --- | --- | --- |
| 58 | 1x70 | (0,53) A: 42 vs 41 | field byte 212 | field scalar 0.835294127 (213/255) |
| 91 | 4x2 | (2,0) A: 0 vs 45 | alpha=1 at (3,1) -> mask 0; field byte 255 at (2,0) | existing alpha>0 field mask owns (3,1); field scalar 0.705882370 at (2,0) |
| 139 | 1x91 | (0,51) A: 168 vs 84 | alpha=1 at (0,52) -> mask 0; field byte 85 at (0,51) | existing alpha>0 field mask owns (0,52); field scalar 0.666666687 at (0,51) |
| 236 | 1x40 | (0,38) A: 42 vs 41 | field byte 212 | field scalar 0.835294127 (213/255) |

- `MAIN/tools/emulation/.venv/bin/python tools/fuzz/probe_distancegradation_default_owner.py --residual-trace --report .../residuals.json` exits 0. All four original input raw hashes and output raw hashes reproduce the saved references; current Mac hashes remain unchanged from baseline. The artifact retains full source/mask/field buffers and every Mac pixel's field/shade trace.
- Cases91/139 first diverge at the existing nonuniform PF8 field mask. Cases58/236 have matching binary masks and diverge by one byte at field staging; the earlier normalization/quantization substage is not yet isolated. No writer change is justified by those observations.
- These are distinct field problems that the signature-only clustering grouped with the uniform-owner bug. They remain open. This change deliberately preserves the ledger's depth-gated field mask and reciprocal normalization; it does not hide their mismatch by changing the compose/store bytes.

inference:
- Missing uniform-mask owner state explains the retained default-color shrinks. Red persisted because the port reached normal foreground selection even though the original callback took its early degenerate branch.
- The unchanged mixed-mask mismatches and distinct standalone Classic output show why this finite closure must not be generalized to all owner/field behavior or native AE. The nondegenerate field-mask differences are separate follow-up work.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp` — owner census and general early compose branch.
- `tools/fuzz/probe_distancegradation_default_owner.py` — reproducible baseline/current/sanitized public replay and original-AEX boundary traces.
- `reports/fuzz/olmdistancegradation_F02_{probe,trace,stages,residuals,regression}.json` — identities, raw results and before/after evidence.
- 139 listed `tests/fuzz_corpus/olmdistancegradation/*.json` — monotonic expectation/provenance updates.
- `orchestra/reports/F02-dg-default-owner-compose.md` — this report.

verify:
```sh
mkdir -p orchestra/state/F02-dg-default-owner-compose
export TMPDIR="$PWD/orchestra/state/F02-dg-default-owner-compose"
export TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/probe_distancegradation_default_owner.py --report "$TMPDIR/verify-probe.json" > "$TMPDIR/verify-probe.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/fuzz/probe_distancegradation_default_owner.py --trace --report "$TMPDIR/verify-trace.json" > "$TMPDIR/verify-trace.log" 2>&1
python3 tools/fuzz/probe_distancegradation_default_owner.py --representatives-only --report "$TMPDIR/verify-stages.json" > "$TMPDIR/verify-stages.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/fuzz/probe_distancegradation_default_owner.py --residual-trace --report "$TMPDIR/verify-residuals.json" > "$TMPDIR/verify-residuals.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$TMPDIR" --corpus "$TMPDIR/verify-corpus" --report "$TMPDIR/verify-census.json" > "$TMPDIR/verify-census.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --scratch "$TMPDIR" --report "$TMPDIR/verify-replay.json" > "$TMPDIR/verify-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py' > "$TMPDIR/verify-admission.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_generic_production_beta_20260820.py' > "$TMPDIR/verify-generic.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$TMPDIR/verify-transactional.log" 2>&1
git diff --check
```
Expected: all commands exit 0; probe 171 conditions with the counts above and 342 sanitizer matches; 18 uniform/mixed traces, 3 representative stage replays and 4 unchanged residual traces; census Classic 158/Smart 177 exact, 8 rejects/2 budget; replay 145/145 matches_saved; tests 7+2+2 pass. Time-budget counts can vary with workstation load; inspect explicit oracle statuses rather than comparing incomparable cases.

next:
- Full F02 target-cluster closure remains incomplete: four C12 shrinks above need nonuniform PF8 field work. Suggested split: DG-PF8-ALPHA1-MASK (91/139) and DG-PF8-FIELD-212-213 (58/236), preserving the recovered uniform-owner behavior. The other two unchanged corpus cases belong to C04/C07 and remain outside this ticket.
- Preserve the separate standalone AEX Classic contract/comparator investigation and PF32 extended-domain/admission work. Case189 remains an oracle dependency rejection, not a proven exact output.
- No release gate, ledger forbidden-action list, other plugin, MAIN source, emulator source, or native AE session was changed. No push or history rewrite. Scratch is under 5 GiB; regenerable binaries are removed by the probes.
