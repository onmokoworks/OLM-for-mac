// ============================================================================
// SubHandler8 — literal port of FUN_1800033d0 (~430 lines).
// Same shape as SubHandler16 except 8-bit pixels and tolerance_lo (state+0x8)
// without the <<7 shift; src_world is at state+0x10 in Win.
// ============================================================================
struct SubHandler8Regs {
	uint64_t rax=0,rbx=0,rcx=0,rdx=0,rsi=0,rdi=0,rbp=0,rsp=0;
	uint64_t r8=0,r9=0,r10=0,r11=0,r12=0,r13=0,r14=0,r15=0;
};
// Pre-4ebcfd7d full 4 KiB zeroed virtual stack, retained verbatim.
struct SubHandlerMemoryReference {
	static constexpr uint64_t kModule=0x180000000ull, kStack=0x700000000000ull;
	uint8_t stack[0x1000]{}; bool zf=false,sf=false,of=false; PF_EffectWorld *world=nullptr;
	RenderState *state=nullptr; bool pf16=false;
	template<class T> T raw(uint64_t a) const { T v{}; memcpy(&v,(const void*)(uintptr_t)a,sizeof(v));return v; }
	// Bound the integer offset before forming a native pointer; a+n can wrap.
	bool is_stack(uint64_t a,size_t n=1) const { return a>=kStack&&n<=sizeof(stack)&&a-kStack<=sizeof(stack)-n; }
	void *ptr(uint64_t a) { return is_stack(a)?(void*)(stack+(a-kStack)):(void*)(uintptr_t)a; }
	uint8_t read8(uint64_t a) const { if(is_stack(a))return stack[a-kStack]; return raw<uint8_t>(a); }
	uint16_t read16(uint64_t a) const { if(is_stack(a,2)){uint16_t v;memcpy(&v,stack+(a-kStack),2);return v;} return raw<uint16_t>(a); }
	uint32_t read32(uint64_t a) const {
		if(is_stack(a,4)){uint32_t v;memcpy(&v,stack+(a-kStack),4);return v;}
		if(state&&a==(uintptr_t)state+8)return uint32_t(state->tolerance_lo);
		if(state&&a==(uintptr_t)state+0xc)return uint32_t(state->tolerance_hi);
		if(state&&pf16&&a==(uintptr_t)state+0x10)return uint32_t(state->threshold);
		if(world&&(a==(uintptr_t)world+4||a==(uintptr_t)world+0x24))return uint32_t(world->width);
		if(world&&(a==(uintptr_t)world+8||a==(uintptr_t)world+0x28))return uint32_t(world->height);
		if(world&&(a==(uintptr_t)world+0xc||a==(uintptr_t)world+0x20))return uint32_t(world->rowbytes);
		if(a>=kModule+0xf000&&a<kModule+0xf114){
			const uint64_t o=a-kModule; const int32_t *p=nullptr; uint64_t base=0;
			if(o>=0xf000&&o<0xf024){p=DAT_18000f000;base=0xf000;}
			else if(o>=0xf028&&o<0xf04c){p=DAT_18000f028;base=0xf028;}
			else if(o>=0xf050&&o<0xf074){p=DAT_18000f050;base=0xf050;}
			else if(o>=0xf078&&o<0xf09c){p=DAT_18000f078;base=0xf078;}
			else if(o>=0xf0a0&&o<0xf0c4){p=DAT_18000f0a0;base=0xf0a0;}
			else if(o>=0xf0c8&&o<0xf0ec){p=DAT_18000f0c8;base=0xf0c8;}
			else if(o>=0xf0f0&&o<0xf114){p=DAT_18000f0f0;base=0xf0f0;}
			if(p)return uint32_t(p[(o-base)/4]);
		}
		return raw<uint32_t>(a);
	}
	uint64_t read64(uint64_t a) const { if(is_stack(a,8)){uint64_t v;memcpy(&v,stack+(a-kStack),8);return v;} if(state&&a==(uintptr_t)state+(pf16?0x18:0x10))return (uintptr_t)world; if(world&&(a==(uintptr_t)world+0x10||a==(uintptr_t)world+0x18))return (uintptr_t)world->data; return raw<uint64_t>(a); }
	void write8(uint64_t a,uint8_t v){if(is_stack(a))stack[a-kStack]=v;else memcpy((void*)(uintptr_t)a,&v,1);}
	void write16(uint64_t a,uint16_t v){if(is_stack(a,2))memcpy(stack+(a-kStack),&v,2);else memcpy((void*)(uintptr_t)a,&v,2);}
	void write32(uint64_t a,uint32_t v){if(is_stack(a,4))memcpy(stack+(a-kStack),&v,4);else memcpy((void*)(uintptr_t)a,&v,4);}
	void write64(uint64_t a,uint64_t v){if(is_stack(a,8))memcpy(stack+(a-kStack),&v,8);else memcpy((void*)(uintptr_t)a,&v,8);}
	uint64_t subflags(uint64_t a,uint64_t b,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);a&=mask;b&=mask;uint64_t r=(a-b)&mask;zf=r==0;sf=(r>>(w-1))&1;of=(((a^b)&(a^r))>>(w-1))&1;return r;}
	uint64_t addflags(uint64_t a,uint64_t b,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);a&=mask;b&=mask;uint64_t r=(a+b)&mask;zf=r==0;sf=(r>>(w-1))&1;of=((~(a^b)&(a^r))>>(w-1))&1;return r;}
	void logicflags(uint64_t r,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);r&=mask;zf=r==0;sf=(r>>(w-1))&1;of=false;}
};

template<size_t StackBegin, size_t StackSize>
struct SubHandlerMemory {
	static constexpr uint64_t kModule=0x180000000ull, kStack=0x700000000000ull;
	static_assert(StackSize > 0 && StackBegin + StackSize <= 0x1000, "virtual stack window");
	static constexpr uint64_t kStorage = kStack + StackBegin;
	uint8_t stack[StackSize]{}; bool zf=false,sf=false,of=false; PF_EffectWorld *world=nullptr;
	RenderState *state=nullptr; bool pf16=false;
	template<class T> T raw(uint64_t a) const { T v{}; memcpy(&v,(const void*)(uintptr_t)a,sizeof(v));return v; }
	// Bound the integer offset before forming a native pointer; a+n can wrap.
	bool is_stack(uint64_t a,size_t n=1) const { return a>=kStorage&&n<=sizeof(stack)&&a-kStorage<=sizeof(stack)-n; }
	void *ptr(uint64_t a) { return is_stack(a)?(void*)(stack+(a-kStorage)):(void*)(uintptr_t)a; }
	uint8_t read8(uint64_t a) const { if(is_stack(a))return stack[a-kStorage]; return raw<uint8_t>(a); }
	uint16_t read16(uint64_t a) const { if(is_stack(a,2)){uint16_t v;memcpy(&v,stack+(a-kStorage),2);return v;} return raw<uint16_t>(a); }
	uint32_t read32(uint64_t a) const {
		if(is_stack(a,4)){uint32_t v;memcpy(&v,stack+(a-kStorage),4);return v;}
		if(state&&a==(uintptr_t)state+8)return uint32_t(state->tolerance_lo);
		if(state&&a==(uintptr_t)state+0xc)return uint32_t(state->tolerance_hi);
		if(state&&pf16&&a==(uintptr_t)state+0x10)return uint32_t(state->threshold);
		if(world&&(a==(uintptr_t)world+4||a==(uintptr_t)world+0x24))return uint32_t(world->width);
		if(world&&(a==(uintptr_t)world+8||a==(uintptr_t)world+0x28))return uint32_t(world->height);
		if(world&&(a==(uintptr_t)world+0xc||a==(uintptr_t)world+0x20))return uint32_t(world->rowbytes);
		if(a>=kModule+0xf000&&a<kModule+0xf114){
			const uint64_t o=a-kModule; const int32_t *p=nullptr; uint64_t base=0;
			if(o>=0xf000&&o<0xf024){p=DAT_18000f000;base=0xf000;}
			else if(o>=0xf028&&o<0xf04c){p=DAT_18000f028;base=0xf028;}
			else if(o>=0xf050&&o<0xf074){p=DAT_18000f050;base=0xf050;}
			else if(o>=0xf078&&o<0xf09c){p=DAT_18000f078;base=0xf078;}
			else if(o>=0xf0a0&&o<0xf0c4){p=DAT_18000f0a0;base=0xf0a0;}
			else if(o>=0xf0c8&&o<0xf0ec){p=DAT_18000f0c8;base=0xf0c8;}
			else if(o>=0xf0f0&&o<0xf114){p=DAT_18000f0f0;base=0xf0f0;}
			if(p)return uint32_t(p[(o-base)/4]);
		}
		return raw<uint32_t>(a);
	}
	uint64_t read64(uint64_t a) const { if(is_stack(a,8)){uint64_t v;memcpy(&v,stack+(a-kStorage),8);return v;} if(state&&a==(uintptr_t)state+(pf16?0x18:0x10))return (uintptr_t)world; if(world&&(a==(uintptr_t)world+0x10||a==(uintptr_t)world+0x18))return (uintptr_t)world->data; return raw<uint64_t>(a); }
	void write8(uint64_t a,uint8_t v){if(is_stack(a))stack[a-kStorage]=v;else memcpy((void*)(uintptr_t)a,&v,1);}
	void write16(uint64_t a,uint16_t v){if(is_stack(a,2))memcpy(stack+(a-kStorage),&v,2);else memcpy((void*)(uintptr_t)a,&v,2);}
	void write32(uint64_t a,uint32_t v){if(is_stack(a,4))memcpy(stack+(a-kStorage),&v,4);else memcpy((void*)(uintptr_t)a,&v,4);}
	void write64(uint64_t a,uint64_t v){if(is_stack(a,8))memcpy(stack+(a-kStorage),&v,8);else memcpy((void*)(uintptr_t)a,&v,8);}
	uint64_t subflags(uint64_t a,uint64_t b,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);a&=mask;b&=mask;uint64_t r=(a-b)&mask;zf=r==0;sf=(r>>(w-1))&1;of=(((a^b)&(a^r))>>(w-1))&1;return r;}
	uint64_t addflags(uint64_t a,uint64_t b,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);a&=mask;b&=mask;uint64_t r=(a+b)&mask;zf=r==0;sf=(r>>(w-1))&1;of=((~(a^b)&(a^r))>>(w-1))&1;return r;}
	void logicflags(uint64_t r,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);r&=mask;zf=r==0;sf=(r>>(w-1))&1;of=false;}
};
// The two PF16 generated CFGs never copy/escape RSP. Their complete
// reachable stack accesses (including wrapper arguments) are [0x7a8,0x830)
// and [0x7d8,0x848), relative to kStack. Keep padding around both intervals.
// See orchestra/reports/P05c-evidence/smoother_stack_bounds.py for CFG proof.
// Other helpers keep the original full window; all virtual addresses stay fixed.
#ifdef OLM_REFERENCE_BUILD
using SubHandler8Memory = SubHandlerMemoryReference;
using Classifier16Memory = SubHandlerMemoryReference;
using EdgeWalker16Memory = SubHandlerMemoryReference;
#else
using SubHandler8Memory = SubHandlerMemory<0, 0x1000>;
using Classifier16Memory = SubHandlerMemory<0x780, 0xc0>;
using EdgeWalker16Memory = SubHandlerMemory<0x7c0, 0xa0>;
#endif

static int32_t
Classifier16Exact(RenderState *state, uint32_t x, uint32_t y,
                  const uintptr_t *neigh, uint32_t dir)
{
	SubHandler8Regs R; Classifier16Memory M; uint64_t T=0;
	M.state=state; M.world=state->src_world; M.pf16=true;
	R.rcx=(uintptr_t)state; R.rdx=x; R.r8=y; R.r9=(uintptr_t)neigh;
	R.rsp=SubHandler8Memory::kStack+0x800;
	M.write64(R.rsp,0xdeadbeefdeadbeefull);
	M.write64(R.rsp+0x28,dir);
#include "OLMSmoother_classifier16.generated.inc"
}

static uint16_t*
EdgeWalker16Exact(RenderState *state, int x, int y, int dir1, uint32_t dir2,
                  int *out_x, int *out_y, int threshold)
{
	SubHandler8Regs R; EdgeWalker16Memory M; uint64_t T=0;
	M.state=state; M.world=state->src_world; M.pf16=true;
	R.rcx=(uintptr_t)state; R.rdx=uint32_t(x); R.r8=uint32_t(y); R.r9=uint32_t(dir1);
	R.rsp=SubHandler8Memory::kStack+0x800; M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir2,(uintptr_t)out_x,(uintptr_t)out_y,uint32_t(threshold)};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_edgewalker16.generated.inc"
}

static void
SubHandler16Exact(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
                  uint32_t *o6, uint8_t *o7, uint8_t *o8,
                  uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
                  uint32_t *o13, uint32_t *o14)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0;
	M.state=state; M.world=state->src_world; M.pf16=true;
	R.rcx=(uintptr_t)state; R.rdx=(uintptr_t)neigh; R.r8=x; R.r9=y;
	R.rsp=SubHandler8Memory::kStack+0x800; M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir,(uintptr_t)o6,(uintptr_t)o7,(uintptr_t)o8,(uintptr_t)o9,
		(uintptr_t)o10,(uintptr_t)o11,(uintptr_t)o12,(uintptr_t)o13,(uintptr_t)o14};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_subhandler16.generated.inc"
}

static uint8_t*
EdgeWalker8Exact(RenderState *state, int x, int y, int dir1, uint32_t dir2,
                 int *out_x, int *out_y, int threshold)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0; M.state=state; M.world=state->src_world;
	R.rcx=(uintptr_t)state; R.rdx=uint32_t(x); R.r8=uint32_t(y); R.r9=uint32_t(dir1);
	R.rsp=SubHandler8Memory::kStack+0x800; M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir2,(uintptr_t)out_x,(uintptr_t)out_y,uint32_t(threshold)};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_edgewalker8.generated.inc"
}

static void
SubHandler8Exact(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
                 uint32_t *o6, uint8_t *o7, uint8_t *o8,
                 uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
                 uint32_t *o13, uint32_t *o14)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0; M.state=state; M.world=state->src_world;
	R.rcx=(uintptr_t)state; R.rdx=(uintptr_t)neigh; R.r8=x; R.r9=y;
	R.rsp=SubHandler8Memory::kStack+0x800;
	M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir,(uintptr_t)o6,(uintptr_t)o7,(uintptr_t)o8,(uintptr_t)o9,
		(uintptr_t)o10,(uintptr_t)o11,(uintptr_t)o12,(uintptr_t)o13,(uintptr_t)o14};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_subhandler8.generated.inc"
}

static void
SubHandler8(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
            uint32_t *o6, uint8_t *o7, uint8_t *o8,
            uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
            uint32_t *o13, uint32_t *o14)
{
	SubHandler8Exact(state,neigh,x,y,dir,o6,o7,o8,o9,o10,o11,o12,o13,o14);
}

static void
SubHandler8Legacy(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
            uint32_t *o6, uint8_t *o7, uint8_t *o8,
            uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
            uint32_t *o13, uint32_t *o14)
{
	const uint8_t *pbVar1, *pbVar2, *pbVar3, *pbVar4;
	uint32_t *puVar5;
	int iVar10, iVar11, iVar12;
	const uint8_t *pbVar13, *pbVar14;
	int64_t lVar15;
	uint32_t uVar9, uVar16, uVar17, uVar18, uVar19, uVar20;
	int iVar21, iVar23;

	uint32_t *puVar22 = o14;
	*o9 = x; *o10 = y;
	*o11 = x; *o12 = y;
	*o13 = x; *o14 = y;
	*o7 = 0;
	*o8 = 0;
	iVar21 = state->threshold;       // *(param_1+0xc)
	iVar23 = state->tolerance_lo;    // *(param_1+0x8)
	lVar15 = (int64_t)(int)dir;
	pbVar13 = *(const uint8_t**)((uint8_t*)neigh + 0x20);
	uint32_t uVar9_init = (uint32_t)((int)DAT_18000f0c8[lVar15] + (int)x);
	uVar9 = uVar9_init;
	iVar11 = DAT_18000f028[lVar15];
	uint32_t param14_dy = (uint32_t)((int)DAT_18000f0f0[lVar15] + (int)y);
	iVar12 = DAT_18000f000[lVar15];
	pbVar14 = (const uint8_t*)neigh[iVar11];
	uVar16 = (uint32_t)DAT_18000f0a0[lVar15];
	pbVar1 = (const uint8_t*)neigh[iVar12];
	pbVar2 = (const uint8_t*)neigh[DAT_18000f050[lVar15]];
	pbVar3 = (const uint8_t*)neigh[DAT_18000f078[lVar15]];
	pbVar4 = (const uint8_t*)neigh[lVar15];
	uint32_t local_res18_0 = x;
	uint32_t local_res20_0 = y;
	uint32_t loc_param5 = 0, loc_param9 = 0, loc_param10 = 0, loc_param13 = 0;

	auto cmp_le_8 = [&](const uint8_t *a, const uint8_t *b) -> bool {
		if (!a || !b) return false;
		if (iVar23 == 0) {
			return (a[1]==b[1]) && (a[3]==b[3]) && (a[2]==b[2]) && (*a==*b);
		}
		uint32_t d, s;
		d = (uint32_t)a[1] - (uint32_t)b[1]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)a[3] - (uint32_t)b[3]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)a[2] - (uint32_t)b[2]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)*a   - (uint32_t)*b;   s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		return true;
	};

	iVar10 = ColorCompare8(pbVar2, pbVar13);
	puVar5 = o9;
	if (iVar23 < iVar10) {
		iVar10 = ColorCompare8(pbVar3, pbVar13);
		puVar5 = o9;
		if (iVar23 < iVar10) {
			iVar10 = ColorCompare8(pbVar1, pbVar13);
			puVar5 = o9;
			if (iVar23 < iVar10) {
				iVar10 = ColorCompare8(pbVar14, pbVar13);
				puVar5 = o9;
				uint32_t uVar17b = local_res20_0;
				uint32_t uVar18b = local_res18_0;
				if (iVar23 < iVar10) {
					*o9  = local_res18_0;
					*o10 = local_res20_0;
					int wa_x = (int)local_res18_0, wa_y = (int)local_res20_0;
					int wb_x = (int)uVar18b,       wb_y = (int)uVar17b;
					uint8_t *rwa = EdgeWalker8(state, (int)local_res18_0, (int)local_res20_0,
					                            iVar12, uVar16, &wa_x, &wa_y, iVar21);
					uint8_t *rwb = EdgeWalker8(state, (int)uVar18b, (int)uVar17b,
					                            iVar11, uVar16, &wb_x, &wb_y, iVar21);
					int param_5_val = wb_x;
					int param_10_val = wb_y;

					uint32_t uVar9c = (uint32_t)((param_5_val - (int)uVar18b) >> 31);
					*o13 = uVar18b;
					*puVar22 = uVar17b;
					iVar23 = (int)((param_5_val - (int)uVar18b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)((wa_x - (int)uVar18b) >> 31);
					iVar21 = (int)((wa_x - (int)uVar18b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)wa_x;
					if (iVar23 < iVar21) uVar9c = (uint32_t)param_5_val;
					*o11 = uVar9c;
					uVar9c = (uint32_t)((param_10_val - (int)uVar17b) >> 31);
					iVar11 = (int)((param_10_val - (int)uVar17b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)((wa_y - (int)uVar17b) >> 31);
					iVar12 = (int)((wa_y - (int)uVar17b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)wa_y;
					if (iVar11 < iVar12) uVar9c = (uint32_t)param_10_val;
					*o12 = uVar9c;
					if ((rwa == nullptr) && (rwb == nullptr)) {
						*o6 = 0;
					} else {
						*o6 = 1;
						if (iVar21 < iVar23) {
							*o11 = (uint32_t)param_5_val;
							*o13 = (uint32_t)wa_x;
						} else {
							*o11 = (uint32_t)wa_x;
							*o13 = (uint32_t)param_5_val;
						}
						if (iVar12 < iVar11) {
							*o12 = (uint32_t)param_10_val;
							*puVar22 = (uint32_t)wa_y;
						} else {
							*o12 = (uint32_t)wa_y;
							*puVar22 = (uint32_t)param_10_val;
						}
						uint32_t uVar9d = (uint32_t)((int)DAT_18000f0c8[(int64_t)(int)uVar16] + (int)*o13);
						PF_EffectWorld *src = state->src_world;
						if (((int)uVar9d > 0) && ((int)uVar9d < src->width)) {
							uint32_t uVar16d = (uint32_t)((int)DAT_18000f0f0[(int64_t)(int)uVar16] + (int)*puVar22);
							if (((int)uVar16d > 0) && ((int)uVar16d < src->height)) {
								*o13 = uVar9d;
								*puVar22 = uVar16d;
							}
						}
					}
					uint32_t a = (*o11 - *puVar5);
					uint32_t s = (uint32_t)((int)a >> 31);
					a = (a ^ s) - s;
					uint32_t b = (*o12 - *o10);
					uint32_t s2 = (uint32_t)((int)b >> 31);
					b = (b ^ s2) - s2;
					if ((int)b < (int)a) b = a;
					if ((b & 1u) != 0) return;
					*o7 = 1;
					return;
				}
			}
		}
	}

	*o6 = 2;
	*puVar5 = uVar9;
	*o10 = param14_dy;
	loc_param13 = uVar9;
	loc_param9  = param14_dy;
	bool entered_b6f = false;

	if (pbVar13 == nullptr) goto LAB_8_180003a;
	if (cmp_le_8(pbVar13, pbVar2)) {
		entered_b6f = true;
		int wa_x = (int)uVar9, wa_y = (int)param14_dy;
		EdgeWalker8(state, uVar9, param14_dy, iVar12, dir, &wa_x, &wa_y, iVar21);
		*puVar5 = (uint32_t)wa_x;
		*o10    = (uint32_t)wa_y;
		goto AFTER_FIRST_WALK_8;
	}

LAB_8_180003a:
	{
		int iVar10b = ColorCompare8(pbVar13, pbVar2);
		if (iVar23 < iVar10b) {
			int wa_x = (int)uVar9, wa_y = (int)param14_dy;
			EdgeWalker8(state, uVar9, param14_dy, iVar12, dir, &wa_x, &wa_y, iVar21);
			*puVar5 = (uint32_t)wa_x;
			*o10    = (uint32_t)wa_y;
			entered_b6f = true;
			goto AFTER_FIRST_WALK_8;
		}
	}
	{
		bool ok_iv9 = false;
		if (pbVar13 == nullptr) {
			int iVar10c = ColorCompare8(pbVar13, pbVar3);
			if (iVar23 < iVar10c) ok_iv9 = true;
		} else {
			ok_iv9 = !cmp_le_8(pbVar13, pbVar3);
		}
		if (ok_iv9) {
			int wb_x = (int)uVar9, wb_y = (int)param14_dy;
			EdgeWalker8(state, uVar9, param14_dy, iVar11, dir, &wb_x, &wb_y, iVar21);
			*puVar5 = (uint32_t)wb_x;
			*o10    = (uint32_t)wb_y;
		}
	}
	goto AFTER_NO_FIRST_WALK_8;

AFTER_FIRST_WALK_8:
	{
		bool do_iv11 = false;
		if (pbVar13 == nullptr) {
			int iVar10d = ColorCompare8(pbVar13, pbVar3);
			if (iVar23 < iVar10d) do_iv11 = true;
		} else {
			do_iv11 = !cmp_le_8(pbVar13, pbVar3);
		}
		if (do_iv11) {
			int p13_x = (int)loc_param13, p13_y = (int)loc_param9;
			EdgeWalker8(state, uVar9, param14_dy, iVar11, dir, &p13_x, &p13_y, iVar21);
			loc_param13 = (uint32_t)p13_x;
			loc_param9  = (uint32_t)p13_y;
		}
		uint32_t a = local_res18_0 - *puVar5;
		uint32_t b = local_res18_0 - loc_param13;
		uint32_t c = local_res20_0 - loc_param9;
		uint32_t d = local_res20_0 - *o10;
		auto absi = [](uint32_t v) -> int {
			uint32_t s = (uint32_t)((int)v >> 31);
			return (int)((v ^ s) - s);
		};
		if (absi(b) <= absi(c)) b = c;
		if (absi(a) <= absi(d)) a = d;
		if (absi(a) < absi(b)) {
			*puVar5 = loc_param13;
			*o10    = loc_param9;
		}
	}

AFTER_NO_FIRST_WALK_8:
	{
		bool went_LAB_180003d46 = false;
		bool stayed_default = (*puVar5 == uVar9) && (*o10 == param14_dy);
		bool jump_180003c5c = false;

		if (stayed_default) {
			if (pbVar13 != nullptr) {
				bool match = false;
				if (cmp_le_8(pbVar13, pbVar1) && cmp_le_8(pbVar13, pbVar14)) {
					match = true;
				}
				if (match) {
					*o6 = 3;
					goto LAB_180003bdb_8;
				}
				goto LAB_180003be9_8;
			}
			jump_180003c5c = true;
		} else {
LAB_180003bdb_8:
			if (pbVar13 == nullptr) { jump_180003c5c = true; goto AFTER_180003c5c_8; }
			if (iVar23 == 0) {
				if (pbVar1 == nullptr) { jump_180003c5c = true; goto AFTER_180003c5c_8; }
LAB_180003be9_8:
				if (!cmp_le_8(pbVar13, pbVar1)) {
					jump_180003c5c = true;
					goto AFTER_180003c5c_8;
				}
				// LAB_180003c6f
				if (pbVar13 != nullptr) {
					if (iVar23 != 0) goto LAB_180003cba_8;
					if (pbVar14 != nullptr &&
					    (pbVar13[1]==pbVar14[1]) && (pbVar13[3]==pbVar14[3]) &&
					    (pbVar13[2]==pbVar14[2]) && (*pbVar13==*pbVar14)) {
						*o8 = 1;
						return;
					}
				}
				goto LAB_180003d0d_8;
			} else {
				if (pbVar1 == nullptr) { jump_180003c5c = true; goto AFTER_180003c5c_8; }
				if (!cmp_le_8(pbVar13, pbVar1)) {
					jump_180003c5c = true;
					goto AFTER_180003c5c_8;
				}
LAB_180003cba_8:
				if (pbVar14 != nullptr && cmp_le_8(pbVar13, pbVar14)) {
					went_LAB_180003d46 = true;
					goto AFTER_180003c5c_8;
				}
				goto LAB_180003d0d_8;
			}
		}

AFTER_180003c5c_8:
		if (jump_180003c5c) {
			int iVar10e = ColorCompare8(pbVar13, pbVar1);
			if (iVar23 < iVar10e) {
				if (pbVar13 != nullptr) {
					if (iVar23 != 0) goto LAB_180003cba_2_8;
					if (pbVar14 != nullptr &&
					    (pbVar13[1]==pbVar14[1]) && (pbVar13[3]==pbVar14[3]) &&
					    (pbVar13[2]==pbVar14[2]) && (*pbVar13==*pbVar14)) {
						*o8 = 1;
						return;
					}
				}
				goto LAB_180003d0d_8;
LAB_180003cba_2_8:
				if (pbVar14 != nullptr && cmp_le_8(pbVar13, pbVar14)) {
					went_LAB_180003d46 = true;
					goto AFTER_180003c5c_8_after;
				}
			}
		}
AFTER_180003c5c_8_after:

LAB_180003d0d_8:
		if (!went_LAB_180003d46) {
			int iVar10f = ColorCompare8(pbVar13, pbVar14);
			if (iVar23 < iVar10f) went_LAB_180003d46 = true;
		}
		if (!went_LAB_180003d46) {
			int iVar10g = ColorCompare8(pbVar1, pbVar4);
			if (iVar10g < -iVar23) {
				int iVar10h = ColorCompare8(pbVar14, pbVar4);
				if (iVar10h < -iVar23) {
					*o8 = 1;
					return;
				}
			}
		}
		if (went_LAB_180003d46) {
			*o8 = 1;
			return;
		}

		// Final walks
		uint32_t uVar18 = local_res20_0;
		uint32_t uVar9b = local_res18_0;
		int p10_x = (int)local_res18_0, p10_y = (int)local_res20_0;
		int p9_x  = (int)local_res18_0, p9_y  = (int)local_res20_0;
		EdgeWalker8(state, local_res18_0, local_res20_0, iVar11, uVar16, &p10_x, &p10_y, iVar21);
		int rl_x = (int)uVar9b, rl_y = (int)uVar18;
		int p5_x = (int)local_res18_0, p5_y = (int)local_res20_0;
		EdgeWalker8(state, uVar9b, uVar18, iVar12, uVar16, &rl_x, &p5_x, iVar21);
		(void)rl_y;
		loc_param10 = (uint32_t)p10_x;
		loc_param9  = (uint32_t)p10_y;
		// In Win FUN_1800033d0 (decomp 1565) the second EdgeWalker writes out_x
		// into local_res20[0] and out_y into param_5; every later use of
		// local_res20[0] (decomp 1621/1624/1643) therefore reads walk B's end X,
		// not the original y.
		uint32_t local_res20_after = (uint32_t)rl_x;  // walk B end x
		loc_param5 = (uint32_t)p5_x;                  // walk B end y

		bool bVar6 = false, bVar7 = false;
		if (iVar23 == 0) {
			if (pbVar13 != nullptr && pbVar1 != nullptr &&
			    (pbVar13[1]==pbVar1[1]) && (pbVar13[3]==pbVar1[3]) &&
			    (pbVar13[2]==pbVar1[2]) && (*pbVar13==*pbVar1)) bVar6 = true;
			if (pbVar13 != nullptr && pbVar14 != nullptr &&
			    (pbVar13[1]==pbVar14[1]) && (pbVar13[3]==pbVar14[3]) &&
			    (pbVar13[2]==pbVar14[2]) && (*pbVar13==*pbVar14)) bVar7 = true;
		} else {
			bVar6 = (pbVar13 && pbVar1  && cmp_le_8(pbVar13, pbVar1));
			bVar7 = (pbVar13 && pbVar14 && cmp_le_8(pbVar13, pbVar14));
		}

		if (bVar6) {
			if (bVar7) return;
			*o11 = loc_param10;
			loc_param5 = loc_param9;
		} else if (bVar7) {
			*o11 = local_res20_after;  // Win *param_11 = local_res20[0] = walk B end x
		} else {
			uint32_t a = uVar9b - local_res20_after;  // x - B.x (decomp 1621)
			uint32_t b = uVar18 - loc_param5;         // y - B.y
			uint32_t c = uVar9b - loc_param10;        // x - A.x
			uint32_t d = uVar18 - loc_param9;         // y - A.y
			*o11 = local_res20_after;
			*o12 = loc_param5;
			auto absi = [](uint32_t v) -> int {
				uint32_t s = (uint32_t)((int)v >> 31);
				return (int)((v ^ s) - s);
			};
			if (absi(c) <= absi(d)) c = d;
			if (absi(a) <= absi(b)) a = b;
			if (absi(a) <= absi(c)) return;
			*o11 = loc_param10;
			*o12 = loc_param9;
			return;
		}
		*o12 = loc_param5;
		return;
	}
}

