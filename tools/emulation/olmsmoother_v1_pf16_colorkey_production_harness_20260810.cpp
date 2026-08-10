#include <cstdint>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

extern "C" int olmsmoother_v1_render16_colorkey(
    uint16_t *source, uint16_t *destination, int32_t width, int32_t height,
    int32_t rowbytes, int32_t use_key, uint8_t key_r, uint8_t key_g,
    uint8_t key_b, int32_t tolerance) {
  PF_ParamDef input{}, use{}, key{}, range{};
  input.u.ld.data = source;
  input.u.ld.width = width;
  input.u.ld.height = height;
  input.u.ld.rowbytes = rowbytes;
  input.u.ld.extent_hint = {0, 0, width, height};
  use.u.bd.value = use_key;
  key.u.cd.value.alpha = 255;
  key.u.cd.value.red = key_r;
  key.u.cd.value.green = key_g;
  key.u.cd.value.blue = key_b;
  range.u.sd.value = tolerance;
  PF_ParamDef *params[SM_NUM_PARAMS] = {&input, &use, &key, &range};

  PF_EffectWorld output{};
  output.data = destination;
  output.width = width;
  output.height = height;
  output.rowbytes = rowbytes;
  output.extent_hint = {0, 0, width, height};
  PF_InData in{};
  return DispatchRender(&in, params, &input.u.ld, &output, 16);
}
