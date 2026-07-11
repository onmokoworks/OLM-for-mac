# Design: OpenCV detour layer for the .aex emulator (Fable 5, 2026-07-06, rev 2)

Performance lever "Bucket B" from README PERF. Goal: turn ~1e9-instruction
emulated OpenCV ops into native calls, bit-matching the emulated result, so
distanceTransform/threshold/etc. witnesses run in seconds not minutes — and so
"drive from a higher entry point" (Bucket C) becomes affordable.

rev 2 (2026-07-06): reviewed against the DistanceGradation decomp, the real
`aex_loader.py` API, and live experiments in the venv. Three premises of rev 1
were wrong and are corrected here: (a) the detour seam passes **IplImage**
(OpenCV C API), not `cv::Mat`; (b) `opencv-python==4.5.5` cannot be imported in
the current venv (verified); (c) the emulated OpenCV runs the **SSE** dispatch
path — Unicorn 2.1.4 has no AVX/AVX2 (verified). Details inline, each marked
FACT (read from decomp / verified by experiment) or INFERENCE.

## 1. Goal / non-goals

**Goal.** When emulated `.aex` code calls a known OpenCV primitive, intercept the
call, read the input image from guest memory, run the *same* operation natively,
write the result back into the guest dst buffer, set the return registers, and
let emulation continue — producing output bit-identical to what full emulation
would have produced.

**What the dual-run does and does not prove.** The dual-run gate proves
`detour ≡ full emulation`. It does NOT by itself prove `≡ Windows hardware`:
the emulated OpenCV dispatches its **SSE** kernels (FACT: Unicorn 2.1.4 raises
`UC_ERR_INSN_INVALID` on `vaddps`, and its CPUID reports AVX=0/AVX2=0/SSE4.2=1
— verified by direct experiment 2026-07-06), while a real Windows machine
dispatches AVX2 kernels for the same ops. For exact integer ops (threshold,
precise EDT) the two paths agree by construction; for SIMD-width-sensitive
float ops (boxFilter, INTER_LINEAR resize) "bit-match the emulator" may
silently differ from "bit-match Windows". Any float op therefore needs a
**Windows capture** as its conformance gate, not just the dual-run (§5, §8 P3).

**Non-goals.**
- NOT reimplementing the plugin's own logic. We detour the *library* (OpenCV), and
  keep the plugin's unique code fully emulated. Detouring the plugin's own wrapper
  (e.g. `FUN_181174760`, which owns real OLM decisions: THRESH mode selection by
  `param_8`, clamping against `DAT_181504a90` — FACT, decomp 3542508ff) would mean
  trusting our reimplementation instead of the binary — that defeats
  binary-grounding. This is the core architectural choice.
- NOT a general OpenCV shim. Only the specific primitives the OLM plugins call,
  added one at a time behind a validation gate.

## 2. Why detour the library, not the plugin (rationale)

The plugin's value-add (field ownership, compose, scatter) is exactly what we must
ground faithfully → keep it emulated. OpenCV primitives are *known, versioned,
reproducible* → safe to service natively **if** we match the algorithm. So the
seam is: emulate everything the plugin wrote; shortcut only what it delegated to
OpenCV.

The seam is even friendlier than rev 1 assumed: the plugin calls OpenCV through
the **C API** (`cvThreshold`, `cvDistTransform`, `cvResize`, ... — FACT, §7),
whose arguments are simple by-value pointers/doubles and whose dst is always
caller-allocated (§6). No `_InputArray` decoding, no `Mat::create` replication.

## 3. Components

1. **`cv_bridge.py` — IplImage <-> numpy bridge.** Reads/writes a guest
   **IplImage** (not cv::Mat — see §4): decodes `nChannels`, `depth`, `width`,
   `height`, `imageData`, `widthStep`, and materializes a numpy view over guest
   memory (via `loader.read_bytes` / `write_bytes`). Writes results back into the
   dst image's existing `imageData` buffer (always pre-allocated at this seam,
   §6). Also provides a **stack-argument reader** (`read_stack_arg(loader, n)`),
   since `install_callback` handlers only receive RCX/RDX/R8/R9 (FACT,
   `aex_loader._read_int_args`) and C-API ops pass their 5th+ args on the stack.
2. **`register_opencv_impls(loader, ops=...)` — op registry.** Installs
   `loader.detour_function(addr, label, handler)` at each confirmed OpenCV entry
   point. Mirror of the existing `register_libm_impls` pattern.
3. **Dual-run validator (`test_opencv_detour.py`).** For every op, runs a small
   input BOTH ways — full emulation vs detour — and asserts bit-identical output.
   Because `detour_function` irreversibly patches the first 12 bytes of the
   target (FACT, aex_loader.py:329), the dual-run instantiates **two separate
   `AexLoader`s** (one clean, one detoured). An op is only trusted after its
   dual-run passes. This is a first-class, non-optional part of the design.

## 4. Guest image decoding — it's IplImage, and the layout is a frozen C ABI

**FACT (decomp):** the objects passed to the detour targets are IplImage
pointers, not cv::Mat. Evidence chain:

- `FUN_181395030` is a 4-qword **OLM wrapper ctor** `{iplPtr@0, hdrHandle@8,
  dataHandle@0x10, context@0x18}` (decomp 3999742) — not a Mat ctor. Call sites
  pass `wrapper[0]` (the IplImage*) into the OpenCV entries.
- `FUN_181395230` allocates a **0x90-byte header via the AE PF Handle Suite**
  (0x90 = sizeof(IplImage) on x64) and fills `+0x50 imageSize`, `+0x58
  imageData`, `+0x88 imageDataOrigin` — the IplImage layout exactly (decomp
  3999814ff). Note it allocates through `wrapper[3]+0x180` (SPBasic), so
  driving it requires the existing suite mocks.
- `FUN_1811765a0` is `cvGetSize` (FACT: carries the literal
  `"Array should be CvMat or IplImage"` and the OpenCV source path).
- The compute entries themselves convert via `FUN_18118ffc0` (cvarrToMat) on
  entry (FACT, e.g. decomp 3797639).

So `cv_bridge` decodes the **public, frozen IplImage C ABI** (x64 offsets:
`nChannels@0x8`, `depth@0x10`, `width@0x28`, `height@0x2c`, `imageSize@0x50`,
`imageData@0x58`, `widthStep@0x60`, `imageDataOrigin@0x88`). No sentinel-based
offset pinning ceremony is required; a one-time sanity check in the P0 dual-run
(dump a header the binary built via `FUN_181395230` and check
width/height/depth against the known input) is enough to catch a wrong-seam
surprise. rev 1's `cv::Mat`/MatStep decoding plan and `flags&0xFFF` type decode
do not apply at this seam.

Depth decode is IplImage-style: `depth` is `IPL_DEPTH_8U=8`, `IPL_DEPTH_16U=16`,
`IPL_DEPTH_32F=0x20`, ... (sign-flagged values use bit 31); channels come from
`nChannels`; row stride is `widthStep` in **bytes**.

## 5. Bit-exactness strategy (the real risk)

Version grounding: **OpenCV 4.5.5, statically linked, confirmed directly in the
DistanceGradation binary** — `FUN_1812b6a40`'s assert path embeds `"cvThreshold"`
and `"C:\Users\devbuild\Documents\4.5.5\sources\modules\imgproc\src\thresh.cpp"`
(FACT, decomp 3797673). (Stronger than rev 1's indirect KiraKira grounding.)

**Dependency reality (verified 2026-07-06):** `opencv-python==4.5.5.64` *installs*
into the venv (cp37-abi3 macosx_11_0_arm64 wheel) but **fails to import** against
numpy 2.5.1 (`ImportError: numpy.core.multiarray failed to import`, `_ARRAY_API
not found` — built against numpy 1.x). numpy<2 has no Python 3.14 wheels, so the
pin is **unsatisfiable inside this venv**. Strategy, tiered by risk:

- **P0/P1 go cv2-free.** The exact-integer ops don't need cv2 at all:
  - `threshold` (THRESH_BINARY/TRUNC) is a per-element compare/select —
    `np.where` is trivially bit-exact for any input.
  - `distanceTransform(DIST_L2, DIST_MASK_PRECISE)` is the Felzenszwalb exact
    EDT. The Mac port already carries a Meijster EDT asserting identical output
    (`mac/OLMDistanceGradation/OLMDistanceGradation.cpp:159`); port that (or an
    equivalent exact EDT) to numpy as the native impl. INFERENCE with a stated
    bound: OpenCV's precise EDT computes squared distances in float32; they are
    exactly representable while `< 2^24`, i.e. up to ~4096 px frame diagonal
    (1920x1080 max² ≈ 4.9e6 — safely inside). Beyond that the "any exact EDT
    matches" argument breaks; re-verify if frames ever exceed it.
- **Float ops need cv2 AND a Windows gate.** If/when `cvResize(INTER_LINEAR)`,
  `boxFilter`, `GaussianBlur` are needed: run pinned `opencv-python==4.5.5.64`
  in a **sidecar venv (Python ≤3.12 + numpy 1.26)** invoked via subprocess. And
  per §1, their dual-run only proves emulation-equivalence (SSE path); accept
  them only against a **Windows SOFTWARE capture** (or document an accepted
  ≤1 ULP band with a named reason). If a float op won't match, keep it emulated
  (slow but exact) — flag, don't fake.

## 6. Detour handler contract

Each handler (signature `handler(loader, args)` per `install_callback`/detour;
`args` = RCX/RDX/R8/R9 only — FACT):

1. Decode args per the **C API** signature. For `cvThreshold(src, dst, thresh,
   maxval, type)`: src=RCX, dst=RDX, `thresh`/`maxval` are **doubles in
   XMM2/XMM3** (FACT: call site passes `(double)fVar4,(double)fVar3`, decomp
   3542553), `type` is the **5th arg on the stack**. At the detour stub RSP
   still points at the caller's return address (the 12-byte patch pushes
   nothing), so stack args live at `[RSP+0x28]` (8 retaddr + 0x20 shadow). Use
   `cv_bridge.read_stack_arg`.
2. Read src IplImage(s) via `cv_bridge` → numpy.
3. **dst allocation: none needed at this seam.** The wrapper allocates the dst
   header+data via `FUN_181395230` *before* calling the op (FACT, decomp
   3542522-3542536), so the handler only writes into the existing `imageData`
   at the existing `widthStep`. The P0 dual-run still compares the dst header
   both ways as a tripwire.
4. Run the native op (numpy for P0/P1; pinned sidecar cv2 for float ops).
5. Write the result back into dst `imageData` honoring `widthStep`.
6. Set the return per the **C API**, confirmed per op from disasm:
   `cvThreshold` returns a **double in XMM0** (the used threshold) — the DG call
   sites ignore it (FACT) but write it anyway; `cvDistTransform`/`cvResize`
   return void → RAX=0 is fine.

## 7. Confirmed / candidate entry points (from DistanceGradation grounding)

- `FUN_1812b6a40` — **cvThreshold** (FACT: name string in its assert path) — **P0**.
- `FUN_1812b15a0` — **cvDistTransform**, called as `(src, dst, 2 /*CV_DIST_L2*/,
  0 /*CV_DIST_MASK_PRECISE*/, 0, 0, 0)` (FACT, decomp 3542536) — **P1**.
- `FUN_1812aef70` — **cvResize**, NOT convertTo as rev 1 claimed (FACT: body
  computes `(double)dst_rows/src_rows`, `(double)dst_cols/src_cols`, decomp
  3791383). The DG wrapper calls it with interpolation **0 (NN)** for the mask
  downscale and **1 (LINEAR)** for the upscale-back. NN is index arithmetic →
  exact-tier (INFERENCE, verify in dual-run); **LINEAR is a SIMD float op →
  ULP/Windows-gated tier (P3), not P2.**
- `FUN_18117ca50` — normalize (6 args incl. optional mask, wraps `FUN_1811e9900`;
  structurally consistent with cvNormalize but the label is **unverified** —
  confirm before implementing) — P2.
- `FUN_1812e39d0` (KiraKira) — boxFilter FilterEngine — **P3 (Windows-gated)**.
  Note: the binary's AVX2 variant of this kernel never executes under Unicorn
  (§1); the emulated reference is its SSE path.
- Image mgmt (not detoured, used by the bridge/tests): `FUN_181395030` (OLM
  wrapper ctor), `FUN_181395230` (IplImage header alloc via PF Handle Suite),
  `FUN_1811765a0` (cvGetSize), `FUN_18118b380` (Mat release).

Each address must be re-confirmed per binary (KiraKira vs DistanceGradation are
different modules; the OpenCV is statically linked into each).

## 8. Phasing

- **P0 — cvThreshold + the IplImage bridge + validator, cv2-free.** Smallest
  exact op; proves the whole pipeline (IplImage decode, detour, stack-arg read,
  XMM0 return, write-back, two-loader dual-run). Acceptance: emulated vs
  detoured `cvThreshold` on a 16×16 IPL_DEPTH_32F input bit-identical, dst
  header identical both ways.
- **P1 — cvDistTransform (precise L2), cv2-free.** The op actually blocking the
  DG 8px lane. Acceptance: detoured EDT on representative masks, including
  no-zero/all-foreground input and 1D/1x1 shapes, bit-matches sidecar OpenCV
  4.5.5 `cv2.distanceTransform(..., DIST_L2, DIST_MASK_PRECISE)`. For ordinary
  masks with at least one zero-source pixel this also matches the Mac
  Meijster-style EDT family; for all-foreground input, OpenCV's large sentinel
  is the authority.
- **P1C — `FUN_1812aef70` same-shape copy only.** This is a narrow harness
  accelerator, not a general `cvResize` implementation. It is valid only when
  source and destination shape/dtype match; it exists so the small
  `FUN_181174760` fieldgen probe can pass through the two observed no-resize
  staging calls. Real downsample/upscale or interpolation behavior remains P2/P3
  and needs a separate gate.
- **P2 — normalize.** `FUN_18117ca50` is now confirmed as a `cvNormalize`
  wrapper on the fieldgen path. The limited detour supports only
  `NORM_MINMAX`, no mask, single-channel `float32` source/destination. It is
  validated against sidecar OpenCV 4.5.5 on ramp, binary, all-zero, and
  all-nonzero inputs, including the equal min/max behavior. Broader normalize
  forms remain disabled.
- **P2/P3 — cvResize(NN/LINEAR).** The current `FUN_1812aef70` detour remains
  same-shape copy only. Real downsample/upscale NN should be exact but is not
  implemented; LINEAR is a SIMD float op and stays Windows-gated.
- **P3 — cvResize(LINEAR), boxFilter/GaussianBlur (KiraKira).** Requires the
  sidecar cv2 venv AND a Windows SOFTWARE capture as the conformance gate (§1,
  §5). Deferred until such a capture exists; do not gate these on the dual-run
  alone.

## 9. Risks & mitigations

- **Wrong seam / wrong object model** → the P0 dual-run compares the dst header
  the binary built against what the bridge decoded; IplImage is a frozen public
  C ABI so drift risk is low.
- **Emulation ≠ Windows for SIMD float ops (SSE vs AVX2 dispatch)** → float ops
  are Windows-capture-gated, never dual-run-gated alone (§1, §5, §8 P3).
- **cv2 dependency unsatisfiable in-venv (verified)** → P0/P1 are cv2-free;
  float ops use a pinned sidecar venv via subprocess.
- **EDT float-exactness bound** → valid below 2^24 squared distance (~4096 px
  diagonal); re-verify for larger frames (§5).
- **Silent wrong detour** → an op with no passing dual-run is DISABLED by
  default; `register_opencv_impls(ops=[...])` opts in only validated ops.
- **`detour_function` is irreversible within a loader** → dual-run uses two
  loader instances (§3).

## 10. First milestone (concrete)

1. `cv_bridge.py`: IplImage decode/encode (`read_ipl`/`write_ipl`) +
   `read_stack_arg`; no new dependencies (numpy already in the venv).
2. `register_opencv_impls` with only `cvThreshold` (P0), native impl =
   `np.where` per THRESH_BINARY/TRUNC.
3. `test_opencv_detour.py`: two-loader dual-run of the DG wrapper's threshold
   call on a 16×16 IPL_DEPTH_32F input; assert bit-identical pixels AND
   identical dst IplImage header fields; write a short report (versions, op,
   input, result) per GOTCHAS fact-discipline.
4. Green = the architecture is proven; proceed to P1 (numpy exact EDT ported
   from the Mac Meijster implementation).

Acceptance for "design done": this doc + the P0 dual-run harness shape agreed.
Implementation is a follow-up; nothing here changes existing tests.
