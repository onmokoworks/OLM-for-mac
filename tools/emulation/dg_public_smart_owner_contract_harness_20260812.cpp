#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <vector>

namespace {
constexpr int W = 17, H = 11, PAD = 16;
PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
std::array<PF_ParamDef, DG_NUM_PARAMS> g_params{};
int g_pre = 0, g_pixels = 0, g_output_checkout = 0, g_layer_checkin = 0;
int g_param_checkout = 0, g_param_checkin = 0, g_fail_param = 0;
bool g_fail_input_checkout = false, g_fail_output_checkout = false, g_fail_layer_checkin = false;
bool g_throw_output_checkout = false, g_throw_param_checkout = false;
bool g_throw_param_checkin = false;

PF_Err pre_checkout(PF_ProgPtr, A_long index, A_long checkout_id, PF_RenderRequest *,
	A_long, A_long, A_long, PF_CheckoutResult *result) {
	++g_pre;
	if (index != DG_INPUT || checkout_id != DG_INPUT || !result) return PF_Err_BAD_CALLBACK_PARAM;
	result->result_rect = {0, 0, W, H};
	result->max_result_rect = {0, 0, W, H};
	return PF_Err_NONE;
}
PF_Err checkout_pixels(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
	++g_pixels;
	if (g_fail_input_checkout) return PF_Err_BAD_CALLBACK_PARAM;
	if (index != DG_INPUT || !world) return PF_Err_BAD_CALLBACK_PARAM;
	*world = g_input;
	return PF_Err_NONE;
}
PF_Err checkin_pixels(PF_ProgPtr, A_long index) {
	++g_layer_checkin;
	if (index != DG_INPUT || g_fail_layer_checkin) return PF_Err_BAD_CALLBACK_PARAM;
	return PF_Err_NONE;
}
PF_Err checkout_output(PF_ProgPtr, PF_EffectWorld **world) {
	++g_output_checkout;
	if (g_throw_output_checkout) throw std::runtime_error("output checkout");
	if (g_fail_output_checkout || !world) return PF_Err_BAD_CALLBACK_PARAM;
	*world = g_output;
	return PF_Err_NONE;
}
PF_Err checkout_param(A_long index, PF_ParamDef *param) {
	++g_param_checkout;
	if (g_throw_param_checkout && index == 5) throw std::runtime_error("param checkout");
	if (index == g_fail_param || index <= 0 || index >= DG_NUM_PARAMS || !param) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	*param = g_params[(size_t)index];
	return PF_Err_NONE;
}
void checkin_param(PF_ParamDef *) {
	++g_param_checkin;
	if (g_throw_param_checkin && g_param_checkin == 5) throw std::runtime_error("param checkin");
}

void reset_callbacks() {
	g_pre = g_pixels = g_output_checkout = g_layer_checkin = 0;
	g_param_checkout = g_param_checkin = 0;
	g_fail_param = 0;
	g_fail_input_checkout = g_fail_output_checkout = g_fail_layer_checkin = false;
	g_throw_output_checkout = g_throw_param_checkout = false;
	g_throw_param_checkin = false;
	dg_harness_fail_color = false;
}
void set_params(A_long interpolation = INTERP_LINEAR, A_long blur = BLUR_MODE_NO_SCALE,
	bool background = false) {
	g_params = {};
	g_params[DG_INVERT].u.bd.value = 1;
	g_params[DG_IN_OUT].u.pd.value = IN_OUT_INSIDE;
	g_params[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	g_params[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	g_params[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	g_params[DG_USE_BG_COLOR].u.bd.value = background;
	g_params[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	g_params[DG_BG_COLOR].u.cd.value = {255, 16, 160, 48};
	g_params[DG_INTERP_MODE].u.pd.value = interpolation;
	g_params[DG_POWER].u.fs_d.value = 2.25;
	g_params[DG_BLUR_MODE].u.pd.value = blur;
	g_params[DG_BLUR_SIZE].u.sd.value = 1;
}
template <class Pixel> void fill_source(std::vector<std::uint8_t> &bytes, int rowbytes) {
	for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) {
		Pixel *p = reinterpret_cast<Pixel *>(bytes.data() + (size_t)y * rowbytes) + x;
		const bool transparent = x >= 4 && x < 13 && y >= 2 && y < 9;
		if constexpr (sizeof(Pixel) == sizeof(PF_Pixel8)) {
			*p = {(std::uint8_t)(transparent ? 0 : 255), (std::uint8_t)((x*613+y*1231)%256),
				(std::uint8_t)((x*997+y*211)%256), (std::uint8_t)((x*1499+y*307)%256)};
		} else if constexpr (sizeof(Pixel) == sizeof(PF_Pixel16)) {
			*p = {(std::uint16_t)(transparent ? 0 : 32768), (std::uint16_t)((x*613+y*1231)%32769),
				(std::uint16_t)((x*997+y*211)%32769), (std::uint16_t)((x*1499+y*307)%32769)};
		} else {
			*p = transparent ? PF_PixelFloat{0.0f, 0.0f, 0.0f, 0.0f}
				: PF_PixelFloat{1.0f, ((x*613+y*1231)%256)/255.0f,
					((x*997+y*211)%256)/255.0f, ((x*1499+y*307)%256)/255.0f};
		}
	}
}
bool rects_exact(const PF_PreRenderOutput &output) {
	return output.result_rect.left == 0 && output.result_rect.top == 0 &&
		output.result_rect.right == W && output.result_rect.bottom == H &&
		output.max_result_rect.left == 0 && output.max_result_rect.top == 0 &&
		output.max_result_rect.right == W && output.max_result_rect.bottom == H;
}
bool world_header_exact(const PF_EffectWorld &a, const PF_EffectWorld &b) {
	return a.data==b.data&&a.width==b.width&&a.height==b.height&&a.rowbytes==b.rowbytes&&
		a.bitdepth==b.bitdepth&&a.extent_hint.left==b.extent_hint.left&&
		a.extent_hint.top==b.extent_hint.top&&a.extent_hint.right==b.extent_hint.right&&
		a.extent_hint.bottom==b.extent_hint.bottom;
}
template <class Pixel> int positive(short depth, A_long interpolation = INTERP_LINEAR,
	A_long blur = BLUR_MODE_NO_SCALE, bool background = false) {
	const int rowbytes = W * (int)sizeof(Pixel) + PAD;
	std::vector<std::uint8_t> input((size_t)rowbytes * H, 0xa5), output(input.size(), 0x5a), direct(input.size(), 0x5a);
	fill_source<Pixel>(input, rowbytes); const auto before = input;
	PF_EffectWorld iw{input.data(), W, H, rowbytes, depth, {0,0,W,H}};
	PF_EffectWorld ow{output.data(), W, H, rowbytes, depth, {0,0,W,H}};
	PF_EffectWorld dw{direct.data(), W, H, rowbytes, depth, {0,0,W,H}};
	g_input=&iw; g_output=&ow; set_params(interpolation, blur, background); reset_callbacks();
	dg_harness_checkout_param=checkout_param; dg_harness_checkin_param=checkin_param;
	PF_InData in{}; in.downsample_x={1,1}; in.downsample_y={1,1}; PF_OutData out{};
	PF_PreRenderInput pri{}; pri.bitdepth=depth; PF_PreRenderOutput pro{};
	PF_PreRenderCallbacks prc{pre_checkout}; PF_PreRenderExtra pre{&pri,&pro,&prc};
	if (EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre) != PF_Err_NONE || !rects_exact(pro)) return 10+depth;
	PF_SmartRenderInput sri{depth}; PF_SmartRenderCallbacks src{checkout_pixels,checkin_pixels,checkout_output};
	PF_SmartRenderExtra smart{&sri,&src};
	if (EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&smart) != PF_Err_NONE) return 20+depth;
	PF_ParamDef *params[DG_NUM_PARAMS]; g_params[DG_INPUT].u.ld=iw;
	for(int i=0;i<DG_NUM_PARAMS;++i)params[i]=&g_params[(size_t)i];
	if(RenderBits<Pixel>(&in,params,&iw,&dw,true)!=PF_Err_NONE) return 30+depth;
	if(input!=before || output!=direct || g_pre!=1 || g_pixels!=1 || g_output_checkout!=1 ||
		g_layer_checkin!=1 || g_param_checkout!=12 || g_param_checkin!=12) return 40+depth;
	for(int y=0;y<H;++y)for(int offset=W*(int)sizeof(Pixel);offset<rowbytes;++offset)
		if(output[(size_t)y*rowbytes+offset]!=0x5a)return 50+depth;
	return 0;
}
int negative_pf32(int which) {
	constexpr int rowbytes=W*(int)sizeof(PF_PixelFloat)+PAD;
	std::vector<std::uint8_t> input((size_t)rowbytes*H,0xa5), output(input.size(),0x5a);
	fill_source<PF_PixelFloat>(input,rowbytes); const auto before=input, output_before=output;
	PF_EffectWorld iw{input.data(),W,H,rowbytes,32,{0,0,W,H}}, ow{output.data(),W,H,rowbytes,32,{0,0,W,H}};
	g_input=&iw;g_output=&ow;set_params();reset_callbacks();
	PF_InData in{};in.downsample_x={1,1};in.downsample_y={1,1};PF_OutData out{};
	if(which==1){iw.width=W-1;iw.extent_hint.right=W-1;}
	if(which==2){set_params(INTERP_LINEAR,BLUR_MODE_BILATERAL,false);g_params[DG_BLUR_SIZE].u.sd.value=2;}
	if(which==3)reinterpret_cast<PF_PixelFloat*>(input.data())[0].alpha=0.0f;
	if(which==4)g_params[DG_POWER].u.fs_d.value=2.0;
	if(which==5)iw.bitdepth=16;
	if(which==6)ow.bitdepth=16;
	if(which==7)iw.rowbytes=W*(int)sizeof(PF_PixelFloat)-1;
	if(which==8)ow.rowbytes=W*(int)sizeof(PF_PixelFloat)-1;
	if(which==9)ow.width=W-1;
	if(which==10)iw.data=nullptr;
	if(which==11)g_fail_output_checkout=true;
	if(which==12)g_fail_param=5;
	if(which==13)g_throw_output_checkout=true;
	if(which==14)g_throw_param_checkout=true;
	if(which==15)g_throw_param_checkin=true;
	if(which==16)g_fail_layer_checkin=true;
	if(which==17)g_fail_input_checkout=true;
	if(which==18)iw.extent_hint.left=1;
	if(which==19)in.output_origin_x=1;
	if(which==20)reinterpret_cast<PF_PixelFloat*>(input.data()+(size_t)2*rowbytes)[4].alpha=-0.0f;
	if(which==21)dg_harness_fail_color=true;
	dg_harness_checkout_param=checkout_param;dg_harness_checkin_param=checkin_param;
	PF_SmartRenderInput sri{32};PF_SmartRenderCallbacks src{checkout_pixels,checkin_pixels,checkout_output};PF_SmartRenderExtra smart{&sri,&src};
	const PF_Err expected=(which==13||which==14||which==15)?PF_Err_INTERNAL_STRUCT_DAMAGED:PF_Err_BAD_CALLBACK_PARAM;
	if(EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&smart)!=expected)return 100+which;
	const int successful_params=(which==11||which==13||which==17)?0:((which==12||which==14)?4:12);
	const int expected_layer_checkin=which==17?0:1;
	const int expected_output_checkout=which==17?0:1;
	const bool output_may_change=which==15||which==16;
	if(g_pixels!=1 || g_layer_checkin!=expected_layer_checkin || g_output_checkout!=expected_output_checkout ||
		g_param_checkin!=successful_params || input!=before && which!=3 && which!=20 ||
		(!output_may_change && output!=output_before))return 120+which;
	return 0;
}
int negative_pf32_power_unlisted(int which) {
	constexpr int rowbytes=W*(int)sizeof(PF_PixelFloat)+PAD;
	std::vector<std::uint8_t> input((size_t)rowbytes*H,0xa5), output(input.size(),0x5a);
	fill_source<PF_PixelFloat>(input,rowbytes); const auto output_before=output;
	PF_EffectWorld iw{input.data(),W,H,rowbytes,32,{0,0,W,H}};
	PF_EffectWorld ow{output.data(),W,H,rowbytes,32,{0,0,W,H}};
	g_input=&iw;g_output=&ow;set_params(INTERP_POWER,BLUR_MODE_NO_SCALE,false);reset_callbacks();
	dg_harness_checkout_param=checkout_param;dg_harness_checkin_param=checkin_param;
	PF_InData in{};in.downsample_x={1,1};in.downsample_y={1,1};PF_OutData out{};
	if(which==1)reinterpret_cast<PF_PixelFloat*>(input.data())[0].alpha=0.0f;
	if(which==2)g_params[DG_POWER].u.fs_d.value=2.0;
	if(which==3)g_params[DG_BLUR_SIZE].u.sd.value=2;
	if(which==4){iw.width=W-1;iw.extent_hint.right=W-1;}
	if(which==5)in.downsample_x={1,2};
	if(which==6)in.output_origin_x=1;
	if(which==7)reinterpret_cast<PF_PixelFloat*>(input.data())[0].red=0.5f;
	const auto before=input;
	const PF_EffectWorld iw_before=iw,ow_before=ow;
	PF_SmartRenderInput sri{32};PF_SmartRenderCallbacks src{checkout_pixels,checkin_pixels,checkout_output};
	PF_SmartRenderExtra smart{&sri,&src};
	if(EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&smart)!=PF_Err_BAD_CALLBACK_PARAM)return 300+which;
	if(g_pixels!=1||g_output_checkout!=1||g_layer_checkin!=1||
		g_param_checkout!=12||g_param_checkin!=12||input!=before||output!=output_before||
		!world_header_exact(iw,iw_before)||!world_header_exact(ow,ow_before))return 320+which;
	for(int y=0;y<H;++y)for(int offset=W*(int)sizeof(PF_PixelFloat);offset<rowbytes;++offset)
		if(output[(size_t)y*rowbytes+offset]!=0x5a)return 340+which;
	return 0;
}
int classic_guards(int which) {
	constexpr int rowbytes=W*(int)sizeof(PF_PixelFloat)+PAD;
	std::vector<std::uint8_t> input((size_t)rowbytes*H,0xa5), output(input.size(),0x5a);
	fill_source<PF_PixelFloat>(input,rowbytes);PF_EffectWorld iw{input.data(),W,H,rowbytes,32,{0,0,W,H}},ow{output.data(),W,H,rowbytes,16,{0,0,W,H}};
	set_params();g_params[DG_INPUT].u.ld=iw;PF_ParamDef*p[DG_NUM_PARAMS];for(int i=0;i<DG_NUM_PARAMS;i++)p[i]=&g_params[(size_t)i];
	PF_InData in{};in.downsample_x={1,1};in.downsample_y={1,1};PF_OutData out{};
	if(which==1)ow.bitdepth=16;
	if(which==2)ow.rowbytes=W*(int)sizeof(PF_PixelFloat)-1;
	if(which==3)p[DG_POWER]=nullptr;
	if(which==4)in.output_origin_x=1;
	if(EffectMain(PF_Cmd_RENDER,&in,&out,p,&ow,nullptr)!=PF_Err_BAD_CALLBACK_PARAM)return 200+which;
	return 0;
}
}
int main(){
	if(int e=positive<PF_Pixel8>(8))return e;if(int e=positive<PF_Pixel16>(16))return e;if(int e=positive<PF_PixelFloat>(32))return e;
	for(A_long interpolation: {INTERP_CONSTANT,INTERP_LINEAR,INTERP_SPHERE})for(bool background: {false,true})
		if(int e=positive<PF_PixelFloat>(32,interpolation,BLUR_MODE_BILATERAL,background))return e;
	for(A_long blur: {BLUR_MODE_NO_SCALE,BLUR_MODE_SCALE,BLUR_MODE_MEDIAN,BLUR_MODE_BILATERAL})for(bool background: {false,true})
		if(int e=positive<PF_PixelFloat>(32,INTERP_POWER,blur,background))return e;
	for(int i=1;i<=7;i++)if(int e=negative_pf32_power_unlisted(i))return e;
	for(int i=1;i<=21;i++)if(int e=negative_pf32(i))return e;for(int i=1;i<=4;i++)if(int e=classic_guards(i))return e;
	std::puts("PASS_OLMDISTANCEGRADATION_PUBLIC_SMART_OWNER_CONTRACT positive=17 mode5_positive=8 power_positive=8 power_negative=7 negative=21 classic_guards=4");return 0;
}
