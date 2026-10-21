#include <algorithm>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#include <zlib.h>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr size_t kBytes = 33177600u;

std::vector<unsigned char> Read(const char *path) {
    std::ifstream stream(path, std::ios::binary);
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(stream),
                                      std::istreambuf_iterator<char>());
}

std::vector<unsigned char> ReadGzip(const char *path) {
    gzFile stream = gzopen(path, "rb");
    if (!stream) return {};
    std::vector<unsigned char> result(kBytes);
    size_t offset = 0;
    while (offset < result.size()) {
        const int count = gzread(stream, result.data() + offset,
                                 static_cast<unsigned>(std::min<size_t>(1u << 20,
                                                                        result.size() - offset)));
        if (count <= 0) break;
        offset += static_cast<size_t>(count);
    }
    unsigned char extra = 0;
    const int tail = gzread(stream, &extra, 1);
    const int close_result = gzclose(stream);
    if (offset != result.size() || tail != 0 || close_result != Z_OK) return {};
    return result;
}

std::string Hex(const unsigned char *data, size_t size) {
    static const char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(size * 2);
    for (size_t i = 0; i < size; ++i) {
        result.push_back(digits[data[i] >> 4]);
        result.push_back(digits[data[i] & 15]);
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

void SetColor(PF_ParamDef &param, unsigned char a, unsigned char r,
              unsigned char g, unsigned char b) {
    param.u.cd.value.alpha = a;
    param.u.cd.value.red = r;
    param.u.cd.value.green = g;
    param.u.cd.value.blue = b;
}

void FillParams(PF_ParamDef params[SM_NUM_PARAMS]) {
    std::memset(params, 0, sizeof(PF_ParamDef) * SM_NUM_PARAMS);
    params[SM_ENABLE_KEY].u.bd.value = 0;
    SetColor(params[SM_KEY_COLOR], 255, 248, 233, 159);
    params[SM_INVERT_KEY].u.bd.value = 0;
    params[SM_SMOOTHNESS].u.sd.value = 10;
    params[SM_EXTRA_SMOOTH].u.sd.value = 1;
    params[SM_SMOOTH_RANGE].u.sd.value = 99;
    params[SM_VERSION].u.pd.value = 2;
    params[SM_GAMMA_MODE].u.pd.value = 1;
    params[SM_GAMMA_VALUE].u.fs_d.value = 1.2699999809265137;
    params[SM_NUM_GAMMA_COLORS].u.sd.value = 2;
    SetColor(params[SM_GAMMA_COLOR_0], 255, 233, 38, 239);
    SetColor(params[SM_GAMMA_COLOR_1], 255, 192, 215, 172);
    SetColor(params[SM_GAMMA_COLOR_2], 255, 124, 34, 100);
    SetColor(params[SM_GAMMA_COLOR_3], 255, 17, 7, 127);
    SetColor(params[SM_GAMMA_COLOR_4], 255, 212, 216, 8);
}
}  // namespace

int main(int argc, char **argv) {
    if (argc != 3) {
        std::fprintf(stderr, "usage: input_argb32f.raw output_argb32f.raw\n");
        return 2;
    }
    std::vector<unsigned char> input = ReadGzip(argv[1]);
    if (input.size() != kBytes ||
        Sha256(input.data(), input.size()) !=
            "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b") {
        std::fprintf(stderr, "input identity mismatch\n");
        return 3;
    }
    std::vector<unsigned char> output(kBytes, 0xa5);
    PF_EffectWorld input_world{};
    input_world.data = input.data();
    input_world.rowbytes = 30720;
    input_world.width = 1920;
    input_world.height = 1080;
    input_world.bitdepth = 32;
    input_world.extent_hint = {0, 0, 1920, 1080};
    PF_EffectWorld output_world = input_world;
    output_world.data = output.data();

    PF_ParamDef storage[SM_NUM_PARAMS];
    FillParams(storage);
    storage[SM_INPUT].u.ld = input_world;
    PF_ParamDef *params[SM_NUM_PARAMS];
    for (int i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &storage[i];
    PF_InData in_data{};
    in_data.pica_basicP = reinterpret_cast<void *>(1);
    SMParams decoded;
    AEFX_CLR_STRUCT(decoded);
    PF_Err err = FetchParams(&in_data, params, &decoded);
    if (!err) {
        err = RenderBits<PF_PixelFloat>(&in_data, params, &input_world,
                                        &output_world, &decoded);
    }
    if (err) {
        std::fprintf(stderr, "render error=%d\n", static_cast<int>(err));
        return 4;
    }
    std::ofstream stream(argv[2], std::ios::binary);
    stream.write(reinterpret_cast<const char *>(output.data()), output.size());
    if (!stream) return 5;
    std::printf("OUTPUT_SHA256 %s\n", Sha256(output.data(), output.size()).c_str());
    std::printf("INPUT_SHA256 %s\n", Sha256(input.data(), input.size()).c_str());
    std::printf("BYTES %zu\n", output.size());
    return 0;
}
