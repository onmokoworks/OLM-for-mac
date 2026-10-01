// Actual SDK AD layout -> production parameter reader -> transform argument.
#include "production_under_test.cpp"

int main(int argc, char **argv)
{
	if (argc != 3) return 64;
	PF_ParamDef definitions[OLMRADIALBLUR_NUM_PARAMS]{};
	PF_ParamDef *parameters[OLMRADIALBLUR_NUM_PARAMS];
	for (int i = 0; i < OLMRADIALBLUR_NUM_PARAMS; ++i) parameters[i] = &definitions[i];
	definitions[OLMRADIALBLUR_ANGLE].param_type = PF_Param_ANGLE;
	definitions[OLMRADIALBLUR_ANGLE].u.ad.value = (PF_Fixed)std::strtoll(argv[1], nullptr, 10);
	definitions[OLMRADIALBLUR_NOISE_OFFSET].param_type = PF_Param_ANGLE;
	definitions[OLMRADIALBLUR_NOISE_OFFSET].u.ad.value = (PF_Fixed)std::strtoll(argv[2], nullptr, 10);
	const auto info = InfoFromParams(parameters, 20, 14);
	const int32_t argument = RadialAngleFixedRadians(info.angle_deg);
	const float cosine = (float)std::cos((double)argument);
	const float sine = (float)std::sin((double)argument);
	uint32_t cosine_bits, sine_bits;
	std::memcpy(&cosine_bits, &cosine, 4);
	std::memcpy(&sine_bits, &sine, 4);
	std::printf("%.17g %d %08x %08x %ld\n", info.angle_deg, argument,
		cosine_bits, sine_bits, (long)info.noise_offset);
}
