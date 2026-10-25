status: blocked
summary: |
  Implemented the ramp/button/preset state machine, draw-command builder, and AE adapter; committed two checkpoints.
  Unit tests pass; 34 original valid presets round-trip through real arbitrary callbacks byte-identically.
  Seed1/n300 completed; pre-ticket versus final candidate is unchanged on all 600 Classic/Smart route checks.
  All 387 KiraKira corpora replay true; Universal Release bundle built only in scratch.
  Exact ordered UI suite-call parity remains incomplete and pending U03; do not promote this to original-UI exact.

## facts

Baseline: `31c7f256d7f19099d64136c39c93c93370737246`, branch `orch/U02-kirakira-ramp-editor`.
Checkpoints: `4e452bb1`, `cdadccfd`.
Durable measured results and source bindings: `mac/OLMKiraKira/tests/U02-results.json`.
Original AEX SHA256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.

Commands actually run (exact recheck invocations below):

- Compiled and ran `tests/ramp_editor.cpp`: exit 0, `ramp editor interaction and drawing assertions passed`. Tests cover insertion/empty/16 stops, both strip endpoints, marker boundary/reverse hit-testing, accepted/cancelled picker, cross-neighbor dragging and [0,1] clamping, y75/y76 preview/release deletion, release sorting, coincident-position ordering, button arming/outside release/drag-out-release-in, copy/paste across ramps and independent clipboards, RGB-only randomization including two fixed bit sequences, asymmetric flip, hover, preset toggle/scroll/select/first/last and seven preview rows, and ordered strip/marker/grid commands.
- `tests/original_ui_constants.py`: exit 0. Read constructor bytes and PE constants, then generated `RampPresets.h` using `--write-header`. **The binary has 34 presets, not 64.** At `18123637d`, `MOV [RCX+18c],0x22` stores the count; at `181236387`, `MOV [RCX+190],0x40` stores preview width. The 34 table records have count 3 or 5. Requested record 34 has count **2172092144**, already unrelated data. The implementation follows the binary, not the erroneous count in U01/the ticket. The full requested 64 count words and exact constant bits are retained in results JSON.
- Static text helper `1812346f0` computes font size from rectangle height and margin. Button calls `1812355e0` pass margin float `0.1`, yielding **16.0** from height20; preset header passes `0.15`, yielding **14.0**. Constructor field `11.0` exists but this draw path does not read it. The adapter uses these recovered call arguments; the ticket's inferred default-font-size11 is not claimed reproduced. This is static evidence, not executed U03 evidence.
- `tests/persistence.py`: exit 0, **34** original valid presets through actual production FLATTEN/UNFLATTEN/COPY/FLATTEN/DISPOSE callbacks: all **325-byte flattened outputs byte-identical**, zero live handles. NEW/COMPARE/INTERP and the entire arbitrary callback implementation remain textually unchanged. Testing 64 valid original presets is impossible for this PE table; no synthetic entries were invented.
- Default `tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 1`: exit 0, completed300 in **651.205 s**. Smart: **287 exact, 13 refusal** (the same 13 original Smart requests reject). Classic: **48 mismatches, 252 refusals**. No claim that this pre-existing Classic surface is exact. Original worker SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- First campaign mismatch: seed1 index2 Classic, **760 differing words / 2023 differing bytes**, first word0, first byte2, original word `00000000`, candidate word `0000803f`. Candidate raw SHA256 `2492c35739b1ea797c16a53870fbe8ee15438dbdf8ae709ffefeb4dd9ad1c60b`.
- `tests/render_unchanged.py`: exit 0. Separately built pre-ticket and final candidate production sources, regenerated default seed1/n300, compared raw SHA256 and result metadata for both routes: **600/600 identical, zero differences**. Thus no exact→non-exact transition in these cases. The earlier campaign and final candidate are linked by this unchanged-render check; it is not a new original-AEX UI test.
- `tests/replay_corpora.py`: exit 0. **383/383** size256 plus **4/4** size1080 corpora `replay_matches_saved=true`, preserving each recorded worker/hash/timeout. Initial harness invocations failed on mixed max-size, an absolute-path filter inadvertently including other plugin corpora, and missing opt-in size sampler; the committed script fixes these configuration errors. No saved expectation was modified.
- `tools/fuzz/build_F47_bundles.py --plugins OLMKiraKira`: final **BUILD SUCCEEDED**, architectures **x86_64 arm64**. Executable SHA256 `df639c09fe327ac0c978ddcda6f9393e420e96f9356683c72ab06b26d89a70a3`. Built only under ticket scratch, never installed into AE. Regenerable products removed after verification per disk rule. Real AE visual/undo/save checks intentionally not performed, as requested.
- `git diff --check`: exit 0. `~/.cache/olm-emu/worker-U03-ui/` and worktree `tests/ui_oracle/` absent at final inspection: **pending U03**. No original UI payload/ordered trace mismatch count exists yet.

Static functions inspected through the committed U01 bounded reader:
`181235bb0`, `181235950`, `181236260`, `1812366b0`, `181236520`, `181235000`, `181235250`, `1812355e0`, `181235760`, `181236130`, `1812342a0`, `181233ed0`, `181234320`, `181239220`, `181235460`, `1812346f0`, `1812392b0`, `181233860`, `181232080`, `181230cd0`, `181156780`, `181155700`, `181233ce0`; constructor/preset draw/interact assembly checked where decompilation omitted branches.

## inference and unresolved boundaries

- The original's 64 preview width was mistaken for preset count in U01. The 11.0 stored field was also mistaken for the actual `NewDefaultFont` argument. Both corrections follow primary binary evidence, but U03 should execute these calls before declaring exactness.
- **Known incomplete full trace behavior:** theme roles7/8/2/42 are currently prefetched once per draw, rather than queried in each original widget's order. The adapter uses current cross-platform suites (App6/EffectCustomUI2), and ordered acquisition/query/resource parity has not been established. Strip lines, frames, grouped tick paths, marker pen lifetime, text geometry, RGB factors and antialias commands are recovered, but they do not constitute a measured full trace match. U03 must compare and drive any remaining corrections. This is the reason for `blocked`, rather than claiming done from unit tests.
- UI state uses a mutex-protected map keyed by effect_ref, shared clipboard per instance, per-ramp state, and global original-seeded RNG. SEQUENCE_SETDOWN/GLOBAL_SETDOWN clear transient state. Native effect_ref lifetime, reentrancy, undo/redo and copy/paste lifetime still need host acceptance.
- Invalid synthetic preset selections past the valid table are guarded; the original raw table-access behavior outside valid records is not reproduced by reading unrelated memory. Normal first/last visible selection is tested.
- Dynamic Use Ramp enable/disable scheduling belongs to companion U04; this ticket did not add an UPDATE handler or alter other plugins, rendering kernels, arbitrary payload contracts, release gates, or ledger.

## changed_files

- `mac/OLMKiraKira/OLMKiraKira.cpp` — AE event/Drawbot adapter and transient-state cleanup.
- `mac/OLMKiraKira/RampEditor.h` — pure event state machine, sampling, command builder.
- `mac/OLMKiraKira/RampPresets.h` — binary-grounded original 34-entry table.
- `mac/OLMKiraKira/tests/ramp_editor.cpp` — interaction/drawing regression assertions.
- `mac/OLMKiraKira/tests/original_ui_constants.py` — reproducible read-only constants/table extraction.
- `mac/OLMKiraKira/tests/persistence.cpp`, `persistence.py` — real callback round-trip test.
- `mac/OLMKiraKira/tests/render_unchanged.py` — production baseline/candidate seed1 comparison.
- `mac/OLMKiraKira/tests/replay_corpora.py` — all-corpus replay using recorded bindings.
- `mac/OLMKiraKira/tests/U02-results.json` — measured counts/hashes and source bindings.
- `orchestra/reports/U02-kirakira-ramp-editor.md` — this report.

## verify

Run from this worktree; long-command output stays in scratch:

```sh
mkdir -p orchestra/state/U02-kirakira-ramp-editor
export TMPDIR="$PWD/orchestra/state/U02-kirakira-ramp-editor"
clang++ -std=c++17 -O2 -ffp-contract=off mac/OLMKiraKira/tests/ramp_editor.cpp -o "$TMPDIR/ramp_editor"
"$TMPDIR/ramp_editor"
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' mac/OLMKiraKira/tests/original_ui_constants.py > "$TMPDIR/original-constants.json"
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' mac/OLMKiraKira/tests/persistence.py > "$TMPDIR/persistence.log" 2>&1
python3 mac/OLMKiraKira/tests/render_unchanged.py > "$TMPDIR/render-unchanged.log" 2>&1
python3 mac/OLMKiraKira/tests/replay_corpora.py > "$TMPDIR/replay-all.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 1 --scratch orchestra/state/U02-kirakira-ramp-editor/fuzz --report orchestra/state/U02-kirakira-ramp-editor/fuzz.json --corpus orchestra/state/U02-kirakira-ramp-editor/corpus > "$TMPDIR/fuzz.log" 2>&1
python3 tools/fuzz/build_F47_bundles.py --plugins OLMKiraKira --scratch orchestra/state/U02-kirakira-ramp-editor/bundle > "$TMPDIR/bundle.log" 2>&1
git diff --check
```

Expected: all exit0; unit pass; 34 valid preset round trips; 600 unchanged route results; 387 replay true; campaign counts above (worker-bound); Universal build succeeds. Build hash may vary with build metadata/path. No native AE installation. Recheck U03 presence before resuming exact UI comparison.

## next

Resume U02 with U03 witnesses: compare event payloads and ordered drawing/suite traces on all five slots, correct query/resource ordering, verify actual font arguments and preset count, then close exact UI acceptance. Keep native AE checks with the user in U06. Report the preset-count/font corrections back to U01/orchestrator; no ledger/gate changes were made here.
