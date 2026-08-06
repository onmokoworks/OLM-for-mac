#include "OLMSmoother.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                          "" },
	{ StrID_Name,                          "OLM Smoother" },
	{ StrID_Description,                   "Smooth line of cell animation.\rCopyright OLM Digital, Inc." },
	{ StrID_UseKey_Param_Name,             "Use Color Key" },
	{ StrID_Key_Param_Name,                "Color Key" },
	{ StrID_Tolerance_Param_Name,          "Do Smooth Range" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
