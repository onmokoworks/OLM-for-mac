#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

namespace {
constexpr int W = 16;
constexpr int H = 16;
constexpr int X = 5;
constexpr int Y = 6;

uint32_t f32_bits(float value) {
  uint32_t bits = 0;
  static_assert(sizeof(bits) == sizeof(value), "float32 size mismatch");
  std::memcpy(&bits, &value, sizeof(bits));
  return bits;
}

void print_f32_array(const char *name, const float *values, int count) {
  std::printf("\"%s\":[", name);
  for (int i = 0; i < count; ++i) {
    if (i) std::putchar(',');
    std::printf("%.9g", values[i]);
  }
  std::putchar(']');
}

void print_u32_array(const char *name, const uint32_t *values, int count) {
  std::printf("\"%s\":[", name);
  for (int i = 0; i < count; ++i) {
    if (i) std::putchar(',');
    std::printf("%u", values[i]);
  }
  std::putchar(']');
}

void print_vertex(const PolyVertex &v) {
  const float rgba[4] = {v.r, v.g, v.b, v.a};
  const uint32_t rgba_u32[4] = {
      f32_bits(v.r), f32_bits(v.g), f32_bits(v.b), f32_bits(v.a)};
  const uint32_t weight_u32 = f32_bits(v.w);
  std::putchar('{');
  print_f32_array("rgba_f32", rgba, 4);
  std::putchar(',');
  print_u32_array("rgba_u32", rgba_u32, 4);
  std::printf(",\"weight_f32\":%.9g,\"weight_u32\":%u}", v.w, weight_u32);
}

void print_vertices(const SmootherPolygon &poly, const char *name) {
  std::printf("\"%s_count\":%d,\"%s_vertices\":[", name, poly.count, name);
  for (int i = 0; i < poly.count; ++i) {
    if (i) std::putchar(',');
    print_vertex(poly.samples[i]);
  }
  std::putchar(']');
}

void set_class(std::vector<uint8_t> &classes, int x, int y,
               uint8_t b0, uint8_t b1, uint8_t b2, uint8_t b3) {
  const size_t off = (static_cast<size_t>(y) * W + x) * 4;
  classes[off + 0] = b0;
  classes[off + 1] = b1;
  classes[off + 2] = b2;
  classes[off + 3] = b3;
}

void init_fixture(std::vector<FPix> &pixels, std::vector<uint8_t> &classes) {
  pixels[static_cast<size_t>(Y - 1) * W + X] = {0.8f, 0.1f, 0.1f, 0.99607843f};
  pixels[static_cast<size_t>(Y) * W + X] = {1, 1, 1, 1};
  set_class(classes, X, Y, 0, 1, 0, 1);
  set_class(classes, X + 1, Y, 1, 0, 0, 0);
  set_class(classes, X + 1, Y + 1, 0, 0, 1, 0);
  set_class(classes, X, Y - 1, 1, 0, 0, 0);
}

void print_pixel(const char *name, const FPix &px) {
  const float rgba[4] = {px.r, px.g, px.b, px.a};
  const uint32_t rgba_u32[4] = {
      f32_bits(px.r), f32_bits(px.g), f32_bits(px.b), f32_bits(px.a)};
  std::printf("\"%s\":{", name);
  print_f32_array("rgba_f32", rgba, 4);
  std::putchar(',');
  print_u32_array("rgba_u32", rgba_u32, 4);
  std::putchar('}');
}
}  // namespace

int main() {
  std::vector<FPix> pixels(static_cast<size_t>(W) * H, FPix{0, 0, 0, 0});
  std::vector<uint8_t> classes(static_cast<size_t>(W) * H * 4, 0);
  init_fixture(pixels, classes);
  FPlane plane{pixels.data(), W * static_cast<int>(sizeof(FPix)), 0};

  SMParams params{};
  params.version = 2;
  params.w = W;
  params.h = H;
  params.class_plane = classes.data();
  // FUN_18000c280 receives these two fixed-point config words and divides
  // both by 100.0f before populating the polygon header.
  params.smoothness_raw = 65536;
  params.extra_smooth_raw = 65536;
  params.gamma_mode = GAMMA_NONE;
  params.gamma_value = 0.0f;
  params.num_gamma_colors = 0;

  SmootherPolygon c280{};
  build_polygon(c280, plane, X, Y, params);
  FPix cce0{};
  win_FUN_18000cce0_orchestrate(cce0, plane, plane, X, Y, params);

  std::printf("{\"fixture\":{\"name\":\"c2_witness\",\"width\":%d,\"height\":%d,"
              "\"xy\":[%d,%d],"
              "\"source_pixels\":[[%d,%d,0.8,0.1,0.1,0.99607843],[%d,%d,1,1,1,1]],"
              "\"class_pixels\":[[%d,%d,0,1,0,1],[%d,%d,1,0,0,0],"
              "[%d,%d,0,0,1,0],[%d,%d,1,0,0,0]]},",
              W, H, X, Y,
              X, Y - 1, X, Y,
              X, Y, X + 1, Y, X + 1, Y + 1, X, Y - 1);
  std::printf("\"caller_config\":{\"version\":2,\"scale_fixed\":[65536,65536],"
              "\"normalized\":[655.36,655.36],\"gamma_mode_byte\":0},"
              "\"c280_count\":%d,",
              c280.count);
  print_vertices(c280, "c280");
  std::putchar(',');
  print_pixel("cce0", cce0);
  std::puts("}");
  return 0;
}
