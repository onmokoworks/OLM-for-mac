#include <cstdint>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

extern "C" int64_t olmsmoother_edgewalker16_generated(
    uint16_t *argb, int width, int height, int x, int y, int dir1,
    uint32_t dir2, int threshold, int *out_x, int *out_y) {
  PF_EffectWorld world{};
  world.data = argb;
  world.width = width;
  world.height = height;
  world.rowbytes = width * 8;
  RenderState state{};
  state.tolerance_lo = threshold;
  state.tolerance_hi = threshold;
  state.threshold = threshold;
  state.src_world = &world;
  uint16_t *result = EdgeWalker16Exact(
      &state, x, y, dir1, dir2, out_x, out_y, threshold);
  // The original routine's decompiler type is misleading: EAX is a small
  // classification code (normally 0/1/2), not a dereferenceable pixel pointer.
  return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(result));
}

extern "C" void olmsmoother_subhandler16_generated(
    uint16_t *argb, int width, int height, int x, int y,
    uint32_t direction, int tolerance_lo, int tolerance_hi,
    uint32_t *out) {
  PF_EffectWorld world{};
  world.data = argb;
  world.width = width;
  world.height = height;
  world.rowbytes = width * 8;
  RenderState state{};
  state.tolerance_lo = tolerance_lo;
  state.tolerance_hi = tolerance_hi;
  state.threshold = tolerance_lo;
  state.src_world = &world;
  uintptr_t neighbors[9];
  int k = 0;
  for (int dy = -1; dy <= 1; ++dy) {
    for (int dx = -1; dx <= 1; ++dx) {
      neighbors[k++] = reinterpret_cast<uintptr_t>(
          argb + ((y + dy) * width + x + dx) * 4);
    }
  }
  uint32_t mode, x1, y1, x2, y2, x3, y3;
  uint8_t flag1, flag2;
  SubHandler16Exact(&state, neighbors, x, y, direction, &mode, &flag1,
                    &flag2, &x1, &y1, &x2, &y2, &x3, &y3);
  const uint32_t values[9] = {mode, flag1, flag2, x1, y1, x2, y2, x3, y3};
  for (int i = 0; i < 9; ++i) out[i] = values[i];
}
