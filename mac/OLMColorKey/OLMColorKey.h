#pragma once
#ifndef OLMCOLORKEY_H
#define OLMCOLORKEY_H

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

#include "OLMColorKey_Strings.h"

#define MAJOR_VERSION 2
#define MINOR_VERSION 3
#define BUG_VERSION   1
#define STAGE_VERSION PF_Stage_DEVELOP
#define BUILD_VERSION 0

#define OLMCOLORKEY_MAX_COLORS 25

enum {
	OLMCOLORKEY_INPUT = 0,
	OLMCOLORKEY_COLOR_KEEP,
	OLMCOLORKEY_THRESHOLD,
	OLMCOLORKEY_PREMULTIPLIED,
	OLMCOLORKEY_COLOR_SPACE,
	OLMCOLORKEY_FORCE_LOWER_PRECISION,
	OLMCOLORKEY_PER_COLOR,
	OLMCOLORKEY_PER_COMPONENT,
	OLMCOLORKEY_THRESHOLD_R,
	OLMCOLORKEY_THRESHOLD_G,
	OLMCOLORKEY_THRESHOLD_B,
	OLMCOLORKEY_EDGE_THIN_AMOUNT,
	OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE,
	OLMCOLORKEY_EDGE_BLUR_AMOUNT,
	OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE,
	OLMCOLORKEY_EDGE_BLUR_DIRECTION,
	OLMCOLORKEY_NUMBER_OF_COLORS,
	OLMCOLORKEY_ENABLE_REPLACE,
	OLMCOLORKEY_COLOR_FIRST,
	OLMCOLORKEY_NUM_PARAMS = OLMCOLORKEY_COLOR_FIRST + OLMCOLORKEY_MAX_COLORS * 8
};

enum {
	COLOR_KEEP_DISK_ID = 1,
	THRESHOLD_DISK_ID = 2,
	PREMULTIPLIED_DISK_ID = 4,
	COLOR_SPACE_DISK_ID = 5,
	FORCE_LOWER_PRECISION_DISK_ID = 0x20a,
	PER_COLOR_DISK_ID = 6,
	PER_COMPONENT_DISK_ID = 7,
	THRESHOLD_R_DISK_ID = 8,
	THRESHOLD_G_DISK_ID = 9,
	THRESHOLD_B_DISK_ID = 10,
	EDGE_THIN_AMOUNT_DISK_ID = 0x0d,
	EDGE_THIN_DISTANCE_TYPE_DISK_ID = 0x0e,
	EDGE_BLUR_AMOUNT_DISK_ID = 0x11,
	EDGE_BLUR_DISTANCE_TYPE_DISK_ID = 0x12,
	EDGE_BLUR_DIRECTION_DISK_ID = 0x13,
	NUMBER_OF_COLORS_DISK_ID = 0x15,
	ENABLE_REPLACE_DISK_ID = 0x20b,
	COLOR_DISK_ID_FIRST = 0x16,
	THRESHOLD_DISK_ID_FIRST = 0x17,
	THRESHOLD_R_DISK_ID_FIRST = 0x18,
	THRESHOLD_G_DISK_ID_FIRST = 0x19,
	THRESHOLD_B_DISK_ID_FIRST = 0x1a,
	USE_COLOR_DISK_ID_FIRST = 0x20c,
	USE_REPLACE_DISK_ID_FIRST = 0x20d,
	REPLACE_COLOR_DISK_ID_FIRST = 0x20e
};

enum {
	COLOR_PARAM_STRIDE = 8,
	COLOR_OFFSET_COLOR = 0,
	COLOR_OFFSET_THRESHOLD = 1,
	COLOR_OFFSET_THRESHOLD_R = 2,
	COLOR_OFFSET_THRESHOLD_G = 3,
	COLOR_OFFSET_THRESHOLD_B = 4,
	COLOR_OFFSET_USE_COLOR = 5,
	COLOR_OFFSET_USE_REPLACE = 6,
	COLOR_OFFSET_REPLACE_COLOR = 7
};

typedef struct {
	PF_Boolean color_keep;
	PF_FpLong threshold;
	PF_Boolean premultiplied;
	A_long color_space;
	PF_Boolean per_color;
	PF_Boolean per_component;
	PF_FpLong threshold_r;
	PF_FpLong threshold_g;
	PF_FpLong threshold_b;
	PF_FpLong edge_thin_amount;
	A_long edge_thin_distance_type;
	PF_FpLong edge_blur_amount;
	A_long edge_blur_distance_type;
	A_long edge_blur_direction;
	A_long number_of_colors;
	PF_Boolean enable_replace;
	PF_Pixel8 colors8[OLMCOLORKEY_MAX_COLORS];
	PF_PixelFloat colors[OLMCOLORKEY_MAX_COLORS];
	PF_FpLong thresholds[OLMCOLORKEY_MAX_COLORS];
	PF_FpLong thresholds_r[OLMCOLORKEY_MAX_COLORS];
	PF_FpLong thresholds_g[OLMCOLORKEY_MAX_COLORS];
	PF_FpLong thresholds_b[OLMCOLORKEY_MAX_COLORS];
	PF_Boolean use_color[OLMCOLORKEY_MAX_COLORS];
} OLMColorKeyInfo;

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
