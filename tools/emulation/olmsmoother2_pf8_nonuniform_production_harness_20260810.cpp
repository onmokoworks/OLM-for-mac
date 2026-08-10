#include <cstdio>
#include <cstring>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static int run(const char *label, const PF_Pixel8 pixels[6], int version)
{
	constexpr int width = 3, height = 2;
	constexpr size_t padding = 5;
	const size_t rowbytes = width * sizeof(PF_Pixel8) + padding;
	std::vector<unsigned char> input(rowbytes * height, 0x3c);
	std::vector<unsigned char> output(rowbytes * height, 0xa5);
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			std::memcpy(input.data() + y * rowbytes + x * sizeof(PF_Pixel8),
			            &pixels[y * width + x], sizeof(PF_Pixel8));
		}
	}
	PF_EffectWorld input_world{}, output_world{};
	input_world.data = input.data(); input_world.width = width; input_world.height = height;
	input_world.rowbytes = rowbytes; input_world.extent_hint = {0, 0, width, height};
	output_world.data = output.data(); output_world.width = width; output_world.height = height;
	output_world.rowbytes = rowbytes; output_world.extent_hint = {0, 0, width, height};
	PF_ParamDef defs[SM_NUM_PARAMS]{}; PF_ParamDef *params[SM_NUM_PARAMS]{};
	for (int i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &defs[i];
	defs[SM_SMOOTHNESS].u.sd.value = 100;
	defs[SM_EXTRA_SMOOTH].u.sd.value = 0;
	defs[SM_SMOOTH_RANGE].u.sd.value = 1;
	defs[SM_VERSION].u.pd.value = version;
	defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
	defs[SM_GAMMA_VALUE].u.fs_d.value = 2.4;
	PF_InData in_data{};
	if (RenderBits<PF_Pixel8>(&in_data, params, &input_world, &output_world) != PF_Err_NONE) return 2;
	std::printf("%s ", label);
	for (unsigned char byte : output) std::printf("%02x", byte);
	std::printf("\n");
	return 0;
}

int main()
{
	const PF_Pixel8 v1[6] = {
		{255,   0,   0,   0}, {255, 255,   0,   0}, {255,   0, 255,   0},
		{255,   0,   0, 255}, {255, 255, 255, 255}, {255, 128, 128, 128},
	};
	const PF_Pixel8 v2[6] = {
		{255,   0,   0,   0}, {255,   0, 255, 255}, {255, 255,   0, 255},
		{255, 255, 255,   0}, {255,  64,  64,  64}, {255, 191, 191, 191},
	};
	if (int rc = run("v1", v1, SMOOTHER_V1)) return rc;
	return run("v2", v2, SMOOTHER_V2);
}
