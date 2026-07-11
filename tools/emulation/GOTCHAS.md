# Emulation GOTCHAS — hard-won facts for driving AE .aex under Unicorn

Every item below cost real debugging time on OLM. Read this before starting a
new plugin so you don't rediscover them. `aex_witness.py` encodes #2/#3/#4.

## 1. `__chkstk` needs a TEB + GS base (large-frame functions crash without it)
Functions with big stack frames call `__chkstk`, which reads `GS:[0x10]`
(StackLimit) and `GS:[0x8]` (StackBase) to probe the guard page. If GS base and
a TEB aren't set up, you get `UC_ERR_READ_UNMAPPED` at the `MOV R11, GS:[0x10]`.
Leaf/small functions never hit this, so it only appears once you drive a real
worker. **AexLoader already maps a TEB and sets GS base via
`uc.msr_write(0xC0000101, TEB_BASE)` — no action needed**, but if you fork the
loader or see a fault reading `GS:[...]`, this is why.

## 2. AE `PF_Pixel` is ARGB (alpha-first) in memory, NOT RGBA
The input pixel world is `{alpha, red, green, blue}`. PIL's `tobytes()` is RGBA,
so feeding it raw makes the source unpack read alpha into blue and blue into
alpha. Signature of the bug: your polar/working cells come out `[x, x, y, y]`
while Windows shows `[z, z, z, 1.0]`. Fix: reorder to A,R,G,B before building the
world — `aex_witness.rgba_to_argb_bytes()`.
Note the *internal* working plane the plugin produces is usually RGBA (alpha
LAST) — the plugin reorders on unpack. So input world = ARGB, working plane =
RGBA. Read working cells with `read_plane_cell_f32` (alpha at index 3).

## 3. AE 16-bit promotion is `trunc(v/32768*65535)`, not `v*2`
AE's internal `PF_MAX_CHAN16 == 32768` (1.0 == 0x8000), but the final full-range
16-bit value is 0..65535. Promotion is `trunc(half/32768*65535)`. Naive `*2`
gives off-by-one on non-endpoints (0x0e0e -> 7196 wrong vs 7195 right; endpoints
like 0x8000 happen to look fine at 65534/65535 boundary). Use
`aex_witness.promote_ae16()`. This promotion happens host-side, outside the
compose callback, so you won't see it in the callback's own disasm.

## 4. 5th+ argument is on the stack (Win x64), and it's the #1 ABI mistake
Win x64 passes args in RCX/RDX/R8/R9 then the stack (after 32B shadow space).
`call_function(addr, int_args=[...])` handles this, but a mis-placed 5th arg
(e.g. an output-pixel pointer) fails silently — you get plausible-looking wrong
numbers, not a crash. **Always run one import-free leaf with a known answer
first** (`aex_witness.leaf_check`) to prove the stack placement before trusting a
real witness. Float args go in XMM0-3 via `float_args={idx: value}`; a float at
arg position N leaves the GP register at N unused (not packed).

## 5. Reconstruct structs by driving the real builder, not by hand
Don't hand-fill a context/param struct from guesses. Either (a) sentinel-fill and
run with an instruction cap to observe which offsets the callee reads, then map
them, or (b) better, drive the real builder function (e.g. the AE param reader)
with mocked suite callbacks so the *binary* constructs the struct — this removes
fabrication risk. The `world` header offsets in `aex_witness` (+0x18 data,
+0x20 rowbytes, +0x24 w, +0x28 h, +0x2c bpc) matched OLM 2025 builds; verify per
new plugin.

## 6. Heavy OpenCV ops are CPU (emulatable) but slow — detour them
distanceTransform / boxFilter / threshold / GaussianBlur are OpenCV CPU code, so
Unicorn *can* run them, but a full-frame op is ~1e9 instructions (~2-3 min at the
interpreter's ~6-7M insn/s). If you only need the result, detour the OpenCV entry
point (`loader.detour_function(addr, ...)`) to a native numpy/scipy/opencv-python
implementation — same trick as `register_libm_impls` does for cos/sin/expf. This
is the main performance lever; see PERF section in README.

## 7. Emulation gives CPU-`.aex` truth — it cannot tell you the GPU path
If a reference PNG was rendered with AE GPU acceleration, its pixels come from a
Metal/CUDA shader that does not exist in the CPU `.aex`. No amount of CPU
emulation reproduces it (this is the "reference-path-split" verdict on RadialBlur
tiny Rotation and DistanceGradation case_0023). When emulation faithfully
reproduces the Windows *CPU* value but the packaged PNG differs, suspect a
GPU/stale reference and request a SOFTWARE (GPU=0) recapture — that's a genuine
Windows trip emulation can't replace.

## Fact vs inference discipline
Mark every claim FACT (read from disasm/decomp/a real dump) or INFERENCE. Never
"correct" a number to make it look right — a mismatch is data. If a value can't
be confirmed, say "unconfirmed", don't fabricate.
