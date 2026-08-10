#pragma once

#include <cstdint>

// Binary-grounded 8bpc DirectionalBlur path for the default front-only mode.
// Input and output are contiguous straight RGBA8 pixels. The output is the
// raw plug-in callback value; AE/output-module premultiplication is external.
extern "C" int olm_dblur_frontonly_rgba8(const std::uint8_t* input_rgba,
                                           std::uint8_t* output_rgba,
                                           int width,
                                           int height,
                                           float angle_degrees,
                                           float brightness_gain,
                                           int front_strength,
                                           int front_alpha_fade);

// PF16 minimal exact branch: packed little-endian A/R/G/B words in and out.
extern "C" int olm_dblur_minimal_argb16(const std::uint16_t* input_argb,
                                         std::uint16_t* output_argb,
                                         int width, int height,
                                         int front_strength,
                                         int back_strength,
                                         float brightness_gain,
                                         float angle_degrees,
                                         float noise_variation_percent,
                                         int noise_type,
                                         std::uint32_t seed,
                                         int noise_offset_ui,
                                         float thickness_ui);
extern "C" int olm_dblur_minimal_layer_argb16(
    const std::uint16_t* input_argb, std::uint16_t* output_argb,
    int width, int height, int front_strength, int back_strength,
    float brightness_gain, float angle_degrees, float noise_variation_percent,
    const std::uint16_t* layer_argb, int layer_rowbytes);
extern "C" int olm_dblur_full_argb16(
    const std::uint16_t* input_argb, std::uint16_t* output_argb,
    int width, int height, int front_strength, int front_alpha_fade,
    float front_sharp_tail_percent, int back_strength, int back_alpha_fade,
    float back_sharp_tail_percent, float size_variation_percent,
    float brightness_gain, float angle_degrees,
    float noise_variation_percent, int noise_type, std::uint32_t seed,
    int noise_offset_ui, float thickness_ui);
extern "C" int olm_dblur_minimal_argb32(const float* input_argb,
                                         float* output_argb,
                                         int width, int height,
                                         int front_strength,
                                         int back_strength,
                                         float size_variation_percent,
                                         float angle_degrees,
                                         float brightness_gain,
                                         float noise_variation_percent,
                                         int noise_type,
                                         std::uint32_t seed,
                                         int noise_offset_ui,
                                         float thickness_ui,
                                         const float* layer_argb,
                                         int layer_rowbytes);
extern "C" int olm_dblur_minimal_fade_argb32(
    const float* input_argb, float* output_argb, int width, int height,
    int front_strength, int back_strength, int front_alpha_fade,
    float size_variation_percent, float angle_degrees, float brightness_gain,
    float noise_variation_percent, int noise_type, std::uint32_t seed,
    int noise_offset_ui, float thickness_ui, const float* layer_argb,
    int layer_rowbytes);
extern "C" int olm_dblur_full_argb32(
    const float* input_argb, float* output_argb, int width, int height,
    int front_strength, int front_alpha_fade, float front_sharp_tail_percent,
    int back_strength, int back_alpha_fade, float back_sharp_tail_percent,
    float size_variation_percent, float angle_degrees, float brightness_gain,
    float noise_variation_percent, int noise_type, std::uint32_t seed,
    int noise_offset_ui, float thickness_ui, const float* layer_argb,
    int layer_rowbytes);

// Extended mode-1 front-only path. `render_scale` is the AE downsample scale
// already projected onto the blur direction; size/sharp values are UI
// percentages. The original entry point remains the zero-variation contract.
extern "C" int olm_dblur_frontonly_mode1_rgba8(
    const std::uint8_t* input_rgba,
    std::uint8_t* output_rgba,
    int width,
    int height,
    float angle_degrees,
    float brightness_gain,
    int front_strength,
    int front_alpha_fade,
    float size_variation_percent,
    float front_sharp_tail_percent,
    float render_scale);

// Complete no-noise mode-1 path, including independent front/back scatter,
// alpha-fade prepasses, and sharp-tail coefficients.
extern "C" int olm_dblur_mode1_rgba8(
    const std::uint8_t* input_rgba,
    std::uint8_t* output_rgba,
    int width,
    int height,
    float angle_degrees,
    float brightness_gain,
    int front_strength,
    int front_alpha_fade,
    float front_sharp_tail_percent,
    int back_strength,
    int back_alpha_fade,
    float back_sharp_tail_percent,
    float size_variation_percent,
    float render_scale);

// Smooth/Block generated-noise modes (UI Noise Type 1/2). Layer-driven mode 2
// is intentionally excluded because it requires an AE checked-out field.
extern "C" int olm_dblur_noise_mode3_rgba8(
    const std::uint8_t* input_rgba,
    std::uint8_t* output_rgba,
    int width,
    int height,
    float angle_degrees,
    float brightness_gain,
    int front_strength,
    int front_alpha_fade,
    float front_sharp_tail_percent,
    int back_strength,
    int back_alpha_fade,
    float back_sharp_tail_percent,
    float size_variation_percent,
    float noise_variation_percent,
    int noise_type,
    std::uint32_t seed,
    int noise_offset_ui,
    float thickness_ui,
    float render_scale);

// Layer-driven noise (UI Noise Type 3), including the exact 8-bpc ARGB
// premultiplied-luminance field and scalar rotation path.
extern "C" int olm_dblur_layer_mode2_rgba8(
    const std::uint8_t* input_rgba,
    std::uint8_t* output_rgba,
    int width,
    int height,
    float angle_degrees,
    float brightness_gain,
    int front_strength,
    int front_alpha_fade,
    float front_sharp_tail_percent,
    int back_strength,
    int back_alpha_fade,
    float back_sharp_tail_percent,
    float size_variation_percent,
    float noise_variation_percent,
    const std::uint8_t* layer_argb,
    int layer_width,
    int layer_height,
    int layer_rowbytes,
    int layer_origin_x,
    int layer_origin_y,
    int render_origin_x,
    int render_origin_y,
    float render_scale);
