status: done

summary:
- Added optional behavior-neutral refusal tracing; all 600 refusals attributed and all 300 baseline result objects preserved.
- Production corpus replay: 8/8 `matches_saved`; scratch gate-off witness replay: 62/62 `matches_saved`.
- Combined gate-off: Classic 184 exact / 103 mismatch; Smart 84 exact / 52 mismatch / 164 refusal; 13 Classic outputs lack a successful AEX reference.
- Gate-off ASan/UBSan: 96 Classic + 54 Smart misaligned-read aborts. No production admission or arithmetic changed.
- Retained 62 bounded-shrink signatures, byte/channel/spatial statistics, classifications and proposed fix tickets below.

facts:
- Base `6ec72ab80c0407b2bad998906187acaf22a9cacc`, branch `orch/T06-triage-kirakira`. T03 was available; T05 report was absent. Read the shared guide, emulator gotchas, KiraKira ledger restrictions, T04 facts and compatibility plan.
- The baseline's AEX `287/13/0` means **success/rejection/budget**, not exact/mismatch/refusal. There were no baseline pixel-mismatch clusters because both Mac routes refused all 300 cases.
- The original production corpus contained only README. Eight refusal fixtures were selected from the original baseline to cover every observed route/guard/depth combination with successful AEX output. Their saved results/provenance are from that original report; regenerated input hashes match it. This is not a claim that a pre-existing nonempty corpus was replayed.
- Census command: `python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch orchestra/state/T06-triage-kirakira --report orchestra/state/T06-triage-kirakira/census.json --corpus orchestra/state/T06-triage-kirakira/census-corpus`. Result: complete, 287 AEX success / 13 reject, 300 Classic and 300 Smart refusals. All 300 `result` objects equal baseline, including reference hashes and metadata. All 300 cases satisfy the captured parameter bounds; zero violations.
- Tracing: `OLM_KIRA_REFUSAL` / `OLM_KIRA_ERROR` append `function:tag@line` to `$OLM_REFUSAL_TRACE` using `O_APPEND`, then return the original error. Thirteen return/error sites are tagged; four guards fired. The adapter uses a per-route file and a shallow copy for its environment, preserving thread safety and the compared result dictionary. No trace file is opened by production when the environment variable is unset.
- Machine-readable evidence: `reports/fuzz/olmkirakira_triage_T06.json` contains the rank census, every experiment's per-case outcomes, provenance, retained cluster mapping and 96 per-route byte-stat records. Its experiments omit repeated parameter arrays; seed/index/generator and the original baseline retain those inputs. All 103 reduction JSONs retain inputs and operations: 62 selected witnesses at the corpus top level, 41 other candidates under `other_reductions/` for auditing the minimum selection.

| Rank | Guard | Classic | Smart | Route refusals | AEX-success subset |
|---|---|---:|---:|---:|---:|
| 1 | `ValidateWorldPair:world-layout-unsafe` | 172 | 82 | 254 | 246 |
| 2 | `SmartPreRender:request-not-admitted` | 0 | 163 | 163 | 150 |
| 3 | `Render:tuple-layout-source` | 128 | 0 | 128 | 123 |
| 4 | `SmartRender:tuple-or-source` | 0 | 55 | 55 | 55 |

- The denominator is **route refusals**, not distinct frames: 300 inputs yield 600 routes. All 254 layout hits have row padding not divisible by the pixel type's alignment (136 PF16, 118 PF32). The allocations/spans and parameter values are valid for this fuzz contract; whether native AE supplies these byte strides remains unverified. This does not establish an AEX odd-stride contract: its input is packed.
- All 163 request hits have width <9 or height <7. The source's generic geometry minimum is 9×7. Removing only that return leaves 5×3 request normalization and then hits `checkout-geometry` in all 163 cases: **no usable fall-through path** for those requests. These are production geometry refusals, not adapter error 710.
- Disabling only alignment moves Classic's 172 layout refusals to tuple admission: all 300 Classic cases then hit `tuple-layout-source`. Smart records 163 request refusals, 136 tuple refusals and one historical 5×3 layout refusal (index 66, PF32, input/output padding 1/1).

Gate-off experiments used only a generated scratch translation unit, `-DOLM_KIRA_TRIAGE_GATE_OFF=1`, and the normal public host. `tuples` bypasses the two final tuple/source guards; `request` bypasses the Smart request return; `layout` bypasses only typed alignment, retaining null/span/format checks; `all` combines those three. The production source has no gate-off switch. Helper fallbacks and arithmetic were not changed.

Each row below covers the same 300 seed-1 cases. All use `--jobs 2`. E/M/R/U are exact/mismatch/refusal/uncompared. Crash excludes sanitizer-classified aborts so columns are disjoint. A dash means that build did not enable sanitizers.

| Scratch experiment | Route | Exact | Mismatch | Refusal | Uncompared | Other crash | Sanitizer error |
|---|---|---:|---:|---:|---:|---:|---:|
| tuples | classic | 74 | 49 | 172 | 5 | 0 | — |
| tuples | smart | 32 | 23 | 245 | 0 | 0 | — |
| request | classic | 0 | 0 | 300 | 0 | 0 | — |
| request | smart | 0 | 0 | 300 | 0 | 0 | — |
| layout | classic | 0 | 0 | 300 | 0 | 0 | — |
| layout | smart | 0 | 0 | 300 | 0 | 0 | — |
| all | classic | 184 | 103 | 0 | 13 | 0 | — |
| all | smart | 84 | 52 | 164 | 0 | 0 | — |
| all + ASan/UBSan | classic | 121 | 72 | 0 | 11 | 0 | 96 |
| all + ASan/UBSan | smart | 51 | 31 | 164 | 0 | 0 | 54 |

- Tuple bypass unblocks 128 Classic cases (74 exact, 49 mismatch, 5 uncompared) and 55 Smart cases (32 exact, 23 mismatch). Alignment or request bypass alone unblocks no outputs. Combined bypass unblocks all 300 Classic cases and 136 Smart cases; 163 Smart cases reach `checkout-geometry`, and index 66 reaches `world-layout`.
- ASan/UBSan was run with `-fsanitize=address,undefined -fno-sanitize-recover=all`; leak detection was disabled. All 150 errors are UBSan reference binding to misaligned `PF_Pixel16` / `PF_PixelFloat` in `ReadPixels`, source line 631 (scratch line 632). Classic: 58 PF16 / 38 PF32; Smart: 32 PF16 / 22 PF32. All exit by signal 6 (`returncode=-6`). No separate ASan finding or unexplained crash was observed before these fail-fast stops; later accesses are not certified clean.
- First sanitizer witness: seed 1 index 3, 39×45, PF16; `ReadPixels` binds a typed reference requiring 2-byte alignment. The guard works in production; this is evidence that admission cannot be widened without addressing typed IO. All completed sanitized outputs have the same hash as the ordinary gate-off build: Classic 204/204, Smart 82/82.
- First original gate-off pixel mismatch: seed 1 index 0, 21×19, PF8, Classic (also Smart). 1,426/1,596 bytes differ; first byte 4 = pixel (1,0), alpha, AEX `40`, Mac `00`. This is an observed output boundary, not an inferred upstream cause.
- Original AEX rejects: indices 28,56,100,103,121,124,206,228,246,248,270 report OpenCV 4.5.5 `cv::resize`, `inv_scale_x > 0`. Indices 57 and 117 report `IwException@ipp` at caller `0x18125ef13` outside the worker's supported selector-abort contract. None supplies a comparable reference output. Native Windows rejection behavior remains unverified.

The cluster table uses the combined experiment as the canonical signature set: 103 mismatching original cases, 62 signatures. Isolated/sanitized campaigns ran without shrinking; their differently grouped signatures are not additional root causes. Each selected witness minimizes measured pixel area, then compressed input size, then index among saved reductions for its signature. Shrinking was bounded to 24 attempts / 8 seconds, not a proof of global minimality. All 103 mismatch cases retained a corpus file; no representative is missing.

`U` = **unexplained processing**, per the compatibility plan. Every row has a successful AEX reference and a reproduced output mismatch, but no paired intermediate AEX/Mac trace for that input. The Mac exposes src/glow/prequantized diagnostic points; the retained public session worker exposes only final raw output. Therefore no first differing internal stage is claimed. The original AEX worker was not rebuilt. Do not upgrade a signature or nearby source comment into a proven cause.

Signatures are `[raw-output, nondefault parameter slots, depth]`; depth/slots are shown below. C/S means Classic/Smart. When both routes mismatch, their raw hashes are identical, so one statistics row covers both. Channel counts are **differing samples** in A/R/G/B order; bytes are differing bytes / total bytes. Δ is maximum absolute typed-sample difference (PF16 remains AE units, PF32 remains float units). Spatial entries give differing pixels / total pixels and the inclusive bounding box. The JSON also includes maximum byte difference, affected rows, first x/y/channel and little-endian expected/actual words. None of these selected witnesses has a nonfinite differing word.

| Cluster (original count) | Slots | Witness index; depth; geometry; routes | Bytes | Max Δ | A/R/G/B | Spatial: pixels; bbox | Class |
|---|---|---|---:|---:|---|---|---|
| C01 (1) | 1,10,16,28,40 | 37; 8; 13×9; C/S | 3/468 | 1 | 0/1/1/1 | 1/117; [0,3,0,3] | U |
| C02 (1) | 1,11,13,16,17,22,23,25,28,29,34,35,37,40 | 62; 16; 1×1; C | 8/8 | 7133 | 1/1/1/1 | 1/1; [0,0,0,0] | U |
| C03 (1) | 1,16,17,22,23,25,28,29,35,40 | 108; 16; 1×1; C | 6/8 | 8942 | 0/1/1/1 | 1/1; [0,0,0,0] | U |
| C04 (1) | 1,16,17,22,23,28,29,31,34,35,40 | 76; 16; 1×1; C | 6/8 | 15571 | 0/1/1/1 | 1/1; [0,0,0,0] | U |
| C05 (1) | 1,16,17,22,25,28,40 | 129; 8; 9×30; C/S | 958/1080 | 221 | 148/270/270/270 | 270/270; [0,0,8,29] | U |
| C06 (1) | 1,17,19,22,23,28,29,31,34,35,37,40 | 61; 8; 1×1; C | 3/4 | 189 | 0/1/1/1 | 1/1; [0,0,0,0] | U |
| C07 (1) | 1,22,23,28,40 | 288; 16; 9×8; C/S | 498/576 | 28957 | 33/72/72/72 | 72/72; [0,0,8,7] | U |
| C08 (1) | 1,22,25,28,40 | 187; 32; 1×1; C | 11/16 | 0.2689761370420456 | 0/1/1/1 | 1/1; [0,0,0,0] | U |
| C09 (1) | 1,22,28,34,40 | 41; 8; 10×7; C/S | 232/280 | 212 | 22/70/70/70 | 70/70; [0,0,9,6] | U |
| C10 (1) | 1,22,28,37,40 | 208; 8; 14×19; C/S | 919/1064 | 217 | 121/266/266/266 | 266/266; [0,0,13,18] | U |
| C11 (1) | 1,28,29,40 | 54; 16; 7×1; C | 6/56 | 1 | 0/1/1/1 | 1/7; [0,0,0,0] | U |
| C12 (1) | 1,35,40 | 73; 8; 1×1; C | 4/4 | 95 | 1/1/1/1 | 1/1; [0,0,0,0] | U |
| C13 (1) | 1,4,5,6,7,8,9,10,11,13,16,17,19,22,23,25,28,29,31,34,35,40 | 214; 16; 17×11; C/S | 308/1496 | 21888 | 0/24/27/104 | 131/187; [0,0,16,10] | U |
| C14 (1) | 1,40 | 136; 16; 1×2; C | 16/16 | 31244 | 2/2/2/2 | 2/2; [0,0,0,1] | U |
| C15 (1) | 1,40 | 262; 32; 1×1; C | 13/16 | 0.4578406289219856 | 1/1/1/1 | 1/1; [0,0,0,0] | U |
| C16 (1) | 1,7,8,9,10,11,16,17,19,22,23,28,29,31,34,35,37,40 | 52; 32; 1×1; C | 8/16 | 1.0 | 1/1/1/1 | 1/1; [0,0,0,0] | U |
| C17 (1) | 10,16,19,22,28,40 | 191; 16; 12×24; C/S | 1/2304 | 1 | 0/0/0/1 | 1/288; [3,12,3,12] | U |
| C18 (1) | 10,16,22,28,40 | 230; 16; 14×14; C/S | 1/1568 | 1 | 0/0/0/1 | 1/196; [1,7,1,7] | U |
| C19 (1) | 10,16,22,28 | 97; 16; 13×22; C/S | 14/2288 | 1 | 0/2/3/2 | 4/286; [2,3,12,17] | U |
| C20 (1) | 10,34,35 | 13; 16; 24×17; C/S | 1/3264 | 1 | 0/1/0/0 | 1/408; [20,8,20,8] | U |
| C21 (1) | 16,22,28,40 | 252; 16; 15×23; C/S | 1/2760 | 1 | 0/0/1/0 | 1/345; [2,4,2,4] | U |
| C22 (1) | 16,28 | 268; 16; 32×29; C/S | 1/7424 | 1 | 0/0/1/0 | 1/928; [25,1,25,1] | U |
| C23 (3) | 1 | 157; 16; 1×1; C | 8/8 | 9709 | 1/1/1/1 | 1/1; [0,0,0,0] | U |
| C24 (3) | 1 | 19; 8; 1×1; C | 2/4 | 76 | 0/0/1/1 | 1/1; [0,0,0,0] | U |
| C25 (1) | 2,10,11,13,16,17,22,23,25,28,29,31,34,35,40 | 235; 16; 3×1; C | 24/24 | 32510 | 3/3/3/3 | 3/3; [0,0,2,0] | U |
| C26 (1) | 2,11,13,16,17,22,23,25,28,29,34,35,40 | 48; 8; 1×1; C | 3/4 | 127 | 0/1/1/1 | 1/1; [0,0,0,0] | U |
| C27 (1) | 2,34,40 | 59; 32; 1×1; C | 6/16 | 0.041938066482543945 | 0/1/0/1 | 1/1; [0,0,0,0] | U |
| C28 (1) | 22,28,40 | 3; 16; 39×45; C/S | 1/14040 | 1 | 0/0/0/1 | 1/1755; [16,22,16,22] | U |
| C29 (1) | 29 | 122; 16; 11×23; C/S | 1/2024 | 1 | 0/0/0/1 | 1/253; [10,10,10,10] | U |
| C30 (1) | 2 | 210; 16; 1×1; C | 2/8 | 6054 | 0/1/0/0 | 1/1; [0,0,0,0] | U |
| C31 (1) | 2 | 23; 32; 1×1; C | 4/16 | 0.5093041360378265 | 0/1/0/0 | 1/1; [0,0,0,0] | U |
| C32 (1) | 2 | 232; 8; 1×1; C | 3/4 | 130 | 0/1/1/1 | 1/1; [0,0,0,0] | U |
| C33 (1) | 4,16,17,22,23,28,40 | 272; 32; 16×31; C/S | 1124/7936 | 0.49228304624557495 | 71/108/117/79 | 259/496; [0,0,15,30] | U |
| C34 (1) | 4,22,25,28,29,40 | 0; 8; 10×9; C/S | 259/360 | 171 | 53/74/64/68 | 88/90; [0,0,9,8] | U |
| C35 (2) | 4,22,28,31,40 | 176; 8; 13×10; C/S | 417/520 | 187 | 101/106/105/105 | 129/130; [0,0,12,9] | U |
| C36 (1) | 4,22,28,40 | 193; 16; 12×8; C/S | 558/768 | 24160 | 69/67/76/70 | 96/96; [0,0,11,7] | U |
| C37 (1) | 4,28,29,40 | 218; 16; 12×20; C/S | 1055/1920 | 14388 | 122/148/132/128 | 236/240; [0,0,11,19] | U |
| C38 (1) | 4,5,6,7,8,9,10,11,13,16,17,22,23,28,29,31,34,35,37 | 215; 32; 4×5; C | 24/320 | 0.09578990936279297 | 0/0/8/0 | 8/20; [0,0,3,4] | U |
| C39 (1) | 4,7,8,9,10,11,16,17,22,23,25,28,29,31,35,37,40 | 282; 16; 9×11; C/S | 616/792 | 31895 | 73/79/79/79 | 79/99; [0,0,8,10] | U |
| C40 (1) | 5,6,8,9,10,11,16,17,19,22,23,25,28,29,31,34,35 | 280; 32; 3×1; C | 3/48 | 1.1920928955078125e-07 | 0/1/1/1 | 1/3; [2,0,2,0] | U |
| C41 (1) | 6,10,16,22,28,34 | 81; 8; 14×14; C/S | 9/784 | 1 | 0/3/3/3 | 3/196; [1,1,13,9] | U |
| C42 (1) | 6,10,16,22,28,40 | 142; 16; 10×31; C/S | 30/2480 | 1 | 0/5/5/5 | 5/310; [3,6,9,30] | U |
| C43 (1) | 6,10,16,22,40 | 182; 32; 10×16; C/S | 3/2560 | 5.960464477539063e-08 | 1/0/0/0 | 1/160; [8,0,8,0] | U |
| C44 (1) | 6,10,22,28,40 | 160; 8; 11×21; C/S | 12/924 | 1 | 0/4/4/4 | 4/231; [3,5,6,14] | U |
| C45 (1) | 6,16,22,28 | 260; 16; 16×26; C/S | 26/3328 | 1 | 0/4/5/4 | 9/416; [6,1,15,22] | U |
| C46 (1) | 6,22,28,29,40 | 29; 16; 11×21; C/S | 1/1848 | 1 | 0/0/1/0 | 1/231; [8,11,8,11] | U |
| C47 (2) | 6,22,28,40 | 24; 32; 12×8; C/S | 8/1536 | 1.1920928955078125e-07 | 1/1/2/4 | 4/96; [0,4,4,7] | U |
| C48 (1) | 6,28,34,40 | 89; 32; 17×21; C/S | 14/5712 | 1.0 | 1/2/1/1 | 2/357; [0,19,0,20] | U |
| C49 (1) | 6,7,8,9,10,11,13,16,17,22,23,25,28,29,31,34,35,37,40 | 45; 8; 14×20; C/S | 371/1120 | 6 | 0/5/200/166 | 214/280; [0,0,13,19] | U |
| C50 (1) | 6,7,8,9,10,11,13,16,17,22,23,28,29,35,37,40 | 7; 32; 11×12; C/S | 63/2112 | 1.1920928955078125e-07 | 0/26/24/13 | 45/132; [0,0,10,11] | U |
| C51 (1) | 6,7,8,9,10,11,16,17,19,22,23,25,28,29,31,35,37,40 | 77; 8; 9×9; C/S | 21/324 | 1 | 0/8/7/6 | 15/81; [1,0,8,8] | U |
| C52 (1) | 7,8,9,10,11,13,16,17,22,23,25,28,29,31,35,40 | 125; 32; 10×16; C/S | 267/2560 | 1.1920928955078125e-07 | 106/48/59/52 | 106/160; [0,0,9,15] | U |
| C53 (1) | 8,10,16,22,23,28,40 | 42; 8; 1×8; C | 1/32 | 1 | 0/0/0/1 | 1/8; [0,6,0,6] | U |
| C54 (1) | 8,10,16,22,28,34 | 104; 8; 16×31; C/S | 108/1984 | 1 | 0/36/37/35 | 49/496; [0,0,15,23] | U |
| C55 (1) | 8,10,16,28,40 | 115; 16; 26×11; C/S | 60/2288 | 1 | 0/10/10/10 | 10/286; [1,1,23,10] | U |
| C56 (1) | 9,10,13,16,17,22,23,25,28,29,35,37,40 | 39; 32; 1×1; C | 2/16 | 5.960464477539063e-08 | 1/0/0/1 | 1/1; [0,0,0,0] | U |
| C57 (1) | 9,10,16,22,28 | 251; 16; 5×1; C | 1/40 | 1 | 0/0/1/0 | 1/5; [4,0,4,0] | U |
| C58 (1) | 9,22,28 | 281; 32; 1×3; C | 2/48 | 5.960464477539063e-08 | 1/0/0/1 | 1/3; [0,1,0,1] | U |
| C59 (1) | 9 | 165; 32; 1×1; C | 3/16 | 1.1920928955078125e-07 | 1/0/1/1 | 1/1; [0,0,0,0] | U |
| C60 (16) | default | 148; 16; 9×1; C | 8/72 | 335 | 0/2/0/2 | 2/9; [0,0,8,0] | U |
| C61 (7) | default | 116; 32; 3×3; C | 26/144 | 0.4048241674900055 | 1/3/3/1 | 3/9; [0,0,0,2] | U |
| C62 (15) | default | 78; 8; 1×9; C | 36/36 | 22 | 9/9/9/9 | 9/9; [0,0,0,8] | U |

Additional classification boundaries:

| Evidence family | Plan classification | What is established / what remains |
|---|---|---|
| 150 gate-off UBSan aborts | Port implementation limitation, demonstrated only in expanded experimental domain | Misaligned typed read is proven. Production refuses it; native AE stride legality and later writer safety still need verification. |
| 163 request-gate hits | Host/settings; unsupported geometry path | Removal alone reaches checkout geometry failure, not rendering. Full-frame predata/request handling must be implemented and compared. |
| 11 resize assertions | Windows dependency boundary; reference output unavailable | Original OpenCV assertion is observed; native AE behavior and intended tiny approximated-input semantics are unverified. |
| 2 IPP exceptions | Comparator/reference boundary | Worker explicitly cannot represent this exception/selector contract. Do not score absent output as a Mac mismatch. |
| Untested native AE, custom ramps, ROI/downsample, Mode 4 | Unverified | Fuzz samples the captured public Blur Mode range 1..3; no promotion to other domains. |

Provenance:
- Original AEX SHA-256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Worker: `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. This is the same prebuilt binary as T04; no rebuild or external source modification.
- Pre-tracing source SHA-256 `f6e8d1759479f21206c8741df60457d976fca16de25c228b4e3eb13f9fbd80da` matches both the baseline and this worktree's starting source.
- Traced production source SHA-256 `5fd4818b4dec04fd14468fd986ded9498a765290923ddfec71e417faf7f52e14`.
- Combined scratch source SHA-256 `0edb71c3ab470e9a6f3c3960ee1e6d5bba435b7c9a6fc56f618e18db51016695`; original combined candidate SHA-256 `1ac1e99e6e802b828aefefb8ea2db5fcd912efe503d459e5286995de8dc1d2f3`. Individual candidate/source manifests and extra core-header hashes are in the JSON.
- Host: original AEX Unicorn CPU Smart versus production EffectMain Classic/Smart fake SDK host; full frame, origin 0, downsample 1:1, time 0/24 step 1, ARGB, no color conversion. AEX uses packed rows, Mac uses the recorded padding. Native Windows UCRT/AE equivalence is not claimed.
- The first experiment-driver attempt produced 300 Python framework errors (`RecursionError`), not plugin results: monkeypatching Adapter affected `super(Adapter, traced)`. Fixed by explicitly calling `PublicAdapter.candidate`; failed scratch artifacts are `failed-driver.*` and excluded from all numerical tables.
- `TMPDIR`/`TMP`/`TEMP` point inside ticket scratch for builds/runs. Scratch remained below 5 GiB; runner temporary build directories were removed. No `/tmp` writes, MAIN changes, other-plugin edits, release-gate/ledger changes, push or history rewrite.

inference:
- The tuple whitelist is a substantial coverage barrier, but its removal exposes real numerical residuals even with aligned storage; the 49/23 isolated tuple mismatches establish this separately from alignment.
- Alignment is a safety requirement of the current typed-access implementation. Ordinary-build exact bytes on unaligned inputs do not establish safe C++ execution.
- C60–C62 cover 38 original cases reduced to legal sampled defaults (gain is clamped to 1 by the generator, unlike the builder's out-of-range 0.1 default). This is a useful controlled starting family, not evidence of a shared root cause.
- Tiny Mode-3 witnesses may exercise the existing helper's `return input` fallback when its geometry is unadmitted. That is a source-backed candidate explanation, not a paired-stage proof. AEX/OpenCV/UCRT numerical causes remain open until traced.
- This ticket completes residual triage. It does not make the plugin generally compatible or authorize promoting the scratch bypass.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp` — optional refusal trace only.
- `tools/fuzz/adapters/olmkirakira.py` — route-local trace capture.
- `tools/fuzz/triage_kirakira.py` — scratch-only switch/sanitizer driver and detailed diff collector.
- `tools/fuzz/kirakira_triage_summary.py` — deterministic census/selection/evidence summary.
- `reports/fuzz/olmkirakira_triage_T06.json` — measured evidence.
- `tests/fuzz_corpus/olmkirakira/README.md` and eight `refusal_seed1_*.json` files — baseline neutrality fixtures.
- `tests/fuzz_corpus/olmkirakira_gate_off_T06/README.md` and 103 JSON files (62 selected, 41 other reductions) — experimental mismatch evidence.
- `orchestra/reports/T06-triage-kirakira.md`.

verify:
Run from this worktree. Commands below use only ticket scratch and the fixed existing worker. All fuzz invocations use `--jobs 2`.

```sh
export OLM_AEX_WORKER='/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker'
scratch="$PWD/orchestra/state/T06-triage-kirakira"
mkdir -p "$scratch"
export TMPDIR="$scratch" TMP="$scratch" TEMP="$scratch" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$scratch" --report "$scratch/verify-replay.json" > "$scratch/verify-replay.log" 2>&1
python3 tools/fuzz/triage_kirakira.py --experiment all --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$scratch" --report "$scratch/verify-clusters.json" --details "$scratch/verify-details.json" > "$scratch/verify-clusters.log" 2>&1
python3 tools/fuzz/test_framework.py > "$scratch/verify-framework.log" 2>&1
```
Expected: replay complete, 8/8 and 62/62 `matches_saved`; framework 8 tests, 7 pass / 1 integration skip. These were actually run with report names `replay.json` / `cluster-replay.json` and log `framework-tests.log`.

Full campaign reproduction (each command was run with these numerical options; execute sequentially):

```sh
python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch "$scratch" --report "$scratch/census.json" --corpus "$scratch/census-corpus" > "$scratch/census.log" 2>&1
python3 tools/fuzz/triage_kirakira.py --experiment all --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 24 --shrink-seconds 8 --scratch "$scratch" --report "$scratch/gate-all.json" --corpus "$scratch/gate-corpus" > "$scratch/gate-all.log" 2>&1
for variant in tuples request layout; do
  python3 tools/fuzz/triage_kirakira.py --experiment "$variant" --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$scratch" --report "$scratch/gate-$variant.json" --corpus "$scratch/$variant-corpus" > "$scratch/gate-$variant.log" 2>&1
done
python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$scratch" --report "$scratch/gate-sanitizers.json" --corpus "$scratch/sanitizer-corpus" > "$scratch/gate-sanitizers.log" 2>&1
python3 tools/fuzz/kirakira_triage_summary.py --state "$scratch" --output "$scratch/verify-summary.json"
```
Expected campaign totals: the guard and gate-off tables above; no framework errors. Full regeneration can choose different reductions/signatures at the wall-time shrinking boundary; the committed 62-witness replay is the deterministic equality check. Summary includes cluster details when `cluster-details.json` exists; use `--details "$scratch/cluster-details.json"` on the committed witness replay to regenerate those exact per-input statistics. The source/worker/AEX/output hashes are authority, not temporary executable path or elapsed time.

next:
Proposed follow-up tickets (evidence motivates investigation; no numerical cause is assumed):
- **KIRA-F01 — typed row IO and stride contract:** replace unsafe typed accesses only after establishing the intended host contract; 254 production layout refusals and 150 gate-off UBSan aborts at `ReadPixels` are the witnesses. Recheck both input and output paths under sanitizers.
- **KIRA-F02 — tiny full-frame Smart owner:** implement consistent request/predata/checkout geometry; 163 request hits (150 AEX successes) become 163 checkout-geometry failures when the gate alone is removed. Keep ROI/tile behavior separate.
- **KIRA-F03 — legal-default Mode-2 stage census:** trace seed → directional rays → aggregation → compose for C60–C62 (38 original cases), starting with indices 148/116/78; max typed deltas 335 / 0.4048241674900055 / 22 remain.
- **KIRA-F04 — Channel selection leaf:** compare AEX seed construction for C23/C24, one changed slot on 1×1 PF16/PF8 (indices 157/19, max deltas 9709/76); isolate channel semantics before touching blur or quantization.
- **KIRA-F05 — tiny Mode-3 Gaussian path:** compare C30–C32, single changed Blur Mode on 1×1 at all depths (indices 210/23/232); test the source's unadmitted-geometry identity fallback against the actual AEX branch.
- **KIRA-F06 — PF16 one-unit pipeline boundaries:** obtain paired intermediate values for C22 and C29 (indices 268/122); each has one differing byte/sample and maximum delta 1, with ray lengths or ray color as the remaining nondefault slots. Do not apply a final-byte correction.
- **KIRA-F07 — PF32 source-opacity operation order:** use C59, index 165, 1×1, only Source Opacity nondefault; max delta 1.1920928955078125e-07. Trace the actual getter/compose sequence before assigning a port or dependency cause.
- **KIRA-F08 — paired stage transport for remaining mixtures:** add/read AEX seed/ray/compose witnesses for the other U rows, preserving public builder provenance; Mac-only debug points cannot identify the first divergent stage. Split resulting fix tickets at the first observed boundary.
- **KIRA-F09 — original-AEX tiny resize/IPP rejection contract:** investigate the 11 resize assertions and 2 unsupported IPP exception aborts independently of pixel differences; confirm native Windows/AE outcomes before widening or matching Mac rejection behavior.
- **KIRA-F10 — evidence-backed tuple admission:** after the preceding causes are resolved, promote only proven general rules; tuple-only bypass currently gives 74/32 exact but 49/23 mismatches (Classic/Smart), so a wholesale guard removal is not supported.
