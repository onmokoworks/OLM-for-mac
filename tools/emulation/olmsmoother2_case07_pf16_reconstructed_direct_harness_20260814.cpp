#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr int kWidth = 1920;
constexpr int kHeight = 1080;
constexpr int kRowbytes = kWidth * static_cast<int>(sizeof(PF_Pixel16));
constexpr size_t kBytes = static_cast<size_t>(kRowbytes) * kHeight;

std::vector<unsigned char> Read(const char *path) {
    std::ifstream stream(path, std::ios::binary);
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(stream),
                                      std::istreambuf_iterator<char>());
}

std::string Hex(const unsigned char *data, size_t size) {
    static const char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(size * 2);
    for (size_t index = 0; index < size; ++index) {
        result.push_back(digits[data[index] >> 4]);
        result.push_back(digits[data[index] & 15]);
    }
    return result;
}

std::string Sha256(const void *data, size_t size) {
    olm::Sha256 sha;
    sha.update(data, size);
    unsigned char digest[32];
    sha.final(digest);
    return Hex(digest, sizeof(digest));
}

PF_PixelFloat Color(unsigned char a, unsigned char r,
                    unsigned char g, unsigned char b) {
    PF_PixelFloat value{};
    value.alpha = a / 255.0f;
    value.red = r / 255.0f;
    value.green = g / 255.0f;
    value.blue = b / 255.0f;
    return value;
}

SMParams Case07Params() {
    SMParams params;
    AEFX_CLR_STRUCT(params);
    params.enable_key = false;
    params.key_color = Color(255, 248, 233, 159);
    params.invert_key = false;
    params.smoothness_raw = 10;
    params.extra_smooth_raw = 1;
    params.smooth_range = 99;
    params.version = 2;
    params.gamma_mode = GAMMA_COLORS_ONLY;
    params.gamma_value = static_cast<float>(1.2699999809265137);
    params.num_gamma_colors = 2;
    params.gamma_colors[0] = Color(255, 233, 38, 239);
    params.gamma_colors[1] = Color(255, 192, 215, 172);
    params.gamma_colors[2] = Color(255, 124, 34, 100);
    params.gamma_colors[3] = Color(255, 17, 7, 127);
    params.gamma_colors[4] = Color(255, 212, 216, 8);
    params.keep_premul = false;
    return params;
}
}  // namespace

int main(int argc, char **argv) {
    if (argc != 3) {
        std::fprintf(stderr, "usage: input_argb16.raw output_argb16.raw\n");
        return 2;
    }
    std::vector<unsigned char> input = Read(argv[1]);
    if (input.size() != kBytes) {
        std::fprintf(stderr, "input size mismatch: %zu\n", input.size());
        return 3;
    }
    std::vector<unsigned char> output(kBytes, 0xa5);
    PF_EffectWorld input_world{};
    input_world.data = input.data();
    input_world.rowbytes = kRowbytes;
    input_world.width = kWidth;
    input_world.height = kHeight;
    input_world.bitdepth = 16;
    input_world.extent_hint = {0, 0, kWidth, kHeight};
    PF_EffectWorld output_world = input_world;
    output_world.data = output.data();

    PF_InData in_data{};
    SMParams params = Case07Params();
    const PF_Err err = RenderBits<PF_Pixel16>(
        &in_data, nullptr, &input_world, &output_world, &params);
    if (err) {
        std::fprintf(stderr, "render error=%d\n", static_cast<int>(err));
        return 4;
    }
    std::ofstream stream(argv[2], std::ios::binary);
    stream.write(reinterpret_cast<const char *>(output.data()), output.size());
    if (!stream) return 5;
    std::printf("INPUT_SHA256 %s\n", Sha256(input.data(), input.size()).c_str());
    std::printf("OUTPUT_SHA256 %s\n", Sha256(output.data(), output.size()).c_str());
    std::printf("BYTES %zu\n", output.size());
    return 0;
}
