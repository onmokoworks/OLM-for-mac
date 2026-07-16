#include <cstdint>
#include <cstdio>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr int W = 128, H = 850, X = 92, Y = 841;

void cls(std::vector<uint8_t> &p, int x, int y, int channel, uint8_t value) {
  p[(static_cast<size_t>(y) * W + x) * 4 + channel] = value;
}

void vertex_json(const SmootherPolygon &poly, int i) {
  const PolyVertex &v = poly.samples[i];
  std::printf("{\"rgba\":[%.9g,%.9g,%.9g,%.9g],\"weight\":%.9g}", v.r, v.g, v.b, v.a, v.w);
}

void snapshot_json(const SmootherPolygon &poly, const char *name) {
  std::printf("\"%s\":{\"boundary\":\"%s\",\"count\":%d,\"vertices\":[", name, name, poly.count);
  for (int i = 0; i < poly.count; ++i) { if (i) std::printf(","); vertex_json(poly, i); }
  std::printf("]}");
}
}

int main() {
  std::vector<FPix> pixels(static_cast<size_t>(W) * H, FPix{0, 0, 0, 0});
  std::vector<uint8_t> classes(static_cast<size_t>(W) * H * 4, 0);
  cls(classes, X, Y, 0, 255);
  cls(classes, X, Y - 1, 0, 255);
  cls(classes, X - 1, Y, 1, 255);
  FPlane plane{pixels.data(), W * static_cast<int>(sizeof(FPix)), 0};
  plane.base[(Y - 1) * W + X] = FPix{0.18447503f, 0.18447503f, 0.18447503f, 0.68235296f};
  plane.base[(Y + 2) * W + X] = FPix{0.125f, 0.25f, 0.75f, 0.625f};
  SmootherPolygon poly{};
  poly.plane = &plane; poly.cplane_base = classes.data(); poly.cplane_w = W;
  poly.cplane_h = H; poly.cplane_stride = W * 4; poly.cur_x = X; poly.cur_y = Y;
  poly.smoothness_n = 2.0f; poly.extra_n = 0.4f;
  int desc[6] = {X, Y, 1, X, Y + 1, 2};
  std::printf("{\"snapshots\":{");
  const int e170 = win_e170(poly, desc);
  const int before = poly.count;
  const bool f270 = win_leaf_f270(poly, desc, K_ONE);
  const int f270_count = poly.count;
  snapshot_json(poly, "after_f270");
  const int df30 = win_df30(poly, desc);
  const bool f130 = win_leaf_f130(poly, desc, K_ONE);
  const int f130_count = poly.count;
  std::printf(","); snapshot_json(poly, "after_f130");
  std::printf("},\"descriptor\":[%d,%d,%d,%d,%d,%d],\"key\":20,\"entry\":{"
              "\"e170_c\":%d,\"df30\":%d},\"calls\":{\"f270_return_low\":%d,\"f130_return_low\":%d,\"count_before\":%d,\"f270_count\":%d,\"f130_count\":%d},\"cce0_called\":false}\n",
              desc[0], desc[1], desc[2], desc[3], desc[4], desc[5], e170, df30,
              f270 ? 1 : 0, f130 ? 1 : 0, before, f270_count, f130_count);
  return 0;
}
