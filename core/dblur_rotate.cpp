#include "dblur_rotate.h"

#include <cmath>

namespace {

__attribute__((noinline)) float fmul(float a, float b) {
    volatile float result = a * b;
    return result;
}

__attribute__((noinline)) float fadd(float a, float b) {
    volatile float result = a + b;
    return result;
}

__attribute__((noinline)) float fsub(float a, float b) {
    volatile float result = a - b;
    return result;
}

__attribute__((noinline)) float fdiv(float a, float b) {
    volatile float result = a / b;
    return result;
}

}  // namespace

extern "C" void olm_dblur_rotate_scalar_f32_trig(const float* source,
                                                  float* destination,
                                                  int width,
                                                  int height,
                                                  float cosine,
                                                  float sine) {
    for (int y = 0; y < height; ++y) {
        const float centered_y = static_cast<float>(y - height / 2);
        float* dst = destination + static_cast<std::size_t>(y) * width;
        for (int x = 0; x < width; ++x, ++dst) {
            const float centered_x = static_cast<float>(x - width / 2);
            const float sample_y = fadd(
                fadd(fmul(centered_x, sine), fmul(centered_y, cosine)),
                static_cast<float>(height / 2));
            const float sample_x = fadd(
                fsub(fmul(centered_x, cosine), fmul(centered_y, sine)),
                static_cast<float>(width / 2));
            const int iy = static_cast<int>(sample_y);
            const int ix = static_cast<int>(sample_x);
            const float fy = fsub(sample_y, static_cast<float>(iy));
            const float fx = fsub(sample_x, static_cast<float>(ix));
            if (!(iy > 0 && iy < height - 1 && ix > 0 && ix < width - 1)) {
                continue;
            }

            const std::size_t top = static_cast<std::size_t>(iy) * width + ix;
            const std::size_t bottom = top + width;
            const float one_minus_y = fsub(1.0f, fy);
            const float one_minus_x = fsub(1.0f, fx);
            volatile float top_right = fmul(fmul(one_minus_y, fx), source[top + 1]);
            volatile float top_left = fmul(fmul(one_minus_x, one_minus_y), source[top]);
            volatile float bottom_left = fmul(fmul(one_minus_x, fy), source[bottom]);
            volatile float bottom_right = fmul(fmul(fy, fx), source[bottom + 1]);
            volatile float value = top_right;
            value = fadd(value, top_left);
            value = fadd(value, bottom_left);
            value = fadd(value, bottom_right);
            *dst = value;
        }
    }
}

extern "C" void olm_dblur_rotate_scalar_f32(const float* source,
                                             float* destination,
                                             int width,
                                             int height,
                                             float angle) {
    const float cosine = static_cast<float>(std::cos(static_cast<double>(angle)));
    const float sine = static_cast<float>(std::sin(static_cast<double>(angle)));
    olm_dblur_rotate_scalar_f32_trig(
        source, destination, width, height, cosine, sine);
}

extern "C" void olm_dblur_rotate_rgba_f32_trig(const float* source,
                                                float* destination,
                                                int width,
                                                int height,
                                                float cosine,
                                                float sine) {
    const int row_stride = width * 4;

    for (int y = 0; y < height; ++y) {
        const float centered_y = static_cast<float>(y - height / 2);
        float* dst = destination + static_cast<std::size_t>(y) * row_stride + 2;
        for (int x = 0; x < width; ++x, dst += 4) {
            const float centered_x = static_cast<float>(x - width / 2);
            const float sample_y = fadd(fadd(fmul(centered_x, sine), fmul(centered_y, cosine)),
                                        static_cast<float>(height / 2));
            const float sample_x = fadd(fsub(fmul(centered_x, cosine), fmul(centered_y, sine)),
                                        static_cast<float>(width / 2));

            // These are CVTTSS2SI conversions: truncation toward zero.
            const int iy = static_cast<int>(sample_y);
            const int ix = static_cast<int>(sample_x);
            const float fy = fsub(sample_y, static_cast<float>(iy));
            const float fx = fsub(sample_x, static_cast<float>(ix));
            if (!(iy > 0 && iy < height - 1 && ix > 0 && ix < width - 1)) {
                continue;
            }

            const std::size_t top = static_cast<std::size_t>(iy) * row_stride +
                                    static_cast<std::size_t>(ix) * 4;
            const std::size_t bottom = top + row_stride;
            const float one_minus_y = fsub(1.0f, fy);
            const float one_minus_x = fsub(1.0f, fx);

            volatile float alpha_top_left = fmul(fmul(one_minus_y, one_minus_x), source[top + 3]);
            volatile float alpha_top_right = fmul(fmul(one_minus_y, fx), source[top + 7]);
            volatile float alpha_bottom_right = fmul(fmul(fy, fx), source[bottom + 7]);
            volatile float alpha_bottom_left = fmul(fmul(one_minus_x, fy), source[bottom + 3]);
            volatile float alpha = alpha_top_right;
            alpha = fadd(alpha, alpha_top_left);
            alpha = fadd(alpha, alpha_bottom_left);
            alpha = fadd(alpha, alpha_bottom_right);

            volatile float w_top_left = alpha_top_left;
            volatile float w_bottom_left = alpha_bottom_left;
            volatile float w_top_right = alpha_top_right;
            volatile float w_bottom_right = alpha_bottom_right;
            if (alpha != 0.0f) {
                w_top_left = fdiv(w_top_left, alpha);
                w_bottom_left = fdiv(w_bottom_left, alpha);
                w_top_right = fdiv(w_top_right, alpha);
                w_bottom_right = fdiv(w_bottom_right, alpha);
            }

            volatile float red_tl = fmul(source[top], w_top_left);
            volatile float red_bl = fmul(source[bottom], w_bottom_left);
            volatile float red_tr = fmul(source[top + 4], w_top_right);
            volatile float red_br = fmul(source[bottom + 4], w_bottom_right);
            volatile float red = red_tl;
            red = fadd(red, red_tr);
            red = fadd(red, red_bl);
            red = fadd(red, red_br);
            volatile float green_tl = fmul(source[top + 1], w_top_left);
            volatile float green_bl = fmul(source[bottom + 1], w_bottom_left);
            volatile float green_tr = fmul(source[top + 5], w_top_right);
            volatile float green_br = fmul(source[bottom + 5], w_bottom_right);
            volatile float green = green_tl;
            green = fadd(green, green_tr);
            green = fadd(green, green_bl);
            green = fadd(green, green_br);
            volatile float blue_tl = fmul(source[top + 2], w_top_left);
            volatile float blue_bl = fmul(source[bottom + 2], w_bottom_left);
            volatile float blue_tr = fmul(source[top + 6], w_top_right);
            volatile float blue_br = fmul(source[bottom + 6], w_bottom_right);
            volatile float blue = blue_tl;
            blue = fadd(blue, blue_tr);
            blue = fadd(blue, blue_bl);
            blue = fadd(blue, blue_br);

            dst[-2] = red;
            dst[-1] = green;
            dst[0] = blue;
            dst[1] = alpha;
        }
    }
}

extern "C" void olm_dblur_rotate_rgba_f32(const float* source,
                                           float* destination,
                                           int width,
                                           int height,
                                           float angle) {
    // The checked-in Unicorn AEX fixture models the imported cosf/sinf with
    // the host libm's double call followed by the import's float return.
    const float cosine = static_cast<float>(std::cos(static_cast<double>(angle)));
    const float sine = static_cast<float>(std::sin(static_cast<double>(angle)));
    olm_dblur_rotate_rgba_f32_trig(source, destination, width, height, cosine, sine);
}
