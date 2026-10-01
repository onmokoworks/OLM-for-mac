// Actual SDK Angle layout -> production reader -> FLOAT32 phase bits.
#include "production_under_test.cpp"

int main(int argc, char **argv)
{
	if (argc != 2) return 64;
	PF_ParamDef definitions[OLMRADIALBLUR_NUM_PARAMS]{};
	PF_ParamDef *parameters[OLMRADIALBLUR_NUM_PARAMS];
	for (int i = 0; i < OLMRADIALBLUR_NUM_PARAMS; ++i) parameters[i] = &definitions[i];
	definitions[OLMRADIALBLUR_NOISE_OFFSET].param_type = PF_Param_ANGLE;
	definitions[OLMRADIALBLUR_NOISE_OFFSET].u.ad.value = (PF_Fixed)std::strtoll(argv[1], nullptr, 10);
	const auto info = InfoFromParams(parameters, 20, 14);
	const float phase = (float)info.noise_offset;
	uint32_t bits;
	std::memcpy(&bits, &phase, 4);
	std::printf("%.17g %08x\n", (double)phase, bits);
}
