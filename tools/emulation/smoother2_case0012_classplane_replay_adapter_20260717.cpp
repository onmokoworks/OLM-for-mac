#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr int W = 128;
constexpr int H = 850;
constexpr int X = 92;
constexpr int Y = 841;

void set_class(std::vector<uint8_t> &classes, int x, int y,
               uint8_t b0, uint8_t b1, uint8_t b2, uint8_t b3) {
  const size_t off = (static_cast<size_t>(y) * W + x) * 4;
  classes[off] = b0;
  classes[off + 1] = b1;
  classes[off + 2] = b2;
  classes[off + 3] = b3;
}

void emit_vertex(const PolyVertex &v) {
  std::printf("{\"rgba\":[%.9g,%.9g,%.9g,%.9g],\"weight\":%.9g}",
              v.r, v.g, v.b, v.a, v.w);
}
}  // namespace

int main(int argc, char **argv) {
  if (argc != 2 || (std::strcmp(argv[1], "zero") != 0 &&
                    std::strcmp(argv[1], "one") != 0)) {
    std::fprintf(stderr, "usage: %s zero|one\n", argv[0]);
    return 2;
  }

  const bool fill_one = std::strcmp(argv[1], "one") == 0;
  std::vector<FPix> pixels(static_cast<size_t>(W) * H, FPix{0, 0, 0, 0});
  std::vector<uint8_t> classes(static_cast<size_t>(W) * H * 4, 0);
  pixels[(Y - 1) * W + X] = FPix{0.18447503f, 0.18447503f, 0.18447503f, 0.68235296f};
  pixels[Y * W + X] = FPix{1, 1, 1, 1};
  pixels[(Y + 2) * W + X] = FPix{0.125f, 0.25f, 0.75f, 0.625f};

  if (fill_one) {
    for (int dy = -4; dy <= 4; ++dy) {
      for (int dx = -4; dx <= 4; ++dx) {
        set_class(classes, X + dx, Y + dy, 255, 255, 255, 255);
      }
    }
  }
  set_class(classes, X, Y, 255, 255, 0, 255);
  set_class(classes, X, Y - 1, 255, 0, 0, 0);
  set_class(classes, X - 1, Y, 0, 255, 0, 255);

  FPlane plane{pixels.data(), W * static_cast<int>(sizeof(FPix)), 0};
  SMParams params{};
  params.version = 2;
  params.w = W;
  params.h = H;
  params.class_plane = classes.data();
  params.smoothness_raw = 65536;
  params.extra_smooth_raw = 65536;
  params.gamma_mode = GAMMA_NONE;
  SmootherPolygon polygon{};
  build_polygon(polygon, plane, X, Y, params);

  std::printf("{\"completion\":\"%s\",\"count\":%d,\"vertices\":[",
              argv[1], polygon.count);
  for (int i = 0; i < polygon.count; ++i) {
    if (i != 0) std::putchar(',');
    emit_vertex(polygon.samples[i]);
  }
  std::printf("]}\n");
  return 0;
}
