# tools/emulation -- Milestone 1: Unicorn-based .aex emulation harness

Goal: run individual internal functions from the compiled `OLMRadialBlur.aex`
(and, in principle, the other OLM `.aex` plugins) directly on macOS/arm64
via Unicorn Engine's x86-64 emulation, without needing a Windows box, a
debugger, or a full After Effects host process. This lets us typed-dump
intermediate values (e.g. the `+0xf250/+0xf252/+0xe`-style offsets inside
`FUN_180004640`, the Rotation entry point) locally.

This directory is Milestone 1 only: a working PE loader + calling-convention
harness, validated against two functions. It does **not** yet drive
`FUN_180004640` end-to-end -- see "Known limitations / what's needed for M2"
below.

## Setup

```bash
cd tools/emulation
python3 -m venv .venv
./.venv/bin/pip install unicorn capstone pefile

# Optional: Sidecar venv for OpenCV detour oracle tests (test_opencv_detour.py)
python3.12 -m venv .venv-cv455
./.venv-cv455/bin/pip install "numpy<2" "opencv-python-headless==4.5.5.64"
```

Verified working versions (as of this milestone): `unicorn==2.1.4`,
`capstone==5.0.7`, `pefile==2024.8.26`, on macOS arm64 (Sequoia), Python
3.14. Unicorn's bundled x86_64 backend emulates the target architecture in
software, so running an x86-64 PE on Apple Silicon works with no special
configuration.

## Files

- `aex_loader.py` -- the loader/harness. Key pieces:
  - `AexLoader(path)` parses the PE with `pefile`, maps all sections into a
    Unicorn `UC_ARCH_X86 / UC_MODE_64` instance at the PE's preferred
    `ImageBase` (`0x180000000` for all the OLM 64-bit `.aex` files inspected
    so far), and applies base relocations if a different load address were
    ever used (not currently exercised -- see limitations).
  - Imports are resolved by pointing every IAT slot at a small per-import
    stub (a single `RET` instruction) in a dedicated code region
    (`0x31000000+`). A `UC_HOOK_CODE` hook detects execution reaching one of
    these stub addresses, logs the call (DLL, name, first 4 integer args
    read from RCX/RDX/R8/R9), looks up a registered Python implementation,
    and sets RAX before letting the `RET` return control to the caller.
    Only `memset`, `memcpy`, `memmove`, `malloc`, and `free` have real
    implementations registered by default; every other import (e.g.
    `sin`, `cos`, `atan2f`, `omp_get_max_threads`, the whole MSVCP140/
    VCRUNTIME140 C++ runtime surface) logs a message and returns 0 in RAX.
  - `loader.bump_alloc(size)` is a simple bump allocator over a dedicated
    16 MiB heap region (`0x20000000+`); it never frees (`free` is a no-op).
  - `loader.call_function(addr, int_args=[...], float_args={...})` invokes
    an arbitrary function address using the Windows x64 calling convention:
    first 4 integer/pointer args in RCX/RDX/R8/R9, remaining integer args on
    the stack (with the required 32-byte shadow space), 16-byte stack
    alignment at the call, and a synthetic return address
    (`RETURN_TRAMPOLINE = 0x30000000`, a single mapped `RET`) so
    `emu_stop()` cleanly ends emulation when the target function returns.
    `float_args` is keyed by *overall argument position* (0-based) and only
    covers the first 4 positions, since the Windows x64 ABI puts float/double
    args in XMM0-XMM3 only when they occupy argument *positions* 0-3;
    positions 4+ (float or not) go on the stack. **`call_function` does not
    currently pack float args at position 4+ into the correct stack slot
    format automatically** -- callers needing that (as
    `test_m1_smoke.py`'s Check 2 does, for `FUN_180001000`'s 5th/6th
    arguments) must place the raw float bit-pattern into the appropriate
    `int_args` slot themselves. This was deliberate for M1: it keeps the ABI
    logic simple and explicit at the call site rather than hiding a subtle
    packing rule inside the harness.

- `test_m1_smoke.py` -- the M1 validation script. Two checks, both against
  `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`:
  1. **`FUN_180001a90`** (`0x180001a90`): a pure leaf function with no
     imports and no branches -- it writes three fixed 32-bit constants
     (`0x3e4ccccd`, `0x3b64c388`, `0x438f3d4c`, i.e. `0.2f`, `~0.00349f`,
     `~286.48f`) into the buffer passed in RCX and returns that pointer in
     RAX. Ground truth is read directly from
     `disasm/OLMRadialBlur.aex.asm.txt` (`MOV dword ptr [RCX], 0x3e4ccccd`
     etc. at `0x180001a90`-`0x180001a99`). This validates: PE mapping, basic
     code execution, memory read/write between Python and the emulated
     image, and the calling-convention plumbing for a pointer argument.
  2. **`FUN_180001000`** (`0x180001000`): the bilinear-interpolation
     resampler documented in `decomp/OLMRadialBlur.aex.c.txt` lines 1-73.
     Called against a synthetic 4x4 RGBA float "plane" with known per-pixel
     values, and cross-checked against an independent pure-Python
     re-implementation of the same decomp logic. This validates: multi-arg
     calling convention including *stack*-passed float arguments (see
     below), floating-point instruction execution (`MULSS`/`ADDSS`/`DIVSS`/
     `CVTTSS2SI`/etc.), and multi-hundred-instruction control flow.

  Run it with:
  ```bash
  tools/emulation/.venv/bin/python tools/emulation/test_m1_smoke.py
  ```
  It prints a live log and writes `M1_REPORT.md` in this directory.
  Current status: **both checks PASS**.

- `M1_REPORT.md` -- generated by the test script; contains the concrete
  expected/actual values, instruction counts, and two debugging notes worth
  reading before starting M2:
  - The Windows x64 ABI puts the 5th/6th positional arguments of
    `FUN_180001000` (its `x`/`y` floats) on the **stack**, not in XMM0/XMM1
    (verified from the callee's own prologue, which loads them via
    `MOVSS XMM6/XMM7, dword ptr [RSP+0x58]/[RSP+0x50]`).
  - `param_4` in `FUN_180001000` (and likely other resampler-style
    functions in this codebase) is the row stride measured in **floats**
    (`width_in_pixels * 4` for an RGBA plane), not in pixels. This was not
    obvious from the decomp variable naming and was only confirmed by
    tracing the raw pointer arithmetic in the disassembly
    (`iVar3*4 + iy*param_4` must be unit-consistent) and cross-checking
    against a hand-computed expected bilinear result. A first pass at this
    test used pixel-stride and produced a channel-swapped, row-misaligned
    result -- a concrete example of why disasm cross-checks matter even when
    a decomp "looks" readable.

## Milestone 2 status (DONE)

M2 is implemented and passing. New files:

- `test_m2_subfuncs.py` -> `M2_SUBFUNCS_REPORT.md`: verifies the two
  sub-functions `FUN_180004640` depends on, using the same
  small-input/independent-Python-reference strategy as M1.
  - `FUN_18000b680` (Gaussian kernel builder): scalar `expf` path (taken
    because `DAT_18002b180 == 1`), `out[i] = expf(-(i*i)/(2*(n*n)/9 + 1e-5))`.
    Matches the Python reference **exactly** (max abs diff 0.0) and exercises
    the newly-wired `expf` import.
  - `FUN_180001bb0` (corner-distance radii): 4 cases, all exact.

- `test_m2_rotation.py` -> `M2_ROTATION_REPORT.md` + `PARAM2_LAYOUT.md`:
  drives the final target `FUN_180004640` to completion under emulation.
  **It runs all the way to RET** (~914k instructions, ~1.5s) on a 16x16
  synthetic input, exercising every needed import (`cos`, `sin`, `atan2f`,
  `expf`, `omp_get_max_threads`) and a fully-mocked AE host suite.

New `aex_loader.py` capabilities added for M2 (all additive; M1 behavior
unchanged):

- `register_libm_impls(max_threads=1)` -- registers real Python-backed
  implementations of `cos`/`sin` (double in/out via XMM0), `expf`/`log2f`
  (float in/out via XMM0), `atan2f` (float y=XMM0, x=XMM1), and
  `omp_get_max_threads` (returns `max_threads`). Only `omp_get_max_threads`
  is imported from VCOMP140 in this binary -- there are **no OpenMP
  fork/parallel-region imports**, so forcing `max_threads=1` is sufficient
  to keep the plugin on its single-threaded path; no `__kmpc`/`vcomp_fork`
  body-invocation shim was needed.
- `install_callback(label, handler)` -- generalizes the M1 import-stub
  mechanism to arbitrary emulated function pointers, used to mock the AE
  `SPBasicSuite` (AcquireSuite/ReleaseSuite) and `PF_HandleSuite1`
  (new/lock/unlock/dispose handle). Handlers get `(loader, args)` and may
  read/write XMM registers for float returns.
- `read_xmm_f32/f64`, `write_xmm_f32/f64` -- XMM access helpers.
- `add_read_trace_range(lo, hi, label)` -- installs a `MEM_READ` hook that
  records every read into a range, used to enumerate the `param_2`
  context-struct offsets dynamically (see `PARAM2_LAYOUT.md`).
- `host_alloc(size)` -- a second bump allocator, in a separate 4 MiB host
  region (`0x40000000+`), for emulated host structs/handles.

### What "completion" required for `FUN_180004640`

`FUN_180004640` is NOT a self-contained numeric kernel. To reach RET the
harness had to supply:

1. A mocked `SPBasicSuite` at `*(*param_2 + 0x180)` plus a `PF_HandleSuite1`,
   because the function allocates + locks several handles and stores the
   locked data pointers into `param_1[0xf250]`, `[0xf252]`, `[0xe]`,
   `[0x10]`, `[0x12]`, `[0x14]`.
2. A `param_2` context struct with ~19 fields set to small, self-consistent
   values (full layout table in `PARAM2_LAYOUT.md`).
3. `param_1[0]` set to a value (90.0) that keeps the derived loop counts
   small (`iVar29 = (int)(360.0 / param_1[0]) = 4`).
4. Valid, mapped input pixel worlds for `param_2[0x12]/[0x13]` (and
   `[0x11]` when the +0x44 alpha flag is set).

### Witnessed f250/f252/+0xe writes

All three witness sub-regions are written with non-zero handle-data pointers,
and their *contents* (via the `witness_cells()` helper) are meaningful:
`f250` is the sampled RGBA polar plane (4 floats/cell), `f252` the weight
plane (1 float/cell), `+0xe` the normalized output (4 floats/cell). With a
gradient input world the per-cell values vary correctly (R rises as the
sampler walks the gradient, output is f250 normalized by weight) --
demonstrating the whole sample -> accumulate -> normalize pipeline ran, not
just the allocation scaffolding. See `M2_ROTATION_REPORT.md` for the dump.

### M2 caveats / honesty notes

- The synthetic input is *plausible* but not a real After Effects render
  request; several `param_2` scalar fields were set to sane placeholders
  rather than reverse-engineered semantic values. The layout table marks
  which offsets were confirmed *read* by the dynamic trace (`0x88` was not,
  because the +0x44 alpha-sampling branch was disabled in this run).
- The AE Handle Suite mock leaks (dispose is a no-op) -- fine for a single
  bounded run, not for a long-lived session.
- Because completion depends on those placeholder inputs, this validates the
  *machinery* (control flow, imports, suite interaction, buffer layout), not
  yet byte-exact rotation output against a real capture -- that is M3.

## Milestone 3 status (case_0010 witness geometry, PARTIAL)

`test_m3_case0010.py` -> `M3_REPORT.md` + `CASE0010_PARAM_MAPPING.md`.

Established (all independently checkable, no fabrication):

- case_0010 = Rotation (Blur Type 2), Center (960,540), Angle 0, Quality 5,
  1920x1080 8bpc, GPU Rendering=1.
- Output witness pixel **(1614,6) = [255,255,255,255]** (Windows) though its
  input pixel is black; it maps to polar cell **radial_row=844,
  angular_col~=1604** for **iVar29=1800**, exactly the Windows-traced cell
  family (`row844` / `col1601-1603`). iVar29=1800 => `param_1[0]~=0.2`
  (FUN_180001ac0 default branch). This validates the emulator's polar
  geometry against the real trace *analytically*.
- The radius-844 source circle carries **17 bright samples** (matches
  lane_state "reference bright count in local window: 17"), nearest ~6-8deg
  clockwise of the witness angle -> the bright family EXISTS upstream; the
  divergence is a gather/promotion problem (lane decision-ladder scenario
  #2), not population absence.

Not done (honest blocker): the bit-exact typed-cell compare
(`row844 col1603 = bc70f44b` ...) needs `param_2` built from case_0010's real
parameters. `param_2` is filled by `FUN_180008690` (AE param reader);
reader-index -> struct-offset map is in `CASE0010_PARAM_MAPPING.md`. Remaining
bounded work: mock the ~20 param-reader suite calls with manifest values, run
`FUN_180008690 -> FUN_180007520 -> FUN_180004640` on the real input. Compute
is tractable (~0.75-1.0B instructions, minutes in `fast=True` mode);
provenance is the gate.

## Known limitations / what's needed for M2 (`FUN_180004640`) [historical -- now addressed above]

`FUN_180004640` (`@ 0x180004640`, the Rotation entry point / final target)
is **not attempted yet**. Reading its decomp
(`decomp/OLMRadialBlur.aex.c.txt` starting at line 1929) surfaces several
concrete blockers beyond what M1's scope covers:

1. **`param_2` (second argument) is an opaque context struct accessed only
   by byte offset** (`*(float *)((longlong)param_2 + 0x7c)`,
   `*(int*)(param_2[1] + 0x24)`, `param_2[5]`, `param_2[0xb]`, etc, up to at
   least offset `0x7c`, plus a further indirection through
   `param_2[1] + 0x24/0x28`). Its layout is not declared anywhere in the
   decomp/disasm as a named struct -- it looks like an After Effects
   `PF_InData`/effect-parameters-adjacent structure, but the exact field
   meanings (units, whether some are doubles vs ints vs pointers) need to be
   worked out field-by-field, most reliably by cross-referencing the AE SDK
   headers (symlinked at `../../Headers` from the repo root) against how
   each offset is used (cast to float, cast to int, compared, etc).

2. **`param_1` (first argument, the working buffer) is written at very
   large indices** -- offsets up to at least `param_1[0xee64]` and
   `param_1[0xf254]` were observed, meaning the caller must allocate a
   buffer of at least ~61,000 floats (~244 KB) before calling this function,
   not a small fixed-size struct. The exact required size and what each
   region is used for (this looks like it holds multiple lookup
   tables/threaded-work buffers, given the `FUN_18000b680(ptr, size)` calls
   writing into several distinct sub-regions of `param_1`) needs mapping
   out before a caller can safely allocate it.

3. **Real import implementations are required, not just stubs**, because
   `FUN_180004640` itself calls `omp_get_max_threads`, `cos`, `sin`, and
   (transitively, via `FUN_180001bb0` and others) likely `atan2f` -- and
   these values flow directly into the rotation math. M1's default "log and
   return 0" stub is *not* safe for M2: returning 0 for `cos`/`sin` would
   silently corrupt the whole computation rather than fail loudly. M2 needs
   `aex_loader.py`'s `register_import_impl()` used to wire these to Python's
   real `math.cos`/`math.sin`/`math.atan2`/`os.cpu_count()`-style
   equivalents (already stubbed as an extension point in `_register_default_impls`,
   just not populated for libm yet).

4. `FUN_180004640` also calls `FUN_18000b680` and `FUN_180001bb0` as
   sub-functions -- these were not analyzed in M1 and would need their own
   decomp/disasm review to confirm they don't have additional undocumented
   requirements (more imports, more struct assumptions).

## Recommended approach for M2

1. Do not try to call `FUN_180004640` directly first. Instead:
   - Register real Python implementations for `cos`, `sin`, `atan2f`,
     `log2f`, `expf`, `omp_get_max_threads` (return a small constant like 1
     or 4) via `register_import_impl()`.
   - Validate `FUN_180001bb0` and `FUN_18000b680` individually first (same
     leaf-then-compose strategy as M1), since `FUN_180004640` depends on
     both and their decomp is already available.
2. Reverse-engineer `param_2`'s struct layout empirically: build a plausible
   `PF_InData`-shaped buffer (cross-referencing the AE SDK headers under
   `Headers/`), fill known fields with sentinel values, run just far enough
   into `FUN_180004640` (Unicorn supports single-stepping / instruction-count
   limits, already used by `call_function`'s `max_instructions` arg) to see
   which offsets get read, and iterate.
3. Size `param_1` generously (round up well past `0xf254` floats) and
   initially fill it with a recognizable sentinel pattern (not zero) so any
   read-before-write bugs in the port attempt are obvious in a typed dump.
4. Once `FUN_180004640` runs without faulting, add a small typed-dump helper
   (reading `param_1[0xf250]`, `param_1[0xf252]`, etc. as floats, per the
   task's stated target offsets) rather than trying to dump the whole
   buffer -- most of it is scratch space this function will still be
   writing to when execution reaches those offsets in the disassembly.

## Constraints honored in this milestone

- No existing source, conformance ledger, or notes files were modified.
- All new files are under `tools/emulation/` only.
- No git commits were made as part of this work.

---

## PERFORMANCE — why we still sometimes go to Windows, and how to push emulation further

Measured throughput: ~6–7M instructions/sec (RadialBlur `FUN_180004640` ~914M
insns in ~140s, `fast=True`). Unicorn is QEMU-TCG based; the ceiling here is
dominated by hook/callback overhead, not raw CPU.

The "still going to Windows" cases split into three buckets — only one is a real
emulation-performance problem:

**Bucket A — fundamentally needs Windows (NOT fixable by faster emulation):**
- GPU-path references (Metal/CUDA shaders don't exist in the CPU `.aex`). See
  GOTCHAS #7 / reference-path-split.
- True AE-host behavior: what the host actually feeds the plugin (real working
  color space, actual UI→param marshalling if we don't drive the reader). We
  already reduce this by driving the real param reader with mocked suites.

**Bucket B — emulatable but SLOW (this is where perf matters):**
- Full-frame OpenCV: distanceTransform, boxFilter, GaussianBlur, threshold. These
  are ~1e9 instructions.
- **Fix: detour the library entry point.** Same mechanism as `register_libm_impls`
  (which services cos/sin/expf natively). Use `loader.detour_function(addr, ...)`
  at the OpenCV dispatcher (e.g. distanceTransform `FUN_1812b15a0`, threshold
  `FUN_1812b6a40`) and service it with numpy/scipy/opencv-python. This collapses a
  billion-instruction op into one native call. Requirement: the native impl must
  bit-match (for exact-EDT/threshold it's testable). This is the single biggest
  lever and is not yet built — it's the recommended next infra investment.

**Bucket C — emulatable but we CHOSE not to (scope, not perf):**
- "Going to Windows for the input" (DirectionalBlur rowdriver inputs, Smoother2
  class-plane bytes). We drove the leaf/kernel but not the upstream stage that
  produces its input. Driving from a higher entry point makes the emulator
  produce those inputs itself — no Windows needed. It's just heavier setup.

**Other levers (smaller):**
- Keep witness runs in `fast=True` (hooks limited to trampoline/stub ranges);
  only enable per-instruction hooks for the narrow window under debug.
- Drive the smallest function that answers the question (leaf-first), not the
  full render — the biggest instruction-count savings come from scope, not speed.
- On an actual Windows box, `LoadLibrary` + direct call of the real `.aex`
  function runs at native speed and is cheaper than a debugger round-trip for
  heavy buffers — a scripted "call + dump" is an option when a Windows machine is
  already in the loop, though it defeats the "avoid Windows entirely" goal.

Bottom line: the frequent Windows trips are mostly Bucket A (genuinely required)
and Bucket C (a scope choice). Bucket B is real but addressable by the OpenCV
detour layer above — building that is the highest-value emulation-perf work left.
