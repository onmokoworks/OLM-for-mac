#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
#include "../../cli/OLMSmoother2/shim/OLMSmoother2.h"
#include "../../core/olm_sha256_rows.h"

static void print_digest(const char *name, const void *data, size_t size)
{
	olm::Sha256 hash;
	hash.update(data, size);
	unsigned char digest[32];
	hash.final(digest);
	std::printf("SOURCE %s ", name);
	for (unsigned char value : digest) std::printf("%02x", value);
	std::printf("\n");
}

struct RGBA8 { unsigned char r, g, b, a; };

static RGBA8 logical17(int x, int y)
{
	unsigned u = (unsigned)(x + 1) * 0x9e3779b9u ^
	             (unsigned)(y + 3) * 0x85ebca6bu;
	u ^= u >> 16; u *= 0x7feb352du; u ^= u >> 15;
	static const unsigned char alpha[] = {0, 1, 64, 128, 192, 255};
	if (x == 0 && y == 0) return {1, 1, 1, 128};
	if (x == 1 && y == 0) return {255, 0, 0, 192};
	return {(unsigned char)u, (unsigned char)(u >> 8),
	        (unsigned char)(u >> 16), alpha[(x + 3 * y) % 6]};
}

template <class P> static P native17(RGBA8 value, bool premultiplied);
template <> PF_Pixel8 native17(RGBA8 q, bool premultiplied)
{
	auto color = [&](unsigned v) { return (unsigned char)(premultiplied ?
		((v * q.a + 127u) / 255u) : v); };
	return {q.a, color(q.r), color(q.g), color(q.b)};
}
template <> PF_Pixel16 native17(RGBA8 q, bool premultiplied)
{
	auto native = [](unsigned v) { return (unsigned)std::lround(v * 32768.0 / 255.0); };
	const unsigned a = native(q.a);
	auto color = [&](unsigned v) { const unsigned c = native(v); return (unsigned short)(premultiplied ?
		((c * a + 16384u) / 32768u) : c); };
	return {(unsigned short)a, color(q.r), color(q.g), color(q.b)};
}
template <> PF_PixelFloat native17(RGBA8 q, bool premultiplied)
{
	const float a = q.a / 255.f;
	auto color = [&](unsigned v) { const float c = v / 255.f; return premultiplied ? c * a : c; };
	return {a, color(q.r), color(q.g), color(q.b)};
}

template <class P>
static void print17(const char *name, bool premultiplied)
{
	std::vector<P> pixels;
	for (int y = 0; y < 11; ++y)
		for (int x = 0; x < 17; ++x)
			pixels.push_back(native17<P>(logical17(x, y), premultiplied));
	print_digest(name, pixels.data(), pixels.size() * sizeof(P));
}

static void print5(const char *family, const unsigned char rgb[25][3])
{
	std::vector<PF_Pixel8> p8;
	std::vector<PF_Pixel16> p16;
	std::vector<PF_PixelFloat> p32;
	for (int i = 0; i < 25; ++i) {
		const auto r = rgb[i][0], g = rgb[i][1], b = rgb[i][2];
		auto widen = [](unsigned v) { return (unsigned short)((v * 0x8000u + 0x80u) / 0xffu); };
		p8.push_back({255, r, g, b});
		p16.push_back({32768, widen(r), widen(g), widen(b)});
		p32.push_back({1.f, r / 255.f, g / 255.f, b / 255.f});
	}
	char name[80];
	std::snprintf(name, sizeof(name), "%s_pf8", family); print_digest(name, p8.data(), p8.size()*sizeof(PF_Pixel8));
	std::snprintf(name, sizeof(name), "%s_pf16", family); print_digest(name, p16.data(), p16.size()*sizeof(PF_Pixel16));
	std::snprintf(name, sizeof(name), "%s_pf32", family); print_digest(name, p32.data(), p32.size()*sizeof(PF_PixelFloat));
}

int main()
{
	print_digest("sha256_empty", "", 0);
	const char *abc = "abc";
	print_digest("sha256_abc", abc, 3);
	unsigned char multi[1000];
	for (unsigned i = 0; i < sizeof(multi); ++i) multi[i] = (unsigned char)((i * 37u + 11u) & 255u);
	print_digest("sha256_multiblock", multi, sizeof(multi));
	static const unsigned char gamma18[25][3] = {
		{202,187,230},{255,0,0},{65,1,1},{0,255,0},{206,55,161},
		{86,55,26},{43,73,217},{231,16,235},{116,106,230},{1,9,43},
		{91,38,34},{99,183,84},{230,125,149},{208,155,60},{168,21,161},
		{233,157,226},{8,57,119},{159,56,196},{232,156,109},{50,140,246},
		{229,135,20},{36,6,46},{176,107,229},{168,83,193},{235,7,162}};
	unsigned char gamma24[25][3];
	memcpy(gamma24, gamma18, sizeof(gamma24));
	gamma24[0][0] = gamma24[0][1] = gamma24[0][2] = 1;
	print5("v2_5x5_gamma18", gamma18);
	print5("v2_5x5_gamma24", gamma24);
	const PF_PixelFloat small[6] = {{1,0,0,0},{1,0,1,1},{1,1,0,1},
	                                {1,1,1,0},{1,.25f,.25f,.25f},{1,.75f,.75f,.75f}};
	print_digest("v2_3x2_pf32", small, sizeof(small));
	print17<PF_Pixel8>("v2_17x11_pf8_straight", false);
	print17<PF_Pixel8>("v2_17x11_pf8_premul", true);
	print17<PF_Pixel16>("v2_17x11_pf16_straight", false);
	print17<PF_Pixel16>("v2_17x11_pf16_premul", true);
	print17<PF_PixelFloat>("v2_17x11_pf32_straight", false);
	print17<PF_PixelFloat>("v2_17x11_pf32_premul", true);
	return 0;
}
