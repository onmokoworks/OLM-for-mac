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
