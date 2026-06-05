#include "OLMDirectionalBlur.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                       "" },
	{ StrID_Name,                       "OLM DirectionalBlur" },
	{ StrID_Description,                "Port of OLM DirectionalBlur.\rCopyright 2010 OLM Digital, Inc." },
	{ StrID_Angle_Param_Name,           "Angle" },
	{ StrID_BrightnessGain_Param_Name,  "Brightness Gain" },
	{ StrID_SizeVariation_Param_Name,   "Size Variation" },
	{ StrID_FrontStrength_Param_Name,   "Front Blur Strength" },
	{ StrID_FrontAlphaFade_Param_Name,  "Front Alpha Fade" },
	{ StrID_FrontSharpTail_Param_Name,  "Front Sharp Tail" },
	{ StrID_BackStrength_Param_Name,    "Back Blur Strength" },
	{ StrID_BackAlphaFade_Param_Name,   "Back Alpha Fade" },
	{ StrID_BackSharpTail_Param_Name,   "Back Sharp Tail" },
	{ StrID_NoiseVariation_Param_Name,  "Noise Variation" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
