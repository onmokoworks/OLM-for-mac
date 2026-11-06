// SDK-free tests of the extracted production functions, not a render oracle.
#include "../../core/radialblur_plane_read.h"
#include "../../core/olm_exact_math.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <utility>
#include <vector>

using A_long = std::int32_t;
using A_u_char = unsigned char;
using PF_FpLong = double;
struct Pixel { float alpha; };
struct PF_EffectWorld { void* data; A_long width, height, rowbytes; };
template <typename T> struct RadialZoomPixelTraits {
    static float Read(const T& p, int channel) { assert(channel == 3); return p.alpha; }
};
template <typename T> T LoadPixel(const PF_EffectWorld* world, A_long x, A_long y) {
    T p;
    std::memcpy(&p, static_cast<const unsigned char*>(world->data) +
        y * world->rowbytes + x * sizeof(T), sizeof(T));
    return p;
}
using olm::exact_math::RadialF32Mul;
using olm::exact_math::RadialF32Add;
using olm::exact_math::RadialF32Sub;
using olm::exact_math::RadialF32Div;

#include "production_functions.inc"

static std::uint32_t bits(float v) {
    std::uint32_t b; std::memcpy(&b, &v, 4); return b;
}
static float word(std::uint32_t b) {
    float v; std::memcpy(&v, &b, 4); return v;
}
static std::size_t scalar_checks = 0, mask_checks = 0;
static void same(float a, float b) {
    if (bits(a) != bits(b)) {
        std::cerr << "first_mismatch: scalar_comparison=" << scalar_checks
                  << " actual_word=" << bits(a) << " expected_word=" << bits(b) << '\n';
    }
    assert(bits(a) == bits(b));
}

static void check_mask(std::vector<Pixel>& pixels, int w, int h, float sv) {
    PF_EffectWorld world{pixels.data(), w, h, A_long(w * sizeof(Pixel))};
    std::vector<float> old_factors, factors;
    std::vector<A_long> old_areas, areas;
    assert(BeforeBuildRadialSizeFactorPlaneAEX<Pixel>(&world, sv, &old_factors, &old_areas));
    assert(BuildRadialSizeFactorPlaneAEX<Pixel>(&world, sv, &factors, &areas));
    assert(areas == old_areas && factors.size() == old_factors.size());
    assert(std::memcmp(factors.data(), old_factors.data(), factors.size() * 4) == 0);
    assert(bits(factors.back()) == 0);
    ++mask_checks;
}

int main(int argc, char** argv) {
    using olm::radialblur::read_plane_or_zero;
    // Include poisoned padding: logical handle length, not vector capacity,
    // controls the read. Every valid bit pattern must be preserved.
    std::vector<unsigned char> mask(783, 0xff);
    for (std::size_t i = 0; i < 782; ++i) assert(read_plane_or_zero(mask.data(), 782, i) == 0xff);
    assert(read_plane_or_zero(mask.data(), 782, 782) == 0);
    std::vector<float> plane(103, 91.0f);
    const std::uint32_t patterns[] = {0, 0x80000000, 1, 0x7f800000, 0xff800000, 0x7fc12345, 0x3f800001};
    for (auto b : patterns) {
        for (std::size_t i = 0; i < 102; ++i) plane[i] = word(b);
        for (std::size_t i = 0; i < 102; ++i) assert(bits(read_plane_or_zero(plane.data(), 102, i)) == b);
        assert(bits(read_plane_or_zero(plane.data(), 102, 102)) == 0);
    }
    assert(bits(read_plane_or_zero<float>(nullptr, 0, 0)) == 0);
    assert(bits(read_plane_or_zero(plane.data(), 102, std::numeric_limits<std::size_t>::max())) == 0);

    // Exact expected arithmetic; right-hand +1 must still cross an in-range
    // row boundary. The final right tap must not consume the poisoned guard.
    std::vector<float> small{1, 2, 4, 8, 999};
    same(SampleScalarAEXRepeat(small, 2, 2, 0.5f, 0.5f), 2.25f);
    same(SampleScalarAEXRepeat(small, 2, 2, 1.5f, 0.5f), 3.5f);
    small.resize(4); // the production sampler must also work with no guard
    same(SampleScalarAEXRepeat(small, 2, 2, 1.5f, 0.5f), 3.5f);

    for (int w = 1; w <= 8; ++w) for (int h = 1; h <= 5; ++h) {
        for (int profile = 0; profile != 2; ++profile) {
            std::vector<float> source(w*h), legacy(w*h+1, 0.0f);
            for (int i = 0; i < w*h; ++i)
                source[i] = legacy[i] = profile ? word(patterns[i % 7]) : float(i+1) / 16.0f;
            for (int ix = -7; ix <= 4*w+7; ++ix) for (int iy = -7; iy <= 4*h+7; ++iy) {
                same(SampleScalarAEXRepeat(source, w, h, ix/4.0f, iy/4.0f),
                     BeforeSampleScalarAEXRepeat(legacy, w, h, ix/4.0f, iy/4.0f));
                ++scalar_checks;
            }
        }
    }
    // Exhaust all alpha topologies of small planes, including 1-row/column
    // shapes and the last occupied pixel. Compare full factors/area lists.
    for (auto dims : {std::pair<int,int>{1,1}, {1,4}, {4,1}, {2,2}, {3,2}, {4,3}}) {
        int w = dims.first, h = dims.second;
        std::vector<Pixel> pixels(w*h);
        for (unsigned m = 0; m < (1u << (w*h)); ++m) {
            for (int i = 0; i < w*h; ++i) pixels[i].alpha = (m >> i) & 1u;
            check_mask(pixels, w, h, 100.0f);
        }
    }
    // Row crossing extends the first component, without joining the two.
    std::vector<Pixel> separate{{0}, {1}, {1}, {0}};
    PF_EffectWorld world{separate.data(), 2, 2, 2 * sizeof(Pixel)};
    std::vector<float> factors; std::vector<A_long> areas;
    assert(BuildRadialSizeFactorPlaneAEX<Pixel>(&world, 100, &factors, &areas));
    assert((areas == std::vector<A_long>{1,2}));

    // Optional T15 packed ARGB fixture: exercise its alpha plane and exact
    // Size Variation through the production size builder, not a full render.
    if (argc == 6) {
        int w = std::stoi(argv[2]), h = std::stoi(argv[3]), depth = std::stoi(argv[4]);
        std::ifstream f(argv[1], std::ios::binary);
        assert(f);
        const int sample_bytes = depth == 16 ? 2 : 4;
        std::vector<unsigned char> raw(w*h*sample_bytes*4);
        f.read(reinterpret_cast<char*>(raw.data()), raw.size());
        assert(f.gcount() == std::streamsize(raw.size()));
        std::vector<Pixel> pixels(w*h);
        for (int i = 0; i < w*h; ++i) {
            if (depth == 16) {
                std::uint16_t a; std::memcpy(&a, raw.data()+i*8, 2);
                pixels[i].alpha = float(a)/32768.0f;
            } else std::memcpy(&pixels[i].alpha, raw.data()+i*16, 4);
        }
        check_mask(pixels, w, h, std::stof(argv[5]));
    } else assert(argc == 1);
    std::cout << "scalar_comparisons=" << scalar_checks << " mask_comparisons=" << mask_checks
              << " differing_values=0 max_ulp=0 first_mismatch=null\n";
}
