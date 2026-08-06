#include "../../core/kirakira_highlight.h"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <vector>

int main()
{
	const std::vector<float> source = {0.0f, 1.0f / 17.0f, 2.0f / 17.0f, 3.0f / 17.0f};
	const std::vector<float> highlight =
		olm::kirakira::highlight_isotropic_box_blur(source, 4, 1, 11, 3);
	if (highlight.size() != 4) return 1;
	for (float value : highlight) {
		std::printf("%08x\n", std::bit_cast<std::uint32_t>(value));
	}
	return 0;
}
