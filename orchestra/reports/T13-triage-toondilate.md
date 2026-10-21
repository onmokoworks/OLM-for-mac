status: done

summary:
- Added behavior-neutral refusal tracing; fresh paired campaign has zero refused legal cases, so no gate bypass applies.
- Smart remains 277 exact / 23 mismatch; Classic is 300 verified no-write results. All 300 original corpus records retain `matches_saved`.
- The historical three clusters reduce to one live PF32 signature cluster. All 23 reduced mismatches first differ at seed initialization.
- Original AEX accepts alpha equal to 1 or unordered NaN as seeds; Mac accepts alpha >= 1. A scratch-only predicate experiment makes all 300 Smart cases exact.
- Sanitized production: 600 unchanged route outputs; sanitized experiment: 300 exact Smart outputs; zero sanitizer errors. No production numerical change.

facts:

Base `58ef618832837adb0f46f016b27a114d7f146df9`, branch `orch/T13-triage-toondilate`. Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the ToonDilate ledger decision row, the plan's classification table, F17/F18, T04's ToonDilate section, and the T03/T05 refusal experiments. Smart is the F18 capability-selected AE target; Classic is a forced diagnostic route. MAIN, original AEX files, emulator sources, release gates, and ledger were read-only. No installation, push, history rewrite, or `/tmp` scratch.

**Refusal attribution and neutrality.** `OLM_TOON_ERROR` tags 44 existing local error sites with `function:tag@line` through `OLM_REFUSAL_TRACE`. File I/O occurs only on an error; the helper preserves errno and returns the original error. Propagated host callback errors remain unchanged. The test-only bitdepth seam remains uninstrumented. The adapter returns attribution outside the comparison result, following T03's established third tuple member.

Seed 1, n 300, jobs 2, full-frame origin-zero 1:1 raw ARGB: both original routes succeeded 300/300; Smart 277 exact / 23 mismatch / 0 refusal; Classic 300 no-write. Campaign elapsed 32.8118 seconds. All 300 original Smart oracle and candidate result dictionaries equal T04's historical report, including hashes and differences. All 300 saved corpus records replay with `matches_saved=true`, elapsed 31.2233 seconds. No saved expectations were changed. A mechanical source check removes only the trace includes/helper/wrappers and reproduces the base source byte-for-byte.

Ranked guard table:

| Rank | Guard | Smart refused legal cases | Classic refused legal cases |
|---|---|---:|---:|
| — | None fired | 0 / 300 | 0 / 300 |

Positive instrumentation control: out-of-range Search Radius 101 produces `SmartPreRender:prerender-radius`, error 516. Trace on/off results and raw bytes agree; an unopenable trace path preserves the same result. This is an **illegal parameter control**, excluded from the legal refusal census.

Gate-off table:

| Population / guard | Eligible refused cases | Unblocked exact | Unblocked mismatch | Crash | Sanitizer error | Finding |
|---|---:|---:|---:|---:|---:|---|
| Top guards in the legal campaign | 0 | N/A | N/A | N/A | N/A | No top guard exists to disable |
| Production sanitizer control, both routes | Already admitted 600 | 277 Smart exact + 300 Classic no-write | 23 Smart mismatch | 0 | 0 | All 600 output hashes unchanged |

The generic Smart implementation already renders every legal input in this campaign. Removing a safety guard would not unblock a residual case. No bypass switch was added to production. The N/A cells are **not** unperformed experiments reported as zero failures.

**Original Classic verification.** The fresh matching Classic AEX command leaves all 300 initially zero destinations zero; the Mac command preserves all 300 initially `0xee` destinations. This agrees with the original static dispatch: `entry_point`, case `0xb`, calls `FUN_1801a7840`, whose body is a constant-zero return. MAIN's `decomp/OLMToonDilate.aex.c.txt` lines 476765–476772 and 480028–480031 contain those bodies. The existing original-AEX sequence probe also documents nonzero destination preservation. The new campaign measures final buffer preservation, not absence of transient stores. No Classic numeric-output fix is indicated.

**Cluster classification.** Signatures use `[first stage, non-default slots, depth]`; they are grouping aids, not root causes. F17 retained the old records while correcting their route oracles. Smallest means minimum retained pixel count, then lowest seed-1 index; greedy reduction is not a proof of global minimality.

| Historical signature | Historical cases | Smallest saved case | Paired smallest-case result / byte difference | Current Smart residual | Plan classification |
|---|---:|---|---|---:|---|
| `["raw-output",[],8]` | 91 | index 0, 1×1, radius 2 | Classic no-write; Smart exact, 0 bytes, max 0, no channel/spatial difference | 0 | Comparator/reference problem, already corrected by F17 |
| `["raw-output",[],16]` | 114 | index 1, 1×1, radius 2 | Classic no-write; Smart exact, 0 bytes, max 0, no channel/spatial difference | 0 | Comparator/reference problem, already corrected by F17 |
| `["raw-output",[],32]` | 95 | index 2, 1×1, radius 2 | Classic no-write; Smart exact, 0 bytes, max 0, no channel/spatial difference | 23 | Mixed historical comparator artifact and actual port bug; see live witnesses below |

Fresh pairing-aware reduction produces **one** live cluster, `["raw-output",[],32]`, with 23 failures: 10 HDR, 8 signed, 5 nonfinite. All 23 reductions are retained separately in `tests/fuzz_corpus/olmtoondilate_T13/`; the original 300 files are untouched. The smallest live witness is index 17, 1×2, radius 2. Smallest per-profile witnesses:

| Profile / cases | Index / geometry | First differing stage, AEX → Mac | Final byte / word differences | Max absolute byte difference | Channels / spatial pattern | Classification |
|---|---|---|---|---:|---|---|
| HDR / 10 | 46 / 1×2 | seed 0, alpha bytes `0ba5fb40`: `ffffffff` → `00000000` distance | 13 / 4; first byte 16, alpha `0000003f` → `0ba5fb40` | 251 | A,R,G,B; lower pixel (0,1) replaced by upper pixel | Port bug |
| signed / 8 | 220 / 1×2 | seed 1, alpha bytes `78ca4840`: `ffffffff` → `00000000` distance | 16 / 4; first byte 0, alpha `0000003f` → `78ca4840` | 243 | A,R,G,B; upper pixel (0,0) replaced by lower pixel | Port bug |
| nonfinite / 5 | 17 / 1×2 | seed 0, alpha bytes `462381ff`: `00000000` → `ffffffff` distance | 15 / 4; first byte 16, alpha `462381ff` → `d60c383e` | 193 | A,R,G,B; AEX propagates upper pixel to (0,1), Mac leaves input | Port bug |

Bytes above are little-endian. Maximum absolute **finite sample** differences are respectively 7.36389684677124, 2.9086236357688904, and 0.6172374486923218. The nonfinite witness additionally has two differing nonfinite sample pairs, for which a finite numeric max is not defined; byte/word comparisons still use strict equality. Full raw hashes, small witness bytes, channel counts, coordinates, and seed maps for all 23 cases are in `reports/fuzz/olmtoondilate_T13_triage.json`.

First unreduced mismatch remains seed 1/index 15, PF32 signed, 9×19: 908 different bytes / 240 words; first byte 128, first word 32, original `0000803f`, Mac `dabfd93f`.

**Paired stage evidence.** Existing public adapters expose final output only; the older copy-boundary fixtures provide the worker ABI/suite machinery used for this focused capture. The committed diagnostic runner executes the real original PF32 worker `0x1801a6800`, with a hook immediately before the seed-distance store at `0x1801a69a3`. It captures alpha bits and EDX. A scratch Mac source records the actual `dist` array after seed initialization and before propagation; its status and output bytes equal the production candidate for every reduced case. For **23/23** cases:

- Original worker final bytes equal the matching original public Smart output exactly.
- The worker input remains unchanged; an import-free `0x1801ac7a0` leaf verifies all five arguments, including the stack argument, by moving four distinct ARGB words to separate RGBA outputs.
- The first captured differing numerical stage is seed initialization. Original constant `0x1803118a8` is `0000803f` (1.0f).
- Static instructions `0x1801a698e UCOMISS XMM0,XMM6` and `0x1801a6991 CMOVZ EDX,EBX` match the captured finite-equality / unordered behavior. Mac's existing `ToonPixelTraits<PF_PixelFloat>::opaque` is `p.alpha >= 1.0f`.

**Cause experiment, scratch only.** A generated source adds an undefined-by-default `OLM_TOON_EXPERIMENT_SEED` branch around that predicate. The experiment build alone defines it and uses `alpha == 1.0f || std::isnan(alpha)`. No coordinates, expected samples, output-byte corrections, or fixture-specific cases are used. Both production and experiment are compiled with ASan/UBSan, `-fno-fast-math`, `-ffp-contract=off`, abort-on-error, and leak checking disabled:

| Build | Measured renders | Exact Smart | Mismatch Smart | Classic no-write | Process errors | Sanitizer errors |
|---|---:|---:|---:|---:|---:|---:|
| Production sanitizer | 600 | 277 | 23 | 300 | 0 | 0 |
| Scratch seed predicate experiment | 300 | 300 | 0 | Not run | 0 | 0 |

All 277 previously exact Smart hashes remain exact; all 23 residual hashes now equal the AEX. This is cause-localization evidence, not a production fix or an all-input proof. Diagnostic setup corrections converted a Python `bytearray` header to `bytes` for Unicorn and resolved a relative corpus path before reporting. These were harness serialization/path failures, not numerical hypothesis failures. No numerical hypothesis was refuted.

Identity: original AEX SHA256 `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3`; indexed prebuilt worker SHA256 `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`; traced production source SHA256 `7d0d63cb807bc31cd917a01361419248e7939d4f0e43fd84ef951cd50c653c4a`. Source transformations, source/candidate hashes, adapter dependencies, and raw output identities are bound in the committed JSON. Diagnostic builds are removed automatically. Remaining scratch is below 5 MiB; `git diff --check` passes.

inference:
- The 23 measured residuals share one cause: PF32 seed eligibility differs from the original's machine comparison, including unordered NaNs. The seed maps and scratch experiment support **port implementation difference**, not Windows-library, host, or comparator classification for these Smart cases.
- HDR and signed profile labels do not independently imply different defects: both expose finite alpha > 1 becoming a false Mac seed. Nonfinite inputs expose NaNs becoming missing Mac seeds (and can also contain infinity).
- The three historical clusters must not become three numerical fix tickets. Integer clusters are already resolved comparator artifacts; the live PF32 cluster yields one general predicate ticket.
- These observations cover a finite CPU emulation/fake-host population. Native AE, native Windows exception modes, all NaN payloads, new seeds, ROI/downsample, and general compatibility remain outside this claim.

changed_files:
- `mac/OLMToonDilate/OLMToonDilate.cpp` — optional tracing only; numerical code and guard conditions unchanged.
- `tools/fuzz/adapters/olmtoondilate.py` — route-local trace capture outside compared results.
- `tools/fuzz/triage_toondilate_T13.py` — reproducible diagnostic builds, byte stats, paired seed traces, sanitizer/cause experiment, and report generation.
- `tests/fuzz_corpus/olmtoondilate_T13/*.json` — 23 pairing-aware reduced witnesses.
- `reports/fuzz/olmtoondilate_T13_triage.json` — measured evidence.
- `orchestra/reports/T13-triage-toondilate.md`.

verify:

Run from this worktree. All campaigns and diagnostic pools explicitly use jobs 2. MAIN assets and the indexed worker are read-only. Generated campaign corpus stays in scratch; the committed reduced corpus and original corpus are only replayed/read.

```sh
s="$PWD/orchestra/state/T13-triage-toondilate"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
python3 tools/fuzz/run.py --plugin olmtoondilate --n 300 --seed 1 --jobs 2 \
  --worker "$w" --scratch "$s" --report "$s/campaign.json" --corpus "$s/corpus" \
  > "$s/campaign.log" 2>&1
python3 tools/fuzz/run.py --plugin olmtoondilate --jobs 2 \
  --replay tests/fuzz_corpus/olmtoondilate --worker "$w" --scratch "$s" \
  --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" \
  tools/fuzz/triage_toondilate_T13.py --jobs 2 --scratch "$s" \
  --corpus tests/fuzz_corpus/olmtoondilate_T13 --report "$s/verify-triage.json" \
  > "$s/verify-triage.log" 2>&1
tail -1 "$s/verify-triage.log"
git diff --check
```

Expected: campaign Smart 277/23/0 and Classic 300 no-write; original corpus replay 300/300. Diagnostic output: production sanitized renders 600 / matching hashes 600 / errors 0 / sanitizer errors 0; seed experiment renders 300 / matching hashes 300 / errors 0 / sanitizer errors 0; reduced 23, seed-stage disagreements 23, guards `{}`. Script asserts all 300 historical Smart observations unchanged, all reduced public/worker/stage identities, the ABI controls, and refusal-control neutrality. Generated timestamps, build paths, and binary hashes can vary; compare behavior and bound inputs. No tolerance.

next:
- Proposed fix ticket **TD-PF32-SEED**: restore the original PF32 seed comparison (finite alpha exactly 1; unordered NaN eligible), with neighboring float/±infinity/quiet-and-signaling NaN witnesses and existing public/ROI regressions. Evidence: 23/23 paired first-stage disagreements; scratch sanitized predicate change yields 300/300 Smart exact with all 277 prior exact cases preserved. Production change requires its own review and regression closure.
- No gate-widening or Classic numerical ticket is justified by this census. Revisit refusal guards only if a new legal refused witness is found; retain the three historical cluster classifications rather than duplicating the F17 comparator repair.
