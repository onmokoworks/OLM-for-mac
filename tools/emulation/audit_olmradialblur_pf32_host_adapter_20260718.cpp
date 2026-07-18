#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace {

constexpr int kOutputWidth = 1920;
constexpr int kOutputHeight = 1080;
constexpr int kPolarWidth = 1104;
constexpr int kPolarHeight = 1800;
constexpr float kCenterX = 960.0f;
constexpr float kCenterY = 540.0f;
constexpr float kRatio = 1.0f;
constexpr float kCosAngle = 1.0f;
constexpr float kSinAngle = 0.0f;
constexpr float kAngleStep = 0.0034906584769487381f;
constexpr int kMinRadius = 0;
constexpr double kTwoPi = 6.283185307179586476925286766559;

float f32_add(float a, float b) { volatile float v = a + b; return v; }
float f32_sub(float a, float b) { volatile float v = a - b; return v; }
float f32_mul(float a, float b) { volatile float v = a * b; return v; }
float f32_div(float a, float b) { volatile float v = a / b; return v; }

std::vector<char> read_all(const char *path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::vector<char>(std::istreambuf_iterator<char>(stream), {});
}

void inverse_coordinate(int x, int y, float &radius_index, float &angle_index)
{
    const float dy = f32_sub(static_cast<float>(y), kCenterY);
    const float dx = f32_sub(static_cast<float>(x), kCenterX);
    const float ey = f32_div(f32_sub(f32_mul(kCosAngle, dy), f32_mul(kSinAngle, dx)), kRatio);
    const float ex = f32_add(f32_mul(kSinAngle, dy), f32_mul(kCosAngle, dx));
    const float radius = std::sqrt(f32_add(f32_mul(ey, ey), f32_mul(ex, ex)));
    float angle = static_cast<float>(std::atan2(static_cast<double>(ey), static_cast<double>(ex)));
    if (angle < 0.0f) angle = static_cast<float>(static_cast<double>(angle) + kTwoPi);
    angle_index = angle < 0.0f ? 0.0f : f32_div(angle, kAngleStep);
    if (angle_index >= static_cast<float>(kPolarHeight)) {
        angle_index = f32_sub(angle_index, static_cast<float>(kPolarHeight));
    }
    radius_index = f32_sub(radius, static_cast<float>(kMinRadius));
}

void sample(const float *plane, float radius, float angle, float out[4])
{
    const int angle0_raw = static_cast<int>(angle);
    const int radius0 = static_cast<int>(radius);
    int angle0 = angle0_raw;
    int angle1 = angle0_raw + 1;
    if (angle0_raw < 0) {
        angle0 = kPolarHeight - 1;
    } else if (angle0_raw == kPolarHeight - 1) {
        angle1 = 0;
    }

    const float fy = f32_sub(angle, static_cast<float>(angle0_raw));
    const float fx = f32_sub(radius, static_cast<float>(radius0));
    const float one_minus_fx = f32_sub(1.0f, fx);
    const float one_minus_fy = f32_sub(1.0f, fy);
    const float weights[4] = {
        f32_mul(one_minus_fx, one_minus_fy),
        f32_mul(one_minus_fy, fx),
        f32_mul(one_minus_fx, fy),
        f32_mul(fy, fx),
    };
    const float *cells[4] = {
        plane + (static_cast<std::size_t>(angle0) * kPolarWidth + radius0) * 4,
        plane + (static_cast<std::size_t>(angle0) * kPolarWidth + radius0 + 1) * 4,
        plane + (static_cast<std::size_t>(angle1) * kPolarWidth + radius0) * 4,
        plane + (static_cast<std::size_t>(angle1) * kPolarWidth + radius0 + 1) * 4,
    };

    out[0] = out[1] = out[2] = out[3] = 0.0f;
    for (int i = 0; i < 4; ++i) {
        const float alpha_weight = f32_mul(weights[i], cells[i][3]);
        out[3] = f32_add(out[3], alpha_weight);
        out[2] = f32_add(out[2], f32_mul(alpha_weight, cells[i][2]));
        out[1] = f32_add(out[1], f32_mul(alpha_weight, cells[i][1]));
        out[0] = f32_add(out[0], f32_mul(alpha_weight, cells[i][0]));
    }
    if (out[3] != 0.0f) {
        const float reciprocal_alpha = f32_div(1.0f, out[3]);
        out[0] = f32_mul(out[0], reciprocal_alpha);
        out[1] = f32_mul(out[1], reciprocal_alpha);
        out[2] = f32_mul(reciprocal_alpha, out[2]);
    }
}

} // namespace

int main(int argc, char **argv)
{
    if (argc != 3) {
        std::fprintf(stderr, "usage: %s normalized_polar_plane.f32rgba complete_pf32_frame.f32rgba\n", argv[0]);
        return 2;
    }
    const std::vector<char> plane_bytes = read_all(argv[1]);
    const std::vector<char> oracle = read_all(argv[2]);
    constexpr std::size_t output_size = static_cast<std::size_t>(kOutputWidth) * kOutputHeight * 4 * sizeof(float);
    constexpr std::size_t polar_size = static_cast<std::size_t>(kPolarWidth) * kPolarHeight * 4 * sizeof(float);
    if (plane_bytes.size() != polar_size || oracle.size() != output_size) {
        std::fprintf(stderr, "invalid_size plane=%zu expected=%zu oracle=%zu expected=%zu\n",
                     plane_bytes.size(), polar_size, oracle.size(), output_size);
        return 2;
    }

    const float *plane = reinterpret_cast<const float *>(plane_bytes.data());
    std::vector<char> actual(output_size, 0);
    float *pixels = reinterpret_cast<float *>(actual.data());
    for (int y = 0; y < kOutputHeight; ++y) {
        for (int x = 0; x < kOutputWidth; ++x) {
            float radius = 0.0f;
            float angle = 0.0f;
            inverse_coordinate(x, y, radius, angle);
            if (radius >= 0.0f) {
                sample(plane, radius, angle, pixels + (static_cast<std::size_t>(y) * kOutputWidth + x) * 4);
            }
        }
    }

    std::size_t first = output_size;
    std::size_t differing = 0;
    for (std::size_t i = 0; i < output_size; ++i) {
        if (actual[i] != oracle[i]) {
            if (first == output_size) first = i;
            ++differing;
        }
    }
    std::printf("compared_bytes=%zu\ndiffering_bytes=%zu\n", output_size, differing);
    if (differing != 0) {
        std::printf("first_difference=%zu actual=%u oracle=%u\n", first,
                    static_cast<unsigned char>(actual[first]), static_cast<unsigned char>(oracle[first]));
        const std::size_t word = first / sizeof(float);
        float actual_float = 0.0f;
        float oracle_float = 0.0f;
        std::memcpy(&actual_float, actual.data() + word * sizeof(float), sizeof(float));
        std::memcpy(&oracle_float, oracle.data() + word * sizeof(float), sizeof(float));
        std::printf("first_float_word=%zu actual_float=%.9g oracle_float=%.9g\n", word, actual_float, oracle_float);
        return 1;
    }
    std::puts("status=exact_internal_pf32_frame");
    std::puts("ae_exact_claim=false");
    return 0;
}
