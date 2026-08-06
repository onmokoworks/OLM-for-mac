#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>

static std::vector<std::uint8_t> read_all(const char *p) {
	std::ifstream s(p, std::ios::binary);
	return {std::istreambuf_iterator<char>(s), {}};
}

int main(int argc, char **argv) {
	if (argc != 4) return 2;
	auto input = read_all(argv[1]);
	auto seeded = read_all(argv[2]);
	auto expected = read_all(argv[3]);
	constexpr int w = 17, h = 11, in_rb = 146, out_rb = 150;
	if (input.size() != in_rb * h || seeded.size() != out_rb * h || expected.size() != out_rb * h) return 3;
	PF_EffectWorld iw{input.data(), w, h, in_rb, 16, {0, 0, w, h}};
	PF_EffectWorld ow{seeded.data(), w, h, out_rb, 16, {0, 0, w, h}};
	if (RenderSmartPF16PreseededField(&iw, &ow) != PF_Err_NONE) return 4;
	size_t bad = 0;
	for (size_t i = 0; i < seeded.size(); ++i) if (seeded[i] != expected[i]) ++bad;
	if (bad) { std::fprintf(stderr, "mismatched bytes=%zu\n", bad); return 1; }
	std::printf("PASS smart_pf16 bytes=%zu mismatches=0 rowbytes=%d/%d\n", seeded.size(), in_rb, out_rb);
	return 0;
}
