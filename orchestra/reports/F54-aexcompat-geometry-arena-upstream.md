status: blocked
summary:
- Geometry and bounded on-demand UHD frame storage are implemented and locally reviewed in isolated AEXCompat branch; no push or PR.
- Release tests: 712 passed, 3 ignored; all nine UHD Smart and three PF32 full-HD cases succeeded.
- Full ColorKey 44/44 and Smoother2 15/15 corpora plus eight fixed F53 crop witnesses are byte-exact.
- Full F53 equivalence is blocked: Blur/RadialBlur arithmetic differences and Smoother legacy DEEP_PIXELS support remain.
- Durable worker is registered; OLM's default oracle, plugins, release gate, ledger and MAIN are unchanged.

facts:

AEXCompat branch: `olm/F54-geometry-arena`.
Final and independently reviewed HEAD: `5a9bd8f7f7dd128f2d5c6c037ce3a71a14b7504c`.
Base: fetched origin/main `8d102ae4` (230 commits after `bd878da6`). Main AEXCompat worktree and all other existing worktrees were not modified.

The isolated worktree was created in the previous run as requested. This resume retained WIP commit `871a1623`, fixed/reviewed descriptor ownership, negotiated-output allocation reuse and mixed-depth cropping (`862227dd`), then committed documentation and the test type annotation (`5a9bd8f7`). Independent review rechecked the entire diff and subsequent changes; no accepted outstanding or rejected findings. Claim and PR remain drafts only; no matching geometry issue number was assigned.

Inventory against the pinned upstream base (static inspection; no numerical equivalence inferred from import names):

| Patch/recipe | Change | origin/main equivalent |
|---|---|---|
| F29 SSE NaN order | Vendored Unicorn first-NaN SSE operand selection, separate x87 policy | Absent (`x86_sse_nan_order` absent) |
| F30 UCRT math | Bundled math crate and float imports/probes | Partial import overlap (atan2f added upstream); implementation is host math, not bit-equivalent UCRT |
| F32 deep pixels | Legacy new-world DEEP_PIXELS selects PF16 | Absent; patch still applies |
| F44 msfloat | Microsoft float math implementations | Absent; no olm-ucrtmath crate |
| F45 msdouble | Microsoft sin/cos/exp double hooks | Absent; no olm-ucrtmath crate |
| F46 pow | Microsoft double pow hook | Absent; no olm-ucrtmath crate |
| F47 | Native plugin load-only bridge | Separate OLM experimental bridge; not geometry |
| F47b/c/d | Native lifecycle/shared-arena Smart bridge | Separate OLM bridge sources; not present as those implementations |
| F49 | Resident Smart rotation watch instrumentation | Absent as a dedicated recipe: opt-in resident Smart rotation watches, first/all occurrence variants, 1 MiB capture cap; generic trace facilities already exist upstream |
| F50 | Instruction-budget execution instead of 20-second wall timeout | Absent; upstream still has 20-second timeout |
| F51 | Universal standalone native plugin host | OLM standalone host; not upstream guest functionality |
| F52 | Downsample, row padding, extent/request, aspect | Absent; implemented in reviewed branch |
| F52c | Negotiated output rectangle/allocation and metadata | Absent; implemented in reviewed branch |
| F53 | Explicit/automatic cropped input checkout | Absent; implemented in reviewed branch |

No separate F31/F33–F43/F48 patch file exists in `tools/emulation/aexcompat_patches`; numbering includes analysis/math dependency tickets. C53b and R08 are separately named later patches and are not silently incorporated.


Implemented option mapping: `--downsample-x/y num/den`, `--rowbytes-pad`, `--extent-hint`, `--request-rect`, `--pixel-aspect num/den`, `--negotiate-output 1`, and `--checkout-rect l,t,r,b|auto`. These are the existing OLM F52/F52c/F53 names; no fuzz-adapter switch is needed. `docs/OLM_SESSION_GEOMETRY.md` in AEXCompat documents packed payload/full-layer coordinates and fixture-layout restrictions. With options absent, existing paths retain their small allocation addresses and default geometry; regression tests pass, but this is not an exhaustive proof of unchanged outputs.

The render cap is 3840x2160. Frame overflow pages are mapped only on demand within a separate bounded 2 GiB address range; it is not a fixed 2 GiB reservation. Negotiated buffers reuse capacity, and cropped descriptor allocations/format registrations are released at scope completion. Behavioral tests cover allocator bounds, crop depth/stride/ownership including mixed input/output formats, and geometry validation.

Commands/results:
- `cargo build --manifest-path guest/Cargo.toml --release -p aex-guest-worker -j 1`: final build success in 55.43 seconds.
- `cargo test --manifest-path guest/Cargo.toml --release -p aex-guest-worker -j 1`: 702 library + 10 CLI tests passed, 3 library tests ignored, zero failures; doc-tests zero. This is the guest worker's behavioral self-test coverage, not the Windows C++ minihost selftest.
- `rustfmt --edition 2024 --check --config skip_children=true` over all 229 tracked `.rs` files: exit 0. `git diff --check`: pass.
- Memory checks before resumed Rust builds: 53%, 52%, 54%, and 50% free, all above 30%. Processes were serial except one build plus one emulator; never more than two.
- Early resumed test compile found an ambiguous integer type in the new crop test; explicit `i32` fixed it, and the full tests above passed. Previous-run build failures from a space-containing target path and a cleanup auto-review rejection were retained in the checkpoint; the final build used the isolated AEXCompat scratch path and narrow Python cleanup succeeded. No permission escalation was used.
- Installed `~/.cache/olm-emu/worker-F54/aex-guest-worker`, SHA256 `dbf9766f23de8f247169f63cf8310a0c73e15f053765e2c9373106623c2e9af2`, registered once in INDEX under its lock. Source manifest, current HEAD, binary hash and unique INDEX binding were checked together: PASS. Metadata is in `F54-evidence/build.json`.
- F53 baseline SHA256: `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`.

Direct equivalence (original AEX through both workers; no Mac candidate build/execution):

| Recursive full corpus | Successful byte-exact | Successful byte-different | Total |
|---|---:|---:|---:|
| ColorKey | 44 | 0 | 44 |
| Smoother2 | 15 | 0 | 15 |
| Blur | 57 | 3 | 60 |

All eight fixed F53 witnesses (DirectionalBlur and Smoother2, explicit/automatic crop, zero/nonzero origins) matched successful bytes and output rectangles. Full seed=1, n=100, realistic-v2 survey replay follows. Smart for nine plugins; Smoother uses its supported Classic route. Matching non-success **statuses** are not byte-equivalence evidence and do not assert identical diagnostics.

| Plugin | Successful exact | Matching non-success status | Successful byte difference | Status difference |
|---|---:|---:|---:|---:|
| olmblur | 97 | 0 | 3 | 0 |
| colorkeep | 100 | 0 | 0 | 0 |
| olmcolorkey | 100 | 0 | 0 | 0 |
| olmdirectionalblur | 100 | 0 | 0 | 0 |
| olmdistancegradation | 97 | 3 | 0 | 0 |
| olmkirakira | 99 | 1 | 0 | 0 |
| olmsmoother2 | 100 | 0 | 0 | 0 |
| olmtoondilate | 100 | 0 | 0 | 0 |
| radialblur | 77 | 12 | 11 | 0 |
| olmsmoother | 31 | 35 | 0 | 34 |
| Total | 901 | 51 | 14 | 34 |

First differences:
- Blur full corpus: `T15b-odd-even-realistic/anchor-PF32.json`, byte 108; both output rectangles `[0,0,2,336]`, 10,752 bytes. F53 SHA256 `04be44bc973799346920354d6fbe11b19d8753fb73eb1a07352af90e333a45a5`, F54 `71d79ced1af4f00b865ef9566e789e6b4975f3ee1ef3841733a9d5803ba451b9`. Other mismatches: `seed1_case000040_1e01a8a5cbd2.json` byte 31,292 and `seed1_case000099_9b13c27c2f2e.json` byte 116.
- Blur survey index 20: byte 4, expected bytes `4151193f3a5b083f`, actual `3f51193f395b083f`.
- RadialBlur survey index 17: byte 32, expected `0000c0ff0000803f`, actual `4523c17f0000803f` (different NaN bits in the first float).
- Smoother survey index 1: F53 succeeds with 8 output bytes; F54 rejects with `legacy new-world requested unsupported DEEP_PIXELS`. All 34 status differences are F53 success / F54 rejection. The other 35 non-success statuses are shared.

Home-directory prefixes in diagnostic text are explicitly redacted in shareable evidence; original logs remain in scratch. Hashes and numerical observations are unchanged. All measured hashes, diagnostics, times, and first differences are in `F54-evidence/*-results.jsonl`; corresponding summaries record worker/AEX hashes where collected. Inputs are reproduced from committed corpora or the seed-1 generator in the committed verification driver.

4K / full-HD measurements (Smart, deterministic finite constant ARGB and declared default controls; successful guards/checksum/size/route/session checks):

| Plugin | Size mode | PF depth | Adapter wall seconds | Maximum worker RSS bytes | Status |
|---|---|---:|---:|---:|---|
| olmblur | 4k | 8 | 9.120 | 350,060,544 | ok |
| olmblur | 4k | 16 | 10.764 | 482,983,936 | ok |
| olmblur | 4k | 32 | 10.161 | 755,007,488 | ok |
| olmcolorkey | 4k | 8 | 3.911 | 243,204,096 | ok |
| olmcolorkey | 4k | 16 | 2.925 | 443,596,800 | ok |
| olmcolorkey | 4k | 32 | 2.276 | 786,759,680 | ok |
| olmdirectionalblur | 4k | 8 | 0.382 | 242,319,360 | ok |
| olmdirectionalblur | 4k | 16 | 0.361 | 441,696,256 | ok |
| olmdirectionalblur | 4k | 32 | 0.603 | 840,253,440 | ok |
| olmblur | hd32 | 32 | 6.643 | 217,989,120 | ok |
| olmcolorkey | hd32 | 32 | 0.642 | 218,529,792 | ok |
| olmdirectionalblur | hd32 | 32 | 0.310 | 217,071,616 | ok |

`4k` = 3840x2160; `hd32` = 1920x1080. Time includes adapter I/O and process execution; RSS is `/usr/bin/time -l` maximum resident set size of the worker. These runs establish these inputs/defaults only, not arbitrary expensive settings. The timing rows' `equal:false`/`different` fields are inapplicable single-worker comparison placeholders, not mismatches; their `status:ok` is the measured acceptance result. Maximum observed worker RSS is 840,253,440 bytes. Frame input/output bytes are streamed through scratch files; regenerable Rust build trees have been deleted. No task-owned processes remain.

inference:
- The absent OLM math and SSE NaN-order patches are plausible causes of Blur/RadialBlur numerical differences; this ticket did not isolate their causal contributions. No tolerance or expected-byte fixes were introduced.
- Smoother's diagnostic identifies the missing legacy DEEP_PIXELS capability inventoried as F32. This is outside the new geometry implementation and should be reviewed as a separate upstream dependency.
- Geometry is proven on the two completely matching corpora, eight fixed crop witnesses and successful survey rows above. Full replacement of the F53 oracle is not justified, so the overall status stays blocked. This is an acceptance/dependency boundary, not a claim that the geometry implementation failed its review.

changed_files:
- AEXCompat: `guest/crates/aex-guest-worker/src/{classic.rs,geometry.rs,lib.rs,main.rs,resident.rs,x64.rs,x64/callbacks.rs,x64/engine.rs,x64/tests_support.rs,x64/types.rs}` and `docs/OLM_SESSION_GEOMETRY.md`.
- OLM: `tools/emulation/aexcompat_patches/{verify_F54.py,install_F54.py}`, this report, and `orchestra/reports/F54-evidence/*`.
- Authorized external cache: `worker-F54/` and its INDEX entry only; no default-worker change.

verify:
```sh
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
F54_WORKER="$HOME/.cache/olm-emu/worker-F54/aex-guest-worker"
for plugin in olmcolorkey olmsmoother2 olmblur; do
  python3 tools/emulation/aexcompat_patches/verify_F54.py --worker "$F54_WORKER" --plugin "$plugin" --jobs 1
done
for plugin in olmdirectionalblur olmsmoother2; do
  python3 tools/emulation/aexcompat_patches/verify_F54.py --worker "$F54_WORKER" --plugin "$plugin" --mode witness --jobs 1
done
for plugin in olmblur colorkeep olmcolorkey olmdirectionalblur olmdistancegradation olmkirakira olmsmoother2 olmtoondilate radialblur olmsmoother; do
  python3 tools/emulation/aexcompat_patches/verify_F54.py --worker "$F54_WORKER" --plugin "$plugin" --mode survey --n 100 --jobs 1
done
for plugin in olmblur olmcolorkey olmdirectionalblur; do
  python3 tools/emulation/aexcompat_patches/verify_F54.py --worker "$F54_WORKER" --plugin "$plugin" --mode 4k --jobs 1
  python3 tools/emulation/aexcompat_patches/verify_F54.py --worker "$F54_WORKER" --plugin "$plugin" --mode hd32 --jobs 1
done
git diff --check
```
Expected: corpus and survey tables above, eight exact crop witnesses, nine UHD and three HD successes. Timings vary; failed original execution categories may vary with runtime budgets. The driver records measurements and does not exit nonzero merely because workers differ. It never builds/runs a Mac candidate.

To rebuild/test inside the isolated AEXCompat worktree, check `memory_pressure` for at least 30% free, set `TMPDIR` and `CARGO_TARGET_DIR` to its `orchestra/state/F54-aexcompat-geometry-arena-upstream/` scratch (target in a `build` subdirectory), then run the exact Cargo commands above with one job. Rebuilds may differ in binary hash due to revision/build paths; do not overwrite the registered oracle. `install_F54.py --source <clean-reviewed-worktree> --binary <release-worker>` installs once and rejects a conflicting cached binary. The 11-file source manifest and HEAD in `F54-evidence/build.json` bind the delivered build. Full Rust workspace, Windows-native C++/AE/SDK gates and CI were not run; no broker dispatch is used by these comparisons.

next:
- Review this isolated upstream branch and the measured geometry/UHD scope.
- Follow-up upstream F32 legacy world support and separately review F29/F30/F44/F45/F46 numerical dependencies; isolate and close the recorded Blur/RadialBlur differences before any default-worker switch.
- User decides whether to post a claim, push or open a PR; none was performed. Draft text is committed in [claim-draft.md](F54-evidence/claim-draft.md) and [pr-draft.md](F54-evidence/pr-draft.md).
