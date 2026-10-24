- **P00c-DG-default-PF32** — confirmed Mac-only refusal group. Recover the
  original no-override In/Out=0/default PF32 owner behavior from the retained
  32×24 witness, then extend general admission with independent alpha/source
  and geometry tests. Do not insert a default-only zero-output shortcut.
- **P00c-DBlur-cropped-world** — probable Mac-only full-layer guard. Start
  with equal 960×540 checkout/output worlds under 1920×1080 layer metadata,
  plus a small original witness; reconstruct input-sized workspace/request
  handling before changing `DirectionalGenericWorldIsFullFrame` admission.
- **P00c-Sm2-checkout-contract** — qualify native/original cropped checkout
  negotiation. Preserve the original-backed equal-world guard; determine
  whether Mac's forced full-frame PreRender creates the unequal world pair.
  This is not a proposal to accept mismatched buffers blindly.
- **P00p-DBlur-rotation-softfloat** — profile `olm_dblur_rotate_rgba_f32_trig`
  and its `x86_float::{sse_result,generated_nan,bits}` calls. Optimize only with
  bit-exact independent finite/nonfinite and signed-zero regression evidence.
- **P00p-DBlur-scatter** — investigate `olm_dblur_scatter_f32` on `corpus09`,
  including the 4K timeouts and 1080p timings. Preserve scatter accumulation
  order and distinguish invariant work from arithmetic changes.
- **P00p-Radial-rotation** — investigate `RenderRotationTyped` using C45
  `C45_seed1_case000108.json` (matrix `corpus05`). The current observed boundary
  is 240×135 completing in 36.4–38.3 s versus 480×270 exceeding 60 s. Establish
  stage/work-count scaling before an exact optimization. The 1080p extent-hint/
  transparent-source variant completed near the limit at PF8/PF32 but timed out
  at PF16; separate metadata effects from alpha coverage and shared-load noise.
  Do not replace the
  timeout with a refusal budget or an approximate blur.
- **P00p-Blur-horizontal** — optimize the measured `olm::blur::horizontal`
  convolution hotspot (`corpus05`, three depths), preserving tap traversal,
  intermediate precision and output bits. Recheck both 1080p and 4K.
- **P00p-ColorKey-Lab-UCRT** — investigate `ucrt_powf` / `RGBToPluginLab76`
  and `ucrt_atan2f` in the heavy 4K Lab-distance path. Look for invariant work
  before changing arithmetic; replacing UCRT with a faster approximate math
  library is outside the bit-exact contract.
- **P00p-Smoother-scratch-memory** — investigate `_platform_memset` and
  `SubHandler8Memory::read32` in default/heavy PF16 and heavy PF8 profiles.
  Establish which clears and address translations are redundant without
  changing initialized-state or traversal semantics.
- **P00p-Smoother-edgewalk** — separately measure `EdgeWalker8`,
  `EdgeWalker16Exact` and the classifier paths after attributing scratch-memory
  cost. Preserve visit order, branching and typed arithmetic in any optimization.
- **P00c-corpus-diversity** — retain ten independent exact tuples for
  ColorKeep, ColorKey, KiraKira and Smoother2. This audit explicitly samples
  smaller corpora with replacement and does not invent independent witnesses.
