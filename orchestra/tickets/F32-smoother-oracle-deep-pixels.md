# F32: Smoother v1 oracle — PF16 DEEP_PIXELS callback and PF8 host disagreement

## Background (facts; read `orchestra/reports/T11-triage-smoother.md` and `F22-smoother-classifier-stack-ub.md`)
Smoother v1 is Classic-only (F18). Seed 1 n300: 62 exact / 29 mismatch / 95 refusal /
114 uncompared.
- **114 uncompared (PF16):** the reference worker rejects them with
  `legacy new-world requested unsupported DEEP_PIXELS`. This is an emulator callback gap, not a
  Mac problem.
- **29 mismatch (PF8):** a second original-AEX Classic harness matches Mac on all 29, but the
  frozen worker differs on all 29. No first differing internal stage was captured.
  Investigate before trusting either host.
- **95 refusal:** unsupported PF32 inputs; the original advertises deep color but not float.
  Leave them as they are.
- Smoother imports no transcendental math (only ceilf/floorf), so this ticket is independent
  of the UCRT work.

## Goal
Build a reference worker variant that supports the DEEP_PIXELS (16-bpc) callbacks Smoother
requests. Resolve the PF8 host disagreement with evidence.

## Steps
1. **DEEP_PIXELS.**
   - Find exactly which suite/callback the original requests (selector, suite name and
     version). Check the AE SDK headers and how AEXCompat implements the 8-bpc counterpart.
   - Implement it in a source copy at `~/.cache/olm-emu/src-F32/`, starting from the F30 source
     `~/.cache/olm-emu/src-F30` or by re-applying F29/F30 patches from
     `tools/emulation/aexcompat_patches/`.
   - Build to `~/.cache/olm-emu/worker-F32-deep/` and add an INDEX entry.
   - Commit the patch and build script to `tools/emulation/aexcompat_patches/`.
   - Semantics must follow the AE SDK documentation (16-bit channel range 0..32768). Cite the
     header lines you used.
2. **Validate.** Every non-Smoother corpus must replay byte-identically under F32 vs F30. Rerun
   Smoother seed 1 n300 under F32 and report how the 114 move (exact / mismatch).
3. **PF8 host disagreement.** For the 29 cases, find the first internal state that differs between
   the frozen worker host and the second harness: InData fields, world/rowbytes, parameter
   unions, callback results, checkout. Decide which one matches the AE SDK contract.
   - If the worker host is wrong, fix it in the F32 worker, as a separate commit or patch.
   - If the Mac port is wrong, fix it in Mac code generally.
4. Under the strict acceptance rule (no exact → non-exact; admitted outputs exact), report E/M/R/U
   before and after.

## Rules
- Use 1-2 processes. Check `memory_pressure` before the Rust build and do not build under 30% free.
- Delete build trees afterwards.
- Do not change the fuzzer default worker; F31 is switching it to F30 in parallel. Propose the F32
  switch in `next`.
- No other plugin code changes.
