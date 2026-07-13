# OLMKiraKira Mode 3 live Gaussian entry and runner fix (2026-07-13)

## Decision

The returned archive remains `exact_bind_failure` and contains no accepted
Gaussian coefficient words. It is not runtime proof of the Gaussian output and
does not authorize a production implementation change.

The retained Windows CDB log does, however, prove that the desktop AE 2026 run
reached the requested live AEX Gaussian kernel entry with the expected first
call arguments. Two runner defects prevented the same run from reaching the
return capture. The replacement package fixes those defects and keeps the
intake fail-closed.

## Returned artifact

- Return SHA-256:
  `61115f8e195df4968b0a891110d6daa9439354912d730cfd5128e5a059e743fd`
- Request ID: `olmkirakira_mode3_live_gaussian_20260713`
- Run ID: `kk-mode3-f918e92e3ddb422baf1c3db362487c43`
- Returned status: `exact_bind_failure`
- Returned failure label: `hook_install`, `absolute base+RVA breakpoints not armed`

The fail-closed classifier correctly rejects this archive because its JSON has
no answered binding and no 21-word payload.

## Facts recovered from the retained CDB log

- The live module base was `0x7fffbe430000`.
- The wrapper, create, and first kernel-entry breakpoints all fired in the same
  run.
- The first kernel entry was `0x7fffbf6a54a0`, or module base plus
  `0x12754a0`.
- Its arguments were exactly `ecx=21`, `xmm1=2.5`, and `r8=5`.
- The output `cv::Mat` address was `0x000000f4237fabe0`.
- The entry return address was `0x00007fffbf69685c`. Subtracting the live
  module base gives RVA `0x126685c`.
- No `KK_KERNEL_RETURN`, `KK_CAPTURE_END`, or 84-byte coefficient file was
  produced.

## Runner defects

1. `.logopen /t cdb_trace.log` created a timestamp-suffixed filename, while the
   PowerShell runner waited for the literal `cdb_trace.log`. The runner could
   therefore report that breakpoints were not armed even after
   `KK_BREAKPOINTS_READY` was written.
2. The kernel-entry command attempted to create a nested breakpoint at
   `poi(@rsp)`. The retained command stream reached kernel entry but did not
   continue through the dynamic return capture.

## V4 desktop retry

The v4 return (SHA-256
`02865cdbd3e68c7cbecadcd2b80cf2f91d534743deb47df3523148709e32613a`)
failed at `ae_jsx_preflight`. PowerShell reported the intended argument vector
as `-m`, `-r`, and the no-space JSX path, while the observed AfterFX command
line contained only `-m`. No preflight marker, AEX binding, or coefficient word
was produced. This is direct evidence that the split `Start-Process
-ArgumentList` form is not reliable under the active PowerShell 5.1 host.

## Replacement package

The v5 package:

- passes `-m -r "<jsx>"` as one explicitly quoted argument string for both
  the minimal preflight and the full render;
- uses `.logopen` without `/t`, so CDB and PowerShell share one exact log path;
- pre-arms a fixed return breakpoint at module base plus `0x126685c`;
- keeps the first entry breakpoint limited to recording the output `cv::Mat`;
- captures exactly 84 bytes at the fixed return breakpoint;
- rejects whitespace in the CDB script, trace, and coefficient paths; and
- requires the wrapper/create/kernel/return bindings, one run identity, the
  exact first-call arguments, and exactly 21 words before classifying the
  result as answered.

## Limits

- RVA `0x126685c` is grounded for this pinned AEX callsite and must not be
  generalized to another AEX hash.
- The 21 live coefficient words are still missing.
- The synthetic Unicorn Gaussian output remains an emulation-path witness only.
- No production KiraKira code changes and no AE-exact promotion are allowed
  until the fixed package returns an accepted same-run payload.
