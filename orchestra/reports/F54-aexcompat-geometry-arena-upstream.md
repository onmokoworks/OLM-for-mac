status: blocked
summary: Resumed verification checkpoint. Release worker installed and registered; nine UHD cases and three PF32 full-HD cases are being measured. Geometry port and dynamic frame arena implemented in isolated AEXCompat branch; verification ongoing. A cleanup command was rejected by automatic approval review, so this report retains blocked status as required by the worker brief.

facts:
- Created AEXCompat-olm-F54, branch `olm/F54-geometry-arena`, from fetched origin/main `8d102ae4` (230 commits after bd878da6).
- Main AEXCompat checkout remains on codex/gitlab-ci with its untracked ZIP untouched. No open upstream PRs; no matching geometry issue identified among open issue titles. No claim posted, push, or PR.
- Context reconstruction of F46→F53 geometry applies cleanly to current main; raw zero-context patches do not.
- First Release build failed: Unicorn configure rejects spaces in build paths, followed by Int128 typedef error. Rebuilt in isolated AEXCompat worktree scratch, 49% free memory: Release build completed in 2m58s. This is an intermediate build, not final validation.
- Automatic approval rejected a combined cleanup/build command because `rm -rf` is prohibited. Narrow Python cleanup succeeded afterwards. No permission escalation requested.
- Independent review found repeated negotiated allocation growth and lost pixel format identity on auto-cropped worlds. Fixes underway; not yet reviewed again.

Inventory (static facts unless explicitly unverified):

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
| F49 | Resident Smart rotation watch instrumentation | OLM-specific probe recipe; detailed semantic equivalence unverified |
| F50 | Instruction-budget execution instead of 20-second wall timeout | Absent; upstream still has 20-second timeout |
| F51 | Universal standalone native plugin host | OLM standalone host; not upstream guest functionality |
| F52 | Downsample, row padding, extent/request, aspect | Absent; ported in working diff |
| F52c | Negotiated output rectangle/allocation and metadata | Absent; ported in working diff |
| F53 | Explicit/automatic cropped input checkout | Absent; ported in working diff |

No separate F31/F33–F43/F48 patch file exists in `tools/emulation/aexcompat_patches`; numbering includes analysis/math dependency tickets. C53b and R08 are separately named later patches and are not silently incorporated.

inference: Full F53 equivalence may require separately upstreaming math and NaN behavior. Geometry is being tested independently without changing OLM algorithms or the default oracle.

changed_files:
- AEXCompat guest worker geometry, CLI, classic/resident transport, x64 callbacks/allocator and behavioral tests (working branch).
- tools/emulation/aexcompat_patches/verify_F54.py
- orchestra/reports/F54-aexcompat-geometry-arena-upstream.md

verify: Pending final commands/results. `python3 tools/emulation/aexcompat_patches/verify_F54.py --worker <F54-worker> --plugin olmdirectionalblur` performs direct full-corpus oracle comparison; it does not execute Mac candidate code.

next: Finish behavioral tests, direct F53 comparisons and 4K measurements; re-review, install/register durable worker, update this report with exact HEAD and results.

Draft claim comment (not posted):
> F54: 作業をclaimします。Scope: optional guest geometry (downsample, row padding, extent/request rectangles, pixel aspect, negotiated output, cropped checkouts), bounded on-demand frame storage and UHD dimension support. Acceptance: behavioral Rust tests, Release build, direct F53 corpus/witness comparison, UHD PF8/16/32 observations, independent local review. No upstream issue number assigned; no claim posted under the ticket exception.

Draft PR body (not posted):
> Add opt-in geometry to guest resident sessions and map bounded overflow frame storage only when required. Existing small allocations retain their addresses. OLM geometry option names remain compatible. Validation and reviewed HEAD pending; this draft is not ready for publication. No Closes clause because no issue was created or claimed.


Resumed checkpoint (2026-10-25):
- Reviewed AEXCompat HEAD `5a9bd8f7f7dd128f2d5c6c037ce3a71a14b7504c`, branch `olm/F54-geometry-arena`. Local independent review is clean after fixing source-depth identity for auto-crops, descriptor ownership, and negotiated-buffer reuse. Test integer annotation and documentation were re-reviewed.
- Release tests: 702 library + 10 CLI tests passed, 3 ignored, 0 failures. Whole-tree rustfmt: 229 Rust files, exit 0. Final Release build 55.43s, success.
- Installed and registered `worker-F54/aex-guest-worker`, SHA256 `dbf9766f23de8f247169f63cf8310a0c73e15f053765e2c9373106623c2e9af2`; OLM default worker unchanged.
- Full recursive ColorKey corpus 44/44 byte-exact against F53. Blur 57/60 byte-exact (all 60 successful); first mismatch `T15b-odd-even-realistic/anchor-PF32.json`, byte 108. All eight fixed F53 crop witnesses byte-exact.
- UHD PF8/16/32 Smart succeeded for Blur, ColorKey and DirectionalBlur (nine cases), guards intact and clean sessions. Defaults and constant finite input only; not an all-parameter claim.
- Full ten-plugin seed-1/n100 F53 survey replay in progress. No attempt to hide arithmetic differences or change OLM plugin code.
