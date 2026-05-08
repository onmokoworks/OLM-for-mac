#include "OLMSmoother2.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                     "" },
	{ StrID_Name,                     "OLM Smoother v2" },
	{ StrID_Description,              "Smooth images.\rCopyright OLM Digital, Inc." },
	{ StrID_EnableKey_Param_Name,     "Enable Color Key" },
	{ StrID_Key_Param_Name,           "Color Key" },
	{ StrID_InvertKey_Param_Name,     "Invert Color Key" },
	{ StrID_Smoothness_Param_Name,    "Smoothness" },
	{ StrID_ExtraSmooth_Param_Name,   "Extra Smooth" },
	{ StrID_SmoothRange_Param_Name,   "Smooth Range" },
	{ StrID_Version_Param_Name,       "Smoother Version" },
	{ StrID_Version_Choices,          "v1|v2" },
	{ StrID_Gamma_Param_Name,         "Gamma Correction" },
	{ StrID_Gamma_Choices,            "None|Gamma Colors|All Colors" },
	{ StrID_GammaValue_Param_Name,    "Gamma Value" },
	{ StrID_NumGamma_Param_Name,      "Number of Gamma Colors" },
	{ StrID_GammaColor_Param_Name,    "Gamma Color" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
