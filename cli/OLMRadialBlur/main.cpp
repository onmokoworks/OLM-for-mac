#include <png.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Image {
    int width = 0;
    int height = 0;
    int bit_depth = 8;
    std::vector<unsigned char> rgba;
    std::vector<uint16_t> rgba16;
};

struct RadialBlurParams {
    int blur_type = 1;
    double center_x = 960.0;
    double center_y = 540.0;
    int outer_strength = 0;
    int outer_offset_mode = 1;
    int outer_offset = 0;
    int outer_edge_fade = 0;
    int inner_strength = 0;
    int inner_offset_mode = 1;
    int inner_offset = 0;
    int inner_edge_fade = 0;
    bool repeat_border = true;
    double ratio = 1.0;
    double angle_deg = 0.0;
    double quality = 5.0;
    double brightness_gain = 1.0;
    double size_variation = 0.0;
    double noise_variation = 0.0;
    double comp_width = 1920.0;
    double comp_height = 1080.0;
    bool ignore_size_variation = false;
    std::string inner_alpha_mode = "max";
    bool inner_source_scatter_prepass = false;
    bool outer_source_scatter_prepass = false;
    std::string inner_prepass_mode = "tail-gather";
    std::string inner_prepass_span_mode = "edge-fade";
    std::string inner_prepass_weight_mode = "aex-alpha";
    std::string inner_prepass_factor_mode = "one";
    bool inner_prepass_overwrite_seed = false;
    std::string inner_scatter_rgb_mode = "straight";
    std::string inner_scatter_seed_mode = "source";
    std::string inner_seed_alpha_mode = "input";
    std::string inner_final_alpha_mode = "max";
    std::string inner_rgb_denominator_mode = "accum";
    std::string inner_scatter_span_scale_mode = "one";
    std::string inner_scatter_param10_plane = "one";
    std::string inner_wrap_mode = "aex-next-row";
    std::string inner_source_scale_mode = "one";
    std::string dynamic_offset_mode = "current";
    std::string polar_valid_mode = "strict";
    std::string polar_sample_mode = "plain";
    std::string rgba_sampler_alpha_mode = "shared-normalized";
    bool aex_quality_span_scale = true;
    bool inner_scatter_span_minus_one = true;
    bool inner_scatter_loop_minus_one = false;
    bool inner_scatter_table_span_minus_one = false;
    std::string rotation_gaussian_mode = "double";
    std::string zoom_grid_mode = "double";
    bool zoom_paired_trig_float = false;
    bool zoom_inverse_float = false;
    std::string zoom_aex_trig_table_path;
    std::string rotation_grid_mode = "double";
    double rotation_grid_angle_offset_steps = 0.0;
    double rotation_grid_radius_offset = 0.0;
    std::string outer_row_coupled_mode = "none";
    double outer_row_coupled_scale = 1.0;
    std::string outer_caller_collapse_mode = "none";
    std::string outer_alpha_quantize_mode = "epsilon";
    std::string final_polar_rgb_mode = "none";
    std::string inner_scatter_stats_path;
    std::string witness_dump_path;
    int witness_x = -1;
    int witness_y = -1;
    int witness_row_half_span = 4;
};

std::string g_rotation_gaussian_mode = "double";

struct PairedTrigFloat {
    float sin_value = 0.0f;
    float cos_value = 1.0f;
};

class Sha256 {
public:
    void update(const uint8_t *data, size_t size) {
        for (size_t i = 0; i < size; ++i) {
            block_[length_ & 63] = data[i];
            ++length_;
            if ((length_ & 63) == 0) transform();
        }
    }

    std::array<uint8_t, 32> finish() const {
        Sha256 copy = *this;
        const uint64_t bit_length = copy.length_ * 8;
        copy.update_byte(0x80);
        while ((copy.length_ & 63) != 56) copy.update_byte(0);
        for (int i = 7; i >= 0; --i) copy.update_byte(static_cast<uint8_t>(bit_length >> (i * 8)));
        std::array<uint8_t, 32> result{};
        for (size_t i = 0; i < copy.state_.size(); ++i) {
            for (int j = 0; j < 4; ++j) result[i * 4 + j] = static_cast<uint8_t>(copy.state_[i] >> (24 - j * 8));
        }
        return result;
    }

private:
    static uint32_t rotr(uint32_t value, int bits) { return (value >> bits) | (value << (32 - bits)); }
    void update_byte(uint8_t value) {
        block_[length_ & 63] = value;
        ++length_;
        if ((length_ & 63) == 0) transform();
    }
    void transform() {
        static constexpr uint32_t k[64] = {
            0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
            0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
            0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
            0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
            0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
            0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
            0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
            0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
        uint32_t w[64];
        for (int i = 0; i < 16; ++i) w[i] = (static_cast<uint32_t>(block_[i * 4]) << 24) |
            (static_cast<uint32_t>(block_[i * 4 + 1]) << 16) | (static_cast<uint32_t>(block_[i * 4 + 2]) << 8) | block_[i * 4 + 3];
        for (int i = 16; i < 64; ++i) {
            const uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
            const uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }
        uint32_t a=state_[0], b=state_[1], c=state_[2], d=state_[3], e=state_[4], f=state_[5], g=state_[6], h=state_[7];
        for (int i = 0; i < 64; ++i) {
            const uint32_t s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
            const uint32_t ch = (e & f) ^ (~e & g);
            const uint32_t temp1 = h + s1 + ch + k[i] + w[i];
            const uint32_t s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
            const uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            const uint32_t temp2 = s0 + maj;
            h=g; g=f; f=e; e=d+temp1; d=c; c=b; b=a; a=temp1+temp2;
        }
        state_[0]+=a; state_[1]+=b; state_[2]+=c; state_[3]+=d; state_[4]+=e; state_[5]+=f; state_[6]+=g; state_[7]+=h;
    }

    std::array<uint8_t, 64> block_{};
    uint64_t length_ = 0;
    std::array<uint32_t, 8> state_ = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
};

uint32_t read_le_u32(const std::vector<uint8_t> &data, size_t offset) {
    if (offset + 4 > data.size()) throw std::runtime_error("trig table header is truncated");
    return static_cast<uint32_t>(data[offset]) | (static_cast<uint32_t>(data[offset + 1]) << 8) |
           (static_cast<uint32_t>(data[offset + 2]) << 16) | (static_cast<uint32_t>(data[offset + 3]) << 24);
}

std::vector<PairedTrigFloat> load_zoom_trig_table(const std::string &path, int expected_count, float expected_step) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("failed to open Zoom AEX trig table: " + path);
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    constexpr size_t header_size = 20;
    constexpr size_t digest_size = 32;
    const char magic[] = "OLMTRIG1";
    if (data.size() < header_size + digest_size || !std::equal(magic, magic + 8, data.begin()))
        throw std::runtime_error("invalid Zoom AEX trig table magic");
    if (read_le_u32(data, 8) != 1) throw std::runtime_error("unsupported Zoom AEX trig table version");
    const uint32_t count = read_le_u32(data, 12);
    const uint32_t step_bits = read_le_u32(data, 16);
    const size_t payload_size = static_cast<size_t>(count) * 8;
    if (data.size() != header_size + payload_size + digest_size) throw std::runtime_error("Zoom AEX trig table length mismatch");
    uint32_t expected_step_bits = 0;
    std::memcpy(&expected_step_bits, &expected_step, sizeof(expected_step_bits));
    if (count != static_cast<uint32_t>(expected_count) || step_bits != expected_step_bits)
        throw std::runtime_error("Zoom AEX trig table grid metadata mismatch");
    Sha256 hash;
    hash.update(data.data(), header_size + payload_size);
    const auto digest = hash.finish();
    if (!std::equal(digest.begin(), digest.end(), data.begin() + header_size + payload_size))
        throw std::runtime_error("Zoom AEX trig table SHA-256 mismatch");
    std::vector<PairedTrigFloat> table(count);
    for (uint32_t i = 0; i < count; ++i) {
        std::memcpy(&table[i].sin_value, data.data() + header_size + i * 8, sizeof(float));
        std::memcpy(&table[i].cos_value, data.data() + header_size + i * 8 + 4, sizeof(float));
    }
    return table;
}

// FUN_18001d060 returns sine in the low lane and cosine in the high lane.
// This diagnostic preserves that paired call boundary, but intentionally uses
// platform sinf/cosf; it does not reproduce the AEX helper's SIMD polynomial.
PairedTrigFloat paired_trig_float(float theta) {
    PairedTrigFloat result;
    result.sin_value = ::sinf(theta);
    result.cos_value = ::cosf(theta);
    return result;
}

struct WitnessDump {
    struct PlaneProbePoint {
        int x = -1;
        int y = -1;
        float radius_index = 0.0f;
        float angle_index = 0.0f;
        double alpha = 0.0;
        double validity_alpha = 0.0;
        int alpha_u8 = 0;
        int validity_alpha_u8 = 0;
        float sample_rgba[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        int sample_u8[4] = {0, 0, 0, 0};
        float cell_valid[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        float cell_alpha[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    };

    bool enabled = false;
    bool captured = false;
    std::string path_kind;
    int x = -1;
    int y = -1;
    float radius_index = 0.0f;
    float angle_index = 0.0f;
    int sample_x0 = 0;
    int sample_x1 = 0;
    int sample_y0 = 0;
    int sample_y1 = 0;
    float fx = 0.0f;
    float fy = 0.0f;
    double w00 = 0.0;
    double w10 = 0.0;
    double w01 = 0.0;
    double w11 = 0.0;
    double a00 = 0.0;
    double a10 = 0.0;
    double a01 = 0.0;
    double a11 = 0.0;
    double alpha = 0.0;
    double validity_alpha = 0.0;
    float sample_rgba[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    int sample_u8[4] = {0, 0, 0, 0};
    double sample_rgb_numerator[3] = {0.0, 0.0, 0.0};
    float cell00_rgba[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float cell10_rgba[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float cell01_rgba[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float cell11_rgba[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float cell00_valid = 0.0f;
    float cell10_valid = 0.0f;
    float cell01_valid = 0.0f;
    float cell11_valid = 0.0f;
    int neighborhood_origin_x = 0;
    int neighborhood_origin_y = 0;
    float neighborhood_rgba[9][4] = {};
    float neighborhood_valid[9] = {};
    int source_probe_origin_x = 0;
    int source_probe_origin_y = 0;
    int source_probe_width = 11;
    int source_probe_height = 13;
    float source_probe_rgba[143][4] = {};
    std::string rgba_sampler_alpha_mode;
    std::string outer_caller_collapse_mode;
    int row_probe_half_span = 4;
    std::vector<PlaneProbePoint> row_probe;
};

void maybe_write_witness_dump(const RadialBlurParams &params, const WitnessDump &witness) {
    if (params.witness_dump_path.empty() || !witness.enabled || !witness.captured) return;
    std::ofstream out(params.witness_dump_path);
    if (!out) throw std::runtime_error("failed to open witness dump path: " + params.witness_dump_path);
    out << std::setprecision(10);
    out << "{\n";
    out << "  \"path_kind\": \"" << witness.path_kind << "\",\n";
    out << "  \"xy\": [" << witness.x << ", " << witness.y << "],\n";
    out << "  \"radius_index\": " << witness.radius_index << ",\n";
    out << "  \"angle_index\": " << witness.angle_index << ",\n";
    out << "  \"sample_x0\": " << witness.sample_x0 << ",\n";
    out << "  \"sample_x1\": " << witness.sample_x1 << ",\n";
    out << "  \"sample_y0\": " << witness.sample_y0 << ",\n";
    out << "  \"sample_y1\": " << witness.sample_y1 << ",\n";
    out << "  \"fx\": " << witness.fx << ",\n";
    out << "  \"fy\": " << witness.fy << ",\n";
    out << "  \"w00\": " << witness.w00 << ",\n";
    out << "  \"w10\": " << witness.w10 << ",\n";
    out << "  \"w01\": " << witness.w01 << ",\n";
    out << "  \"w11\": " << witness.w11 << ",\n";
    out << "  \"a00\": " << witness.a00 << ",\n";
    out << "  \"a10\": " << witness.a10 << ",\n";
    out << "  \"a01\": " << witness.a01 << ",\n";
    out << "  \"a11\": " << witness.a11 << ",\n";
    out << "  \"alpha\": " << witness.alpha << ",\n";
    out << "  \"validity_alpha\": " << witness.validity_alpha << ",\n";
    out << "  \"sample_rgba\": [" << witness.sample_rgba[0] << ", " << witness.sample_rgba[1] << ", "
        << witness.sample_rgba[2] << ", " << witness.sample_rgba[3] << "],\n";
    out << "  \"sample_u8\": [" << witness.sample_u8[0] << ", " << witness.sample_u8[1] << ", "
        << witness.sample_u8[2] << ", " << witness.sample_u8[3] << "],\n";
    out << "  \"sample_rgb_numerator\": [" << witness.sample_rgb_numerator[0] << ", "
        << witness.sample_rgb_numerator[1] << ", " << witness.sample_rgb_numerator[2] << "],\n";
    out << "  \"cell00_rgba\": [" << witness.cell00_rgba[0] << ", " << witness.cell00_rgba[1] << ", "
        << witness.cell00_rgba[2] << ", " << witness.cell00_rgba[3] << "],\n";
    out << "  \"cell10_rgba\": [" << witness.cell10_rgba[0] << ", " << witness.cell10_rgba[1] << ", "
        << witness.cell10_rgba[2] << ", " << witness.cell10_rgba[3] << "],\n";
    out << "  \"cell01_rgba\": [" << witness.cell01_rgba[0] << ", " << witness.cell01_rgba[1] << ", "
        << witness.cell01_rgba[2] << ", " << witness.cell01_rgba[3] << "],\n";
    out << "  \"cell11_rgba\": [" << witness.cell11_rgba[0] << ", " << witness.cell11_rgba[1] << ", "
        << witness.cell11_rgba[2] << ", " << witness.cell11_rgba[3] << "],\n";
    out << "  \"cell00_valid\": " << witness.cell00_valid << ",\n";
    out << "  \"cell10_valid\": " << witness.cell10_valid << ",\n";
    out << "  \"cell01_valid\": " << witness.cell01_valid << ",\n";
    out << "  \"cell11_valid\": " << witness.cell11_valid << ",\n";
    out << "  \"neighborhood_origin\": [" << witness.neighborhood_origin_x << ", " << witness.neighborhood_origin_y << "],\n";
    out << "  \"neighborhood\": [\n";
    for (int i = 0; i < 9; ++i) {
        const int nx = witness.neighborhood_origin_x + (i % 3);
        const int ny = witness.neighborhood_origin_y + (i / 3);
        out << "    {\"xy\": [" << nx << ", " << ny << "], "
            << "\"rgba\": [" << witness.neighborhood_rgba[i][0] << ", " << witness.neighborhood_rgba[i][1] << ", "
            << witness.neighborhood_rgba[i][2] << ", " << witness.neighborhood_rgba[i][3] << "], "
            << "\"valid\": " << witness.neighborhood_valid[i] << "}";
        out << (i == 8 ? "\n" : ",\n");
    }
    out << "  ],\n";
    out << "  \"source_probe_origin\": [" << witness.source_probe_origin_x << ", "
        << witness.source_probe_origin_y << "],\n";
    out << "  \"source_probe_size\": [" << witness.source_probe_width << ", "
        << witness.source_probe_height << "],\n";
    out << "  \"source_probe\": [\n";
    const int source_probe_count = witness.source_probe_width * witness.source_probe_height;
    for (int i = 0; i < source_probe_count; ++i) {
        const int nx = witness.source_probe_origin_x + (i % witness.source_probe_width);
        const int ny = witness.source_probe_origin_y + (i / witness.source_probe_width);
        out << "    {\"xy\": [" << nx << ", " << ny << "], "
            << "\"rgba\": [" << witness.source_probe_rgba[i][0] << ", "
            << witness.source_probe_rgba[i][1] << ", "
            << witness.source_probe_rgba[i][2] << ", "
            << witness.source_probe_rgba[i][3] << "]}";
        out << (i + 1 == source_probe_count ? "\n" : ",\n");
    }
    out << "  ],\n";
    out << "  \"rgba_sampler_alpha_mode\": \"" << witness.rgba_sampler_alpha_mode << "\",\n";
    out << "  \"outer_caller_collapse_mode\": \"" << witness.outer_caller_collapse_mode << "\",\n";
    out << "  \"row_probe_half_span\": " << witness.row_probe_half_span << ",\n";
    out << "  \"row_probe\": [\n";
    for (size_t i = 0; i < witness.row_probe.size(); ++i) {
        const auto &point = witness.row_probe[i];
        out << "    {\"xy\": [" << point.x << ", " << point.y << "], "
            << "\"radius_index\": " << point.radius_index << ", "
            << "\"angle_index\": " << point.angle_index << ", "
            << "\"alpha\": " << point.alpha << ", "
            << "\"validity_alpha\": " << point.validity_alpha << ", "
            << "\"alpha_u8\": " << point.alpha_u8 << ", "
            << "\"validity_alpha_u8\": " << point.validity_alpha_u8 << ", "
            << "\"sample_rgba\": [" << point.sample_rgba[0] << ", " << point.sample_rgba[1] << ", "
            << point.sample_rgba[2] << ", " << point.sample_rgba[3] << "], "
            << "\"sample_u8\": [" << point.sample_u8[0] << ", " << point.sample_u8[1] << ", "
            << point.sample_u8[2] << ", " << point.sample_u8[3] << "], "
            << "\"cell_valid\": [" << point.cell_valid[0] << ", " << point.cell_valid[1] << ", "
            << point.cell_valid[2] << ", " << point.cell_valid[3] << "], "
            << "\"cell_alpha\": [" << point.cell_alpha[0] << ", " << point.cell_alpha[1] << ", "
            << point.cell_alpha[2] << ", " << point.cell_alpha[3] << "]}";
        out << (i + 1 == witness.row_probe.size() ? "\n" : ",\n");
    }
    out << "  ]\n";
    out << "}\n";
}

struct Json {
    enum Type { Null, Bool, Number, String, Array, Object } type = Null;
    bool bool_value = false;
    double number_value = 0.0;
    std::string string_value;
    std::vector<Json> array_value;
    std::map<std::string, Json> object_value;

    const Json *get(const std::string &key) const {
        if (type != Object) return nullptr;
        auto it = object_value.find(key);
        return it == object_value.end() ? nullptr : &it->second;
    }
};

class JsonParser {
public:
    explicit JsonParser(std::string text) : text_(std::move(text)) {}

    Json parse() {
        Json value = parse_value();
        skip_ws();
        if (pos_ != text_.size()) throw std::runtime_error("unexpected trailing JSON data");
        return value;
    }

private:
    Json parse_value() {
        skip_ws();
        if (pos_ >= text_.size()) throw std::runtime_error("unexpected end of JSON");
        char c = text_[pos_];
        if (c == 'n') return parse_literal("null", Json{});
        if (c == 't') {
            Json v = parse_literal("true", Json{});
            v.type = Json::Bool;
            v.bool_value = true;
            return v;
        }
        if (c == 'f') {
            Json v = parse_literal("false", Json{});
            v.type = Json::Bool;
            v.bool_value = false;
            return v;
        }
        if (c == '"') return parse_string();
        if (c == '[') return parse_array();
        if (c == '{') return parse_object();
        return parse_number();
    }

    Json parse_literal(const char *literal, Json value) {
        std::string expected(literal);
        if (text_.compare(pos_, expected.size(), expected) != 0) {
            throw std::runtime_error("invalid JSON literal");
        }
        pos_ += expected.size();
        return value;
    }

    Json parse_string() {
        Json value;
        value.type = Json::String;
        ++pos_;
        while (pos_ < text_.size()) {
            char c = text_[pos_++];
            if (c == '"') return value;
            if (c != '\\') {
                value.string_value.push_back(c);
                continue;
            }
            if (pos_ >= text_.size()) throw std::runtime_error("unterminated JSON escape");
            char e = text_[pos_++];
            switch (e) {
            case '"': value.string_value.push_back('"'); break;
            case '\\': value.string_value.push_back('\\'); break;
            case '/': value.string_value.push_back('/'); break;
            case 'b': value.string_value.push_back('\b'); break;
            case 'f': value.string_value.push_back('\f'); break;
            case 'n': value.string_value.push_back('\n'); break;
            case 'r': value.string_value.push_back('\r'); break;
            case 't': value.string_value.push_back('\t'); break;
            case 'u':
                append_utf8(parse_hex4(), value.string_value);
                break;
            default:
                throw std::runtime_error("invalid JSON escape");
            }
        }
        throw std::runtime_error("unterminated JSON string");
    }

    Json parse_number() {
        size_t start = pos_;
        if (text_[pos_] == '-') ++pos_;
        while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) ++pos_;
        if (pos_ < text_.size() && text_[pos_] == '.') {
            ++pos_;
            while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) ++pos_;
        }
        if (pos_ < text_.size() && (text_[pos_] == 'e' || text_[pos_] == 'E')) {
            ++pos_;
            if (pos_ < text_.size() && (text_[pos_] == '+' || text_[pos_] == '-')) ++pos_;
            while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) ++pos_;
        }
        if (start == pos_) throw std::runtime_error("expected JSON value");
        Json value;
        value.type = Json::Number;
        value.number_value = std::strtod(text_.c_str() + start, nullptr);
        return value;
    }

    Json parse_array() {
        Json value;
        value.type = Json::Array;
        ++pos_;
        skip_ws();
        if (peek(']')) return value;
        while (true) {
            value.array_value.push_back(parse_value());
            skip_ws();
            if (peek(']')) return value;
            expect(',');
        }
    }

    Json parse_object() {
        Json value;
        value.type = Json::Object;
        ++pos_;
        skip_ws();
        if (peek('}')) return value;
        while (true) {
            skip_ws();
            Json key = parse_string();
            skip_ws();
            expect(':');
            value.object_value[key.string_value] = parse_value();
            skip_ws();
            if (peek('}')) return value;
            expect(',');
        }
    }

    unsigned parse_hex4() {
        if (pos_ + 4 > text_.size()) throw std::runtime_error("short unicode escape");
        unsigned value = 0;
        for (int i = 0; i < 4; ++i) {
            char c = text_[pos_++];
            value <<= 4;
            if (c >= '0' && c <= '9') value += static_cast<unsigned>(c - '0');
            else if (c >= 'a' && c <= 'f') value += static_cast<unsigned>(c - 'a' + 10);
            else if (c >= 'A' && c <= 'F') value += static_cast<unsigned>(c - 'A' + 10);
            else throw std::runtime_error("invalid unicode escape");
        }
        return value;
    }

    static void append_utf8(unsigned cp, std::string &out) {
        if (cp <= 0x7f) {
            out.push_back(static_cast<char>(cp));
        } else if (cp <= 0x7ff) {
            out.push_back(static_cast<char>(0xc0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3f)));
        } else {
            out.push_back(static_cast<char>(0xe0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3f)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3f)));
        }
    }

    void skip_ws() {
        while (pos_ < text_.size() && std::isspace(static_cast<unsigned char>(text_[pos_]))) ++pos_;
    }

    bool peek(char c) {
        if (pos_ < text_.size() && text_[pos_] == c) {
            ++pos_;
            return true;
        }
        return false;
    }

    void expect(char c) {
        skip_ws();
        if (pos_ >= text_.size() || text_[pos_] != c) throw std::runtime_error("unexpected JSON character");
        ++pos_;
    }

    std::string text_;
    size_t pos_ = 0;
};

std::string read_text_file(const std::string &path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("failed to open " + path);
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

double json_number_or(const Json *value, double fallback) {
    if (!value) return fallback;
    if (value->type == Json::Number) return value->number_value;
    if (value->type == Json::Bool) return value->bool_value ? 1.0 : 0.0;
    if (value->type == Json::String) {
        char *end = nullptr;
        double parsed = std::strtod(value->string_value.c_str(), &end);
        if (end && *end == '\0') return parsed;
    }
    return fallback;
}

const Json *find_effect_params(const Json &root) {
    const Json *scope = &root;
    if (const Json *params = root.get("params")) scope = params;
    const Json *effects = scope->get("effects");
    if (!effects || effects->type != Json::Array) return scope;
    for (const Json &effect : effects->array_value) {
        const Json *name = effect.get("name");
        const Json *match = effect.get("match_name");
        bool is_target = false;
        if (name && name->type == Json::String && name->string_value == "OLM RadialBlur") is_target = true;
        if (match && match->type == Json::String && match->string_value == "OLM RadialBlur") is_target = true;
        if (is_target) {
            if (const Json *params = effect.get("params")) return params;
        }
    }
    return scope;
}

RadialBlurParams read_params(const std::string &path) {
    Json root = JsonParser(read_text_file(path)).parse();
    RadialBlurParams rp;
    const Json *params = find_effect_params(root);
    if (params && params->type == Json::Array) {
        std::string group = "root";
        for (const Json &param : params->array_value) {
            const Json *name_json = param.get("name");
            if (!name_json || name_json->type != Json::String) continue;
            const std::string &name = name_json->string_value;
            if (name == "Outer Blur") {
                group = "outer";
                continue;
            }
            if (name == "Inner Blur") {
                group = "inner";
                continue;
            }
            if (name == "Ellipse") {
                group = "ellipse";
                continue;
            }
            if (name == "Noise Parameters") {
                group = "noise";
                continue;
            }
            const Json *value = param.get("value");
            if (!value) continue;

            if (group == "root" && name == "Blur Type") {
                rp.blur_type = static_cast<int>(json_number_or(value, rp.blur_type));
            } else if (group == "root" && name == "Center" && value->type == Json::Array && value->array_value.size() >= 2) {
                rp.center_x = json_number_or(&value->array_value[0], rp.center_x);
                rp.center_y = json_number_or(&value->array_value[1], rp.center_y);
            } else if (group == "outer" && name == "Strength") {
                rp.outer_strength = static_cast<int>(json_number_or(value, rp.outer_strength));
            } else if (group == "outer" && name == "Offset Mode") {
                rp.outer_offset_mode = static_cast<int>(json_number_or(value, rp.outer_offset_mode));
            } else if (group == "outer" && name == "Offset") {
                rp.outer_offset = static_cast<int>(json_number_or(value, rp.outer_offset));
            } else if (group == "outer" && name == "Edge Fade") {
                rp.outer_edge_fade = static_cast<int>(json_number_or(value, rp.outer_edge_fade));
            } else if (group == "inner" && name == "Strength") {
                rp.inner_strength = static_cast<int>(json_number_or(value, rp.inner_strength));
            } else if (group == "inner" && name == "Offset Mode") {
                rp.inner_offset_mode = static_cast<int>(json_number_or(value, rp.inner_offset_mode));
            } else if (group == "inner" && name == "Offset") {
                rp.inner_offset = static_cast<int>(json_number_or(value, rp.inner_offset));
            } else if (group == "inner" && name == "Edge Fade") {
                rp.inner_edge_fade = static_cast<int>(json_number_or(value, rp.inner_edge_fade));
            } else if (name == "Repeat Border") {
                rp.repeat_border = json_number_or(value, rp.repeat_border ? 1.0 : 0.0) != 0.0;
            } else if (group == "ellipse" && name == "Ratio") {
                rp.ratio = json_number_or(value, rp.ratio);
            } else if (group == "ellipse" && name == "Angle") {
                rp.angle_deg = json_number_or(value, rp.angle_deg);
            } else if (name == "Quality") {
                rp.quality = json_number_or(value, rp.quality);
            } else if (name == "Brightness Gain") {
                rp.brightness_gain = json_number_or(value, rp.brightness_gain);
            } else if (name == "Size Variation") {
                rp.size_variation = json_number_or(value, rp.size_variation);
            } else if (name == "Noise Variation") {
                rp.noise_variation = json_number_or(value, rp.noise_variation);
            }
        }
    }
    if (const Json *comp = root.get("comp")) {
        rp.comp_width = json_number_or(comp->get("width"), rp.comp_width);
        rp.comp_height = json_number_or(comp->get("height"), rp.comp_height);
    }
    return rp;
}

Image read_png(const std::string &path) {
    FILE *fp = std::fopen(path.c_str(), "rb");
    if (!fp) throw std::runtime_error("failed to open input PNG " + path);

    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, nullptr, nullptr, nullptr);
    png_infop info = png_create_info_struct(png);
    if (!png || !info) {
        std::fclose(fp);
        png_destroy_read_struct(&png, &info, nullptr);
        throw std::runtime_error("failed to initialize libpng reader");
    }
    if (setjmp(png_jmpbuf(png))) {
        png_destroy_read_struct(&png, &info, nullptr);
        std::fclose(fp);
        throw std::runtime_error("failed to read PNG " + path);
    }

    png_init_io(png, fp);
    png_read_info(png, info);
    png_uint_32 width = png_get_image_width(png, info);
    png_uint_32 height = png_get_image_height(png, info);
    int color_type = png_get_color_type(png, info);
    int bit_depth = png_get_bit_depth(png, info);

    int original_bit_depth = bit_depth;
    if (original_bit_depth == 16) png_set_swap(png);
    if (color_type == PNG_COLOR_TYPE_PALETTE) png_set_palette_to_rgb(png);
    if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8) png_set_expand_gray_1_2_4_to_8(png);
    bool has_alpha = (color_type & PNG_COLOR_MASK_ALPHA) != 0;
    bool has_trns = png_get_valid(png, info, PNG_INFO_tRNS) != 0;
    if (has_trns) png_set_tRNS_to_alpha(png);
    if (color_type == PNG_COLOR_TYPE_GRAY || color_type == PNG_COLOR_TYPE_GRAY_ALPHA) png_set_gray_to_rgb(png);
    if (!has_alpha && !has_trns) png_set_filler(png, 0xff, PNG_FILLER_AFTER);

    png_read_update_info(png, info);
    Image image;
    image.width = static_cast<int>(width);
    image.height = static_cast<int>(height);
    image.bit_depth = original_bit_depth == 16 ? 16 : 8;
    if (image.bit_depth == 16) {
        if (png_get_rowbytes(png, info) != width * 8) {
            png_destroy_read_struct(&png, &info, nullptr);
            std::fclose(fp);
            throw std::runtime_error("unsupported PNG color conversion result");
        }
        image.rgba16.resize(static_cast<size_t>(image.width) * static_cast<size_t>(image.height) * 4);
        std::vector<png_bytep> rows(image.height);
        for (int y = 0; y < image.height; ++y) rows[y] = reinterpret_cast<png_bytep>(image.rgba16.data() + static_cast<size_t>(y) * image.width * 4);
        png_read_image(png, rows.data());
    } else {
        if (png_get_rowbytes(png, info) != width * 4) {
            png_destroy_read_struct(&png, &info, nullptr);
            std::fclose(fp);
            throw std::runtime_error("unsupported PNG color conversion result");
        }
        image.rgba.resize(static_cast<size_t>(image.width) * static_cast<size_t>(image.height) * 4);
        std::vector<png_bytep> rows(image.height);
        for (int y = 0; y < image.height; ++y) rows[y] = image.rgba.data() + static_cast<size_t>(y) * image.width * 4;
        png_read_image(png, rows.data());
    }
    png_read_end(png, nullptr);
    png_destroy_read_struct(&png, &info, nullptr);
    std::fclose(fp);
    return image;
}

void write_png(const std::string &path, const Image &image) {
    std::filesystem::path out_path(path);
    if (!out_path.parent_path().empty()) std::filesystem::create_directories(out_path.parent_path());

    FILE *fp = std::fopen(path.c_str(), "wb");
    if (!fp) throw std::runtime_error("failed to open output PNG " + path);

    png_structp png = png_create_write_struct(PNG_LIBPNG_VER_STRING, nullptr, nullptr, nullptr);
    png_infop info = png_create_info_struct(png);
    if (!png || !info) {
        std::fclose(fp);
        png_destroy_write_struct(&png, &info);
        throw std::runtime_error("failed to initialize libpng writer");
    }
    if (setjmp(png_jmpbuf(png))) {
        png_destroy_write_struct(&png, &info);
        std::fclose(fp);
        throw std::runtime_error("failed to write PNG " + path);
    }

    png_init_io(png, fp);
    png_set_IHDR(png, info, image.width, image.height, image.bit_depth, PNG_COLOR_TYPE_RGBA,
                 PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    if (image.bit_depth == 16) png_set_swap(png);
    png_write_info(png, info);
    std::vector<png_bytep> rows(image.height);
    for (int y = 0; y < image.height; ++y) {
        if (image.bit_depth == 16) {
            rows[y] = reinterpret_cast<png_bytep>(const_cast<uint16_t *>(image.rgba16.data() + static_cast<size_t>(y) * image.width * 4));
        } else {
            rows[y] = const_cast<unsigned char *>(image.rgba.data() + static_cast<size_t>(y) * image.width * 4);
        }
    }
    png_write_image(png, rows.data());
    png_write_end(png, nullptr);
    png_destroy_write_struct(&png, &info);
    std::fclose(fp);
}

struct FloatImage {
    int width = 0;
    int height = 0;
    std::vector<float> rgba;
};

struct RotationTypedPlanes {
    FloatImage polar;
    FloatImage accum;
    FloatImage collapsed;
    std::vector<float> prepass_alpha;
    std::vector<float> scatter_alpha;
    std::vector<float> source_alpha;
    std::vector<std::array<float, 2>> polar_coordinates;
    std::vector<uint8_t> polar_valid;
};

struct RotationTypedPolarInput {
    int width = 0;
    int height = 0;
    int row_stride = 0;
    std::vector<float> rgba;
    std::vector<uint8_t> polar_valid;
};

float clamp_float(float v, float lo, float hi) {
    return std::max(lo, std::min(v, hi));
}

using Complex = std::complex<double>;

struct InnerScatterStats {
    long long outer_calls = 0;
    long long inner_calls = 0;
    long long inner_source_skips = 0;
    long long inner_effective_span_le1 = 0;
    long long inner_total_effective_span = 0;
    long long inner_total_loop_limit = 0;
    long long inner_writes = 0;
    long long inner_underflow_wraps = 0;
    long long inner_oob_radius_skips = 0;
    long long inner_zero_contribution_skips = 0;
    std::map<int, long long> outer_caller_span_hist;
    std::map<int, long long> inner_caller_span_hist;
    std::map<int, long long> inner_effective_span_hist;
    std::map<int, long long> inner_loop_limit_hist;
};

void write_inner_scatter_stats(const std::string &path, const InnerScatterStats &stats) {
    if (path.empty()) return;
    std::filesystem::path out_path(path);
    if (!out_path.parent_path().empty()) std::filesystem::create_directories(out_path.parent_path());
    std::ofstream out(path, std::ios::binary);
    if (!out) throw std::runtime_error("failed to open inner scatter stats output " + path);
    auto write_hist = [&](const std::map<int, long long> &hist) {
        out << "{";
        bool first = true;
        for (const auto &[key, value] : hist) {
            if (!first) out << ",";
            first = false;
            out << "\"" << key << "\":" << value;
        }
        out << "}";
    };
    out << "{\n";
    out << "  \"outer_calls\": " << stats.outer_calls << ",\n";
    out << "  \"inner_calls\": " << stats.inner_calls << ",\n";
    out << "  \"inner_source_skips\": " << stats.inner_source_skips << ",\n";
    out << "  \"inner_effective_span_le1\": " << stats.inner_effective_span_le1 << ",\n";
    out << "  \"inner_total_effective_span\": " << stats.inner_total_effective_span << ",\n";
    out << "  \"inner_total_loop_limit\": " << stats.inner_total_loop_limit << ",\n";
    out << "  \"inner_writes\": " << stats.inner_writes << ",\n";
    out << "  \"inner_underflow_wraps\": " << stats.inner_underflow_wraps << ",\n";
    out << "  \"inner_oob_radius_skips\": " << stats.inner_oob_radius_skips << ",\n";
    out << "  \"inner_zero_contribution_skips\": " << stats.inner_zero_contribution_skips << ",\n";
    out << "  \"outer_caller_span_hist\": ";
    write_hist(stats.outer_caller_span_hist);
    out << ",\n  \"inner_caller_span_hist\": ";
    write_hist(stats.inner_caller_span_hist);
    out << ",\n";
    out << "  \"inner_effective_span_hist\": ";
    write_hist(stats.inner_effective_span_hist);
    out << ",\n  \"inner_loop_limit_hist\": ";
    write_hist(stats.inner_loop_limit_hist);
    out << "\n}\n";
}

int next_power_of_two(int value) {
    int out = 1;
    while (out < value) out <<= 1;
    return out;
}

void fft(std::vector<Complex> &a, bool invert) {
    const int n = static_cast<int>(a.size());
    for (int i = 1, j = 0; i < n; ++i) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) std::swap(a[static_cast<size_t>(i)], a[static_cast<size_t>(j)]);
    }

    for (int len = 2; len <= n; len <<= 1) {
        const double angle = (invert ? -2.0 : 2.0) * M_PI / static_cast<double>(len);
        const Complex wlen(std::cos(angle), std::sin(angle));
        for (int i = 0; i < n; i += len) {
            Complex w(1.0, 0.0);
            const int half = len >> 1;
            for (int j = 0; j < half; ++j) {
                Complex u = a[static_cast<size_t>(i + j)];
                Complex v = a[static_cast<size_t>(i + j + half)] * w;
                a[static_cast<size_t>(i + j)] = u + v;
                a[static_cast<size_t>(i + j + half)] = u - v;
                w *= wlen;
            }
        }
    }

    if (invert) {
        const double inv_n = 1.0 / static_cast<double>(n);
        for (Complex &value : a) value *= inv_n;
    }
}

class ForwardConvolver {
public:
    ForwardConvolver(int value_count, const std::vector<float> &weights)
        : value_count_(value_count),
          fft_count_(next_power_of_two(value_count + static_cast<int>(weights.size()) - 1)),
          kernel_fft_(static_cast<size_t>(fft_count_)) {
        for (size_t i = 0; i < weights.size(); ++i) kernel_fft_[i] = Complex(weights[i], 0.0);
        fft(kernel_fft_, false);
    }

    void convolve(const std::vector<double> &values, std::vector<double> &out) const {
        std::vector<Complex> spectrum(static_cast<size_t>(fft_count_));
        for (int i = 0; i < value_count_; ++i) spectrum[static_cast<size_t>(i)] = Complex(values[static_cast<size_t>(i)], 0.0);
        fft(spectrum, false);
        for (int i = 0; i < fft_count_; ++i) spectrum[static_cast<size_t>(i)] *= kernel_fft_[static_cast<size_t>(i)];
        fft(spectrum, true);
        out.resize(static_cast<size_t>(value_count_));
        for (int i = 0; i < value_count_; ++i) out[static_cast<size_t>(i)] = spectrum[static_cast<size_t>(i)].real();
    }

private:
    int value_count_ = 0;
    int fft_count_ = 0;
    std::vector<Complex> kernel_fft_;
};

float sample_channel(const FloatImage &image, float x, float y, int channel, bool repeat) {
    const int w = image.width;
    const int h = image.height;
    bool valid = true;
    if (repeat) {
        x = clamp_float(x, 0.0f, static_cast<float>(w - 1));
        y = clamp_float(y, 0.0f, static_cast<float>(h - 1));
    } else {
        valid = x >= 0.0f && x <= static_cast<float>(w - 1) && y >= 0.0f && y <= static_cast<float>(h - 1);
        x = clamp_float(x, 0.0f, static_cast<float>(w - 1));
        y = clamp_float(y, 0.0f, static_cast<float>(h - 1));
    }
    if (!valid) return 0.0f;
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    int x1 = std::min(x0 + 1, w - 1);
    int y1 = std::min(y0 + 1, h - 1);
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    auto at = [&](int px, int py) -> float {
        return image.rgba[(static_cast<size_t>(py) * w + px) * 4 + channel];
    };
    float top = at(x0, y0) * (1.0f - fx) + at(x1, y0) * fx;
    float bottom = at(x0, y1) * (1.0f - fx) + at(x1, y1) * fx;
    return top * (1.0f - fy) + bottom * fy;
}

float sample_scalar_plane(const std::vector<float> &plane, int w, int h, float x, float y, bool repeat) {
    bool valid = true;
    if (repeat) {
        x = clamp_float(x, 0.0f, static_cast<float>(w - 1));
        y = clamp_float(y, 0.0f, static_cast<float>(h - 1));
    } else {
        valid = x >= 0.0f && x <= static_cast<float>(w - 1) && y >= 0.0f && y <= static_cast<float>(h - 1);
        x = clamp_float(x, 0.0f, static_cast<float>(w - 1));
        y = clamp_float(y, 0.0f, static_cast<float>(h - 1));
    }
    if (!valid) return 0.0f;
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    int x1 = std::min(x0 + 1, w - 1);
    int y1 = std::min(y0 + 1, h - 1);
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    auto at = [&](int px, int py) -> float {
        return plane[static_cast<size_t>(py) * w + px];
    };
    float top = at(x0, y0) * (1.0f - fx) + at(x1, y0) * fx;
    float bottom = at(x0, y1) * (1.0f - fx) + at(x1, y1) * fx;
    return top * (1.0f - fy) + bottom * fy;
}

std::vector<float> build_size_factor_plane(const FloatImage &src, double size_variation_percent) {
    const int w = src.width;
    const int h = src.height;
    const size_t count = static_cast<size_t>(w) * h;
    std::vector<float> factor(count, 1.0f);
    const float sv = clamp_float(static_cast<float>(size_variation_percent * 0.01), 0.0f, 1.0f);
    if (sv <= 0.0f || count == 0) return factor;

    std::vector<int> dist(count, 0);
    bool has_opaque = false;
    bool has_transparent = false;
    constexpr int inf = 1 << 28;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const size_t cell = static_cast<size_t>(y) * w + x;
            const float alpha = src.rgba[cell * 4 + 3];
            if (alpha > 0.0f) {
                dist[cell] = inf;
                has_opaque = true;
            } else {
                dist[cell] = 0;
                has_transparent = true;
            }
        }
    }
    if (!has_opaque || !has_transparent) return factor;

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const size_t cell = static_cast<size_t>(y) * w + x;
            int best = dist[cell];
            if (x > 0) best = std::min(best, dist[cell - 1] + 1);
            if (y > 0) best = std::min(best, dist[cell - static_cast<size_t>(w)] + 1);
            dist[cell] = best;
        }
    }
    int max_dist = 0;
    for (int y = h - 1; y >= 0; --y) {
        for (int x = w - 1; x >= 0; --x) {
            const size_t cell = static_cast<size_t>(y) * w + x;
            int best = dist[cell];
            if (x + 1 < w) best = std::min(best, dist[cell + 1] + 1);
            if (y + 1 < h) best = std::min(best, dist[cell + static_cast<size_t>(w)] + 1);
            dist[cell] = best;
            if (best < inf) max_dist = std::max(max_dist, best);
        }
    }
    if (max_dist <= 0) return factor;

    for (size_t cell = 0; cell < count; ++cell) {
        const float normalized = dist[cell] >= inf ? 1.0f : static_cast<float>(dist[cell]) / static_cast<float>(max_dist);
        factor[cell] = normalized * sv + (1.0f - sv);
    }
    return factor;
}

void sample_rgba_aex_alpha(const FloatImage &image,
                           float x,
                           float y,
                           bool repeat,
                           const std::string &alpha_mode,
                           float out[4]) {
    const int w = image.width;
    const int h = image.height;
    for (int c = 0; c < 4; ++c) out[c] = 0.0f;
    int xi = static_cast<int>(x);
    int yi = static_cast<int>(y);
    if (!repeat && !(-2 < xi && xi < w && -2 < yi && yi < h)) return;

    float fx = x - static_cast<float>(xi);
    float fy = y - static_cast<float>(yi);
    int x0 = xi;
    int x1 = xi + 1;
    int y0 = yi;
    int y1 = yi + 1;
    if (repeat) {
        x0 = std::max(0, std::min(x0, w - 1));
        x1 = std::max(0, std::min(x1, w - 1));
        y0 = std::max(0, std::min(y0, h - 1));
        y1 = std::max(0, std::min(y1, h - 1));
    }

    double rgb_sum[3] = {0.0, 0.0, 0.0};
    double alpha_sum = 0.0;
    float alpha_sum_f32 = 0.0f;
    double weight_sum = 0.0;
    auto tap = [&](int px, int py, double weight) {
        if (weight == 0.0) return;
        if (px < 0 || px >= w || py < 0 || py >= h) return;
        const size_t idx = (static_cast<size_t>(py) * w + px) * 4;
        const double alpha_weight = static_cast<double>(image.rgba[idx + 3]) * weight;
        alpha_sum += alpha_weight;
        const float alpha_weight_f32 = static_cast<float>(image.rgba[idx + 3] * static_cast<float>(weight));
        alpha_sum_f32 = static_cast<float>(alpha_sum_f32 + alpha_weight_f32);
        weight_sum += weight;
        for (int c = 0; c < 3; ++c) {
            rgb_sum[c] += static_cast<double>(image.rgba[idx + c]) * alpha_weight;
        }
    };

    tap(x0, y0, (1.0f - fx) * (1.0f - fy));
    tap(x1, y0, fx * (1.0f - fy));
    tap(x0, y1, (1.0f - fx) * fy);
    tap(x1, y1, fx * fy);
    if (alpha_sum > 1.0e-12) {
        for (int c = 0; c < 3; ++c) out[c] = static_cast<float>(rgb_sum[c] / alpha_sum);
        if (repeat && alpha_mode == "repeat-raw") {
            out[3] = static_cast<float>(alpha_sum);
        } else if (repeat && alpha_mode == "repeat-raw-f32") {
            out[3] = alpha_sum_f32;
        } else {
            out[3] = static_cast<float>(alpha_sum / std::max(1.0e-12, weight_sum));
        }
    }
}

std::vector<float> zoom_gaussian_weights(int length) {
    if (length <= 1) return std::vector<float>{1.0f};
    std::vector<float> weights(static_cast<size_t>(length));
    const double denom = static_cast<double>(length) * static_cast<double>(length) * 2.0 * 0.111111119389534 + 1.0e-5;
    const double inv_denom = 1.0 / denom;
    for (int i = 0; i < length; ++i) weights[static_cast<size_t>(i)] = static_cast<float>(std::exp(-(i * i) * inv_denom));
    return weights;
}

std::vector<float> rotation_gaussian_weights(int length) {
    if (length <= 1) return std::vector<float>{1.0f};
    constexpr int table_len = 30000;
    const double denom = static_cast<double>(table_len) * static_cast<double>(table_len) * 2.0 * 0.111111119389534 + 1.0e-5;
    const double inv_denom = 1.0 / denom;
    float aex_inv_denom = 0.0f;
    if (g_rotation_gaussian_mode == "aex-float") {
        float aex_denom = static_cast<float>(table_len);
        aex_denom = aex_denom * aex_denom;
        aex_denom = aex_denom * 0.111111119389534f;
        aex_denom = aex_denom + aex_denom;
        aex_denom = static_cast<float>(static_cast<double>(aex_denom) + 1.0e-5);
        aex_inv_denom = 1.0f / aex_denom;
    }
    const int idx_scale = table_len / length;
    std::vector<float> weights(static_cast<size_t>(length), 1.0f);
    for (int i = 1; i < length; ++i) {
        const int table_index = static_cast<int>(static_cast<float>(i) * static_cast<float>(idx_scale));
        if (g_rotation_gaussian_mode == "aex-float") {
            float arg = static_cast<float>(-(table_index * table_index));
            arg = arg * aex_inv_denom;
            weights[static_cast<size_t>(i)] = std::exp(arg);
        } else {
            weights[static_cast<size_t>(i)] = static_cast<float>(std::exp(-(table_index * table_index) * inv_denom));
        }
    }
    return weights;
}

float rotation_gaussian_reindexed_weight(int table_length, int offset) {
    if (table_length <= 1 || offset <= 0) return 1.0f;
    constexpr int table_len = 30000;
    const int idx_scale = table_len / table_length;
    const int table_index = static_cast<int>(static_cast<float>(offset) * static_cast<float>(idx_scale));
    if (g_rotation_gaussian_mode == "aex-float") {
        float denom = static_cast<float>(table_len);
        denom = denom * denom;
        denom = denom * 0.111111119389534f;
        denom = denom + denom;
        denom = static_cast<float>(static_cast<double>(denom) + 1.0e-5);
        float arg = static_cast<float>(-(table_index * table_index));
        arg = arg * (1.0f / denom);
        return std::exp(arg);
    }
    const double denom = static_cast<double>(table_len) * static_cast<double>(table_len) * 2.0 * 0.111111119389534 + 1.0e-5;
    const double inv_denom = 1.0 / denom;
    return static_cast<float>(std::exp(-(table_index * table_index) * inv_denom));
}

float rotation_gaussian_weight_at(int span, int offset) {
    if (span <= 1 || offset <= 0) return 1.0f;
    const int table_index = offset;
    if (g_rotation_gaussian_mode == "aex-float") {
        float denom = static_cast<float>(span);
        denom = denom * denom;
        denom = denom * 0.111111119389534f;
        denom = denom + denom;
        denom = static_cast<float>(static_cast<double>(denom) + 1.0e-5);
        float arg = static_cast<float>(-(table_index * table_index));
        arg = arg * (1.0f / denom);
        return std::exp(arg);
    }
    const double denom = static_cast<double>(span) * static_cast<double>(span) * 2.0 * 0.111111119389534 + 1.0e-5;
    const double inv_denom = 1.0 / denom;
    return static_cast<float>(std::exp(-(table_index * table_index) * inv_denom));
}

float rotation_gaussian_weight_at_scaled(int table_span, int offset, float alpha_scale) {
    if (table_span <= 1 || offset <= 0) return 1.0f;
    if (alpha_scale <= 1.0e-8f) return 0.0f;
    const int table_index = static_cast<int>(static_cast<float>(offset) / alpha_scale);
    if (g_rotation_gaussian_mode == "aex-float") {
        float denom = static_cast<float>(table_span);
        denom = denom * denom;
        denom = denom * 0.111111119389534f;
        denom = denom + denom;
        denom = static_cast<float>(static_cast<double>(denom) + 1.0e-5);
        float arg = static_cast<float>(-(table_index * table_index));
        arg = arg * (1.0f / denom);
        return std::exp(arg);
    }
    const double denom = static_cast<double>(table_span) * static_cast<double>(table_span) * 2.0 * 0.111111119389534 + 1.0e-5;
    const double inv_denom = 1.0 / denom;
    return static_cast<float>(std::exp(-(table_index * table_index) * inv_denom));
}

int zoom_effective_length(const RadialBlurParams &params) {
    int span = params.outer_strength;
    if (params.outer_offset_mode == 2) span = std::max(params.outer_strength, params.outer_offset);
    else if (params.outer_offset_mode == 3) span = params.outer_offset;
    return std::max(0, std::min(span, 3000));
}

int rotation_effective_length(int strength, int offset_mode, int dynamic_offset) {
    int span = strength;
    if (offset_mode == 1) span = strength + dynamic_offset;
    else if (offset_mode == 2) span = std::max(strength, dynamic_offset);
    else if (offset_mode == 3) span = dynamic_offset;
    return std::max(0, std::min(span - 1, 3000));
}

int rotation_scatter_span(int strength, int offset_mode, int dynamic_offset) {
    int span = strength;
    if (offset_mode == 1) span = strength + dynamic_offset;
    else if (offset_mode == 2) span = std::max(strength, dynamic_offset);
    else if (offset_mode == 3) span = dynamic_offset;
    return std::max(0, std::min(span, 3000));
}

int scale_aex_span_param(int value, double quality_span_scale) {
    return static_cast<int>(static_cast<float>(value) * static_cast<float>(quality_span_scale));
}

int dynamic_offset_for_radius(int radius_count, int min_radius, int offset, int radius_index, const std::string &mode) {
    if (offset <= 0) return 0;
    if (mode == "min-radius") {
        return static_cast<int>(static_cast<double>((radius_count / 2) * offset) /
                                static_cast<double>(std::max(1, min_radius + radius_index + 1)));
    }
    if (mode == "aex-row") {
        return static_cast<int>((float)((radius_count / 2) * offset) *
                                (1.0f / (float)std::max(1, radius_index + 1)));
    }
    return static_cast<int>(static_cast<double>((radius_count / 2) * offset) /
                            static_cast<double>(std::max(1, radius_index + 1)));
}

int positive_mod(int value, int divisor) {
    int wrapped = value % divisor;
    return wrapped < 0 ? wrapped + divisor : wrapped;
}

double combine_inner_alpha(const std::string &mode,
                           double combined_sum,
                           double outer_alpha,
                           double inner_alpha,
                           double source_alpha) {
    if (mode == "sum") return std::min(1.0, std::max(0.0, combined_sum));
    if (mode == "outer") return outer_alpha;
    if (mode == "inner") return inner_alpha;
    if (mode == "input") return source_alpha;
    return std::max(outer_alpha, inner_alpha);
}

bool polar_valid_sample(float x, float y, int width, int height, bool repeat_border, const std::string &mode) {
    if (mode == "aex-repeat" && repeat_border) {
        const int ix = static_cast<int>(x);
        const int iy = static_cast<int>(y);
        return -2 < ix && ix < width && -2 < iy && iy < height;
    }
    return x >= 0.0f && x <= static_cast<float>(width - 1) &&
           y >= 0.0f && y <= static_cast<float>(height - 1);
}

class CircularConvolver {
public:
    CircularConvolver(int value_count, const std::vector<float> &weights)
        : value_count_(value_count),
          repeated_count_(value_count * 3),
          fft_count_(next_power_of_two(repeated_count_ + static_cast<int>(weights.size()) - 1)),
          kernel_fft_(static_cast<size_t>(fft_count_)) {
        for (size_t i = 0; i < weights.size(); ++i) kernel_fft_[i] = Complex(weights[i], 0.0);
        fft(kernel_fft_, false);
    }

    void convolve(const std::vector<double> &values, std::vector<double> &out) const {
        std::vector<Complex> spectrum(static_cast<size_t>(fft_count_));
        for (int i = 0; i < repeated_count_; ++i) {
            spectrum[static_cast<size_t>(i)] = Complex(values[static_cast<size_t>(i % value_count_)], 0.0);
        }
        fft(spectrum, false);
        for (int i = 0; i < fft_count_; ++i) spectrum[static_cast<size_t>(i)] *= kernel_fft_[static_cast<size_t>(i)];
        fft(spectrum, true);
        out.resize(static_cast<size_t>(value_count_));
        for (int i = 0; i < value_count_; ++i) out[static_cast<size_t>(i)] = spectrum[static_cast<size_t>(value_count_ + i)].real();
    }

private:
    int value_count_ = 0;
    int repeated_count_ = 0;
    int fft_count_ = 0;
    std::vector<Complex> kernel_fft_;
};

Image render_olmradialblur_zoom(const Image &input, const RadialBlurParams &params) {
    if (params.blur_type != 1) throw std::runtime_error("C++ OLMRadialBlur CLI currently supports only Blur Type=1 (Zoom)");
    if (params.inner_strength != 0) throw std::runtime_error("C++ OLMRadialBlur CLI currently does not support Inner Blur");
    if (params.noise_variation != 0.0) throw std::runtime_error("C++ OLMRadialBlur CLI currently does not support Noise Variation");
    if (params.size_variation != 0.0 && !params.ignore_size_variation) {
        throw std::runtime_error("C++ OLMRadialBlur CLI currently does not support Size Variation; pass --ignore-size-variation");
    }

    const int w = input.width;
    const int h = input.height;
    FloatImage src;
    src.width = w;
    src.height = h;
    src.rgba.resize(static_cast<size_t>(w) * h * 4);
    if (input.bit_depth == 16) {
        for (size_t i = 0; i < input.rgba16.size(); ++i) src.rgba[i] = static_cast<float>(input.rgba16[i]) / 65535.0f;
    } else {
        for (size_t i = 0; i < input.rgba.size(); ++i) src.rgba[i] = static_cast<float>(input.rgba[i]) / 255.0f;
    }
    const double scale_x = static_cast<double>(w) / params.comp_width;
    const double scale_y = static_cast<double>(h) / params.comp_height;
    const double cx = params.center_x * scale_x;
    const double cy = params.center_y * scale_y;
    const double ratio = params.ratio;
    const double base_angle = params.angle_deg * M_PI / 180.0;
    const double quality = params.quality > 0.0 ? params.quality : 5.0;
    const double step_deg = 1.0 / quality;
    const double step_rad = step_deg * M_PI / 180.0;
    const int angular_count = static_cast<int>(360.0 / step_deg);

    const double min_dx = (0.0 <= cx && cx < w) ? 0.0 : std::abs(cx < 0.0 ? cx : cx - w);
    const double min_dy = (0.0 <= cy && cy < h) ? 0.0 : std::abs(cy < 0.0 ? cy : cy - h);
    const double max_dx = (0.0 <= cx && cx < w) ? std::max(cx, static_cast<double>(w) - cx) : (cx < 0.0 ? static_cast<double>(w) - cx : cx);
    const double max_dy = (0.0 <= cy && cy < h) ? std::max(cy, static_cast<double>(h) - cy) : (cy < 0.0 ? static_cast<double>(h) - cy : cy);
    const int min_r = std::max(0, static_cast<int>(std::sqrt(min_dx * min_dx + min_dy * min_dy) / ratio) - 2);
    const int max_r = static_cast<int>(std::sqrt(max_dx * max_dx + max_dy * max_dy)) + 2;
    const int radius_count = max_r - min_r + 1;
    const std::vector<PairedTrigFloat> trig_table = params.zoom_aex_trig_table_path.empty()
        ? std::vector<PairedTrigFloat>()
        : load_zoom_trig_table(params.zoom_aex_trig_table_path, angular_count, static_cast<float>(step_rad));

    FloatImage polar;
    polar.width = radius_count;
    polar.height = angular_count;
    polar.rgba.resize(static_cast<size_t>(angular_count) * radius_count * 4);
    std::vector<float> polar_valid(static_cast<size_t>(angular_count) * radius_count, 0.0f);
    const double cos_a = std::cos(base_angle);
    const double sin_a = std::sin(base_angle);
    const float ratio_f = static_cast<float>(ratio);
    const float cx_f = static_cast<float>(cx);
    const float cy_f = static_cast<float>(cy);
    const float base_angle_f = static_cast<float>(base_angle);
    const float cos_a_f = ::cosf(base_angle_f);
    const float sin_a_f = ::sinf(base_angle_f);
    const float step_rad_f = static_cast<float>(step_rad);
    for (int ai = 0; ai < angular_count; ++ai) {
            const double theta = static_cast<double>(ai) * step_rad;
            const double cos_t = std::cos(theta);
            const double sin_t = std::sin(theta);
            for (int ri = 0; ri < radius_count; ++ri) {
                const double r = static_cast<double>(min_r + ri);
                float sx = 0.0f;
                float sy = 0.0f;
                if (!trig_table.empty() || params.zoom_paired_trig_float || params.zoom_grid_mode == "aex-float") {
                    const float theta_f = static_cast<float>(static_cast<float>(ai) * step_rad_f);
                    const PairedTrigFloat trig = trig_table.empty() ? paired_trig_float(theta_f) : trig_table[static_cast<size_t>(ai)];
                    const float radius_f = static_cast<float>(min_r + ri);
                    const float sx0 = static_cast<float>(radius_f * trig.cos_value);
                    const float sy0 = static_cast<float>(static_cast<float>(radius_f * trig.sin_value) * ratio_f);
                    const float rotated_x = static_cast<float>(cos_a_f * sx0);
                    const float rotated_y = static_cast<float>(sin_a_f * sy0);
                    sx = static_cast<float>(static_cast<float>(rotated_x - rotated_y) + cx_f);
                    const float rotated_x_y = static_cast<float>(sin_a_f * sx0);
                    const float rotated_y_y = static_cast<float>(cos_a_f * sy0);
                    sy = static_cast<float>(static_cast<float>(rotated_x_y + rotated_y_y) + cy_f);
                } else {
                    const double sx0 = r * cos_t;
                    const double sy0 = r * sin_t * ratio;
                    sx = static_cast<float>(cx + cos_a * sx0 - sin_a * sy0);
                    sy = static_cast<float>(cy + sin_a * sx0 + cos_a * sy0);
                }
                const size_t dst = (static_cast<size_t>(ai) * radius_count + ri) * 4;
                float sampled[4];
                sample_rgba_aex_alpha(src, sx, sy, params.repeat_border, params.rgba_sampler_alpha_mode, sampled);
            for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sampled[c];
            polar_valid[static_cast<size_t>(ai) * radius_count + ri] =
                polar_valid_sample(sx, sy, w, h, params.repeat_border, params.polar_valid_mode) ? 1.0f : 0.0f;
        }
    }

    const std::vector<float> weights = zoom_gaussian_weights(zoom_effective_length(params));
    const bool use_fft_convolution = weights.size() > 512;
    const bool use_propagated_validity_alpha =
        params.outer_caller_collapse_mode == "propagated-validity-alpha";
    FloatImage blurred;
    blurred.width = radius_count;
    blurred.height = angular_count;
    blurred.rgba.assign(static_cast<size_t>(angular_count) * radius_count * 4, 0.0f);
    std::vector<float> outer_collapse_plane;
    if (use_propagated_validity_alpha) {
        outer_collapse_plane.assign(static_cast<size_t>(angular_count) * radius_count, 0.0f);
    }
    if (!use_fft_convolution) {
        for (int ai = 0; ai < angular_count; ++ai) {
            for (int ri = 0; ri < radius_count; ++ri) {
                double weighted_rgb[3] = {0.0, 0.0, 0.0};
                double weighted_alpha = 0.0;
                double accum_alpha = 0.0;
                double validity_sum = 0.0;
                const int limit = std::min<int>(static_cast<int>(weights.size()), ri + 1);
                for (int k = 0; k < limit; ++k) {
                    const size_t src_idx = (static_cast<size_t>(ai) * radius_count + (ri - k)) * 4;
                    const double alpha = polar.rgba[src_idx + 3];
                    const double weight = weights[static_cast<size_t>(k)];
                    for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * alpha * weight;
                    weighted_alpha += alpha * weight;
                    accum_alpha += alpha * weight;
                    validity_sum += polar_valid[static_cast<size_t>(ai) * radius_count + (ri - k)] * weight;
                }
                const size_t dst = (static_cast<size_t>(ai) * radius_count + ri) * 4;
                if (weighted_alpha > 1.0e-8) {
                    for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = static_cast<float>(weighted_rgb[c] / weighted_alpha);
                }
                blurred.rgba[dst + 3] = clamp_float(static_cast<float>(accum_alpha), 0.0f, 1.0f);
                if (use_propagated_validity_alpha) {
                    outer_collapse_plane[static_cast<size_t>(ai) * radius_count + ri] =
                        clamp_float(static_cast<float>(validity_sum), 0.0f, 1.0f);
                }
            }
        }
    } else {
        ForwardConvolver convolver(radius_count, weights);
        std::vector<double> values(static_cast<size_t>(radius_count));
        std::vector<double> alpha_conv;
        std::vector<double> rgb_conv[3];
        std::vector<double> validity_conv;
        for (int ai = 0; ai < angular_count; ++ai) {
            for (int ri = 0; ri < radius_count; ++ri) {
                const size_t src_idx = (static_cast<size_t>(ai) * radius_count + ri) * 4;
                values[static_cast<size_t>(ri)] = polar.rgba[src_idx + 3];
            }
            convolver.convolve(values, alpha_conv);
            if (use_propagated_validity_alpha) {
                for (int ri = 0; ri < radius_count; ++ri) {
                    values[static_cast<size_t>(ri)] = polar_valid[static_cast<size_t>(ai) * radius_count + ri];
                }
                convolver.convolve(values, validity_conv);
            }

            for (int c = 0; c < 3; ++c) {
                for (int ri = 0; ri < radius_count; ++ri) {
                    const size_t src_idx = (static_cast<size_t>(ai) * radius_count + ri) * 4;
                    const double alpha = polar.rgba[src_idx + 3];
                    values[static_cast<size_t>(ri)] = polar.rgba[src_idx + c] * alpha;
                }
                convolver.convolve(values, rgb_conv[c]);
            }

            for (int ri = 0; ri < radius_count; ++ri) {
                const size_t dst = (static_cast<size_t>(ai) * radius_count + ri) * 4;
                const double weighted_alpha = alpha_conv[static_cast<size_t>(ri)];
                if (weighted_alpha > 1.0e-8) {
                    for (int c = 0; c < 3; ++c) {
                        blurred.rgba[dst + c] = static_cast<float>(rgb_conv[c][static_cast<size_t>(ri)] / weighted_alpha);
                    }
                }
                blurred.rgba[dst + 3] = clamp_float(static_cast<float>(weighted_alpha), 0.0f, 1.0f);
                if (use_propagated_validity_alpha) {
                    outer_collapse_plane[static_cast<size_t>(ai) * radius_count + ri] =
                        clamp_float(static_cast<float>(validity_conv[static_cast<size_t>(ri)]), 0.0f, 1.0f);
                }
            }
        }
    }

    Image out;
    out.width = w;
    out.height = h;
    out.bit_depth = input.bit_depth;
    if (out.bit_depth == 16) out.rgba16.resize(static_cast<size_t>(w) * h * 4);
    else out.rgba.resize(static_cast<size_t>(w) * h * 4);
    const float max_val = out.bit_depth == 16 ? 65535.0f : 255.0f;
    WitnessDump witness;
    witness.enabled = !params.witness_dump_path.empty() && params.witness_x >= 0 && params.witness_y >= 0;
    witness.row_probe_half_span = params.witness_row_half_span;
    witness.rgba_sampler_alpha_mode = params.rgba_sampler_alpha_mode;
    witness.outer_caller_collapse_mode = params.outer_caller_collapse_mode;
    const double rgb_quantize_epsilon = use_fft_convolution ? 0.0 : 1.0e-4;
    const double alpha_quantize_epsilon = params.outer_alpha_quantize_mode == "truncate" ? 0.0 : 1.0e-4;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float radius_index = 0.0f;
            float angle_index = 0.0f;
            if (params.zoom_inverse_float) {
                // FUN_18000a850: preserve the SUBSS/MULSS/SUBSS/ADDSS/
                // DIVSS/MULSS/ADDSS/SQRTSS order before atan2f.
                const float y_delta = static_cast<float>(static_cast<float>(y) - cy_f);
                const float x_delta = static_cast<float>(static_cast<float>(x) - cx_f);
                const float cos_y = static_cast<float>(cos_a_f * y_delta);
                const float sin_x = static_cast<float>(sin_a_f * x_delta);
                const float sin_y = static_cast<float>(sin_a_f * y_delta);
                const float cos_x = static_cast<float>(cos_a_f * x_delta);
                const float radial_unscaled = static_cast<float>(cos_y - sin_x);
                const float angular = static_cast<float>(cos_x + sin_y);
                const float radial = static_cast<float>(radial_unscaled / ratio_f);
                const float angular_squared = static_cast<float>(angular * angular);
                const float radial_squared = static_cast<float>(radial * radial);
                const float radius = ::sqrtf(static_cast<float>(radial_squared + angular_squared));
                const float angle_float = ::atan2f(radial, angular);
                float normalized_angle = angle_float;
                if (normalized_angle < 0.0f) {
                    normalized_angle = static_cast<float>(static_cast<double>(normalized_angle) + M_PI * 2.0);
                }
                radius_index = static_cast<float>(radius - static_cast<float>(min_r));
                angle_index = static_cast<float>(normalized_angle / step_rad_f);
            } else {
                const double dx = static_cast<double>(x) - cx;
                const double dy = static_cast<double>(y) - cy;
                const double ex = cos_a * dx + sin_a * dy;
                const double ey = (cos_a * dy - sin_a * dx) / ratio;
                const double radius = std::sqrt(ex * ex + ey * ey);
                double angle = std::atan2(ey, ex);
                if (angle < 0.0) angle += M_PI * 2.0;
                radius_index = static_cast<float>(radius - min_r);
                angle_index = static_cast<float>(angle / step_rad);
            }

            int xi_raw = static_cast<int>(std::floor(radius_index));
            int yi = static_cast<int>(std::floor(angle_index));
            float fx = radius_index - static_cast<float>(xi_raw);
            float fy = angle_index - static_cast<float>(yi);
            int xi = std::max(0, std::min(xi_raw, radius_count - 1));
            int x1 = std::max(0, std::min(xi_raw + 1, radius_count - 1));
            int y0 = ((yi % angular_count) + angular_count) % angular_count;
            int y1 = (y0 + 1) % angular_count;
            auto collapsed_valid = [&](int px, int py) -> float {
                return polar_valid[static_cast<size_t>(py) * radius_count + px];
            };
            auto sample = [&](int px, int py, int c) -> float {
                const size_t cell = static_cast<size_t>(py) * radius_count + px;
                if (params.outer_caller_collapse_mode == "binary-validity") {
                    if (c == 3) return collapsed_valid(px, py);
                    return collapsed_valid(px, py) > 0.0f ? blurred.rgba[cell * 4 + c] : 0.0f;
                }
                if (params.outer_caller_collapse_mode == "zero-rgb-on-invalid") {
                    if (c == 3) return blurred.rgba[cell * 4 + c];
                    return collapsed_valid(px, py) > 0.0f ? blurred.rgba[cell * 4 + c] : 0.0f;
                }
                if (params.outer_caller_collapse_mode == "propagated-validity-alpha") {
                    if (c == 3) return outer_collapse_plane[cell];
                    return outer_collapse_plane[cell] > 0.0f ? blurred.rgba[cell * 4 + c] : 0.0f;
                }
                if (params.outer_caller_collapse_mode == "polar-alpha") {
                    if (c == 3) return polar.rgba[cell * 4 + 3];
                    return blurred.rgba[cell * 4 + c];
                }
                float value = blurred.rgba[cell * 4 + c];
                if (c < 3 && params.final_polar_rgb_mode == "clamp-nonnegative") value = std::max(0.0f, value);
                return value;
            };
            const double w00 = (1.0 - fx) * (1.0 - fy);
            const double w10 = fx * (1.0 - fy);
            const double w01 = (1.0 - fx) * fy;
            const double w11 = fx * fy;
            const double a00 = sample(xi, y0, 3) * w00;
            const double a10 = sample(x1, y0, 3) * w10;
            const double a01 = sample(xi, y1, 3) * w01;
            const double a11 = sample(x1, y1, 3) * w11;
            const double alpha = a00 + a10 + a01 + a11;
            const double validity_alpha = collapsed_valid(xi, y0) * w00 + collapsed_valid(x1, y0) * w10 +
                                          collapsed_valid(xi, y1) * w01 + collapsed_valid(x1, y1) * w11;
            const size_t dst = (static_cast<size_t>(y) * w + x) * 4;
            const bool capture_row_probe = witness.enabled && y == params.witness_y &&
                                           std::abs(x - params.witness_x) <= witness.row_probe_half_span;
            WitnessDump::PlaneProbePoint row_probe_point;
            if (capture_row_probe) {
                row_probe_point.x = x;
                row_probe_point.y = y;
                row_probe_point.radius_index = radius_index;
                row_probe_point.angle_index = angle_index;
                row_probe_point.alpha = alpha;
                row_probe_point.validity_alpha = validity_alpha;
                row_probe_point.validity_alpha_u8 = static_cast<int>(
                    clamp_float(static_cast<float>(std::floor(validity_alpha * 255.0 + alpha_quantize_epsilon)), 0.0f, 255.0f));
                row_probe_point.cell_valid[0] = collapsed_valid(xi, y0);
                row_probe_point.cell_valid[1] = collapsed_valid(x1, y0);
                row_probe_point.cell_valid[2] = collapsed_valid(xi, y1);
                row_probe_point.cell_valid[3] = collapsed_valid(x1, y1);
                row_probe_point.cell_alpha[0] = sample(xi, y0, 3);
                row_probe_point.cell_alpha[1] = sample(x1, y0, 3);
                row_probe_point.cell_alpha[2] = sample(xi, y1, 3);
                row_probe_point.cell_alpha[3] = sample(x1, y1, 3);
            }
            if (witness.enabled && x == params.witness_x && y == params.witness_y) {
                witness.captured = true;
                witness.path_kind = "zoom";
                witness.x = x;
                witness.y = y;
                witness.radius_index = radius_index;
                witness.angle_index = angle_index;
                witness.sample_x0 = xi;
                witness.sample_x1 = x1;
                witness.sample_y0 = y0;
                witness.sample_y1 = y1;
                witness.fx = fx;
                witness.fy = fy;
                witness.w00 = w00;
                witness.w10 = w10;
                witness.w01 = w01;
                witness.w11 = w11;
                witness.a00 = a00;
                witness.a10 = a10;
                witness.a01 = a01;
                witness.a11 = a11;
                witness.alpha = alpha;
                witness.validity_alpha = validity_alpha;
                for (int c = 0; c < 4; ++c) {
                    witness.cell00_rgba[c] = sample(xi, y0, c);
                    witness.cell10_rgba[c] = sample(x1, y0, c);
                    witness.cell01_rgba[c] = sample(xi, y1, c);
                    witness.cell11_rgba[c] = sample(x1, y1, c);
                }
                witness.cell00_valid = collapsed_valid(xi, y0);
                witness.cell10_valid = collapsed_valid(x1, y0);
                witness.cell01_valid = collapsed_valid(xi, y1);
                witness.cell11_valid = collapsed_valid(x1, y1);
                witness.neighborhood_origin_x = xi > 0 ? xi - 1 : xi;
                witness.neighborhood_origin_y = y0 > 0 ? y0 - 1 : y0;
                int ni = 0;
                for (int oy = 0; oy < 3; ++oy) {
                    for (int ox = 0; ox < 3; ++ox, ++ni) {
                        const int px = std::max(0, std::min(radius_count - 1, witness.neighborhood_origin_x + ox));
                        const int py = positive_mod(witness.neighborhood_origin_y + oy, angular_count);
                        for (int c = 0; c < 4; ++c) witness.neighborhood_rgba[ni][c] = sample(px, py, c);
                        witness.neighborhood_valid[ni] = collapsed_valid(px, py);
                    }
                }
            }
            for (int c = 0; c < 3; ++c) {
                const double rgb_numerator = sample(xi, y0, c) * a00 + sample(x1, y0, c) * a10 +
                                             sample(xi, y1, c) * a01 + sample(x1, y1, c) * a11;
                double rgb = 0.0;
                if (alpha > 1.0e-8) {
                    rgb = rgb_numerator / alpha;
                }
                rgb *= params.brightness_gain;
                const int q = static_cast<int>(clamp_float(static_cast<float>(std::floor(rgb * max_val + rgb_quantize_epsilon)), 0.0f, max_val));
                if (out.bit_depth == 16) out.rgba16[dst + c] = static_cast<uint16_t>(q);
                else out.rgba[dst + c] = static_cast<unsigned char>(q);
                if (witness.enabled && x == params.witness_x && y == params.witness_y) {
                    witness.sample_rgb_numerator[c] = rgb_numerator;
                    witness.sample_rgba[c] = static_cast<float>(rgb);
                    witness.sample_u8[c] = out.bit_depth == 16 ? q >> 8 : q;
                }
                if (capture_row_probe) {
                    row_probe_point.sample_rgba[c] = static_cast<float>(rgb);
                    row_probe_point.sample_u8[c] = out.bit_depth == 16 ? q >> 8 : q;
                }
            }
            const int aq = static_cast<int>(clamp_float(static_cast<float>(std::floor(alpha * max_val + alpha_quantize_epsilon)), 0.0f, max_val));
            if (out.bit_depth == 16) out.rgba16[dst + 3] = static_cast<uint16_t>(aq);
            else out.rgba[dst + 3] = static_cast<unsigned char>(aq);
            if (witness.enabled && x == params.witness_x && y == params.witness_y) {
                witness.sample_rgba[3] = static_cast<float>(alpha);
                witness.sample_u8[3] = out.bit_depth == 16 ? aq >> 8 : aq;
            }
            if (capture_row_probe) {
                row_probe_point.sample_rgba[3] = static_cast<float>(alpha);
                row_probe_point.sample_u8[3] = aq;
                row_probe_point.alpha_u8 = aq;
                witness.row_probe.push_back(row_probe_point);
            }
        }
    }
    maybe_write_witness_dump(params, witness);
    return out;
}

Image render_olmradialblur_rotation_float(const FloatImage &src, const RadialBlurParams &params,
                                          RotationTypedPlanes *typed_planes = nullptr,
                                          int output_bit_depth = 8,
                                          const RotationTypedPolarInput *typed_polar = nullptr) {
    if (params.blur_type != 2) throw std::runtime_error("C++ OLMRadialBlur rotation supports only Blur Type=2");
    if (params.noise_variation != 0.0) throw std::runtime_error("C++ OLMRadialBlur rotation currently does not support Noise Variation");
    const bool has_inner_input = params.inner_strength != 0 || params.inner_offset != 0;
    const bool force_inner_source_scatter_prepass = has_inner_input;

    const int w = src.width;
    const int h = src.height;
    const double scale_x = static_cast<double>(w) / params.comp_width;
    const double scale_y = static_cast<double>(h) / params.comp_height;
    const double cx = params.center_x * scale_x;
    const double cy = params.center_y * scale_y;
    const double ratio = params.ratio;
    const double base_angle = params.angle_deg * M_PI / 180.0;
    const double quality = params.quality > 0.0 ? params.quality : 5.0;
    const double quality_span_scale = params.aex_quality_span_scale ? quality / 5.0 : 1.0;
    const double step_deg = 1.0 / quality;
    const double step_rad = step_deg * M_PI / 180.0;
    int angular_count = static_cast<int>(360.0 / step_deg);

    const double left = std::max(0.0, -cx);
    const double right = std::max({0.0, cx - static_cast<double>(w), cx <= static_cast<double>(w) / 2.0 ? static_cast<double>(w) - cx : cx});
    const double top = std::max(0.0, -cy);
    const double bottom = std::max({0.0, cy - static_cast<double>(h), cy <= static_cast<double>(h) / 2.0 ? static_cast<double>(h) - cy : cy});
    int min_r = std::max(0, static_cast<int>(std::sqrt(left * left + top * top) / ratio) - 2);
    const int max_r = static_cast<int>(std::sqrt(std::max(left, right) * std::max(left, right) + std::max(top, bottom) * std::max(top, bottom))) + 2;
    int radius_count = max_r - min_r + 1;

    if (typed_polar) {
        if (typed_polar->width <= 0 || typed_polar->height <= 0 || typed_polar->row_stride <= 0 ||
            static_cast<size_t>(typed_polar->row_stride) != static_cast<size_t>(typed_polar->width) * 4) {
            throw std::runtime_error("typed polar input must have positive width/height and row_stride=width*4");
        }
        const size_t cell_count = static_cast<size_t>(typed_polar->width) * typed_polar->height;
        if (typed_polar->rgba.size() != cell_count * 4 || typed_polar->polar_valid.size() != cell_count) {
            throw std::runtime_error("typed polar input has non-exact RGBA or validity size");
        }
        angular_count = typed_polar->width;
        radius_count = typed_polar->height;
        min_r = 0;
    }

    FloatImage polar;
    polar.width = angular_count;
    polar.height = radius_count;
    polar.rgba.resize(static_cast<size_t>(radius_count) * angular_count * 4);
    std::vector<uint8_t> polar_valid(static_cast<size_t>(radius_count) * angular_count, 0);
    const bool use_size_variation_planes = params.size_variation != 0.0 && !params.ignore_size_variation;
    const std::vector<float> source_size_factor = use_size_variation_planes
        ? build_size_factor_plane(src, params.size_variation)
        : std::vector<float>{};
    std::vector<float> polar_size_factor(static_cast<size_t>(radius_count) * angular_count, 1.0f);
    std::vector<float> polar_span_gate(static_cast<size_t>(radius_count) * angular_count, 1.0f);
    const double cos_a = std::cos(base_angle);
    const double sin_a = std::sin(base_angle);
    const float cos_af = static_cast<float>(cos_a);
    const float sin_af = static_cast<float>(sin_a);
    const float cxf = static_cast<float>(cx);
    const float cyf = static_cast<float>(cy);
    const float ratiof = static_cast<float>(ratio);
    const float step_radf = static_cast<float>(step_rad);
    const double angle_offset_steps = params.rotation_grid_angle_offset_steps;
    const double radius_offset = params.rotation_grid_radius_offset;
    for (int ri = 0; ri < radius_count; ++ri) {
        const double r = static_cast<double>(min_r + ri) + radius_offset;
        for (int ai = 0; ai < angular_count; ++ai) {
            float sx = 0.0f;
            float sy = 0.0f;
            if (params.rotation_grid_mode == "aex-float") {
                const float rf = static_cast<float>(static_cast<double>(min_r + ri) + radius_offset);
                const float theta = static_cast<float>(static_cast<double>(ai) + angle_offset_steps) * step_radf;
                const float sx0 = std::cos(theta) * rf;
                const float sy0 = std::sin(theta) * rf * ratiof;
                sx = cxf + cos_af * sx0 - sin_af * sy0;
                sy = cyf + sin_af * sx0 + cos_af * sy0;
            } else {
                const double theta = (static_cast<double>(ai) + angle_offset_steps) * step_rad;
                const double sx0 = std::cos(theta) * r;
                const double sy0 = std::sin(theta) * r * ratio;
                sx = static_cast<float>(cx + cos_a * sx0 - sin_a * sy0);
                sy = static_cast<float>(cy + sin_a * sx0 + cos_a * sy0);
            }
            const size_t dst = (static_cast<size_t>(ri) * angular_count + ai) * 4;
            if (typed_polar) continue;
            const bool use_aex_alpha_sample =
                params.polar_sample_mode == "aex-alpha" ||
                params.repeat_border ||
                (params.polar_sample_mode == "conditional-inner" &&
                 params.outer_edge_fade == 0 &&
                 params.inner_edge_fade == 0 &&
                 params.inner_offset_mode != 3);
            if (use_aex_alpha_sample) {
                float sampled[4];
                sample_rgba_aex_alpha(src, sx, sy, params.repeat_border, params.rgba_sampler_alpha_mode, sampled);
                for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sampled[c];
            } else {
                for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sample_channel(src, sx, sy, c, params.repeat_border);
            }
            polar_valid[static_cast<size_t>(ri) * angular_count + ai] =
                polar_valid_sample(sx, sy, w, h, params.repeat_border, params.polar_valid_mode);
            if (use_size_variation_planes) {
                const size_t cell = static_cast<size_t>(ri) * angular_count + ai;
                const float size_factor = sample_scalar_plane(source_size_factor, w, h, sx, sy, params.repeat_border);
                polar_size_factor[cell] = size_factor;
                polar_span_gate[cell] = size_factor;
            }
        }
    }

    if (typed_polar) {
        polar.rgba = typed_polar->rgba;
        polar_valid = typed_polar->polar_valid;
    }

    const int outer_strength_for_span = scale_aex_span_param(params.outer_strength, quality_span_scale);
    const int inner_strength_for_span = scale_aex_span_param(params.inner_strength, quality_span_scale);
    const int outer_offset_for_span = scale_aex_span_param(params.outer_offset, quality_span_scale);
    const int inner_offset_for_span = scale_aex_span_param(params.inner_offset, quality_span_scale);
    const int outer_edge_fade_for_span = scale_aex_span_param(params.outer_edge_fade, quality_span_scale);
    const int inner_edge_fade_for_span = scale_aex_span_param(params.inner_edge_fade, quality_span_scale);
    const bool variable_offset = outer_offset_for_span != 0 || inner_offset_for_span != 0;
    const int outer_length = rotation_effective_length(outer_strength_for_span, params.outer_offset_mode, 0);
    const int inner_length = rotation_effective_length(inner_strength_for_span, params.inner_offset_mode, 0);
    const bool has_inner = has_inner_input;
    const std::vector<float> weights = variable_offset ? std::vector<float>{} : rotation_gaussian_weights(outer_length);
    const std::vector<float> inner_weights = variable_offset ? std::vector<float>{} : rotation_gaussian_weights(inner_length);
    FloatImage blurred;
    blurred.width = angular_count;
    blurred.height = radius_count;
    blurred.rgba.assign(static_cast<size_t>(radius_count) * angular_count * 4, 0.0f);

    auto convolve_row = [&](CircularConvolver &convolver,
                            const std::vector<double> &values,
                            std::vector<double> &out,
                            bool reverse) {
        if (!reverse) {
            convolver.convolve(values, out);
            return;
        }
        std::vector<double> reversed(static_cast<size_t>(angular_count));
        for (int ai = 0; ai < angular_count; ++ai) {
            reversed[static_cast<size_t>(ai)] = values[static_cast<size_t>((angular_count - ai) % angular_count)];
        }
        convolver.convolve(reversed, out);
        std::vector<double> restored(static_cast<size_t>(angular_count));
        for (int ai = 0; ai < angular_count; ++ai) {
            restored[static_cast<size_t>(ai)] = out[static_cast<size_t>((angular_count - ai) % angular_count)];
        }
        out.swap(restored);
    };

    auto direct_accumulate_row = [&](int ri,
                                     const std::vector<float> &row_weights,
                                     bool reverse,
                                     std::vector<double> &rgb0,
                                     std::vector<double> &rgb1,
                                     std::vector<double> &rgb2,
                                     std::vector<double> &alpha_sum,
                                     std::vector<double> &alpha_accum) {
        rgb0.assign(static_cast<size_t>(angular_count), 0.0);
        rgb1.assign(static_cast<size_t>(angular_count), 0.0);
        rgb2.assign(static_cast<size_t>(angular_count), 0.0);
        alpha_sum.assign(static_cast<size_t>(angular_count), 0.0);
        alpha_accum.assign(static_cast<size_t>(angular_count), 0.0);
        for (int ai = 0; ai < angular_count; ++ai) {
            for (size_t k = 0; k < row_weights.size(); ++k) {
                const int delta = static_cast<int>(k) % angular_count;
                const int src_ai = reverse ? (ai + delta) % angular_count
                                           : (ai - delta + angular_count) % angular_count;
                const size_t src_idx = (static_cast<size_t>(ri) * angular_count + src_ai) * 4;
                const double alpha = polar.rgba[src_idx + 3];
                const double contribution = alpha * row_weights[k];
                rgb0[static_cast<size_t>(ai)] += polar.rgba[src_idx + 0] * contribution;
                rgb1[static_cast<size_t>(ai)] += polar.rgba[src_idx + 1] * contribution;
                rgb2[static_cast<size_t>(ai)] += polar.rgba[src_idx + 2] * contribution;
                alpha_sum[static_cast<size_t>(ai)] += contribution;
                alpha_accum[static_cast<size_t>(ai)] = std::max(alpha_accum[static_cast<size_t>(ai)], contribution);
            }
        }
    };

    auto fft_accumulate_row = [&](int ri,
                                  const std::vector<float> &row_weights,
                                  bool reverse,
                                  std::map<int, CircularConvolver> &convolver_cache,
                                  std::vector<double> &values,
                                  std::vector<double> &rgb0,
                                  std::vector<double> &rgb1,
                                  std::vector<double> &rgb2,
                                  std::vector<double> &alpha_sum,
                                  std::vector<double> &alpha_accum) {
        const int row_length = static_cast<int>(row_weights.size());
        auto convolver_it = convolver_cache.find(row_length);
        if (convolver_it == convolver_cache.end()) {
            convolver_it = convolver_cache.emplace(row_length, CircularConvolver(angular_count, row_weights)).first;
        }
        CircularConvolver &convolver = convolver_it->second;

        for (int ai = 0; ai < angular_count; ++ai) {
            const size_t src_idx = (static_cast<size_t>(ri) * angular_count + ai) * 4;
            values[static_cast<size_t>(ai)] = polar.rgba[src_idx + 3];
        }
        convolve_row(convolver, values, alpha_sum, reverse);

        for (int c = 0; c < 3; ++c) {
            for (int ai = 0; ai < angular_count; ++ai) {
                const size_t src_idx = (static_cast<size_t>(ri) * angular_count + ai) * 4;
                const double alpha = polar.rgba[src_idx + 3];
                values[static_cast<size_t>(ai)] = polar.rgba[src_idx + c] * alpha;
            }
            if (c == 0) convolve_row(convolver, values, rgb0, reverse);
            else if (c == 1) convolve_row(convolver, values, rgb1, reverse);
            else convolve_row(convolver, values, rgb2, reverse);
        }

        alpha_accum.resize(static_cast<size_t>(angular_count));
        for (int ai = 0; ai < angular_count; ++ai) {
            const size_t src_idx = (static_cast<size_t>(ri) * angular_count + ai) * 4;
            alpha_accum[static_cast<size_t>(ai)] = polar.rgba[src_idx + 3];
        }
    };

    auto accumulate_row = [&](int ri,
                              const std::vector<float> &row_weights,
                              bool reverse,
                              std::map<int, CircularConvolver> &convolver_cache,
                              std::vector<double> &values,
                              std::vector<double> &rgb0,
                              std::vector<double> &rgb1,
                              std::vector<double> &rgb2,
                              std::vector<double> &alpha_sum,
                              std::vector<double> &alpha_accum) {
        if (row_weights.size() < 64) {
            direct_accumulate_row(ri, row_weights, reverse, rgb0, rgb1, rgb2, alpha_sum, alpha_accum);
        } else {
            fft_accumulate_row(ri, row_weights, reverse, convolver_cache, values, rgb0, rgb1, rgb2, alpha_sum, alpha_accum);
        }
    };

    const bool use_source_scatter_prepass =
        params.outer_source_scatter_prepass ||
        ((params.inner_source_scatter_prepass || force_inner_source_scatter_prepass) && has_inner);
    std::vector<float> prepass_alpha_export;

    if (use_source_scatter_prepass) {
        InnerScatterStats scatter_stats;
        FloatImage accum;
        accum.width = angular_count;
        accum.height = radius_count;
        accum.rgba.assign(static_cast<size_t>(radius_count) * angular_count * 4, 0.0f);
        std::vector<float> max_alpha(static_cast<size_t>(radius_count) * angular_count, 0.0f);
        std::vector<float> source_alpha(static_cast<size_t>(radius_count) * angular_count, 0.0f);
        std::vector<float> source_scale(static_cast<size_t>(radius_count) * angular_count, 1.0f);
        FloatImage source_rgba = polar;
        std::map<int, std::vector<float>> weight_cache;
        const bool seed_source =
            params.inner_scatter_seed_mode == "source" ||
            (params.inner_scatter_seed_mode == "edgefade-none" &&
             params.outer_edge_fade == 0 && params.inner_edge_fade == 0);

        for (int ri = 0; ri < radius_count; ++ri) {
            for (int ai = 0; ai < angular_count; ++ai) {
                const size_t cell = static_cast<size_t>(ri) * angular_count + ai;
                const size_t dst = cell * 4;
                const float alpha = polar.rgba[dst + 3];
                if (alpha <= 0.0f) continue;
                if (params.inner_scatter_rgb_mode == "prepass-premul") {
                    for (int c = 0; c < 3; ++c) source_rgba.rgba[dst + c] = polar.rgba[dst + c] * alpha;
                    source_rgba.rgba[dst + 3] = alpha;
                }
                if (seed_source) {
                    for (int c = 0; c < 3; ++c) accum.rgba[dst + c] = polar.rgba[dst + c] * alpha;
                    accum.rgba[dst + 3] = alpha;
                    max_alpha[cell] = alpha;
                }
                source_alpha[cell] = alpha;
                if (params.inner_source_scale_mode == "alpha") {
                    source_scale[cell] = alpha;
                } else if (params.inner_source_scale_mode == "inv-alpha") {
                    source_scale[cell] = alpha > 1.0e-8f ? 1.0f / alpha : 0.0f;
                } else {
                    source_scale[cell] = 1.0f;
                }
            }
        }

        if (params.inner_prepass_mode == "tail-gather") {
            std::vector<float> prepass_alpha(static_cast<size_t>(radius_count) * angular_count, 0.0f);
            for (int ri = 0; ri < radius_count; ++ri) {
                const int outer_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, outer_offset_for_span, ri, params.dynamic_offset_mode);
                const int inner_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, inner_offset_for_span, ri, params.dynamic_offset_mode);
                int row_outer_span = rotation_scatter_span(outer_strength_for_span, params.outer_offset_mode, outer_dynamic_offset);
                int row_inner_span = rotation_scatter_span(inner_strength_for_span, params.inner_offset_mode, inner_dynamic_offset);
                if (params.inner_prepass_span_mode == "offset") {
                    row_outer_span = std::max(0, std::min(outer_dynamic_offset, 3000));
                    row_inner_span = std::max(0, std::min(inner_dynamic_offset, 3000));
                } else if (params.inner_prepass_span_mode == "edge-fade") {
                    row_outer_span = std::max(0, std::min(outer_edge_fade_for_span, 3000));
                    row_inner_span = std::max(0, std::min(inner_edge_fade_for_span, 3000));
                }
                const int outer_table_span = row_outer_span;
                const int inner_table_span = row_inner_span;
                for (int ai = 0; ai < angular_count; ++ai) {
                    const size_t cell = static_cast<size_t>(ri) * angular_count + ai;
                    const float base_alpha = polar.rgba[cell * 4 + 3];
                    float base_factor = use_size_variation_planes ? polar_size_factor[cell] : base_alpha;
                    if (!use_size_variation_planes && params.inner_prepass_factor_mode == "one") {
                        base_factor = 1.0f;
                    } else if (!use_size_variation_planes && params.inner_prepass_factor_mode == "valid") {
                        base_factor = polar_valid[cell] ? 1.0f : 0.0f;
                    }
                    if (!polar_valid[cell] || base_alpha <= 0.0f || base_factor <= 0.0f) continue;
                    int effective_outer_span = row_outer_span;
                    int effective_inner_span = row_inner_span;
                    if (params.inner_prepass_weight_mode == "aex-alpha") {
                        effective_outer_span = std::max(0, std::min(static_cast<int>(static_cast<float>(row_outer_span) * base_factor), 3000));
                        effective_inner_span = std::max(0, std::min(static_cast<int>(static_cast<float>(row_inner_span) * base_factor), 3000));
                    }

                    float weighted_alpha = base_alpha;
                    float weight_sum = 1.0f;
                    for (int offset = 1; offset < effective_outer_span; ++offset) {
                        const int src_ai = positive_mod(ai - offset, angular_count);
                        const size_t src_cell = static_cast<size_t>(ri) * angular_count + src_ai;
                        const float weight = params.inner_prepass_weight_mode == "aex-alpha"
                            ? rotation_gaussian_weight_at_scaled(outer_table_span, offset, base_factor)
                            : rotation_gaussian_weight_at(row_outer_span, offset);
                        weighted_alpha += polar.rgba[src_cell * 4 + 3] * weight;
                        weight_sum += weight;
                    }
                    for (int offset = 1; offset < effective_inner_span; ++offset) {
                        const int src_ai = positive_mod(ai + offset, angular_count);
                        const size_t src_cell = static_cast<size_t>(ri) * angular_count + src_ai;
                        const float weight = params.inner_prepass_weight_mode == "aex-alpha"
                            ? rotation_gaussian_weight_at_scaled(inner_table_span, offset, base_factor)
                            : rotation_gaussian_weight_at(row_inner_span, offset);
                        weighted_alpha += polar.rgba[src_cell * 4 + 3] * weight;
                        weight_sum += weight;
                    }
                    prepass_alpha[cell] = weight_sum > 1.0e-8f ? weighted_alpha / weight_sum : 0.0f;
                }
            }

            for (int ri = 0; ri < radius_count; ++ri) {
                for (int ai = 0; ai < angular_count; ++ai) {
                    const size_t cell = static_cast<size_t>(ri) * angular_count + ai;
                    const size_t dst = cell * 4;
                    const float alpha = prepass_alpha[cell];
                    if (params.inner_prepass_overwrite_seed) {
                        for (int c = 0; c < 4; ++c) accum.rgba[dst + c] = 0.0f;
                        max_alpha[cell] = 0.0f;
                    }
                    if (alpha <= 0.0f) continue;
                    source_alpha[cell] = alpha;
                    source_scale[cell] = 1.0f;
                    if (params.inner_prepass_overwrite_seed ||
                        (seed_source &&
                         params.inner_seed_alpha_mode == "prepass")) {
                        for (int c = 0; c < 3; ++c) accum.rgba[dst + c] = polar.rgba[dst + c] * alpha;
                        accum.rgba[dst + 3] = alpha;
                        max_alpha[cell] = alpha;
                    }
                    if (params.inner_scatter_rgb_mode == "prepass-premul") {
                        for (int c = 0; c < 3; ++c) source_rgba.rgba[dst + c] = polar.rgba[dst + c] * alpha;
                    } else {
                        for (int c = 0; c < 3; ++c) source_rgba.rgba[dst + c] = polar.rgba[dst + c];
                    }
                    source_rgba.rgba[dst + 3] = alpha;
                }
            }
            prepass_alpha_export = prepass_alpha;
        }

        auto weights_for_span = [&](int span) -> const std::vector<float> & {
            auto it = weight_cache.find(span);
            if (it == weight_cache.end()) {
                it = weight_cache.emplace(span, rotation_gaussian_weights(span)).first;
            }
            return it->second;
        };

        auto scatter_one = [&](int ri, int ai, int span, bool inner) {
            if (inner) ++scatter_stats.inner_calls;
            else ++scatter_stats.outer_calls;
            if (inner) ++scatter_stats.inner_caller_span_hist[span];
            else ++scatter_stats.outer_caller_span_hist[span];
            if (inner && params.inner_scatter_span_minus_one) span -= 1;
            if (span <= 1) return;
            const size_t src_cell = static_cast<size_t>(ri) * angular_count + ai;
            if (!polar_valid[src_cell] || source_alpha[src_cell] == 0.0f || source_scale[src_cell] == 0.0f) {
                if (inner) ++scatter_stats.inner_source_skips;
                return;
            }
            float param10 = 1.0f;
            if (params.inner_scatter_param10_plane == "polar-alpha") {
                param10 = polar.rgba[src_cell * 4 + 3];
            } else if (params.inner_scatter_param10_plane == "prepass-alpha") {
                param10 = source_alpha[src_cell];
            } else if (params.inner_scatter_param10_plane == "factor") {
                param10 = polar_valid[src_cell] ? 1.0f : 0.0f;
            } else if (use_size_variation_planes) {
                param10 = polar_span_gate[src_cell];
            } else if (params.inner_scatter_span_scale_mode == "source-alpha") {
                param10 = source_alpha[src_cell];
            } else if (params.inner_scatter_span_scale_mode == "input-alpha") {
                param10 = polar.rgba[src_cell * 4 + 3];
            }
            int effective_span = static_cast<int>(static_cast<float>(span) * param10);
            effective_span = std::max(0, std::min(effective_span, 3000));
            if (effective_span <= 1) {
                if (inner) ++scatter_stats.inner_effective_span_le1;
                return;
            }
            const int table_span = inner && params.inner_scatter_table_span_minus_one
                ? std::max(1, effective_span - 1)
                : effective_span;
            const int loop_limit = inner && params.inner_scatter_loop_minus_one
                ? std::max(1, effective_span - 1)
                : effective_span;
            if (inner) {
                scatter_stats.inner_total_effective_span += effective_span;
                scatter_stats.inner_total_loop_limit += loop_limit;
                ++scatter_stats.inner_effective_span_hist[effective_span];
                ++scatter_stats.inner_loop_limit_hist[loop_limit];
            }
            const std::vector<float> &row_weights = weights_for_span(effective_span);
            const size_t src_idx = src_cell * 4;
            for (int offset = 1; offset < loop_limit && offset < static_cast<int>(row_weights.size()); ++offset) {
                int dst_ri = ri;
                int dst_ai = 0;
                if (inner) {
                    const int raw_ai = ai - offset;
                    if (params.inner_wrap_mode == "aex-next-row" && raw_ai < 0) {
                        ++scatter_stats.inner_underflow_wraps;
                        dst_ri = ri + ((-raw_ai - 1) / angular_count) + 1;
                        dst_ai = angular_count - 1 - ((-raw_ai - 1) % angular_count);
                    } else {
                        dst_ai = positive_mod(raw_ai, angular_count);
                    }
                } else {
                    dst_ai = positive_mod(ai + offset, angular_count);
                }
                if (dst_ri < 0 || dst_ri >= radius_count) {
                    if (inner) ++scatter_stats.inner_oob_radius_skips;
                    continue;
                }
                const size_t dst_cell = static_cast<size_t>(dst_ri) * angular_count + dst_ai;
                const size_t dst = dst_cell * 4;
                const float weight = inner && params.inner_scatter_table_span_minus_one
                    ? rotation_gaussian_reindexed_weight(table_span, offset)
                    : row_weights[static_cast<size_t>(offset)];
                const float contribution = source_alpha[src_cell] * source_scale[src_cell] * weight;
                if (contribution <= 0.0f) {
                    if (inner) ++scatter_stats.inner_zero_contribution_skips;
                    continue;
                }
                for (int c = 0; c < 3; ++c) accum.rgba[dst + c] += source_rgba.rgba[src_idx + c] * contribution;
                accum.rgba[dst + 3] += contribution;
                max_alpha[dst_cell] = std::max(max_alpha[dst_cell], contribution);
                if (inner) ++scatter_stats.inner_writes;
            }
        };

        for (int ri = 0; ri < radius_count; ++ri) {
            const int outer_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, outer_offset_for_span, ri, params.dynamic_offset_mode);
            const int inner_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, inner_offset_for_span, ri, params.dynamic_offset_mode);
            const int row_outer_span = rotation_scatter_span(outer_strength_for_span, params.outer_offset_mode, outer_dynamic_offset);
            const int row_inner_span = rotation_scatter_span(inner_strength_for_span, params.inner_offset_mode, inner_dynamic_offset);
            for (int ai = 0; ai < angular_count; ++ai) {
                scatter_one(ri, ai, row_outer_span, false);
                scatter_one(ri, ai, row_inner_span, true);
            }
        }

        for (int ri = 0; ri < radius_count; ++ri) {
            for (int ai = 0; ai < angular_count; ++ai) {
                const size_t cell = static_cast<size_t>(ri) * angular_count + ai;
                const size_t dst = cell * 4;
                const float denom = params.inner_rgb_denominator_mode == "max"
                    ? max_alpha[cell]
                    : accum.rgba[dst + 3];
                if (denom > 1.0e-8f) {
                    for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = accum.rgba[dst + c] / denom;
                }
                if (params.inner_final_alpha_mode == "denom") {
                    blurred.rgba[dst + 3] = accum.rgba[dst + 3];
                } else if (params.inner_final_alpha_mode == "source") {
                    blurred.rgba[dst + 3] = source_alpha[cell];
                } else {
                    blurred.rgba[dst + 3] = max_alpha[cell];
                }
            }
        }
        if (typed_planes) {
            typed_planes->accum = accum;
            typed_planes->prepass_alpha = prepass_alpha_export;
            typed_planes->scatter_alpha = max_alpha;
            typed_planes->source_alpha = source_alpha;
        }
        write_inner_scatter_stats(params.inner_scatter_stats_path, scatter_stats);
    } else if (variable_offset) {
        std::map<int, std::vector<float>> weight_cache;
        std::map<int, CircularConvolver> convolver_cache;
        std::vector<double> values(static_cast<size_t>(angular_count));
        std::vector<double> outer_rgb[3];
        std::vector<double> inner_rgb[3];
        std::vector<double> outer_alpha_sum;
        std::vector<double> inner_alpha_sum;
        std::vector<double> outer_alpha_accum;
        std::vector<double> inner_alpha_accum;

        for (int ri = 0; ri < radius_count; ++ri) {
            const int outer_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, outer_offset_for_span, ri, params.dynamic_offset_mode);
            const int inner_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, inner_offset_for_span, ri, params.dynamic_offset_mode);
            const int row_outer_length = rotation_effective_length(outer_strength_for_span, params.outer_offset_mode, outer_dynamic_offset);
            const int row_inner_length = rotation_effective_length(inner_strength_for_span, params.inner_offset_mode, inner_dynamic_offset);
            auto outer_weight_it = weight_cache.find(row_outer_length);
            if (outer_weight_it == weight_cache.end()) {
                outer_weight_it = weight_cache.emplace(row_outer_length, rotation_gaussian_weights(row_outer_length)).first;
            }
            auto inner_weight_it = weight_cache.find(row_inner_length);
            if (inner_weight_it == weight_cache.end()) {
                inner_weight_it = weight_cache.emplace(row_inner_length, rotation_gaussian_weights(row_inner_length)).first;
            }
            const std::vector<float> &row_outer_weights = outer_weight_it->second;
            const std::vector<float> &row_inner_weights = inner_weight_it->second;
            accumulate_row(ri, row_outer_weights, false, convolver_cache, values,
                           outer_rgb[0], outer_rgb[1], outer_rgb[2], outer_alpha_sum, outer_alpha_accum);
            if (has_inner && row_inner_weights.size() > 1) {
                accumulate_row(ri, row_inner_weights, true, convolver_cache, values,
                               inner_rgb[0], inner_rgb[1], inner_rgb[2], inner_alpha_sum, inner_alpha_accum);
            }

            for (int ai = 0; ai < angular_count; ++ai) {
                const size_t dst = (static_cast<size_t>(ri) * angular_count + ai) * 4;
                const double source_alpha = polar.rgba[dst + 3];
                double weighted_alpha = outer_alpha_sum[static_cast<size_t>(ai)];
                double weighted_rgb[3] = {
                    outer_rgb[0][static_cast<size_t>(ai)],
                    outer_rgb[1][static_cast<size_t>(ai)],
                    outer_rgb[2][static_cast<size_t>(ai)],
                };
                double accum_alpha = outer_alpha_accum[static_cast<size_t>(ai)];
                if (has_inner && row_inner_weights.size() > 1) {
                    weighted_alpha += inner_alpha_sum[static_cast<size_t>(ai)] - source_alpha;
                    for (int c = 0; c < 3; ++c) {
                        weighted_rgb[c] += inner_rgb[c][static_cast<size_t>(ai)] - polar.rgba[dst + c] * source_alpha;
                    }
                    accum_alpha = combine_inner_alpha(params.inner_alpha_mode,
                                                      weighted_alpha,
                                                      outer_alpha_accum[static_cast<size_t>(ai)],
                                                      inner_alpha_accum[static_cast<size_t>(ai)],
                                                      source_alpha);
                }
                if (weighted_alpha > 1.0e-8) {
                    for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = static_cast<float>(weighted_rgb[c] / weighted_alpha);
                }
                blurred.rgba[dst + 3] = static_cast<float>(accum_alpha);
            }
        }
    } else if (weights.size() < 64 && (!has_inner || inner_weights.size() < 64)) {
        for (int ri = 0; ri < radius_count; ++ri) {
            for (int ai = 0; ai < angular_count; ++ai) {
                double weighted_rgb[3] = {0.0, 0.0, 0.0};
                double weighted_alpha = 0.0;
                double accum_alpha = 0.0;
                for (size_t k = 0; k < weights.size(); ++k) {
                    const int src_ai = (ai - static_cast<int>(k) % angular_count + angular_count) % angular_count;
                    const size_t src_idx = (static_cast<size_t>(ri) * angular_count + src_ai) * 4;
                    const double alpha = polar.rgba[src_idx + 3];
                    const double contribution = alpha * weights[k];
                    for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * contribution;
                    weighted_alpha += contribution;
                    accum_alpha = std::max(accum_alpha, contribution);
                    if (!has_inner && params.outer_row_coupled_scale > 0.0) {
                        auto add_row_coupled = [&](int row_delta, bool tail_only, bool positive_only) {
                            if (ri < row_delta) return;
                            if (tail_only && k == 0) return;
                            const size_t row_idx =
                                (static_cast<size_t>(ri - row_delta) * angular_count + src_ai) * 4;
                            const double row_alpha = polar.rgba[row_idx + 3];
                            double row_contribution = row_alpha * weights[k] * params.outer_row_coupled_scale;
                            if (positive_only) {
                                const double row_luma =
                                    (static_cast<double>(polar.rgba[row_idx + 0]) +
                                     static_cast<double>(polar.rgba[row_idx + 1]) +
                                     static_cast<double>(polar.rgba[row_idx + 2])) / 3.0;
                                if (row_luma <= 0.0) row_contribution = 0.0;
                            }
                            if (row_contribution <= 0.0) return;
                            for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[row_idx + c] * row_contribution;
                            weighted_alpha += row_contribution;
                            accum_alpha = std::max(accum_alpha, row_contribution);
                        };

                        if (params.outer_row_coupled_mode == "prev-row-add") {
                            add_row_coupled(1, false, false);
                        } else if (params.outer_row_coupled_mode == "prev-row-tail-add") {
                            add_row_coupled(1, true, false);
                        } else if (params.outer_row_coupled_mode == "prev-row-tail-positive") {
                            add_row_coupled(1, true, true);
                        } else if (params.outer_row_coupled_mode == "prev2-row-tail-positive") {
                            add_row_coupled(2, true, true);
                        } else if (params.outer_row_coupled_mode == "prev-ladder-tail-positive") {
                            add_row_coupled(1, true, true);
                            add_row_coupled(2, true, true);
                        } else if (params.outer_row_coupled_mode == "prev2-k2-positive") {
                            if (k == 2) add_row_coupled(2, true, true);
                        } else if (params.outer_row_coupled_mode == "prev-hybrid-k12-positive") {
                            if (k == 1) add_row_coupled(1, true, true);
                            if (k == 2) add_row_coupled(2, true, true);
                        }
                    }
                }
                if (has_inner && inner_weights.size() > 1) {
                    const double outer_accum_alpha = accum_alpha;
                    double inner_accum_alpha = 0.0;
                    const size_t self_idx = (static_cast<size_t>(ri) * angular_count + ai) * 4;
                    const double source_alpha = polar.rgba[self_idx + 3];
                    for (size_t k = 0; k < inner_weights.size(); ++k) {
                        const int src_ai = (ai + static_cast<int>(k) % angular_count) % angular_count;
                        const size_t src_idx = (static_cast<size_t>(ri) * angular_count + src_ai) * 4;
                        const double alpha = polar.rgba[src_idx + 3];
                        const double contribution = alpha * inner_weights[k];
                        for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * contribution;
                        weighted_alpha += contribution;
                        inner_accum_alpha = std::max(inner_accum_alpha, contribution);
                    }
                    for (int c = 0; c < 3; ++c) weighted_rgb[c] -= polar.rgba[self_idx + c] * source_alpha;
                    weighted_alpha -= source_alpha;
                    accum_alpha = combine_inner_alpha(params.inner_alpha_mode,
                                                      weighted_alpha,
                                                      outer_accum_alpha,
                                                      inner_accum_alpha,
                                                      source_alpha);
                }
                const size_t dst = (static_cast<size_t>(ri) * angular_count + ai) * 4;
                if (weighted_alpha > 1.0e-8) {
                    for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = static_cast<float>(weighted_rgb[c] / weighted_alpha);
                }
                blurred.rgba[dst + 3] = static_cast<float>(accum_alpha);
            }
        }
    } else {
        std::map<int, CircularConvolver> convolver_cache;
        std::vector<double> values(static_cast<size_t>(angular_count));
        std::vector<double> outer_rgb[3];
        std::vector<double> inner_rgb[3];
        std::vector<double> outer_alpha_sum;
        std::vector<double> inner_alpha_sum;
        std::vector<double> outer_alpha_accum;
        std::vector<double> inner_alpha_accum;
        for (int ri = 0; ri < radius_count; ++ri) {
            accumulate_row(ri, weights, false, convolver_cache, values,
                           outer_rgb[0], outer_rgb[1], outer_rgb[2], outer_alpha_sum, outer_alpha_accum);
            if (has_inner && inner_weights.size() > 1) {
                accumulate_row(ri, inner_weights, true, convolver_cache, values,
                               inner_rgb[0], inner_rgb[1], inner_rgb[2], inner_alpha_sum, inner_alpha_accum);
            }
            for (int ai = 0; ai < angular_count; ++ai) {
                const size_t dst = (static_cast<size_t>(ri) * angular_count + ai) * 4;
                const double source_alpha = polar.rgba[dst + 3];
                double weighted_alpha = outer_alpha_sum[static_cast<size_t>(ai)];
                double weighted_rgb[3] = {
                    outer_rgb[0][static_cast<size_t>(ai)],
                    outer_rgb[1][static_cast<size_t>(ai)],
                    outer_rgb[2][static_cast<size_t>(ai)],
                };
                double accum_alpha = outer_alpha_accum[static_cast<size_t>(ai)];
                if (has_inner && inner_weights.size() > 1) {
                    weighted_alpha += inner_alpha_sum[static_cast<size_t>(ai)] - source_alpha;
                    for (int c = 0; c < 3; ++c) {
                        weighted_rgb[c] += inner_rgb[c][static_cast<size_t>(ai)] - polar.rgba[dst + c] * source_alpha;
                    }
                    accum_alpha = combine_inner_alpha(params.inner_alpha_mode,
                                                      weighted_alpha,
                                                      outer_alpha_accum[static_cast<size_t>(ai)],
                                                      inner_alpha_accum[static_cast<size_t>(ai)],
                                                      source_alpha);
                }
                if (weighted_alpha > 1.0e-8) {
                    for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = static_cast<float>(weighted_rgb[c] / weighted_alpha);
                }
                blurred.rgba[dst + 3] = static_cast<float>(accum_alpha);
            }
        }
    }

    if (typed_planes) {
        typed_planes->polar = polar;
        typed_planes->polar_coordinates.clear();
        typed_planes->polar_valid = polar_valid;
        typed_planes->polar_coordinates.reserve(static_cast<size_t>(radius_count) * angular_count);
        for (int ri = 0; ri < radius_count; ++ri) {
            const double r = static_cast<double>(min_r + ri) + radius_offset;
            for (int ai = 0; ai < angular_count; ++ai) {
                const double theta = (static_cast<double>(ai) + angle_offset_steps) * step_rad;
                const double sx = cx + cos_a * (std::cos(theta) * r) - sin_a * (std::sin(theta) * r * ratio);
                const double sy = cy + sin_a * (std::cos(theta) * r) + cos_a * (std::sin(theta) * r * ratio);
                typed_planes->polar_coordinates.push_back({static_cast<float>(sx), static_cast<float>(sy)});
            }
        }
        typed_planes->collapsed = blurred;
        if (!use_source_scatter_prepass) {
            typed_planes->accum = FloatImage{};
            typed_planes->prepass_alpha.clear();
            typed_planes->scatter_alpha.clear();
            typed_planes->source_alpha.clear();
        }
    }

    Image out;
    out.width = w;
    out.height = h;
    out.bit_depth = output_bit_depth;
    if (out.bit_depth == 16) out.rgba16.resize(static_cast<size_t>(w) * h * 4);
    else out.rgba.resize(static_cast<size_t>(w) * h * 4);
    const float max_val = out.bit_depth == 16 ? 65535.0f : 255.0f;
    WitnessDump witness;
    witness.enabled = !params.witness_dump_path.empty() && params.witness_x >= 0 && params.witness_y >= 0;
    witness.rgba_sampler_alpha_mode = params.rgba_sampler_alpha_mode;
    witness.outer_caller_collapse_mode = params.outer_caller_collapse_mode;
    const double alpha_quantize_epsilon = 1.0e-4;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float angle_index = 0.0f;
            float radius_index = 0.0f;
            if (params.rotation_grid_mode == "aex-float") {
                const float dx = static_cast<float>(x) - cxf;
                const float dy = static_cast<float>(y) - cyf;
                const float ex = cos_af * dx + sin_af * dy;
                const float ey = (cos_af * dy - sin_af * dx) / ratiof;
                const float radius = std::sqrt(ey * ey + ex * ex);
                float angle = std::atan2(ey, ex);
                if (angle < 0.0f) angle = static_cast<float>(static_cast<double>(angle) + M_PI * 2.0);
                angle_index = angle / step_radf;
                radius_index = radius - static_cast<float>(min_r);
            } else {
                const double dx = static_cast<double>(x) - cx;
                const double dy = static_cast<double>(y) - cy;
                const double ex = cos_a * dx + sin_a * dy;
                const double ey = (cos_a * dy - sin_a * dx) / ratio;
                const double radius = std::sqrt(ex * ex + ey * ey);
                double angle = std::atan2(ey, ex);
                if (angle < 0.0) angle += M_PI * 2.0;
                angle_index = static_cast<float>(angle / step_rad);
                radius_index = static_cast<float>(radius - min_r);
            }

            int xi = static_cast<int>(std::floor(angle_index));
            int yi_raw = static_cast<int>(std::floor(radius_index));
            float fx = angle_index - static_cast<float>(xi);
            float fy = radius_index - static_cast<float>(yi_raw);
            int x0 = ((xi % angular_count) + angular_count) % angular_count;
            int x1 = (x0 + 1) % angular_count;
            int y0 = std::max(0, std::min(yi_raw, radius_count - 1));
            int y1 = std::max(0, std::min(yi_raw + 1, radius_count - 1));
            auto collapsed_valid = [&](int px, int py) -> float {
                return polar_valid[static_cast<size_t>(py) * angular_count + px] ? 1.0f : 0.0f;
            };
            auto sample = [&](int px, int py, int c) -> float {
                const size_t cell = static_cast<size_t>(py) * angular_count + px;
                if (params.outer_caller_collapse_mode == "binary-validity") {
                    if (c == 3) return collapsed_valid(px, py);
                    return collapsed_valid(px, py) > 0.0f ? blurred.rgba[cell * 4 + c] : 0.0f;
                }
                if (params.outer_caller_collapse_mode == "zero-rgb-on-invalid") {
                    if (c == 3) return blurred.rgba[cell * 4 + c];
                    return collapsed_valid(px, py) > 0.0f ? blurred.rgba[cell * 4 + c] : 0.0f;
                }
                float value = blurred.rgba[cell * 4 + c];
                if (c < 3 && params.final_polar_rgb_mode == "clamp-nonnegative") value = std::max(0.0f, value);
                return value;
            };
            const double w00 = (1.0 - fx) * (1.0 - fy);
            const double w10 = fx * (1.0 - fy);
            const double w01 = (1.0 - fx) * fy;
            const double w11 = fx * fy;
            const double a00 = sample(x0, y0, 3) * w00;
            const double a10 = sample(x1, y0, 3) * w10;
            const double a01 = sample(x0, y1, 3) * w01;
            const double a11 = sample(x1, y1, 3) * w11;
            const double alpha = a00 + a10 + a01 + a11;
            const double validity_alpha = collapsed_valid(x0, y0) * w00 + collapsed_valid(x1, y0) * w10 +
                                          collapsed_valid(x0, y1) * w01 + collapsed_valid(x1, y1) * w11;
            const size_t dst = (static_cast<size_t>(y) * w + x) * 4;
            const bool capture_row_probe = witness.enabled && y == params.witness_y &&
                                           std::abs(x - params.witness_x) <= witness.row_probe_half_span;
            WitnessDump::PlaneProbePoint row_probe_point;
            if (capture_row_probe) {
                row_probe_point.x = x;
                row_probe_point.y = y;
                row_probe_point.radius_index = radius_index;
                row_probe_point.angle_index = angle_index;
                row_probe_point.alpha = alpha;
                row_probe_point.validity_alpha = validity_alpha;
                row_probe_point.validity_alpha_u8 = static_cast<int>(
                    clamp_float(static_cast<float>(std::floor(validity_alpha * 255.0 + alpha_quantize_epsilon)), 0.0f, 255.0f));
                row_probe_point.cell_valid[0] = collapsed_valid(x0, y0);
                row_probe_point.cell_valid[1] = collapsed_valid(x1, y0);
                row_probe_point.cell_valid[2] = collapsed_valid(x0, y1);
                row_probe_point.cell_valid[3] = collapsed_valid(x1, y1);
                row_probe_point.cell_alpha[0] = sample(x0, y0, 3);
                row_probe_point.cell_alpha[1] = sample(x1, y0, 3);
                row_probe_point.cell_alpha[2] = sample(x0, y1, 3);
                row_probe_point.cell_alpha[3] = sample(x1, y1, 3);
            }
            if (witness.enabled && x == params.witness_x && y == params.witness_y) {
                witness.captured = true;
                witness.path_kind = "rotation";
                witness.x = x;
                witness.y = y;
                witness.radius_index = radius_index;
                witness.angle_index = angle_index;
                witness.sample_x0 = x0;
                witness.sample_x1 = x1;
                witness.sample_y0 = y0;
                witness.sample_y1 = y1;
                witness.fx = fx;
                witness.fy = fy;
                witness.w00 = w00;
                witness.w10 = w10;
                witness.w01 = w01;
                witness.w11 = w11;
                witness.a00 = a00;
                witness.a10 = a10;
                witness.a01 = a01;
                witness.a11 = a11;
                witness.alpha = alpha;
                witness.validity_alpha = validity_alpha;
                for (int c = 0; c < 4; ++c) {
                    witness.cell00_rgba[c] = sample(x0, y0, c);
                    witness.cell10_rgba[c] = sample(x1, y0, c);
                    witness.cell01_rgba[c] = sample(x0, y1, c);
                    witness.cell11_rgba[c] = sample(x1, y1, c);
                }
                witness.cell00_valid = collapsed_valid(x0, y0);
                witness.cell10_valid = collapsed_valid(x1, y0);
                witness.cell01_valid = collapsed_valid(x0, y1);
                witness.cell11_valid = collapsed_valid(x1, y1);
                witness.neighborhood_origin_x = positive_mod(x0 - 1, angular_count);
                witness.neighborhood_origin_y = y0 > 0 ? y0 - 1 : y0;
                int ni = 0;
                for (int oy = 0; oy < 3; ++oy) {
                    for (int ox = 0; ox < 3; ++ox, ++ni) {
                        const int px = positive_mod(witness.neighborhood_origin_x + ox, angular_count);
                        const int py = std::max(0, std::min(radius_count - 1, witness.neighborhood_origin_y + oy));
                        for (int c = 0; c < 4; ++c) witness.neighborhood_rgba[ni][c] = sample(px, py, c);
                        witness.neighborhood_valid[ni] = collapsed_valid(px, py);
                    }
                }
                witness.source_probe_origin_x = positive_mod(x0 - 5, angular_count);
                witness.source_probe_origin_y = std::max(0, y0 - 6);
                int spi = 0;
                for (int oy = 0; oy < witness.source_probe_height; ++oy) {
                    for (int ox = 0; ox < witness.source_probe_width; ++ox, ++spi) {
                        const int px = positive_mod(witness.source_probe_origin_x + ox, angular_count);
                        const int py = std::max(0, std::min(radius_count - 1, witness.source_probe_origin_y + oy));
                        const size_t src_idx = (static_cast<size_t>(py) * angular_count + px) * 4;
                        for (int c = 0; c < 4; ++c) witness.source_probe_rgba[spi][c] = polar.rgba[src_idx + c];
                    }
                }
            }
            for (int c = 0; c < 3; ++c) {
                const double rgb_numerator = sample(x0, y0, c) * a00 + sample(x1, y0, c) * a10 +
                                             sample(x0, y1, c) * a01 + sample(x1, y1, c) * a11;
                double rgb = 0.0;
                if (alpha > 1.0e-8) {
                    rgb = rgb_numerator / alpha;
                }
                rgb *= params.brightness_gain;
                const int q = static_cast<int>(clamp_float(static_cast<float>(std::floor(rgb * max_val)), 0.0f, max_val));
                if (out.bit_depth == 16) out.rgba16[dst + c] = static_cast<uint16_t>(q);
                else out.rgba[dst + c] = static_cast<unsigned char>(q);
                if (witness.enabled && x == params.witness_x && y == params.witness_y) {
                    witness.sample_rgb_numerator[c] = rgb_numerator;
                    witness.sample_rgba[c] = static_cast<float>(rgb);
                    witness.sample_u8[c] = out.bit_depth == 16 ? q >> 8 : q;
                }
                if (capture_row_probe) {
                    row_probe_point.sample_rgba[c] = static_cast<float>(rgb);
                    row_probe_point.sample_u8[c] = out.bit_depth == 16 ? q >> 8 : q;
                }
            }
            const int aq = static_cast<int>(clamp_float(static_cast<float>(std::floor(alpha * max_val + alpha_quantize_epsilon)), 0.0f, max_val));
            if (out.bit_depth == 16) out.rgba16[dst + 3] = static_cast<uint16_t>(aq);
            else out.rgba[dst + 3] = static_cast<unsigned char>(aq);
            if (witness.enabled && x == params.witness_x && y == params.witness_y) {
                witness.sample_rgba[3] = static_cast<float>(alpha);
                witness.sample_u8[3] = out.bit_depth == 16 ? aq >> 8 : aq;
            }
            if (capture_row_probe) {
                row_probe_point.sample_rgba[3] = static_cast<float>(alpha);
                row_probe_point.sample_u8[3] = out.bit_depth == 16 ? aq >> 8 : aq;
                row_probe_point.alpha_u8 = out.bit_depth == 16 ? aq >> 8 : aq;
                witness.row_probe.push_back(row_probe_point);
            }
        }
    }
    maybe_write_witness_dump(params, witness);
    return out;
}

Image render_olmradialblur_rotation(const Image &input, const RadialBlurParams &params) {
    FloatImage src;
    src.width = input.width;
    src.height = input.height;
    src.rgba.resize(static_cast<size_t>(src.width) * src.height * 4);
    if (input.bit_depth == 16) {
        for (size_t i = 0; i < input.rgba16.size(); ++i) src.rgba[i] = static_cast<float>(input.rgba16[i]) / 65535.0f;
    } else {
        for (size_t i = 0; i < input.rgba.size(); ++i) src.rgba[i] = static_cast<float>(input.rgba[i]) / 255.0f;
    }
    return render_olmradialblur_rotation_float(src, params, nullptr, input.bit_depth);
}

struct Args {
    std::string input;
    std::string params;
    std::string output;
    bool ignore_size_variation = false;
    std::string inner_alpha_mode = "max";
    bool inner_source_scatter_prepass = false;
    bool outer_source_scatter_prepass = false;
    std::string inner_prepass_mode = "tail-gather";
    std::string inner_prepass_span_mode = "edge-fade";
    std::string inner_prepass_weight_mode = "aex-alpha";
    std::string inner_prepass_factor_mode = "one";
    bool inner_prepass_overwrite_seed = false;
    std::string inner_scatter_rgb_mode = "straight";
    std::string inner_scatter_seed_mode = "source";
    std::string inner_seed_alpha_mode = "input";
    std::string inner_final_alpha_mode = "max";
    std::string inner_rgb_denominator_mode = "accum";
    std::string inner_scatter_span_scale_mode = "one";
    std::string inner_scatter_param10_plane = "one";
    std::string inner_wrap_mode = "aex-next-row";
    std::string inner_source_scale_mode = "one";
    std::string dynamic_offset_mode = "current";
    std::string polar_valid_mode = "strict";
    std::string polar_sample_mode = "plain";
    std::string rgba_sampler_alpha_mode = "shared-normalized";
    bool aex_quality_span_scale = true;
    bool inner_scatter_span_minus_one = true;
    bool inner_scatter_loop_minus_one = false;
    bool inner_scatter_table_span_minus_one = false;
    std::string rotation_gaussian_mode = "double";
    std::string zoom_grid_mode = "double";
    bool zoom_paired_trig_float = false;
    bool zoom_inverse_float = false;
    std::string zoom_aex_trig_table_path;
    std::string rotation_grid_mode = "double";
    double rotation_grid_angle_offset_steps = 0.0;
    double rotation_grid_radius_offset = 0.0;
    std::string outer_row_coupled_mode = "none";
    double outer_row_coupled_scale = 1.0;
    std::string outer_caller_collapse_mode = "none";
    std::string outer_alpha_quantize_mode = "epsilon";
    std::string final_polar_rgb_mode = "none";
    std::string inner_scatter_stats_path;
    std::string witness_dump_path;
    int witness_x = -1;
    int witness_y = -1;
    int witness_row_half_span = 4;
};

Args parse_args(int argc, char **argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        std::string key(argv[i]);
        auto need_value = [&](const char *name) -> std::string {
            if (i + 1 >= argc) throw std::runtime_error(std::string("missing value for ") + name);
            return std::string(argv[++i]);
        };
        if (key == "--input") {
            args.input = need_value("--input");
        } else if (key == "--params") {
            args.params = need_value("--params");
        } else if (key == "--output") {
            args.output = need_value("--output");
        } else if (key == "--ignore-size-variation") {
            args.ignore_size_variation = true;
        } else if (key == "--inner-source-scatter-prepass") {
            args.inner_source_scatter_prepass = true;
        } else if (key == "--outer-source-scatter-prepass") {
            args.outer_source_scatter_prepass = true;
        } else if (key == "--inner-prepass-mode") {
            args.inner_prepass_mode = need_value("--inner-prepass-mode");
            if (args.inner_prepass_mode != "simple" && args.inner_prepass_mode != "tail-gather") {
                throw std::runtime_error("--inner-prepass-mode must be simple or tail-gather");
            }
        } else if (key == "--inner-prepass-span-mode") {
            args.inner_prepass_span_mode = need_value("--inner-prepass-span-mode");
            if (args.inner_prepass_span_mode != "strength" && args.inner_prepass_span_mode != "offset" &&
                args.inner_prepass_span_mode != "edge-fade") {
                throw std::runtime_error("--inner-prepass-span-mode must be strength, offset, or edge-fade");
            }
        } else if (key == "--inner-prepass-weight-mode") {
            args.inner_prepass_weight_mode = need_value("--inner-prepass-weight-mode");
            if (args.inner_prepass_weight_mode != "row-span" && args.inner_prepass_weight_mode != "aex-alpha") {
                throw std::runtime_error("--inner-prepass-weight-mode must be row-span or aex-alpha");
            }
        } else if (key == "--inner-prepass-factor-mode") {
            args.inner_prepass_factor_mode = need_value("--inner-prepass-factor-mode");
            if (args.inner_prepass_factor_mode != "alpha" && args.inner_prepass_factor_mode != "one" &&
                args.inner_prepass_factor_mode != "valid") {
                throw std::runtime_error("--inner-prepass-factor-mode must be alpha, one, or valid");
            }
        } else if (key == "--inner-prepass-overwrite-seed") {
            args.inner_prepass_overwrite_seed = true;
        } else if (key == "--inner-scatter-rgb-mode") {
            args.inner_scatter_rgb_mode = need_value("--inner-scatter-rgb-mode");
            if (args.inner_scatter_rgb_mode != "straight" && args.inner_scatter_rgb_mode != "prepass-premul") {
                throw std::runtime_error("--inner-scatter-rgb-mode must be straight or prepass-premul");
            }
        } else if (key == "--inner-scatter-seed-mode") {
            args.inner_scatter_seed_mode = need_value("--inner-scatter-seed-mode");
            if (args.inner_scatter_seed_mode != "source" && args.inner_scatter_seed_mode != "none" &&
                args.inner_scatter_seed_mode != "edgefade-none") {
                throw std::runtime_error("--inner-scatter-seed-mode must be source, none, or edgefade-none");
            }
        } else if (key == "--inner-seed-alpha-mode") {
            args.inner_seed_alpha_mode = need_value("--inner-seed-alpha-mode");
            if (args.inner_seed_alpha_mode != "input" && args.inner_seed_alpha_mode != "prepass") {
                throw std::runtime_error("--inner-seed-alpha-mode must be input or prepass");
            }
        } else if (key == "--inner-final-alpha-mode") {
            args.inner_final_alpha_mode = need_value("--inner-final-alpha-mode");
            if (args.inner_final_alpha_mode != "max" && args.inner_final_alpha_mode != "denom" &&
                args.inner_final_alpha_mode != "source") {
                throw std::runtime_error("--inner-final-alpha-mode must be max, denom, or source");
            }
        } else if (key == "--inner-rgb-denominator-mode") {
            args.inner_rgb_denominator_mode = need_value("--inner-rgb-denominator-mode");
            if (args.inner_rgb_denominator_mode != "accum" && args.inner_rgb_denominator_mode != "max") {
                throw std::runtime_error("--inner-rgb-denominator-mode must be accum or max");
            }
        } else if (key == "--inner-scatter-span-scale-mode") {
            args.inner_scatter_span_scale_mode = need_value("--inner-scatter-span-scale-mode");
            if (args.inner_scatter_span_scale_mode != "one" &&
                args.inner_scatter_span_scale_mode != "source-alpha" &&
                args.inner_scatter_span_scale_mode != "input-alpha") {
                throw std::runtime_error("--inner-scatter-span-scale-mode must be one, source-alpha, or input-alpha");
            }
        } else if (key == "--inner-scatter-param10-plane") {
            args.inner_scatter_param10_plane = need_value("--inner-scatter-param10-plane");
            if (args.inner_scatter_param10_plane != "one" &&
                args.inner_scatter_param10_plane != "polar-alpha" &&
                args.inner_scatter_param10_plane != "prepass-alpha" &&
                args.inner_scatter_param10_plane != "factor") {
                throw std::runtime_error("--inner-scatter-param10-plane must be one, polar-alpha, prepass-alpha, or factor");
            }
        } else if (key == "--inner-wrap-mode") {
            args.inner_wrap_mode = need_value("--inner-wrap-mode");
            if (args.inner_wrap_mode != "circular" && args.inner_wrap_mode != "aex-next-row") {
                throw std::runtime_error("--inner-wrap-mode must be circular or aex-next-row");
            }
        } else if (key == "--inner-source-scale-mode") {
            args.inner_source_scale_mode = need_value("--inner-source-scale-mode");
            if (args.inner_source_scale_mode != "one" && args.inner_source_scale_mode != "alpha" &&
                args.inner_source_scale_mode != "inv-alpha") {
                throw std::runtime_error("--inner-source-scale-mode must be one, alpha, or inv-alpha");
            }
        } else if (key == "--dynamic-offset-mode") {
            args.dynamic_offset_mode = need_value("--dynamic-offset-mode");
            if (args.dynamic_offset_mode != "current" && args.dynamic_offset_mode != "aex-row" &&
                args.dynamic_offset_mode != "min-radius") {
                throw std::runtime_error("--dynamic-offset-mode must be current, aex-row, or min-radius");
            }
        } else if (key == "--polar-valid-mode") {
            args.polar_valid_mode = need_value("--polar-valid-mode");
            if (args.polar_valid_mode != "strict" && args.polar_valid_mode != "aex-repeat") {
                throw std::runtime_error("--polar-valid-mode must be strict or aex-repeat");
            }
        } else if (key == "--polar-sample-mode") {
            args.polar_sample_mode = need_value("--polar-sample-mode");
            if (args.polar_sample_mode != "plain" && args.polar_sample_mode != "aex-alpha" &&
                args.polar_sample_mode != "conditional-inner") {
                throw std::runtime_error("--polar-sample-mode must be plain, aex-alpha, or conditional-inner");
            }
        } else if (key == "--rgba-sampler-alpha-mode") {
            args.rgba_sampler_alpha_mode = need_value("--rgba-sampler-alpha-mode");
            if (args.rgba_sampler_alpha_mode != "shared-normalized" &&
                args.rgba_sampler_alpha_mode != "repeat-raw" &&
                args.rgba_sampler_alpha_mode != "repeat-raw-f32") {
                throw std::runtime_error("--rgba-sampler-alpha-mode must be shared-normalized, repeat-raw, or repeat-raw-f32");
            }
        } else if (key == "--aex-quality-span-scale") {
            args.aex_quality_span_scale = true;
        } else if (key == "--inner-scatter-span-minus-one") {
            args.inner_scatter_span_minus_one = true;
        } else if (key == "--no-inner-scatter-span-minus-one") {
            args.inner_scatter_span_minus_one = false;
        } else if (key == "--inner-scatter-loop-minus-one") {
            args.inner_scatter_loop_minus_one = true;
        } else if (key == "--inner-scatter-table-span-minus-one") {
            args.inner_scatter_table_span_minus_one = true;
        } else if (key == "--rotation-gaussian-mode") {
            args.rotation_gaussian_mode = need_value("--rotation-gaussian-mode");
            if (args.rotation_gaussian_mode != "double" && args.rotation_gaussian_mode != "aex-float") {
                throw std::runtime_error("--rotation-gaussian-mode must be double or aex-float");
            }
        } else if (key == "--zoom-grid-mode") {
            args.zoom_grid_mode = need_value("--zoom-grid-mode");
            if (args.zoom_grid_mode != "double" && args.zoom_grid_mode != "aex-float") {
                throw std::runtime_error("--zoom-grid-mode must be double or aex-float");
            }
        } else if (key == "--zoom-paired-trig-float") {
            args.zoom_paired_trig_float = true;
        } else if (key == "--zoom-inverse-float") {
            args.zoom_inverse_float = true;
        } else if (key == "--zoom-aex-trig-table") {
            args.zoom_aex_trig_table_path = need_value("--zoom-aex-trig-table");
        } else if (key == "--rotation-grid-mode") {
            args.rotation_grid_mode = need_value("--rotation-grid-mode");
            if (args.rotation_grid_mode != "double" && args.rotation_grid_mode != "aex-float") {
                throw std::runtime_error("--rotation-grid-mode must be double or aex-float");
            }
        } else if (key == "--rotation-grid-angle-offset-steps") {
            args.rotation_grid_angle_offset_steps = std::stod(need_value("--rotation-grid-angle-offset-steps"));
        } else if (key == "--rotation-grid-radius-offset") {
            args.rotation_grid_radius_offset = std::stod(need_value("--rotation-grid-radius-offset"));
        } else if (key == "--outer-row-coupled-mode") {
            args.outer_row_coupled_mode = need_value("--outer-row-coupled-mode");
            if (args.outer_row_coupled_mode != "none" &&
                args.outer_row_coupled_mode != "prev-row-add" &&
                args.outer_row_coupled_mode != "prev-row-tail-add" &&
                args.outer_row_coupled_mode != "prev-row-tail-positive" &&
                args.outer_row_coupled_mode != "prev2-row-tail-positive" &&
                args.outer_row_coupled_mode != "prev-ladder-tail-positive" &&
                args.outer_row_coupled_mode != "prev2-k2-positive" &&
                args.outer_row_coupled_mode != "prev-hybrid-k12-positive") {
                throw std::runtime_error("--outer-row-coupled-mode must be none, prev-row-add, prev-row-tail-add, prev-row-tail-positive, prev2-row-tail-positive, prev-ladder-tail-positive, prev2-k2-positive, or prev-hybrid-k12-positive");
            }
        } else if (key == "--outer-row-coupled-scale") {
            args.outer_row_coupled_scale = std::stod(need_value("--outer-row-coupled-scale"));
        } else if (key == "--outer-caller-collapse-mode") {
            args.outer_caller_collapse_mode = need_value("--outer-caller-collapse-mode");
            if (args.outer_caller_collapse_mode != "none" &&
                args.outer_caller_collapse_mode != "binary-validity" &&
                args.outer_caller_collapse_mode != "zero-rgb-on-invalid" &&
                args.outer_caller_collapse_mode != "propagated-validity-alpha" &&
                args.outer_caller_collapse_mode != "polar-alpha") {
                throw std::runtime_error("--outer-caller-collapse-mode must be none, binary-validity, zero-rgb-on-invalid, propagated-validity-alpha, or polar-alpha");
            }
        } else if (key == "--outer-alpha-quantize-mode") {
            args.outer_alpha_quantize_mode = need_value("--outer-alpha-quantize-mode");
            if (args.outer_alpha_quantize_mode != "epsilon" && args.outer_alpha_quantize_mode != "truncate") {
                throw std::runtime_error("--outer-alpha-quantize-mode must be epsilon or truncate");
            }
        } else if (key == "--final-polar-rgb-mode") {
            args.final_polar_rgb_mode = need_value("--final-polar-rgb-mode");
            if (args.final_polar_rgb_mode != "none" &&
                args.final_polar_rgb_mode != "clamp-nonnegative") {
                throw std::runtime_error("--final-polar-rgb-mode must be none or clamp-nonnegative");
            }
        } else if (key == "--inner-scatter-stats") {
            args.inner_scatter_stats_path = need_value("--inner-scatter-stats");
        } else if (key == "--witness-dump") {
            args.witness_dump_path = need_value("--witness-dump");
        } else if (key == "--witness-x") {
            args.witness_x = std::stoi(need_value("--witness-x"));
        } else if (key == "--witness-y") {
            args.witness_y = std::stoi(need_value("--witness-y"));
        } else if (key == "--witness-row-half-span") {
            args.witness_row_half_span = std::stoi(need_value("--witness-row-half-span"));
        } else if (key == "--inner-alpha-mode") {
            args.inner_alpha_mode = need_value("--inner-alpha-mode");
            if (args.inner_alpha_mode != "max" && args.inner_alpha_mode != "sum" &&
                args.inner_alpha_mode != "outer" && args.inner_alpha_mode != "inner" &&
                args.inner_alpha_mode != "input") {
                throw std::runtime_error("--inner-alpha-mode must be max, sum, outer, inner, or input");
            }
        } else if (key == "--help" || key == "-h") {
            std::printf("Usage: olmradialblur_cli --input in.png --params params.json --output out.png [--ignore-size-variation] [--inner-alpha-mode max|sum|outer|inner|input] [--inner-source-scatter-prepass] [--outer-source-scatter-prepass] [--inner-prepass-mode simple|tail-gather] [--inner-prepass-span-mode strength|offset|edge-fade] [--inner-prepass-weight-mode row-span|aex-alpha] [--inner-prepass-factor-mode alpha|one|valid] [--inner-prepass-overwrite-seed] [--inner-scatter-rgb-mode straight|prepass-premul] [--inner-scatter-seed-mode source|none|edgefade-none] [--inner-seed-alpha-mode input|prepass] [--inner-final-alpha-mode max|denom|source] [--inner-rgb-denominator-mode accum|max] [--inner-scatter-span-scale-mode one|source-alpha|input-alpha] [--inner-scatter-param10-plane one|polar-alpha|prepass-alpha|factor] [--inner-wrap-mode circular|aex-next-row] [--inner-source-scale-mode one|alpha|inv-alpha] [--dynamic-offset-mode current|aex-row|min-radius] [--polar-valid-mode strict|aex-repeat] [--polar-sample-mode plain|aex-alpha|conditional-inner] [--rgba-sampler-alpha-mode shared-normalized|repeat-raw] [--zoom-grid-mode double|aex-float] [--zoom-paired-trig-float] [--zoom-aex-trig-table table.bin] [--zoom-inverse-float] [--rotation-gaussian-mode double|aex-float] [--rotation-grid-mode double|aex-float] [--rotation-grid-angle-offset-steps S] [--rotation-grid-radius-offset R] [--outer-row-coupled-mode none|prev-row-add|prev-row-tail-add|prev-row-tail-positive|prev2-row-tail-positive|prev-ladder-tail-positive|prev2-k2-positive|prev-hybrid-k12-positive] [--outer-row-coupled-scale V] [--outer-caller-collapse-mode none|binary-validity|zero-rgb-on-invalid|propagated-validity-alpha] [--final-polar-rgb-mode none|clamp-nonnegative] [--aex-quality-span-scale] [--inner-scatter-span-minus-one|--no-inner-scatter-span-minus-one] [--inner-scatter-loop-minus-one] [--inner-scatter-table-span-minus-one] [--inner-scatter-stats path.json] [--witness-dump path.json --witness-x N --witness-y N]\n");
            std::exit(0);
        } else {
            throw std::runtime_error("unknown argument: " + key);
        }
    }
    if (args.input.empty() || args.params.empty() || args.output.empty()) {
        throw std::runtime_error("required arguments: --input, --params, --output");
    }
    return args;
}

}  // namespace

int main(int argc, char **argv) {
    try {
        Args args = parse_args(argc, argv);
        Image input = read_png(args.input);
        RadialBlurParams params = read_params(args.params);
        params.ignore_size_variation = args.ignore_size_variation;
        params.inner_alpha_mode = args.inner_alpha_mode;
        params.inner_source_scatter_prepass = args.inner_source_scatter_prepass;
        params.outer_source_scatter_prepass = args.outer_source_scatter_prepass;
        params.inner_prepass_mode = args.inner_prepass_mode;
        params.inner_prepass_span_mode = args.inner_prepass_span_mode;
        params.inner_prepass_weight_mode = args.inner_prepass_weight_mode;
        params.inner_prepass_factor_mode = args.inner_prepass_factor_mode;
        params.inner_prepass_overwrite_seed = args.inner_prepass_overwrite_seed;
        params.inner_scatter_rgb_mode = args.inner_scatter_rgb_mode;
        params.inner_scatter_seed_mode = args.inner_scatter_seed_mode;
        params.inner_seed_alpha_mode = args.inner_seed_alpha_mode;
        params.inner_final_alpha_mode = args.inner_final_alpha_mode;
        params.inner_rgb_denominator_mode = args.inner_rgb_denominator_mode;
        params.inner_scatter_span_scale_mode = args.inner_scatter_span_scale_mode;
        params.inner_scatter_param10_plane = args.inner_scatter_param10_plane;
        params.inner_wrap_mode = args.inner_wrap_mode;
        params.inner_source_scale_mode = args.inner_source_scale_mode;
        params.dynamic_offset_mode = args.dynamic_offset_mode;
        params.polar_valid_mode = args.polar_valid_mode;
        params.polar_sample_mode = args.polar_sample_mode;
        params.rgba_sampler_alpha_mode = args.rgba_sampler_alpha_mode;
        params.aex_quality_span_scale = args.aex_quality_span_scale;
        params.inner_scatter_span_minus_one = args.inner_scatter_span_minus_one;
        params.inner_scatter_loop_minus_one = args.inner_scatter_loop_minus_one;
        params.inner_scatter_table_span_minus_one = args.inner_scatter_table_span_minus_one;
        params.rotation_gaussian_mode = args.rotation_gaussian_mode;
        params.zoom_grid_mode = args.zoom_grid_mode;
        params.zoom_paired_trig_float = args.zoom_paired_trig_float;
        params.zoom_inverse_float = args.zoom_inverse_float;
        params.zoom_aex_trig_table_path = args.zoom_aex_trig_table_path;
        params.rotation_grid_mode = args.rotation_grid_mode;
        params.rotation_grid_angle_offset_steps = args.rotation_grid_angle_offset_steps;
        params.rotation_grid_radius_offset = args.rotation_grid_radius_offset;
        params.outer_row_coupled_mode = args.outer_row_coupled_mode;
        params.outer_row_coupled_scale = args.outer_row_coupled_scale;
        params.outer_caller_collapse_mode = args.outer_caller_collapse_mode;
        params.outer_alpha_quantize_mode = args.outer_alpha_quantize_mode;
        params.final_polar_rgb_mode = args.final_polar_rgb_mode;
        params.inner_scatter_stats_path = args.inner_scatter_stats_path;
        params.witness_dump_path = args.witness_dump_path;
        params.witness_x = args.witness_x;
        params.witness_y = args.witness_y;
        params.witness_row_half_span = args.witness_row_half_span;
        g_rotation_gaussian_mode = params.rotation_gaussian_mode;
        Image output = params.blur_type == 2 ? render_olmradialblur_rotation(input, params)
                                             : render_olmradialblur_zoom(input, params);
        write_png(args.output, output);
        std::printf("wrote: %s (experimental %s C++ slice)\n", args.output.c_str(), params.blur_type == 2 ? "rotation" : "zoom");
        return 0;
    } catch (const std::exception &ex) {
        std::fprintf(stderr, "olmradialblur_cli: %s\n", ex.what());
        return 1;
    }
}
