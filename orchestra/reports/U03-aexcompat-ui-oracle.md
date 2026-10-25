status: partial
summary: |
  Resumed with physical space-free Cargo target/TMPDIR; Unicorn and Release guest builds now succeed.
  Implemented explicit UI-session UPDATE/EVENT, Drawbot/App capture, arbitrary FLATTEN snapshots, and state injection.
  Original KiraKira draw/click/drag, picker, copy/paste, randomize/flip and five plugins' UPDATE runs succeed.
  Corrected U01's PF_Point ordering from supplied SDK and original coordinate conversion: x first, y second.
  This is a checkpoint; final witness replay, remaining suite version coverage and installation are in progress.

## facts

- OLM requested directory initially contained only empty orchestra directories and no `.git`; `git rev-parse --show-toplevel` resolved MAIN. Restored the existing `orch/U03-aexcompat-ui-oracle` branch as an actual worktree at the requested path. No MAIN tracked content changed.
- AEXCompat branch: `olm/U03-ui-session`, checkpoint `add877b1`; base documentation commit `f402b7713c81ef235f5899621406841c3e8df1c5`.
- Space-free build command (from the AEXCompat U03 worktree): `TMPDIR=/Users/onmk/.cache/olm-emu/build-U03/tmp CARGO_TARGET_DIR=/Users/onmk/.cache/olm-emu/build-U03/target CARGO_BUILD_JOBS=1 cargo build --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker -j 1`.
- `cargo test --release --locked --manifest-path guest/Cargo.toml -p aex-guest-worker ui_ -- --test-threads=1`: **10 passed, 0 failed** at the first reviewed implementation boundary.
- Capture3: DistanceGradation 3 UPDATE, KiraKira 3 UPDATE, Blur 2 UPDATE, ColorKeep 4 UPDATE, DirectionalBlur 3 UPDATE succeeded. ColorKey/Smoother2/RadialBlur reached unsupported Effect Suite v4; support is being added from the SDK's matching disposal slot.
- KiraKira click insertion changes active stop count 3→4. Release y+20 retains 3 stops; y+21 deletes to 2. Fixed RNG 123456789 evolves to 2408881247 then 770683682 across two randomizations; flip leaves that RNG value unchanged.
- Original FLATTEN returns 325 bytes: version byte plus 324-byte ramp struct. Inactive tail bytes can change even on DRAW; raw flattened data is preserved, not repaired. Active stop count and records are a separate semantic comparison boundary.
- No Mac plugin changes or pixel differential. Draw/pixel mismatch count: not measured against Mac.

## inference

The physical cache path resolves the earlier configure blocker. The UI path now reaches actual original handler logic; this is not native AE scheduling/visual acceptance. U01's y-first claim is contradicted by `Headers/AE_Effect.h` PF_Point x/h then y/v and original KiraKira `181155700` subtraction of frame.left from extra+20. Corrected x-first dispatch produces the insertion boundary.

## changed_files

- AEXCompat guest: `classic.rs`, `classic_ui.rs`, `main.rs`, `x64.rs`, `x64/types.rs`, `x64/iterate_and_suites.rs`, `x64/ui_session.rs`, `x64/ui_draw.rs`, `x64/tests_register_ui.rs`.
- OLM: `tests/ui_oracle/capture.py`; this report.

## verify

Checkpoint only (new worker not installed yet):

```sh
python3 tests/ui_oracle/capture.py --worker /Users/onmk/.cache/olm-emu/build-U03/target/release/aex-guest-worker --output orchestra/state/U03-aexcompat-ui-oracle/recheck
```

Expected final matrix is not yet established. Do not use this checkpoint as final acceptance.

## CLI usage

`aex-guest-worker ui-session <original.aex> <session.json>`

Session includes `current_time`, `time_scale`, ordered `operations` (`update` with `parameters`, or `event` with explicit event fields), and optional `initial_state_u32` (RVA→u32, restricted to writable original-image data). Convenience `updates`/`events` arrays cannot be mixed with `operations`. JSONL stdout has one report per completed dispatch; failures exit nonzero. `capture.py` generates concrete request files.

## Draft claim text (not posted)

作業をclaimします: U03 — explicit Unicorn UI-session oracle, original EVENT/UPDATE and arbitrary serialization, exact Win64 ABI, recording suites and reproducible OLM witnesses. Render dispatch remains unchanged. Acceptance: focused behavioral tests, Release build, independent local review and original-AEX replay. No GitHub issue number assigned; no invented Closes reference.

## Draft PR body (not posted)

Add explicit Unicorn UI-session dispatch so original effects' control logic and semantic drawing calls can be captured independently of rendering. Record parameter flags/names, hidden stream flags, arbitrary serialization, ordered Drawbot resources/calls and injected theme/picker/RNG inputs. Correct PF_Point marshalling to x-first as defined by the supplied SDK and observed original conversion code.

Validation and final review SHA will be filled after replay. This checkpoint is not a PR-ready completion claim.

## next

Finish Effect Suite v4 matrix, preset selection witness, final review, replay comparison and durable worker registration. Preserve original raw serialization anomalies and outstanding-handle counts as data. Native AE scheduling/theme/font/rasterization acceptance remains separate.
