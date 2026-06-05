// AE-free CLI harness for OLMSmoother2.
//
// Drives mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp directly against PNG +
// manifest params so the same render path used by the mac plug-in can be
// compared to Windows reference frames without After Effects.

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

#include "OLMSmoother2_port.cpp"

namespace {

struct Image {
	int width = 0;
	int height = 0;
	std::vector<uint8_t> rgba;
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
	png_write_end(png, info);
	png_destroy_write_struct(&png, &info);
	std::fclose(fp);
}

std::string slurp(const std::string &path) {
	std::ifstream f(path, std::ios::binary);
	if (!f) throw std::runtime_error("failed to open params " + path);
	std::ostringstream ss;
	ss << f.rdbuf();
	return ss.str();
}

size_t find_param(const std::string &json, const std::string &key) {
	std::string needle = "\"" + key + "\"";
	return json.find(needle);
}

bool find_param_number(const std::string &json, const std::string &key, double &out) {
	size_t pos = find_param(json, key);
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

bool find_param_color(const std::string &json, const std::string &key, PF_Pixel8 &out) {
	size_t pos = find_param(json, key);
	if (pos == std::string::npos) return false;
	size_t vpos = json.find("\"value\"", pos);
	if (vpos == std::string::npos) return false;
	size_t open = json.find('[', vpos);
	size_t close = json.find(']', open);
	if (open == std::string::npos || close == std::string::npos) return false;
	std::string s = json.substr(open + 1, close - open - 1);
	std::vector<double> vals;
	size_t i = 0;
	while (i < s.size() && vals.size() < 4) {
		while (i < s.size() && (s[i] == ' ' || s[i] == '\t' || s[i] == ',')) ++i;
		size_t j = i;
		while (j < s.size() && (std::isdigit((unsigned char)s[j]) || s[j] == '-' || s[j] == '+' || s[j] == '.' || s[j] == 'e' || s[j] == 'E')) ++j;
		if (j == i) break;
		vals.push_back(std::stod(s.substr(i, j - i)));
		i = j;
	}
	if (vals.size() < 3) return false;
	auto to8 = [](double v) -> uint8_t {
		if (v <= 1.0) v *= 255.0;
		long iv = std::lround(v);
		if (iv < 0) iv = 0;
		if (iv > 255) iv = 255;
		return static_cast<uint8_t>(iv);
	};
	out.red = to8(vals[0]);
	out.green = to8(vals[1]);
	out.blue = to8(vals[2]);
	out.alpha = vals.size() >= 4 ? to8(vals[3]) : 255;
	return true;
}

}  // namespace

int main(int argc, char **argv) {
	std::string in_path, params_path, out_path;
	double force_version = -1.0;
	std::string idx0_mode = "none";
	std::string plane_split_mode = "none";
	for (int i = 1; i < argc; ++i) {
		std::string a = argv[i];
		auto next = [&]() -> std::string { return (i + 1 < argc) ? argv[++i] : std::string(); };
		if (a == "--input") in_path = next();
		else if (a == "--params") params_path = next();
		else if (a == "--output") out_path = next();
		else if (a == "--force-version") force_version = std::stod(next());
		else if (a == "--idx0-mode") idx0_mode = next();
		else if (a == "--plane-split-mode") plane_split_mode = next();
	}
	if (in_path.empty() || out_path.empty()) {
		std::fprintf(stderr, "usage: olmsmoother2_cli --input in.png --params case.json --output out.png [--force-version 1|2] [--idx0-mode none|suppress|half|quarter] [--plane-split-mode none|sample-pre-setup|class-pre-setup|sample-pre-gamma|class-pre-gamma]\n");
		return 2;
	}
	if (idx0_mode == "none") g_olmsmoother2_idx0_diag_mode = 0;
	else if (idx0_mode == "suppress") g_olmsmoother2_idx0_diag_mode = 1;
	else if (idx0_mode == "half") g_olmsmoother2_idx0_diag_mode = 2;
	else if (idx0_mode == "quarter") g_olmsmoother2_idx0_diag_mode = 3;
	else {
		std::fprintf(stderr, "--idx0-mode must be none, suppress, half, or quarter\n");
		return 2;
	}
	if (plane_split_mode == "none") g_olmsmoother2_plane_split_diag_mode = 0;
	else if (plane_split_mode == "sample-pre-setup") g_olmsmoother2_plane_split_diag_mode = 1;
	else if (plane_split_mode == "class-pre-setup") g_olmsmoother2_plane_split_diag_mode = 2;
	else if (plane_split_mode == "sample-pre-gamma") g_olmsmoother2_plane_split_diag_mode = 3;
	else if (plane_split_mode == "class-pre-gamma") g_olmsmoother2_plane_split_diag_mode = 4;
	else {
		std::fprintf(stderr, "--plane-split-mode must be none, sample-pre-setup, class-pre-setup, sample-pre-gamma, or class-pre-gamma\n");
		return 2;
	}

	try {
		double enable_key = 0.0, invert_key = 0.0, smoothness = 100.0, extra_smooth = 0.0;
		double smooth_range = 2.0, version = 2.0, gamma_mode = 1.0, gamma_value = 2.4, num_gamma = 1.0;
		PF_Pixel8 key{255, 255, 255, 255};
		PF_Pixel8 gamma_colors[NUM_GAMMA_COLORS] = {
			{255, 0, 0, 0},
			{255, 0, 0, 0},
			{255, 0, 0, 0},
			{255, 0, 0, 0},
			{255, 0, 0, 0},
		};
		if (!params_path.empty()) {
			std::string json = slurp(params_path);
			if (!find_param_number(json, "Enable Color Key", enable_key))
				find_param_number(json, "Use Color Key", enable_key);
			find_param_color(json, "Color Key", key);
			find_param_number(json, "Invert Color Key", invert_key);
			find_param_number(json, "Smoothness", smoothness);
			find_param_number(json, "Extra Smooth", extra_smooth);
			if (!find_param_number(json, "Smooth Range", smooth_range))
				find_param_number(json, "Do Smooth Range", smooth_range);
			find_param_number(json, "Smoother Version", version);
			find_param_number(json, "Gamma Correction", gamma_mode);
			find_param_number(json, "Gamma Value", gamma_value);
			find_param_number(json, "Number of Gamma Colors", num_gamma);
			for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
				size_t search_from = 0;
				for (int k = 0; k <= i; ++k) {
					search_from = json.find("\"Gamma Color\"", search_from);
					if (search_from == std::string::npos) break;
					if (k != i) ++search_from;
				}
				if (search_from != std::string::npos) {
					std::string sub = json.substr(search_from);
					find_param_color(sub, "Gamma Color", gamma_colors[i]);
				}
			}
		}
		if (force_version > 0.0) version = force_version;

		Image img = read_png(in_path);
		const int W = img.width, H = img.height;
		const size_t row = static_cast<size_t>(W) * 4;

		std::vector<uint8_t> in_argb(static_cast<size_t>(H) * row);
		std::vector<uint8_t> out_argb(static_cast<size_t>(H) * row);
		for (size_t p = 0; p < static_cast<size_t>(W) * H; ++p) {
			const uint8_t *s = &img.rgba[p * 4];
			uint8_t *d = &in_argb[p * 4];
			d[0] = s[3];
			d[1] = s[0];
			d[2] = s[1];
			d[3] = s[2];
		}

		PF_EffectWorld input{}, output{};
		input.data = in_argb.data();
		input.width = W; input.height = H; input.rowbytes = static_cast<A_long>(row);
		input.bitdepth = 8; input.extent_hint = PF_LRect{0, 0, W, H};
		output.data = out_argb.data();
		output.width = W; output.height = H; output.rowbytes = static_cast<A_long>(row);
		output.bitdepth = 8; output.extent_hint = PF_LRect{0, 0, W, H};

		PF_ParamDef p_input{}, p_enable{}, p_key{}, p_invert{}, p_smooth{}, p_extra{};
		PF_ParamDef p_range{}, p_version{}, p_gamma_mode{}, p_gamma_value{}, p_num_gamma{};
		PF_ParamDef p_gamma[NUM_GAMMA_COLORS]{};

		p_enable.u.bd.value = enable_key != 0.0 ? 1 : 0;
		p_key.u.cd.value = key;
		p_invert.u.bd.value = invert_key != 0.0 ? 1 : 0;
		p_smooth.u.sd.value = static_cast<A_long>(smoothness + 0.5);
		p_extra.u.sd.value = static_cast<A_long>(extra_smooth + 0.5);
		p_range.u.sd.value = static_cast<A_long>(smooth_range + 0.5);
		p_version.u.pd.value = static_cast<A_long>(version + 0.5);
		p_gamma_mode.u.pd.value = static_cast<A_long>(gamma_mode + 0.5);
		p_gamma_value.u.fs_d.value = gamma_value;
		p_num_gamma.u.sd.value = static_cast<A_long>(num_gamma + 0.5);
		for (int i = 0; i < NUM_GAMMA_COLORS; ++i) p_gamma[i].u.cd.value = gamma_colors[i];

		PF_ParamDef *params[SM_NUM_PARAMS] = {
			&p_input, &p_enable, &p_key, &p_invert, &p_smooth, &p_extra, &p_range,
			&p_version, &p_gamma_mode, &p_gamma_value, &p_num_gamma,
			&p_gamma[0], &p_gamma[1], &p_gamma[2], &p_gamma[3], &p_gamma[4],
		};

		PF_InData in_data{};
		PF_Err err = RenderBits<PF_Pixel8>(&in_data, params, &input, &output);
		if (err != PF_Err_NONE) {
			std::fprintf(stderr, "RenderBits failed: %d\n", (int)err);
			return 1;
		}

		Image res; res.width = W; res.height = H; res.rgba.resize(static_cast<size_t>(H) * row);
		for (size_t p = 0; p < static_cast<size_t>(W) * H; ++p) {
			const uint8_t *s = &out_argb[p * 4];
			uint8_t *d = &res.rgba[p * 4];
			d[0] = s[1]; d[1] = s[2]; d[2] = s[3]; d[3] = s[0];
		}
		write_png(out_path, res);
		std::printf("wrote: %s (OLMSmoother2 smoothness=%d extra=%d range=%d version=%d gamma=%d)\n",
		            out_path.c_str(), (int)p_smooth.u.sd.value, (int)p_extra.u.sd.value,
		            (int)p_range.u.sd.value, (int)p_version.u.pd.value,
		            (int)p_gamma_mode.u.pd.value);
		return 0;
	} catch (const std::exception &e) {
		std::fprintf(stderr, "error: %s\n", e.what());
		return 1;
	}
}
