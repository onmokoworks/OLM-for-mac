#pragma once
#ifndef OLMBLUR_H
#define OLMBLUR_H

typedef unsigned char  u_char;
typedef unsigned short u_short;
typedef unsigned short u_int16;
typedef unsigned long  u_long;
typedef short int      int16;

#define PF_TABLE_BITS   12
#define PF_TABLE_SZ_16  4096
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

#include "OLMBlur_Strings.h"

#define MAJOR_VERSION 1
#define MINOR_VERSION 2
#define BUG_VERSION   1
#define STAGE_VERSION PF_Stage_DEVELOP
#define BUILD_VERSION 0

enum {
	OLMBLUR_INPUT = 0,
	OLMBLUR_BLUR_AMOUNT,
	OLMBLUR_BLUR_SMOOTHNESS,
	OLMBLUR_REPEAT,
	OLMBLUR_BIAS_DIRECTION,
	OLMBLUR_LEGACY,
	OLMBLUR_NUM_PARAMS
};

enum {
	BLUR_AMOUNT_DISK_ID = 5,
	BLUR_SMOOTHNESS_DISK_ID = 6,
	REPEAT_DISK_ID = 3,
	BIAS_DIRECTION_DISK_ID = 4,
	LEGACY_DISK_ID = 7
};

enum {
	BIAS_DIR_VERTICAL = 1,
	BIAS_DIR_HORIZONTAL = 2
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
