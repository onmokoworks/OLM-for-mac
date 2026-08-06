#include "../../core/kirakira_merge2.h"
#include "../../core/kirakira_mode4.h"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <vector>

int main()
{
	constexpr int width = 9, height = 7;
	std::vector<float> source(width * height);
	for (int i = 0; i < width * height; ++i) source[i] = static_cast<float>(i % 17) / 17.0f;
	const auto helper = olm::kirakira::mode4_rotated_scalar_chain(
		source, width, height, 4.5, 3.5, 5.0, 5);
	const auto cropped = olm::kirakira::centered_crop_scalar(helper, width, height, width, height);
	if (cropped.size() != helper.size() || cropped != helper) return 1;
	const float r = cropped[0];
	const float g = r * 0.5f;
	const float b = r * 0.25f;
	const float a = 1.0f;
	const unsigned pf8[4] = {
		olm::kirakira::truncate_merge2_channel(a, 255.0f),
		olm::kirakira::truncate_merge2_channel(r, 255.0f),
		olm::kirakira::truncate_merge2_channel(g, 255.0f),
		olm::kirakira::truncate_merge2_channel(b, 255.0f)};
	const unsigned pf16[4] = {
		olm::kirakira::truncate_merge2_channel(a, 32768.0f),
		olm::kirakira::truncate_merge2_channel(r, 32768.0f),
		olm::kirakira::truncate_merge2_channel(g, 32768.0f),
		olm::kirakira::truncate_merge2_channel(b, 32768.0f)};
	std::printf("RGBA_BITS=%08x,%08x,%08x,%08x\n",
		std::bit_cast<std::uint32_t>(r), std::bit_cast<std::uint32_t>(g),
		std::bit_cast<std::uint32_t>(b), std::bit_cast<std::uint32_t>(a));
	std::printf("PF8=%02x%02x%02x%02x\n", pf8[0], pf8[1], pf8[2], pf8[3]);
	std::printf("PF16=%04x%04x%04x%04x\n", pf16[0], pf16[1], pf16[2], pf16[3]);
	std::printf("PF32=%08x%08x%08x%08x\n",
		std::bit_cast<std::uint32_t>(a), std::bit_cast<std::uint32_t>(r),
		std::bit_cast<std::uint32_t>(g), std::bit_cast<std::uint32_t>(b));
}
