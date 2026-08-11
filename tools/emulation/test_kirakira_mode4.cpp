#include "../../core/kirakira_mode4.h"

#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <vector>

int main()
{
	constexpr int width = 9;
	constexpr int height = 7;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 5, 5.0)) return 10;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 5, 0.0)) return 18;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 9, 5, 45.0)) return 19;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 9, 5, -45.0)) return 20;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 9, 5, 90.0)) return 21;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 4, 5.0)) return 11;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 6, 5.0)) return 12;
	if (olm::kirakira::mode4_rotated_scalar_admitted(7, 9, 5, 5.0)) return 13;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(1920, 1080, 5, 5.0)) return 14;
	if (olm::kirakira::mode4_rotated_scalar_admitted(0, 7, 5, 5.0)) return 15;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 5, 45.0)) return 16;
	if (!olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 5, -5.0)) return 17;
	if (olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 0, 0.0)) return 22;
	if (olm::kirakira::mode4_rotated_scalar_admitted(9, 7, 1001, 0.0)) return 23;
	if (olm::kirakira::mode4_rotated_scalar_admitted(8, 7, 5, 0.0)) return 24;
	if (olm::kirakira::mode4_rotated_scalar_admitted(9, 6, 5, 0.0)) return 25;
	constexpr std::array<std::uint32_t, width * height> source_bits = {
		0x3c3c3c3c,0x3d634b4c,0x3dd9a5a6,0x3e2e9697,0x3e7ba5a6,0x3eb0f0f1,0x3ee8787a,0x3ef71697,0x3e6e1e1e,
		0x3eb0f0f1,0x3ee78789,0x3f0b4b4b,0x3f270f10,0x3f42d2d3,0x3f4e9697,0x3f561e1d,0x3f2e21e2,0x3e045a5b,
		0x3e7a5a5c,0x3e8c3c3d,0x3e92d2d3,0x3e9a5a5a,0x3ea1e1e2,0x3ec9696a,0x3ef07879,0x3ec00001,0x3eab4b4c,
		0x3ec9696a,0x3ef87879,0x3f180001,0x3f33c3c5,0x3f4f0f10,0x3f5e9696,0x3f5b5a5b,0x3df0f0f2,0x3e5e7879,
		0x3e992d2e,0x3ea4b4b5,0x3eac3c3c,0x3eb3c3c4,0x3ebb4b4c,0x3eda5a5b,0x3ed4f0f2,0x3ed87879,0x3ee00002,
		0x3ec18787,0x3f087879,0x3f243c3c,0x3f400001,0x3f578787,0x3f6b4b4a,0x3e2c3c3c,0x3e2b4b4c,0x3e8c3c3c,
		0x3e98f0f1,0x3ebd2d2d,0x3ec4b4b5,0x3ecc3c3c,0x3edb4b4c,0x3ee30787,0x3ee7696a,0x3ee625a6,0x3ee961e2,
	};
	std::vector<float> source;
	for (auto bits : source_bits) source.push_back(std::bit_cast<float>(bits));
	std::vector<float> destination(width * height, 0.0f);
	if (!olm::kirakira::mode4_scalar_recurrence(
			source.data(), width, destination.data(), width, width, height, 5)) return 1;
	constexpr std::array<std::uint32_t, width * height> expected = {
		0x3e0b6c3b,0x3e1f7882,0x3e34854a,0x3e473f82,0x3e55090f,0x3e57bf55,0x3e4c8530,0x3e3beaec,0x3e45ac7c,
		0x3ec64930,0x3edfee13,0x3ef56e3a,0x3f011c94,0x3f0287da,0x3f0024d4,0x3eee83bb,0x3edcbd40,0x3ee0a901,
		0x3e55b45d,0x3e7478ba,0x3e875095,0x3e90972c,0x3e961c5b,0x3e924ed3,0x3e884558,0x3e840145,0x3e69b0b0,
		0x3ec71328,0x3ee173af,0x3ef420da,0x3efe0db1,0x3efca14e,0x3ef08af0,0x3ed9ff10,0x3ef0580c,0x3ec3c736,
		0x3e70ee07,0x3e8a61a4,0x3e986d4e,0x3ea1fc1c,0x3ea6f488,0x3ea329fa,0x3e9ec25e,0x3e925385,0x3e7c27eb,
		0x3ec15b08,0x3ed56a64,0x3ee5680d,0x3eeacbba,0x3ee41713,0x3ece4b6e,0x3eebe605,0x3ecc94d5,0x3ea62623,
		0x3e863d6e,0x3e96cce6,0x3ea6a978,0x3eb126a0,0x3eb4f18a,0x3eb3ce1f,0x3eac9b3c,0x3e9f3f02,0x3e89a87b,
	};
	for (std::size_t i = 0; i < destination.size(); ++i) {
		const auto actual = std::bit_cast<std::uint32_t>(destination[i]);
		if (actual != expected[i]) {
			std::fprintf(stderr, "mismatch[%zu]: %08x != %08x\n", i, actual, expected[i]);
			return 2;
		}
	}
	std::vector<float> original(width * height);
	for (int i = 0; i < width * height; ++i) original[i] = static_cast<float>(i % 17) / 17.0f;
	const auto chain = olm::kirakira::mode4_rotated_scalar_chain(
		original, width, height, 4.5, 3.5, 5.0, 5);
	constexpr std::array<std::uint32_t, width * height> final_expected = {
		0x3e2f4bae,0x3e71354a,0x3e712307,0x3e729f88,0x3e643408,0x3e502f2c,0x3e360670,0x3e16dd32,0x3e0be300,
		0x3e82ed53,0x3ebb3e08,0x3ed90ae0,0x3ef15122,0x3efd782c,0x3efca6f1,0x3ee109c5,0x3ec470e8,0x3ebc5b15,
		0x3e7c8e52,0x3e982371,0x3e9d546f,0x3e9d1a90,0x3e9be1e7,0x3e963953,0x3e966d46,0x3e985177,0x3e97f970,
		0x3ea1ea9c,0x3ec5802e,0x3edf8445,0x3ef23c75,0x3ef9fdb1,0x3eedf7b0,0x3ed11792,0x3ed79ca6,0x3ead5296,
		0x3e97403e,0x3ea2bed4,0x3ea9ce7e,0x3eab4e3c,0x3ea8bac8,0x3ea56d3c,0x3ea5e946,0x3ea617f8,0x3e8f3d1a,
		0x3eae1dd6,0x3ec45731,0x3ed87e84,0x3ee2ea80,0x3edff91a,0x3ecf08a5,0x3edea2f3,0x3ebb87ff,0x3e866c66,
		0x3e2cf99f,0x3e5dc366,0x3e83ff49,0x3e9bbba3,0x3eaf0c3c,0x3eb463a2,0x3eb11ab5,0x3ea3a283,0x3e65009b,
	};
	for (std::size_t i = 0; i < chain.size(); ++i) {
		const auto actual = std::bit_cast<std::uint32_t>(chain[i]);
		if (actual != final_expected[i]) {
			std::fprintf(stderr, "chain mismatch[%zu]: %08x != %08x\n", i, actual, final_expected[i]);
			return 3;
		}
	}
	std::puts("PASS_KIRAKIRA_MODE4_ACTUAL_AEX_9X7_RADIUS5");
	return 0;
}
