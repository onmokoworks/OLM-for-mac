The OLM stack adds bounded guest geometry and tracing, numeric compatibility work, explicit UI sessions, and macOS deep-image/chained rendering. It also includes Japanese and English GUI guides. These are host and transport capabilities with bounded evidence; this PR does not claim full platform parity or universal AE equivalence.

## Changes

- F54: opt-in downsample, padded rowbytes, extent/request rectangles, pixel aspect, negotiated output and cropped checkouts. Admit 3840×2160 and map required overflow pages within the bounded frame arena, preserving small-allocation addresses and checkout ownership.
- F54b: SSE NaN operand ordering, UCRT-compatible float/double functions, legacy DEEP_PIXELS allocation, caller-selected resident watches and opt-in instruction budgets. Existing execution defaults remain intact; numeric behavior is tested as raw bits.
- F54c: resident pointer chains, bounded full-plane snapshots, first/all occurrence selection, JSON/raw dumps, aggregate capture reservations and explicit dropped-capture reporting.
- U03: explicit UPDATE/EVENT CLI sessions with checked UI suite handles and drawing-call recording. Ordinary rendering does not enable UI-session interception; this is not an interactive custom-UI canvas.
- X01/X01b: shared deep decoding, validated ARGB16 artifacts and F54 rectangle responses; Mac effect chains with independent stage state and typed intermediates, 4K UHD admission, and corrected native point coordinate order. Final chain raw artifacts are ARGB; Windows chain sidecars remain RGBA.
- X02/X03: bilingual GUI guide and README links, updated to the X01b boundary. Format the three inherited guest files required by the repository-wide CI formatting gate.

## Local validation

All commands used one build job and one test thread, Rust/Cargo 1.93.1, and space-free disposable build paths.

- Release guest tests: 719 library + 10 CLI + 8 olm-ucrtmath passed, zero failed, 3 ignored. Release guest build passed.
- Harness tests: 87 passed, zero failed, 5 ignored (includes GUI state). Shared artifact tests: 8 passed; decoded input tests: 2 passed.
- Real ColorKeep chain tests with the newly built worker: 5 passed. 4K admission and 8/16/32-bpc real rendering: 2 passed. Resident ARGB16 export: 1 passed.
- Frozen U03 replay with this build: 17 sessions / 174 operations / zero semantic mismatches. Ten KiraKira sessions retain raw inactive-tail differences, as in X01b.
- Windows x86_64-pc-windows-msvc harness `cargo check`: passed. macOS Release harness build: passed. Portable native UI coordinate compilation/execution: passed.
- CI-equivalent rustfmt over all 244 tracked Rust files: passed. `git diff --check`: passed. Japanese manual lint: exit 0, 0 errors, 5 wording warnings and 1 info retained after review. All 10 local guide links resolve.

Commands: `cargo test --release --manifest-path guest/Cargo.toml -p aex-guest-worker -p olm-ucrtmath --locked --jobs 1 -- --test-threads=1`; harness `cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness --locked --jobs 1 -- --test-threads=1`; focused `render_artifacts`, `decoded_rgba`, `chain`, `4k`, and `real_resident_argb16_gui_export_matches_worker_world`; Release builds of guest/harness; Windows target check; `clang++ -std=c++20 -D__cdecl= -Iminihost/src tests/portable/ui_event_coordinates.cpp minihost/src/worker_ui_event_execution.cpp` and execute. Reproduction script and machine-readable UI summary are retained in the OLM X03 report.

## Earlier evidence and its limits

These are retained results from the individual stack reports, not reruns on this PR head:

- F54's original geometry-only draft recorded 44 ColorKey, 15 Smoother2 and eight cropped witnesses exact; its survey still had numeric/DEEP_PIXELS differences. F54b subsequently compared all 23 saved corpus sets: 2,976 inputs, 5,649 routes, 5,542 successful byte-exact outputs, 107 matching rejections, zero byte/status differences. Its 320,000 math-probe rows and eight real-AEX trace runs matched. Matching rejection is not successful rendering.
- F54b 4K measurements had 20 successes and 10 rejections, including six wall-limit stops, three Smoother2 guest exceptions and unsupported Smoother float depth. UHD admission does not promise every AEX completes within existing bounds.
- F54c matched 17 R06 cases / 342 snapshots and measured cropped/4K captures. Its later 5,687-route inventory had zero byte differences but TWO RadialBlur status differences at the existing wall bound. Full F53 equivalence is still blocked; the registered experimental worker does not replace OLM's default oracle. A selector-entry watch also produced zero captures; direct-call and tested function watches work, not universal watch-site coverage.
- X01b replayed 17 U03 sessions / 174 operations with zero semantic mismatches using the existing active-arbitrary-record comparator. Ten KiraKira sessions had different inactive serializer tails; full raw-buffer equality is not claimed.

No OLM plugin kernel, release gate, frozen UI manifest or existing registered oracle is changed by this PR. Full OLM render corpora and AE comparisons were not rerun for X03.

## Windows and remaining work

Local validation is on Apple Silicon. The Windows harness target check is compile-only. The native worker, original-AEX click/drag/keydown lifecycle, Windows deep-chain runtime and native AE behavior were not executed locally. A portable test links the actual native UI event dispatcher, but does not substitute for Windows runtime verification. GitHub Actions results are recorded separately below.

Follow-up work remains for native instruction/RVA/pointer-chain watches; paired native/guest ROI and negotiated geometry fixtures; interactive Mac custom UI and font rasterization; exhaustive suite/version/slot coverage (including ACE and arbitrary streams); deep previews, additional image chooser formats, audio/timeline, and shared diagnostic UI. The existing RadialBlur wall-limit and selector-entry capture boundaries remain open.

## Local review

A separate local reviewer reviewed `git diff origin/main...HEAD` before publication. The pre-integration boundary was `13bda6be`; X02 merged without conflicts, and `origin/main` was already an ancestor. The reviewer then reviewed the integrated guides and formatting delta. One accepted finding corrected the guide's Mac chain raw channel order by following the final artifact writer; the amended diff was re-reviewed with no remaining findings.

Rejected findings: none. Accepted unresolved findings: none.
Reviewed-boundary SHA: `e483fc65ebd6bb7c66932d15c3922472690309e9`.

This combines the F54 PR draft and F54b/F54c/X01/X01b report material. No issue was claimed under the owner's ticket exception; no issue is implicitly closed.

## CI correction

The first run on `08300c3f` failed only the Windows guest full-plane snapshot test (709 passed, 1 failed, 3 ignored in that test binary). The failure stopped at the existing wall bound before the synthetic RET executed. The identified cause is excessive host-side work while encoding the 132,710,400-byte capture with per-byte allocations; the local timing comparison below supports that diagnosis. Replace the shared hex encoder with a once-reserved ASCII encoding loop; preserve byte output, watch bounds and timeout defaults. Add empty/leading-zero/all-256-value behavioral checks. Independent local review of the complete delta found no remaining issues; no findings were rejected.

On the same Mac debug build, the full-plane test passed before in 25.26 seconds and after in 12.08 seconds. This timing is local evidence, not a Windows timing claim. The first failed run is https://github.com/onmokoworks/AEXCompat/actions/runs/40257857610 .

After the correction, the full Release guest suite passed again: 720 library + 10 CLI + 8 math tests, zero failures, 3 ignored. The new hex test also passed in debug. Release guest rebuilt successfully. Other local harness/transport checks above were run at `08300c3f`; this correction only changes trace hex encoding.

## Final CI

All 21 jobs succeeded on reviewed head `e483fc65ebd6bb7c66932d15c3922472690309e9`: https://github.com/onmokoworks/AEXCompat/actions/runs/40258815367 . The Windows guest binary reports 711 passed / 0 failed / 3 ignored, including the full-plane snapshot test; CLI 10 and math 8 passed. The standard CI native/probe/Python suites also passed. This does not claim the original-AEX/native-AE parity follow-ups listed above were run.
