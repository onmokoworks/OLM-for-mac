# F39: RadialBlur retained fixtures — re-adjudicate 18 numeric failures against the F32 oracle

## Facts (F36, `orchestra/reports/F36-fixture-runner-worktree-and-triage.md`)
- 18 fixed-fixture numeric failures, all RadialBlur (commands 152–181): Rotation, Zoom, fades, PF16/PF32.
- They bisect to old RadialBlur commits: f5a74754, 7a7f53fe, b07f5c00, ea3a16c5/f3765f38.
  Four of these commands keep an exact final output and differ only in intermediate planes.
- Their expected bytes were captured from the original AEX under an older worker. That worker
  used host Apple libm for expf/atan2f, and Unicorn's wrong SSE NaN order.
- Today the default oracle is F32: UCRT-exact expf/atan2f/powf plus the NaN fix. The Mac
  RadialBlur uses `ucrtmath`. Fuzz: RadialBlur Smart is 240 exact / 0 mismatch.

## Do
For every failing command:
1. Re-run the original AEX with the **F32 worker** on that fixture's exact inputs and controls.
   Compare raw bits with (i) the stored expected bytes and (ii) HEAD's Mac output.
2. Classify each command:
   - **A — oracle drift**: F32 AEX equals Mac HEAD, but the stored expectation differs.
     Generate a new fixture version from F32 AEX output with a provenance JSON (AEX sha, worker
     sha, controls). Point the test at it and keep the old files as superseded, as F35 did.
   - **B — real Mac regression**: F32 AEX equals the stored expectation, or neither matches,
     and Mac differs. Find the first divergent stage and fix it generally. Keep the fuzz baseline:
     RadialBlur corpus 35/35, seed 1 n300 no exact loss.
   - **C — intermediate-plane-only assertions with exact final output**: list them. Propose
     whether the intermediate assertion encodes AEX truth or an old Mac trace. Do not delete
     assertions.
3. Never generate expected bytes from Mac output.
- Do not touch the release gate/ledger. Use 1-2 processes. Use the F36 asset resolver for MAIN assets.
