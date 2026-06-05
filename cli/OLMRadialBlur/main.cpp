#include <png.h>

#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <filesystem>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Image {
    int width = 0;
    int height = 0;
    std::vector<unsigned char> rgba;
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
    std::string inner_prepass_mode = "simple";
    std::string inner_prepass_span_mode = "strength";
    std::string inner_prepass_weight_mode = "row-span";
    std::string inner_scatter_rgb_mode = "straight";
    std::string inner_scatter_seed_mode = "source";
    std::string inner_seed_alpha_mode = "input";
    std::string inner_final_alpha_mode = "max";
    std::string inner_rgb_denominator_mode = "accum";
    std::string inner_scatter_span_scale_mode = "one";
    std::string inner_wrap_mode = "circular";
    std::string inner_source_scale_mode = "one";
    std::string dynamic_offset_mode = "current";
    std::string polar_valid_mode = "strict";
};

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

    if (bit_depth == 16) png_set_strip_16(png);
    if (color_type == PNG_COLOR_TYPE_PALETTE) png_set_palette_to_rgb(png);
    if (color_type == PNG_COLOR_TYPE_GRAY && bit_depth < 8) png_set_expand_gray_1_2_4_to_8(png);
    bool has_alpha = (color_type & PNG_COLOR_MASK_ALPHA) != 0;
    bool has_trns = png_get_valid(png, info, PNG_INFO_tRNS) != 0;
    if (has_trns) png_set_tRNS_to_alpha(png);
    if (color_type == PNG_COLOR_TYPE_GRAY || color_type == PNG_COLOR_TYPE_GRAY_ALPHA) png_set_gray_to_rgb(png);
    if (!has_alpha && !has_trns) png_set_filler(png, 0xff, PNG_FILLER_AFTER);

    png_read_update_info(png, info);
    if (png_get_rowbytes(png, info) != width * 4) {
        png_destroy_read_struct(&png, &info, nullptr);
        std::fclose(fp);
        throw std::runtime_error("unsupported PNG color conversion result");
    }
    Image image;
    image.width = static_cast<int>(width);
    image.height = static_cast<int>(height);
    image.rgba.resize(static_cast<size_t>(image.width) * static_cast<size_t>(image.height) * 4);
    std::vector<png_bytep> rows(image.height);
    for (int y = 0; y < image.height; ++y) rows[y] = image.rgba.data() + static_cast<size_t>(y) * image.width * 4;
    png_read_image(png, rows.data());
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
    png_set_IHDR(png, info, image.width, image.height, 8, PNG_COLOR_TYPE_RGBA,
                 PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_write_info(png, info);
    std::vector<png_bytep> rows(image.height);
    for (int y = 0; y < image.height; ++y) {
        rows[y] = const_cast<unsigned char *>(image.rgba.data() + static_cast<size_t>(y) * image.width * 4);
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

float clamp_float(float v, float lo, float hi) {
    return std::max(lo, std::min(v, hi));
}

using Complex = std::complex<double>;

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
    const int idx_scale = table_len / length;
    std::vector<float> weights(static_cast<size_t>(length), 1.0f);
    for (int i = 1; i < length; ++i) {
        const int table_index = static_cast<int>(static_cast<float>(i) * static_cast<float>(idx_scale));
        weights[static_cast<size_t>(i)] = static_cast<float>(std::exp(-(table_index * table_index) * inv_denom));
    }
    return weights;
}

float rotation_gaussian_weight_at(int span, int offset) {
    if (span <= 1 || offset <= 0) return 1.0f;
    const int table_index = offset;
    const double denom = static_cast<double>(span) * static_cast<double>(span) * 2.0 * 0.111111119389534 + 1.0e-5;
    const double inv_denom = 1.0 / denom;
    return static_cast<float>(std::exp(-(table_index * table_index) * inv_denom));
}

float rotation_gaussian_weight_at_scaled(int table_span, int offset, float alpha_scale) {
    if (table_span <= 1 || offset <= 0) return 1.0f;
    if (alpha_scale <= 1.0e-8f) return 0.0f;
    const int table_index = static_cast<int>(static_cast<float>(offset) / alpha_scale);
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
    for (size_t i = 0; i < input.rgba.size(); ++i) src.rgba[i] = static_cast<float>(input.rgba[i]) / 255.0f;

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

    FloatImage polar;
    polar.width = radius_count;
    polar.height = angular_count;
    polar.rgba.resize(static_cast<size_t>(angular_count) * radius_count * 4);
    const double cos_a = std::cos(base_angle);
    const double sin_a = std::sin(base_angle);
    for (int ai = 0; ai < angular_count; ++ai) {
        const double theta = static_cast<double>(ai) * step_rad;
        const double cos_t = std::cos(theta);
        const double sin_t = std::sin(theta);
        for (int ri = 0; ri < radius_count; ++ri) {
            const double r = static_cast<double>(min_r + ri);
            const double sx0 = r * cos_t;
            const double sy0 = r * sin_t * ratio;
            const float sx = static_cast<float>(cx + cos_a * sx0 - sin_a * sy0);
            const float sy = static_cast<float>(cy + sin_a * sx0 + cos_a * sy0);
            const size_t dst = (static_cast<size_t>(ai) * radius_count + ri) * 4;
            for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sample_channel(src, sx, sy, c, params.repeat_border);
        }
    }

    const std::vector<float> weights = zoom_gaussian_weights(zoom_effective_length(params));
    const bool use_fft_convolution = weights.size() > 512;
    FloatImage blurred;
    blurred.width = radius_count;
    blurred.height = angular_count;
    blurred.rgba.assign(static_cast<size_t>(angular_count) * radius_count * 4, 0.0f);
    if (!use_fft_convolution) {
        for (int ai = 0; ai < angular_count; ++ai) {
            for (int ri = 0; ri < radius_count; ++ri) {
                double weighted_rgb[3] = {0.0, 0.0, 0.0};
                double weighted_alpha = 0.0;
                double accum_alpha = 0.0;
                const int limit = std::min<int>(static_cast<int>(weights.size()), ri + 1);
                for (int k = 0; k < limit; ++k) {
                    const size_t src_idx = (static_cast<size_t>(ai) * radius_count + (ri - k)) * 4;
                    const double alpha = polar.rgba[src_idx + 3];
                    const double weight = weights[static_cast<size_t>(k)];
                    for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * alpha * weight;
                    weighted_alpha += alpha * weight;
                    accum_alpha += alpha * weight;
                }
                const size_t dst = (static_cast<size_t>(ai) * radius_count + ri) * 4;
                if (weighted_alpha > 1.0e-8) {
                    for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = static_cast<float>(weighted_rgb[c] / weighted_alpha);
                }
                blurred.rgba[dst + 3] = clamp_float(static_cast<float>(accum_alpha), 0.0f, 1.0f);
            }
        }
    } else {
        ForwardConvolver convolver(radius_count, weights);
        std::vector<double> values(static_cast<size_t>(radius_count));
        std::vector<double> alpha_conv;
        std::vector<double> rgb_conv[3];
        for (int ai = 0; ai < angular_count; ++ai) {
            for (int ri = 0; ri < radius_count; ++ri) {
                const size_t src_idx = (static_cast<size_t>(ai) * radius_count + ri) * 4;
                values[static_cast<size_t>(ri)] = polar.rgba[src_idx + 3];
            }
            convolver.convolve(values, alpha_conv);

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
            }
        }
    }

    Image out;
    out.width = w;
    out.height = h;
    out.rgba.resize(static_cast<size_t>(w) * h * 4);
    const double rgb_quantize_epsilon = use_fft_convolution ? 0.0 : 1.0e-4;
    const double alpha_quantize_epsilon = 1.0e-4;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const double dx = static_cast<double>(x) - cx;
            const double dy = static_cast<double>(y) - cy;
            const double ex = cos_a * dx + sin_a * dy;
            const double ey = (cos_a * dy - sin_a * dx) / ratio;
            const double radius = std::sqrt(ex * ex + ey * ey);
            double angle = std::atan2(ey, ex);
            if (angle < 0.0) angle += M_PI * 2.0;
            const float radius_index = static_cast<float>(radius - min_r);
            const float angle_index = static_cast<float>(angle / step_rad);

            int xi_raw = static_cast<int>(std::floor(radius_index));
            int yi = static_cast<int>(std::floor(angle_index));
            float fx = radius_index - static_cast<float>(xi_raw);
            float fy = angle_index - static_cast<float>(yi);
            int xi = std::max(0, std::min(xi_raw, radius_count - 1));
            int x1 = std::max(0, std::min(xi_raw + 1, radius_count - 1));
            int y0 = ((yi % angular_count) + angular_count) % angular_count;
            int y1 = (y0 + 1) % angular_count;
            auto sample = [&](int px, int py, int c) -> float {
                return blurred.rgba[(static_cast<size_t>(py) * radius_count + px) * 4 + c];
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
            const size_t dst = (static_cast<size_t>(y) * w + x) * 4;
            for (int c = 0; c < 3; ++c) {
                double rgb = 0.0;
                if (alpha > 1.0e-8) {
                    rgb = (sample(xi, y0, c) * a00 + sample(x1, y0, c) * a10 +
                           sample(xi, y1, c) * a01 + sample(x1, y1, c) * a11) / alpha;
                }
                rgb *= params.brightness_gain;
                out.rgba[dst + c] = static_cast<unsigned char>(clamp_float(static_cast<float>(std::floor(rgb * 255.0 + rgb_quantize_epsilon)), 0.0f, 255.0f));
            }
            out.rgba[dst + 3] = static_cast<unsigned char>(clamp_float(static_cast<float>(std::floor(alpha * 255.0 + alpha_quantize_epsilon)), 0.0f, 255.0f));
        }
    }
    return out;
}

Image render_olmradialblur_rotation(const Image &input, const RadialBlurParams &params) {
    if (params.blur_type != 2) throw std::runtime_error("C++ OLMRadialBlur rotation supports only Blur Type=2");
    if (params.noise_variation != 0.0) throw std::runtime_error("C++ OLMRadialBlur rotation currently does not support Noise Variation");
    if (params.size_variation != 0.0 && !params.ignore_size_variation) {
        throw std::runtime_error("C++ OLMRadialBlur rotation currently does not support Size Variation");
    }

    const int w = input.width;
    const int h = input.height;
    FloatImage src;
    src.width = w;
    src.height = h;
    src.rgba.resize(static_cast<size_t>(w) * h * 4);
    for (size_t i = 0; i < input.rgba.size(); ++i) src.rgba[i] = static_cast<float>(input.rgba[i]) / 255.0f;

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

    const double left = std::max(0.0, -cx);
    const double right = std::max({0.0, cx - static_cast<double>(w), cx <= static_cast<double>(w) / 2.0 ? static_cast<double>(w) - cx : cx});
    const double top = std::max(0.0, -cy);
    const double bottom = std::max({0.0, cy - static_cast<double>(h), cy <= static_cast<double>(h) / 2.0 ? static_cast<double>(h) - cy : cy});
    const int min_r = std::max(0, static_cast<int>(std::sqrt(left * left + top * top) / ratio) - 2);
    const int max_r = static_cast<int>(std::sqrt(std::max(left, right) * std::max(left, right) + std::max(top, bottom) * std::max(top, bottom))) + 2;
    const int radius_count = max_r - min_r + 1;

    FloatImage polar;
    polar.width = angular_count;
    polar.height = radius_count;
    polar.rgba.resize(static_cast<size_t>(radius_count) * angular_count * 4);
    std::vector<uint8_t> polar_valid(static_cast<size_t>(radius_count) * angular_count, 0);
    const double cos_a = std::cos(base_angle);
    const double sin_a = std::sin(base_angle);
    for (int ri = 0; ri < radius_count; ++ri) {
        const double r = static_cast<double>(min_r + ri);
        for (int ai = 0; ai < angular_count; ++ai) {
            const double theta = static_cast<double>(ai) * step_rad;
            const double sx0 = std::cos(theta) * r;
            const double sy0 = std::sin(theta) * r * ratio;
            const float sx = static_cast<float>(cx + cos_a * sx0 - sin_a * sy0);
            const float sy = static_cast<float>(cy + sin_a * sx0 + cos_a * sy0);
            const size_t dst = (static_cast<size_t>(ri) * angular_count + ai) * 4;
            for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = sample_channel(src, sx, sy, c, params.repeat_border);
            polar_valid[static_cast<size_t>(ri) * angular_count + ai] =
                polar_valid_sample(sx, sy, w, h, params.repeat_border, params.polar_valid_mode);
        }
    }

    const bool variable_offset = params.outer_offset != 0 || params.inner_offset != 0;
    const int outer_length = rotation_effective_length(params.outer_strength, params.outer_offset_mode, 0);
    const int inner_length = rotation_effective_length(params.inner_strength, params.inner_offset_mode, 0);
    const bool has_inner = params.inner_strength != 0 || params.inner_offset != 0;
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

    if (params.inner_source_scatter_prepass && has_inner) {
        FloatImage accum;
        accum.width = angular_count;
        accum.height = radius_count;
        accum.rgba.assign(static_cast<size_t>(radius_count) * angular_count * 4, 0.0f);
        std::vector<float> max_alpha(static_cast<size_t>(radius_count) * angular_count, 0.0f);
        std::vector<float> source_alpha(static_cast<size_t>(radius_count) * angular_count, 0.0f);
        std::vector<float> source_scale(static_cast<size_t>(radius_count) * angular_count, 1.0f);
        FloatImage source_rgba = polar;
        std::map<int, std::vector<float>> weight_cache;

        for (int ri = 0; ri < radius_count; ++ri) {
            for (int ai = 0; ai < angular_count; ++ai) {
                const size_t cell = static_cast<size_t>(ri) * angular_count + ai;
                const size_t dst = cell * 4;
                if (!polar_valid[cell]) continue;
                const float alpha = polar.rgba[dst + 3];
                if (alpha <= 0.0f) continue;
                if (params.inner_scatter_rgb_mode == "prepass-premul") {
                    for (int c = 0; c < 3; ++c) source_rgba.rgba[dst + c] = polar.rgba[dst + c] * alpha;
                    source_rgba.rgba[dst + 3] = alpha;
                }
                if (params.inner_scatter_seed_mode == "source") {
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
                const int outer_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, params.outer_offset, ri, params.dynamic_offset_mode);
                const int inner_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, params.inner_offset, ri, params.dynamic_offset_mode);
                int row_outer_span = rotation_scatter_span(params.outer_strength, params.outer_offset_mode, outer_dynamic_offset);
                int row_inner_span = rotation_scatter_span(params.inner_strength, params.inner_offset_mode, inner_dynamic_offset);
                if (params.inner_prepass_span_mode == "offset") {
                    row_outer_span = std::max(0, std::min(outer_dynamic_offset, 3000));
                    row_inner_span = std::max(0, std::min(inner_dynamic_offset, 3000));
                } else if (params.inner_prepass_span_mode == "edge-fade") {
                    row_outer_span = std::max(0, std::min(params.outer_edge_fade, 3000));
                    row_inner_span = std::max(0, std::min(params.inner_edge_fade, 3000));
                }
                const int outer_table_span = row_outer_span;
                const int inner_table_span = row_inner_span;
                for (int ai = 0; ai < angular_count; ++ai) {
                    const size_t cell = static_cast<size_t>(ri) * angular_count + ai;
                    const float base_alpha = polar.rgba[cell * 4 + 3];
                    if (!polar_valid[cell] || base_alpha <= 0.0f) continue;
                    int effective_outer_span = row_outer_span;
                    int effective_inner_span = row_inner_span;
                    if (params.inner_prepass_weight_mode == "aex-alpha") {
                        effective_outer_span = std::max(0, std::min(static_cast<int>(static_cast<float>(row_outer_span) * base_alpha), 3000));
                        effective_inner_span = std::max(0, std::min(static_cast<int>(static_cast<float>(row_inner_span) * base_alpha), 3000));
                    }

                    float weighted_alpha = base_alpha;
                    float weight_sum = 1.0f;
                    for (int offset = 1; offset < effective_outer_span; ++offset) {
                        const int src_ai = positive_mod(ai - offset, angular_count);
                        const size_t src_cell = static_cast<size_t>(ri) * angular_count + src_ai;
                        const float weight = params.inner_prepass_weight_mode == "aex-alpha"
                            ? rotation_gaussian_weight_at_scaled(outer_table_span, offset, base_alpha)
                            : rotation_gaussian_weight_at(row_outer_span, offset);
                        weighted_alpha += polar.rgba[src_cell * 4 + 3] * weight;
                        weight_sum += weight;
                    }
                    for (int offset = 1; offset < effective_inner_span; ++offset) {
                        const int src_ai = positive_mod(ai + offset, angular_count);
                        const size_t src_cell = static_cast<size_t>(ri) * angular_count + src_ai;
                        const float weight = params.inner_prepass_weight_mode == "aex-alpha"
                            ? rotation_gaussian_weight_at_scaled(inner_table_span, offset, base_alpha)
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
                    if (alpha <= 0.0f) continue;
                    source_alpha[cell] = alpha;
                    source_scale[cell] = 1.0f;
                    if (params.inner_scatter_seed_mode == "source" &&
                        params.inner_seed_alpha_mode == "prepass") {
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
        }

        auto weights_for_span = [&](int span) -> const std::vector<float> & {
            auto it = weight_cache.find(span);
            if (it == weight_cache.end()) {
                it = weight_cache.emplace(span, rotation_gaussian_weights(span)).first;
            }
            return it->second;
        };

        auto scatter_one = [&](int ri, int ai, int span, bool inner) {
            if (span <= 1) return;
            const size_t src_cell = static_cast<size_t>(ri) * angular_count + ai;
            if (!polar_valid[src_cell] || source_alpha[src_cell] == 0.0f || source_scale[src_cell] == 0.0f) return;
            int effective_span = span;
            if (params.inner_scatter_span_scale_mode == "source-alpha") {
                effective_span = static_cast<int>(static_cast<float>(span) * source_alpha[src_cell]);
            } else if (params.inner_scatter_span_scale_mode == "input-alpha") {
                effective_span = static_cast<int>(static_cast<float>(span) * polar.rgba[src_cell * 4 + 3]);
            }
            effective_span = std::max(0, std::min(effective_span, 3000));
            if (effective_span <= 1) return;
            const std::vector<float> &row_weights = weights_for_span(effective_span);
            const size_t src_idx = src_cell * 4;
            for (int offset = 1; offset < effective_span && offset < static_cast<int>(row_weights.size()); ++offset) {
                int dst_ri = ri;
                int dst_ai = 0;
                if (inner) {
                    const int raw_ai = ai - offset;
                    if (params.inner_wrap_mode == "aex-next-row" && raw_ai < 0) {
                        dst_ri = ri + ((-raw_ai - 1) / angular_count) + 1;
                        dst_ai = angular_count - 1 - ((-raw_ai - 1) % angular_count);
                    } else {
                        dst_ai = positive_mod(raw_ai, angular_count);
                    }
                } else {
                    dst_ai = positive_mod(ai + offset, angular_count);
                }
                if (dst_ri < 0 || dst_ri >= radius_count) continue;
                const size_t dst_cell = static_cast<size_t>(dst_ri) * angular_count + dst_ai;
                const size_t dst = dst_cell * 4;
                const float contribution = source_alpha[src_cell] * source_scale[src_cell] *
                                           row_weights[static_cast<size_t>(offset)];
                if (contribution <= 0.0f) continue;
                for (int c = 0; c < 3; ++c) accum.rgba[dst + c] += source_rgba.rgba[src_idx + c] * contribution;
                accum.rgba[dst + 3] += contribution;
                max_alpha[dst_cell] = std::max(max_alpha[dst_cell], contribution);
            }
        };

        for (int ri = 0; ri < radius_count; ++ri) {
            const int outer_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, params.outer_offset, ri, params.dynamic_offset_mode);
            const int inner_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, params.inner_offset, ri, params.dynamic_offset_mode);
            const int row_outer_span = rotation_scatter_span(params.outer_strength, params.outer_offset_mode, outer_dynamic_offset);
            const int row_inner_span = rotation_scatter_span(params.inner_strength, params.inner_offset_mode, inner_dynamic_offset);
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
            const int outer_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, params.outer_offset, ri, params.dynamic_offset_mode);
            const int inner_dynamic_offset = dynamic_offset_for_radius(radius_count, min_r, params.inner_offset, ri, params.dynamic_offset_mode);
            const int row_outer_length = rotation_effective_length(params.outer_strength, params.outer_offset_mode, outer_dynamic_offset);
            const int row_inner_length = rotation_effective_length(params.inner_strength, params.inner_offset_mode, inner_dynamic_offset);
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

    Image out;
    out.width = w;
    out.height = h;
    out.rgba.resize(static_cast<size_t>(w) * h * 4);
    const double alpha_quantize_epsilon = 1.0e-4;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const double dx = static_cast<double>(x) - cx;
            const double dy = static_cast<double>(y) - cy;
            const double ex = cos_a * dx + sin_a * dy;
            const double ey = (cos_a * dy - sin_a * dx) / ratio;
            const double radius = std::sqrt(ex * ex + ey * ey);
            double angle = std::atan2(ey, ex);
            if (angle < 0.0) angle += M_PI * 2.0;
            const float angle_index = static_cast<float>(angle / step_rad);
            const float radius_index = static_cast<float>(radius - min_r);

            int xi = static_cast<int>(std::floor(angle_index));
            int yi_raw = static_cast<int>(std::floor(radius_index));
            float fx = angle_index - static_cast<float>(xi);
            float fy = radius_index - static_cast<float>(yi_raw);
            int x0 = ((xi % angular_count) + angular_count) % angular_count;
            int x1 = (x0 + 1) % angular_count;
            int y0 = std::max(0, std::min(yi_raw, radius_count - 1));
            int y1 = std::max(0, std::min(yi_raw + 1, radius_count - 1));
            auto sample = [&](int px, int py, int c) -> float {
                return blurred.rgba[(static_cast<size_t>(py) * angular_count + px) * 4 + c];
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
            const size_t dst = (static_cast<size_t>(y) * w + x) * 4;
            for (int c = 0; c < 3; ++c) {
                double rgb = 0.0;
                if (alpha > 1.0e-8) {
                    rgb = (sample(x0, y0, c) * a00 + sample(x1, y0, c) * a10 +
                           sample(x0, y1, c) * a01 + sample(x1, y1, c) * a11) / alpha;
                }
                rgb *= params.brightness_gain;
                out.rgba[dst + c] = static_cast<unsigned char>(clamp_float(static_cast<float>(std::floor(rgb * 255.0)), 0.0f, 255.0f));
            }
            out.rgba[dst + 3] = static_cast<unsigned char>(clamp_float(static_cast<float>(std::floor(alpha * 255.0 + alpha_quantize_epsilon)), 0.0f, 255.0f));
        }
    }
    return out;
}

struct Args {
    std::string input;
    std::string params;
    std::string output;
    bool ignore_size_variation = false;
    std::string inner_alpha_mode = "max";
    bool inner_source_scatter_prepass = false;
    std::string inner_prepass_mode = "simple";
    std::string inner_prepass_span_mode = "strength";
    std::string inner_prepass_weight_mode = "row-span";
    std::string inner_scatter_rgb_mode = "straight";
    std::string inner_scatter_seed_mode = "source";
    std::string inner_seed_alpha_mode = "input";
    std::string inner_final_alpha_mode = "max";
    std::string inner_rgb_denominator_mode = "accum";
    std::string inner_scatter_span_scale_mode = "one";
    std::string inner_wrap_mode = "circular";
    std::string inner_source_scale_mode = "one";
    std::string dynamic_offset_mode = "current";
    std::string polar_valid_mode = "strict";
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
        } else if (key == "--inner-scatter-rgb-mode") {
            args.inner_scatter_rgb_mode = need_value("--inner-scatter-rgb-mode");
            if (args.inner_scatter_rgb_mode != "straight" && args.inner_scatter_rgb_mode != "prepass-premul") {
                throw std::runtime_error("--inner-scatter-rgb-mode must be straight or prepass-premul");
            }
        } else if (key == "--inner-scatter-seed-mode") {
            args.inner_scatter_seed_mode = need_value("--inner-scatter-seed-mode");
            if (args.inner_scatter_seed_mode != "source" && args.inner_scatter_seed_mode != "none") {
                throw std::runtime_error("--inner-scatter-seed-mode must be source or none");
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
        } else if (key == "--inner-alpha-mode") {
            args.inner_alpha_mode = need_value("--inner-alpha-mode");
            if (args.inner_alpha_mode != "max" && args.inner_alpha_mode != "sum" &&
                args.inner_alpha_mode != "outer" && args.inner_alpha_mode != "inner" &&
                args.inner_alpha_mode != "input") {
                throw std::runtime_error("--inner-alpha-mode must be max, sum, outer, inner, or input");
            }
        } else if (key == "--help" || key == "-h") {
            std::printf("Usage: olmradialblur_cli --input in.png --params params.json --output out.png [--ignore-size-variation] [--inner-alpha-mode max|sum|outer|inner|input] [--inner-source-scatter-prepass] [--inner-prepass-mode simple|tail-gather] [--inner-prepass-span-mode strength|offset|edge-fade] [--inner-prepass-weight-mode row-span|aex-alpha] [--inner-scatter-rgb-mode straight|prepass-premul] [--inner-scatter-seed-mode source|none] [--inner-seed-alpha-mode input|prepass] [--inner-final-alpha-mode max|denom|source] [--inner-rgb-denominator-mode accum|max] [--inner-scatter-span-scale-mode one|source-alpha|input-alpha] [--inner-wrap-mode circular|aex-next-row] [--inner-source-scale-mode one|alpha|inv-alpha] [--dynamic-offset-mode current|aex-row|min-radius] [--polar-valid-mode strict|aex-repeat]\n");
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
        params.inner_prepass_mode = args.inner_prepass_mode;
        params.inner_prepass_span_mode = args.inner_prepass_span_mode;
        params.inner_prepass_weight_mode = args.inner_prepass_weight_mode;
        params.inner_scatter_rgb_mode = args.inner_scatter_rgb_mode;
        params.inner_scatter_seed_mode = args.inner_scatter_seed_mode;
        params.inner_seed_alpha_mode = args.inner_seed_alpha_mode;
        params.inner_final_alpha_mode = args.inner_final_alpha_mode;
        params.inner_rgb_denominator_mode = args.inner_rgb_denominator_mode;
        params.inner_scatter_span_scale_mode = args.inner_scatter_span_scale_mode;
        params.inner_wrap_mode = args.inner_wrap_mode;
        params.inner_source_scale_mode = args.inner_source_scale_mode;
        params.dynamic_offset_mode = args.dynamic_offset_mode;
        params.polar_valid_mode = args.polar_valid_mode;
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
