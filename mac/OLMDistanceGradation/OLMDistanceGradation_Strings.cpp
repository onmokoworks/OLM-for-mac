#include "OLMDistanceGradation.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                          "" },
	{ StrID_Name,                          "Distance Gradation" },
	{ StrID_Description,                   "Generate color gradation using distance transform.\rCopyright 2014 OLM Digital, Inc." },
	{ StrID_Invert_Param_Name,             "Invert" },
	{ StrID_InOut_Param_Name,              "In/Out" },
	{ StrID_InOut_Choices,                 "Inside|Outside|Both" },
	{ StrID_InsideThreshold_Param_Name,    "Inside Threshold" },
	{ StrID_OutsideThreshold_Param_Name,   "Outside Threshold" },
	{ StrID_RenderMode_Param_Name,         "Render Mode" },
	{ StrID_RenderMode_Choices,            "RGB|Layer" },
	{ StrID_UseBgColor_Param_Name,         "Use Background Color" },
	{ StrID_GradColor_Param_Name,          "Gradation Color" },
	{ StrID_BgColor_Param_Name,            "BG Color " },
	{ StrID_InterpMode_Param_Name,         "Interpolation Mode" },
	{ StrID_InterpMode_Choices,            "Constant|Linear|Sphere|Power" },
	{ StrID_Power_Param_Name,              "Power" },
	{ StrID_BlurMode_Param_Name,           "Blur Mode" },
	{ StrID_BlurMode_Choices,              "No Blur|Blur No Scale|Blur" },
	{ StrID_BlurSize_Param_Name,           "Blur Size" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
