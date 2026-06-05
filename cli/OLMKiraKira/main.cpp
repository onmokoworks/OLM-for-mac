#include <png.h>

#include <algorithm>
#include <cmath>
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
    std::vector<float> data;

    FloatImage() = default;
    FloatImage(int w, int h, int channels) : width(w), height(h), data(static_cast<size_t>(w) * h * channels) {}
};

struct Color {
    float r = 1.0f;
    float g = 1.0f;
    float b = 1.0f;
    float a = 1.0f;
};

struct KiraKiraParams {
    double glow_rotation = 0.0;
    double brightness_gain = 1.0;
    int vertical_length = 0;
    int horizontal_length = 0;
    int diagonal_length = 0;
    int diagonal2_length = 0;
    double glow_opacity = 1.0;
    int channel = 2;
    int blur_mode = 2;
    double strength_multiplier = 1.0;
    double source_opacity = 1.0;
    Color vertical_color;
    Color horizontal_color;
    Color diagonal_color;
    Color diagonal2_color;
};

struct Options {
    std::string input;
    std::string params;
    std::string output;
    std::string seed_mode = "aex";
    std::string falloff = "box3";
    std::string compose_mode = "aex-premul";
    double gain_scale = 0.72;
    double scale_override = -1.0;
    bool has_scale_override = false;
    bool auto_length_scale = false;
    double length_scale = 1.0;
    double comp_width = 1920.0;
    std::string filter_border = "mirror";
    std::string box_size_mode = "length";
    std::string box_anchor_mode = "opencv";
    std::string box_normalize = "true";
    std::string box_output_depth = "float";
    std::string rotate_filter = "bilinear";
    std::string rotate_border = "constant";
    std::string warp_mode = "current";
    std::string rotate_size_mode = "round";
    bool axis_fast_path = true;
    std::string axis_fast_path_mode = "true";
    std::string crop_mode = "floor";
    std::string glow_normalize = "union";
    std::string aggregation_mode = "current";
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

Color json_color_or(const Json *value, Color fallback = {}) {
    if (!value || value->type != Json::Array || value->array_value.size() < 3) return fallback;
    Color c;
    c.r = static_cast<float>(json_number_or(&value->array_value[0], fallback.r));
    c.g = static_cast<float>(json_number_or(&value->array_value[1], fallback.g));
    c.b = static_cast<float>(json_number_or(&value->array_value[2], fallback.b));
    c.a = static_cast<float>(value->array_value.size() > 3 ? json_number_or(&value->array_value[3], fallback.a) : fallback.a);
    if (std::max({c.r, c.g, c.b, c.a}) > 1.0f) {
        c.r /= 255.0f;
        c.g /= 255.0f;
        c.b /= 255.0f;
        c.a /= 255.0f;
    }
    return c;
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
        if (name && name->type == Json::String && name->string_value == "OLM Kira Kira") is_target = true;
        if (match && match->type == Json::String && match->string_value == "OLM OLM Kira Kira") is_target = true;
        if (is_target) {
            if (const Json *params = effect.get("params")) return params;
        }
    }
    return scope;
}

std::map<std::string, const Json *> kira_param_map(const Json &root) {
    std::map<std::string, const Json *> result;
    const Json *params = find_effect_params(root);
    if (!params) return result;
    if (params->type == Json::Array) {
        for (const Json &param : params->array_value) {
            const Json *match = param.get("match_name");
            const Json *name = param.get("name");
            const Json *value = param.get("value");
            if (!value) continue;
            if (name && name->type == Json::String) result[name->string_value] = value;
            if (match && match->type == Json::String) {
                const std::string &m = match->string_value;
                auto suffix = [&](const char *s) { return m.size() >= 5 && m.compare(m.size() - 5, 5, s) == 0; };
                if (suffix("-0001")) result["glow_rotation"] = value;
                else if (suffix("-0002")) result["brightness_gain"] = value;
                else if (suffix("-0003")) result["vertical_length"] = value;
                else if (suffix("-0004")) result["horizontal_length"] = value;
                else if (suffix("-0005")) result["diagonal_length"] = value;
                else if (suffix("-0007")) result["glow_opacity"] = value;
                else if (suffix("-0008")) result["channel"] = value;
                else if (suffix("-0009")) result["blur_mode"] = value;
                else if (suffix("-0011")) result["strength_multiplier"] = value;
                else if (suffix("-0012")) result["source_opacity"] = value;
                else if (suffix("-0013")) result["vertical_color"] = value;
                else if (suffix("-0014")) result["horizontal_color"] = value;
                else if (suffix("-0015")) result["diagonal_color"] = value;
                else if (suffix("-0026")) result["diagonal2_length"] = value;
                else if (suffix("-0028")) result["diagonal2_color"] = value;
            }
        }
    }
    return result;
}

KiraKiraParams read_params(const std::string &path) {
    Json root = JsonParser(read_text_file(path)).parse();
    auto params = kira_param_map(root);
    auto get = [&](const char *name) -> const Json * {
        auto it = params.find(name);
        return it == params.end() ? nullptr : it->second;
    };

    KiraKiraParams kp;
    kp.glow_rotation = json_number_or(get("glow_rotation"), kp.glow_rotation);
    kp.brightness_gain = json_number_or(get("brightness_gain"), kp.brightness_gain);
    kp.vertical_length = static_cast<int>(std::lround(json_number_or(get("vertical_length"), 0.0)));
    kp.horizontal_length = static_cast<int>(std::lround(json_number_or(get("horizontal_length"), 0.0)));
    kp.diagonal_length = static_cast<int>(std::lround(json_number_or(get("diagonal_length"), 0.0)));
    kp.diagonal2_length = static_cast<int>(std::lround(json_number_or(get("diagonal2_length"), 0.0)));
    kp.glow_opacity = json_number_or(get("glow_opacity"), 100.0) / 100.0;
    kp.channel = static_cast<int>(std::lround(json_number_or(get("channel"), kp.channel)));
    kp.blur_mode = static_cast<int>(std::lround(json_number_or(get("blur_mode"), kp.blur_mode)));
    kp.strength_multiplier = json_number_or(get("strength_multiplier"), 100.0) / 100.0;
    kp.source_opacity = json_number_or(get("source_opacity"), 100.0) / 100.0;
    kp.vertical_color = json_color_or(get("vertical_color"));
    kp.horizontal_color = json_color_or(get("horizontal_color"));
    kp.diagonal_color = json_color_or(get("diagonal_color"));
    kp.diagonal2_color = json_color_or(get("diagonal2_color"));
    return kp;
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
    Image image;
    image.width = static_cast<int>(width);
    image.height = static_cast<int>(height);
    image.rgba.resize(static_cast<size_t>(image.width) * image.height * 4);
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

float clamp01(float v) {
    return std::min(1.0f, std::max(0.0f, v));
}

unsigned char quantize(float v) {
    return static_cast<unsigned char>(std::lround(clamp01(v) * 255.0f));
}

int reflect_index(int i, int n) {
    if (n <= 1) return 0;
    while (i < 0 || i >= n) {
        if (i < 0) i = -i - 1;
        if (i >= n) i = 2 * n - i - 1;
    }
    return i;
}

int mirror_index(int i, int n) {
    if (n <= 1) return 0;
    while (i < 0 || i >= n) {
        if (i < 0) i = -i;
        if (i >= n) i = 2 * n - i - 2;
    }
    return i;
}

int border_index(int i, int n, const std::string &mode) {
    if (mode == "reflect") return reflect_index(i, n);
    return mirror_index(i, n);
}

std::vector<float> make_seed(const Image &input, const KiraKiraParams &params, const Options &options) {
    const int w = input.width;
    const int h = input.height;
    std::vector<float> seed(static_cast<size_t>(w) * h);
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const size_t idx = static_cast<size_t>(y) * w + x;
            const size_t p = idx * 4;
            float r = input.rgba[p + 0] / 255.0f;
            float g = input.rgba[p + 1] / 255.0f;
            float b = input.rgba[p + 2] / 255.0f;
            float a = input.rgba[p + 3] / 255.0f;
            float v = 0.0f;
            if (options.seed_mode == "max") {
                v = std::max({r, g, b}) * a;
            } else if (params.channel == 1) {
                v = std::pow(a, std::max(1.0e-6, params.strength_multiplier));
            } else if (params.channel == 2) {
                float luma = r * 0.299f + g * 0.587f + b * 0.114f;
                v = std::pow(luma, std::max(1.0e-6, params.strength_multiplier)) * a;
            } else if (params.channel == 4) {
                v = std::pow(std::max({r, g, b}), std::max(1.0e-6, params.strength_multiplier)) * a;
            } else {
                v = std::max({std::pow(r, std::max(1.0e-6, params.strength_multiplier)),
                              std::pow(g, std::max(1.0e-6, params.strength_multiplier)),
                              std::pow(b, std::max(1.0e-6, params.strength_multiplier))}) * a;
            }
            seed[idx] = v;
        }
    }
    return seed;
}

std::vector<float> direction_box_blur(
    const std::vector<float> &input,
    int width,
    int height,
    int length,
    int dx,
    int dy,
    int passes,
    const std::string &filter_border,
    const std::string &box_anchor_mode,
    const std::string &box_normalize,
    const std::string &box_output_depth
) {
    if (length <= 1) return input;
    std::vector<float> src = input;
    std::vector<float> dst(src.size());
    int left = length / 2;
    if (box_anchor_mode == "floor-left") {
        left = (length - 1) / 2;
    } else if (box_anchor_mode == "origin") {
        left = 0;
    } else if (box_anchor_mode == "end") {
        left = length - 1;
    }
    const int right = length - left - 1;
    for (int pass = 0; pass < passes; ++pass) {
        std::fill(dst.begin(), dst.end(), 0.0f);
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                double sum = 0.0;
                for (int k = -left; k <= right; ++k) {
                    int sx = border_index(x + dx * k, width, filter_border);
                    int sy = border_index(y + dy * k, height, filter_border);
                    sum += src[static_cast<size_t>(sy) * width + sx];
                }
                double v = box_normalize == "false" ? sum : sum / static_cast<double>(length);
                if (box_output_depth == "u8-each") {
                    v = std::round(clamp01(static_cast<float>(v)) * 255.0) / 255.0;
                } else if (box_output_depth == "u16-each") {
                    v = std::round(std::max(0.0, std::min(1.0, v)) * 65535.0) / 65535.0;
                }
                dst[static_cast<size_t>(y) * width + x] = static_cast<float>(v);
            }
        }
        src.swap(dst);
    }
    return src;
}

float sample_zero(const std::vector<float> &input, int width, int height, int x, int y) {
    if (x < 0 || y < 0 || x >= width || y >= height) return 0.0f;
    return input[static_cast<size_t>(y) * width + x];
}

float sample_bilinear_zero(const std::vector<float> &input, int width, int height, double x, double y) {
    if (x < 0.0 || y < 0.0 || x > static_cast<double>(width - 1) || y > static_cast<double>(height - 1)) return 0.0f;
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    int x1 = std::min(width - 1, x0 + 1);
    int y1 = std::min(height - 1, y0 + 1);
    double tx = x - static_cast<double>(x0);
    double ty = y - static_cast<double>(y0);
    float v00 = input[static_cast<size_t>(y0) * width + x0];
    float v10 = input[static_cast<size_t>(y0) * width + x1];
    float v01 = input[static_cast<size_t>(y1) * width + x0];
    float v11 = input[static_cast<size_t>(y1) * width + x1];
    double a = v00 * (1.0 - tx) + v10 * tx;
    double b = v01 * (1.0 - tx) + v11 * tx;
    return static_cast<float>(a * (1.0 - ty) + b * ty);
}

float sample_bilinear_constant(const std::vector<float> &input, int width, int height, double x, double y) {
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    int x1 = x0 + 1;
    int y1 = y0 + 1;
    double tx = x - static_cast<double>(x0);
    double ty = y - static_cast<double>(y0);
    float v00 = sample_zero(input, width, height, x0, y0);
    float v10 = sample_zero(input, width, height, x1, y0);
    float v01 = sample_zero(input, width, height, x0, y1);
    float v11 = sample_zero(input, width, height, x1, y1);
    double a = v00 * (1.0 - tx) + v10 * tx;
    double b = v01 * (1.0 - tx) + v11 * tx;
    return static_cast<float>(a * (1.0 - ty) + b * ty);
}

float sample_bilinear_constant_fixed5(const std::vector<float> &input, int width, int height, double x, double y) {
    int x0 = static_cast<int>(std::floor(x));
    int y0 = static_cast<int>(std::floor(y));
    int fx = static_cast<int>(std::lround((x - static_cast<double>(x0)) * 32.0));
    int fy = static_cast<int>(std::lround((y - static_cast<double>(y0)) * 32.0));
    if (fx >= 32) {
        fx = 0;
        ++x0;
    }
    if (fy >= 32) {
        fy = 0;
        ++y0;
    }
    const int x1 = x0 + 1;
    const int y1 = y0 + 1;
    const double tx = static_cast<double>(fx) / 32.0;
    const double ty = static_cast<double>(fy) / 32.0;
    float v00 = sample_zero(input, width, height, x0, y0);
    float v10 = sample_zero(input, width, height, x1, y0);
    float v01 = sample_zero(input, width, height, x0, y1);
    float v11 = sample_zero(input, width, height, x1, y1);
    double a = v00 * (1.0 - tx) + v10 * tx;
    double b = v01 * (1.0 - tx) + v11 * tx;
    return static_cast<float>(a * (1.0 - ty) + b * ty);
}

double cubic_weight(double x) {
    x = std::abs(x);
    if (x < 1.0) return ((-0.5 * x + 1.5) * x - 1.5) * x + 1.0;
    if (x < 2.0) return (((0.5 * x - 2.5) * x + 4.0) * x - 2.0);
    return 0.0;
}

float sample_bicubic_zero(const std::vector<float> &input, int width, int height, double x, double y) {
    int ix = static_cast<int>(std::floor(x));
    int iy = static_cast<int>(std::floor(y));
    double sum = 0.0;
    for (int yy = iy - 1; yy <= iy + 2; ++yy) {
        double wy = cubic_weight(y - static_cast<double>(yy));
        for (int xx = ix - 1; xx <= ix + 2; ++xx) {
            double wx = cubic_weight(x - static_cast<double>(xx));
            sum += static_cast<double>(sample_zero(input, width, height, xx, yy)) * wx * wy;
        }
    }
    return static_cast<float>(std::max(0.0, std::min(1.0, sum)));
}

int rounded_extent(double value, const std::string &rotate_size_mode) {
    if (rotate_size_mode == "floor") return std::max(1, static_cast<int>(std::floor(value)));
    if (rotate_size_mode == "ceil") return std::max(1, static_cast<int>(std::ceil(value)));
    return std::max(1, static_cast<int>(value + 0.5));
}

std::vector<float> rotate_image(
    const std::vector<float> &input,
    int width,
    int height,
    double angle_deg,
    int &out_width,
    int &out_height,
    const std::string &rotate_filter,
    const std::string &rotate_border,
    const std::string &warp_mode,
    const std::string &rotate_size_mode
) {
    const double pi = 3.14159265358979323846;
    double rad = angle_deg * pi / 180.0;
    double c = std::cos(rad);
    double s = std::sin(rad);
    if (warp_mode == "opencv-center") {
        const double cx = static_cast<double>(width) * 0.5;
        const double cy = static_cast<double>(height) * 0.5;
        double bounds[4][2] = {
            {0.0, 0.0},
            {static_cast<double>(width), 0.0},
            {0.0, static_cast<double>(height)},
            {static_cast<double>(width), static_cast<double>(height)},
        };
        double min_x = 1.0e30;
        double min_y = 1.0e30;
        double max_x = -1.0e30;
        double max_y = -1.0e30;
        for (auto &corner : bounds) {
            const double sx = corner[0] - cx;
            const double sy = corner[1] - cy;
            const double dx = sx * c - sy * s;
            const double dy = sx * s + sy * c;
            min_x = std::min(min_x, dx);
            max_x = std::max(max_x, dx);
            min_y = std::min(min_y, dy);
            max_y = std::max(max_y, dy);
        }
        out_width = rounded_extent(max_x - min_x, rotate_size_mode);
        out_height = rounded_extent(max_y - min_y, rotate_size_mode);
        std::vector<float> output(static_cast<size_t>(out_width) * out_height);
        for (int y = 0; y < out_height; ++y) {
            for (int x = 0; x < out_width; ++x) {
                const double dx = static_cast<double>(x) + min_x;
                const double dy = static_cast<double>(y) + min_y;
                const double sx = dx * c + dy * s + cx;
                const double sy = -dx * s + dy * c + cy;
                if (rotate_filter == "bicubic") {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bicubic_zero(input, width, height, sx, sy);
                } else if (rotate_filter == "bilinear-fixed5") {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_constant_fixed5(input, width, height, sx, sy);
                } else if (rotate_border == "constant") {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_constant(input, width, height, sx, sy);
                } else {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_zero(input, width, height, sx, sy);
                }
            }
        }
        return output;
    }
    double bounds[4][2] = {
        {0.0, 0.0},
        {static_cast<double>(height), 0.0},
        {0.0, static_cast<double>(width)},
        {static_cast<double>(height), static_cast<double>(width)},
    };
    double min_oy = 1.0e30;
    double min_ox = 1.0e30;
    double max_oy = -1.0e30;
    double max_ox = -1.0e30;
    for (auto &corner : bounds) {
        const double y = corner[0];
        const double x = corner[1];
        const double oy = y * c + x * s;
        const double ox = -y * s + x * c;
        min_oy = std::min(min_oy, oy);
        max_oy = std::max(max_oy, oy);
        min_ox = std::min(min_ox, ox);
        max_ox = std::max(max_ox, ox);
    }
    if (rotate_size_mode == "aex-min4") {
        const double ac = std::abs(c);
        const double as = std::abs(s);
        out_width = std::max(width + 4, static_cast<int>(static_cast<double>(width) * ac + static_cast<double>(height) * as + 0.5));
        out_height = std::max(height + 4, static_cast<int>(static_cast<double>(width) * as + static_cast<double>(height) * ac + 0.5));
    } else {
        out_width = rounded_extent(max_ox - min_ox, rotate_size_mode);
        out_height = rounded_extent(max_oy - min_oy, rotate_size_mode);
    }
    std::vector<float> output(static_cast<size_t>(out_width) * out_height);
    double cx = (static_cast<double>(width) - 1.0) * 0.5;
    double cy = (static_cast<double>(height) - 1.0) * 0.5;
    double ocx = (static_cast<double>(out_width) - 1.0) * 0.5;
    double ocy = (static_cast<double>(out_height) - 1.0) * 0.5;
    if (warp_mode == "aex-getrot") {
        const double aex_cx = static_cast<double>(out_width) * 0.5;
        const double aex_cy = static_cast<double>(out_height) * 0.5;
        const double alpha = c;
        const double beta = s;
        const double m00 = alpha;
        const double m01 = beta;
        const double m02 = (1.0 - alpha) * aex_cx - beta * aex_cy;
        const double m10 = -beta;
        const double m11 = alpha;
        const double m12 = beta * aex_cx + (1.0 - alpha) * aex_cy;
        const double det = m00 * m11 - m01 * m10;
        std::vector<float> output(static_cast<size_t>(out_width) * out_height);
        for (int y = 0; y < out_height; ++y) {
            for (int x = 0; x < out_width; ++x) {
                const double dx = static_cast<double>(x) - m02;
                const double dy = static_cast<double>(y) - m12;
                const double sx = (m11 * dx - m01 * dy) / det;
                const double sy = (-m10 * dx + m00 * dy) / det;
                if (rotate_filter == "bicubic") {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bicubic_zero(input, width, height, sx, sy);
                } else if (rotate_filter == "bilinear-fixed5") {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_constant_fixed5(input, width, height, sx, sy);
                } else if (rotate_border == "constant") {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_constant(input, width, height, sx, sy);
                } else {
                    output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_zero(input, width, height, sx, sy);
                }
            }
        }
        return output;
    }
    for (int y = 0; y < out_height; ++y) {
        for (int x = 0; x < out_width; ++x) {
            double ox = static_cast<double>(x) - ocx;
            double oy = static_cast<double>(y) - ocy;
            double sx = ox * c + oy * s + cx;
            double sy = -ox * s + oy * c + cy;
            if (rotate_filter == "bicubic") {
                output[static_cast<size_t>(y) * out_width + x] = sample_bicubic_zero(input, width, height, sx, sy);
            } else if (rotate_filter == "bilinear-fixed5") {
                output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_constant_fixed5(input, width, height, sx, sy);
            } else if (rotate_border == "constant") {
                output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_constant(input, width, height, sx, sy);
            } else {
                output[static_cast<size_t>(y) * out_width + x] = sample_bilinear_zero(input, width, height, sx, sy);
            }
        }
    }
    return output;
}

std::vector<float> warp_getrot_direct(
    const std::vector<float> &input,
    int src_width,
    int src_height,
    int dst_width,
    int dst_height,
    double center_x,
    double center_y,
    double angle_deg,
    const std::string &rotate_filter,
    const std::string &rotate_border
) {
    const double pi = 3.14159265358979323846;
    const double rad = angle_deg * pi / 180.0;
    const double alpha = std::cos(rad);
    const double beta = std::sin(rad);
    const double m00 = alpha;
    const double m01 = beta;
    const double m02 = (1.0 - alpha) * center_x - beta * center_y;
    const double m10 = -beta;
    const double m11 = alpha;
    const double m12 = beta * center_x + (1.0 - alpha) * center_y;
    const double det = m00 * m11 - m01 * m10;
    std::vector<float> output(static_cast<size_t>(dst_width) * dst_height);
    for (int y = 0; y < dst_height; ++y) {
        for (int x = 0; x < dst_width; ++x) {
            const double dx = static_cast<double>(x) - m02;
            const double dy = static_cast<double>(y) - m12;
            const double sx = (m11 * dx - m01 * dy) / det;
            const double sy = (-m10 * dx + m00 * dy) / det;
            if (rotate_filter == "bicubic") {
                output[static_cast<size_t>(y) * dst_width + x] = sample_bicubic_zero(input, src_width, src_height, sx, sy);
            } else if (rotate_filter == "bilinear-fixed5") {
                output[static_cast<size_t>(y) * dst_width + x] = sample_bilinear_constant_fixed5(input, src_width, src_height, sx, sy);
            } else if (rotate_border == "constant") {
                output[static_cast<size_t>(y) * dst_width + x] = sample_bilinear_constant(input, src_width, src_height, sx, sy);
            } else {
                output[static_cast<size_t>(y) * dst_width + x] = sample_bilinear_zero(input, src_width, src_height, sx, sy);
            }
        }
    }
    return output;
}

std::vector<float> copy_centered_roi(
    const std::vector<float> &input,
    int src_width,
    int src_height,
    int dst_width,
    int dst_height,
    int offset_x = 0,
    int offset_y = 0
) {
    std::vector<float> output(static_cast<size_t>(dst_width) * dst_height);
    const int x0 = static_cast<int>(static_cast<float>(src_width) * 0.5f) - dst_width / 2 + offset_x;
    const int y0 = static_cast<int>(static_cast<float>(src_height) * 0.5f) - dst_height / 2 + offset_y;
    for (int y = 0; y < dst_height; ++y) {
        const int sy = y + y0;
        if (sy < 0 || sy >= src_height) continue;
        for (int x = 0; x < dst_width; ++x) {
            const int sx = x + x0;
            if (sx < 0 || sx >= src_width) continue;
            output[static_cast<size_t>(y) * dst_width + x] = input[static_cast<size_t>(sy) * src_width + sx];
        }
    }
    return output;
}

std::vector<float> paste_centered_roi(
    const std::vector<float> &input,
    int src_width,
    int src_height,
    int dst_width,
    int dst_height
) {
    std::vector<float> output(static_cast<size_t>(dst_width) * dst_height);
    const int x0 = static_cast<int>(static_cast<float>(dst_width) * 0.5f) - src_width / 2;
    const int y0 = static_cast<int>(static_cast<float>(dst_height) * 0.5f) - src_height / 2;
    for (int y = 0; y < src_height; ++y) {
        const int dy = y + y0;
        if (dy < 0 || dy >= dst_height) continue;
        for (int x = 0; x < src_width; ++x) {
            const int dx = x + x0;
            if (dx < 0 || dx >= dst_width) continue;
            output[static_cast<size_t>(dy) * dst_width + dx] = input[static_cast<size_t>(y) * src_width + x];
        }
    }
    return output;
}

std::vector<float> crop_center(
    const std::vector<float> &input,
    int in_width,
    int in_height,
    int width,
    int height,
    const std::string &crop_mode
) {
    std::vector<float> output(static_cast<size_t>(width) * height);
    double raw_x0 = static_cast<double>(in_width - width) * 0.5;
    double raw_y0 = static_cast<double>(in_height - height) * 0.5;
    int x0 = static_cast<int>(std::floor(raw_x0));
    int y0 = static_cast<int>(std::floor(raw_y0));
    if (crop_mode == "ceil") {
        x0 = static_cast<int>(std::ceil(raw_x0));
        y0 = static_cast<int>(std::ceil(raw_y0));
    } else if (crop_mode == "round") {
        x0 = static_cast<int>(std::round(raw_x0));
        y0 = static_cast<int>(std::round(raw_y0));
    }
    x0 = std::max(0, x0);
    y0 = std::max(0, y0);
    for (int y = 0; y < height; ++y) {
        int sy = y + y0;
        if (sy < 0 || sy >= in_height) continue;
        for (int x = 0; x < width; ++x) {
            int sx = x + x0;
            if (sx < 0 || sx >= in_width) continue;
            output[static_cast<size_t>(y) * width + x] = input[static_cast<size_t>(sy) * in_width + sx];
        }
    }
    return output;
}

std::vector<float> rotated_axis_box_blur(
    const std::vector<float> &input,
    int width,
    int height,
    int length,
    double angle_deg,
    int passes,
    const std::string &filter_border,
    const std::string &box_anchor_mode,
    const std::string &box_normalize,
    const std::string &box_output_depth,
    const std::string &rotate_filter,
    const std::string &rotate_border,
    const std::string &warp_mode,
    const std::string &rotate_size_mode,
    bool axis_fast_path,
    const std::string &crop_mode
) {
    if (length <= 1) return input;
    if (axis_fast_path) {
        if (angle_deg == 0.0) return direction_box_blur(input, width, height, length, 1, 0, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
        if (angle_deg == 90.0) return direction_box_blur(input, width, height, length, 0, 1, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
    }

    if (warp_mode == "aex-roi-temp") {
        const double pi = 3.14159265358979323846;
        const double rad = angle_deg * pi / 180.0;
        const double ac = std::abs(std::cos(rad));
        const double as = std::abs(std::sin(rad));
        const int rw = std::max(width + 4, static_cast<int>(static_cast<double>(width) * ac + static_cast<double>(height) * as + 0.5));
        const int rh = std::max(height + 4, static_cast<int>(static_cast<double>(width) * as + static_cast<double>(height) * ac + 0.5));
        const double cx = static_cast<double>(width) * 0.5;
        const double cy = static_cast<double>(height) * 0.5;
        std::vector<float> temp = copy_centered_roi(input, width, height, rw, rh);
        std::vector<float> rotated = warp_getrot_direct(temp, rw, rh, width, height, cx, cy, angle_deg, rotate_filter, rotate_border);
        std::vector<float> restored_temp = paste_centered_roi(rotated, width, height, rw, rh);
        std::vector<float> blurred = direction_box_blur(restored_temp, rw, rh, length, 1, 0, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
        std::vector<float> restored = warp_getrot_direct(blurred, rw, rh, width, height, cx, cy, -angle_deg, rotate_filter, rotate_border);
        return restored;
    }

    if (warp_mode == "aex-inplace-temp") {
        const double pi = 3.14159265358979323846;
        const double rad = angle_deg * pi / 180.0;
        const double ac = std::abs(std::cos(rad));
        const double as = std::abs(std::sin(rad));
        const int rw = std::max(width + 4, static_cast<int>(static_cast<double>(width) * ac + static_cast<double>(height) * as + 0.5));
        const int rh = std::max(height + 4, static_cast<int>(static_cast<double>(width) * as + static_cast<double>(height) * ac + 0.5));
        const double temp_cx = static_cast<double>(rw) * 0.5;
        const double temp_cy = static_cast<double>(rh) * 0.5;
        const double frame_cx = static_cast<double>(width) * 0.5;
        const double frame_cy = static_cast<double>(height) * 0.5;
        std::vector<float> temp = copy_centered_roi(input, width, height, rw, rh);
        temp = warp_getrot_direct(temp, rw, rh, rw, rh, temp_cx, temp_cy, angle_deg, rotate_filter, rotate_border);
        std::vector<float> blurred = direction_box_blur(temp, rw, rh, length, 1, 0, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
        return warp_getrot_direct(blurred, rw, rh, width, height, frame_cx, frame_cy, -angle_deg, rotate_filter, rotate_border);
    }

    if (warp_mode == "aex-two-temp" ||
        warp_mode == "aex-two-temp-final-xm" ||
        warp_mode == "aex-two-temp-final-xp" ||
        warp_mode == "aex-two-temp-final-ym" ||
        warp_mode == "aex-two-temp-final-yp" ||
        warp_mode == "aex-two-temp-direct-back" ||
        warp_mode == "aex-two-temp-center-minus-half") {
        const double pi = 3.14159265358979323846;
        const double rad = angle_deg * pi / 180.0;
        const double ac = std::abs(std::cos(rad));
        const double as = std::abs(std::sin(rad));
        const int rw = std::max(width + 4, static_cast<int>(static_cast<double>(width) * ac + static_cast<double>(height) * as + 0.5));
        const int rh = std::max(height + 4, static_cast<int>(static_cast<double>(width) * as + static_cast<double>(height) * ac + 0.5));
        double temp_cx = static_cast<double>(rw) * 0.5;
        double temp_cy = static_cast<double>(rh) * 0.5;
        if (warp_mode == "aex-two-temp-center-minus-half") {
            temp_cx -= 0.5;
            temp_cy -= 0.5;
        }
        std::vector<float> temp_a = copy_centered_roi(input, width, height, rw, rh);
        temp_a = warp_getrot_direct(temp_a, rw, rh, rw, rh, temp_cx, temp_cy, angle_deg, rotate_filter, rotate_border);
        std::vector<float> temp_b = direction_box_blur(temp_a, rw, rh, length, 1, 0, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
        if (warp_mode == "aex-two-temp-direct-back") {
            return warp_getrot_direct(temp_b, rw, rh, width, height, temp_cx, temp_cy, -angle_deg, rotate_filter, rotate_border);
        }
        temp_b = warp_getrot_direct(temp_b, rw, rh, rw, rh, temp_cx, temp_cy, -angle_deg, rotate_filter, rotate_border);
        int shift_x = 0;
        int shift_y = 0;
        if (warp_mode == "aex-two-temp-final-xm") shift_x = -1;
        if (warp_mode == "aex-two-temp-final-xp") shift_x = 1;
        if (warp_mode == "aex-two-temp-final-ym") shift_y = -1;
        if (warp_mode == "aex-two-temp-final-yp") shift_y = 1;
        return copy_centered_roi(temp_b, rw, rh, width, height, shift_x, shift_y);
    }

    if (warp_mode == "aex-frame") {
        const double cx = static_cast<double>(width) * 0.5;
        const double cy = static_cast<double>(height) * 0.5;
        std::vector<float> rotated = warp_getrot_direct(input, width, height, width, height, cx, cy, angle_deg, rotate_filter, rotate_border);
        std::vector<float> blurred = direction_box_blur(rotated, width, height, length, 1, 0, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
        return warp_getrot_direct(blurred, width, height, width, height, cx, cy, -angle_deg, rotate_filter, rotate_border);
    }

    if (warp_mode == "aex-direct-back") {
        const double pi = 3.14159265358979323846;
        const double rad = angle_deg * pi / 180.0;
        const double ac = std::abs(std::cos(rad));
        const double as = std::abs(std::sin(rad));
        const int rw = std::max(width + 4, static_cast<int>(static_cast<double>(width) * ac + static_cast<double>(height) * as + 0.5));
        const int rh = std::max(height + 4, static_cast<int>(static_cast<double>(width) * as + static_cast<double>(height) * ac + 0.5));
        const double cx = static_cast<double>(rw) * 0.5;
        const double cy = static_cast<double>(rh) * 0.5;
        std::vector<float> rotated = warp_getrot_direct(input, width, height, rw, rh, cx, cy, angle_deg, rotate_filter, rotate_border);
        std::vector<float> blurred = direction_box_blur(rotated, rw, rh, length, 1, 0, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
        return warp_getrot_direct(blurred, rw, rh, width, height, cx, cy, -angle_deg, rotate_filter, rotate_border);
    }

    int rw = 0;
    int rh = 0;
    std::vector<float> rotated = rotate_image(input, width, height, angle_deg, rw, rh, rotate_filter, rotate_border, warp_mode, rotate_size_mode);
    std::vector<float> blurred = direction_box_blur(rotated, rw, rh, length, 1, 0, passes, filter_border, box_anchor_mode, box_normalize, box_output_depth);
    int bw = 0;
    int bh = 0;
    std::vector<float> restored = rotate_image(blurred, rw, rh, -angle_deg, bw, bh, rotate_filter, rotate_border, warp_mode, rotate_size_mode);
    return crop_center(restored, bw, bh, width, height, crop_mode);
}

void add_colored_union(
    FloatImage &glow,
    std::vector<float> &glow_weight_sum,
    const std::vector<float> &amount,
    const Color &color,
    double scale
) {
    const int pixels = glow.width * glow.height;
    for (int i = 0; i < pixels; ++i) {
        float alpha = clamp01(static_cast<float>(amount[static_cast<size_t>(i)] * scale) * color.a);
        size_t p = static_cast<size_t>(i) * 4;
        glow.data[p + 0] += alpha * color.r;
        glow.data[p + 1] += alpha * color.g;
        glow.data[p + 2] += alpha * color.b;
        glow.data[p + 3] = glow.data[p + 3] + alpha - glow.data[p + 3] * alpha;
        glow_weight_sum[static_cast<size_t>(i)] += alpha;
    }
}

FloatImage aggregate_fd90_five(
    int width,
    int height,
    const std::vector<std::vector<float>> &amounts,
    const std::vector<Color> &colors,
    double scale
) {
    FloatImage glow(width, height, 4);
    const int pixels = width * height;
    for (int i = 0; i < pixels; ++i) {
        size_t p = static_cast<size_t>(i) * 4;
        float alpha_union = 0.0f;
        for (size_t layer = 0; layer < amounts.size(); ++layer) {
            float alpha = clamp01(static_cast<float>(amounts[layer][static_cast<size_t>(i)] * scale) * colors[layer].a);
            if (alpha <= 1.0e-6f) continue;
            glow.data[p + 0] += alpha * colors[layer].r;
            glow.data[p + 1] += alpha * colors[layer].g;
            glow.data[p + 2] += alpha * colors[layer].b;
            alpha_union = alpha_union + alpha - alpha_union * alpha;
        }
        glow.data[p + 3] = clamp01(alpha_union);
        if (alpha_union > 1.0e-6f) {
            glow.data[p + 0] /= alpha_union;
            glow.data[p + 1] /= alpha_union;
            glow.data[p + 2] /= alpha_union;
        }
    }
    return glow;
}

Image render_kirakira(const Image &input, const KiraKiraParams &params, const Options &options) {
    const int w = input.width;
    const int h = input.height;
    double length_scale = options.length_scale;
    if (options.auto_length_scale) length_scale = options.comp_width > 0.0 ? static_cast<double>(w) / options.comp_width : 1.0;

    std::vector<float> seed = make_seed(input, params, options);
    auto scaled_len = [&](int v) {
        int len = std::max(0, static_cast<int>(std::lround(v * length_scale)));
        if (options.box_size_mode == "radius" && len > 0) len = len * 2 + 1;
        return len;
    };
    int passes = options.falloff == "box3" ? 3 : 1;
    bool axis_fast_path = options.axis_fast_path;
    if (options.axis_fast_path_mode == "strength-nonzero") {
        axis_fast_path = params.strength_multiplier > 1.0e-6;
    }

    const double glow_rotation = params.glow_rotation;
    std::vector<float> vertical = rotated_axis_box_blur(seed, w, h, scaled_len(params.vertical_length), 90.0 + glow_rotation, passes, options.filter_border, options.box_anchor_mode, options.box_normalize, options.box_output_depth, options.rotate_filter, options.rotate_border, options.warp_mode, options.rotate_size_mode, axis_fast_path, options.crop_mode);
    std::vector<float> horizontal = rotated_axis_box_blur(seed, w, h, scaled_len(params.horizontal_length), glow_rotation, passes, options.filter_border, options.box_anchor_mode, options.box_normalize, options.box_output_depth, options.rotate_filter, options.rotate_border, options.warp_mode, options.rotate_size_mode, axis_fast_path, options.crop_mode);
    std::vector<float> diagonal = rotated_axis_box_blur(seed, w, h, scaled_len(params.diagonal_length), 45.0 + glow_rotation, passes, options.filter_border, options.box_anchor_mode, options.box_normalize, options.box_output_depth, options.rotate_filter, options.rotate_border, options.warp_mode, options.rotate_size_mode, axis_fast_path, options.crop_mode);
    std::vector<float> diagonal2 = rotated_axis_box_blur(seed, w, h, scaled_len(params.diagonal2_length), -45.0 + glow_rotation, passes, options.filter_border, options.box_anchor_mode, options.box_normalize, options.box_output_depth, options.rotate_filter, options.rotate_border, options.warp_mode, options.rotate_size_mode, axis_fast_path, options.crop_mode);

    double scale = params.brightness_gain * (params.strength_multiplier <= 1.0e-6 ? 1.0 : options.gain_scale);
    if (options.has_scale_override) scale = options.scale_override;

    FloatImage glow;
    if (options.aggregation_mode == "fd90-five") {
        std::vector<float> highlight_zero(static_cast<size_t>(w) * h, 0.0f);
        glow = aggregate_fd90_five(
            w,
            h,
            {vertical, horizontal, diagonal, highlight_zero, diagonal2},
            {params.vertical_color, params.horizontal_color, params.diagonal_color, Color{}, params.diagonal2_color},
            scale
        );
    } else {
        glow = FloatImage(w, h, 4);
        std::vector<float> glow_weight_sum(static_cast<size_t>(w) * h, 0.0f);
        add_colored_union(glow, glow_weight_sum, vertical, params.vertical_color, scale);
        add_colored_union(glow, glow_weight_sum, horizontal, params.horizontal_color, scale);
        add_colored_union(glow, glow_weight_sum, diagonal, params.diagonal_color, scale);
        add_colored_union(glow, glow_weight_sum, diagonal2, params.diagonal2_color, scale);
        const int pixels = w * h;
        for (int i = 0; i < pixels; ++i) {
            size_t p = static_cast<size_t>(i) * 4;
            float a = options.glow_normalize == "sum" ? glow_weight_sum[static_cast<size_t>(i)] : glow.data[p + 3];
            if (a > 1.0e-6f) {
                glow.data[p + 0] /= a;
                glow.data[p + 1] /= a;
                glow.data[p + 2] /= a;
            }
        }
    }

    Image out = input;
    out.rgba.assign(static_cast<size_t>(w) * h * 4, 0);
    const int pixels = w * h;
    for (int i = 0; i < pixels; ++i) {
        size_t p = static_cast<size_t>(i) * 4;
        float src_a = (input.rgba[p + 3] / 255.0f) * static_cast<float>(params.source_opacity);
        float glow_a = clamp01(glow.data[p + 3] * static_cast<float>(params.glow_opacity));
        float denom = src_a + glow_a;
        float out_r = 0.0f;
        float out_g = 0.0f;
        float out_b = 0.0f;
        if (options.compose_mode == "aex-add-rgb") {
            out_r = clamp01((input.rgba[p + 0] / 255.0f) * src_a + glow.data[p + 0] * glow_a);
            out_g = clamp01((input.rgba[p + 1] / 255.0f) * src_a + glow.data[p + 1] * glow_a);
            out_b = clamp01((input.rgba[p + 2] / 255.0f) * src_a + glow.data[p + 2] * glow_a);
        } else if (options.compose_mode == "aex-screen-rgb") {
            const float src_r = (input.rgba[p + 0] / 255.0f) * src_a;
            const float src_g = (input.rgba[p + 1] / 255.0f) * src_a;
            const float src_b = (input.rgba[p + 2] / 255.0f) * src_a;
            out_r = 1.0f - (1.0f - src_r) * (1.0f - glow.data[p + 0] * glow_a);
            out_g = 1.0f - (1.0f - src_g) * (1.0f - glow.data[p + 1] * glow_a);
            out_b = 1.0f - (1.0f - src_b) * (1.0f - glow.data[p + 2] * glow_a);
        } else if (denom > 1.0e-6f) {
            out_r = ((input.rgba[p + 0] / 255.0f) * src_a + glow.data[p + 0] * glow_a) / denom;
            out_g = ((input.rgba[p + 1] / 255.0f) * src_a + glow.data[p + 1] * glow_a) / denom;
            out_b = ((input.rgba[p + 2] / 255.0f) * src_a + glow.data[p + 2] * glow_a) / denom;
        }
        out.rgba[p + 0] = quantize(out_r);
        out.rgba[p + 1] = quantize(out_g);
        out.rgba[p + 2] = quantize(out_b);
        out.rgba[p + 3] = quantize(std::min(1.0f, denom));
    }
    return out;
}

Options parse_args(int argc, char **argv) {
    Options args;
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
        } else if (key == "--seed-mode") {
            args.seed_mode = need_value("--seed-mode");
        } else if (key == "--falloff") {
            args.falloff = need_value("--falloff");
        } else if (key == "--filter-border") {
            args.filter_border = need_value("--filter-border");
            if (args.filter_border != "reflect" && args.filter_border != "mirror") {
                throw std::runtime_error("--filter-border must be reflect or mirror");
            }
        } else if (key == "--compose-mode") {
            args.compose_mode = need_value("--compose-mode");
        } else if (key == "--gain-scale") {
            args.gain_scale = std::strtod(need_value("--gain-scale").c_str(), nullptr);
        } else if (key == "--scale-override") {
            args.scale_override = std::strtod(need_value("--scale-override").c_str(), nullptr);
            args.has_scale_override = true;
        } else if (key == "--auto-length-scale") {
            args.auto_length_scale = true;
        } else if (key == "--length-scale") {
            args.length_scale = std::strtod(need_value("--length-scale").c_str(), nullptr);
        } else if (key == "--comp-width") {
            args.comp_width = std::strtod(need_value("--comp-width").c_str(), nullptr);
        } else if (key == "--box-size-mode") {
            args.box_size_mode = need_value("--box-size-mode");
            if (args.box_size_mode != "length" && args.box_size_mode != "radius") {
                throw std::runtime_error("--box-size-mode must be length or radius");
            }
        } else if (key == "--box-anchor-mode") {
            args.box_anchor_mode = need_value("--box-anchor-mode");
            if (args.box_anchor_mode != "opencv" && args.box_anchor_mode != "floor-left" &&
                args.box_anchor_mode != "origin" && args.box_anchor_mode != "end") {
                throw std::runtime_error("--box-anchor-mode must be opencv, floor-left, origin, or end");
            }
        } else if (key == "--box-normalize") {
            args.box_normalize = need_value("--box-normalize");
            if (args.box_normalize != "true" && args.box_normalize != "false") {
                throw std::runtime_error("--box-normalize must be true or false");
            }
        } else if (key == "--box-output-depth") {
            args.box_output_depth = need_value("--box-output-depth");
            if (args.box_output_depth != "float" && args.box_output_depth != "u8-each" &&
                args.box_output_depth != "u16-each") {
                throw std::runtime_error("--box-output-depth must be float, u8-each, or u16-each");
            }
        } else if (key == "--rotate-filter") {
            args.rotate_filter = need_value("--rotate-filter");
            if (args.rotate_filter != "bilinear" && args.rotate_filter != "bicubic" &&
                args.rotate_filter != "bilinear-fixed5") {
                throw std::runtime_error("--rotate-filter must be bilinear, bicubic, or bilinear-fixed5");
            }
        } else if (key == "--rotate-border") {
            args.rotate_border = need_value("--rotate-border");
            if (args.rotate_border != "edge" && args.rotate_border != "constant") {
                throw std::runtime_error("--rotate-border must be edge or constant");
            }
        } else if (key == "--warp-mode") {
            args.warp_mode = need_value("--warp-mode");
            if (args.warp_mode != "current" && args.warp_mode != "opencv-center" &&
                args.warp_mode != "aex-getrot" && args.warp_mode != "aex-direct-back" &&
                args.warp_mode != "aex-frame" && args.warp_mode != "aex-roi-temp" &&
                args.warp_mode != "aex-inplace-temp" && args.warp_mode != "aex-two-temp" &&
                args.warp_mode != "aex-two-temp-final-xm" && args.warp_mode != "aex-two-temp-final-xp" &&
                args.warp_mode != "aex-two-temp-final-ym" && args.warp_mode != "aex-two-temp-final-yp" &&
                args.warp_mode != "aex-two-temp-direct-back" &&
                args.warp_mode != "aex-two-temp-center-minus-half") {
                throw std::runtime_error("--warp-mode must be current, opencv-center, aex-getrot, aex-direct-back, aex-frame, aex-roi-temp, aex-inplace-temp, aex-two-temp, aex-two-temp-direct-back, aex-two-temp-final-{xm,xp,ym,yp}, or aex-two-temp-center-minus-half");
            }
        } else if (key == "--rotate-size-mode") {
            args.rotate_size_mode = need_value("--rotate-size-mode");
            if (args.rotate_size_mode != "round" && args.rotate_size_mode != "floor" &&
                args.rotate_size_mode != "ceil" && args.rotate_size_mode != "aex-min4") {
                throw std::runtime_error("--rotate-size-mode must be round, floor, ceil, or aex-min4");
            }
        } else if (key == "--axis-fast-path") {
            std::string value = need_value("--axis-fast-path");
            if (value == "true") {
                args.axis_fast_path = true;
                args.axis_fast_path_mode = "true";
            } else if (value == "false") {
                args.axis_fast_path = false;
                args.axis_fast_path_mode = "false";
            } else {
                throw std::runtime_error("--axis-fast-path must be true or false");
            }
        } else if (key == "--axis-fast-path-mode") {
            args.axis_fast_path_mode = need_value("--axis-fast-path-mode");
            if (args.axis_fast_path_mode == "true") {
                args.axis_fast_path = true;
            } else if (args.axis_fast_path_mode == "false") {
                args.axis_fast_path = false;
            } else if (args.axis_fast_path_mode != "strength-nonzero") {
                throw std::runtime_error("--axis-fast-path-mode must be true, false, or strength-nonzero");
            }
        } else if (key == "--crop-mode") {
            args.crop_mode = need_value("--crop-mode");
            if (args.crop_mode != "floor" && args.crop_mode != "ceil" && args.crop_mode != "round") {
                throw std::runtime_error("--crop-mode must be floor, ceil, or round");
            }
        } else if (key == "--glow-normalize") {
            args.glow_normalize = need_value("--glow-normalize");
            if (args.glow_normalize != "union" && args.glow_normalize != "sum") {
                throw std::runtime_error("--glow-normalize must be union or sum");
            }
        } else if (key == "--aggregation-mode") {
            args.aggregation_mode = need_value("--aggregation-mode");
            if (args.aggregation_mode != "current" && args.aggregation_mode != "fd90-five") {
                throw std::runtime_error("--aggregation-mode must be current or fd90-five");
            }
        } else if (key == "--filter-border" || key == "--ray-mode") {
            (void)need_value(key.c_str());
        } else if (key == "--help" || key == "-h") {
            std::printf("Usage: olmkk_cli --input in.png --params params.json --output out.png [--seed-mode aex|max] [--falloff box3] [--filter-border mirror|reflect] [--auto-length-scale] [--box-size-mode length|radius] [--box-anchor-mode opencv|floor-left|origin|end] [--box-normalize true|false] [--box-output-depth float|u8-each|u16-each] [--rotate-filter bilinear|bicubic|bilinear-fixed5] [--rotate-border edge|constant] [--warp-mode current|opencv-center|aex-getrot|aex-direct-back|aex-frame|aex-roi-temp|aex-inplace-temp|aex-two-temp|aex-two-temp-direct-back|aex-two-temp-final-{xm,xp,ym,yp}|aex-two-temp-center-minus-half] [--rotate-size-mode round|floor|ceil|aex-min4] [--axis-fast-path true|false] [--axis-fast-path-mode true|false|strength-nonzero] [--crop-mode floor|ceil|round] [--glow-normalize union|sum] [--aggregation-mode current|fd90-five]\n");
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
        Options args = parse_args(argc, argv);
        Image input = read_png(args.input);
        KiraKiraParams params = read_params(args.params);
        Image output = render_kirakira(input, params, args);
        write_png(args.output, output);
        std::printf("wrote: %s (experimental kirakira C++ slice)\n", args.output.c_str());
        return 0;
    } catch (const std::exception &ex) {
        std::fprintf(stderr, "olmkirakira_cli: %s\n", ex.what());
        return 1;
    }
}
