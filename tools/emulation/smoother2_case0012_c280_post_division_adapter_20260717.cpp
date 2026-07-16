#include <cstdio>
#include <cstdint>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr int W = 128, H = 850, X = 92, Y = 841;
void emit(const SmootherPolygon &p, int i) {
  const PolyVertex &v = p.samples[i];
  std::printf("{\"rgba\":[%.9g,%.9g,%.9g,%.9g],\"weight\":%.9g}", v.r, v.g, v.b, v.a, v.w);
}
}

int main() {
  std::vector<FPix> pixels(static_cast<size_t>(W) * H, FPix{0, 0, 0, 0});
  std::vector<uint8_t> classes(static_cast<size_t>(W) * H * 4, 0);
  pixels[(Y - 1) * W + X] = FPix{0.18447503f, 0.18447503f, 0.18447503f, 0.68235296f};
  pixels[Y * W + X] = FPix{1, 1, 1, 1};
  pixels[(Y + 2) * W + X] = FPix{0.125f, 0.25f, 0.75f, 0.625f};
  auto cls = [&](int x, int y, uint8_t a, uint8_t r, uint8_t g, uint8_t b) {
    auto off = (static_cast<size_t>(y) * W + x) * 4;
    classes[off + 0] = a; classes[off + 1] = r; classes[off + 2] = g; classes[off + 3] = b;
  };
  cls(X, Y, 255, 255, 0, 255);
  cls(X, Y - 1, 255, 0, 0, 0);
  cls(X - 1, Y, 0, 255, 0, 255);
  FPlane plane{pixels.data(), W * static_cast<int>(sizeof(FPix)), 0};
  SMParams p{}; p.version = 2; p.w = W; p.h = H; p.class_plane = classes.data();
  p.smoothness_raw = 65536; p.extra_smooth_raw = 65536; p.gamma_mode = GAMMA_NONE;
  SmootherPolygon poly{};
  build_polygon(poly, plane, X, Y, p);
  FPix out{};
  win_FUN_18000cce0_orchestrate(out, plane, plane, X, Y, p);
  std::printf("{\"c280\":{\"count\":%d,\"vertices\":[", poly.count);
  for (int i = 0; i < poly.count; ++i) { if (i) std::putchar(','); emit(poly, i); }
  std::printf("]},\"cce0\":[%.9g,%.9g,%.9g,%.9g]}\n", out.r, out.g, out.b, out.a);
}
