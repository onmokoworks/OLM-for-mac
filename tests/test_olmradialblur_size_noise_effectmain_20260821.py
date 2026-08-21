import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_size_noise_classic_effectmain_all_depths_and_families() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_size_noise_effectmain_") as name:
        temp = Path(name)
        cpp, exe = temp / "probe.cpp", temp / "probe"
        cpp.write_text(f'''#include <cstdlib>
#include <new>
static bool fail_alloc=false;static size_t alloc_ordinal=0,fail_ordinal=0;
void* operator new(size_t n){{if(fail_alloc&&++alloc_ordinal==fail_ordinal)throw std::bad_alloc();if(void*p=std::malloc(n?n:1))return p;throw std::bad_alloc();}}
void* operator new[](size_t n){{return ::operator new(n);}}void operator delete(void*p)noexcept{{std::free(p);}}void operator delete[](void*p)noexcept{{std::free(p);}}
void operator delete(void*p,size_t)noexcept{{std::free(p);}}void operator delete[](void*p,size_t)noexcept{{std::free(p);}}
#include "{source}"
#include <cstring>
#include <vector>
static PF_PixelFormat g_format=PF_PixelFormat_INVALID;
static PF_Err get_format(const PF_EffectWorld*,PF_PixelFormat*f){{*f=g_format;return PF_Err_NONE;}}
static PF_WorldSuite2 world_suite{{nullptr,nullptr,get_format}};
static SPErr acquire(const char*,int32,const void**s){{*s=&world_suite;return kSPNoError;}}
static SPErr release(const char*,int32){{return kSPNoError;}}
static SPBasicSuite basic{{acquire,release}};
static PF_ParamDef smart_params[OLMRADIALBLUR_NUM_PARAMS]={{}};static PF_EffectWorld*smart_in=nullptr,*smart_out=nullptr;
static int pixel_out=0,pixel_in=0,param_out_count=0,param_in_count=0;
static PF_Err checkout_param(PF_ProgPtr,A_long i,A_long,A_long,A_u_long,PF_ParamDef*p){{*p=smart_params[i];++param_out_count;return PF_Err_NONE;}}
static PF_Err checkin_param(PF_ProgPtr,PF_ParamDef*){{++param_in_count;return PF_Err_NONE;}}
static PF_Err pre_layer(PF_ProgPtr,PF_ParamIndex,A_long,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult*r){{AEFX_CLR_STRUCT(*r);r->result_rect={{0,0,17,11}};r->max_result_rect=r->result_rect;r->ref_width=17;r->ref_height=11;return PF_Err_NONE;}}
static PF_Err checkout_pixels(PF_ProgPtr,A_long,PF_EffectWorld**w){{++pixel_out;*w=smart_in;return PF_Err_NONE;}}
static PF_Err checkin_pixels(PF_ProgPtr,A_long){{++pixel_in;return PF_Err_NONE;}}
static PF_Err checkout_output(PF_ProgPtr,PF_EffectWorld**w){{*w=smart_out;return PF_Err_NONE;}}
template<class P> int one(short depth,int family){{constexpr int W=17,H=11;
 const int IRB=(W+3)*(int)sizeof(P),ORB=(W+5)*(int)sizeof(P);
 std::vector<unsigned char>a((size_t)IRB*H,0xa5),b((size_t)ORB*H,0x5a);auto before=a,out_before=b;
 PF_ParamDef defs[OLMRADIALBLUR_NUM_PARAMS]={{}};PF_ParamDef*params[OLMRADIALBLUR_NUM_PARAMS]={{}};
 for(int i=0;i<OLMRADIALBLUR_NUM_PARAMS;++i)params[i]=&defs[i];
 auto&iw=defs[OLMRADIALBLUR_INPUT].u.ld;iw.data=(PF_PixelPtr)a.data();iw.rowbytes=IRB;iw.width=W;iw.height=H;
 PF_EffectWorld ow{{}};ow.data=(PF_PixelPtr)b.data();ow.rowbytes=ORB;ow.width=W;ow.height=H;
 for(int y=0;y<H;++y)for(int x=0;x<W;++x){{P*p=(P*)(a.data()+(size_t)y*IRB)+x;std::memset(p,0,sizeof(P));
  float v=(float)((x*13+y*7)%23)/23.0f;bool on=(x<16)&&((x==2&&y==2)||(x>=6&&x<=8&&y>=3&&y<=5)||(x>=11&&x<=14&&y>=7));
  if constexpr(std::is_same<P,PF_Pixel8>::value){{p->alpha=on?255:0;p->red=(A_u_char)(v*255);}}
  else if constexpr(std::is_same<P,PF_Pixel16>::value){{p->alpha=on?32768:0;p->red=(A_u_short)(v*32768);}}
  else{{p->alpha=on?1.0f:0.0f;p->red=v;}}
 }}before=a;
 defs[OLMRADIALBLUR_BLUR_TYPE].u.pd.value=family;defs[OLMRADIALBLUR_CENTER].u.td.x_value=(W/2)*65536;defs[OLMRADIALBLUR_CENTER].u.td.y_value=(H/2)*65536;
 defs[OLMRADIALBLUR_OUTER_STRENGTH].u.sd.value=4;defs[OLMRADIALBLUR_OUTER_OFFSET_MODE].u.pd.value=1;defs[OLMRADIALBLUR_INNER_OFFSET_MODE].u.pd.value=1;
 defs[OLMRADIALBLUR_REPEAT_BORDER].u.bd.value=TRUE;defs[OLMRADIALBLUR_RATIO].u.fs_d.value=1;defs[OLMRADIALBLUR_QUALITY].u.fs_d.value=5;
 defs[OLMRADIALBLUR_BRIGHTNESS_GAIN].u.fs_d.value=1;defs[OLMRADIALBLUR_SIZE_VARIATION].u.fs_d.value=25;defs[OLMRADIALBLUR_NOISE_VARIATION].u.fs_d.value=25;
 defs[OLMRADIALBLUR_NOISE_TYPE].u.pd.value=1;defs[OLMRADIALBLUR_SEED].u.sd.value=1;defs[OLMRADIALBLUR_THICKNESS].u.fs_d.value=10;
 PF_InData in{{}};in.pica_basicP=&basic;PF_OutData out{{}};PF_Err e=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);if(e)return 1;
 if(a!=before)return 2;bool changed=false;for(int y=0;y<H;++y){{for(int x=0;x<W*(int)sizeof(P);++x)changed|=b[(size_t)y*ORB+x]!=0x5a;
  for(int x=W*(int)sizeof(P);x<ORB;++x)if(b[(size_t)y*ORB+x]!=0x5a)return 3;}}if(!changed)return 4;
 b=out_before;defs[OLMRADIALBLUR_SIZE_VARIATION].u.fs_d.value=100;defs[OLMRADIALBLUR_NOISE_VARIATION].u.fs_d.value=100;defs[OLMRADIALBLUR_NOISE_TYPE].u.pd.value=2;
 e=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);if(e)return 5;if(a!=before)return 6;return 0;
}}
template<class P> int smart_one(short depth,int family){{constexpr int W=17,H=11;
 const int IRB=(W+3)*(int)sizeof(P),ORB=(W+5)*(int)sizeof(P);std::vector<unsigned char>a((size_t)IRB*H,0xa5),b((size_t)ORB*H,0x5a);auto before=a;
 PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)a.data();iw.rowbytes=IRB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)b.data();ow.rowbytes=ORB;ow.width=W;ow.height=H;
 for(int y=0;y<H;++y)for(int x=0;x<W;++x){{P*p=(P*)(a.data()+(size_t)y*IRB)+x;std::memset(p,0,sizeof(P));float v=(float)((x*13+y*7)%23)/23.0f;
  bool on=(x<16)&&((x==2&&y==2)||(x>=6&&x<=8&&y>=3&&y<=5)||(x>=11&&x<=14&&y>=7));
  if constexpr(std::is_same<P,PF_Pixel8>::value){{p->alpha=on?255:0;p->red=(A_u_char)(v*255);}}else if constexpr(std::is_same<P,PF_Pixel16>::value){{p->alpha=on?32768:0;p->red=(A_u_short)(v*32768);}}else{{p->alpha=on?1.0f:0.0f;p->red=v;}}}}
 before=a;std::memset(smart_params,0,sizeof(smart_params));smart_params[OLMRADIALBLUR_BLUR_TYPE].u.pd.value=family;
 smart_params[OLMRADIALBLUR_CENTER].u.td.x_value=(W/2)*65536;smart_params[OLMRADIALBLUR_CENTER].u.td.y_value=(H/2)*65536;
 smart_params[OLMRADIALBLUR_OUTER_STRENGTH].u.sd.value=4;smart_params[OLMRADIALBLUR_OUTER_OFFSET_MODE].u.pd.value=1;smart_params[OLMRADIALBLUR_INNER_OFFSET_MODE].u.pd.value=1;
 smart_params[OLMRADIALBLUR_REPEAT_BORDER].u.bd.value=TRUE;smart_params[OLMRADIALBLUR_RATIO].u.fs_d.value=1;smart_params[OLMRADIALBLUR_QUALITY].u.fs_d.value=5;
 smart_params[OLMRADIALBLUR_BRIGHTNESS_GAIN].u.fs_d.value=1;smart_params[OLMRADIALBLUR_SIZE_VARIATION].u.fs_d.value=25;smart_params[OLMRADIALBLUR_NOISE_VARIATION].u.fs_d.value=25;
 smart_params[OLMRADIALBLUR_NOISE_TYPE].u.pd.value=1;smart_params[OLMRADIALBLUR_SEED].u.sd.value=1;smart_params[OLMRADIALBLUR_THICKNESS].u.fs_d.value=10;
 smart_in=&iw;smart_out=&ow;pixel_out=pixel_in=param_out_count=param_in_count=0;PF_InData in{{}};in.width=W;in.height=H;in.pica_basicP=&basic;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;PF_OutData out{{}};
 PF_PreRenderInput pri{{}};PF_PreRenderOutput pro{{}};PF_PreRenderCallbacks prc{{pre_layer,nullptr}};PF_PreRenderExtra pre{{&pri,&pro,&prc}};
 if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE||!pro.pre_render_data)return 1;
 PF_SmartRenderInput sri{{}};sri.bitdepth=depth;sri.pre_render_data=pro.pre_render_data;PF_SmartRenderCallbacks src{{checkout_pixels,checkin_pixels,checkout_output}};PF_SmartRenderExtra sre{{&sri,&src}};
 PF_Err e=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&sre);if(e)return 2;
	 if(pixel_out!=1||pixel_in!=1||param_out_count!=32||param_in_count!=32||a!=before)return 3;bool changed=false;
	 for(int y=0;y<H;++y){{for(int x=0;x<W*(int)sizeof(P);++x)changed|=b[(size_t)y*ORB+x]!=0x5a;for(int x=W*(int)sizeof(P);x<ORB;++x)if(b[(size_t)y*ORB+x]!=0x5a)return 4;}}if(!changed)return 5;
	 if(depth==32&&family==1){{bool saw_oom=false,saw_success=false;for(size_t ordinal=1;ordinal<=128;++ordinal){{std::fill(b.begin(),b.end(),0x5a);const auto untouched=b;
	   fail_ordinal=ordinal;alloc_ordinal=0;fail_alloc=true;PF_Err injected=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&sre);fail_alloc=false;
	   if(injected==PF_Err_OUT_OF_MEMORY){{saw_oom=true;if(b!=untouched)return 6;}}else if(injected==PF_Err_NONE){{saw_success=true;break;}}else return 7;}}
	   if(!saw_oom||!saw_success)return 8;}}
	 if(pro.delete_pre_render_data_func)pro.delete_pre_render_data_func(pro.pre_render_data);return 0;
}}
int main(){{for(int family=1;family<=2;++family){{g_format=PF_PixelFormat_ARGB32;if(one<PF_Pixel8>(8,family))return 10+family;
 if(smart_one<PF_Pixel8>(8,family))return 40+family;g_format=PF_PixelFormat_ARGB64;if(one<PF_Pixel16>(16,family))return 20+family;
 if(smart_one<PF_Pixel16>(16,family))return 50+family;g_format=PF_PixelFormat_ARGB128;if(one<PF_PixelFloat>(32,family))return 30+family;
 if(smart_one<PF_PixelFloat>(32,family))return 60+family;}}return 0;}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        build = subprocess.run([
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-ffunction-sections", "-fdata-sections", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
            "-I", str(ROOT / "Resources"), str(cpp),
            str(ROOT / "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
            "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe),
        ], cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, f"EffectMain probe returned {run.returncode}: {run.stderr}"
