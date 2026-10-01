// FLOAT32 noise grid diagnostic; inputs are bits, not rounded decimal strings.
#include "../../core/dblur_noise.h"
#include <cstdio>
#include <cstring>
#include <string>

static float FloatBits(const char *value)
{
	const uint32_t bits = (uint32_t)std::stoul(value, nullptr, 16);
	float result;
	std::memcpy(&result, &bits, 4);
	return result;
}

int main(int argc, char **argv)
{
	if (argc != 6) return 64;
	std::vector<float> values;
	int width = 0, height = 0;
	if (!olm::dblur::generate_radial_noise_plane(std::stoi(argv[1]), std::stoi(argv[2]),
		FloatBits(argv[3]), FloatBits(argv[4]), (uint32_t)std::stoul(argv[5]),
		&values, &width, &height)) return 65;
	std::fprintf(stderr, "%d %d\n", width, height);
	return std::fwrite(values.data(), sizeof(float), values.size(), stdout) == values.size() ? 0 : 66;
}
