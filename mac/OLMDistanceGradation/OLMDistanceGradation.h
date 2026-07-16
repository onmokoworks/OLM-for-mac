#pragma once
#ifndef OLMDISTANCEGRADATION_H
#define OLMDISTANCEGRADATION_H

typedef unsigned char  u_char;
typedef unsigned short u_short;
typedef unsigned short u_int16;
typedef unsigned long  u_long;
typedef short int      int16;

#define PF_TABLE_BITS      12
#define PF_TABLE_SZ_16     4096
#define PF_DEEP_COLOR_AWARE 1

#include "AEConfig.h"

#ifdef AE_OS_WIN
	typedef unsigned short PixelType;
	#include <Windows.h>
#endif

#include "entry.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include "AE_Macros.h"
#include "Param_Utils.h"
#include "AE_EffectCBSuites.h"
#include "String_Utils.h"
#include "AE_GeneralPlug.h"
#include "AEFX_ChannelDepthTpl.h"
#include "AEGP_SuiteHandler.h"

#include "OLMDistanceGradation_Strings.h"

#define MAJOR_VERSION 0
#define MINOR_VERSION 8
#define BUG_VERSION   2
#define STAGE_VERSION PF_Stage_ALPHA
#define BUILD_VERSION 0

enum {
	DG_INPUT = 0,
	DG_INVERT,
	DG_IN_OUT,
	DG_INSIDE_THRESHOLD,
	DG_OUTSIDE_THRESHOLD,
	DG_RENDER_MODE,
	DG_USE_BG_COLOR,
	DG_GRAD_COLOR,
	DG_BG_COLOR,
	DG_INTERP_MODE,
	DG_POWER,
	DG_BLUR_MODE,
	DG_BLUR_SIZE,
	DG_NUM_PARAMS
};

enum {
	INVERT_DISK_ID            = 1,
	IN_OUT_DISK_ID            = 2,
	INSIDE_THRESHOLD_DISK_ID  = 3,
	OUTSIDE_THRESHOLD_DISK_ID = 4,
	RENDER_MODE_DISK_ID       = 5,
	USE_BG_COLOR_DISK_ID      = 6,
	GRAD_COLOR_DISK_ID        = 7,
	BG_COLOR_DISK_ID          = 8,
	INTERP_MODE_DISK_ID       = 9,
	POWER_DISK_ID             = 10,
	BLUR_MODE_DISK_ID         = 11,
	BLUR_SIZE_DISK_ID         = 12
};

enum {
	IN_OUT_INSIDE  = 1,
	IN_OUT_OUTSIDE = 2,
	IN_OUT_BOTH    = 3
};

enum {
	RENDER_MODE_RGB   = 1,
	RENDER_MODE_LAYER = 2
};

enum {
	INTERP_CONSTANT = 1,
	INTERP_LINEAR   = 2,
	INTERP_SPHERE   = 3,
	INTERP_POWER    = 4
};

enum {
	BLUR_MODE_NONE      = 1,
	BLUR_MODE_NO_SCALE  = 2,
	BLUR_MODE_SCALE     = 3
};

extern "C" {
	DllExport
	PF_Err EffectMain(
		PF_Cmd         cmd,
		PF_InData     *in_data,
		PF_OutData    *out_data,
		PF_ParamDef   *params[],
		PF_LayerDef   *output,
		void          *extra);
}

#endif
