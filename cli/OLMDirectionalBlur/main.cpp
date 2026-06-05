#include <png.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cctype>
#include <cstdio>
#include <cstdlib>
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

struct FloatImage {
    int width = 0;
    int height = 0;
    std::vector<float> rgba;
};

struct ComponentInfo {
    float area = 0.0f;
    float min_y = 0.0f;
    float center_y = 0.0f;
    float half_height = 1.0f;
};

struct ComponentMap {
    int width = 0;
    int height = 0;
    float max_area = 1.0f;
    std::vector<ComponentInfo> pixels;
};

struct DirectionalBlurParams {
    double angle = 0.0;
    double brightness_gain = 1.0;
    double size_variation = 0.0;
    int front_strength = 0;
    int front_alpha_fade = 0;
    double front_sharp_tail = 0.0;
    int back_strength = 0;
    int back_alpha_fade = 0;
    double back_sharp_tail = 0.0;
    double noise_variation = 0.0;
    double frame_rate = 0.0;
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
        if (text_.compare(pos_, expected.size(), expected) != 0) throw std::runtime_error("invalid JSON literal");
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
            case 'u': append_utf8(parse_hex4(), value.string_value); break;
            default: throw std::runtime_error("invalid JSON escape");
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

std::string key_for_name(const std::string &name) {
    std::string key;
    for (char c : name) key.push_back(c == ' ' ? '_' : static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
    return key;
}

std::map<std::string, const Json *> grouped_param_map(const Json &root) {
    const Json *scope = &root;
    if (const Json *params = root.get("params")) scope = params;
    const Json *effects = scope->get("effects");
    if (!effects || effects->type != Json::Array) return {};

    std::map<std::string, const Json *> out;
    for (const Json &effect : effects->array_value) {
        const Json *name = effect.get("name");
        const Json *match = effect.get("match_name");
        bool target = false;
        if (name && name->type == Json::String && name->string_value == "OLM DirectionalBlur") target = true;
        if (match && match->type == Json::String && match->string_value == "OLM Directional Blur") target = true;
        if (!target) continue;

        const Json *params = effect.get("params");
        if (!params || params->type != Json::Array) continue;
        std::string group = "root";
        int front_sharp_tail = 0;
        int back_sharp_tail = 0;
        for (const Json &param : params->array_value) {
            const Json *param_name = param.get("name");
            if (!param_name || param_name->type != Json::String) continue;
            const std::string &pname = param_name->string_value;
            if (pname == "Front Blur Parameters") {
                group = "front";
                continue;
            }
            if (pname == "Back Blur Parameters") {
                group = "back";
                continue;
            }
            if (pname == "Noise Parameters") {
                group = "noise";
                continue;
            }
            const Json *value = param.get("value");
            if (!value || value->type == Json::Null) continue;
            std::string key = key_for_name(pname);
            if ((group == "front" || group == "back") && (pname == "Blur Strength" || pname == "Alpha Fade")) {
                key = group + "_" + key;
            } else if (group == "front" && pname == "Sharp Tail") {
                key = "front_sharp_tail_" + std::to_string(++front_sharp_tail);
            } else if (group == "back" && pname == "Sharp Tail") {
                key = "back_sharp_tail_" + std::to_string(++back_sharp_tail);
            } else if (group == "noise" && pname == "Offset") {
                key = "noise_offset";
            }
            out[key] = value;
        }
    }
    return out;
}

DirectionalBlurParams read_params(const std::string &path) {
    Json root = JsonParser(read_text_file(path)).parse();
    auto params = grouped_param_map(root);
    auto get = [&](const char *name) -> const Json * {
        auto it = params.find(name);
        return it == params.end() ? nullptr : it->second;
    };

    DirectionalBlurParams dp;
    dp.angle = json_number_or(get("angle"), 0.0);
    dp.brightness_gain = json_number_or(get("brightness_gain"), 1.0);
    dp.size_variation = json_number_or(get("size_variation"), 0.0) / 100.0;
    dp.front_strength = static_cast<int>(json_number_or(get("front_blur_strength"), 0.0));
    dp.front_alpha_fade = static_cast<int>(json_number_or(get("front_alpha_fade"), 0.0));
    dp.front_sharp_tail = json_number_or(get("front_sharp_tail_1"), 0.0) / 100.0;
    dp.back_strength = static_cast<int>(json_number_or(get("back_blur_strength"), 0.0));
    dp.back_alpha_fade = static_cast<int>(json_number_or(get("back_alpha_fade"), 0.0));
    dp.back_sharp_tail = json_number_or(get("back_sharp_tail_1"), 0.0) / 100.0;
    dp.noise_variation = json_number_or(get("noise_variation"), 0.0);
    if (const Json *comp = root.get("comp")) dp.frame_rate = json_number_or(comp->get("frame_rate"), 0.0);
    return dp;
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

std::vector<float> gaussian_weights(int length) {
    length = std::max(length, 1);
    std::vector<float> weights(static_cast<size_t>(length), 1.0f);
    const float denom = 2.0f * (static_cast<float>(length) / 0.5f) * (static_cast<float>(length) / 0.5f) + 1.0e-5f;
    for (int i = 0; i < length; ++i) weights[static_cast<size_t>(i)] = std::exp(-(static_cast<float>(i * i)) / denom);
    return weights;
}

void sample_bilinear(const Image &image, float x, float y, float out[4]) {
    const int w = image.width;
    const int h = image.height;
    if (x < 0.0f || x > static_cast<float>(w - 1) || y < 0.0f || y > static_cast<float>(h - 1)) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    int x1 = std::min(x0 + 1, w - 1);
    int y1 = std::min(y0 + 1, h - 1);
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    const size_t i00 = (static_cast<size_t>(y0) * w + x0) * 4;
    const size_t i10 = (static_cast<size_t>(y0) * w + x1) * 4;
    const size_t i01 = (static_cast<size_t>(y1) * w + x0) * 4;
    const size_t i11 = (static_cast<size_t>(y1) * w + x1) * 4;
    for (int c = 0; c < 4; ++c) {
        float c00 = static_cast<float>(image.rgba[i00 + c]) / 255.0f;
        float c10 = static_cast<float>(image.rgba[i10 + c]) / 255.0f;
        float c01 = static_cast<float>(image.rgba[i01 + c]) / 255.0f;
        float c11 = static_cast<float>(image.rgba[i11 + c]) / 255.0f;
        float top = c00 * (1.0f - fx) + c10 * fx;
        float bottom = c01 * (1.0f - fx) + c11 * fx;
        out[c] = top * (1.0f - fy) + bottom * fy;
    }
}

void sample_bilinear(const FloatImage &image, float x, float y, float out[4]) {
    const int w = image.width;
    const int h = image.height;
    if (x < 0.0f || x > static_cast<float>(w - 1) || y < 0.0f || y > static_cast<float>(h - 1)) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    int x1 = std::min(x0 + 1, w - 1);
    int y1 = std::min(y0 + 1, h - 1);
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    const size_t i00 = (static_cast<size_t>(y0) * w + x0) * 4;
    const size_t i10 = (static_cast<size_t>(y0) * w + x1) * 4;
    const size_t i01 = (static_cast<size_t>(y1) * w + x0) * 4;
    const size_t i11 = (static_cast<size_t>(y1) * w + x1) * 4;
    for (int c = 0; c < 4; ++c) {
        float top = image.rgba[i00 + c] * (1.0f - fx) + image.rgba[i10 + c] * fx;
        float bottom = image.rgba[i01 + c] * (1.0f - fx) + image.rgba[i11 + c] * fx;
        out[c] = top * (1.0f - fy) + bottom * fy;
    }
}

void sample_bilinear_strict(const Image &image, float x, float y, float out[4]) {
    const int w = image.width;
    const int h = image.height;
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    if (x0 <= 0 || x0 >= w - 1 || y0 <= 0 || y0 >= h - 1) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x1 = x0 + 1;
    int y1 = y0 + 1;
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    const size_t i00 = (static_cast<size_t>(y0) * w + x0) * 4;
    const size_t i10 = (static_cast<size_t>(y0) * w + x1) * 4;
    const size_t i01 = (static_cast<size_t>(y1) * w + x0) * 4;
    const size_t i11 = (static_cast<size_t>(y1) * w + x1) * 4;
    for (int c = 0; c < 4; ++c) {
        float c00 = static_cast<float>(image.rgba[i00 + c]) / 255.0f;
        float c10 = static_cast<float>(image.rgba[i10 + c]) / 255.0f;
        float c01 = static_cast<float>(image.rgba[i01 + c]) / 255.0f;
        float c11 = static_cast<float>(image.rgba[i11 + c]) / 255.0f;
        float top = c00 * (1.0f - fx) + c10 * fx;
        float bottom = c01 * (1.0f - fx) + c11 * fx;
        out[c] = top * (1.0f - fy) + bottom * fy;
    }
}

void sample_bilinear_strict(const FloatImage &image, float x, float y, float out[4]) {
    const int w = image.width;
    const int h = image.height;
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    if (x0 <= 0 || x0 >= w - 1 || y0 <= 0 || y0 >= h - 1) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x1 = x0 + 1;
    int y1 = y0 + 1;
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    const size_t i00 = (static_cast<size_t>(y0) * w + x0) * 4;
    const size_t i10 = (static_cast<size_t>(y0) * w + x1) * 4;
    const size_t i01 = (static_cast<size_t>(y1) * w + x0) * 4;
    const size_t i11 = (static_cast<size_t>(y1) * w + x1) * 4;
    for (int c = 0; c < 4; ++c) {
        float top = image.rgba[i00 + c] * (1.0f - fx) + image.rgba[i10 + c] * fx;
        float bottom = image.rgba[i01 + c] * (1.0f - fx) + image.rgba[i11 + c] * fx;
        out[c] = top * (1.0f - fy) + bottom * fy;
    }
}

void sample_bilinear_alpha_weighted(const Image &image, float x, float y, float out[4]) {
    const int w = image.width;
    const int h = image.height;
    if (x < 0.0f || x > static_cast<float>(w - 1) || y < 0.0f || y > static_cast<float>(h - 1)) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    if (x0 <= 0 || x0 >= w - 1 || y0 <= 0 || y0 >= h - 1) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x1 = std::min(x0 + 1, w - 1);
    int y1 = std::min(y0 + 1, h - 1);
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    const size_t idx[4] = {
        (static_cast<size_t>(y0) * w + x0) * 4,
        (static_cast<size_t>(y0) * w + x1) * 4,
        (static_cast<size_t>(y1) * w + x0) * 4,
        (static_cast<size_t>(y1) * w + x1) * 4,
    };
    const float wt[4] = {
        (1.0f - fx) * (1.0f - fy),
        fx * (1.0f - fy),
        (1.0f - fx) * fy,
        fx * fy,
    };
    float alpha_sum = 0.0f;
    float rgb_sum[3] = {0.0f, 0.0f, 0.0f};
    for (int i = 0; i < 4; ++i) {
        const float alpha = static_cast<float>(image.rgba[idx[i] + 3]) / 255.0f;
        const float aw = wt[i] * alpha;
        alpha_sum += aw;
        for (int c = 0; c < 3; ++c) {
            rgb_sum[c] += (static_cast<float>(image.rgba[idx[i] + c]) / 255.0f) * aw;
        }
    }
    if (alpha_sum > 1.0e-8f) {
        for (int c = 0; c < 3; ++c) out[c] = rgb_sum[c] / alpha_sum;
    } else {
        out[0] = out[1] = out[2] = 0.0f;
    }
    out[3] = alpha_sum;
}

void sample_bilinear_alpha_weighted(const FloatImage &image, float x, float y, float out[4]) {
    const int w = image.width;
    const int h = image.height;
    if (x < 0.0f || x > static_cast<float>(w - 1) || y < 0.0f || y > static_cast<float>(h - 1)) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    if (x0 <= 0 || x0 >= w - 1 || y0 <= 0 || y0 >= h - 1) {
        out[0] = out[1] = out[2] = out[3] = 0.0f;
        return;
    }
    int x1 = std::min(x0 + 1, w - 1);
    int y1 = std::min(y0 + 1, h - 1);
    float fx = x - static_cast<float>(x0);
    float fy = y - static_cast<float>(y0);
    const size_t idx[4] = {
        (static_cast<size_t>(y0) * w + x0) * 4,
        (static_cast<size_t>(y0) * w + x1) * 4,
        (static_cast<size_t>(y1) * w + x0) * 4,
        (static_cast<size_t>(y1) * w + x1) * 4,
    };
    const float wt[4] = {
        (1.0f - fx) * (1.0f - fy),
        fx * (1.0f - fy),
        (1.0f - fx) * fy,
        fx * fy,
    };
    float alpha_sum = 0.0f;
    float rgb_sum[3] = {0.0f, 0.0f, 0.0f};
    for (int i = 0; i < 4; ++i) {
        const float alpha = image.rgba[idx[i] + 3];
        const float aw = wt[i] * alpha;
        alpha_sum += aw;
        for (int c = 0; c < 3; ++c) rgb_sum[c] += image.rgba[idx[i] + c] * aw;
    }
    if (alpha_sum > 1.0e-8f) {
        for (int c = 0; c < 3; ++c) out[c] = rgb_sum[c] / alpha_sum;
    } else {
        out[0] = out[1] = out[2] = 0.0f;
    }
    out[3] = alpha_sum;
}

unsigned char quantize(float value) {
    value = std::clamp(value, 0.0f, 1.0f) * 255.0f;
    return static_cast<unsigned char>(std::floor(value + 0.5f));
}

unsigned char quantize_trunc(float value) {
    value = std::clamp(value, 0.0f, 1.0f) * 255.0f;
    return static_cast<unsigned char>(std::floor(value));
}

ComponentMap build_component_map_from_alpha(const FloatImage &image, bool exact_half_height = false) {
    const int w = image.width;
    const int h = image.height;
    const int pixels = w * h;
    ComponentMap map;
    map.width = w;
    map.height = h;
    map.pixels.resize(static_cast<size_t>(pixels));

    std::vector<unsigned char> visited(static_cast<size_t>(pixels), 0);
    std::vector<int> stack;
    std::vector<int> component_pixels;
    stack.reserve(1024);
    component_pixels.reserve(1024);

    for (int start = 0; start < pixels; ++start) {
        if (visited[static_cast<size_t>(start)]) continue;
        visited[static_cast<size_t>(start)] = 1;
        if (image.rgba[static_cast<size_t>(start) * 4 + 3] <= 0.0f) continue;

        stack.clear();
        component_pixels.clear();
        stack.push_back(start);
        int min_y = h;
        int max_y = -1;
        while (!stack.empty()) {
            int p = stack.back();
            stack.pop_back();
            component_pixels.push_back(p);
            const int x = p % w;
            const int y = p / w;
            min_y = std::min(min_y, y);
            max_y = std::max(max_y, y);

            const int neighbors[4] = {p - 1, p + 1, p - w, p + w};
            for (int n : neighbors) {
                if (n < 0 || n >= pixels) continue;
                if ((n == p - 1 && x == 0) || (n == p + 1 && x == w - 1)) continue;
                if (visited[static_cast<size_t>(n)]) continue;
                visited[static_cast<size_t>(n)] = 1;
                if (image.rgba[static_cast<size_t>(n) * 4 + 3] > 0.0f) stack.push_back(n);
            }
        }

        ComponentInfo info;
        info.area = static_cast<float>(component_pixels.size());
        info.min_y = static_cast<float>(min_y);
        info.center_y = static_cast<float>((min_y + max_y) / 2);
        info.half_height = static_cast<float>(max_y) - info.center_y;
        if (!exact_half_height) info.half_height = std::max(info.half_height, 1.0f);
        map.max_area = std::max(map.max_area, info.area);
        for (int p : component_pixels) map.pixels[static_cast<size_t>(p)] = info;
    }
    return map;
}

Image render_direct(const Image &input, const DirectionalBlurParams &params, double strength_scale,
                    double angle_sign, double sample_sign, const std::string &rgb_normalize,
                    bool component_map_coeff = false, bool include_back = false,
                    bool ignore_noise_variation = false) {
    if (params.noise_variation != 0.0 && !ignore_noise_variation) throw std::runtime_error("noise variation is not implemented");
    if (params.back_strength != 0 && !include_back) throw std::runtime_error("back blur is not implemented; pass --direction both to probe it");

    const int w = input.width;
    const int h = input.height;
    const int pixels = w * h;
    Image out;
    out.width = w;
    out.height = h;
    out.rgba.resize(static_cast<size_t>(pixels) * 4);

    if (strength_scale < 0.0) {
        strength_scale = params.frame_rate > 0.0 ? 1.0 / params.frame_rate : 1.0;
    }
    const int front_strength = static_cast<int>(static_cast<double>(params.front_strength) * strength_scale);
    const int back_strength = include_back ? static_cast<int>(static_cast<double>(params.back_strength) * strength_scale) : 0;
    const double angle = params.angle * angle_sign * M_PI / 180.0;
    const float vx = static_cast<float>(std::cos(angle));
    const float vy = static_cast<float>(std::sin(angle));
    const float center = (static_cast<float>(h) - 1.0f) * 0.5f;
    const float span = std::max(center, 1.0f);
    FloatImage float_input;
    ComponentMap component_map;
    if (component_map_coeff) {
        float_input.width = w;
        float_input.height = h;
        float_input.rgba.resize(static_cast<size_t>(pixels) * 4, 0.0f);
        for (int p = 0; p < pixels; ++p) {
            const size_t src = static_cast<size_t>(p) * 4;
            for (int c = 0; c < 4; ++c) {
                float_input.rgba[src + c] = static_cast<float>(input.rgba[src + c]) / 255.0f;
            }
        }
        component_map = build_component_map_from_alpha(float_input);
    }

    std::vector<float> accum_rgb(static_cast<size_t>(pixels) * 3, 0.0f);
    std::vector<float> accum_sum(static_cast<size_t>(pixels), 0.0f);
    std::vector<float> accum_alpha(static_cast<size_t>(pixels), 0.0f);

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const int p = y * w + x;
            const size_t src = static_cast<size_t>(p) * 4;
            float a = static_cast<float>(input.rgba[src + 3]) / 255.0f;
            for (int c = 0; c < 3; ++c) {
                accum_rgb[static_cast<size_t>(p) * 3 + c] = (static_cast<float>(input.rgba[src + c]) / 255.0f) * a;
            }
            accum_sum[static_cast<size_t>(p)] = a;
            accum_alpha[static_cast<size_t>(p)] = a;
        }
    }

    auto apply_one_sided = [&](int strength, double sharp_tail, double sign) {
        if (strength <= 1) return;
        const std::vector<float> weights = gaussian_weights(std::max(strength, 1));
        for (int i = 1; i < strength; ++i) {
            const float base_weight = weights[static_cast<size_t>(i)];
            for (int y = 0; y < h; ++y) {
                float tail = 1.0f;
                if (sharp_tail > 0.0) {
                    tail = std::max(0.0f, 1.0f - std::fabs(static_cast<float>(y) - center) * static_cast<float>(sharp_tail) / span);
                    if (static_cast<float>(i) >= static_cast<float>(strength) * tail) continue;
                }
                int idx = i;
                if (sharp_tail > 0.0) {
                    idx = std::clamp(static_cast<int>(static_cast<float>(i) / std::max(tail, 1.0e-6f)), 0, strength - 1);
                }
                const float weight = sharp_tail > 0.0 ? weights[static_cast<size_t>(idx)] : base_weight;
                for (int x = 0; x < w; ++x) {
                    const float sample_x = static_cast<float>(x) + static_cast<float>(sign * sample_sign) * vx * static_cast<float>(i);
                    const float sample_y = static_cast<float>(y) + static_cast<float>(sign * sample_sign) * vy * static_cast<float>(i);
                    float local_weight = weight;
                    if (component_map_coeff) {
                        const int sx = static_cast<int>(std::floor(sample_x + 0.5f));
                        const int sy = static_cast<int>(std::floor(sample_y + 0.5f));
                        if (sx < 0 || sx >= w || sy < 0 || sy >= h) continue;
                        const ComponentInfo &comp = component_map.pixels[static_cast<size_t>(sy * w + sx)];
                        if (comp.area <= 0.0f) continue;
                        const float area_factor = std::pow(std::clamp(comp.area / component_map.max_area, 0.0f, 1.0f),
                                                           static_cast<float>(params.size_variation));
                        float tail_factor = 1.0f;
                        if (sharp_tail > 0.0) {
                            tail_factor = std::max(0.0f, 1.0f - std::fabs(static_cast<float>(sy) - comp.center_y) *
                                                            static_cast<float>(sharp_tail) / comp.half_height);
                        }
                        const float coeff = area_factor * tail_factor;
                        if (coeff <= 0.0f || static_cast<float>(i) >= static_cast<float>(strength) * coeff) continue;
                        const int local_idx = std::clamp(static_cast<int>(static_cast<float>(i) / std::max(coeff, 1.0e-6f)),
                                                         0, strength - 1);
                        local_weight = weights[static_cast<size_t>(local_idx)];
                    }
                    float sample[4];
                    sample_bilinear(input, sample_x, sample_y, sample);
                    float alpha = sample[3] * local_weight;
                    if (params.size_variation != 0.0 && !component_map_coeff) {
                        alpha *= std::pow(std::clamp(sample[3], 0.0f, 1.0f), static_cast<float>(params.size_variation));
                    }
                    const int p = y * w + x;
                    for (int c = 0; c < 3; ++c) {
                        accum_rgb[static_cast<size_t>(p) * 3 + c] += sample[c] * alpha;
                    }
                    accum_sum[static_cast<size_t>(p)] += alpha;
                    accum_alpha[static_cast<size_t>(p)] = std::max(accum_alpha[static_cast<size_t>(p)], alpha);
                }
            }
        }
    };

    apply_one_sided(front_strength, params.front_sharp_tail, 1.0);
    apply_one_sided(back_strength, params.back_sharp_tail, -1.0);

    float kernel_sum = 0.0f;
    for (float weight : gaussian_weights(std::max(front_strength, 1))) kernel_sum += weight;
    for (int p = 0; p < pixels; ++p) {
        float denom = accum_sum[static_cast<size_t>(p)];
        if (rgb_normalize == "front-strength") denom = std::max(static_cast<float>(front_strength), 1.0f);
        else if (rgb_normalize == "total-strength") denom = std::max(static_cast<float>(front_strength + back_strength), 1.0f);
        else if (rgb_normalize == "kernel-sum") denom = std::max(kernel_sum, 1.0e-8f);
        const size_t dst = static_cast<size_t>(p) * 4;
        for (int c = 0; c < 3; ++c) {
            float rgb = denom > 1.0e-8f ? accum_rgb[static_cast<size_t>(p) * 3 + c] / denom : 0.0f;
            out.rgba[dst + c] = quantize(rgb * static_cast<float>(params.brightness_gain));
        }
        out.rgba[dst + 3] = quantize(accum_alpha[static_cast<size_t>(p)]);
    }
    return out;
}

Image render_rotated(const Image &input, const DirectionalBlurParams &params, double strength_scale,
                     double angle_sign, double sample_sign, bool gather_first,
                     bool alpha_weighted_input_rotate, bool alpha_weighted_output_rotate,
                     bool component_map_coeff, bool premultiply_gather_source, bool use_alpha_fade_gather,
                     bool aex_buffer_init, const std::string &alpha_mode, bool strict_plain_sampler,
                     bool alpha_sum_output = false, bool alpha_coeff_output = false,
                     bool aex_pad_size = false, bool dest_component_coeff = false,
                     bool front_strength_rgb_denom = false, bool rowdriver_prepass = false,
                     bool aex_two_stage_input = false, bool aex_two_stage_output = false,
                     int row_init_mode = -1, bool truncate_component_span = false,
                     bool truncate_output_quantize = false, bool exact_component_half_height = false,
                     bool aex_rotate_math = false) {
    if (params.noise_variation != 0.0) throw std::runtime_error("noise variation is not implemented");
    if (params.back_strength != 0) throw std::runtime_error("back blur is not implemented");

    const int w = input.width;
    const int h = input.height;
    const int pad_w = [&]() {
        if (!aex_pad_size) {
            return static_cast<int>(std::ceil(std::sqrt(static_cast<double>(w * w + h * h)))) + 4;
        }
        const float diag = std::sqrt(static_cast<float>(w * w + h * h));
        const int half_span = 2 - static_cast<int>(diag * -0.5f);
        return w + (half_span - w / 2) * 2;
    }();
    const int pad_h = [&]() {
        if (!aex_pad_size) return pad_w;
        const float diag = std::sqrt(static_cast<float>(w * w + h * h));
        const int half_span = 2 - static_cast<int>(diag * -0.5f);
        return h + (half_span - h / 2) * 2;
    }();
    const int pad_pixels = pad_w * pad_h;

    if (strength_scale < 0.0) {
        strength_scale = params.frame_rate > 0.0 ? 1.0 / params.frame_rate : 1.0;
    }
    const int front_strength = static_cast<int>(static_cast<double>(params.front_strength) * strength_scale);
    const std::vector<float> weights = gaussian_weights(std::max(front_strength, 1));
    const double angle = params.angle * angle_sign * M_PI / 180.0;
    const float angle_f = static_cast<float>(params.angle * angle_sign * M_PI / 180.0);
    const float cos_a = aex_rotate_math ? std::cos(angle_f) : static_cast<float>(std::cos(angle));
    const float sin_a = aex_rotate_math ? std::sin(angle_f) : static_cast<float>(std::sin(angle));

    FloatImage source_canvas;
    source_canvas.width = pad_w;
    source_canvas.height = pad_h;
    source_canvas.rgba.resize(static_cast<size_t>(pad_pixels) * 4, 0.0f);
    if (aex_two_stage_input) {
        const int offset_x = pad_w / 2 - w / 2;
        const int offset_y = pad_h / 2 - h / 2;
        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                const int dx = x + offset_x;
                const int dy = y + offset_y;
                if (dx < 0 || dx >= pad_w || dy < 0 || dy >= pad_h) continue;
                const size_t src = (static_cast<size_t>(y) * w + x) * 4;
                const size_t dst = (static_cast<size_t>(dy) * pad_w + dx) * 4;
                for (int c = 0; c < 4; ++c) {
                    source_canvas.rgba[dst + c] = static_cast<float>(input.rgba[src + c]) / 255.0f;
                }
            }
        }
    }

    FloatImage rotated;
    rotated.width = pad_w;
    rotated.height = pad_h;
    rotated.rgba.resize(static_cast<size_t>(pad_pixels) * 4, 0.0f);
    for (int y = 0; y < pad_h; ++y) {
        for (int x = 0; x < pad_w; ++x) {
            const float dst_cx = aex_rotate_math ? static_cast<float>(pad_w / 2) : static_cast<float>(pad_w) / 2.0f;
            const float dst_cy = aex_rotate_math ? static_cast<float>(pad_h / 2) : static_cast<float>(pad_h) / 2.0f;
            const float src_cx = aex_rotate_math ? static_cast<float>((aex_two_stage_input ? pad_w : w) / 2)
                                                 : static_cast<float>(aex_two_stage_input ? pad_w : w) / 2.0f;
            const float src_cy = aex_rotate_math ? static_cast<float>((aex_two_stage_input ? pad_h : h) / 2)
                                                 : static_cast<float>(aex_two_stage_input ? pad_h : h) / 2.0f;
            const float dx = static_cast<float>(x) - dst_cx;
            const float dy = static_cast<float>(y) - dst_cy;
            const float src_x = dx * cos_a - dy * sin_a + src_cx;
            const float src_y = dx * sin_a + dy * cos_a + src_cy;
            float sample[4];
            if (aex_two_stage_input) {
                if (alpha_weighted_input_rotate) sample_bilinear_alpha_weighted(source_canvas, src_x, src_y, sample);
                else if (strict_plain_sampler) sample_bilinear_strict(source_canvas, src_x, src_y, sample);
                else sample_bilinear(source_canvas, src_x, src_y, sample);
            } else {
                if (alpha_weighted_input_rotate) sample_bilinear_alpha_weighted(input, src_x, src_y, sample);
                else if (strict_plain_sampler) sample_bilinear_strict(input, src_x, src_y, sample);
                else sample_bilinear(input, src_x, src_y, sample);
            }
            const size_t dst = (static_cast<size_t>(y) * pad_w + x) * 4;
            for (int c = 0; c < 4; ++c) rotated.rgba[dst + c] = sample[c];
        }
    }

    ComponentMap component_map;
    if (component_map_coeff || rowdriver_prepass) component_map = build_component_map_from_alpha(rotated, exact_component_half_height);

    std::vector<float> gather_alpha(static_cast<size_t>(pad_pixels), 0.0f);
    int min_valid_y = pad_h;
    int max_valid_y = -1;
    for (int y = 0; y < pad_h; ++y) {
        for (int x = 0; x < pad_w; ++x) {
            const int p = y * pad_w + x;
            const size_t src = static_cast<size_t>(p) * 4;
            const float alpha = rotated.rgba[src + 3];
            if (alpha > 0.0f) {
                min_valid_y = std::min(min_valid_y, y);
                max_valid_y = std::max(max_valid_y, y);
            }
            gather_alpha[static_cast<size_t>(p)] = alpha;
        }
    }

    int front_gather = front_strength;
    int back_gather = 0;
    if (use_alpha_fade_gather) {
        front_gather = static_cast<int>(static_cast<double>(params.front_alpha_fade) * strength_scale);
        back_gather = static_cast<int>(static_cast<double>(params.back_alpha_fade) * strength_scale);
    }

    const std::vector<float> front_gather_weights = gaussian_weights(std::max(front_gather, 1));
    const std::vector<float> back_gather_weights = gaussian_weights(std::max(back_gather, 1));
    if (gather_first && (front_gather > 1 || back_gather > 1)) {
        for (int y = 0; y < pad_h; ++y) {
            for (int x = 0; x < pad_w; ++x) {
                const int p = y * pad_w + x;
                const float center_alpha = rotated.rgba[static_cast<size_t>(p) * 4 + 3];
                if (center_alpha == 0.0f) {
                    gather_alpha[static_cast<size_t>(p)] = 0.0f;
                    continue;
                }
                float alpha_sum = center_alpha;
                float weight_sum = 1.0f;
                const int front_count = std::min(front_gather, pad_w - x);
                for (int i = 1; i < front_count; ++i) {
                    const int sp = y * pad_w + x + i;
                    const float weight = front_gather_weights[static_cast<size_t>(i)];
                    alpha_sum += weight * rotated.rgba[static_cast<size_t>(sp) * 4 + 3];
                    weight_sum += weight;
                }
                const int back_count = std::min(back_gather, x + 1);
                for (int i = 1; i < back_count; ++i) {
                    const int sp = y * pad_w + x - i;
                    const float weight = back_gather_weights[static_cast<size_t>(i)];
                    alpha_sum += weight * rotated.rgba[static_cast<size_t>(sp) * 4 + 3];
                    weight_sum += weight;
                }
                gather_alpha[static_cast<size_t>(p)] = alpha_sum / std::max(weight_sum, 1.0e-8f);
            }
        }
    }

    std::vector<float> accum_rgb(static_cast<size_t>(pad_pixels) * 3, 0.0f);
    std::vector<float> accum_sum(static_cast<size_t>(pad_pixels), 0.0f);
    std::vector<float> accum_alpha(static_cast<size_t>(pad_pixels), 0.0f);
    std::vector<float> source_rgb(static_cast<size_t>(pad_pixels) * 3, 0.0f);
    std::vector<float> source_alpha(static_cast<size_t>(pad_pixels), 0.0f);
    if (row_init_mode < 0) row_init_mode = aex_buffer_init ? 1 : 0;
    for (int p = 0; p < pad_pixels; ++p) {
        const size_t src = static_cast<size_t>(p) * 4;
        float alpha = gather_alpha[static_cast<size_t>(p)];
        if (rowdriver_prepass) {
            const ComponentInfo &comp = component_map.pixels[static_cast<size_t>(p)];
            if (alpha <= 0.0f || comp.area <= 0.0f) {
                alpha = 0.0f;
            } else {
                const float coeff = std::pow(std::clamp(comp.area / component_map.max_area, 0.0f, 1.0f),
                                             static_cast<float>(params.size_variation));
                const float inv_coeff = coeff > 1.0e-8f ? 1.0f / coeff : 1.0f;
                const int x = p % pad_w;
                const int y = p / pad_w;
                const int front_count = std::min(static_cast<int>(static_cast<float>(front_gather) * coeff), pad_w - x);
                const int back_count = std::min(static_cast<int>(static_cast<float>(back_gather) * coeff), x + 1);
                float alpha_sum = rotated.rgba[src + 3];
                float weight_sum = 1.0f;
                for (int i = 1; i < front_count; ++i) {
                    const int idx = std::clamp(static_cast<int>(static_cast<float>(i) * inv_coeff), 0, std::max(front_gather - 1, 0));
                    const float weight = front_gather_weights[static_cast<size_t>(idx)];
                    alpha_sum += rotated.rgba[(static_cast<size_t>(y) * pad_w + (x + i)) * 4 + 3] * weight;
                    weight_sum += weight;
                }
                for (int i = 1; i < back_count; ++i) {
                    const int idx = std::clamp(static_cast<int>(static_cast<float>(i) * inv_coeff), 0, std::max(back_gather - 1, 0));
                    const float weight = back_gather_weights[static_cast<size_t>(idx)];
                    alpha_sum += rotated.rgba[(static_cast<size_t>(y) * pad_w + (x - i)) * 4 + 3] * weight;
                    weight_sum += weight;
                }
                alpha = alpha_sum / std::max(weight_sum, 1.0e-8f);
            }
        }
        source_alpha[static_cast<size_t>(p)] = alpha;
        accum_sum[static_cast<size_t>(p)] = row_init_mode == 0 ? alpha : 0.0f;
        accum_alpha[static_cast<size_t>(p)] = row_init_mode == 3 ? 0.0f : alpha;
        for (int c = 0; c < 3; ++c) {
            const float raw_rgb = rotated.rgba[src + c];
            source_rgb[static_cast<size_t>(p) * 3 + c] =
                gather_first && !premultiply_gather_source ? raw_rgb : raw_rgb * alpha;
            float initial_rgb = 0.0f;
            if (row_init_mode == 0 || row_init_mode == 2) initial_rgb = raw_rgb * alpha;
            else if (row_init_mode == 1) initial_rgb = raw_rgb;
            accum_rgb[static_cast<size_t>(p) * 3 + c] = initial_rgb;
        }
    }

    const bool has_tail = params.front_sharp_tail > 0.0 && min_valid_y <= max_valid_y;
    const float tail_center = has_tail ? (static_cast<float>(min_valid_y) + static_cast<float>(max_valid_y)) * 0.5f : 0.0f;
    const float tail_span = has_tail ? std::max((static_cast<float>(max_valid_y) - static_cast<float>(min_valid_y)) * 0.5f, 1.0f) : 1.0f;

    for (int i = 1; i < front_strength; ++i) {
        const int shift = static_cast<int>(sample_sign) * i;
        for (int y = 0; y < pad_h; ++y) {
            float tail = 1.0f;
            if (has_tail) {
                tail = std::max(0.0f, 1.0f - std::fabs(static_cast<float>(y) - tail_center) *
                                                 static_cast<float>(params.front_sharp_tail) / tail_span);
                if (static_cast<float>(i) >= static_cast<float>(front_strength) * tail) continue;
            }
            int weight_idx = i;
            if (has_tail) {
                weight_idx = std::clamp(static_cast<int>(static_cast<float>(i) / std::max(tail, 1.0e-6f)),
                                        0, front_strength - 1);
            }
            const float weight = weights[static_cast<size_t>(weight_idx)];
            if (shift > 0) {
                for (int x = shift; x < pad_w; ++x) {
                    const int dst_p = y * pad_w + x;
                    const int src_p = y * pad_w + (x - shift);
                    float coeff = 1.0f;
                    int local_weight_idx = weight_idx;
                    if (component_map_coeff) {
                        const int coeff_p = dest_component_coeff ? dst_p : src_p;
                        const ComponentInfo &comp = component_map.pixels[static_cast<size_t>(coeff_p)];
                        if (comp.area <= 0.0f) continue;
                        float area_factor = std::pow(std::clamp(comp.area / component_map.max_area, 0.0f, 1.0f),
                                                     static_cast<float>(params.size_variation));
                        float tail_factor = 1.0f;
                        if (params.front_sharp_tail > 0.0) {
                            tail_factor = std::max(0.0f, 1.0f - std::fabs(static_cast<float>(y) - comp.center_y) *
                                                            static_cast<float>(params.front_sharp_tail) / comp.half_height);
                        }
                        coeff = area_factor * tail_factor;
                        const int effective_span = static_cast<int>(static_cast<float>(front_strength) * coeff);
                        if (coeff <= 0.0f) continue;
                        if (truncate_component_span) {
                            if (i >= effective_span) continue;
                        } else if (static_cast<float>(i) >= static_cast<float>(front_strength) * coeff) {
                            continue;
                        }
                        local_weight_idx = std::clamp(static_cast<int>(static_cast<float>(i) / std::max(coeff, 1.0e-6f)),
                                                      0, front_strength - 1);
                    }
                    const float local_weight = component_map_coeff ? weights[static_cast<size_t>(local_weight_idx)] : weight;
                    const float alpha = source_alpha[static_cast<size_t>(src_p)] * local_weight;
                    const float output_alpha = alpha_coeff_output ? alpha * coeff : alpha;
                    for (int c = 0; c < 3; ++c) {
                        const float rgb_weight = gather_first ? alpha : local_weight;
                        accum_rgb[static_cast<size_t>(dst_p) * 3 + c] += source_rgb[static_cast<size_t>(src_p) * 3 + c] * rgb_weight;
                    }
                    accum_sum[static_cast<size_t>(dst_p)] += alpha;
                    if (alpha_sum_output) accum_alpha[static_cast<size_t>(dst_p)] += output_alpha;
                    else accum_alpha[static_cast<size_t>(dst_p)] = std::max(accum_alpha[static_cast<size_t>(dst_p)], output_alpha);
                }
            } else {
                const int nshift = -shift;
                for (int x = 0; x < pad_w - nshift; ++x) {
                    const int dst_p = y * pad_w + x;
                    const int src_p = y * pad_w + (x + nshift);
                    float coeff = 1.0f;
                    int local_weight_idx = weight_idx;
                    if (component_map_coeff) {
                        const int coeff_p = dest_component_coeff ? dst_p : src_p;
                        const ComponentInfo &comp = component_map.pixels[static_cast<size_t>(coeff_p)];
                        if (comp.area <= 0.0f) continue;
                        float area_factor = std::pow(std::clamp(comp.area / component_map.max_area, 0.0f, 1.0f),
                                                     static_cast<float>(params.size_variation));
                        float tail_factor = 1.0f;
                        if (params.front_sharp_tail > 0.0) {
                            tail_factor = std::max(0.0f, 1.0f - std::fabs(static_cast<float>(y) - comp.center_y) *
                                                            static_cast<float>(params.front_sharp_tail) / comp.half_height);
                        }
                        coeff = area_factor * tail_factor;
                        const int effective_span = static_cast<int>(static_cast<float>(front_strength) * coeff);
                        if (coeff <= 0.0f) continue;
                        if (truncate_component_span) {
                            if (i >= effective_span) continue;
                        } else if (static_cast<float>(i) >= static_cast<float>(front_strength) * coeff) {
                            continue;
                        }
                        local_weight_idx = std::clamp(static_cast<int>(static_cast<float>(i) / std::max(coeff, 1.0e-6f)),
                                                      0, front_strength - 1);
                    }
                    const float local_weight = component_map_coeff ? weights[static_cast<size_t>(local_weight_idx)] : weight;
                    const float alpha = source_alpha[static_cast<size_t>(src_p)] * local_weight;
                    const float output_alpha = alpha_coeff_output ? alpha * coeff : alpha;
                    for (int c = 0; c < 3; ++c) {
                        const float rgb_weight = gather_first ? alpha : local_weight;
                        accum_rgb[static_cast<size_t>(dst_p) * 3 + c] += source_rgb[static_cast<size_t>(src_p) * 3 + c] * rgb_weight;
                    }
                    accum_sum[static_cast<size_t>(dst_p)] += alpha;
                    if (alpha_sum_output) accum_alpha[static_cast<size_t>(dst_p)] += output_alpha;
                    else accum_alpha[static_cast<size_t>(dst_p)] = std::max(accum_alpha[static_cast<size_t>(dst_p)], output_alpha);
                }
            }
        }
    }

    FloatImage blurred;
    blurred.width = pad_w;
    blurred.height = pad_h;
    blurred.rgba.resize(static_cast<size_t>(pad_pixels) * 4, 0.0f);
    for (int p = 0; p < pad_pixels; ++p) {
        const float denom = front_strength_rgb_denom ? std::max(static_cast<float>(front_strength), 1.0f)
                                                     : accum_sum[static_cast<size_t>(p)];
        const size_t dst = static_cast<size_t>(p) * 4;
        if (denom > 1.0e-8f) {
            for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = accum_rgb[static_cast<size_t>(p) * 3 + c] / denom;
        }
        blurred.rgba[dst + 3] = std::min(accum_alpha[static_cast<size_t>(p)], 1.0f);
    }

    FloatImage output_canvas;
    if (aex_two_stage_output) {
        output_canvas.width = pad_w;
        output_canvas.height = pad_h;
        output_canvas.rgba.resize(static_cast<size_t>(pad_pixels) * 4, 0.0f);
        for (int y = 0; y < pad_h; ++y) {
            for (int x = 0; x < pad_w; ++x) {
                const float center_x = aex_rotate_math ? static_cast<float>(pad_w / 2) : static_cast<float>(pad_w) / 2.0f;
                const float center_y = aex_rotate_math ? static_cast<float>(pad_h / 2) : static_cast<float>(pad_h) / 2.0f;
                const float odx = static_cast<float>(x) - center_x;
                const float ody = static_cast<float>(y) - center_y;
                const float bx = odx * cos_a + ody * sin_a + center_x;
                const float by = -odx * sin_a + ody * cos_a + center_y;
                float sample[4];
                if (alpha_weighted_output_rotate) sample_bilinear_alpha_weighted(blurred, bx, by, sample);
                else if (strict_plain_sampler) sample_bilinear_strict(blurred, bx, by, sample);
                else sample_bilinear(blurred, bx, by, sample);
                const size_t dst = (static_cast<size_t>(y) * pad_w + x) * 4;
                for (int c = 0; c < 4; ++c) output_canvas.rgba[dst + c] = sample[c];
            }
        }
    }

    Image out;
    out.width = w;
    out.height = h;
    out.rgba.resize(static_cast<size_t>(w) * h * 4, 0);
    const int crop_x = pad_w / 2 - w / 2;
    const int crop_y = pad_h / 2 - h / 2;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float sample[4];
            if (aex_two_stage_output) {
                const int sx = x + crop_x;
                const int sy = y + crop_y;
                const size_t src = (static_cast<size_t>(sy) * pad_w + sx) * 4;
                for (int c = 0; c < 4; ++c) sample[c] = output_canvas.rgba[src + c];
            } else {
                const float odx = static_cast<float>(x) - static_cast<float>(w) / 2.0f;
                const float ody = static_cast<float>(y) - static_cast<float>(h) / 2.0f;
                const float bx = odx * cos_a + ody * sin_a + static_cast<float>(pad_w) / 2.0f;
                const float by = -odx * sin_a + ody * cos_a + static_cast<float>(pad_h) / 2.0f;
                if (alpha_weighted_output_rotate) sample_bilinear_alpha_weighted(blurred, bx, by, sample);
                else if (strict_plain_sampler) sample_bilinear_strict(blurred, bx, by, sample);
                else sample_bilinear(blurred, bx, by, sample);
            }
            const size_t dst = (static_cast<size_t>(y) * w + x) * 4;
            for (int c = 0; c < 3; ++c) {
                const float value = sample[c] * static_cast<float>(params.brightness_gain);
                out.rgba[dst + c] = truncate_output_quantize ? quantize_trunc(value) : quantize(value);
            }
            const float input_alpha = static_cast<float>(input.rgba[dst + 3]) / 255.0f;
            float alpha = sample[3];
            if (alpha_mode == "input") alpha = input_alpha;
            else if (alpha_mode == "min-input") alpha = std::min(input_alpha, sample[3]);
            else if (alpha_mode == "max-input") alpha = std::max(input_alpha, sample[3]);
            else if (alpha_mode == "zero") alpha = 0.0f;
            else if (alpha_mode != "blurred") throw std::runtime_error("unknown rotated alpha mode: " + alpha_mode);
            out.rgba[dst + 3] = truncate_output_quantize ? quantize_trunc(alpha) : quantize(alpha);
        }
    }
    return out;
}

struct Args {
    std::string input;
    std::string params;
    std::string output;
    std::string algorithm = "direct";
    double angle_sign = -1.0;
    double sample_sign = -1.0;
    double strength_scale = -1.0;
    std::string rgb_normalize = "front-strength";
    std::string direction = "front";
    bool ignore_noise_variation = false;
};

Args parse_args(int argc, char **argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        std::string key(argv[i]);
        auto need_value = [&](const char *name) -> std::string {
            if (i + 1 >= argc) throw std::runtime_error(std::string("missing value for ") + name);
            return std::string(argv[++i]);
        };
        if (key == "--input") args.input = need_value("--input");
        else if (key == "--params") args.params = need_value("--params");
        else if (key == "--output") args.output = need_value("--output");
        else if (key == "--algorithm") args.algorithm = need_value("--algorithm");
        else if (key == "--angle-sign") args.angle_sign = std::strtod(need_value("--angle-sign").c_str(), nullptr);
        else if (key == "--sample-sign") args.sample_sign = std::strtod(need_value("--sample-sign").c_str(), nullptr);
        else if (key == "--strength-scale") {
            std::string value = need_value("--strength-scale");
            args.strength_scale = value == "auto" ? -1.0 : std::strtod(value.c_str(), nullptr);
        } else if (key == "--rgb-normalize") args.rgb_normalize = need_value("--rgb-normalize");
        else if (key == "--direction") {
            args.direction = need_value("--direction");
            if (args.direction != "front" && args.direction != "both") throw std::runtime_error("--direction must be front or both");
        } else if (key == "--ignore-noise-variation") args.ignore_noise_variation = true;
        else if (key == "--help" || key == "-h") {
            std::printf("Usage: olmdirectionalblur_cli --input in.png --params params.json --output out.png [--algorithm direct|direct-map|rotated|rotated-aex-choreo|rotated-aex-full-choreo|rotated-aex-pad-full-choreo|rotated-aex-prepass-full-choreo|rotated-aex-halfheight|rotated-aex-float-math|rotated-aex-trunc-output|rotated-aex-truncated-span|rotated-aex-row-init-straight-zero|rotated-aex-row-init-premul-zero|rotated-aex-row-init-zero|rotated-front-strength|rotated-front-strength-preserve-alpha|rotated-rowdriver-prepass|rotated-rowdriver-prepass-init|rotated-aex-pad|rotated-alpha-sum|rotated-strict|rotated-strict-preserve-alpha|rotated-preserve-alpha|rotated-min-alpha|rotated-max-alpha|rotated-zero-alpha|rotated-gather|rotated-alpha|rotated-alpha-in|rotated-alpha-out|rotated-aex|rotated-aex-init|rotated-map|rotated-map-dest-coeff|rotated-map-alpha-coeff|rotated-map-preserve-alpha|rotated-map-aex|rotated-map-aex-init|rotated-aex-premul|rotated-map-aex-premul] [--direction front|both] [--ignore-noise-variation] [--angle-sign -1] [--sample-sign -1] [--strength-scale auto] [--rgb-normalize front-strength]\n");
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
        DirectionalBlurParams params = read_params(args.params);
        const bool include_back = args.direction == "both";
        Image output;
        if (args.algorithm == "direct") {
            output = render_direct(input, params, args.strength_scale, args.angle_sign, args.sample_sign, args.rgb_normalize, false, include_back, args.ignore_noise_variation);
        } else if (args.algorithm == "direct-map") {
            output = render_direct(input, params, args.strength_scale, args.angle_sign, args.sample_sign, args.rgb_normalize, true, include_back, args.ignore_noise_variation);
        } else if (args.algorithm == "rotated") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "blurred", false);
        } else if (args.algorithm == "rotated-aex-choreo") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "blurred", false, false, false, false, false, false, false, true);
        } else if (args.algorithm == "rotated-aex-full-choreo") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true);
        } else if (args.algorithm == "rotated-aex-pad-full-choreo") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, true, false, false, false, true, true);
        } else if (args.algorithm == "rotated-aex-prepass-full-choreo") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, true, false, "blurred", false, false, false, false, false, false, true, true, true);
        } else if (args.algorithm == "rotated-aex-halfheight") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true, -1, false, false, true);
        } else if (args.algorithm == "rotated-aex-float-math") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true, -1, false, false, false, true);
        } else if (args.algorithm == "rotated-aex-trunc-output") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true, -1, false, true);
        } else if (args.algorithm == "rotated-aex-truncated-span") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true, -1, true);
        } else if (args.algorithm == "rotated-aex-row-init-straight-zero") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true, 1);
        } else if (args.algorithm == "rotated-aex-row-init-premul-zero") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true, 2);
        } else if (args.algorithm == "rotated-aex-row-init-zero") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, false, false, "blurred", false, false, false, false, false, false, false, true, true, 3);
        } else if (args.algorithm == "rotated-front-strength") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "blurred", false, false, false, false, false, true);
        } else if (args.algorithm == "rotated-front-strength-preserve-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "input", false, false, false, false, false, true);
        } else if (args.algorithm == "rotated-rowdriver-prepass") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, true, false, "blurred", false, false, false, false, false, false, true);
        } else if (args.algorithm == "rotated-rowdriver-prepass-init") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, true, false, true, true, "blurred", false, false, false, false, false, false, true);
        } else if (args.algorithm == "rotated-aex-pad") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "blurred", false, false, false, true);
        } else if (args.algorithm == "rotated-alpha-sum") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "blurred", false, true);
        } else if (args.algorithm == "rotated-strict") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "blurred", true);
        } else if (args.algorithm == "rotated-strict-preserve-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "input", true);
        } else if (args.algorithm == "rotated-preserve-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "input", false);
        } else if (args.algorithm == "rotated-min-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "min-input", false);
        } else if (args.algorithm == "rotated-max-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "max-input", false);
        } else if (args.algorithm == "rotated-zero-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, false, false, false, false, "zero", false);
        } else if (args.algorithm == "rotated-gather") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, true, false, false, false, false, false, false, "blurred", false);
        } else if (args.algorithm == "rotated-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, true, false, false, false, false, "blurred", false);
        } else if (args.algorithm == "rotated-alpha-in") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, true, false, false, false, false, false, "blurred", false);
        } else if (args.algorithm == "rotated-alpha-out") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, true, false, false, false, false, "blurred", false);
        } else if (args.algorithm == "rotated-aex") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, true, true, true, false, false, true, false, "blurred", false);
        } else if (args.algorithm == "rotated-aex-init") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, true, true, true, false, false, true, true, "blurred", false);
        } else if (args.algorithm == "rotated-map") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, true, false, false, false, "blurred", false);
        } else if (args.algorithm == "rotated-map-dest-coeff") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, true, false, false, false, "blurred", false, false, false, false, true);
        } else if (args.algorithm == "rotated-map-alpha-coeff") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, true, false, false, false, "blurred", false, false, true);
        } else if (args.algorithm == "rotated-map-preserve-alpha") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, false, false, false, true, false, false, false, "input", false);
        } else if (args.algorithm == "rotated-map-aex") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, true, true, true, true, false, true, false, "blurred", false);
        } else if (args.algorithm == "rotated-map-aex-init") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, true, true, true, true, false, true, true, "blurred", false);
        } else if (args.algorithm == "rotated-aex-premul") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, true, true, true, false, true, true, false, "blurred", false);
        } else if (args.algorithm == "rotated-map-aex-premul") {
            output = render_rotated(input, params, args.strength_scale, args.angle_sign, args.sample_sign, true, true, true, true, true, true, false, "blurred", false);
        } else {
            throw std::runtime_error("unknown algorithm: " + args.algorithm);
        }
        write_png(args.output, output);
        std::printf("wrote: %s (experimental directional C++ slice)\n", args.output.c_str());
        return 0;
    } catch (const std::exception &ex) {
        std::fprintf(stderr, "olmdirectionalblur_cli: %s\n", ex.what());
        return 1;
    }
}
