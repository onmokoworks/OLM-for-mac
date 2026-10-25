status: done
summary: |
  Production SDK EVENT/UPDATE host matches 13 original-AEX sessions / 159 dispatches exactly on active payloads and ordered calls.
  Restored widget theme-query order, retained-pointer DRAW conversion, and five-ramp UPDATE enable/disable handling.
  Added 105 original dispatches covering stop capacity, marker boundaries, five slots, non-gray themes and first/last presets.
  Inactive serialized capacity remains explicitly classified, not claimed byte-identical; saved-project callbacks are unchanged.
  Render unchanged: 600 baseline route checks, 387 saved corpus replays and 225 reference/fast cases; seed1/n300 retains prior counts.

## facts

- Baseline: `af8cedfa2ba5f9451f0599f6dac05dccfab9ef44`, branch `orch/U02b-kirakira-ui-vs-original`.
- The host includes the production source and dispatches `EffectMain`. Each original session's first before snapshot is an explicit initial condition. Subsequent scalar fields, FLATTEN output, UI updates, RNG and calls come from Mac execution; no expected after-state is fed back. This tests handlers, not Mac ParamsSetup. Context window types, continuation, frame, time, theme, picker and RNG inputs are supplied. Original setup provenance is not misrepresented as Mac provenance.
- `python3 mac/OLMKiraKira/tests/ui_compare.py`: exit 0. **13 sessions, 159 dispatches, 91,468 ordered suite calls, zero active-payload/parameter/draw mismatches, zero process failures**. Breakdown: 55 DRAW, 51 CLICK, 45 DRAG, 5 ADJUST_CURSOR, 3 UPDATE. Resources and arbitrary handles are balanced at host exit. `--no-build` replay also passed and checks executable/source binding.
- Existing U03 witnesses contribute 54 KiraKira dispatches. `ui_matrix.py` captured another **105** with the immutable worker: counts/boundaries 63, five-slot hover 25, menu first/last 17; all original process exits 0. The original count progression is 3→2→1→0→1→16; another insertion stays 16. Maximum-scroll draw records 1,958 calls and last-preset selection produces five stops. Requests, compressed raw witnesses and hashes are committed under `mac/OLMKiraKira/tests/ui_witnesses/`.
- Original worker SHA256: `e476ba8ddfbda5fc2ef1cda49c700f15c5d09a232930f6a2074d7026f2c406b0`. Original AEX SHA256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`. No original binary, emulator source, registered worker, MAIN, release gate or ledger was modified.
- First pre-fix draw mismatch: `/calls/0`, original `PF_GetDrawingReference`, Mac `PF_AppGetColor`. After restoring query order, the remaining button fill mismatch was original bits **1049505934**, Mac **1053499595**; the scrolled preset outline was original **1063936234**, Mac **1049403533**. Original `181155700` subtracts frame.left/top even on DRAW while retaining the prior point. Reproducing that general conversion eliminates these differences. Static recheck: `python3 orchestra/reports/U01-read-function.py OLMKiraKira 181155700 181235000 1812355e0`.
- Raw inactive capacity differs in all 159 dispatches. First raw difference in `KiraKira-count-boundaries` dispatch 0: `/after/13/value/flat_bytes/65`, original **254**, Mac **0**. The original writes 325 bytes including unstable inactive stack capacity. Version/count/active bytes and every other event field compare exactly. Full raw originals and Mac outputs are retained; no tail bytes are patched into Mac results.
- Comparator negative checks (included in `ui_compare.py`) reject a one-bit active-payload change and a one-bit coordinate change; a changed inactive byte remains a visible raw difference and is classified separately. Fixture hash checks reject modified committed requests/outputs. `python3 tests/ui_oracle/verify.py`: exit 0, **17 original fixture sessions / 174 dispatches**; this is fixture integrity, not a new replay of the other plugins.
- Unit test: exit 0, `ramp editor interaction and drawing assertions passed`. Persistence test: exit 0, **34 original valid presets**, production UNFLATTEN/COPY/FLATTEN byte-identical, **zero live handles**. Production arbitrary callbacks were not changed.
- Final source versus baseline `render_unchanged.py --baseline af8cedfa2ba5f9451f0599f6dac05dccfab9ef44`: exit 0, default seed1/n300, **600/600 Classic/Smart route results identical**, zero differences.
- Saved corpus replay: exit 0, **383/383** max-size256 and **4/4** max-size1080, all `replay_matches_saved=true`. Recorded workers, timeouts and expectations are preserved.
- `ref_vs_fast.py --plugin olmkirakira --jobs 1 --parallel 1`: exit 0, default 200 small + 20 HD + 5 UHD cases, **216 exact, 9 matching refusals, 0 mismatches**. Both reference and fast are rebuilt from this source. This run covers thread cap 1.

- Default original-AEX fuzz `--n 300 --seed 1 --jobs 1`: exit 0, **300 completed in 656.1326 seconds**; Smart **287 exact / 13 refusals**, Classic **48 mismatches / 252 refusals**, identical to U02's reported counts. First mismatch is index2 Classic: **760 differing words / 2,023 bytes**, word0/byte2, original `00000000`, Mac `0000803f`; Mac raw SHA256 `2492c35739b1ea797c16a53870fbe8ee15438dbdf8ae709ffefeb4dd9ad1c60b`. These pre-existing render differences are not promoted to exact. Fuzz built during UI development; the final-source 600-route baseline check establishes unchanged final render output. Full measured summaries/provenance are committed in `U02b-results.json`.

- Cleanup: removed regenerable UI/persistence/render/reference build trees and binaries; retained logs, raw traces and summaries. Scratch is **22,563,786 bytes** (below 5 GiB). All started test/capture/build processes exited; no background worker remains. `git diff --check` exits 0. No push or native AE installation.

## inference

The measured corrections close the retained UI-session boundary, including the new natural boundary requests. Theme values must be resolved when each widget requests them, rather than prefetched globally. Original DRAW pointer conversion explains hover colors at nonzero frame origins; changing color constants would have concealed the actual cause.

The stable saved-project contract is version 1, count and active 20-byte records within a 325-byte payload. Mac zero-filled inactive capacity remains compatible with the existing writer/reader contract; exact arbitrary original stack garbage is neither stable nor claimed reproduced. Native AE project reopening, scheduling, font rasterization and undo remain U06 acceptance, not established by an SDK recorder. U03 has no injectable font rasterizer or scale in its request schema; the tested handlers request exact NewDefaultFont sizes and do not query screen scale.

The original advertises `out_flags=0x02008040`, which does not include SEND_UPDATE_PARAMS_UI. Those flags remain unchanged; this ticket proves explicit UPDATE dispatch, not native scheduling. Coordinate and resource equality is not pixel-rasterization equality.

## changed_files

- `mac/OLMKiraKira/OLMKiraKira.cpp`: ordered theme resolution, DRAW pointer conversion, explicit UPDATE handler.
- `mac/OLMKiraKira/RampEditor.h`: ordered theme-query commands and deferred theme colors.
- `mac/OLMKiraKira/tests/ui_host.mm`, `ui_compare.py`: real SDK host, exact recorder, streaming comparator, binding and negative checks.
- `mac/OLMKiraKira/tests/ui_matrix.py`, `ui_witnesses/*`: additional original sessions and provenance.
- `mac/OLMKiraKira/tests/UI_ORACLE.md`: reproduction and evidence boundaries.
- `mac/OLMKiraKira/tests/ramp_editor.cpp`: command-query assertion while retaining geometry checks.
- `mac/OLMKiraKira/tests/{persistence.py,render_unchanged.py,replay_corpora.py}`: caller-selected scratch paths; baseline header snapshots for the unchanged-render test.
- `mac/OLMKiraKira/tests/U02b-results.json`: measured results and source bindings.
- This report.

## verify

From this worktree, sequentially (long-command output is redirected):

```sh
mkdir -p orchestra/state/U02b-kirakira-ui-vs-original
export TMPDIR="$PWD/orchestra/state/U02b-kirakira-ui-vs-original"
python3 mac/OLMKiraKira/tests/ui_compare.py > "$TMPDIR/compare.log" 2>&1
clang++ -std=c++17 -O2 -ffp-contract=off mac/OLMKiraKira/tests/ramp_editor.cpp -o "$TMPDIR/ramp_editor"
"$TMPDIR/ramp_editor"
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' mac/OLMKiraKira/tests/persistence.py --scratch "$TMPDIR/persistence" > "$TMPDIR/persistence.log" 2>&1
python3 mac/OLMKiraKira/tests/render_unchanged.py --baseline af8cedfa2ba5f9451f0599f6dac05dccfab9ef44 --scratch "$TMPDIR/render-unchanged" > "$TMPDIR/render-unchanged.log" 2>&1
python3 mac/OLMKiraKira/tests/replay_corpora.py --scratch "$TMPDIR/corpora" > "$TMPDIR/corpora.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 1 --scratch "$TMPDIR/fuzz" --report "$TMPDIR/fuzz.json" --corpus "$TMPDIR/corpus" > "$TMPDIR/fuzz.log" 2>&1
python3 tools/perf/ref_vs_fast.py --plugin olmkirakira --jobs 1 --parallel 1 --scratch "$TMPDIR/ref-vs-fast" > "$TMPDIR/ref-vs-fast.log" 2>&1
python3 tests/ui_oracle/verify.py
git diff --check
```

Expected: every command exits 0; UI 13/159 with no active or ordered-call mismatches; unit pass; 34 persistence cases; 600 unchanged route results; 387 saved corpus matches; reference/fast 216 exact + 9 matching refusals; fuzz Smart 287 exact/13 refusals and Classic 48 existing mismatches/252 refusals. Raw inactive-tail differences remain separately reported.

Optional original recapture: `python3 mac/OLMKiraKira/tests/ui_matrix.py > "$TMPDIR/matrix.log" 2>&1`. This intentionally regenerates the three committed additional witnesses and their hashes, including unstable raw tails; it must produce 63/25/17 successful dispatches.

## next

Coordinate the KiraKira UPDATE handler with U04 to avoid duplicate implementation. Native AE visual/rasterizer, scheduling, undo and project-reopen checks remain U06. Broader context-lifetime/host-error sessions can be separate tickets; this report does not generalize measured handler parity to all native host behavior.
