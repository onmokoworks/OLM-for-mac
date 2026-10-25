// SDK EVENT host. Foundation is used only for JSON I/O; plugin code is
// included directly, without a test-only EVENT implementation.
#include "ui_host_base.cpp"
#import <Foundation/Foundation.h>
#include <cassert>
static NSMutableArray *calls;
static NSDictionary *input;
static uint64_t next_object = 0x554900000000ULL;
static std::map<uint64_t, int> refs;
static id nullv() { return [NSNull null]; }
static NSNumber *bits(float f) {
  uint32_t u;
  memcpy(&u, &f, 4);
  return @(u);
}
static NSArray *floats(const void *p, int n) {
  NSMutableArray *a = [NSMutableArray array];
  for (int i = 0; i < n; i++) {
    float f;
    memcpy(&f, (const char *)p + 4 * i, 4);
    [a addObject:bits(f)];
  }
  return a;
}
static NSArray *bytes(const void *p, int n) {
  NSMutableArray *a = [NSMutableArray array];
  for (int i = 0; i < n; i++)
    [a addObject:@(((const unsigned char *)p)[i])];
  return a;
}
static void rec(NSDictionary *d) { [calls addObject:d]; }
static uint64_t obj(NSString *name, const void *c, id size) {
  uint64_t o = ++next_object;
  refs[o] = 1;
  rec(@{
    @"call" : name,
    @"object" : @(o),
    @"color_bits" : c ? floats(c, 4) : nullv(),
    @"size_bits" : size
  });
  return o;
}
static SPErr pen(DRAWBOT_SupplierRef, const DRAWBOT_ColorRGBA *c, float w,
                 DRAWBOT_PenRef *o) {
  *o = (DRAWBOT_PenRef)obj(@"NewPen", c, bits(w));
  return 0;
}
static SPErr brush(DRAWBOT_SupplierRef, const DRAWBOT_ColorRGBA *c,
                   DRAWBOT_BrushRef *o) {
  *o = (DRAWBOT_BrushRef)obj(@"NewBrush", c, nullv());
  return 0;
}
static SPErr font(DRAWBOT_SupplierRef, float s, DRAWBOT_FontRef *o) {
  *o = (DRAWBOT_FontRef)obj(@"NewDefaultFont", nullptr, bits(s));
  return 0;
}
static SPErr path(DRAWBOT_SupplierRef, DRAWBOT_PathRef *o) {
  *o = (DRAWBOT_PathRef)obj(@"NewPath", nullptr, nullv());
  return 0;
}
static SPErr release(DRAWBOT_ObjectRef o) {
  assert(refs.at((uint64_t)o) > 0);
  rec(@{
    @"call" : @"ReleaseObject",
    @"object" : @((uint64_t)o),
    @"references" : @(--refs[(uint64_t)o])
  });
  return 0;
}
static SPErr move(DRAWBOT_PathRef p, float x, float y) {
  rec(@{
    @"call" : @"MoveTo",
    @"path" : @((uint64_t)p),
    @"point_bits" : @[ bits(x), bits(y) ]
  });
  return 0;
}
static SPErr line(DRAWBOT_PathRef p, float x, float y) {
  rec(@{
    @"call" : @"LineTo",
    @"path" : @((uint64_t)p),
    @"point_bits" : @[ bits(x), bits(y) ]
  });
  return 0;
}
static SPErr rect(DRAWBOT_PathRef p, const DRAWBOT_RectF32 *r) {
  rec(@{
    @"call" : @"AddRect",
    @"path" : @((uint64_t)p),
    @"rect_bits" : floats(r, 4)
  });
  return 0;
}
static SPErr stroke(DRAWBOT_SurfaceRef, DRAWBOT_PenRef p, DRAWBOT_PathRef q) {
  rec(@{
    @"call" : @"StrokePath",
    @"object" : @((uint64_t)p),
    @"path" : @((uint64_t)q),
    @"fill_type" : nullv()
  });
  return 0;
}
static SPErr paint(DRAWBOT_SurfaceRef, const DRAWBOT_ColorRGBA *c,
                   const DRAWBOT_RectF32 *r) {
  rec(@{
    @"call" : @"PaintRect",
    @"color_bits" : floats(c, 4),
    @"rect_bits" : floats(r, 4)
  });
  return 0;
}
static SPErr aa(DRAWBOT_SurfaceRef, DRAWBOT_AntiAliasPolicy p) {
  rec(@{@"call" : @"SetAntiAliasPolicy", @"policy" : @(p)});
  return 0;
}
static SPErr text(DRAWBOT_SurfaceRef, DRAWBOT_BrushRef b, DRAWBOT_FontRef f,
                  const DRAWBOT_UTF16Char *s, const DRAWBOT_PointF32 *p,
                  DRAWBOT_TextAlignment a, DRAWBOT_TextTruncation t, float w) {
  NSMutableArray *u = [NSMutableArray array];
  for (; *s; s++)
    [u addObject:@(*s)];
  rec(@{
    @"call" : @"DrawString",
    @"brush" : @((uint64_t)b),
    @"font" : @((uint64_t)f),
    @"origin_bits" : floats(p, 2),
    @"alignment" : @(a),
    @"truncation" : @(t),
    @"truncation_width_bits" : bits(w),
    @"utf16" : u
  });
  return 0;
}
static PF_Err drawref(PF_ContextH, DRAWBOT_DrawRef *d) {
  *d = (DRAWBOT_DrawRef)1;
  rec(@{@"call" : @"PF_GetDrawingReference", @"draw" : @1});
  return 0;
}
static SPErr supplier(DRAWBOT_DrawRef, DRAWBOT_SupplierRef *d) {
  *d = (DRAWBOT_SupplierRef)2;
  rec(@{@"call" : @"GetSupplier", @"object" : @2});
  return 0;
}
static SPErr surface(DRAWBOT_DrawRef, DRAWBOT_SurfaceRef *d) {
  *d = (DRAWBOT_SurfaceRef)3;
  rec(@{@"call" : @"GetSurface", @"object" : @3});
  return 0;
}
static PF_Err color(PF_App_ColorType r, PF_App_Color *c) {
  NSArray *a = input[@"theme"][[NSString stringWithFormat:@"%d", r]];
  assert(a && a.count == 3);
  c->red = [a[0] intValue];
  c->green = [a[1] intValue];
  c->blue = [a[2] intValue];
  rec(@{@"call" : @"PF_AppGetColor", @"role" : @(r), @"rgb16" : a});
  return 0;
}
static PF_Err invalidate(PF_ContextH, const PF_Rect *r) {
  assert(r);
  rec(@{
    @"call" : @"PF_InvalidateRect",
    @"rect_bytes_u32" : @[ @(r->left), @(r->top), @(r->right), @(r->bottom) ]
  });
  return 0;
}
static PF_Err pick_color(const A_char *title, const PF_PixelFloat *s,
                         PF_Boolean t, PF_PixelFloat *o) {
  id a = input[@"picker_argb_bits"];
  rec(@{
    @"call" : @"PF_AppColorPickerDialog",
    @"title_bytes" : bytes(title, strlen(title)),
    @"sample_argb_bits" : floats(s, 4),
    @"transform" : @(bool(t)),
    @"result_argb_bits" : a
  });
  if (a == nullv())
    return PF_Interrupt_CANCEL;
  for (int i = 0; i < 4; i++) {
    uint32_t b = [a[i] unsignedIntValue];
    memcpy((char *)o + i * 4, &b, 4);
  }
  return 0;
}
static PF_Err update_ui(PF_ProgPtr, PF_ParamIndex slot, const PF_ParamDef *p) {
  rec(@{
    @"call" : @"PF_UpdateParamUI",
    @"slot" : @(slot),
    @"flags" : @(p->flags),
    @"ui_flags" : @(p->ui_flags),
    @"width" : @(p->ui_width),
    @"height" : @(p->ui_height),
    @"name_bytes" : bytes(p->name, 32),
    @"slider_ui" : @[]
  });
  g_defs[slot].ui_flags = p->ui_flags;
  return 0;
}
static PF_ParamUtilsSuite3 utils{};
static PFAppSuite6 app{};
static PF_EffectCustomUISuite2 custom{};
static DRAWBOT_DrawbotSuite1 draw{};
static DRAWBOT_SupplierSuite1 sup{};
static DRAWBOT_SurfaceSuite2 surf{};
static DRAWBOT_PathSuite1 paths{};
static SPErr ui_acquire(const char *n, int32 v, const void **p) {
#define SUITE(N, V, S)                                                         \
  if (!strcmp(n, N) && v == V) {                                               \
    *p = &S;                                                                   \
    return 0;                                                                  \
  }
  SUITE(kPFParamUtilsSuite, kPFParamUtilsSuiteVersion3, utils)
  SUITE(kPFAppSuite, kPFAppSuiteVersion6, app)
  SUITE(kPFEffectCustomUISuite, kPFEffectCustomUISuiteVersion2, custom)
  SUITE(kDRAWBOT_DrawSuite, 1, draw)
  SUITE(kDRAWBOT_SupplierSuite, 1, sup)
  SUITE(kDRAWBOT_SurfaceSuite, 2, surf)
  SUITE(kDRAWBOT_PathSuite, 1, paths)
#undef SUITE
  if (acquire_suite(n, v, p) == 0)
    return 0;
  fprintf(stderr, "unsupported suite %s v%d\n", n, v);
  abort();
}
// Expose real SDK scalar fields, never echo saved expected values after
// dispatch.
static std::pair<void *, size_t> scalar(PF_ParamDef &p) {
  switch (p.param_type) {
  case PF_Param_POPUP:
    return {&p.u.pd.value, 4};
  case PF_Param_CHECKBOX:
    return {&p.u.bd.value, 4};
  case PF_Param_SLIDER:
    return {&p.u.sd.value, 4};
  case PF_Param_FLOAT_SLIDER:
    return {&p.u.fs_d.value, 8};
  case PF_Param_ANGLE:
    return {&p.u.ad.value, 4};
  case PF_Param_COLOR:
    return {&p.u.cd.value, 4};
  case PF_Param_GROUP_START:
  case PF_Param_GROUP_END:
    return {nullptr, 0};
  default:
    abort();
  }
}
static NSArray *snapshot(NSArray *seed, PF_InData *in) {
  NSMutableArray *a = [NSMutableArray array];
  for (NSDictionary *s in seed) {
    int slot = [s[@"slot"] intValue];
    auto &p = g_defs[slot];
    NSMutableDictionary *d = [s mutableCopy];
    d[@"type"] = @(p.param_type);
    d[@"change_flags"] = @(p.uu.change_flags);
    d[@"ui_flags"] = @(p.ui_flags);
    d[@"flags"] = @(p.flags);
    d[@"name_bytes"] = bytes(p.name, 32);
    if (p.param_type != PF_Param_ARBITRARY_DATA) {
      auto v = scalar(p);
      d[@"value"] = @{@"bytes" : bytes(v.first, v.second)};
    }
    if (p.param_type == PF_Param_ARBITRARY_DATA) {
      unsigned char flat[325]{};
      PF_ArbParamsExtra e{};
      e.which_function = PF_Arbitrary_FLATTEN_FUNC;
      e.u.flatten_func_params.arbH = p.u.arb_d.value;
      e.u.flatten_func_params.buf_sizeLu = 325;
      e.u.flatten_func_params.flat_dataPV = flat;
      assert(RampArbitraryCallback(in, &e) == 0);
      d[@"value"] = @{@"flat_bytes" : bytes(flat, 325)};
    }
    [a addObject:d];
  }
  return a;
}
int main(int argc, char **argv) {
  @autoreleasepool {
    assert(argc == 2);
    NSDictionary *request = [NSJSONSerialization
        JSONObjectWithData:[NSData dataWithContentsOfFile:@(argv[1])]
                   options:0
                     error:nil];
    assert(request);
    utils.PF_UpdateParamUI = update_ui;
    app.PF_AppGetColor = color;
    app.PF_InvalidateRect = invalidate;
    app.PF_AppColorPickerDialog = pick_color;
    custom.PF_GetDrawingReference = drawref;
    draw.GetSupplier = supplier;
    draw.GetSurface = surface;
    sup.NewPen = pen;
    sup.NewBrush = brush;
    sup.NewDefaultFont = font;
    sup.NewPath = path;
    sup.ReleaseObject = release;
    surf.PaintRect = paint;
    surf.StrokePath = stroke;
    surf.SetAntiAliasPolicy = aa;
    surf.DrawString = text;
    paths.MoveTo = move;
    paths.LineTo = line;
    paths.AddRect = rect;
    g_basic.AcquireSuite = ui_acquire;
    PF_InData in{};
    in.pica_basicP = &g_basic;
    in.effect_ref = (PF_ProgPtr)1;
    in.current_time = [request[@"current_time"] intValue];
    in.time_scale = [request[@"time_scale"] intValue];
    NSArray *seed = request[@"initial_parameters"];
    PF_ParamDef *params[OLMKIRAKIRA_NUM_PARAMS]{};
    for (int i = 0; i < OLMKIRAKIRA_NUM_PARAMS; i++)
      params[i] = &g_defs[i];
    for (NSDictionary *s in seed) {
      auto &p = g_defs [[s [@"slot"] intValue]];
      p.param_type = (PF_ParamType)[s[@"type"] intValue];
      p.uu.change_flags = [s[@"change_flags"] intValue];
      p.flags = [s[@"flags"] intValue];
      NSDictionary *metadata =
          request[@"setup_parameters"][[s[@"slot"] intValue] - 1];
      assert([metadata[@"slot"] intValue] == [s[@"slot"] intValue]);
      p.ui_width = [metadata[@"ui_width"] intValue];
      p.ui_height = [metadata[@"ui_height"] intValue];
      p.ui_flags = [s[@"ui_flags"] intValue];
      if (p.param_type != PF_Param_ARBITRARY_DATA) {
        auto v = scalar(p);
        NSArray *a = s[@"value"][@"bytes"];
        assert(a.count == v.second);
        for (size_t i = 0; i < v.second; i++)
          ((unsigned char *)v.first)[i] = [a[i] unsignedIntValue];
      }
      for (int i = 0; i < 32; i++)
        p.name[i] = [s[@"name_bytes"][i] intValue];
      if (p.param_type == PF_Param_ARBITRARY_DATA) {
        unsigned char flat[325];
        for (int i = 0; i < 325; i++)
          flat[i] = [s[@"value"][@"flat_bytes"][i] intValue];
        PF_ArbParamsExtra e{};
        e.which_function = PF_Arbitrary_UNFLATTEN_FUNC;
        e.u.unflatten_func_params.flat_dataPV = flat;
        e.u.unflatten_func_params.buf_sizeLu = 325;
        e.u.unflatten_func_params.arbPH = &p.u.arb_d.value;
        assert(RampArbitraryCallback(&in, &e) == 0);
      }
    }
    if (request[@"rng"])
      ramp_ui_rng = [request[@"rng"] unsignedIntValue];
    for (NSArray *assignments in request[@"updates"]) {
      for (NSString *assignment in assignments) {
        int slot, value;
        assert(sscanf(assignment.UTF8String, "p@%d=%d", &slot, &value) == 2);
        g_defs[slot].u.bd.value = value;
      }
      calls = [NSMutableArray array];
      NSArray *before = snapshot(seed, &in);
      PF_OutData out{};
      PF_Err err = EffectMain(PF_Cmd_UPDATE_PARAMS_UI, &in, &out, params,
                              nullptr, nullptr);
      NSDictionary *row = @{
        @"before" : before,
        @"after" : snapshot(seed, &in),
        @"calls" : calls,
        @"selector" : @14,
        @"selector_error" : @(err)
      };
      NSData *data =
          [NSJSONSerialization dataWithJSONObject:row
                                          options:NSJSONWritingSortedKeys
                                            error:nil];
      fwrite(data.bytes, 1, data.length, stdout);
      puts("");
      assert(err == 0);
    }
    std::map<int, PF_Context> contexts;
    std::map<int, PF_ContextPtr> context_handles;
    std::map<int, std::array<A_intptr_t, 4>> continuation;
    for (NSDictionary *i in request[@"events"]) {
      input = i;
      calls = [NSMutableArray array];
      PF_EventExtra e{};
      e.e_type = (PF_EventType)[i[@"event"] intValue];
      e.effect_win.area = (PF_EffectArea)[i[@"area"] intValue];
      e.effect_win.index = [i[@"slot"] intValue];
      NSArray *f = i[@"frame"];
      e.effect_win.current_frame = {
          [f[0] intValue], [f[1] intValue], [f[2] intValue], [f[3] intValue]};
      const int context_id = [i[@"context"] intValue];
      auto &context = contexts[context_id];
      context.magic = PF_CONTEXT_MAGIC;
      context.w_type = (PF_WindowType)[i[@"window_type"] intValue];
      context_handles[context_id] = &context;
      e.contextH = &context_handles[context_id];
      e.u.do_click.screen_point = {[i[@"x"] intValue], [i[@"y"] intValue]};
      e.u.do_click.num_clicks = [i[@"clicks"] intValue];
      e.u.do_click.last_time = [i[@"last"] boolValue];
      if (e.e_type == PF_Event_DRAG)
        memcpy(e.u.do_click.continue_refcon, continuation[context_id].data(),
               sizeof(e.u.do_click.continue_refcon));
      if (e.e_type == PF_Event_ADJUST_CURSOR)
        e.u.adjust_cursor.screen_point = {[i[@"x"] intValue],
                                          [i[@"y"] intValue]};
      NSArray *before = snapshot(seed, &in);
      uint32_t rng_before = ramp_ui_rng;
      PF_OutData out{};
      PF_Err err = EffectMain(PF_Cmd_EVENT, &in, &out, params, nullptr, &e);
      if (e.e_type == PF_Event_DO_CLICK || e.e_type == PF_Event_DRAG)
        memcpy(continuation[context_id].data(), e.u.do_click.continue_refcon,
               sizeof(e.u.do_click.continue_refcon));
      NSDictionary *row = @{
        @"before" : before,
        @"after" : snapshot(seed, &in),
        @"calls" : calls,
        @"input" : i,
        @"selector" : @15,
        @"selector_error" : @(err),
        @"event_out_flags" : @(e.evt_out_flags),
        @"send_drag" : @(e.u.do_click.send_drag),
        @"rng_before" : @(rng_before),
        @"rng_after" : @(ramp_ui_rng)
      };
      NSData *data =
          [NSJSONSerialization dataWithJSONObject:row
                                          options:NSJSONWritingSortedKeys
                                            error:nil];
      fwrite(data.bytes, 1, data.length, stdout);
      puts("");
      assert(err == 0);
    }
    PF_OutData out{};
    assert(EffectMain(PF_Cmd_SEQUENCE_SETDOWN, &in, &out, params, nullptr,
                      nullptr) == 0);
    assert(EffectMain(PF_Cmd_GLOBAL_SETDOWN, &in, &out, params, nullptr,
                      nullptr) == 0);
    for (auto &p : g_defs)
      if (p.param_type == PF_Param_ARBITRARY_DATA)
        host_dispose_handle(p.u.arb_d.value);
    for (auto &r : refs)
      assert(r.second == 0);
    assert(g_sizes.empty());
  }
}
