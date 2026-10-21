status: done

summary:
- Fixed ColorKeep fuzz DEEP flags to PF16 only; production admission guards remain intact.
- Pixel callbacks now copy through byte pointers into aligned locals; ROI row addressing also uses byte offsets.
- Smart seed-1 exact improves 205→300/300; all 300 Classic results and all previously rendered bytes remain unchanged.
- Final ASan/UBSan: 600 route executions clean; six existing tests and six focused AEX witnesses pass. Replays change only toward exact.

facts:

Base commit: `c736e6767627de32bdb39e30f8904ee0b1c9a3ab`, branch `orch/F19-colorkeep-host-flags-and-byte-safe`. Read AGENT_GUIDE, GOTCHAS, the compatibility plan, ColorKeep's decision/forbidden-action row, and T12/F17 evidence. MAIN, original binaries, SDK, and emulator cache were read-only. No release gate, ledger, other plugin production code, installation, push, or history rewrite changed. Scratch is ticket-local and below 5 GiB; regenerable build/corpus outputs were removed after verification.

Machine-readable evidence: `reports/fuzz/colorkeep_F19.json`. It retains every seed/input hash, complete before/after comparison dictionary, provenance, route transitions, focused witnesses, and the procedural inputs/reduction operations/results for the 100 retained shrunk cases. `tools/fuzz/verify_colorkeep_F19.py` reconstructs replay corpora without copying MAIN assets.

Hashes:

- Original AEX: `6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86`.
- Indexed worker: `/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker`, SHA256 `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c`. No rebuild.
- Before ColorKeep.cpp: `650421a70899b79c232620465859808b15e6b341c4ae710abcfab8b9e3690755`.
- Final ColorKeep.cpp: `8ee2aff5145528ffb7347f0db0760eb6aeb090c14b012b8e3cbf235f53d6cfb5`.

**Cause and boundary traces.** The fuzz host used `depth==8?0:DEEP`, while `ColorKeepValidateWorldPair` requires DEEP only at 16bpc. Seed 1 index 2 (10×19 PF32, input/output padding 7/5) traces `ColorKeepValidateWorldPair:world-flags-or-bounds@216`, error 516. Its callback counts were `1 1 1 1 0 0`: pixel checkout/checkin occurred, palette checkout/render did not. With the corrected host and unchanged guards, counts become `1 1 1 1 2 2`, error 0, and output equals original Smart AEX SHA256 `50d4555aa1eca427fec7389deeec4fa71dd659408bcb26578c78213a7b3fe72c`.

Seed 1 index 3 is 39×45 PF16, padding 1/11. Its first reported default UB is the typed member access in ColorKeep16Func (old line 276). Both before and after bytes equal AEX SHA256 `b4a11f9a7c35a8fec8105586d62164975aef84bd366c40b7bf50d59efca7852f`. Host-corrected pre-fix sanitizer replay reports 83 PF16 and 65 PF32 Smart UB cases, all alignment diagnostics; Classic has 83. This reproduces T12's 83 default plus 65 newly reachable cases.

Static check used MAIN's `decomp/ColorKeep.aex.c.txt` functions `180001280` (PF16), `180001580` (PF8), and `180001850` (PF32), plus `disasm/ColorKeep.aex.asm.txt`. At `180001a48..180001a5f`, the float worker copies original RGB words with integer MOVs; `180001a64..180001a7f` copies original alpha on match or stores positive zero. Ordered rejection is preserved, including unordered NaN fall-through. This fix changes memory access only; it retains comparisons, constants, palette order, admission, staging, and checkout/checkin behavior. The public worker exposes final raw output, not paired numerical intermediate planes; the traces here locate the admission and memory-access boundaries, not an invented numerical intermediate mismatch.

An initial prototype passed typed pointers directly to memcpy. Its sanitized campaign still aborted in 83 Classic/148 Smart cases: first PF32 diagnostic at new line 303 was `load of misaligned address ... for type 'PF_PixelFloat *', which requires 4 byte alignment`. Explicit byte-pointer casts at the copy boundary eliminated that diagnostic; the four-case probe then passed before the full final rerun. No sanitizer suppression or disabled alignment check was used.

**Campaigns actually run.** With `s="$PWD/orchestra/state/F19-colorkeep-host-flags-and-byte-safe"` and `w` set to the worker above:

```sh
# Before edits, then again with final source (replace before with final).
python3 tools/fuzz/run.py --plugin colorkeep --n 300 --seed 1 --jobs 2 \
  --worker "$w" --scratch "$s/before" --report "$s/before.json" \
  --corpus "$s/before-corpus" > "$s/before.log" 2>&1

# Before production edits: corrected host only, recoverable sanitizer census.
OLM_COLOR_TRIAGE_HOST_FLAGS=1 OLM_COLOR_TRIAGE_SANITIZE=1 \
ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=halt_on_error=0 \
python3 tools/fuzz/run.py --plugin colorkeep --n 300 --seed 1 --jobs 2 \
  --shrink-attempts 0 --worker "$w" --scratch "$s/host-before-sanitize" \
  --report "$s/host-before-sanitize.json" --corpus "$s/host-before-sanitize-corpus" \
  > "$s/host-before-sanitize.log" 2>&1
```

Both normal campaigns completed with 300 successful Classic and 300 successful Smart AEX sessions. The default shrink budget was retained for the required normal runs. No comparison borrows another route's reference.

| Route | Before exact / mismatch / refusal | Final exact / mismatch / refusal | Exact change |
|---|---:|---:|---:|
| Classic | 74 / 131 / 95 | 74 / 131 / 95 | 0 |
| Smart | 205 / 0 / 95 | 300 / 0 / 0 | +95 |

First surviving mismatch is Classic seed-1 index 0: byte 8, AEX `00`, Mac `ff` (191 differing bytes in 1596). This matches the previously documented F17 Classic boundary and is unchanged. No new Classic behavior is claimed. First Smart mismatch: none. Every original oracle dictionary is unchanged. Removing diagnostic fields, the corrected-host/pre-fix, final normal, and final sanitized results agree **600/600 route dictionaries**, including bytes/hashes and callback counts. The final sanitized campaign uses abort-on-error, and has zero UBSan/ASan diagnostics, crashes, or harness errors. Leak checking is disabled, not claimed.

**Orchestrator-visible corpus before/after table.** The historical tracked ColorKeep corpus contains no JSON cases; an empty directory is not counted as a passing replay. We instead captured all 300 pre-edit cases and the normal baseline's 100 retained shrunk cases (the configured 2,000,000-byte corpus cap). No historical fixture was overwritten.

| Corpus / route | Saved before → observed after | Count |
|---|---|---:|
| Full snapshot / Classic | exact→exact, same complete result | 74 |
| Full snapshot / Classic | mismatch→mismatch, same complete result | 131 |
| Full snapshot / Classic | refusal→refusal, same complete result | 95 |
| Full snapshot / Smart | exact→exact, same complete result | 205 |
| Full snapshot / Smart | refusal→exact | 95 |
| Baseline shrunk corpus / both routes | complete saved result unchanged | 100 cases |

`--replay "$s/snapshot-before" --jobs 2` completes 300, with 205 matches_saved and exit 1 **as expected** for the 95 improvements. Every replayed result equals its final campaign result. After generating the corrected scratch snapshot, `--replay "$s/snapshot-after" --jobs 2` is 300/300 matches_saved, exit 0. `--replay "$s/before-corpus" --jobs 2` is 100/100 matches_saved, exit 0. Reconstructing those 100 procedural cases from the committed evidence and replaying again also passes 100/100. Each replay used the same worker, ticket-local scratch/report/corpus, and redirected logs.

**Focused and existing checks.** `python3 tools/fuzz/verify_colorkeep_F19.py witnesses`: 6/6 Smart AEX exact with ASan/UBSan abort-on-error. Cases are the index-2/index-3 inputs cropped to 1×2 (odd row padding retained), and four independent 1×2 PF32 cases with signaling-NaN alpha/RGB payloads, rejected alpha with signaling-NaN RGB, signed zero, and infinity. Integer-word construction avoids Python float quieting before execution. Source immutability, padding, failure atomicity and callback balance are checked by the public harness.

`python3 tools/fuzz/verify_colorkeep_F19.py tests`: **6 passed**, zero skips/failures, 4.621 seconds:

- All three `tests/test_colorkeep_windows_callback_contract_20260731.py` tests (including compiled quantization/tolerance/NaN callbacks).
- `test_checkout_cleanup_contract_and_windows_owner_evidence` and `test_generic_worlds_counts_and_typed_workers` from `tests/test_colorkeep_generic_beta_20260820.py`; the latter compiles with ASan/UBSan and now includes odd PF16/PF32 row strides.
- `test_roi_tile_admission_contract_is_one_to_one` from `tests/test_colorkeep_roi_tile_beta_20260820.py`.

The wrapper resolves only missing SDK include/translation-unit paths to absolute MAIN paths; production source remains this worktree's source. It sets all test temporary paths under ticket scratch. `git diff --check` passes.

inference:

- The 95 refusals were a malformed fuzz-host flag, not evidence that valid PF32 native worlds needed relaxed production admission. Corrected-host control and final output equality support this classification.
- Copying object representations through byte pointers resolves the observed odd-stride callback UB while retaining source RGB/NaN bits and the original match-dependent alpha rule. Full input compatibility, native AE odd-stride reachability, FP exception flags, and installed binaries are not established by these finite tests.

changed_files:

- `mac/ColorKeep/ColorKeep.cpp`
- `tools/fuzz/harnesses/colorkeep_main.cpp`
- `tools/fuzz/adapters/color_triage.py` (ColorKeep-only host-control compatibility; ColorKey branch unchanged)
- `tests/test_colorkeep_generic_beta_20260820.py`
- `tools/fuzz/verify_colorkeep_F19.py`
- `reports/fuzz/colorkeep_F19.json`
- `orchestra/reports/F19-colorkeep-host-flags-and-byte-safe.md`

verify:

Run from this worktree. These commands reproduce the final normal/sanitized campaigns, verify all saved result dictionaries, run the six existing tests and six focused witnesses, and reconstruct/replay both the rebaselined full corpus and baseline shrunk corpus. Expected: all commands exit 0; Classic 74/131/95, Smart 300/0/0; no sanitizer diagnostics; full replay 300/300 and shrunk replay 100/100 matches_saved.

```sh
s="$PWD/orchestra/state/F19-colorkeep-host-flags-and-byte-safe/verify"
w=/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_HOST_FLAGS OLM_COLOR_TRIAGE_SANITIZE OLM_COLOR_TRIAGE_NO_TRACE
python3 tools/fuzz/run.py --plugin colorkeep --n 300 --seed 1 --jobs 2 \
  --worker "$w" --scratch "$s/normal" --report "$s/normal.json" \
  --corpus "$s/normal-corpus" > "$s/normal.log" 2>&1
python3 tools/fuzz/verify_colorkeep_F19.py check --report "$s/normal.json"
OLM_COLOR_TRIAGE_SANITIZE=1 ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1 \
python3 tools/fuzz/run.py --plugin colorkeep --n 300 --seed 1 --jobs 2 --shrink-attempts 0 \
  --worker "$w" --scratch "$s/sanitized" --report "$s/sanitized.json" \
  --corpus "$s/sanitized-corpus" > "$s/sanitized.log" 2>&1
python3 tools/fuzz/verify_colorkeep_F19.py check --report "$s/sanitized.json"
python3 tools/fuzz/verify_colorkeep_F19.py tests --scratch "$s" > "$s/tests.log" 2>&1
python3 tools/fuzz/verify_colorkeep_F19.py witnesses --scratch "$s" > "$s/witnesses.log" 2>&1
for phase in after shrunk; do
  python3 tools/fuzz/verify_colorkeep_F19.py snapshot --scratch "$s" \
    --phase "$phase" --destination "$s/corpus-$phase"
  python3 tools/fuzz/run.py --plugin colorkeep --replay "$s/corpus-$phase" --jobs 2 \
    --worker "$w" --scratch "$s/replay-$phase" --report "$s/replay-$phase.json" \
    --corpus "$s/disposable" > "$s/replay-$phase.log" 2>&1
done
git diff --check
```

For the explicit before→after audit, reconstruct with `snapshot --phase before` and replay with the same arguments: expected `replay_complete`, 205/300 matches_saved, exit 1; the 95 differences must be Smart refusal→exact, with unchanged Classic results. The committed evidence records both dictionaries for every case.

next:

No F19 work remains. Keep the existing production admission guards. A separate ticket may investigate the unchanged 131 Classic mismatches and native AE odd-stride reachability; this report does not promote those boundaries or alter the release gate.
