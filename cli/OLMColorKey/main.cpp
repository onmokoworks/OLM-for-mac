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

struct Color {
    float r = 0.0f;
    float g = 0.0f;
    float b = 0.0f;
};

struct KeyColor {
    Color rgb;
    float threshold = 0.0f;
    float comp[3] = {0.0f, 0.0f, 0.0f};
    bool use_replace = false;
    // Replace color, RGB in 0..1 (param "Replace Color N", stored as ARGB float
    // in the keyer ctx at +0x204+idx*0x10; keyer reads R/G/B from +4/+8/+0xc).
    float replace_rgb[3] = {0.0f, 0.0f, 0.0f};
};

struct ColorKeyParams {
    bool color_keep = false;
    float threshold = 0.0f;
    bool premultiplied = false;
    int color_space = 1;
    bool per_color = false;
    bool per_component = false;
    bool enable_replace = false;
    float edge_thin_amount = 0.0f;
    int edge_thin_distance_type = 1;
    float edge_blur_amount = 0.0f;
    int edge_blur_distance_type = 1;
    int edge_blur_direction = 2;
    std::vector<KeyColor> colors;
};

struct TracePixel {
    int x = -1;
    int y = -1;
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

long json_int_or(const Json *value, long fallback) {
    return static_cast<long>(std::lround(json_number_or(value, static_cast<double>(fallback))));
}

Color json_color_or(const Json *value, Color fallback = {}) {
    if (!value || value->type != Json::Array || value->array_value.size() < 3) return fallback;
    Color c;
    c.r = static_cast<float>(json_number_or(&value->array_value[0], 0.0));
    c.g = static_cast<float>(json_number_or(&value->array_value[1], 0.0));
    c.b = static_cast<float>(json_number_or(&value->array_value[2], 0.0));
    if (std::max({c.r, c.g, c.b}) > 1.0f) {
        c.r /= 255.0f;
        c.g /= 255.0f;
        c.b /= 255.0f;
    }
    c.r = std::clamp(c.r, 0.0f, 1.0f);
    c.g = std::clamp(c.g, 0.0f, 1.0f);
    c.b = std::clamp(c.b, 0.0f, 1.0f);
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
        if (name && name->type == Json::String && name->string_value == "OLM Color Key") is_target = true;
        if (match && match->type == Json::String && match->string_value == "OLM Color Key") is_target = true;
        if (is_target) {
            if (const Json *params = effect.get("params")) return params;
        }
    }
    return scope;
}

std::map<std::string, const Json *> param_map(const Json &root) {
    std::map<std::string, const Json *> result;
    const Json *params = find_effect_params(root);
    if (!params) return result;
    if (params->type == Json::Array) {
        for (const Json &param : params->array_value) {
            const Json *name = param.get("name");
            const Json *value = param.get("value");
            if (name && name->type == Json::String && value) result[name->string_value] = value;
        }
    } else if (params->type == Json::Object) {
        for (const auto &entry : params->object_value) result[entry.first] = &entry.second;
    }
    return result;
}

ColorKeyParams read_params(const std::string &path) {
    Json root = JsonParser(read_text_file(path)).parse();
    auto params = param_map(root);
    auto get = [&](const std::string &name) -> const Json * {
        auto it = params.find(name);
        return it == params.end() ? nullptr : it->second;
    };

    ColorKeyParams cfg;
    cfg.color_keep = json_number_or(get("Color Keep"), 0.0) != 0.0;
    cfg.threshold = static_cast<float>(json_number_or(get("Threshold"), 0.0));
    cfg.premultiplied = json_number_or(get("Premultiplied Color"), 0.0) != 0.0;
    cfg.color_space = static_cast<int>(json_int_or(get("Color Space"), 1));
    cfg.per_color = json_number_or(get("Per Color"), 0.0) != 0.0;
    cfg.per_component = json_number_or(get("Per Component"), 0.0) != 0.0;
    cfg.enable_replace = json_number_or(get("Enable Replace"), 0.0) != 0.0;

    const Json *params_json = find_effect_params(root);
    if (params_json && params_json->type == Json::Array) {
        for (size_t i = 0; i < params_json->array_value.size(); ++i) {
            const Json &param = params_json->array_value[i];
            const Json *name = param.get("name");
            if (!name || name->type != Json::String) continue;
            if (name->string_value == "Edge Thin") {
                if (i + 1 < params_json->array_value.size()) cfg.edge_thin_amount = static_cast<float>(json_number_or(params_json->array_value[i + 1].get("value"), 0.0));
                if (i + 2 < params_json->array_value.size()) cfg.edge_thin_distance_type = static_cast<int>(json_int_or(params_json->array_value[i + 2].get("value"), 1));
            } else if (name->string_value == "Edge Blur") {
                if (i + 1 < params_json->array_value.size()) cfg.edge_blur_amount = static_cast<float>(json_number_or(params_json->array_value[i + 1].get("value"), 0.0));
                if (i + 2 < params_json->array_value.size()) cfg.edge_blur_distance_type = static_cast<int>(json_int_or(params_json->array_value[i + 2].get("value"), 1));
                if (i + 3 < params_json->array_value.size()) cfg.edge_blur_direction = static_cast<int>(json_int_or(params_json->array_value[i + 3].get("value"), 2));
            }
        }
    } else {
        cfg.edge_thin_amount = static_cast<float>(json_number_or(get("Edge Thin Amount"), 0.0));
        cfg.edge_thin_distance_type = static_cast<int>(json_int_or(get("Edge Thin Distance Type"), 1));
        cfg.edge_blur_amount = static_cast<float>(json_number_or(get("Edge Blur Amount"), 0.0));
        cfg.edge_blur_distance_type = static_cast<int>(json_int_or(get("Edge Blur Distance Type"), 1));
        cfg.edge_blur_direction = static_cast<int>(json_int_or(get("Edge Blur Direction"), 2));
    }

    int ncolors = static_cast<int>(json_int_or(get("Number of Colors"), 1));
    ncolors = std::clamp(ncolors, 1, 25);
    for (int i = 1; i <= ncolors; ++i) {
        std::string suffix = std::to_string(i);
        if (json_number_or(get("Use Color " + suffix), 1.0) == 0.0) continue;
        KeyColor kc;
        kc.rgb = json_color_or(get("Color " + suffix));
        kc.threshold = static_cast<float>(json_number_or(get("Threshold " + suffix), 0.0));
        kc.comp[0] = static_cast<float>(json_number_or(get("Threshold(R,H,L,Y,Y) " + suffix), 0.0));
        kc.comp[1] = static_cast<float>(json_number_or(get("Threshold(G,S,a,U,Cr) " + suffix), 0.0));
        kc.comp[2] = static_cast<float>(json_number_or(get("Threshold(B,V,b,V,Cb) " + suffix), 0.0));
        kc.use_replace = json_number_or(get("Use Replace Color " + suffix), 0.0) != 0.0;
        Color rep = json_color_or(get("Replace Color " + suffix));
        kc.replace_rgb[0] = rep.r;
        kc.replace_rgb[1] = rep.g;
        kc.replace_rgb[2] = rep.b;
        cfg.colors.push_back(kc);
    }
    if (cfg.colors.empty()) {
        KeyColor kc;
        kc.rgb = json_color_or(get("Color 1"));
        cfg.colors.push_back(kc);
    }
    return cfg;
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

std::vector<float> l1_distance_to(const std::vector<unsigned char> &mask, int w, int h) {
    const float inf = 1.0e9f;
    std::vector<float> d(static_cast<size_t>(w) * h, inf);
    for (int i = 0; i < w * h; ++i) {
        if (mask[i]) d[i] = 0.0f;
    }
    for (int x = 1; x < w; ++x) {
        for (int y = 0; y < h; ++y) {
            int i = y * w + x;
            d[i] = std::min(d[i], d[i - 1] + 1.0f);
        }
    }
    for (int x = w - 2; x >= 0; --x) {
        for (int y = 0; y < h; ++y) {
            int i = y * w + x;
            d[i] = std::min(d[i], d[i + 1] + 1.0f);
        }
    }
    for (int y = 1; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            int i = y * w + x;
            d[i] = std::min(d[i], d[i - w] + 1.0f);
        }
    }
    for (int y = h - 2; y >= 0; --y) {
        for (int x = 0; x < w; ++x) {
            int i = y * w + x;
            d[i] = std::min(d[i], d[i + w] + 1.0f);
        }
    }
    return d;
}

std::vector<float> chessboard_distance_to(const std::vector<unsigned char> &mask, int w, int h) {
    const float inf = 1.0e9f;
    std::vector<float> d(static_cast<size_t>(w) * h, inf);
    for (int i = 0; i < w * h; ++i) {
        if (mask[i]) d[i] = 0.0f;
    }
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            int i = y * w + x;
            if (x > 0) d[i] = std::min(d[i], d[i - 1] + 1.0f);
            if (y > 0) d[i] = std::min(d[i], d[i - w] + 1.0f);
            if (x > 0 && y > 0) d[i] = std::min(d[i], d[i - w - 1] + 1.0f);
            if (x + 1 < w && y > 0) d[i] = std::min(d[i], d[i - w + 1] + 1.0f);
        }
    }
    for (int y = h - 1; y >= 0; --y) {
        for (int x = w - 1; x >= 0; --x) {
            int i = y * w + x;
            if (x + 1 < w) d[i] = std::min(d[i], d[i + 1] + 1.0f);
            if (y + 1 < h) d[i] = std::min(d[i], d[i + w] + 1.0f);
            if (x + 1 < w && y + 1 < h) d[i] = std::min(d[i], d[i + w + 1] + 1.0f);
            if (x > 0 && y + 1 < h) d[i] = std::min(d[i], d[i + w - 1] + 1.0f);
        }
    }
    return d;
}

static float edt_square(float x) {
    return x * x;
}

std::vector<float> edt_1d(const std::vector<float> &f, int n) {
    const float inf = 1.0e9f;
    std::vector<int> sites;
    sites.reserve(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        if (f[static_cast<size_t>(i)] < inf * 0.5f) sites.push_back(i);
    }
    std::vector<float> d(static_cast<size_t>(n), inf);
    if (sites.empty()) return d;

    std::vector<int> v(static_cast<size_t>(sites.size()));
    std::vector<float> z(static_cast<size_t>(sites.size()) + 1);
    int k = 0;
    v[0] = sites[0];
    z[0] = -1.0e20f;
    z[1] = 1.0e20f;
    for (size_t site_index = 1; site_index < sites.size(); ++site_index) {
        int q = sites[site_index];
        float s = 0.0f;
        while (true) {
            int vk = v[static_cast<size_t>(k)];
            s = ((f[static_cast<size_t>(q)] + edt_square(static_cast<float>(q))) -
                 (f[static_cast<size_t>(vk)] + edt_square(static_cast<float>(vk)))) /
                (2.0f * static_cast<float>(q - vk));
            if (s > z[static_cast<size_t>(k)]) break;
            if (k == 0) break;
            --k;
        }
        if (s <= z[static_cast<size_t>(k)]) {
            k = 0;
        } else {
            ++k;
        }
        v[static_cast<size_t>(k)] = q;
        z[static_cast<size_t>(k)] = s;
        z[static_cast<size_t>(k + 1)] = 1.0e20f;
    }
    k = 0;
    for (int q = 0; q < n; ++q) {
        while (z[static_cast<size_t>(k + 1)] < static_cast<float>(q)) ++k;
        int vk = v[static_cast<size_t>(k)];
        d[static_cast<size_t>(q)] = edt_square(static_cast<float>(q - vk)) + f[static_cast<size_t>(vk)];
    }
    return d;
}

std::vector<float> euclidean_distance_to(const std::vector<unsigned char> &mask, int w, int h) {
    const float inf = 1.0e9f;
    std::vector<float> tmp(static_cast<size_t>(w) * h);
    std::vector<float> f(static_cast<size_t>(std::max(w, h)));
    for (int x = 0; x < w; ++x) {
        for (int y = 0; y < h; ++y) f[static_cast<size_t>(y)] = mask[y * w + x] ? 0.0f : inf;
        std::vector<float> col = edt_1d(f, h);
        for (int y = 0; y < h; ++y) tmp[static_cast<size_t>(y) * w + x] = col[static_cast<size_t>(y)];
    }
    std::vector<float> out(static_cast<size_t>(w) * h);
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) f[static_cast<size_t>(x)] = tmp[static_cast<size_t>(y) * w + x];
        std::vector<float> row = edt_1d(f, w);
        for (int x = 0; x < w; ++x) out[static_cast<size_t>(y) * w + x] = std::sqrt(row[static_cast<size_t>(x)]);
    }
    return out;
}

std::vector<float> matte_distance(const std::vector<unsigned char> &mask, int w, int h, int distance_type) {
    if (distance_type == 1) return chessboard_distance_to(mask, w, h);
    if (distance_type == 3) return euclidean_distance_to(mask, w, h);
    return l1_distance_to(mask, w, h);
}

std::vector<float> edge_blur_distance(const std::vector<unsigned char> &mask, int w, int h, int distance_type) {
    return matte_distance(mask, w, h, distance_type);
}

std::vector<unsigned char> boundary8(const std::vector<unsigned char> &mask, int w, int h) {
    std::vector<unsigned char> out(static_cast<size_t>(w) * h, 0);
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const int i = y * w + x;
            if (!mask[i]) continue;
            bool all_inside = true;
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = std::clamp(x + dx, 0, w - 1);
                    int ny = std::clamp(y + dy, 0, h - 1);
                    all_inside = all_inside && mask[ny * w + nx] != 0;
                }
            }
            out[i] = all_inside ? 0 : 1;
        }
    }
    return out;
}

float lab_f(float t) {
    return t <= 0.008856000378727913f
        ? t * 7.7870001792907715f + 0.13793103396892548f
        : std::pow(t, 0.3333300054073334f);
}

void rgb_to_plugin_lab76(const float rgb[3], float out[3]) {
    float r = rgb[0];
    float g = rgb[1];
    float b = rgb[2];
    float x = g * 2.1455016136169434f + r * 0.6380193829536438f + b * 0.2165091633796692f;
    float fx = lab_f(x);
    out[0] = x <= 0.008856000378727913f
        ? g * 1938.031494140625f + r * 576.3229370117188f + b * 195.57272338867188f
        : std::pow(x, 0.3333300054073334f) * 116.0f - 16.0f;
    float a_source = r * 1.2373713254928589f + g * 1.0727508068084717f + b * 0.5412744283676147f;
    float b_source = g * 0.35758259892463684f + r * 0.05800257995724678f + b * 2.8507096767425537f;
    out[1] = (lab_f(a_source) - fx) * 500.0f;
    out[2] = (fx - lab_f(b_source)) * 200.0f;
}

// RGB -> HSV matching FUN_180009e10: standard 6-sector hue in degrees
// (sector coeff 60, offsets 120/240), wrapped mod 360 then normalized to [0,1];
// S = (max-min)/max; V = max. Inputs are 0..1 (premultiplied when enabled).
void rgb_to_plugin_hsv(const float rgb[3], float out[3]) {
    const float r = rgb[0], g = rgb[1], b = rgb[2];
    const float mx = std::max(r, std::max(g, b));
    const float mn = std::min(r, std::min(g, b));
    const float delta = mx - mn;
    float h;
    if (delta == 0.0f) h = 0.0f;
    else if (mx == r) h = (g - b) * 60.0f / delta;
    else if (mx == g) h = (b - r) * 60.0f / delta + 120.0f;
    else h = (r - g) * 60.0f / delta + 240.0f;
    h = std::fmod(h, 360.0f);
    if (h < 0.0f) h += 360.0f;
    out[0] = h / 360.0f;
    out[1] = mx == 0.0f ? 0.0f : delta / mx;
    out[2] = mx;
}

// RGB -> YUV (color space 5), inline matrix in FUN_1800029d0.
void rgb_to_plugin_yuv(const float rgb[3], float out[3]) {
    const float r = rgb[0], g = rgb[1], b = rgb[2];
    out[0] = g * 0.5870000123977661f + r * 0.29899999499320984f + b * 0.11400000005960464f;
    out[1] = b * 0.4359999895095825f - (g * 0.2888599932193756f + r * 0.14712999761104584f);
    out[2] = r * 0.6150000095367432f - g * 0.514989972114563f - b * 0.10001000016927719f;
}

// RGB -> YCrCb (color space 6), FUN_18000a190. out = {Y, Cb, Cr}.
void rgb_to_plugin_ycrcb(const float rgb[3], float out[3]) {
    const float r = rgb[0], g = rgb[1], b = rgb[2];
    out[0] = r * 0.298909991979599f + g * 0.5866100192070007f + b * 0.11448000371456146f;
    out[1] = b * 0.5f - (r * 0.16874000430107117f + g * 0.33125999569892883f);
    out[2] = r * 0.5f - g * 0.4186899960041046f - b * 0.08130999654531479f;
}

// Lab94 (color space 4) distance, matching FUN_180004510 non-per-component path:
// CIE94-style with geometric-mean chroma sqrt(C1*C2), hue angle in degrees
// (atan2*180/pi + 180, mod 360), SC = 1 + 0.045*Cmean, SH = 1 + 0.015*Cmean.
float lab94_distance(const float a[3], const float b[3]) {
    const float C1 = std::sqrt(a[1] * a[1] + a[2] * a[2]);
    const float C2 = std::sqrt(b[1] * b[1] + b[2] * b[2]);
    const float cmean = std::sqrt(C2 * C1);
    auto hue = [](float aa, float bb) {
        float h = std::atan2(bb, aa) * 57.2957763671875f + 180.0f;
        if (h != 0.0f) {
            if (h < 0.0f) h += 540.0f;
            h = std::fmod(h, 360.0f);
        }
        return h;
    };
    const float h1 = hue(a[1], a[2]);
    const float h2 = hue(b[1], b[2]);
    const float dL = b[0] - a[0];
    const float dC = (C2 - C1) / (cmean * 0.04500000178813934f + 1.0f);
    const float dH = (h2 - h1) / (cmean * 0.014999999664723873f + 1.0f);
    return std::sqrt(dL * dL + dC * dC + dH * dH);
}

float edge_blur_weight(bool inside, float dist, float amount, int direction) {
    if (amount <= 0.0f) return inside ? 1.0f : 0.0f;
    if (direction == 1) {
        if (!inside) return 0.0f;
        if (dist >= amount) return 1.0f;
        return (std::sin((dist * (static_cast<float>(M_PI) / amount)) - static_cast<float>(M_PI / 2.0)) + 1.0f) * 0.5f;
    }
    if (direction == 2) {
        if (inside) return 1.0f;
        if (dist >= amount) return 0.0f;
        return (std::sin(static_cast<float>(M_PI / 2.0) - (dist * (static_cast<float>(M_PI) / amount))) + 1.0f) * 0.5f;
    }
    if (direction == 3) {
        if (!inside) return 0.0f;
        if (dist >= amount) return 1.0f;
        return (std::sin((dist * (static_cast<float>(M_PI) / amount)) - static_cast<float>(M_PI / 2.0)) + 1.0f) * 0.5f;
    }
    return inside ? 1.0f : 0.0f;
}

std::vector<TracePixel> parse_trace_pixels_env() {
    std::vector<TracePixel> result;
    const char *trace = std::getenv("OLMCOLORKEY_TRACE_PIXELS");
    if (!trace) return result;
    const char *p = trace;
    while (*p) {
        int x = -1;
        int y = -1;
        int consumed = 0;
        if (std::sscanf(p, "%d,%d%n", &x, &y, &consumed) == 2 && consumed > 0) {
            result.push_back({x, y});
            p += consumed;
            while (*p == ';' || *p == ' ' || *p == '\t' || *p == '\n') ++p;
        } else {
            break;
        }
    }
    return result;
}

Image render_olmcolorkey(const Image &input, const ColorKeyParams &cfg) {
    Image out = input;
    const int w = input.width;
    const int h = input.height;
    const int n = w * h;
    const std::vector<TracePixel> trace_pixels = parse_trace_pixels_env();
    std::vector<unsigned char> matched(n, 0);
    // Index (into cfg.colors) of the first key that matched each pixel, or -1.
    // The keyer (FUN_1800029d0) records the matched index to drive the Replace
    // output path; see notes/OLMColorKey_ASM_FACTS.md.
    std::vector<int> matched_idx(n, -1);
    constexpr float eps8 = 0.5f / 255.0f;

    for (int i = 0; i < n; ++i) {
        const size_t p = static_cast<size_t>(i) * 4;
        float a = static_cast<float>(input.rgba[p + 3]) / 255.0f;
        float rgb[3] = {
            static_cast<float>(input.rgba[p + 0]) / 255.0f,
            static_cast<float>(input.rgba[p + 1]) / 255.0f,
            static_cast<float>(input.rgba[p + 2]) / 255.0f,
        };
        float cmp[3] = {
            cfg.premultiplied ? rgb[0] * a : rgb[0],
            cfg.premultiplied ? rgb[1] * a : rgb[1],
            cfg.premultiplied ? rgb[2] * a : rgb[2],
        };
        if (cfg.color_space == 3 || cfg.color_space == 4) {
            float lab[3];
            rgb_to_plugin_lab76(cmp, lab);
            cmp[0] = lab[0];
            cmp[1] = lab[1];
            cmp[2] = lab[2];
        } else if (cfg.color_space == 2) {
            float hsv[3];
            rgb_to_plugin_hsv(cmp, hsv);
            cmp[0] = hsv[0];
            cmp[1] = hsv[1];
            cmp[2] = hsv[2];
        } else if (cfg.color_space == 5) {
            float yuv[3];
            rgb_to_plugin_yuv(cmp, yuv);
            cmp[0] = yuv[0];
            cmp[1] = yuv[1];
            cmp[2] = yuv[2];
        } else if (cfg.color_space == 6) {
            float yc[3];
            rgb_to_plugin_ycrcb(cmp, yc);
            cmp[0] = yc[0];
            cmp[1] = yc[1];
            cmp[2] = yc[2];
        }
        bool hit_any = false;
        int hit_idx = -1;
        for (size_t ci = 0; ci < cfg.colors.size(); ++ci) {
            const KeyColor &kc = cfg.colors[ci];
            float key[3] = {kc.rgb.r, kc.rgb.g, kc.rgb.b};
            float comp_scale[3] = {1.0f, 1.0f, 1.0f};
            if (cfg.color_space == 3) {
                rgb_to_plugin_lab76(key, key);
                comp_scale[0] = 151.30099487304688f;
                comp_scale[1] = 264.36700439453125f;
                comp_scale[2] = 295.572998046875f;
            } else if (cfg.color_space == 4) {
                rgb_to_plugin_lab76(key, key);
                comp_scale[0] = 151.30099487304688f;
                comp_scale[1] = 264.36700439453125f;
                comp_scale[2] = 295.572998046875f;
            } else if (cfg.color_space == 2) {
                rgb_to_plugin_hsv(key, key);
            } else if (cfg.color_space == 5) {
                rgb_to_plugin_yuv(key, key);
            } else if (cfg.color_space == 6) {
                rgb_to_plugin_ycrcb(key, key);
            }
            bool hit = false;
            if (cfg.color_space == 5) {
                // YUV comparator FUN_180004850: ch0 (Y) direct, ch1 (U)
                // normalized via (double)u*1.146789+0.5, ch2 (V) ignored.
                const float t0 = cfg.per_component ? kc.comp[0] : cfg.threshold;
                const float t1 = cfg.per_component ? kc.comp[1] : cfg.threshold;
                auto un = [](float u) {
                    return static_cast<float>(static_cast<double>(u) * 1.146788990825688 + 0.5);
                };
                hit = std::fabs(cmp[0] - key[0]) <= t0 + eps8
                    && std::fabs(un(cmp[1]) - un(key[1])) <= t1 + eps8;
            } else if (cfg.color_space == 6) {
                // YCrCb comparator FUN_180004910: ch0 (Y), ch1 (Cb); ch2 (Cr) ignored.
                const float t0 = cfg.per_component ? kc.comp[0] : cfg.threshold;
                const float t1 = cfg.per_component ? kc.comp[1] : cfg.threshold;
                hit = std::fabs(cmp[0] - key[0]) <= t0 + eps8
                    && std::fabs(cmp[1] - key[1]) <= t1 + eps8;
            } else if (cfg.color_space == 4) {
                // Lab94 comparator FUN_180004510.
                if (cfg.per_component) {
                    hit = std::fabs(cmp[0] - key[0]) <= (eps8 + kc.comp[0]) * comp_scale[0]
                        && std::fabs(cmp[1] - key[1]) <= (eps8 + kc.comp[1]) * comp_scale[1]
                        && std::fabs(cmp[2] - key[2]) <= (eps8 + kc.comp[2]) * comp_scale[2];
                } else {
                    hit = lab94_distance(key, cmp)
                        <= static_cast<float>(static_cast<double>(eps8 + cfg.threshold) * 352.978);
                }
            } else if (cfg.color_space == 2) {
                // HSV comparator FUN_180004290: comp_scale = {1,1,1}.
                if (cfg.per_component) {
                    float sh = cmp[0];
                    if (sh < key[0]) sh += 1.0f;  // hue wraps in [0,1]
                    hit = (sh - key[0]) <= eps8 + kc.comp[0]
                        && std::fabs(cmp[1] - key[1]) <= eps8 + kc.comp[1]
                        && std::fabs(cmp[2] - key[2]) <= eps8 + kc.comp[2];
                } else {
                    const float d0 = cmp[0] - key[0];
                    const float d1 = cmp[1] - key[1];
                    const float d2 = cmp[2] - key[2];
                    const float dist = std::sqrt(d0 * d0 + d1 * d1 + d2 * d2);
                    hit = dist <= std::sqrt(3.0f) * (eps8 + cfg.threshold);
                }
            } else if (cfg.per_component) {
                hit = std::fabs(cmp[0] - key[0]) <= eps8 + kc.comp[0] * comp_scale[0]
                    && std::fabs(cmp[1] - key[1]) <= eps8 + kc.comp[1] * comp_scale[1]
                    && std::fabs(cmp[2] - key[2]) <= eps8 + kc.comp[2] * comp_scale[2];
            } else {
                float mean = (std::fabs(cmp[0] - key[0]) / comp_scale[0]
                            + std::fabs(cmp[1] - key[1]) / comp_scale[1]
                            + std::fabs(cmp[2] - key[2]) / comp_scale[2]) / 3.0f;
                hit = mean <= cfg.threshold;
            }
            if (hit && hit_idx == -1) hit_idx = static_cast<int>(ci);
            hit_any = hit_any || hit;
        }
        matched[i] = hit_any ? 1 : 0;
        matched_idx[i] = hit_idx;
    }

    std::vector<unsigned char> matched_before_edge_thin = matched;
    std::vector<float> edge_thin_dist;
    float edge_thin_limit = 0.0f;
    if (cfg.edge_thin_amount < 0.0f) {
        std::vector<unsigned char> nonmatch(n, 0);
        for (int i = 0; i < n; ++i) nonmatch[i] = matched[i] ? 0 : 1;
        edge_thin_dist = matte_distance(nonmatch, w, h, cfg.edge_thin_distance_type);
        edge_thin_limit = std::fabs(cfg.edge_thin_amount) + ((cfg.edge_thin_distance_type == 0 || cfg.edge_thin_distance_type == 2) ? 1.0f : 0.0f);
        for (int i = 0; i < n; ++i) matched[i] = (matched[i] && edge_thin_dist[i] > edge_thin_limit) ? 1 : 0;
    } else if (cfg.edge_thin_amount > 0.0f) {
        edge_thin_dist = matte_distance(matched, w, h, cfg.edge_thin_distance_type);
        edge_thin_limit = cfg.edge_thin_amount;
        for (int i = 0; i < n; ++i) matched[i] = (matched[i] || edge_thin_dist[i] <= cfg.edge_thin_amount) ? 1 : 0;
    }

    std::vector<unsigned char> keep_mask(n, 0);
    for (int i = 0; i < n; ++i) {
        bool keep = cfg.color_keep ? matched[i] != 0 : matched[i] == 0;
        keep_mask[i] = keep ? 1 : 0;
        size_t p = static_cast<size_t>(i) * 4;
        if (!keep) {
            out.rgba[p + 0] = 0;
            out.rgba[p + 1] = 0;
            out.rgba[p + 2] = 0;
            out.rgba[p + 3] = 0;
        } else {
            // Replace output (keyer FUN_1800029d0 tail @LAB_180003253): the
            // matched pixel's RGB is overwritten with Replace Color N, gated on
            //   ctx+0x24 (Color Keep) && ctx+0x4d (Enable Replace)
            //   && ctx+0x53d+idx (Use Replace Color N) && idx != -1.
            // Scale = FUN_180011790(8-bit) = 255; cast is truncating int.
            // Alpha is untouched (matched -> keeps original alpha).
            const int idx = matched_idx[i];
            if (cfg.color_keep && cfg.enable_replace && idx >= 0
                && cfg.colors[static_cast<size_t>(idx)].use_replace) {
                const float *rep = cfg.colors[static_cast<size_t>(idx)].replace_rgb;
                out.rgba[p + 0] = static_cast<unsigned char>(static_cast<int>(255.0f * rep[0]));
                out.rgba[p + 1] = static_cast<unsigned char>(static_cast<int>(255.0f * rep[1]));
                out.rgba[p + 2] = static_cast<unsigned char>(static_cast<int>(255.0f * rep[2]));
            }
        }
    }
    if (cfg.edge_blur_amount != 0.0f) {
        std::vector<unsigned char> boundary = boundary8(keep_mask, w, h);
        std::vector<float> dist = edge_blur_distance(boundary, w, h, cfg.edge_blur_distance_type);
        for (int i = 0; i < n; ++i) {
            const bool keep = keep_mask[i] != 0;
            const float weight = edge_blur_weight(keep, dist[static_cast<size_t>(i)], cfg.edge_blur_amount, cfg.edge_blur_direction);
            size_t p = static_cast<size_t>(i) * 4;
            unsigned char src_r = ((!keep && weight != 0.0f) ? input.rgba[p + 0] : out.rgba[p + 0]);
            unsigned char src_g = ((!keep && weight != 0.0f) ? input.rgba[p + 1] : out.rgba[p + 1]);
            unsigned char src_b = ((!keep && weight != 0.0f) ? input.rgba[p + 2] : out.rgba[p + 2]);
            unsigned char src_alpha = ((!keep && weight != 0.0f) ? input.rgba[p + 3] : out.rgba[p + 3]);
            int red = static_cast<int>(static_cast<float>(src_r) * weight);
            int green = static_cast<int>(static_cast<float>(src_g) * weight);
            int blue = static_cast<int>(static_cast<float>(src_b) * weight);
            int alpha = static_cast<int>(static_cast<float>(src_alpha) * weight);
            out.rgba[p + 0] = static_cast<unsigned char>(std::clamp(red, 0, 255));
            out.rgba[p + 1] = static_cast<unsigned char>(std::clamp(green, 0, 255));
            out.rgba[p + 2] = static_cast<unsigned char>(std::clamp(blue, 0, 255));
            out.rgba[p + 3] = static_cast<unsigned char>(std::clamp(alpha, 0, 255));
        }
        for (const TracePixel &pixel : trace_pixels) {
            if (0 <= pixel.x && pixel.x < w && 0 <= pixel.y && pixel.y < h) {
                const int i = pixel.y * w + pixel.x;
                const size_t p = static_cast<size_t>(i) * 4;
                const bool keep = keep_mask[i] != 0;
                const float weight = edge_blur_weight(
                    keep,
                    dist[static_cast<size_t>(i)],
                    cfg.edge_blur_amount,
                    cfg.edge_blur_direction);
                std::fprintf(
                    stderr,
                    "OLMCOLORKEY_TRACE x=%d y=%d matched0=%u matched1=%u keep=%u "
                    "edge_thin_amount=%.9g edge_thin_limit=%.9g edge_thin_dist=%.9g "
                    "edge_blur_amount=%.9g edge_blur_dir=%d edge_blur_dist_type=%d "
                    "boundary=%u edge_blur_dist=%.9g edge_blur_weight=%.9g "
                    "final_rgba=(%u,%u,%u,%u)\n",
                    pixel.x,
                    pixel.y,
                    matched_before_edge_thin[i],
                    matched[i],
                    keep_mask[i],
                    cfg.edge_thin_amount,
                    edge_thin_limit,
                    edge_thin_dist.empty() ? -1.0f : edge_thin_dist[static_cast<size_t>(i)],
                    cfg.edge_blur_amount,
                    cfg.edge_blur_direction,
                    cfg.edge_blur_distance_type,
                    boundary[i],
                    dist[static_cast<size_t>(i)],
                    weight,
                    out.rgba[p + 0],
                    out.rgba[p + 1],
                    out.rgba[p + 2],
                    out.rgba[p + 3]);
            }
        }
    } else {
        for (const TracePixel &pixel : trace_pixels) {
            if (0 <= pixel.x && pixel.x < w && 0 <= pixel.y && pixel.y < h) {
                const int i = pixel.y * w + pixel.x;
                const size_t p = static_cast<size_t>(i) * 4;
                std::fprintf(
                    stderr,
                    "OLMCOLORKEY_TRACE x=%d y=%d matched0=%u matched1=%u keep=%u "
                    "edge_thin_amount=%.9g edge_thin_limit=%.9g edge_thin_dist=%.9g "
                    "edge_blur_amount=%.9g edge_blur_dir=%d edge_blur_dist_type=%d "
                    "final_rgba=(%u,%u,%u,%u)\n",
                    pixel.x,
                    pixel.y,
                    matched_before_edge_thin[i],
                    matched[i],
                    keep_mask[i],
                    cfg.edge_thin_amount,
                    edge_thin_limit,
                    edge_thin_dist.empty() ? -1.0f : edge_thin_dist[static_cast<size_t>(i)],
                    cfg.edge_blur_amount,
                    cfg.edge_blur_direction,
                    cfg.edge_blur_distance_type,
                    out.rgba[p + 0],
                    out.rgba[p + 1],
                    out.rgba[p + 2],
                    out.rgba[p + 3]);
            }
        }
    }
    return out;
}

void usage(const char *argv0) {
    std::fprintf(stderr, "usage: %s --input in.png --params params.json --output out.png\n", argv0);
}

} // namespace

int main(int argc, char **argv) {
    std::string input_path;
    std::string params_path;
    std::string output_path;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        auto need_value = [&](const char *name) -> std::string {
            if (i + 1 >= argc) {
                usage(argv[0]);
                throw std::runtime_error(std::string("missing value for ") + name);
            }
            return argv[++i];
        };
        if (arg == "--input") input_path = need_value("--input");
        else if (arg == "--params") params_path = need_value("--params");
        else if (arg == "--output") output_path = need_value("--output");
        else if (arg == "--help" || arg == "-h") {
            usage(argv[0]);
            return 0;
        } else {
            usage(argv[0]);
            std::fprintf(stderr, "unknown argument: %s\n", arg.c_str());
            return 2;
        }
    }
    if (input_path.empty() || params_path.empty() || output_path.empty()) {
        usage(argv[0]);
        return 2;
    }

    try {
        Image input = read_png(input_path);
        ColorKeyParams params = read_params(params_path);
        Image output = render_olmcolorkey(input, params);
        write_png(output_path, output);
        std::printf("wrote: %s\n", output_path.c_str());
    } catch (const std::exception &e) {
        std::fprintf(stderr, "error: %s\n", e.what());
        return 1;
    }
    return 0;
}
