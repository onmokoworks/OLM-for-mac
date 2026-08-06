#include <cstdio>
#include <cstring>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

template <typename P>
static int run_one(const char *depth, const P &pixel, size_t padding)
{
	constexpr int width = 3;
	constexpr int height = 2;
	const size_t rowbytes = width * sizeof(P) + padding;
	std::vector<unsigned char> input_bytes(rowbytes * height, 0x3c);
	std::vector<unsigned char> output_bytes(rowbytes * height, 0xa5);
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			std::memcpy(input_bytes.data() + y * rowbytes + x * sizeof(P), &pixel, sizeof(P));
		}
	}

	PF_EffectWorld input{};
	PF_EffectWorld output{};
	input.data = input_bytes.data();
	input.width = width; input.height = height; input.rowbytes = rowbytes;
	input.extent_hint = PF_LRect{0, 0, width, height};
	output.data = output_bytes.data();
	output.width = width; output.height = height; output.rowbytes = rowbytes;
	output.extent_hint = PF_LRect{0, 0, width, height};

	PF_ParamDef defs[SM_NUM_PARAMS]{};
	PF_ParamDef *params[SM_NUM_PARAMS]{};
	for (int i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &defs[i];
	defs[SM_SMOOTHNESS].u.sd.value = 0;
	defs[SM_EXTRA_SMOOTH].u.sd.value = 0;
	defs[SM_SMOOTH_RANGE].u.sd.value = 1;
	defs[SM_VERSION].u.pd.value = SMOOTHER_V1;
	defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
	defs[SM_GAMMA_VALUE].u.fs_d.value = 2.4;

	PF_InData in_data{};
	const PF_Err err = RenderBits<P>(&in_data, params, &input, &output);
	if (err != PF_Err_NONE) return 10 + err;

	std::printf("%s ", depth);
	for (unsigned char byte : output_bytes) std::printf("%02x", byte);
	std::printf("\n");
	return 0;
}

int main()
{
	const PF_Pixel16 p16{20480, 4045, 16384, 28723};
	const PF_PixelFloat p32{0.625f, 0.1234567f, 0.5f, 0.8765432f};
	if (const int rc = run_one("PF16", p16, 6)) return rc;
	return run_one("PF32", p32, 12);
}
