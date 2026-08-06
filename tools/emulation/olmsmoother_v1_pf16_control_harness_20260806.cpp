#include <cstdint>
#include <cstring>
#include <new>
#define OLMSMOOTHER_TEST_HOOKS 1
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

struct MainCall16 { int32_t values[11]; int32_t evaluator_kind; uint32_t fields[5]; };
static MainCall16 *captures; static int capture_count, capture_capacity;
static uint16_t *source_base; static int source_rowbytes;
static int evaluator_kind(LinearEvalBase *e) {
	if(dynamic_cast<LinearOffsetFunction*>(e))return 0;
	if(dynamic_cast<LinearOffsetOneValue*>(e))return 1;
	if(dynamic_cast<LinearOffsetZeroOneValue*>(e))return 2;
	if(dynamic_cast<LinearOffsetZeroValue*>(e))return 3;
	if(dynamic_cast<LinearThreeOffsetFunction*>(e))return 4;
	return -1;
}
static void capture_executor(RenderState*,int d,int x1,int y1,const uint16_t *a,
	int x2,int y2,const uint16_t *b,LinearEvalBase *e,char use,int span) {
	if(capture_count>=capture_capacity)return; MainCall16 &c=captures[capture_count++];
	int64_t ao=a-source_base,bo=b-source_base;
	int32_t v[11]={d,x1,y1,int((ao%source_rowbytes)/4),int(ao/source_rowbytes),
		x2,y2,int((bo%source_rowbytes)/4),int(bo/source_rowbytes),(uint8_t)use,span};
	memcpy(c.values,v,sizeof(v));c.evaluator_kind=evaluator_kind(e);memcpy(c.fields,&e->offset,20);
}

static RenderState make_state(PF_EffectWorld *world, int tolerance) {
	RenderState state{}; state.src_world=world; state.tolerance_lo=tolerance;
	state.tolerance_hi=tolerance; state.tolerance=tolerance; state.threshold=tolerance;
	return state;
}

extern "C" void olmsmoother_subhandler16_exact(
    uint16_t *argb, int width, int height, int x, int y, int direction,
    int tolerance, uint32_t *result)
{
	PF_EffectWorld world{}; world.data=argb; world.width=width; world.height=height;
	world.rowbytes=width*8; RenderState state=make_state(&world,tolerance);
	uintptr_t neigh[9]{}; NeighborExtract16(x,y,&state,neigh); uint8_t f1=0,f2=0;
	SubHandler16Exact(&state,neigh,x,y,direction,&result[0],&f1,&f2,
	                  &result[3],&result[4],&result[5],&result[6],&result[7],&result[8]);
	result[1]=f1; result[2]=f2;
}

extern "C" uint64_t olmsmoother_edgewalker16_exact(
    uint16_t *argb, int width, int height, int x, int y, int direction,
    int pair_direction, int tolerance, int *out_x, int *out_y)
{
	PF_EffectWorld world{}; world.data=argb; world.width=width; world.height=height;
	world.rowbytes=width*8; RenderState state=make_state(&world,tolerance);
	return (uintptr_t)EdgeWalker16Exact(&state,x,y,direction,(uint32_t)pair_direction,
	                                   out_x,out_y,tolerance);
}

extern "C" int olmsmoother_mainkernel16_capture(
    uint16_t *argb, int width, int height, const int32_t *args12,
    MainCall16 *output, int capacity)
{
	PF_EffectWorld world{}; world.data=argb; world.width=width; world.height=height;
	world.rowbytes=width*8; RenderState state=make_state(&world,6); state.dst_world=&world;
	uintptr_t neigh[9]{}; NeighborExtract16(args12[0],args12[1],&state,neigh);
	captures=output;capture_count=0;capture_capacity=capacity;source_base=argb;source_rowbytes=width*4;
	g_interp_executor16_test_hook=capture_executor;
	MainInterpKernel16(&state,neigh,args12[0],args12[1],args12[2],args12[3],
		(char)args12[4],(char)args12[5],args12[6],args12[7],args12[8],args12[9],args12[10],args12[11]);
	g_interp_executor16_test_hook=nullptr;return capture_count;
}

extern "C" void olmsmoother_mainkernel16_execute(
    uint16_t *src_argb, uint16_t *dst_argb, int width, int height,
    const int32_t *args12)
{
	PF_EffectWorld src{}; src.data=src_argb; src.width=width; src.height=height;
	src.rowbytes=width*8;
	PF_EffectWorld dst{}; dst.data=dst_argb; dst.width=width; dst.height=height;
	dst.rowbytes=width*8;
	RenderState state=make_state(&src,6); state.dst_world=&dst;
	uintptr_t neigh[9]{}; NeighborExtract16(args12[0],args12[1],&state,neigh);
	g_interp_executor16_test_hook=nullptr;
	MainInterpKernel16(&state,neigh,args12[0],args12[1],args12[2],args12[3],
		(char)args12[4],(char)args12[5],args12[6],args12[7],args12[8],args12[9],args12[10],args12[11]);
}

extern "C" void olmsmoother_scanpixel16_execute(
    uint16_t *src_argb, uint16_t *dst_argb, int width, int height, int x, int y)
{
	PF_EffectWorld src{}; src.data=src_argb; src.width=width; src.height=height;
	src.rowbytes=width*8;
	PF_EffectWorld dst{}; dst.data=dst_argb; dst.width=width; dst.height=height;
	dst.rowbytes=width*8;
	RenderState state=make_state(&src,6); state.dst_world=&dst;
	ScanlinePixel16_Main(&state,x,y,
		(PF_Pixel16*)(src_argb+(y*width+x)*4),
		(PF_Pixel16*)(dst_argb+(y*width+x)*4));
}

extern "C" void olmsmoother_render16_rowmajor(
    uint16_t *src_argb, uint16_t *dst_argb, int width, int height, int tolerance)
{
	PF_EffectWorld src{}; src.data=src_argb; src.width=width; src.height=height;
	src.rowbytes=width*8;
	PF_EffectWorld dst{}; dst.data=dst_argb; dst.width=width; dst.height=height;
	dst.rowbytes=width*8;
	RenderState state=make_state(&src,tolerance); state.dst_world=&dst;
	for (int y=0; y<height; ++y) for (int x=0; x<width; ++x)
		ScanlinePixel16_Main(&state,x,y,
			(PF_Pixel16*)(src_argb+(y*width+x)*4),
			(PF_Pixel16*)(dst_argb+(y*width+x)*4));
}

extern "C" void olmsmoother_render16_order(
    uint16_t *src_argb, uint16_t *dst_argb, int width, int height,
    int tolerance, int order)
{
	PF_EffectWorld src{}; src.data=src_argb; src.width=width; src.height=height; src.rowbytes=width*8;
	PF_EffectWorld dst{}; dst.data=dst_argb; dst.width=width; dst.height=height; dst.rowbytes=width*8;
	RenderState state=make_state(&src,tolerance); state.dst_world=&dst;
	auto run=[&](int x,int y){ ScanlinePixel16_Main(&state,x,y,
		(PF_Pixel16*)(src_argb+(y*width+x)*4),(PF_Pixel16*)(dst_argb+(y*width+x)*4)); };
	bool column=(order&4)!=0, reverse_outer=(order&2)!=0, reverse_inner=(order&1)!=0;
	int outer_count=column?width:height, inner_count=column?height:width;
	for(int oi=0;oi<outer_count;++oi){ int o=reverse_outer?outer_count-1-oi:oi;
		for(int ii=0;ii<inner_count;++ii){ int i=reverse_inner?inner_count-1-ii:ii;
			if(column)run(o,i);else run(i,o); }}
}
