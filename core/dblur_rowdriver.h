#pragma once

// Float32 RGBA leaf ABI recovered from OLMDirectionalBlur.aex.
// The final float is deliberately part of each exported signature: on the
// Windows AEX ABI it is the stack argument after the integer/pointer slots.
extern "C" void olm_dblur_prepass_f32(int start, int offset,
                                       const float* source, float* destination,
                                       float* denominator, float* valid,
                                       const float* front_weights, int front_count,
                                       const float* back_weights, int back_count,
                                       int end, float coefficient);

extern "C" void olm_dblur_scatter_f32(int start, int offset, char backward,
                                       const float* source, float* destination,
                                       float* denominator, float* alpha_max,
                                       const float* weights, int count, int end,
                                       float coefficient);

// Explicit typed candidate for FUN_1800038d0. All buffers are flat float32
// arrays: RGBA pixels for source/destination/comp_map, scalar arrays for the
// accumulators. This is the detour-friendly form of the AEX params fields used
// by the default rowdriver path. Mode-specific auxiliary inputs are exposed by
// the field/noise entry points below.
extern "C" void olm_dblur_rowdriver_f32(int row_start, int row_end,
                                         const float* source, float* destination,
                                         int width, int mode, float opacity,
                                         float exponent, float scale,
                                         float edge_x, float edge_y,
                                         const float* scatter_front,
                                         const float* scatter_back,
                                         const float* prepass_front,
                                         const float* prepass_back,
                                         float* denominator, float* alpha_max,
                                         const float* comp_map,
                                         int scatter_front_count,
                                         int scatter_back_count,
                                         int prepass_front_count,
                                         int prepass_back_count);

// Mode-3 variant. The noise plane and interpolation flag correspond to
// params+0x80c0 and params+0x80bc in the AEX worker context.
extern "C" void olm_dblur_rowdriver_noise_f32(
    int row_start, int row_end, const float* source, float* destination,
    int width, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count, const float* noise_samples,
    int noise_stride, float noise_cell_size, int interpolate_noise);

// Mode-2 variant. `field` is the rotated one-float-per-pixel layer map stored
// at params+0x80b0 by the AEX host-sampling stage.
extern "C" void olm_dblur_rowdriver_field_f32(
    int row_start, int row_end, const float* source, float* destination,
    int width, float opacity, float exponent, float scale,
    float edge_x, float edge_y, const float* scatter_front,
    const float* scatter_back, const float* prepass_front,
    const float* prepass_back, float* denominator, float* alpha_max,
    const float* comp_map, int scatter_front_count, int scatter_back_count,
    int prepass_front_count, int prepass_back_count, const float* field);
