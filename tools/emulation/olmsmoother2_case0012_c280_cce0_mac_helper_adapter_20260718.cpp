#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <cstdint>
#include <cstring>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static bool read_all(const char *path, void *data, size_t size) {
  std::ifstream file(path, std::ios::binary);
  if (!file) return false;
  file.read(static_cast<char *>(data), static_cast<std::streamsize>(size));
  return file.good() || file.gcount() == static_cast<std::streamsize>(size);
}

static uint32_t f32_u32(float value) {
  uint32_t bits;
  std::memcpy(&bits, &value, sizeof(bits));
  return bits;
}

int main(int argc, char **argv) {
  if (argc != 3) return 2;
  constexpr int w = 16;
  constexpr int h = 16;
  std::vector<FPix> pixels(static_cast<size_t>(w) * h);
  std::vector<uint8_t> classes(static_cast<size_t>(w) * h * 4);
  if (!read_all(argv[1], pixels.data(), pixels.size() * sizeof(FPix)) ||
      !read_all(argv[2], classes.data(), classes.size())) return 3;

  FPlane plane{pixels.data(), static_cast<size_t>(w) * sizeof(FPix), 0};
  SMParams params{};
  params.version = 2;
  params.w = w;
  params.h = h;
  params.smoothness_raw = 100;
  params.extra_smooth_raw = 40;
  params.smooth_range = 88;
  params.gamma_mode = GAMMA_COLORS_ONLY;
  params.gamma_value = 2.16954731941223f;
  params.num_gamma_colors = 5;
  params.class_plane = classes.data();

  SmootherPolygon polygon{};
  build_polygon(polygon, plane, 8, 8, params);
  FPix output{};
  win_FUN_18000cce0_orchestrate(output, plane, plane, 8, 8, params);

  std::printf("{\"count\":%d,\"vertices\":[", polygon.count);
  for (int i = 0; i < polygon.count; ++i) {
    if (i) std::putchar(',');
    const PolyVertex &v = polygon.samples[i];
    std::printf("{\"rgba\":[%.9g,%.9g,%.9g,%.9g],\"rgba_u32\":[%u,%u,%u,%u],\"weight\":%.9g,\"weight_u32\":%u}",
                v.r, v.g, v.b, v.a, f32_u32(v.r), f32_u32(v.g),
                f32_u32(v.b), f32_u32(v.a), v.w, f32_u32(v.w));
  }
  std::printf("],\"orchestrated\":[%.9g,%.9g,%.9g,%.9g]}\n",
              output.r, output.g, output.b, output.a);
  return 0;
}
