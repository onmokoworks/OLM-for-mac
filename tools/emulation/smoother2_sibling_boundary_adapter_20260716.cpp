#include <cstdio>
#include <cstring>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {

constexpr int W = 16;
constexpr int H = 16;
constexpr int X = 5;
constexpr int Y = 5;

void set_class(std::vector<uint8_t> &classes, int x, int y, int channel) {
  classes[(static_cast<size_t>(y) * W + x) * 4 + channel] = 1;
}

void install_fixture(std::vector<uint8_t> &classes, const char *leaf, int scenario) {
  if (std::strcmp(leaf, "e4b0") == 0) {
    set_class(classes, X + 1, Y, 0);
    if (scenario == 3) set_class(classes, X + 1, Y + 1, 0);
  } else if (std::strcmp(leaf, "edb0") == 0) {
    set_class(classes, X, Y, 0);
    if (scenario == 3) set_class(classes, X, Y - 1, 0);
  } else if (std::strcmp(leaf, "e7c0") == 0) {
    set_class(classes, X, Y, 0);
    if (scenario == 3) set_class(classes, X, Y + 1, 0);
  }
}

void print_vertices(const SmootherPolygon &poly) {
  std::printf("\"emitted_count\":%d,\"vertices\":[", poly.count);
  for (int i = 0; i < poly.count; ++i) {
    if (i) std::putchar(',');
    const PolyVertex &v = poly.samples[i];
    std::printf("{\"weight\":%.9g}", v.w);
  }
  std::putchar(']');
}

}  // namespace

int main(int argc, char **argv) {
  if (argc != 3) return 2;
  const char *leaf = argv[1];
  const int scenario = std::atoi(argv[2]);
  if ((std::strcmp(leaf, "e4b0") != 0 && std::strcmp(leaf, "edb0") != 0 &&
       std::strcmp(leaf, "e7c0") != 0) || (scenario != 1 && scenario != 3)) return 2;

  std::vector<FPix> pixels(static_cast<size_t>(W) * H, FPix{0, 0, 0, 1});
  std::vector<uint8_t> classes(static_cast<size_t>(W) * H * 4, 0);
  install_fixture(classes, leaf, scenario);
  FPlane plane{pixels.data(), W * static_cast<int>(sizeof(FPix)), 0};
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
  int desc[6] = {2, 2, 1, X, Y, 5};
  if (std::strcmp(leaf, "edb0") == 0) {
    desc[0] = X;
    desc[1] = Y;
  }
  bool emitted = false;
  int predicate = 0;
  float scale_h = K_ONE;
  int primary[3] = {0, 0, 0};
  int secondary[3] = {0, 0, 0};
  GridDesc grid = grid_of(poly);
  if (std::strcmp(leaf, "e4b0") == 0) {
    predicate = win_de10(poly, desc);
    int in[2] = {desc[3], desc[4]};
    scan_d3b0(primary, &grid, in);
    if (scenario == 3) {
      int next[2] = {desc[3], desc[4] + 1};
      scan_d6a0(secondary, &grid, next);
      scale_h = secondary[2] == 2 ? K_ONE : K_HALF;
    }
    emitted = win_leaf_e4b0(poly, desc);
  } else if (std::strcmp(leaf, "edb0") == 0) {
    predicate = win_e170(poly, desc);
    int in[2] = {desc[0], desc[1]};
    scan_d6a0(primary, &grid, in);
    if (scenario == 3) {
      int next[2] = {desc[0], desc[1] - 1};
      scan_d3b0(secondary, &grid, next);
      scale_h = secondary[2] == 2 ? K_ONE : K_HALF;
    }
    emitted = win_leaf_edb0(poly, desc);
  } else {
    predicate = win_df30(poly, desc);
    int in[2] = {desc[3], desc[4]};
    scan_cee0(primary, &grid, in);
    if (scenario == 3) {
      int next[2] = {desc[3], desc[4] + 1};
      scan_da50(secondary, &grid, next);
      scale_h = secondary[2] == 1 ? K_ONE : K_HALF;
    }
    emitted = win_leaf_e7c0(poly, desc);
  }
  std::printf("{\"leaf\":\"%s\",\"scenario\":%d,\"descriptor\":[%d,%d,%d,%d,%d,%d],"
              "\"predicate\":%d,\"secondary_expected\":%s,\"primary_scan\":[%d,%d,%d],"
              "\"secondary_scan\":[%d,%d,%d],\"scale_h\":%.9g,\"emitted\":%s,",
              leaf, scenario, desc[0], desc[1], desc[2], desc[3], desc[4], desc[5],
              predicate, scenario == 3 ? "true" : "false",
              primary[0], primary[1], primary[2], secondary[0], secondary[1], secondary[2], scale_h,
              emitted ? "true" : "false");
  print_vertices(poly);
  std::printf("}\n");
  return 0;
}
