#include <cstdio>
#include <vector>

// Test-only translation unit exposing the production port's static helpers.
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

int main() {
  constexpr int width = 16;
  constexpr int height = 16;
  constexpr int x = 5;
  constexpr int y = 6;

  std::vector<FPix> pixels((size_t)width * height, FPix{0, 0, 0, 0});
  std::vector<uint8_t> classes((size_t)width * height * 4, 0);
  pixels[(size_t)(y - 1) * width + x] = {0.8f, 0.1f, 0.1f, 0.99607843f};
  pixels[(size_t)y * width + x] = {1, 1, 1, 1};

  auto set_class = [&](int xx, int yy, int b0, int b1, int b2, int b3) {
    const size_t off = ((size_t)yy * width + xx) * 4;
    classes[off + 0] = (uint8_t)b0;
    classes[off + 1] = (uint8_t)b1;
    classes[off + 2] = (uint8_t)b2;
    classes[off + 3] = (uint8_t)b3;
  };
  set_class(x, y, 1, 1, 1, 1);
  set_class(x + 1, y, 1, 0, 0, 0);
  set_class(x + 1, y + 1, 0, 0, 1, 0);
  set_class(x - 1, y + 1, 0, 0, 0, 1);
  set_class(x, y - 1, 1, 0, 0, 0);

  FPlane plane{pixels.data(), width * (int)sizeof(FPix), 0};
  SmootherPolygon poly{};
  poly.plane = &plane;
  poly.cplane_base = classes.data();
  poly.cplane_w = width;
  poly.cplane_h = height;
  poly.cplane_stride = width * 4;
  poly.cur_x = x;
  poly.cur_y = y;
  poly.smoothness_n = (float)65536 / 100.0f;
  poly.extra_n = (float)65536 / 100.0f;

  GridDesc grid = grid_of(poly);
  int center[2] = {x, y};
  int scan_up[3];
  int scan_down[3];
  scan_cee0(scan_up, &grid, center);
  scan_d6a0(scan_down, &grid, center);
  int desc[6] = {
      scan_up[0], scan_up[1], scan_up[2],
      scan_down[0], scan_down[1], scan_down[2],
  };
  const int key = desc[2] + (desc[5] * 5 - 1) * 2;
  const int predicate = win_e050(poly, desc);

  int primary_in[2] = {desc[0], desc[1]};
  int primary[3];
  scan_da50(primary, &grid, primary_in);
  const int total_y = desc[4] - desc[1];
  const int cur_span = primary[1] - desc[1];
  const float fmul = poly.extra_n * K_DD8 + K_HALF;
  const float scale_m = (float)(cur_span + 1) * fmul / (float)(total_y + 1);

  int secondary_in[2] = {desc[0], desc[1] - 1};
  int secondary[3] = {0, 0, 0};
  const bool secondary_executed = predicate == 3 || predicate == 7;
  float scale_h = K_ONE;
  if (secondary_executed) {
    scan_cee0(secondary, &grid, secondary_in);
    scale_h = K_ONE;
    if (secondary[2] != 1) scale_h = K_HALF;
  }

  const float trap_p1 =
      (float)(desc[4] - desc[1] + 1) * scale_m * poly.smoothness_n;
  const int trap_p2 = poly.cur_y - desc[1];
  const float trap_p3 = scale_h * K_HALF;
  const float modeled_weight =
      win_FUN_180013630_trapezoid(trap_p1, trap_p2, trap_p3);

  win_cardinal_9(poly);
  const float emitted_weight = poly.count ? poly.samples[0].w : 0.0f;

  std::printf(
      "{\"descriptor\":[%d,%d,%d,%d,%d,%d],\"key\":%d,"
      "\"leaf\":\"win_leaf_ead0\",\"predicate\":%d,"
      "\"primary_scan\":[%d,%d,%d],\"secondary_executed\":%s,"
      "\"secondary_input\":[%d,%d],"
      "\"secondary_scan\":[%d,%d,%d],\"smoothness_n\":%.17g,"
      "\"extra_n\":%.17g,\"scale_m\":%.17g,\"scale_h\":%.17g,"
      "\"trap\":{\"p1\":%.17g,\"p2\":%d,\"p3\":%.17g,"
      "\"weight\":%.17g},\"emitted_count\":%d,"
      "\"emitted_weight\":%.17g}\n",
      desc[0], desc[1], desc[2], desc[3], desc[4], desc[5], key,
      predicate, primary[0], primary[1], primary[2],
      secondary_executed ? "true" : "false", secondary_in[0],
      secondary_in[1], secondary[0], secondary[1], secondary[2],
      poly.smoothness_n, poly.extra_n, scale_m, scale_h, trap_p1, trap_p2,
      trap_p3, modeled_weight, poly.count, emitted_weight);
  return 0;
}
