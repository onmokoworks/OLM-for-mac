#include <png.h>

#include <algorithm>
#include <cmath>
#include <cstddef>
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

constexpr long BIAS_DIR_VERTICAL = 1;
constexpr long BIAS_DIR_HORIZONTAL = 2;

struct Image {
    int width = 0;
    int height = 0;
    std::vector<unsigned char> rgba;
};

struct BlurParams {
    float blur_amount = 1.0f;
    float blur_smoothness = 1.0f;
    float comp_width = 0.0f;
    long repeat = 2;
    long bias_dir = BIAS_DIR_VERTICAL;
    long legacy = 0;
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

std::string lower_ascii(std::string text) {
    for (char &c : text) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return text;
}

long bias_direction_or(const Json *value, long fallback) {
    if (!value) return fallback;
    if (value->type == Json::String) {
        std::string s = lower_ascii(value->string_value);
        if (s.find("vertical") != std::string::npos) return BIAS_DIR_VERTICAL;
        if (s.find("horizontal") != std::string::npos) return BIAS_DIR_HORIZONTAL;
    }
    return json_int_or(value, fallback);
}

const Json *find_effect_params(const Json &root) {
    const Json *scope = &root;
    if (const Json *params = root.get("params")) scope = params;
    const Json *effects = scope->get("effects");
    if (!effects || effects->type != Json::Array) return scope;
    for (const Json &effect : effects->array_value) {
        const Json *name = effect.get("name");
        if (name && name->type == Json::String && name->string_value == "OLM Blur") {
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

BlurParams read_params(const std::string &path) {
    Json root = JsonParser(read_text_file(path)).parse();
    auto params = param_map(root);
    auto get = [&](const char *name) -> const Json * {
        auto it = params.find(name);
        return it == params.end() ? nullptr : it->second;
    };

    BlurParams bp;
    bp.blur_amount = static_cast<float>(json_number_or(get("Blur Amount"), bp.blur_amount));
    bp.blur_smoothness = static_cast<float>(json_number_or(get("Blur Smoothness"), bp.blur_smoothness));
    bp.repeat = std::max<long>(1, json_int_or(get("Number of Repeat"), bp.repeat));
    bp.bias_dir = bias_direction_or(get("Bias Direction"), bp.bias_dir);
    bp.legacy = json_int_or(get("Legacy"), bp.legacy) != 0 ? 1 : 0;
    if (const Json *comp = root.get("comp")) {
        float comp_width = static_cast<float>(json_number_or(comp->get("width"), 0.0));
        if (comp_width > 0.0f) {
            bp.comp_width = comp_width;
        }
    }
    return bp;
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

void blur_1d_horizontal(const float *srcRGB, const unsigned char *srcA, float *dstRGB, unsigned char *dstA,
                        long w, long h, long radius, const float *weights) {
    for (long y = 0; y < h; ++y) {
        const float *srow = srcRGB + y * w * 3;
        float *drow = dstRGB + y * w * 3;
        const unsigned char *sa = srcA + y * w;
        unsigned char *da = dstA + y * w;
        for (long x = 0; x < w; ++x) {
            da[x] = sa[x];
            if (!sa[x]) {
                drow[x * 3 + 0] = srow[x * 3 + 0];
                drow[x * 3 + 1] = srow[x * 3 + 1];
                drow[x * 3 + 2] = srow[x * 3 + 2];
                continue;
            }
            float sumR = 0, sumG = 0, sumB = 0, sumW = 0;
            long left = (x < radius) ? x : radius;
            for (long k = 0; k <= left; ++k) {
                long xi = x - k;
                if (!sa[xi]) break;
                float w_ = weights[k];
                sumW += w_;
                sumR += w_ * srow[xi * 3 + 0];
                sumG += w_ * srow[xi * 3 + 1];
                sumB += w_ * srow[xi * 3 + 2];
            }
            long right = (w - 1 - x < radius) ? (w - 1 - x) : radius;
            for (long k = 1; k <= right; ++k) {
                long xi = x + k;
                if (!sa[xi]) break;
                float w_ = weights[k];
                sumW += w_;
                sumR += w_ * srow[xi * 3 + 0];
                sumG += w_ * srow[xi * 3 + 1];
                sumB += w_ * srow[xi * 3 + 2];
            }
            if (sumW == 0) {
                drow[x * 3 + 0] = drow[x * 3 + 1] = drow[x * 3 + 2] = 0;
            } else {
                float inv = 1.0f / sumW;
                drow[x * 3 + 0] = sumR * inv;
                drow[x * 3 + 1] = sumG * inv;
                drow[x * 3 + 2] = sumB * inv;
            }
        }
    }
}

void blur_1d_vertical(const float *srcRGB, const unsigned char *srcA, float *dstRGB, unsigned char *dstA,
                      long w, long h, long radius, const float *weights) {
    for (long y = 0; y < h; ++y) {
        for (long x = 0; x < w; ++x) {
            long idx = y * w + x;
            dstA[idx] = srcA[idx];
            if (!srcA[idx]) {
                dstRGB[idx * 3 + 0] = srcRGB[idx * 3 + 0];
                dstRGB[idx * 3 + 1] = srcRGB[idx * 3 + 1];
                dstRGB[idx * 3 + 2] = srcRGB[idx * 3 + 2];
                continue;
            }
            float sumR = 0, sumG = 0, sumB = 0, sumW = 0;
            long up = (y < radius) ? y : radius;
            for (long k = 0; k <= up; ++k) {
                long yi = y - k;
                long i = yi * w + x;
                if (!srcA[i]) break;
                float w_ = weights[k];
                sumW += w_;
                sumR += w_ * srcRGB[i * 3 + 0];
                sumG += w_ * srcRGB[i * 3 + 1];
                sumB += w_ * srcRGB[i * 3 + 2];
            }
            long down = (h - 1 - y < radius) ? (h - 1 - y) : radius;
            for (long k = 1; k <= down; ++k) {
                long yi = y + k;
                long i = yi * w + x;
                if (!srcA[i]) break;
                float w_ = weights[k];
                sumW += w_;
                sumR += w_ * srcRGB[i * 3 + 0];
                sumG += w_ * srcRGB[i * 3 + 1];
                sumB += w_ * srcRGB[i * 3 + 2];
            }
            if (sumW == 0) {
                dstRGB[idx * 3 + 0] = dstRGB[idx * 3 + 1] = dstRGB[idx * 3 + 2] = 0;
            } else {
                float inv = 1.0f / sumW;
                dstRGB[idx * 3 + 0] = sumR * inv;
                dstRGB[idx * 3 + 1] = sumG * inv;
                dstRGB[idx * 3 + 2] = sumB * inv;
            }
        }
    }
}

void legacy_blur_1d_horizontal(const float *srcRGB, const unsigned char *srcA, float *dstRGB, unsigned char *dstA,
                               long w, long h, long radius, const float *kernel) {
    for (long y = 0; y < h; ++y) {
        for (long x = 0; x < w; ++x) {
            long idx = y * w + x;
            dstA[idx] = srcA[idx];
            if (!srcA[idx]) {
                dstRGB[idx * 3 + 0] = srcRGB[idx * 3 + 0];
                dstRGB[idx * 3 + 1] = srcRGB[idx * 3 + 1];
                dstRGB[idx * 3 + 2] = srcRGB[idx * 3 + 2];
                continue;
            }
            float sumR = 0.0f, sumG = 0.0f, sumB = 0.0f, sumW = 0.0f;
            bool all_same = true;
            bool have_prev = false;
            float prevR = 0.0f, prevG = 0.0f, prevB = 0.0f;
            for (long off = -radius; off <= radius; ++off) {
                long sx = x + off;
                if (sx <= 0 || sx >= w) continue;
                long si = y * w + sx;
                if (!srcA[si]) break;
                float wr = kernel[radius + off];
                sumW += wr;
                sumR += wr * srcRGB[si * 3 + 0];
                sumG += wr * srcRGB[si * 3 + 1];
                sumB += wr * srcRGB[si * 3 + 2];
                float curR = srcRGB[si * 3 + 0];
                float curG = srcRGB[si * 3 + 1];
                float curB = srcRGB[si * 3 + 2];
                if (have_prev && (curR != prevR || curG != prevG || curB != prevB)) {
                    all_same = false;
                }
                prevR = curR;
                prevG = curG;
                prevB = curB;
                have_prev = true;
            }
            if (all_same || sumW == 0.0f) {
                dstRGB[idx * 3 + 0] = srcRGB[idx * 3 + 0];
                dstRGB[idx * 3 + 1] = srcRGB[idx * 3 + 1];
                dstRGB[idx * 3 + 2] = srcRGB[idx * 3 + 2];
            } else {
                float inv = 1.0f / sumW;
                dstRGB[idx * 3 + 0] = sumR * inv;
                dstRGB[idx * 3 + 1] = sumG * inv;
                dstRGB[idx * 3 + 2] = sumB * inv;
            }
        }
    }
}

void legacy_blur_1d_vertical(const float *srcRGB, const unsigned char *srcA, float *dstRGB, unsigned char *dstA,
                             long w, long h, long radius, const float *kernel) {
    for (long y = 0; y < h; ++y) {
        for (long x = 0; x < w; ++x) {
            long idx = y * w + x;
            dstA[idx] = srcA[idx];
            if (!srcA[idx]) {
                dstRGB[idx * 3 + 0] = srcRGB[idx * 3 + 0];
                dstRGB[idx * 3 + 1] = srcRGB[idx * 3 + 1];
                dstRGB[idx * 3 + 2] = srcRGB[idx * 3 + 2];
                continue;
            }
            float sumR = 0.0f, sumG = 0.0f, sumB = 0.0f, sumW = 0.0f;
            bool all_same = true;
            bool have_prev = false;
            float prevR = 0.0f, prevG = 0.0f, prevB = 0.0f;
            for (long off = -radius; off <= radius; ++off) {
                long sy = y + off;
                if (sy <= 0 || sy >= h) continue;
                long si = sy * w + x;
                if (!srcA[si]) break;
                float wr = kernel[radius + off];
                sumW += wr;
                sumR += wr * srcRGB[si * 3 + 0];
                sumG += wr * srcRGB[si * 3 + 1];
                sumB += wr * srcRGB[si * 3 + 2];
                float curR = srcRGB[si * 3 + 0];
                float curG = srcRGB[si * 3 + 1];
                float curB = srcRGB[si * 3 + 2];
                if (have_prev && (curR != prevR || curG != prevG || curB != prevB)) {
                    all_same = false;
                }
                prevR = curR;
                prevG = curG;
                prevB = curB;
                have_prev = true;
            }
            if (all_same || sumW == 0.0f) {
                dstRGB[idx * 3 + 0] = srcRGB[idx * 3 + 0];
                dstRGB[idx * 3 + 1] = srcRGB[idx * 3 + 1];
                dstRGB[idx * 3 + 2] = srcRGB[idx * 3 + 2];
            } else {
                float inv = 1.0f / sumW;
                dstRGB[idx * 3 + 0] = sumR * inv;
                dstRGB[idx * 3 + 1] = sumG * inv;
                dstRGB[idx * 3 + 2] = sumB * inv;
            }
        }
    }
}

Image render_olmblur(const Image &input, const BlurParams &bp) {
    Image output = input;
    long w = input.width, h = input.height;
    if (w <= 0 || h <= 0 || bp.blur_amount <= 0.0f) return output;

    float blur_amount = bp.blur_amount;
    if (bp.comp_width > 0.0f) {
        blur_amount *= static_cast<float>(w) / bp.comp_width;
    }
    if (blur_amount <= 0.0f) return output;

    size_t npix = static_cast<size_t>(w) * static_cast<size_t>(h);
    std::vector<float> buf1(npix * 3), buf2(npix * 3);
    std::vector<unsigned char> alpha1(npix), alpha2(npix);

    for (size_t i = 0; i < npix; ++i) {
        buf1[i * 3 + 0] = static_cast<float>(input.rgba[i * 4 + 0]);
        buf1[i * 3 + 1] = static_cast<float>(input.rgba[i * 4 + 1]);
        buf1[i * 3 + 2] = static_cast<float>(input.rgba[i * 4 + 2]);
        alpha1[i] = input.rgba[i * 4 + 3] ? 1 : 0;
    }

    long max_radius = static_cast<long>(blur_amount) + 2;
    std::vector<float> weights(static_cast<size_t>(max_radius * 2 + 1));

    if (bp.legacy) {
        long radius = static_cast<long>(blur_amount);
        if (radius > 0) {
            float smoothness = bp.blur_smoothness;
            if (smoothness <= 0.0f) smoothness = 1.0f;
            float sigma_base = ((blur_amount * smoothness) / 100.0f) * (blur_amount / 3.0f);
            for (long iter = 1; iter <= bp.repeat; ++iter) {
                float sigma = sigma_base / static_cast<float>(iter);
                if (sigma <= 0.0f) break;
                float denom = 2.0f * sigma * sigma;
                weights[radius] = 1.0f;
                for (long k = 1; k <= radius; ++k) {
                    float v = std::exp(-static_cast<float>(k * k) / denom);
                    weights[radius - k] = v;
                    weights[radius + k] = v;
                }
                if (bp.bias_dir == BIAS_DIR_VERTICAL) {
                    legacy_blur_1d_horizontal(buf1.data(), alpha1.data(), buf2.data(), alpha2.data(), w, h, radius, weights.data());
                    legacy_blur_1d_vertical(buf2.data(), alpha2.data(), buf1.data(), alpha1.data(), w, h, radius, weights.data());
                } else if (bp.bias_dir == BIAS_DIR_HORIZONTAL) {
                    legacy_blur_1d_vertical(buf1.data(), alpha1.data(), buf2.data(), alpha2.data(), w, h, radius, weights.data());
                    legacy_blur_1d_horizontal(buf2.data(), alpha2.data(), buf1.data(), alpha1.data(), w, h, radius, weights.data());
                }
            }
        }
    } else {
        float decay = 1.0f;
        if (bp.repeat > 1) decay = std::pow(3.0f / blur_amount, 1.0f / static_cast<float>(bp.repeat - 1));

        for (long iter = 0; iter < bp.repeat; ++iter) {
            double radius_d = static_cast<double>(blur_amount) *
                              std::pow(static_cast<double>(decay), static_cast<double>(iter));
            long radius = static_cast<long>(radius_d);
            if (radius == 0) break;
            float sigma = static_cast<float>(radius_d) / 3.0f;
            float denom = 2.0f * sigma * sigma;
            for (long k = 0; k <= radius; ++k) {
                weights[k] = std::exp(-static_cast<float>(k * k) / denom);
            }
            if (bp.bias_dir == BIAS_DIR_VERTICAL) {
                blur_1d_horizontal(buf1.data(), alpha1.data(), buf2.data(), alpha2.data(), w, h, radius, weights.data());
                blur_1d_vertical(buf2.data(), alpha2.data(), buf1.data(), alpha1.data(), w, h, radius, weights.data());
            } else if (bp.bias_dir == BIAS_DIR_HORIZONTAL) {
                blur_1d_vertical(buf1.data(), alpha1.data(), buf2.data(), alpha2.data(), w, h, radius, weights.data());
                blur_1d_horizontal(buf2.data(), alpha2.data(), buf1.data(), alpha1.data(), w, h, radius, weights.data());
            }
        }
    }

    if (const char *trace = std::getenv("OLMBLUR_TRACE_PIXELS")) {
        const char *p = trace;
        while (*p) {
            int tx = -1;
            int ty = -1;
            int consumed = 0;
            if (std::sscanf(p, "%d,%d%n", &tx, &ty, &consumed) == 2 && consumed > 0) {
                if (0 <= tx && tx < input.width && 0 <= ty && ty < input.height) {
                    size_t ti = static_cast<size_t>(ty) * static_cast<size_t>(input.width) +
                                static_cast<size_t>(tx);
                    std::fprintf(stderr,
                                 "OLMBLUR_TRACE x=%d y=%d rgb=(%.9g,%.9g,%.9g) rgb_hex=(%a,%a,%a) floor05=(%.9g,%.9g,%.9g) nearby=(%.9g,%.9g,%.9g) legacy=%ld repeat=%ld\n",
                                 tx, ty,
                                 buf1[ti * 3 + 0], buf1[ti * 3 + 1], buf1[ti * 3 + 2],
                                 static_cast<double>(buf1[ti * 3 + 0]),
                                 static_cast<double>(buf1[ti * 3 + 1]),
                                 static_cast<double>(buf1[ti * 3 + 2]),
                                 std::floor(buf1[ti * 3 + 0] + 0.5f),
                                 std::floor(buf1[ti * 3 + 1] + 0.5f),
                                 std::floor(buf1[ti * 3 + 2] + 0.5f),
                                 std::nearbyint(buf1[ti * 3 + 0]),
                                 std::nearbyint(buf1[ti * 3 + 1]),
                                 std::nearbyint(buf1[ti * 3 + 2]),
                                 bp.legacy, bp.repeat);
                }
                p += consumed;
                while (*p == ';' || *p == ' ' || *p == '\t' || *p == '\n') ++p;
            } else {
                break;
            }
        }
    }

    for (size_t i = 0; i < npix; ++i) {
        for (int c = 0; c < 3; ++c) {
            float v = bp.legacy ? std::floor(buf1[i * 3 + c] + 0.5f)
                                : std::nearbyint(buf1[i * 3 + c]);
            v = std::max(0.0f, std::min(255.0f, v));
            output.rgba[i * 4 + c] = static_cast<unsigned char>(v);
        }
    }
    return output;
}

struct Args {
    std::string input;
    std::string params;
    std::string output;
};

Args parse_args(int argc, char **argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        std::string key = argv[i];
        if ((key == "--input" || key == "--params" || key == "--output") && i + 1 < argc) {
            std::string value = argv[++i];
            if (key == "--input") args.input = value;
            else if (key == "--params") args.params = value;
            else args.output = value;
        } else if (key == "--help" || key == "-h") {
            std::printf("Usage: olmblur_cli --input in.png --params params.json --output out.png\n");
            std::exit(0);
        } else {
            throw std::runtime_error("unknown or incomplete argument: " + key);
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
        BlurParams params = read_params(args.params);
        Image output = render_olmblur(input, params);
        write_png(args.output, output);
        std::printf("wrote: %s\n", args.output.c_str());
        return 0;
    } catch (const std::exception &ex) {
        std::fprintf(stderr, "olmblur_cli: %s\n", ex.what());
        return 1;
    }
}
