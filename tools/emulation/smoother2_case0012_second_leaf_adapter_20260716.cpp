#include <cstdint>
#include <cstdio>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr int W = 128;
constexpr int H = 850;
constexpr int X = 92;
constexpr int Y = 841;

void set_class(std::vector<uint8_t> &classes, int x, int y, int channel, uint8_t value) {
  classes[(static_cast<size_t>(y) * W + x) * 4 + channel] = value;
}

void emit_vertex(const SmootherPolygon &poly, int index) {
  const PolyVertex &v = poly.samples[index];
  std::printf("{\"source_xy\":[%d,%d],\"rgba\":[%.9g,%.9g,%.9g,%.9g],\"weight\":%.9g}",
              index == 0 ? X : X, index == 0 ? Y - 1 : Y + 2,
              v.r, v.g, v.b, v.a, v.w);
}
}

int main() {
  std::vector<FPix> pixels(static_cast<size_t>(W) * H, FPix{0, 0, 0, 0});
  std::vector<uint8_t> classes(static_cast<size_t>(W) * H * 4, 0);
  // These are the accepted first-leaf predicate bytes. The second-leaf bytes
  // are intentionally a local fixture; no Windows second-leaf value is used.
  set_class(classes, X, Y, 0, 255);
  set_class(classes, X, Y - 1, 0, 255);
  set_class(classes, X - 1, Y, 1, 255);
  FPlane plane{pixels.data(), W * static_cast<int>(sizeof(FPix)), 0};
  plane.base[(Y + 2) * W + X] = FPix{0.125f, 0.25f, 0.75f, 0.625f};
  SmootherPolygon poly{};
  poly.plane = &plane;
  poly.cplane_base = classes.data();
  poly.cplane_w = W;
  poly.cplane_h = H;
  poly.cplane_stride = W * 4;
  poly.cur_x = X;
  poly.cur_y = Y;
  poly.smoothness_n = 2.0f;
  poly.extra_n = 0.4f;
  int desc[6] = {X, Y, 1, X, Y + 1, 2};

  const int count_before = poly.count;
  const int first_predicate = win_e170(poly, desc);
  const bool first_append = win_leaf_f270(poly, desc, K_ONE);
  const int count_after_first = poly.count;
  const int second_predicate = win_df30(poly, desc);
  const bool second_append = win_leaf_f130(poly, desc, K_ONE);
  const int count_after_second = poly.count;
  SmootherPolygon dispatch_poly = poly;
  dispatch_poly.count = 0;
  win_disp_fef0(dispatch_poly, desc);

  std::printf("{\"descriptor\":[%d,%d,%d,%d,%d,%d],\"entry\":{\"first_predicate_e170\":%d,\"second_predicate_df30\":%d},"
              "\"first_leaf\":{\"name\":\"f270->e3a0\",\"append\":%s,\"count_before\":%d,\"count_after\":%d},"
              "\"second_leaf\":{\"name\":\"f130->e290\",\"path\":{\"predicate\":\"FUN_18000df30\",\"wrapper\":\"FUN_18000f130\",\"emitter\":\"FUN_18000e290\"},\"append\":%s,\"count_before\":%d,\"count_after\":%d,\"returned_vertex\":",
              desc[0], desc[1], desc[2], desc[3], desc[4], desc[5], first_predicate, second_predicate,
              first_append ? "true" : "false", count_before, count_after_first,
              second_append ? "true" : "false", count_after_first, count_after_second);
  if (second_append && count_after_second > count_after_first) emit_vertex(poly, count_after_first);
  else std::printf("null");
  std::printf("},\"dispatcher\":{\"name\":\"fef0\",\"key\":%d,\"count_after\":%d},\"vertices_total\":%d}\n",
              desc[2] - 1 + desc[5] * 10, dispatch_poly.count, poly.count);
  return 0;
}
