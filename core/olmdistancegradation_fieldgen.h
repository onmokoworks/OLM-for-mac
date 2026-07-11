#pragma once

#include <cstddef>
#include <cstdint>

namespace olm::distancegradation {

struct FieldgenParams {
    std::int32_t threshold;
    std::int32_t param8;
};

struct Pixel16AGRB {
    std::uint16_t alpha;
    std::uint16_t green;
    std::uint16_t red;
    std::uint16_t blue;
};

struct Compose16Params {
    bool invert;
    std::int32_t in_out;
    std::int32_t render_mode;
    bool use_background;
    std::int32_t interpolation_mode;
    float power;
    float grad_red;
    float grad_green;
    float grad_blue;
    float background_red;
    float background_green;
    float background_blue;
};

// Host-neutral distanceTransform -> threshold -> normalize stage.
bool distance_to_normalized_u8(
    const std::uint8_t* mask,
    std::size_t width,
    std::size_t height,
    std::size_t input_rowbytes,
    float* output,
    std::size_t output_rowbytes,
    float threshold,
    bool constant_interpolation);

// Portable subset of DistanceGradation.aex FUN_181174760 used by the first
// function-level fixture. Input is one uint8 mask plane; output is float32.
bool fieldgen_u8(
    const std::uint8_t* mask,
    std::size_t width,
    std::size_t height,
    std::size_t input_rowbytes,
    float* output,
    std::size_t output_rowbytes,
    const FieldgenParams& params);

// OpenCV 4.5.5 cvConvertScale uses round-to-nearest-even when a normalized
// float field is stored in a PF16-style uint16 world. These helpers model the
// resulting word and the value read back by the 16bpc compose callback.
std::uint16_t pack_normalized_pf16_even(float value);
float roundtrip_normalized_pf16_even(float value);

// Portable subset of the 16bpc FUN_181170480 compose callback. The initial
// fixture deliberately covers BOTH + RGB + background + linear only.
bool compose_16(
    const Pixel16AGRB& source,
    std::uint16_t field_word,
    const Compose16Params& params,
    Pixel16AGRB* output);

}  // namespace olm::distancegradation
