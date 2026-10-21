#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr int kWidth = 1920;
constexpr int kHeight = 1080;
constexpr int kRowbytes = kWidth * static_cast<int>(sizeof(PF_Pixel8));
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
    return PF_PixelFloat{a / 255.0f, r / 255.0f, g / 255.0f, b / 255.0f};
}

PF_PixelFloat ParseColor(const char *text) {
    const unsigned long value = std::strtoul(text, nullptr, 16);
    return Color(static_cast<unsigned char>(value >> 24),
                 static_cast<unsigned char>(value >> 16),
                 static_cast<unsigned char>(value >> 8),
                 static_cast<unsigned char>(value));
}

SMParams Params(char **argv) {
    SMParams params;
    AEFX_CLR_STRUCT(params);
    params.enable_key = std::atoi(argv[3]) != 0;
    params.invert_key = std::atoi(argv[4]) != 0;
    params.smoothness_raw = std::atoi(argv[5]);
    params.extra_smooth_raw = std::atoi(argv[6]);
    params.smooth_range = std::atoi(argv[7]);
    params.version = std::atoi(argv[8]);
    params.gamma_mode = std::atoi(argv[9]);
    params.gamma_value = std::strtof(argv[10], nullptr);
    params.num_gamma_colors = std::atoi(argv[11]);
    params.key_color = ParseColor(argv[12]);
    for (int index = 0; index < NUM_GAMMA_COLORS; ++index) {
        params.gamma_colors[index] = ParseColor(argv[13 + index]);
    }
    params.keep_premul = false;
    return params;
}
}  // namespace

int main(int argc, char **argv) {
    if (argc != 18) {
        std::fprintf(stderr,
            "usage: input output enable invert smooth extra range version "
            "gamma_mode gamma_value gamma_count key gamma0..gamma4\n");
        return 2;
    }
    std::vector<unsigned char> input = Read(argv[1]);
    if (input.size() != kBytes) return 3;
    std::vector<unsigned char> output(kBytes, 0xa5);
    PF_EffectWorld input_world{};
    input_world.data = input.data();
    input_world.rowbytes = kRowbytes;
    input_world.width = kWidth;
    input_world.height = kHeight;
    input_world.bitdepth = 8;
    input_world.extent_hint = {0, 0, kWidth, kHeight};
    PF_EffectWorld output_world = input_world;
    output_world.data = output.data();
    PF_InData in_data{};
    SMParams params = Params(argv);
    const PF_Err err = RenderBits<PF_Pixel8>(
        &in_data, nullptr, &input_world, &output_world, &params);
    if (err) return 4;
    std::ofstream stream(argv[2], std::ios::binary);
    stream.write(reinterpret_cast<const char *>(output.data()), output.size());
    if (!stream) return 5;
    std::printf("INPUT_SHA256 %s\n", Sha256(input.data(), input.size()).c_str());
    std::printf("OUTPUT_SHA256 %s\n", Sha256(output.data(), output.size()).c_str());
    std::printf("BYTES %zu\n", output.size());
    return 0;
}
