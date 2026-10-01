// Exercise the production Zoom PF8 writer using exact FLOAT32 input bits.
#include "production_under_test.cpp"

int main()
{
	unsigned int bits[4];
	while (std::scanf("%x %x %x %x", &bits[0], &bits[1], &bits[2], &bits[3]) == 4) {
		RadialBlurOuterSampleState state{};
		for (int c = 0; c < 3; ++c) std::memcpy(&state.final_rgb[c], &bits[c], 4);
		std::memcpy(&state.alpha, &bits[3], 4);
		PF_Pixel8 pixel{};
		RadialZoomPixelTraits<PF_Pixel8>::WriteZoom(pixel, state, false);
		std::printf("%02x%02x%02x%02x\n", pixel.alpha, pixel.red, pixel.green, pixel.blue);
	}
	return std::ferror(stdin) ? 1 : 0;
}
