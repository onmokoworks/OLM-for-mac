#include <png.h>

#include <algorithm>
#include <cmath>
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

struct ToonDilateParams {
    double search_radius = 0.0;
    double comp_width = 1920.0;
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
        if (name && name->type == Json::String && name->string_value == "OLM Toon Dilate") is_target = true;
        if (match && match->type == Json::String && match->string_value == "OLM Toon Dilate") is_target = true;
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

ToonDilateParams read_params(const std::string &path, double cli_comp_width) {
    Json root = JsonParser(read_text_file(path)).parse();
    auto params = param_map(root);
    auto get = [&](const char *name) -> const Json * {
        auto it = params.find(name);
        return it == params.end() ? nullptr : it->second;
    };

    ToonDilateParams tp;
    tp.search_radius = json_number_or(get("Search Radius"), 0.0);
    if (const Json *comp = root.get("comp")) {
        tp.comp_width = json_number_or(comp->get("width"), tp.comp_width);
    }
    if (cli_comp_width > 0.0) tp.comp_width = cli_comp_width;
    return tp;
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

Image render_olmtoondilate(const Image &input, const ToonDilateParams &params) {
    Image out = input;
    const int w = input.width;
    const int h = input.height;
    if (params.search_radius <= 0.0) return out;

    const int r_eff = static_cast<int>(std::ceil(params.search_radius * (static_cast<double>(w) / params.comp_width)));
    if (r_eff <= 0) return out;

    const int n = w * h;
    std::vector<int> dist(n, -1);
    std::vector<int> sx(n, -1);
    std::vector<int> sy(n, -1);
    std::deque<int> queue;

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const int idx = y * w + x;
            if (input.rgba[static_cast<size_t>(idx) * 4 + 3] == 255) {
                dist[idx] = 0;
                sx[idx] = x;
                sy[idx] = y;
                queue.push_back(idx);
            }
        }
    }
    if (queue.empty()) return out;

    constexpr int DX[8] = {-1, 0, 1, -1, 1, -1, 0, 1};
    constexpr int DY[8] = {-1, -1, -1, 0, 0, 1, 1, 1};
    while (!queue.empty()) {
        int idx = queue.front();
        queue.pop_front();
        int d = dist[idx];
        if (d >= r_eff) continue;
        int x = idx % w;
        int y = idx / w;
        for (int k = 0; k < 8; ++k) {
            int nx = x + DX[k];
            int ny = y + DY[k];
            if (nx < 0 || nx >= w || ny < 0 || ny >= h) continue;
            int nidx = ny * w + nx;
            if (dist[nidx] >= 0) continue;
            dist[nidx] = d + 1;
            sx[nidx] = sx[idx];
            sy[nidx] = sy[idx];
            queue.push_back(nidx);
        }
    }

    for (int idx = 0; idx < n; ++idx) {
        if (dist[idx] <= 0 || dist[idx] > r_eff) continue;
        const size_t dst = static_cast<size_t>(idx) * 4;
        if (input.rgba[dst + 3] == 255) continue;
        int source_idx = sy[idx] * w + sx[idx];
        const size_t src = static_cast<size_t>(source_idx) * 4;
        out.rgba[dst + 0] = input.rgba[src + 0];
        out.rgba[dst + 1] = input.rgba[src + 1];
        out.rgba[dst + 2] = input.rgba[src + 2];
        out.rgba[dst + 3] = input.rgba[src + 3];
    }
    return out;
}

struct Args {
    std::string input;
    std::string params;
    std::string output;
    double comp_width = 0.0;
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
        } else if (key == "--comp-width") {
            args.comp_width = std::strtod(need_value("--comp-width").c_str(), nullptr);
        } else if (key == "--help" || key == "-h") {
            std::printf("Usage: olmtoondilate_cli --input in.png --params params.json --output out.png [--comp-width 1920]\n");
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
        ToonDilateParams params = read_params(args.params, args.comp_width);
        Image output = render_olmtoondilate(input, params);
        write_png(args.output, output);
        std::printf("wrote: %s (search_radius=%.3f comp_width=%.3f)\n",
                    args.output.c_str(), params.search_radius, params.comp_width);
        return 0;
    } catch (const std::exception &ex) {
        std::fprintf(stderr, "olmtoondilate_cli: %s\n", ex.what());
        return 1;
    }
}
