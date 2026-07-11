#pragma once

#include <cstddef>

// Exact candidate for OLMDirectionalBlur FUN_180001ec0.
//
// Pixels are four contiguous float32 values in R,G,B,A order.  The helper
// writes only for strict-interior source samples; callers own destination
// initialization for all skipped samples.
extern "C" void olm_dblur_rotate_rgba_f32(const float* source,
                                           float* destination,
                                           int width,
                                           int height,
                                           float angle);

// Diagnostic entry point for pinning the Windows CRT trig boundary. Pixel
// arithmetic is identical to olm_dblur_rotate_rgba_f32 after cosf/sinf return.
extern "C" void olm_dblur_rotate_rgba_f32_trig(const float* source,
                                                float* destination,
                                                int width,
                                                int height,
                                                float cosine,
                                                float sine);
