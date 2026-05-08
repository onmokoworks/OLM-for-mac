#pragma once
#ifndef OLMSMOOTHER_H
#define OLMSMOOTHER_H

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

#include "OLMSmoother_Strings.h"

// Win版 eVER = 0x00090800 → vers=1, subvers=2, bugfix=1, stage=0, build=0
#define MAJOR_VERSION 1
#define MINOR_VERSION 2
#define BUG_VERSION   1
#define STAGE_VERSION PF_Stage_DEVELOP
#define BUILD_VERSION 0

enum {
	SM_INPUT = 0,
	SM_USE_KEY,
	SM_KEY_COLOR,
	SM_TOLERANCE,
	SM_NUM_PARAMS
};

// Disk IDs — match Win v1 FUN_18000a2c0 PARAMS_SETUP
enum {
	USE_KEY_DISK_ID   = 1,
	KEY_COLOR_DISK_ID = 2,
	TOLERANCE_DISK_ID = 3
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
