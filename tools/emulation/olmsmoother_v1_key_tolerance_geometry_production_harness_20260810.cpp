#include <cstdint>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

template <typename T>
static int render_effectmain(
    T *source, T *destination, int32_t width, int32_t height,
    int32_t rowbytes, int32_t bitdepth, int32_t use_key,
    uint8_t key_r, uint8_t key_g, uint8_t key_b, int32_t tolerance) {
  PF_ParamDef input{}, use{}, key{}, range{};
  input.u.ld.data = source;
  input.u.ld.width = width;
  input.u.ld.height = height;
  input.u.ld.rowbytes = rowbytes;
  input.u.ld.bitdepth = static_cast<short>(bitdepth);
  input.u.ld.extent_hint = {0, 0, width, height};
  use.u.bd.value = use_key;
  key.u.cd.value = {255, key_r, key_g, key_b};
  range.u.sd.value = tolerance;
  PF_ParamDef *params[SM_NUM_PARAMS] = {&input, &use, &key, &range};
  PF_LayerDef output{};
  output.data = destination;
  output.width = width;
  output.height = height;
  output.rowbytes = rowbytes;
  output.bitdepth = static_cast<short>(bitdepth);
  output.extent_hint = {0, 0, width, height};
  PF_InData in{};
  PF_OutData out{};
  return EffectMain(PF_Cmd_RENDER, &in, &out, params, &output, nullptr);
}

extern "C" int olmsmoother_v1_effectmain_render8_matrix(
    uint8_t *source, uint8_t *destination, int32_t width, int32_t height,
    int32_t rowbytes, int32_t use_key, uint8_t key_r, uint8_t key_g,
    uint8_t key_b, int32_t tolerance) {
  return render_effectmain(source, destination, width, height, rowbytes, 8,
                           use_key, key_r, key_g, key_b, tolerance);
}

extern "C" int olmsmoother_v1_effectmain_render16_matrix(
    uint16_t *source, uint16_t *destination, int32_t width, int32_t height,
    int32_t rowbytes, int32_t use_key, uint8_t key_r, uint8_t key_g,
    uint8_t key_b, int32_t tolerance) {
  return render_effectmain(source, destination, width, height, rowbytes, 16,
                           use_key, key_r, key_g, key_b, tolerance);
}

extern "C" int32_t olmsmoother_v1_color_compare8(
    const uint8_t *first, const uint8_t *second) {
  return ColorCompare8(first, second);
}

extern "C" int32_t olmsmoother_v1_color_compare16(
    const uint16_t *first, const uint16_t *second) {
  return ColorCompare16(first, second);
}

extern "C" int32_t olmsmoother_v1_classifier16_matrix(
    uint16_t *source, int32_t width, int32_t height, int32_t rowbytes,
    int32_t x, int32_t y, int32_t direction, int32_t tolerance) {
  PF_EffectWorld world{}; world.data=source; world.width=width; world.height=height; world.rowbytes=rowbytes;
  RenderState state{}; state.src_world=&world; state.tolerance_hi=tolerance;
  uintptr_t neighbors[10]{}; NeighborExtract16(x,y,&state,neighbors);
  return Classifier16(&state,x,y,neighbors,direction);
}
