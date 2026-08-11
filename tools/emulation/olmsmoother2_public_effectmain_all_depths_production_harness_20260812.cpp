#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static constexpr int W=17,H=11;
struct Tuple{int depth,version,gamma,key,count,kind,s,r,e;double value;bool premul;};
static const Tuple T[6]={
 {8,1,GAMMA_NONE,0,1,0,100,2,0,1.0,false},
 {8,2,GAMMA_COLORS_ONLY,2,5,2,50,50,50,2.4,true},
 {16,2,GAMMA_ALL_COLORS,0,1,0,50,50,50,2.4,false},
 {16,2,GAMMA_COLORS_ONLY,1,5,1,100,2,0,1.0,true},
 {32,1,GAMMA_NONE,0,1,0,50,50,50,1.0,true},
 {32,2,GAMMA_COLORS_ONLY,1,1,0,100,2,0,2.4,false}};
struct RGBA{unsigned char r,g,b,a;};
static RGBA logical(int x,int y){unsigned u=(unsigned)(x+1)*0x9e3779b9u^(unsigned)(y+3)*0x85ebca6bu;u^=u>>16;u*=0x7feb352du;u^=u>>15;static const unsigned char a[]={0,1,64,128,192,255};if(x==0&&y==0)return{1,1,1,128};if(x==1&&y==0)return{255,0,0,192};return{(unsigned char)u,(unsigned char)(u>>8),(unsigned char)(u>>16),a[(x+3*y)%6]};}
template<class P>static P native_pixel(RGBA q,bool premul);
template<>PF_Pixel8 native_pixel(RGBA q,bool premul){auto c=[&](unsigned v){return(unsigned char)(premul?((v*q.a+127u)/255u):v);};return{q.a,c(q.r),c(q.g),c(q.b)};}
template<>PF_Pixel16 native_pixel(RGBA q,bool premul){auto n=[](unsigned v){return(unsigned)std::lround(v*32768.0/255.0);};unsigned a=n(q.a);auto c=[&](unsigned v){unsigned z=n(v);return(unsigned short)(premul?((z*a+16384u)/32768u):z);};return{(unsigned short)a,c(q.r),c(q.g),c(q.b)};}
template<>PF_PixelFloat native_pixel(RGBA q,bool premul){float a=q.a/255.f;auto c=[&](unsigned v){float z=v/255.f;return premul?z*a:z;};return{a,c(q.r),c(q.g),c(q.b)};}
static PF_EffectWorld *g_in,*g_out;static PF_ParamDef g_params[SM_NUM_PARAMS];static int pre_calls,layer_calls,output_calls,param_calls,checkin_calls;
static PF_Err pre_checkout(PF_ProgPtr,A_long a,A_long b,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*r){pre_calls++;if(a!=SM_INPUT||b!=SM_INPUT)return 90;r->result_rect={1,2,16,10};r->max_result_rect={-1,-2,18,13};return 0;}
static PF_Err layer(PF_ProgPtr,A_long i,PF_EffectWorld**p){layer_calls++;if(i!=SM_INPUT)return 91;*p=g_in;return 0;}
static PF_Err output(PF_ProgPtr,PF_EffectWorld**p){output_calls++;*p=g_out;return 0;}
static PF_Err checkout(A_long i,PF_ParamDef*p){param_calls++;*p=g_params[i];return 0;}static void checkin(PF_ParamDef*){checkin_calls++;}
static bool rects_ok(const PF_PreRenderOutput&p){return p.result_rect.left==1&&p.result_rect.top==2&&p.result_rect.right==16&&p.result_rect.bottom==10&&p.max_result_rect.left==-1&&p.max_result_rect.top==-2&&p.max_result_rect.right==18&&p.max_result_rect.bottom==13;}
static void color(PF_ParamDef&d,RGBA q){d.u.cd.value={q.a,q.r,q.g,q.b};}
template<class P>static int run_case(int ti){const Tuple&t=T[ti];const size_t pad=std::is_same<P,PF_Pixel8>::value?5:(std::is_same<P,PF_Pixel16>::value?7:13),rb=W*sizeof(P)+pad;std::vector<unsigned char>in(rb*H,0x3c),smart(rb*H,0xa5),classic(rb*H,0xa5);for(int y=0;y<H;y++)for(int x=0;x<W;x++){P p=native_pixel<P>(logical(x,y),t.premul);memcpy(in.data()+y*rb+x*sizeof(P),&p,sizeof(P));}auto original=in;PF_EffectWorld iw{},sw{},cw{};iw.data=in.data();iw.width=W;iw.height=H;iw.rowbytes=rb;iw.bitdepth=t.depth;iw.extent_hint={0,0,W,H};sw=iw;sw.data=smart.data();cw=iw;cw.data=classic.data();g_in=&iw;g_out=&sw;memset(g_params,0,sizeof(g_params));g_params[SM_SMOOTHNESS].u.sd.value=t.s;g_params[SM_SMOOTH_RANGE].u.sd.value=t.r;g_params[SM_EXTRA_SMOOTH].u.sd.value=t.e;g_params[SM_VERSION].u.pd.value=t.version;g_params[SM_GAMMA_MODE].u.pd.value=t.gamma;g_params[SM_GAMMA_VALUE].u.fs_d.value=t.value;g_params[SM_NUM_GAMMA_COLORS].u.sd.value=t.count;g_params[SM_ENABLE_KEY].u.bd.value=t.key!=0;g_params[SM_INVERT_KEY].u.bd.value=t.key==2;color(g_params[SM_KEY_COLOR],{1,1,1,255});RGBA n[5]={{255,0,0,255},{1,1,1,255},{0,0,255,255},{0,255,0,255},{255,255,0,255}},re[5]={{255,255,0,255},{0,255,0,255},{1,1,1,255},{255,0,0,255},{0,0,255,255}},du[5]={{255,0,0,255},{1,1,1,255},{255,0,0,255},{1,1,1,255},{0,0,255,255}};RGBA*pal=t.kind==1?re:(t.kind==2?du:n);for(int k=0;k<t.count;k++)color(g_params[SM_GAMMA_COLOR_0+k],pal[k]);g_cli_checkout_param_hook=&checkout;g_cli_checkin_param_hook=&checkin;pre_calls=layer_calls=output_calls=param_calls=checkin_calls=0;PF_InData id{};id.current_time=7;id.time_step=1;id.time_scale=24;PF_OutData od{};PF_PreRenderInput pi{};pi.bitdepth=t.depth;PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{&pre_checkout};PF_PreRenderExtra pe{&pi,&po,&pcb};int ep=EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&pe);PF_SmartRenderInput si{(short)t.depth};PF_SmartRenderCallbacks scb{&layer,&output};PF_SmartRenderExtra se{&si,&scb};int er=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&se);if(ep||er||pre_calls!=1||layer_calls!=1||output_calls!=1||param_calls!=SM_NUM_PARAMS-1||checkin_calls!=SM_NUM_PARAMS-1||!rects_ok(po)||in!=original)return 10+ti;bool classic_equal=false;if(t.depth!=32){PF_ParamDef*p[SM_NUM_PARAMS];for(int k=0;k<SM_NUM_PARAMS;k++)p[k]=g_params+k;g_params[SM_INPUT].u.ld=iw;if(EffectMain(PF_Cmd_RENDER,&id,&od,p,&cw,nullptr))return 30+ti;classic_equal=classic==smart;}for(int y=0;y<H;y++)for(size_t k=W*sizeof(P);k<rb;k++)if(smart[y*rb+k]!=0xa5||((t.depth!=32)&&classic[y*rb+k]!=0xa5))return 40+ti;if(t.depth!=32&&!classic_equal)return 50+ti;printf("CASE %d ",ti);for(auto b:smart)printf("%02x",b);printf("\nMETA %d %d %d %d %d %d %d %d %d\n",ti,pre_calls,layer_calls,output_calls,param_calls,checkin_calls,po.result_rect.right,po.max_result_rect.left,classic_equal?1:0);return 0;}
int main(){for(int i=0;i<6;i++){int r=T[i].depth==8?run_case<PF_Pixel8>(i):(T[i].depth==16?run_case<PF_Pixel16>(i):run_case<PF_PixelFloat>(i));if(r)return r;}return 0;}
