#include "OLMBlur.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                          "" },
	{ StrID_Name,                          "OLM Blur" },
	{ StrID_Description,                   "Blur the source while keeping the selected divisions.\rCopyright 2014 OLM Digital, Inc." },
	{ StrID_BlurAmount_Param_Name,         "Blur Amount" },
	{ StrID_BlurSmoothness_Param_Name,     "Blur Smoothness" },
	{ StrID_Repeat_Param_Name,             "Number of Repeat" },
	{ StrID_BiasDirection_Param_Name,      "Bias Direction" },
	{ StrID_BiasDirection_Choices,         "Vertical|Horizontal" },
	{ StrID_Legacy_Param_Name,             "Legacy" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
