# OpenCV detour layer — P0 implementation report (2026-07-07, Opus 4.8)

## 2026-07-17 superseding GATE C addendum

The historical GATE C blocker below is resolved for the bounded
DistanceGradation fixtures. `windows_runtime.py` now supplies an opt-in
single-thread TLS/FLS/aligned-allocation scaffold. The embedded `cvThreshold`
body and ten embedded `cvDistTransform` fixtures execute without detours, and
three complete `FUN_181174760` field-generator fixtures match their detoured
counterparts byte-for-byte. This remains a bounded host-stub execution, not a
full Windows CRT or AE-host oracle. See
`refs/conformance/olmdistancegradation_embedded_opencv_gate_c_20260717.md`.

The original blocked analysis is retained below as historical provenance.

Implements OPENCV_DETOUR_DESIGN.md rev 2 §8/§10 P0 (cvThreshold). Written after a
review found the prior agy/Gemini "implementation" had produced **nothing**.

## Review finding that preceded this work (FACT)

The design was said to have been implemented via agy→Gemini in the background.
Ground-truth check found no implementation existed anywhere:
- `find` across the repo: no `cv_bridge.py` / `opencv_impls.py` / `opencv_detour.py`
  / `test_opencv_detour.py`.
- `tools/emulation/` entirely git-untracked; no stash/worktree/branch hid them.
- `__pycache__/` held only `aex_loader`/`aex_witness` `.pyc` — no opencv module
  was ever imported or run.
- venv had only numpy 2.5.1 (no cv2).
- Design doc + README + GOTCHAS unmodified since the rev 2 write.

This matches the agy print-mode hangs observed directly the same day (47-min
hangs, zero output, zero file changes). Conclusion: the detour layer was never
built. It is now built (below), by Claude directly, not via agy.

## What was built

- **`cv_bridge.py`** — IplImage↔numpy bridge (design §4). Decodes the frozen x64
  IplImage C ABI by fixed offsets (nSize@0, nChannels@8, depth@0x10, width@0x28,
  height@0x2c, imageSize@0x50, imageData@0x58, widthStep@0x60,
  imageDataOrigin@0x88). `read_ipl`/`write_ipl` honor widthStep; `build_ipl`
  constructs a valid header (nSize=0x90 — the value the binary's cvGetSize gate
  checks) + data buffer via `bump_alloc`; `read_stack_arg` reads 5th+ args at
  `[RSP+0x28+…]` (design §6).
- **`opencv_impls.py`** — `cvthreshold_native` (pure numpy, all 5 THRESH types,
  bit-exact) + a detour handler (reads src IplImage, XMM2/XMM3 doubles, stack
  `type`, writes dst, returns thresh in XMM0) + `register_opencv_impls(loader,
  module, ops=[...])` (opt-in, mirrors `register_libm_impls`).
- **`test_opencv_detour.py`** — the validator.

## Results (FACT — `.venv/bin/python test_opencv_detour.py`)

- Bridge round-trip (uint8/uint16/float32 + 3-channel): **PASS**.
- Detour, 5 types × {float32, uint8} = 10 cases: **all PASS** — emulated body
  bypassed (3 instructions: `mov rax,imm; jmp rax` → handler → RET), dst written,
  dst IplImage header intact (design §6.3 tripwire), and output **bit-identical**
  to the exact numpy reference.

Why bit-exact vs reference == correct: threshold is a per-element compare/select
with no SIMD reduction order (design §5), so there is no AVX2-vs-numpy last-ULP
ambiguity. For this op the numpy reference IS the ground truth (also == Windows).

## Honest limitation — GATE C (emulated-equivalence gold gate) is BLOCKED

The design's strongest gate ("emulated real cvThreshold vs detour") does not run
yet. Findings (FACT, from probing the emulated FUN_1812b6a40):
1. First fault `MOV RAX,GS:[0x58]` (TEB ThreadLocalStoragePointer) — the loader
   sets GS:[0x8]/[0x10] for `__chkstk` but not the TLS pointer. `setup_tls()`
   (in the test) points TEB+0x58 at a zeroed TLS array and clears this fault.
2. Next fault at RIP=0x181187e41 inside FUN_181187e20 — OpenCV's **global
   initializer** (adjacent to env-var reads `OPENCV_DUMP_ERRORS` etc., decomp
   3539778ff). Normally run by the CRT static-init at DLL load, which the
   emulator never executes.

So GATE C needs an **OpenCV static-init scaffold** (run the module's TLS/CRT
init + static constructors, or seed the post-init globals). That is a separate
infra task. It is reported SKIPPED/BLOCKED, never faked (design §9). GATE C
matters most for the FLOAT ops (P3: boxFilter/GaussianBlur/resize-LINEAR) where
SSE-vs-numpy could differ; for exact-integer threshold, GATE B is authoritative.

## Next steps

1. **P1 — cvDistTransform (FUN_1812b15a0, DIST_L2 PRECISE)**: add a numpy exact
   EDT (port the Mac Meijster, `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:159`)
   as the native impl; extend `_OPS`; validate GATE A+B on the case_0023 mask.
2. **GATE C scaffold** (unblocks emulated ground truth, needed before any FLOAT
   op): drive the binary's CRT/TLS init + OpenCV static ctors once per loader,
   then the emulated path becomes callable and can cross-check P1's EDT and gate
   P3 float ops. Resume from the exact wall RIP=0x181187e41.
3. Wire `register_opencv_impls` into the DG witness runners once P1 lands, to
   collapse the ~1e9-instruction full-frame ops (design Bucket B).
