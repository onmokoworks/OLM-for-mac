#include "../../core/kirakira_warp.h"

#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>

int main()
{
	constexpr int width = 9, height = 7;
	std::vector<float> source(width * height);
	for (int i = 0; i < width * height; ++i) source[i] = static_cast<float>(i % 17) / 17.0f;
	const auto output = olm::kirakira::warp_get_rotation_matrix_2d(
		source, width, height, width, height, 4.5, 3.5, 5.0);
	constexpr std::array<std::uint32_t, width * height> expected = {
		0x3c3c3c3c,0x3d634b4c,0x3dd9a5a6,0x3e2e9697,0x3e7ba5a6,0x3eb0f0f1,0x3ee8787a,0x3ef71697,0x3e6e1e1e,
		0x3eb0f0f1,0x3ee78789,0x3f0b4b4b,0x3f270f10,0x3f42d2d3,0x3f4e9697,0x3f561e1d,0x3f2e21e2,0x3e045a5b,
		0x3e7a5a5c,0x3e8c3c3d,0x3e92d2d3,0x3e9a5a5a,0x3ea1e1e2,0x3ec9696a,0x3ef07879,0x3ec00001,0x3eab4b4c,
		0x3ec9696a,0x3ef87879,0x3f180001,0x3f33c3c5,0x3f4f0f10,0x3f5e9696,0x3f5b5a5b,0x3df0f0f2,0x3e5e7879,
		0x3e992d2e,0x3ea4b4b5,0x3eac3c3c,0x3eb3c3c4,0x3ebb4b4c,0x3eda5a5b,0x3ed4f0f2,0x3ed87879,0x3ee00002,
		0x3ec18787,0x3f087879,0x3f243c3c,0x3f400001,0x3f578787,0x3f6b4b4a,0x3e2c3c3c,0x3e2b4b4c,0x3e8c3c3c,
		0x3e98f0f1,0x3ebd2d2d,0x3ec4b4b5,0x3ecc3c3c,0x3edb4b4c,0x3ee30787,0x3ee7696a,0x3ee625a6,0x3ee961e2,
	};
	for (std::size_t i = 0; i < output.size(); ++i) {
		const auto bits = std::bit_cast<std::uint32_t>(output[i]);
		if (bits != expected[i]) {
			std::fprintf(stderr, "mismatch[%zu] %08x != %08x\n", i, bits, expected[i]);
			return 1;
		}
	}
	std::puts("PASS_KIRAKIRA_ACTUAL_AEX_FORWARD_WARP_63_WORDS");
}
