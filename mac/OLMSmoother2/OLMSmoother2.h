#pragma once
#ifndef OLMSMOOTHER2_H
#define OLMSMOOTHER2_H

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

#include "OLMSmoother2_Strings.h"

#define MAJOR_VERSION 2
#define MINOR_VERSION 1
#define BUG_VERSION   0
#define STAGE_VERSION PF_Stage_DEVELOP
#define BUILD_VERSION 0

#define NUM_GAMMA_COLORS 5

enum {
	SM_INPUT = 0,
	SM_ENABLE_KEY,
	SM_KEY_COLOR,
	SM_INVERT_KEY,
	SM_SMOOTHNESS,
	SM_EXTRA_SMOOTH,
	SM_SMOOTH_RANGE,
	SM_VERSION,
	SM_GAMMA_MODE,
	SM_GAMMA_VALUE,
	SM_NUM_GAMMA_COLORS,
	SM_GAMMA_COLOR_0,
	SM_GAMMA_COLOR_1,
	SM_GAMMA_COLOR_2,
	SM_GAMMA_COLOR_3,
	SM_GAMMA_COLOR_4,
	SM_NUM_PARAMS
};

// Disk IDs from Win disasm (FUN_180001c30):
//   Enable Color Key = 1, Color Key = 2, Invert Color Key = 15,
//   Smoothness = 3, Extra Smooth = 4, Smooth Range = 5,
//   Smoother Version = 6, Gamma Correction = 7, Gamma Value = 8,
//   Number of Gamma Colors = 9, Gamma Color 0..4 = 10..14
enum {
	ENABLE_KEY_DISK_ID      = 1,
	KEY_COLOR_DISK_ID       = 2,
	SMOOTHNESS_DISK_ID      = 3,
	EXTRA_SMOOTH_DISK_ID    = 4,
	SMOOTH_RANGE_DISK_ID    = 5,
	VERSION_DISK_ID         = 6,
	GAMMA_MODE_DISK_ID      = 7,
	GAMMA_VALUE_DISK_ID     = 8,
	NUM_GAMMA_DISK_ID       = 9,
	GAMMA_COLOR_0_DISK_ID   = 10,
	GAMMA_COLOR_1_DISK_ID   = 11,
	GAMMA_COLOR_2_DISK_ID   = 12,
	GAMMA_COLOR_3_DISK_ID   = 13,
	GAMMA_COLOR_4_DISK_ID   = 14,
	INVERT_KEY_DISK_ID      = 15
};

enum {
	SMOOTHER_V1 = 1,
	SMOOTHER_V2 = 2
};

enum {
	GAMMA_NONE        = 1,
	GAMMA_COLORS_ONLY = 2,
	GAMMA_ALL_COLORS  = 3
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
