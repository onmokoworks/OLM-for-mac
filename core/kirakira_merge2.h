#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <vector>

namespace olm::kirakira {

struct Merge2Color {
    float red;
    float green;
    float blue;
};

struct Merge2RampStop {
    float position;
    float alpha;
    float red;
    float green;
    float blue;
};

struct Merge2RampView {
    const Merge2RampStop* stops = nullptr;
    std::size_t count = 0;
};

inline float clamp_merge2_channel(float value)
{
    if (value >= 1.0f) return 1.0f;
    if (value <= 0.0f) return 0.0f;
    return value;
}

inline unsigned int truncate_merge2_channel(float value, float scale)
{
    const volatile float scaled = clamp_merge2_channel(value) * scale;
    return static_cast<unsigned int>(scaled);
}

template <typename Pixel>
inline Pixel compose_merge2_pixel(
    const Pixel& glow, const Pixel& source, float glow_opacity, float source_opacity)
{
    const volatile float raw_alpha_sum = glow.a + source.a;
    if (raw_alpha_sum == 0.0f)
        return {};
    const volatile float glow_alpha_product = glow.a * glow_opacity;
    const volatile float source_alpha_product = source_opacity * source.a;
    const float glow_alpha = clamp_merge2_channel(glow_alpha_product);
    const float source_alpha = clamp_merge2_channel(source_alpha_product);
    const volatile float alpha_sum = source_alpha + glow_alpha;
    const volatile float source_r = source_alpha * source.r;
    const volatile float source_g = source_alpha * source.g;
    const volatile float source_b = source_alpha * source.b;
    const volatile float glow_r = glow_alpha * glow.r;
    const volatile float glow_g = glow_alpha * glow.g;
    const volatile float glow_b = glow_alpha * glow.b;
    const volatile float red = source_r + glow_r;
    const volatile float green = source_g + glow_g;
    const volatile float blue = source_b + glow_b;
    return {
        clamp_merge2_channel(red), clamp_merge2_channel(green),
        clamp_merge2_channel(blue), clamp_merge2_channel(alpha_sum)
    };
}

inline bool parse_merge2_ramp_payload(
    const void* bytes,
    std::size_t size,
    std::vector<Merge2RampStop>& stops)
{
    stops.clear();
    if (!bytes || size < sizeof(std::uint32_t))
        return false;
    const unsigned char* raw = static_cast<const unsigned char*>(bytes);
    std::uint32_t count = 0;
    std::memcpy(&count, raw, sizeof(count));
    constexpr std::size_t record_size = sizeof(float) * 5;
    if (count > 16 || sizeof(count) + static_cast<std::size_t>(count) * record_size > size)
        return false;
    stops.resize(count);
    for (std::uint32_t i = 0; i < count; ++i) {
        float fields[5];
        std::memcpy(fields, raw + sizeof(count) + static_cast<std::size_t>(i) * record_size,
                    record_size);
        stops[i] = {fields[0], fields[1], fields[2], fields[3], fields[4]};
    }
    return true;
}

inline bool parse_merge2_ramp_flat(
    const void* bytes, std::size_t size,
    Merge2RampStop* stops, std::size_t capacity, std::size_t* count_out)
{
    if (!bytes || !stops || !count_out || size < 5)
        return false;
    const unsigned char* raw = static_cast<const unsigned char*>(bytes);
    std::uint32_t count = 0;
    std::memcpy(&count, raw + 1, sizeof(count));
    const std::size_t active_size = static_cast<std::size_t>(count) * sizeof(Merge2RampStop);
    if (count > capacity || 5 + active_size > size)
        return false;
    std::memcpy(stops, raw + 5, active_size);
    *count_out = count;
    return true;
}

inline bool equal_merge2_ramps(
    const Merge2RampStop* left, std::size_t left_count,
    const Merge2RampStop* right, std::size_t right_count)
{
    if (!left || !right || left_count != right_count)
        return false;
    for (std::size_t i = 0; i < left_count; ++i) {
        const float* a = reinterpret_cast<const float*>(&left[i]);
        const float* b = reinterpret_cast<const float*>(&right[i]);
        for (std::size_t field = 0; field < 5; ++field) {
            if (a[field] != b[field])
                return false;
        }
    }
    return true;
}

inline std::size_t interpolate_merge2_ramps(
    Merge2RampStop* output,
    const Merge2RampStop* left, std::size_t left_count,
    const Merge2RampStop* right, std::size_t right_count,
    float t)
{
    if (!output || !left || !right || left_count == 0 || right_count == 0)
        return 0;
    const std::size_t count = left_count > right_count ? left_count : right_count;
    for (std::size_t i = 0; i < count; ++i) {
        const Merge2RampStop& a = left[i < left_count ? i : left_count - 1];
        const Merge2RampStop& b = right[i < right_count ? i : right_count - 1];
        const float* av = reinterpret_cast<const float*>(&a);
        const float* bv = reinterpret_cast<const float*>(&b);
        float* dst = reinterpret_cast<float*>(&output[i]);
        for (std::size_t field = 0; field < 5; ++field) {
            const volatile float delta = (bv[field] - av[field]) * t;
            dst[field] = av[field] + delta;
        }
    }
    return count;
}

inline Merge2Color sample_merge2_ramp(const Merge2RampView& ramp, float amount)
{
    if (!ramp.stops || ramp.count == 0)
        return {1.0f, 0.0f, 0.0f};

    const Merge2RampStop* lower = nullptr;
    const Merge2RampStop* upper = nullptr;
    for (std::size_t i = 0; i < ramp.count; ++i) {
        const Merge2RampStop& stop = ramp.stops[i];
        if (stop.position <= amount) {
            if (!lower || (lower->position <= stop.position && stop.position != lower->position))
                lower = &stop;
        } else if (!upper || stop.position < upper->position) {
            upper = &stop;
        }
    }
    if (!lower)
        return {upper->red, upper->green, upper->blue};
    if (!upper)
        return {lower->red, lower->green, lower->blue};

    const float t = (amount - lower->position) / (upper->position - lower->position);
    const volatile float red_delta = (upper->red - lower->red) * t;
    const volatile float green_delta = (upper->green - lower->green) * t;
    const volatile float blue_delta = (upper->blue - lower->blue) * t;
    return {
        lower->red + red_delta,
        lower->green + green_delta,
        lower->blue + blue_delta,
    };
}

inline std::size_t nearest_merge2_ramp_stop(const Merge2RampStop* stops, std::size_t count, float position)
{
    if (!stops || count == 0)
        return 0;
    std::size_t selected = 0;
    float best = stops[0].position > position ? stops[0].position - position : position - stops[0].position;
    for (std::size_t i = 1; i < count; ++i) {
        const float distance = stops[i].position > position ? stops[i].position - position : position - stops[i].position;
        if (distance < best) {
            best = distance;
            selected = i;
        }
    }
    return selected;
}

inline std::size_t hit_merge2_ramp_stop(
    const Merge2RampStop* stops, std::size_t count, float position, float tolerance)
{
    if (!stops)
        return count;
    for (std::size_t i = count; i > 0; --i) {
        const float distance = stops[i - 1].position > position
            ? stops[i - 1].position - position : position - stops[i - 1].position;
        if (distance <= tolerance)
            return i - 1;
    }
    return count;
}

inline bool set_merge2_ramp_stop_color(
    Merge2RampStop* stops, std::size_t count, std::size_t selected,
    float alpha, float red, float green, float blue)
{
    if (!stops || selected >= count)
        return false;
    stops[selected].alpha = alpha;
    stops[selected].red = red;
    stops[selected].green = green;
    stops[selected].blue = blue;
    return true;
}

inline bool apply_merge2_ramp_color_picker_result(
    Merge2RampStop* stops, std::size_t count, std::size_t* selected,
    int result, int cancel_result, float alpha, float red, float green, float blue)
{
    if (!selected || *selected >= count)
        return false;
    if (result == cancel_result) {
        *selected = count;
        return false;
    }
    if (result != 0)
        return false;
    return set_merge2_ramp_stop_color(
        stops, count, *selected, alpha, red, green, blue);
}

inline void drag_merge2_ramp_stop(Merge2RampStop* stops, std::size_t count, std::size_t selected, float position)
{
    if (!stops || selected >= count)
        return;
    const float lower = selected > 0 ? stops[selected - 1].position : 0.0f;
    const float upper = selected + 1 < count ? stops[selected + 1].position : 1.0f;
    if (position < lower) position = lower;
    if (position > upper) position = upper;
    stops[selected].position = position;
}

inline std::size_t erase_merge2_ramp_stop(Merge2RampStop* stops, std::size_t count, std::size_t selected)
{
    if (!stops || selected >= count)
        return count;
    for (std::size_t i = selected + 1; i < count; ++i)
        stops[i - 1] = stops[i];
    return count - 1;
}

inline std::size_t insert_merge2_ramp_stop(Merge2RampStop* stops, std::size_t count, float position)
{
    if (!stops || count >= 16)
        return count;
    if (position < 0.0f) position = 0.0f;
    if (position > 1.0f) position = 1.0f;
    const Merge2Color color = sample_merge2_ramp({stops, count}, position);
    std::size_t insertion = 0;
    while (insertion < count && stops[insertion].position <= position)
        ++insertion;
    for (std::size_t i = count; i > insertion; --i)
        stops[i] = stops[i - 1];
    stops[insertion] = {position, 1.0f, color.red, color.green, color.blue};
    return count + 1;
}

// The optional ramp is a bounded test seam until the Mac AE parameter surface
// can supply the Windows custom payload. Normal host rendering passes nullptr.
template <typename Pixel>
inline void add_colored_merge2(
    Pixel* glow,
    const float* amount,
    std::size_t pixels,
    const Merge2Color& fixed_color,
    const Merge2RampView* ramp = nullptr)
{
    if (!glow || !amount)
        return;
    for (std::size_t i = 0; i < pixels; ++i) {
        if (amount[i] <= 0.001f)
            continue;
        const Merge2Color color = ramp ? sample_merge2_ramp(*ramp, amount[i]) : fixed_color;
        glow[i].r += color.red;
        glow[i].g += color.green;
        glow[i].b += color.blue;
        glow[i].a += amount[i];
    }
}

}  // namespace olm::kirakira
