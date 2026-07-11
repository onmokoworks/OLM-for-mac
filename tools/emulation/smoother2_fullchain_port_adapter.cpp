#include "smoother2_fullchain_port_adapter.h"

#include <array>
#include <cstdio>
#include <cstdlib>
#include <vector>

// The production port deliberately keeps its binary-shaped helpers static.
// Including it here exposes those helpers only in this test translation unit.
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {

void print_vertices(const SmootherPolygon &poly, const char *prefix) {
  std::printf("\"%s_count\":%d,\"%s_vertices\":[", prefix, poly.count, prefix);
  for (int i = 0; i < poly.count; ++i) {
    const PolyVertex &v = poly.samples[i];
    if (i) std::putchar(',');
    std::printf("{\"rgba\":[%.9g,%.9g,%.9g,%.9g],\"weight\":%.9g}",
                v.r, v.g, v.b, v.a, v.w);
  }
  std::putchar(']');
}

int classifier_index(const uint8_t *cp, int w, int h, int x, int y) {
  auto b = [&](int xx, int yy, int channel) -> uint8_t {
    if (xx < 0 || xx >= w || yy < 0 || yy >= h) return 0;
    return cp[((size_t)yy * w + xx) * 4 + channel];
  };
  const int east_clear = x < w - 1 ? b(x + 1, y, 0) == 0 : 1;
  const bool sw_b = y < h - 1 && x > 0 && b(x - 1, y + 1, 3) != 0;
  const bool south_r = y < h - 1 && b(x, y + 1, 1) != 0;
  const int se_g_clear = y < h - 1 && x < w - 1 ? b(x + 1, y + 1, 2) == 0 : 1;
  return (((sw_b ? 0 : 2) + east_clear + ((!south_r + se_g_clear * 2) * 4)) * 0x10
          + (b(x, y, 3) == 0 ? 4 : 0) + (b(x, y, 2) == 0 ? 1 : 0)
          + (b(x, y, 1) == 0 ? 2 : 0) + (b(x, y, 0) == 0 ? 8 : 0));
}

}  // namespace

int smoother2_fullchain_port_adapter_main(int argc, char **argv) {
  if (argc != 2) return 2;
  const bool suppress = std::atoi(argv[1]) != 0;
  constexpr int w = 16, h = 16, x = 5, y = 6;
  std::vector<FPix> pixels((size_t)w * h, FPix{0, 0, 0, 0});
  std::vector<uint8_t> classes((size_t)w * h * 4, 0);
  pixels[(size_t)(y - 1) * w + x] = {0.99106717f, 0.99106717f, 0.99106717f, 0.99607843f};
  pixels[(size_t)y * w + x] = {1, 1, 1, 0};
  // Additional independent classifier bytes make c280's index exactly 0x69.
  classes[((size_t)y * w + x) * 4 + 1] = 1;
  classes[((size_t)y * w + x) * 4 + 3] = 1;
  classes[((size_t)y * w + (x + 1)) * 4] = 1;
  classes[((size_t)(y + 1) * w + (x + 1)) * 4 + 2] = 1;
  if (suppress) classes[((size_t)y * w + (x - 1)) * 4 + 1] = 1;
  else classes[((size_t)(y - 1) * w + x) * 4] = 1;

  FPlane plane{pixels.data(), w * sizeof(FPix), 0};
  SmootherPolygon direct{};
  direct.plane = &plane; direct.cplane_base = classes.data();
  direct.cplane_w = w; direct.cplane_h = h; direct.cplane_stride = w * 4;
  direct.cur_x = x; direct.cur_y = y; direct.smoothness_n = 2.0f; direct.extra_n = 0.4f;
  int desc[6] = {x, y, 1, x, y + 2, 5};
  const int c = win_e170(direct, desc);
  const bool appended = win_leaf_f270(direct, desc, K_ONE);

  SmootherPolygon chained{};
  chained.plane = &plane; chained.cplane_base = classes.data();
  chained.cplane_w = w; chained.cplane_h = h; chained.cplane_stride = w * 4;
  chained.cur_x = x; chained.cur_y = y; chained.smoothness_n = 2.0f; chained.extra_n = 0.4f;
  const bool preappend = win_FUN_1800125c0(chained);
  GridDesc grid = grid_of(chained);
  int center[2] = {x, y}, scan_a[3], scan_b[3];
  scan_d3b0(scan_a, &grid, center);
  scan_da50(scan_b, &grid, center);
  int generated_desc[6] = {scan_a[0], scan_a[1], scan_a[2], scan_b[0], scan_b[1], scan_b[2]};
  win_cardinal_6(chained);
  const int before_normalize = chained.count;
  win_FUN_18000cc70_normalize(chained);

  FPix final{};
  composite(final, pixels[(size_t)y * w + x], direct);
  std::printf("{\"fixture\":\"%s\",\"idx\":%d,\"descriptor\":[5,6,1,5,8,5],"
              "\"c\":%d,\"append\":%s,", suppress ? "c4_control" : "c2_witness",
              classifier_index(classes.data(), w, h, x, y), c, appended ? "true" : "false");
  print_vertices(direct, "direct");
  std::printf(",\"pre125c0_append\":%s,\"chain_before_normalize\":%d,",
              preappend ? "true" : "false", before_normalize);
  std::printf("\"cardinal6_descriptor\":[%d,%d,%d,%d,%d,%d],",
              generated_desc[0], generated_desc[1], generated_desc[2], generated_desc[3],
              generated_desc[4], generated_desc[5]);
  print_vertices(chained, "chain");
  std::printf(",\"port_composite_float\":[%.9g,%.9g,%.9g,%.9g]}\n",
              final.r, final.g, final.b, final.a);
  return 0;
}

int main(int argc, char **argv) { return smoother2_fullchain_port_adapter_main(argc, argv); }
