status: done
summary: |
  Implemented explicit original-AEX Unicorn UI sessions with stateful EVENT/UPDATE and recording suites.
  Committed 17 witness sessions: 123 UPDATE + 51 EVENT = 174 successful dispatches.
  Release build and 10 focused behavioral tests pass; installed-worker replay has zero semantic mismatches.
  Preserved original KiraKira inactive serialization-tail differences separately; no Mac parity claim.
  Installed immutable worker/source archive and registered worker-U03-ui in the shared cache INDEX.

## facts

- AEXCompat branch: `olm/U03-ui-session`; final HEAD **888e43811264d3a51124f52a9f61e9a841413b68**. Executable source commit: **add877b1da1cc6060979de66ad665067b3e22922**; subsequent commit changes documentation only. Base: `f402b7713c81ef235f5899621406841c3e8df1c5`.
- OLM checkpoint commit: `ede1824b`. The requested directory initially lacked `.git`; restored the existing ticket branch as a real worktree before edits. No MAIN tracked content, release gates, forbidden-action lists or OLM plugin sources changed.
- All Cargo commands ran from the space-free AEXCompat U03 worktree with cache target/TMPDIR, resolving the earlier Unicorn configure blocker. Memory checks before builds showed 47–57% free, above the required 30%. One-process final Release build succeeded; focused Release tests: **10 passed, 0 failed**. Whole tracked Rust formatting check and `git diff --check` passed. Build/test logs remain in ticket scratch.
- Final original capture and installed-worker replay: **17 sessions, 174 dispatches, all process exits 0, semantic mismatches 0**. Seven non-KiraKira sessions also match the raw JSON exactly. Ten KiraKira sessions have raw inactive-tail differences. First raw mismatch in filename-sorted final replay: `KiraKira-context-negative`, `/0/event/after/13/value/flat_bytes/224`, fixture **184**, replay **236**. No active-value mismatch.
- Negative verification checks: nonzero capture exit, changed request hash, one active-payload bit, and one Drawbot coordinate bit each caused verifier exit **1**. Modified replay files were restored. Fixture-only verification labels itself `fixture_invariants` with `semantic_mismatches: null`.
- Original KiraKira insertion changes stops **3→4**. Drag release at strip-bottom+20 retains **3**; +21 deletes to **2**. Picker cancel preserves active payload, accept changes it; copy/paste transfers active payload across slots 14/20. RNG at original writable RVA `0x1824968`, seed **123456789**, advances to **2408881247**, then **770683682**; flip leaves RNG unchanged. Default draw records **1495** ordered calls, inserted ramp **1503**, deleted ramp **1487**, open preset menu **4730**. Negative area/ordinary-slot draws record zero calls.
- UPDATE witnesses capture DISABLED, HIDDEN and name bytes. Names remain unchanged for these rows. ColorKeep retains one acquired stream handle per UPDATE (four outstanding at pre-teardown); this original behavior is reported, not concealed. Session teardown success is not a zero-outstanding-handle assertion.
- Installed worker: `/Users/onmk/.cache/olm-emu/worker-U03-ui/aex-guest-worker`, SHA-256 **e476ba8ddfbda5fc2ef1cda49c700f15c5d09a232930f6a2074d7026f2c406b0**.
- Cleanup: removed the 381 MiB regenerable `build-U03` tree after installation and verification; ticket scratch is 59 MiB (below 5 GiB). No worker-started build/emulator process remains. Durable cache is 9.4 MiB.
- Durable source archive SHA-256: **4711e708579ae3663278bbd4420ba64b7c49ad49ef7278db3e46cac5f5abbf58**. Installation used `tests/ui_oracle/install_worker.py`, refused overwrite, and appended INDEX under a lock; registered workers were not rebuilt in place. Exact metadata is committed as `tests/ui_oracle/build.json`.
- Required local independent review covered AEX source, ABI, state continuation, invalidation, suite-table isolation, lifetimes, picker handling and verifier integrity. All findings were fixed; no rejected findings remain. Reviewer independently ran fixture checks and the final replay. No claim comments, PRs, pushes or external messages were sent.

## inference

The observed results establish an original-handler oracle for the covered UI calls and matrix rows. They do not establish native AE scheduling, font rasterization, pixels, undo/save behavior, or Mac bit parity.

**U01 ABI correction:** supplied SDK `Headers/AE_Effect.h:1245–1254` defines PF_Point as x/h first, y/v second. Original KiraKira `181155700` copies extra+20 and subtracts frame.left, then handles extra+24 as y. Thus click x/y offsets are 20/24 (hover 16/20), contrary to U01's y-first note. Correct marshalling reaches the insertion boundary.

KiraKira's original FLATTEN returns 325 bytes: version + count + capacity for sixteen 20-byte records. Inactive capacity changes even on DRAW. Raw evidence is retained unchanged. Semantic replay checks exact version/count/active records and all remaining fields; it explicitly reports inactive-tail differences. This is a schema boundary, not tolerance or a final-byte repair, and raw serialization equivalence remains unproven.

## changed_files

- AEXCompat guest: `classic.rs`, `classic_ui.rs`, `main.rs`, `x64.rs`, `x64/types.rs`, `x64/iterate_and_suites.rs`, `x64/ui_session.rs`, `x64/ui_draw.rs`, `x64/tests_register_ui.rs`.
- AEXCompat docs: `docs/olm/U03-ui-session.md`, `docs/olm/U03-ui-session-build-blocker.md`.
- OLM: `tests/ui_oracle/{README.md,build.json,capture.py,verify.py,install_worker.py,manifest.json,witnesses/*}` and this report.
- Durable local cache: new `worker-U03-ui/` and its INDEX entry.

## verify

From the OLM ticket worktree:

```sh
python3 tests/ui_oracle/verify.py
python3 tests/ui_oracle/capture.py --worker /Users/onmk/.cache/olm-emu/worker-U03-ui/aex-guest-worker --output orchestra/state/U03-aexcompat-ui-oracle/recheck
python3 tests/ui_oracle/verify.py --replay orchestra/state/U03-aexcompat-ui-oracle/recheck
```

Expected: fixture checks exit 0; capture has 17 successful sessions / 174 lines; replay exits 0 with `semantic_mismatches: 0`. KiraKira raw-tail differences are separately reported and can vary per execution. Full original and request hashes are in fixtures/manifest; originals remain read-only in MAIN `plugins_2025/`.

To rebuild, first check `memory_pressure` (at least 30% free), create cache `build-U03/tmp`, and run **from AEXCompat U03**, never from OLM's space-containing path:

```sh
TMPDIR=/Users/onmk/.cache/olm-emu/build-U03/tmp CARGO_TARGET_DIR=/Users/onmk/.cache/olm-emu/build-U03/target CARGO_BUILD_JOBS=1 cargo build --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker -j 1
TMPDIR=/Users/onmk/.cache/olm-emu/build-U03/tmp CARGO_TARGET_DIR=/Users/onmk/.cache/olm-emu/build-U03/target CARGO_BUILD_JOBS=1 cargo test --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker ui_ -- --test-threads=1
```

Expected: successful Release build, 10 passing focused tests. Do not overwrite the registered worker. Remove regenerable build trees after verification.

## CLI usage

`aex-guest-worker ui-session <original.aex> <session.json>`

Explicit opt-in mode runs original GlobalSetup/ParamsSetup/SequenceSetup and original arbitrary initialization/copy/flatten callbacks. Session accepts current_time/time_scale and ordered `operations` tagged `update` (parameters) or `event` (slot, CONTROL area, frame, x/y, click count, drag/final, context). Convenience updates/events arrays cannot mix with operations. State and shared copy buffer persist; continuation is scoped to context/slot and survives draws. Optional `initial_state_u32` injects bounded writable original-image RVAs and records before/after state. Each dispatch emits canonical JSONL with arbitrary before/after, parameter/UI/name/hidden mutations and ordered calls; failures are nonzero and unsupported suite calls fail closed.

Recording covers Drawbot Supplier (including default font), Surface (including DrawString/AA), Path, stable IDs and retain/release, injected theme/picker and invalidation. Float bits, strings, rect/path data are retained. PF Interface/Layer/Effect/Stream handle lifetimes and current time are modeled for observed older-suite versions. Detailed protocol and limits: AEXCompat `docs/olm/U03-ui-session.md`. Existing render dispatch is unchanged by the explicit UI-mode interception.

## witness list

| Session | Dispatches / coverage |
|---|---|
| DistanceGradation-update | 3 |
| KiraKira-update | 3, five ramp enable rows |
| Blur-update | 2 |
| ColorKeep-update | 4, N=1/2/99/100 |
| DirectionalBlur-update | 3, noise=1/2/3 |
| Smoother2-update | 18, key on/off × mode 1/2/3 × count 0/1/5 |
| RadialBlur-update | 54, noise × type × outer/inner mode |
| ColorKey-update | 36, P/C/R × N=0/1/24/25 plus first/last use/replace rows |
| KiraKira-draw-click | 5, default draw/insertion/drag |
| KiraKira-drag-delete-20 / -21 | 6 each, select/drag/intermediate draw/final boundary |
| KiraKira-picker-cancel / -accept | 3 each |
| KiraKira-copy-paste | 9, two ramp slots |
| KiraKira-randomize-flip | 8, fixed original RNG state |
| KiraKira-presets | 9, open/draw/scroll/release/select |
| KiraKira-context-negative | 2, wrong area and ordinary parameter |

## Draft claim text (not posted)

Claim U03: implement an explicit Unicorn UI-session oracle for original EVENT/UPDATE handlers, recording Drawbot/App/CustomUI calls and parameter/arbitrary state. Deliver focused tests, Release build, independent local review and reproducible OLM witnesses. Render mode stays unchanged. No issue number was assigned; no invented Closes reference.

## Draft PR body (not posted)

Original effects previously could not run stateful EVENT/UPDATE sessions in the Unicorn worker. Add opt-in `ui-session` dispatch with original setup/arbitrary callbacks, correct Win64 event marshalling, persistent drag/copy/RNG state and recording suites. Capture exact active payload bytes, UI flags/names/hidden streams and ordered drawing calls, with injected theme/picker inputs and fail-closed unsupported calls.

Validation: Release build; 10 focused behavioral tests; independent local review; 17 original-AEX sessions / 174 successful dispatches; installed-worker replay with zero semantic differences; negative verifier tests reject changed inputs, failed processes and active/draw bit changes. Correct PF_Point ordering to SDK x-first. Preserve and report KiraKira's unstable unused serialized capacity separately; do not claim raw serialization or native rendering parity. Reviewed code SHA add877b1; final docs HEAD 888e4381.

## next

U02 can consume KiraKira event/trace witnesses; U04/U05 can consume UPDATE matrices. Follow up native AE host scheduling/undo/save/font/pixel behavior (U06) and establish a serialization policy for original unused ramp capacity before claiming whole-payload byte parity. Extend unsupported suites only when new original call evidence requires them. No further implementation work is required for this ticket's starter oracle.
