#pragma once

#include <cstdint>

// Construct DirectionalBlur's unrotated mode-2 scalar field from a checked-out
// PF_Pixel8 (A/R/G/B) Layer. Destination is caller-zeroed and uses the enlarged
// work-plane geometry shared by the RGBA renderer.
extern "C" float olm_dblur_layer_field_argb8(
    const std::uint8_t* layer_argb,
    int layer_width,
    int layer_height,
    int layer_rowbytes,
    int layer_origin_x,
    int layer_origin_y,
    float* destination,
    int work_width,
    int work_height,
    int work_col0,
    int work_row0,
    int render_width,
    int render_height,
    int render_origin_x,
    int render_origin_y);

extern "C" float olm_dblur_layer_field_argb16(
    const std::uint16_t* layer_argb, int layer_width, int layer_height,
    int layer_rowbytes, int layer_origin_x, int layer_origin_y,
    float* destination, int work_width, int work_height, int work_col0,
    int work_row0, int render_width, int render_height, int render_origin_x,
    int render_origin_y);

extern "C" float olm_dblur_layer_field_argb32(
    const float* layer_argb, int layer_width, int layer_height, int layer_rowbytes,
    int layer_origin_x, int layer_origin_y, float* destination,
    int work_width, int work_height, int work_col0, int work_row0,
    int render_width, int render_height, int render_origin_x, int render_origin_y);
