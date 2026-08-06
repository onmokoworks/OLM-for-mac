// AE-free CLI harness for OLMSmoother.
//
// Compiles the mac port (mac/OLMSmoother/Mac/OLMSmoother_port.cpp) against the
// shim headers in ./shim and drives its 8-bit render path on a PNG, so the
// MLAA-style smoother can be verified against Windows reference renders without
// After Effects.
//
//   olmsmoother_cli --input in.png --params case.json --output out.png
//
// Params JSON is the per-case file emitted by run_algorithm_cases.py; the
// "OLM Smoother" effect's "Use Color Key", "Color Key", and "Do Smooth Range"
// (= the Tolerance slider) values are read out of it.

#include <png.h>

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Pull in the literal port + its statics (DispatchRender, kernels, ...).
// Its #include "OLMSmoother.h" / "AEFX_SuiteHandlerTemplate.h" resolve to the
// shims in ./shim via the build's -I flag.
#include "OLMSmoother_port.cpp"

namespace {

struct Image {
	int width = 0;
	int height = 0;
	std::vector<uint8_t> rgba;  // width*height*4, R,G,B,A
};

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
	image.rgba.resize(static_cast<size_t>(width) * height * 4);
	std::vector<png_bytep> rows(height);
	for (png_uint_32 y = 0; y < height; ++y) rows[y] = image.rgba.data() + static_cast<size_t>(y) * width * 4;
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
	for (int y = 0; y < image.height; ++y)
		rows[y] = const_cast<png_bytep>(image.rgba.data() + static_cast<size_t>(y) * image.width * 4);
	png_write_image(png, rows.data());
	png_write_end(png, nullptr);
	png_destroy_write_struct(&png, &info);
	std::fclose(fp);
}

// Minimal scan of the per-case params JSON: locate a "name":"<key>" object and
// return the first numeric "value" that follows it. Sufficient for the flat
// effect-param layout emitted by run_algorithm_cases.py.
bool find_param_number(const std::string &json, const std::string &key, double &out) {
	std::string needle = "\"" + key + "\"";
	size_t pos = json.find(needle);
	if (pos == std::string::npos) return false;
	size_t vpos = json.find("\"value\"", pos);
	if (vpos == std::string::npos) return false;
	size_t colon = json.find(':', vpos);
	if (colon == std::string::npos) return false;
	size_t i = colon + 1;
	while (i < json.size() && (json[i] == ' ' || json[i] == '\t' || json[i] == '\n' || json[i] == '[')) ++i;
	size_t j = i;
	while (j < json.size() && (std::isdigit((unsigned char)json[j]) || json[j] == '-' || json[j] == '+' || json[j] == '.' || json[j] == 'e' || json[j] == 'E')) ++j;
	if (j == i) return false;
	try { out = std::stod(json.substr(i, j - i)); } catch (...) { return false; }
	return true;
}

bool find_param_color(const std::string &json, const std::string &key,
	                  uint8_t &red, uint8_t &green, uint8_t &blue) {
	std::string needle = "\"" + key + "\"";
	size_t pos = json.find(needle);
	if (pos == std::string::npos) return false;
	size_t vpos = json.find("\"value\"", pos);
	if (vpos == std::string::npos) return false;
	size_t cursor = json.find('[', vpos);
	if (cursor == std::string::npos) return false;
	double values[3]{};
	for (int component = 0; component < 3; ++component) {
		++cursor;
		while (cursor < json.size() &&
		       (json[cursor] == ' ' || json[cursor] == '\t' ||
		        json[cursor] == '\n' || json[cursor] == ',')) ++cursor;
		char *end = nullptr;
		values[component] = std::strtod(json.c_str() + cursor, &end);
		if (end == json.c_str() + cursor) return false;
		cursor = static_cast<size_t>(end - json.c_str());
	}
	auto to_byte = [](double value) -> uint8_t {
		if (value < 0.0) value = 0.0;
		if (value <= 1.0) value *= 255.0;
		if (value > 255.0) value = 255.0;
		return static_cast<uint8_t>(value + 0.5);
	};
	red = to_byte(values[0]); green = to_byte(values[1]); blue = to_byte(values[2]);
	return true;
}

std::string slurp(const std::string &path) {
	std::ifstream f(path, std::ios::binary);
	if (!f) throw std::runtime_error("failed to open params " + path);
	std::ostringstream ss;
	ss << f.rdbuf();
	return ss.str();
}

}  // namespace

int main(int argc, char **argv) {
	std::string in_path, params_path, out_path;
	for (int i = 1; i < argc; ++i) {
		std::string a = argv[i];
		auto next = [&]() -> std::string { return (i + 1 < argc) ? argv[++i] : std::string(); };
		if (a == "--input") in_path = next();
		else if (a == "--params") params_path = next();
		else if (a == "--output") out_path = next();
	}
	if (in_path.empty() || out_path.empty()) {
		std::fprintf(stderr, "usage: olmsmoother_cli --input in.png --params case.json --output out.png\n");
		return 2;
	}

	try {
		// Defaults match the OLMSmoother v1 param defaults (Tolerance=6).
		double use_key = 0.0, tolerance = 6.0;
		uint8_t key_red = 255, key_green = 255, key_blue = 255;
		if (!params_path.empty()) {
			std::string json = slurp(params_path);
			find_param_number(json, "Use Color Key", use_key);
			find_param_color(json, "Color Key", key_red, key_green, key_blue);
			// "Do Smooth Range" is the AE label for the Tolerance slider.
			if (!find_param_number(json, "Do Smooth Range", tolerance))
				find_param_number(json, "Tolerance", tolerance);
		}

		Image img = read_png(in_path);
		const int W = img.width, H = img.height;
		const size_t row = static_cast<size_t>(W) * 4;

		// Build ARGB worlds (AE native order) from the RGBA PNG.
		std::vector<uint8_t> in_argb(static_cast<size_t>(H) * row);
		std::vector<uint8_t> out_argb(static_cast<size_t>(H) * row);
		for (size_t p = 0; p < static_cast<size_t>(W) * H; ++p) {
			const uint8_t *s = &img.rgba[p * 4];
			uint8_t *d = &in_argb[p * 4];
			d[0] = s[3];  // A
			d[1] = s[0];  // R
			d[2] = s[1];  // G
			d[3] = s[2];  // B
		}

		PF_EffectWorld input{}, output{};
		input.data = in_argb.data();
		input.width = W; input.height = H; input.rowbytes = static_cast<A_long>(row);
		input.bitdepth = 8; input.extent_hint = PF_LRect{0, 0, W, H};
		output.data = out_argb.data();
		output.width = W; output.height = H; output.rowbytes = static_cast<A_long>(row);
		output.bitdepth = 8; output.extent_hint = PF_LRect{0, 0, W, H};

		PF_ParamDef p_input{}, p_use{}, p_color{}, p_tol{};
		p_use.u.bd.value = (use_key != 0.0) ? 1 : 0;
		p_tol.u.sd.value = static_cast<A_long>(tolerance + 0.5);
		p_color.u.cd.value = PF_Pixel8{255, key_red, key_green, key_blue};
		PF_ParamDef *params[SM_NUM_PARAMS] = {&p_input, &p_use, &p_color, &p_tol};

		PF_InData in_data{};
		PF_Err err = DispatchRender(&in_data, params, &input, &output, 8);
		if (err != PF_Err_NONE) {
			std::fprintf(stderr, "DispatchRender failed: %d\n", (int)err);
			return 1;
		}

		// ARGB -> RGBA back out.
		Image res; res.width = W; res.height = H; res.rgba.resize(static_cast<size_t>(H) * row);
		for (size_t p = 0; p < static_cast<size_t>(W) * H; ++p) {
			const uint8_t *s = &out_argb[p * 4];
			uint8_t *d = &res.rgba[p * 4];
			d[0] = s[1]; d[1] = s[2]; d[2] = s[3]; d[3] = s[0];
		}
		write_png(out_path, res);
		std::printf("wrote: %s (tolerance=%d use_key=%d key=%u,%u,%u)\n", out_path.c_str(),
		            (int)p_tol.u.sd.value, (int)p_use.u.bd.value,
		            (unsigned)key_red, (unsigned)key_green, (unsigned)key_blue);
		return 0;
	} catch (const std::exception &e) {
		std::fprintf(stderr, "error: %s\n", e.what());
		return 1;
	}
}
