status: partial
summary: Mac effect chains and 4K UHD rendering implemented and tested at 8/16/32 bpc.
  Integrated U03's explicit UI recorder, with 17-session replay matching its semantic contract.
  Corrected native event coordinate order; portable dispatcher test passes, untested on Windows.
  Native RVA watches, interactive Mac custom UI, and exhaustive suite parity remain open.
  No push, PR, claim, MAIN edit, plugin-kernel change, or release-gate change.

facts:
- AEXCompat worktree `AEXCompat-olm-X01`, branch `olm/X01-platform-parity`, resumed at `97b596d1`.
- Final AEXCompat head: `13bda6be` (reviewed inventory/draft update); clean worktree.
- Commits: `c5c7746d` typed GUI chains/shared state and chain artifact identity; `92c5b4b3` merge U03; `80640847` GUI 4K; `2c7b29d6` native UI coordinate ABI. One gap per commit; merge imports U03 behavioral tests. Only merge conflict was adjacent EOF additions in `classic.rs`; retained F54 watches and U03 include. Independent review passed.
- `git fetch gitlab`, read-only GitHub issue/PR listing succeeded. No external posting.
- Harness unit suite: **87 passed, 0 failed, 5 ignored**. Shared artifact suite: **8 passed**. Chain suite against combined worker: **5 passed**, including original ColorKeep at all three depths and no-worker all-bypass exports. Intermediate output/input checksums match exactly; no image tolerance.
- Real ColorKeep 4K UHD tests: **2 passed**, including 3840x2160 input admission at all depths, one-past rejection, and original AEX rendering/export at 8/16/32 bpc through registered F54c. No process, file, byte, or deadline limit raised. Deep multi-layer requests can still hit existing explicit resource bounds.
- Guest `ui_`: **10 passed**. Guest full release suite: **719 passed, 3 ignored** (lib), **10 passed** (CLI), 0 doc tests. Ordinary render/session tests included; full OLM render corpora were not replayed.
- Initial real-chain boundary: session audit rejected `6 files/7764707 bytes; limits 4/536870912`. Fixed by using the existing declared fixture extra-file accounting, also fixing resident secondary-layer accounting. Subsequent deep export exposed `comparison identity lacks plugin_sha256`; added a strict chain identity variant with canonical stage identities and hash linkage, including honest no-plugin identity copies. Final tests pass.
- Native coordinate test: linked actual `worker_ui_event_execution.cpp` on macOS. Before fix exit **134**, first assertion `points[i].h == 17 + 2*i`; after fix exit **0**. Distinct signed x/y values, drag interpolation and keydown exercised. Native Windows process/ABI runtime is **untested on Windows**; native worker executable not built.
- `cargo check ... -p aexcompat-harness --target x86_64-pc-windows-msvc --locked --jobs 1`: **exit 0**. This checks shared chain/artifact code and Windows GUI compilation, not native C++ execution.
- macOS Release guest and harness builds: **exit 0**. Release `--describe-aex` via combined worker: valid descriptor, **101 ColorKeep parameters**. No visual GUI QA claimed.
- Frozen U03 requests replayed without changing their manifest: **17 sessions / 174 operations / 0 semantic mismatches**. Ten KiraKira sessions differ in inactive arbitrary serializer bytes. First raw difference in `KiraKira-update`: `$[0].event.after[13].value.flat_bytes[304]`, expected **4**, actual **242**. Existing U03 comparator compares active records and all other fields exactly; this is **not full raw-buffer equality** or AE equivalence.
- New durable worker: `$HOME/.cache/olm-emu/worker-X01b-parity/aex-guest-worker`; SHA-256 `34ce39821a53815dbd2252046cf375222d27a8045685fa6d946cfad211e40c4b`. Source `2c7b29d60962c57a7f376c3fa5c5cc34de51e00d`, `build.json`, `source.tar.gz`; separately registered under INDEX lock. Existing oracle workers were not overwritten. F54c remains SHA-256 `3d5eec0c6792f176a9cfbc38093c53b852f4ea1baae2cfd313345c02f55d6fba`.
- Independent reviews found and resolved single-stage warmup publication, missing selected deep export and stale FHD label. No rejected or accepted-unaddressed findings. Reviewed code boundary `2c7b29d6`; inventory and reproducibility helpers separately reviewed.
- Whole-tree rustfmt exit 1 only for inherited guest x64 `engine.rs`, `tests_cases.rs`, `trace.rs`; `git diff 97b596d1 --exit-code --` these paths exits 0. Changed Rust formatting and `git diff --check` pass.
- Logs in `orchestra/state/X01b-aexcompat-platform-parity/`. Disposable build cache peaked below 2 GiB; cleanup status recorded below. No permission rejection occurred.

inference:
- Chains, 4K and U03 recording are bounded host/transport capabilities supported by actual tests, not universal plugin compatibility or native AE arithmetic claims.
- Native TraceWriter records host callbacks; it cannot provide instruction-site F54c pointer-chain/plane observations by adding flag aliases. Native instrumentation remains implementable, but is not implemented by this partial stack.
- U03 fixes an important worker-side UI gap. Its recorder does not implement Mac GUI custom-control rasterization, mouse dispatch, font metrics, full suite versions, native scheduling or project persistence.

changed_files:
- AEXCompat: `broker/crates/harness/src/{macos.rs,macos_chain.rs,gui_state.rs,windows/effect_chain.rs}`; `broker/crates/broker/src/image_render/artifacts.rs`.
- AEXCompat U03 merge: `guest/crates/aex-guest-worker/src/{classic.rs,classic_ui.rs,main.rs,x64.rs,x64/iterate_and_suites.rs,x64/tests_register_ui.rs,x64/types.rs,x64/ui_draw.rs,x64/ui_session.rs}`, plus `docs/olm/U03-ui-session*.md`.
- AEXCompat: `minihost/src/worker_ui_event_execution.cpp`, `tests/portable/ui_event_coordinates.cpp`, `analysis/PLATFORM_PARITY_2026-10-26.md`.
- OLM: this report, `orchestra/reports/X01b-platform-parity-inventory.md`, `tools/emulation/aexcompat_patches/{verify_X01b_parity.py,install_X01b_worker.py}`.

verify:
Run in AEXCompat's space-free X01 worktree, logging long output in the OLM ticket scratch directory. Use one job and one test thread. These reproduce the meaningful checks:

```sh
export TMPDIR="$HOME/.cache/olm-emu/build-X01b/tmp"
export CARGO_TARGET_DIR="$HOME/.cache/olm-emu/build-X01b/target"
export CARGO_PROFILE_DEV_DEBUG=0 CARGO_PROFILE_TEST_DEBUG=0 CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_INCREMENTAL=0
mkdir -p "$TMPDIR"
cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness --locked --jobs 1 -- --test-threads=1
# 87 passed, 5 ignored
cargo test --manifest-path broker/Cargo.toml -p aexcompat-broker --lib render_artifacts --locked --jobs 1 -- --test-threads=1
# 8 passed
export AEXCOMPAT_TEST_AEX="$HOME/Documents/Projects/Personal/OLM as/refs/upstream_official/20260619_olm_official_zips/extracted/OLMColorKeep/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
export AEXCOMPAT_GUEST_WORKER="$HOME/.cache/olm-emu/worker-X01b-parity/aex-guest-worker"
cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness chain --locked --jobs 1 -- --include-ignored --test-threads=1
# 5 passed
AEXCOMPAT_GUEST_WORKER="$HOME/.cache/olm-emu/worker-F54c/aex-guest-worker" cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness 4k --locked --jobs 1 -- --include-ignored --test-threads=1
# 2 passed
cargo test --release --manifest-path guest/Cargo.toml -p aex-guest-worker --locked --jobs 1 -- --test-threads=1
# 719 passed + 3 ignored (lib), 10 passed (CLI)
cargo check --manifest-path broker/Cargo.toml -p aexcompat-harness --target x86_64-pc-windows-msvc --locked --jobs 1
# exit 0; Windows runtime still untested
cargo build --release --manifest-path broker/Cargo.toml -p aexcompat-harness --locked --jobs 1
cargo build --release --manifest-path guest/Cargo.toml -p aex-guest-worker --locked --jobs 1
clang++ -std=c++20 -D__cdecl= -Iminihost/src tests/portable/ui_event_coordinates.cpp minihost/src/worker_ui_event_execution.cpp -o "$HOME/.cache/olm-emu/build-X01b/ui-event-coordinates"
"$HOME/.cache/olm-emu/build-X01b/ui-event-coordinates"
# exit 0
```

From OLM worktree, with a fresh output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/aexcompat_patches/verify_X01b_parity.py --worker "$HOME/.cache/olm-emu/worker-X01b-parity/aex-guest-worker" --main "$HOME/Documents/Projects/Personal/OLM as" --output orchestra/state/X01b-aexcompat-platform-parity/ui-recheck
# 17 sessions, 174 operations, semantic_mismatches 0; raw inactive tails reported separately
```

Do not rerun installation over the existing cache entry; the installer intentionally refuses replacement. See `build.json` / source archive for rebuild provenance. The inventory contains draft claim/PR text (not posted), suite/version boundaries and Windows verification steps.

next:
- Review/merge the partial stack through the orchestrator.
- Implement native instruction-site watches with bounded pointer reads, module-relative addressing, occurrence ordering and paired guest/native fixtures; then execute Windows validation. Current native host-call trace is not an equivalent.
- Connect explicit UI sessions to an interactive Mac custom-UI canvas, audit remaining suite slots/versions (including ACE/AEGP/arbitrary streams) and create paired behavior witnesses.
- Deep previews, audio/timeline, full diagnostic UX and negotiated geometry/ROI GUI parity remain open as documented in the inventory. Do not claim “no platform-only features” yet.

cleanup:
- `find "$HOME/.cache/olm-emu/build-X01b" -depth -delete` succeeded; the disposable build tree no longer exists. Registered `worker-X01b-parity` remains and its hash was reverified. All launched build/test commands completed; no worker/background process was intentionally retained. Logs remain in ticket scratch.
