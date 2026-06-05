// AE-free shim for AEFX_SuiteHandlerTemplate.h.
//
// Provides AEFX_SuiteScoper backed by an in-process PF_Iterate{8,16,Float}
// implementation that walks every pixel of the source world and invokes the
// per-pixel callback — exactly the contract the port's RenderEntryChain relies
// on. No After Effects host required.
#pragma once
#ifndef OLMSMOOTHER_SHIM_SUITES_H
#define OLMSMOOTHER_SHIM_SUITES_H

#include "OLMSmoother.h"
#include <cstdint>

template <class PixT, class Fn>
static PF_Err cli_iterate_impl(PF_InData *, A_long start, A_long end,
                               PF_EffectWorld *src, const PF_LRect *,
                               void *refcon, Fn fn, PF_EffectWorld *dst)
{
	uint8_t *sbase = static_cast<uint8_t *>(src->data);
	uint8_t *dbase = static_cast<uint8_t *>(dst->data);
	for (A_long y = start; y < end; ++y) {
		PixT *srow = reinterpret_cast<PixT *>(sbase + static_cast<int64_t>(y) * src->rowbytes);
		PixT *drow = reinterpret_cast<PixT *>(dbase + static_cast<int64_t>(y) * dst->rowbytes);
		for (A_long x = 0; x < src->width; ++x) {
			PF_Err e = fn(refcon, x, y, &srow[x], &drow[x]);
			if (e != PF_Err_NONE) return e;
		}
	}
	return PF_Err_NONE;
}

static PF_Err cli_iterate8(PF_InData *d, A_long s, A_long e, PF_EffectWorld *src,
                           const PF_LRect *a, void *r, PF_Iterate8Fn fn, PF_EffectWorld *dst)
{ return cli_iterate_impl<PF_Pixel8>(d, s, e, src, a, r, fn, dst); }

static PF_Err cli_iterate16(PF_InData *d, A_long s, A_long e, PF_EffectWorld *src,
                            const PF_LRect *a, void *r, PF_Iterate16Fn fn, PF_EffectWorld *dst)
{ return cli_iterate_impl<PF_Pixel16>(d, s, e, src, a, r, fn, dst); }

static PF_Err cli_iterateF(PF_InData *d, A_long s, A_long e, PF_EffectWorld *src,
                           const PF_LRect *a, void *r, PF_IterateFloatFn fn, PF_EffectWorld *dst)
{ return cli_iterate_impl<PF_PixelFloat>(d, s, e, src, a, r, fn, dst); }

static PF_Iterate8Suite1     g_iterate8_suite     = { &cli_iterate8 };
static PF_Iterate16Suite1    g_iterate16_suite    = { &cli_iterate16 };
static PF_IterateFloatSuite1 g_iterateFloat_suite = { &cli_iterateF };

template <class T> struct SuitePtrOf;
template <> struct SuitePtrOf<PF_Iterate8Suite1>     { static PF_Iterate8Suite1     *get() { return &g_iterate8_suite; } };
template <> struct SuitePtrOf<PF_Iterate16Suite1>    { static PF_Iterate16Suite1    *get() { return &g_iterate16_suite; } };
template <> struct SuitePtrOf<PF_IterateFloatSuite1> { static PF_IterateFloatSuite1 *get() { return &g_iterateFloat_suite; } };

template <class T>
struct AEFX_SuiteScoper {
	T *sp;
	AEFX_SuiteScoper(PF_InData *, const char *, int) { sp = SuitePtrOf<T>::get(); }
	T *operator->() { return sp; }
};

#endif // OLMSMOOTHER_SHIM_SUITES_H
